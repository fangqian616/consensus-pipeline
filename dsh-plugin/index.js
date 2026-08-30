// @deepseek-ai/dsh-consensus-pipeline
// Native tool plugin: spawns the Python MCP server (mcp_server.py) over stdio
// JSON-RPC 2.0 (newline-framed), discovers its tools via tools/list, and
// re-registers them as native DSH tools with background-job progress for the
// long-running full pipeline. Also mounts a web control panel (same-origin,
// under /consensus-pipeline/) via the DSH webServer service.
//
// Deliberately has NO `@deepseek-ai/*` runtime imports: tool definitions are
// built as raw JSON-Schema objects, so this module resolves in any DSH checkout
// regardless of hoisted dependency versions and needs no bundled node_modules.
import readline from 'node:readline';
import { readFile, readdir, stat, mkdir } from 'node:fs/promises';
import { readFileSync, writeFileSync, existsSync, realpathSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const name = 'dsh-consensus-pipeline';
export const inject = ['tools', 'subprocess', 'systemPrompt', 'webServer', 'skills'];

const REQUEST_TIMEOUT_MS = 30_000;
const TOOL_CALL_TIMEOUT_MS = 3600_000;
const POLL_INTERVAL_MS = 15_000;

// 自动 clone 用的仓库与目标目录（config 可覆盖）。目录固定，避免每次重启重复 clone。
const DEFAULT_REPO = 'https://github.com/fangqian616/consensus-pipeline.git';
const DEFAULT_CLONE_DIR = () => join(homedir(), '.dsh', 'consensus-pipeline');

function detectProjectRoot() {
  // Walk up from this plugin file (resolving symlinks for pnpm) to find mcp_server.py
  let here;
  try {
    here = dirname(fileURLToPath(import.meta.url));
    here = dirname(realpathSync(here)); // resolve pnpm symlink if any
  } catch {
    here = process.cwd();
  }
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(here, 'mcp_server.py'))) return here;
    const parent = dirname(here);
    if (parent === here) break;
    here = parent;
  }
  return null; // 未找到 → 由 resolveProjectRoot 走 clone 兜底
}

// 解析项目根目录：显式 config > 插件邻近目录 > 已有 clone 目录 > 自动 git clone。
function resolveProjectRoot(config) {
  // 1. 用户显式指定 cwd / script
  if (config.cwd || config.script) {
    const root = config.cwd ?? dirname(config.script);
    return { root, script: config.script ?? join(root, 'mcp_server.py'), cloned: false };
  }

  // 2. 插件文件邻近目录（本地 file:/junction 安装的常规路径）
  const detected = detectProjectRoot();
  if (detected) {
    return { root: detected, script: join(detected, 'mcp_server.py'), cloned: false };
  }

  // 3. 已有 clone 目录（重启复用）
  const cloneDir = config.cloneDir ?? DEFAULT_CLONE_DIR();
  const cloneScript = join(cloneDir, 'mcp_server.py');
  if (existsSync(cloneScript)) {
    return { root: cloneDir, script: cloneScript, cloned: true };
  }

  // 3.5 清理上一次 clone 失败留下的残留空目录（否则 git 会报 "already exists"）
  try {
    if (existsSync(cloneDir)) rmSync(cloneDir, { recursive: true, force: true });
  } catch { /* 忽略清理失败，交给 git clone 报错 */ }

  // 4. 自动 git clone
  const repo = config.repo ?? DEFAULT_REPO;
  const ref = config.ref ? [config.ref] : [];
  const result = spawnSync('git', ['clone', '--depth', '1', ...ref, repo, cloneDir], {
    stdio: 'pipe', encoding: 'utf8', timeout: 180_000,
  });

  if (result.status === 0 && existsSync(cloneScript)) {
    return { root: cloneDir, script: cloneScript, cloned: true };
  }
  // 再次清理失败残留，避免下次启动撞上 "already exists"
  try { if (existsSync(cloneDir)) rmSync(cloneDir, { recursive: true, force: true }); } catch {}

  // 克隆失败：给出中英文提示（git 不可用 / 网络失败 / 仓库地址错误等）
  const errDetail = (result.stderr || result.stdout || '').trim().slice(0, 400);
  console.error('\n[dsh-consensus-pipeline] ⚠️ 未能自动获取 Consensus Pipeline 项目代码。');
  console.error('  插件本身已安装，但缺少 Python 管线（mcp_server.py）。请手动执行：');
  console.error('    git clone ' + repo);
  console.error('  然后将 clone 目录通过插件配置 cwd/script 指定，或放到：' + cloneDir);
  console.error('  （原因：' + (errDetail || 'git clone 失败') + '）\n');
  console.error('[dsh-consensus-pipeline] ⚠️ Failed to auto-clone the Consensus Pipeline project.');
  console.error('  The plugin is installed but the Python pipeline (mcp_server.py) is missing.');
  console.error('  Run manually: git clone ' + repo);
  console.error('  Then point the plugin config cwd/script at it, or place it at: ' + cloneDir);
  console.error('  (reason: ' + (errDetail || 'git clone failed') + ')\n');

  return null;
}

export function apply(ctx, config = {}) {
  const python = config.python ?? 'python';

  const project = resolveProjectRoot(config);
  if (!project) {
    // 项目代码缺失：不注册任何工具，但保持插件挂载（web 面板也不注册，避免空转）。
    return () => {};
  }
  const _root = project.root;
  const script = project.script;
  const cwd = _root;
  const graceMs = config.graceMs ?? 5000;

  const disposers = [];

  let proc = null;
  let nextId = 1;
  const pending = new Map();
  let rl = null;
  let initialized = false;
  let toolSchemas = [];

  function failAllPending(error) {
    for (const [, p] of pending) { clearTimeout(p.timer); p.reject(error); }
    pending.clear();
  }

  function ensureProc() {
    if (proc) return proc;
    proc = ctx.subprocess.spawn({
      argv: [python, script],
      cwd,
      stdio: { stdin: 'pipe', stdout: 'pipe', stderr: 'inherit' },
      graceMs,
    });
    rl = readline.createInterface({ input: proc.stdout, crlfDelay: Infinity });
    rl.on('line', (line) => {
      let msg;
      try { msg = JSON.parse(line); } catch { return; }
      if (msg && msg.id != null && pending.has(msg.id)) {
        const { resolve, reject, timer } = pending.get(msg.id);
        pending.delete(msg.id);
        clearTimeout(timer);
        if (msg.error) reject(new Error(msg.error.message ?? 'JSON-RPC error'));
        else resolve(msg.result);
      }
    });
    proc.done.catch(() => {
      failAllPending(new Error('consensus-pipeline python process exited'));
      proc = null; rl = null; initialized = false;
    });
    return proc;
  }

  function request(method, params = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
    return new Promise((resolve, reject) => {
      let p;
      try { p = ensureProc(); } catch (error) { reject(error); return; }
      const id = nextId++;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error('consensus-pipeline JSON-RPC timeout: ' + method));
      }, timeoutMs);
      pending.set(id, { resolve, reject, timer });
      try {
        p.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
      } catch (error) {
        clearTimeout(timer); pending.delete(id); reject(error);
      }
    });
  }

  async function callTool(toolName, args) {
    const res = await request('tools/call', { name: toolName, arguments: args ?? {} }, TOOL_CALL_TIMEOUT_MS);
    const block = res?.content?.[0];
    if (block?.type === 'text') return block.text;
    return JSON.stringify(res ?? {}, null, 2);
  }

  async function ensureInitialized() {
    if (initialized) return;
    await request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'dsh-consensus-pipeline', version: '0.1.0' },
    });
    const list = await request('tools/list', {});
    toolSchemas = list?.tools ?? [];
    initialized = true;
  }

  ctx.systemPrompt?.section?.({
    name: 'tool:consensus-pipeline',
    order: 100,
    text: 'Consensus Pipeline tools run the academic research pipeline (search → debate → report). Important: when the user expresses a research intent — even a vague one — do NOT ask them to finalize a topic upfront. First run a requirement research interview in conversation: ask about core questions, discipline/scope, time range, methodology, quality standard, and deliverable, refining the topic through this multi-turn dialogue. Then call run_requirement_research with the refined topic and a free-text summary of what you gathered to produce the working-group configuration, then call run_full_pipeline with that topic to start the pipeline. Use get_pipeline_status to check progress and locate output files. A web control panel is served at /consensus-pipeline/ on this host.',
  });

  // 注册「需求调研逐个追问」skill —— 随插件绑定，任何 agent 在做研究任务时
  // 加载它，就获得同一套逐轮访谈 SOP（不靠 agent 临场发挥）。
  ctx.skills?.register?.({
    name: 'consensus-requirement-interview',
    description: '逐个追问的需求调研访谈流程，把模糊的研究主题收敛成结构化需求，再交给管线生成配置。',
    source: 'dsh-consensus-pipeline',
    whenToUse: '当用户表达研究意图、准备用 Consensus Pipeline 做学术调研/文献综述时，先加载本 skill 再开始访谈。',
    content: [
      '# 需求调研逐个追问 SOP（Consensus Pipeline）',
      '',
      '## 铁律',
      '1. 一次只问一个问题，禁止一次性抛出问题清单。',
      '2. 禁止预设/硬编码任何学科方向（不要默认「能源」「用能权」等）。',
      '3. 每轮只做：提问 → 收到回答 → 提取信息 → 判断是否完成 → 未完成则问下一个维度。',
      '',
      '## 固定维度顺序（逐个问，不要跳过）',
      '1. 核心研究问题 / 侧重点',
      '2. 学科范围（让用户自己说，不预设）',
      '3. 时间范围（近 3/5/10 年，或自定义区间）',
      '4. 方法论偏好（计量 / 机器学习 / 混合 / 定性等）',
      '5. 论文质量标准（顶刊 / 同行评审 / 不限）',
      '6. 预期交付物（综述报告 / 综述+技术选型+教程 等）',
      '',
      '## 完成判定',
      '覆盖 ≥80% 维度（至少 5/6）且已有明确目标、已有交付物 → 结束访谈。',
      '',
      '## 完成后',
      '1. 把收集到的信息整理成一段 free-text requirements summary（含目标、约束、时间范围、交付物、质量标准、检索来源）。',
      '2. 调用 run_requirement_research(topic, requirements=summary) 生成工作组配置。',
      '3. 调用 run_full_pipeline(topic) 启动完整管线。',
      '4. 用 get_pipeline_status 查进度和输出文件位置。',
    ].join('\n'),
  });

  (async () => {
    try {
      await ensureInitialized();
    } catch (e) {
      console.error('[dsh-consensus-pipeline] discovery failed: ' + e.message);
      return;
    }
    for (const t of toolSchemas) {
      const toolName = t.name;
      const description = t.description ?? ('Consensus pipeline tool: ' + toolName);
      const isFullPipeline = toolName === 'run_full_pipeline';

      const def = {
        name: toolName,
        description,
        parameters: t.inputSchema ?? { type: 'object', properties: {} },
        output: {
          schema: {
            type: 'object',
            additionalProperties: false,
            properties: { text: { type: 'string' }, jobId: { type: 'string' } },
            required: ['text'],
          },
          render: (_args, value) => [{ type: 'text', text: value?.text ?? '' }],
        },
        async execute(args, exec) {
          if (!isFullPipeline) return { text: await callTool(toolName, args) };
          const jobs = ctx.get('jobs');
          const start = await callTool(toolName, args);
          let jobId;
          try { jobId = JSON.parse(start)?.job_id; } catch { jobId = undefined; }
          if (!jobs || !jobId) return { text: start };
          const started = jobs.start({
            kind: 'consensus-pipeline',
            label: ('run_full_pipeline ' + (args?.topic ?? '')).trim(),
            ...(exec?.agent ? { owner: exec.agent } : {}),
            run: () => {
              const done = (async () => {
                for (;;) {
                  const st = await callTool('get_job_status', { job_id: jobId });
                  let parsed = {};
                  try { parsed = JSON.parse(st); } catch {}
                  if (parsed.status === 'done' || parsed.status === 'error') {
                    return { status: 'completed', detail: parsed.status, text: parsed.summary ?? parsed.error ?? '' };
                  }
                  await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
                }
              })();
              return {
                cancel: () => {},
                done: done.then((o) => ({ status: o.status, detail: o.detail })),
                readOutput: async () => {
                  try {
                    const st = await callTool('get_job_status', { job_id: jobId });
                    let parsed = {};
                    try { parsed = JSON.parse(st); } catch {}
                    return ('[' + (parsed.status ?? 'running') + '] ' + (parsed.summary ?? '')).slice(0, 800) || '[running] consensus pipeline executing...';
                  } catch { return '[running] consensus pipeline executing...'; }
                },
              };
            },
          });
          return { text: 'started background job ' + started + ' — poll get_job_status for progress', jobId: started };
        },
        presentCall(args) {
          const topic = (args && args.topic) ? String(args.topic) : '';
          return {
            card: 'generic',
            title: toolName + (topic ? (' · ' + topic) : ''),
            kind: 'execute',
            rawInput: topic || undefined,
            content: [{ type: 'text', text: 'Consensus Pipeline 控制台：/consensus-pipeline/' }],
          };
        },
        presentResult(_args, result) {
          const v = (result && result.value) || {};
          const text = typeof v.text === 'string' ? v.text : '';
          const body = (text ? text.slice(0, 1500) + '\n\n' : '') + '控制台：/consensus-pipeline/';
          return {
            card: 'generic',
            title: toolName + ' 完成',
            content: [{ type: 'text', text: body }],
          };
        },
      };

      disposers.push(ctx.tools.register(def));
    }
    console.error('[dsh-consensus-pipeline] registered ' + toolSchemas.length + ' tools');
  })();

  try {
    registerWebPanel(ctx, { cwd, callTool, disposers, python });
  } catch (e) {
    console.error('[dsh-consensus-pipeline] web panel registration failed: ' + (e?.message ?? e));
  }

  return () => {
    for (const d of disposers) { try { d(); } catch {} }
    if (rl) rl.close();
    if (proc) proc.terminate();
  };
}

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (c) => { data += c; });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function json(res, status, obj) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(obj));
}

async function findReport(root, topic) {
  const tag = topic.slice(0, 20).replace(/[\/\\\s:：]+/g, '_');
  const needles = [tag, topic.slice(0, 8)].filter((n) => n.length > 0);
  const hits = [];
  for (const dirName of ['v2_run_output', 'run_output']) {
    const dir = join(root, dirName);
    let entries = [];
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      const runDir = join(dir, e.name);
      if (!needles.some((n) => e.name.includes(n))) continue;
      for (const fname of ['final_report_validated.md', 'final_report.md', 'consensus_report.md', 'report.md']) {
        const p = join(runDir, fname);
        try {
          const st = await stat(p);
          hits.push({ path: p, mtime: st.mtimeMs, name: dirName + '/' + e.name + '/' + fname, dir: runDir });
          break;
        } catch {}
      }
    }
  }
  hits.sort((a, b) => b.mtime - a.mtime);
  if (hits.length === 0) return null;
  try {
    const content = await readFile(hits[0].path, 'utf8');
    return { name: hits[0].name, content, dir: hits[0].dir };
  } catch { return null; }
}

async function findVerification(root, topic) {
  const tag = topic.slice(0, 20).replace(/[\/\\\s:：]+/g, '_');
  const needles = [tag, topic.slice(0, 8)].filter((n) => n.length > 0);
  const hits = [];
  for (const dirName of ['v2_run_output', 'run_output']) {
    const dir = join(root, dirName);
    let entries = [];
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      const runDir = join(dir, e.name);
      if (!needles.some((n) => e.name.includes(n))) continue;
      const p = join(runDir, 'citation_verification.json');
      try {
        const st = await stat(p);
        hits.push({ path: p, mtime: st.mtimeMs, name: dirName + '/' + e.name });
      } catch {}
    }
  }
  hits.sort((a, b) => b.mtime - a.mtime);
  if (hits.length === 0) return null;
  try {
    const d = JSON.parse(await readFile(hits[0].path, 'utf8'));
    return {
      name: hits[0].name,
      total_claims: d.total_claims ?? 0,
      verified: d.verified ?? 0,
      partially_verified: d.partially_verified ?? 0,
      contradicted: d.contradicted ?? 0,
      unverified: d.unverified ?? 0,
      insufficient_evidence: d.insufficient_evidence ?? 0,
      needs_fulltext: d.needs_fulltext ?? 0,
      overall_confidence: d.overall_confidence ?? 0,
      nli_llm_failures: d.nli_llm_failures ?? 0,
      evidence_insufficient: d.evidence_insufficient ?? false,
      summary: d.summary ?? '',
    };
  } catch { return null; }
}

async function findVerificationMissing(root, topic) {
  const tag = topic.slice(0, 20).replace(/[\/\\\s:：]+/g, '_');
  const needles = [tag, topic.slice(0, 8)].filter((n) => n.length > 0);
  const hits = [];
  for (const dirName of ['v2_run_output', 'run_output']) {
    const dir = join(root, dirName);
    let entries = [];
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      const runDir = join(dir, e.name);
      if (!needles.some((n) => e.name.includes(n))) continue;
      const p = join(runDir, 'citation_verification.json');
      try { const st = await stat(p); hits.push({ path: p, mtime: st.mtimeMs }); } catch {}
    }
  }
  hits.sort((a, b) => b.mtime - a.mtime);
  if (hits.length === 0) return null;
  const d = JSON.parse(await readFile(hits[0].path, 'utf8'));
  const rows = [];
  for (const cv of (d.claim_verifications || [])) {
    if (cv.status === 'verified' || cv.status === 'partially_verified') continue;
    const papers = [];
    for (const n of (cv.nli_results || [])) {
      papers.push({ title: n.ref_title || '', doi: n.ref_doi || '', evidence: n.evidence || '' });
    }
    // Tier mirrors citation_verifier.py: title-only → insufficient_evidence,
    // abstract-but-neutral → needs_fulltext, else → plain unverified.
    let type = 'unverified';
    if (cv.status === 'contradicted') {
      type = 'contradicted';
    } else if (papers.length > 0) {
      const allTitle = papers.every((p) => (p.evidence || 'abstract') === 'title');
      type = allTitle ? 'insufficient_evidence' : 'needs_fulltext';
    }
    rows.push({ claim: (cv.claim && cv.claim.text) || '', status: cv.status, type, papers });
  }
  return rows;
}

// ── Phase 5.5 全文断点: pending import 状态 ──────────────────────────────
async function findPendingImportPath(root) {
  const hits = [];
  for (const dirName of ['v2_run_output', 'run_output']) {
    const dir = join(root, dirName);
    let entries = [];
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      const p = join(dir, e.name, 'pending_fulltext_import.json');
      try { const st = await stat(p); hits.push({ path: p, mtime: st.mtimeMs }); } catch {}
    }
  }
  hits.sort((a, b) => b.mtime - a.mtime);
  return hits.length > 0 ? hits[0].path : null;
}

// ── Seed paper management helpers ─────────────────────────────────────────
function seedManifestPath(cwd) { return join(cwd, 'seed_papers', 'manifest.json'); }

function readSeedManifest(cwd) {
  try {
    const d = JSON.parse(readFileSync(seedManifestPath(cwd), 'utf8'));
    return d && typeof d === 'object' ? d : {};
  } catch { return {}; }
}

function writeSeedManifest(cwd, data) {
  writeFileSync(seedManifestPath(cwd), JSON.stringify(data, null, 2), 'utf8');
}

async function listSeedPdf(cwd) {
  const dir = join(cwd, 'seed_papers');
  try {
    const entries = await readdir(dir);
    return entries.filter((n) => n.toLowerCase().endsWith('.pdf'));
  } catch { return []; }
}

function runSeedImport(cwd, python) {
  const code = 'import json; from paper_importer import import_seed_papers; print(json.dumps(import_seed_papers("seed_papers"), ensure_ascii=False))';
  const r = spawnSync(python, ['-c', code], { cwd, encoding: 'utf8', timeout: 120000 });
  if (r.status !== 0) return null;
  try { return JSON.parse(r.stdout); } catch { return null; }
}

function registerWebPanel(ctx, { cwd, callTool, disposers, python }) {
  const webServer = ctx.get('webServer');
  if (!webServer) {
    console.error('[dsh-consensus-pipeline] webServer service unavailable — web panel skipped');
    return;
  }

  // v0.13: in-flight re-verify (Phase 7.7) job state for the panel's one-click re-run.
  let reverify = null;

  const route = webServer.register({
    kind: 'prefix',
    path: '/consensus-pipeline',
    handler: async (req, res) => {
      let url;
      try { url = new URL(req.url ?? '/', 'http://x'); } catch { url = new URL('/', 'http://x'); }
      const pathname = url.pathname;

      if (pathname === '/consensus-pipeline' || pathname === '/consensus-pipeline/' || pathname === '/consensus-pipeline/index.html') {
        try {
          const html = await readFile(join(cwd, 'panel.html'), 'utf8');
          res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-cache' });
          res.end(html);
        } catch {
          res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
          res.end('<!DOCTYPE html><meta charset="utf-8"><title>Consensus Pipeline</title><h1>Consensus Pipeline</h1><p>panel.html 未找到（应位于项目根目录）。</p>');
        }
        return;
      }

      if (pathname === '/consensus-pipeline/api/run' && req.method === 'POST') {
        try {
          const body = await readRequestBody(req);
          let p = {};
          try { p = JSON.parse(body || '{}'); } catch {}
          const topic = String(p.topic ?? '').trim();
          if (!topic) return json(res, 400, { error: 'topic is required' });
          const text = await callTool('run_full_pipeline', {
            topic, lang: p.lang ?? 'zh', use_v2: p.use_v2 !== false, max_rounds: p.max_rounds ?? 8,
          });
          res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
          res.end(text);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/status') {
        try {
          const jobId = url.searchParams.get('job_id') ?? '';
          const text = await callTool('get_job_status', { job_id: jobId });
          res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
          res.end(text);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/pipeline-status') {
        try {
          const text = await callTool('get_pipeline_status', {});
          res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
          res.end(text);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/report') {
        try {
          const topic = url.searchParams.get('topic') ?? '';
          const found = await findReport(cwd, topic);
          if (!found) return json(res, 404, { error: 'report not found (still generating?)' });
          json(res, 200, found);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/image') {
        try {
          const topic = url.searchParams.get('topic') ?? '';
          const file = url.searchParams.get('file') ?? '';
          // 安全：拒绝路径穿越 / 绝对路径，只允许报告目录内的相对路径
          if (!file || file.includes('..') || file.startsWith('/') || file.startsWith('\\') || /^[a-zA-Z]:/.test(file)) {
            return json(res, 400, { error: 'bad file' });
          }
          const found = await findReport(cwd, topic);
          if (!found || !found.dir) return json(res, 404, { error: 'report not found' });
          let buf;
          try { buf = await readFile(join(found.dir, file)); } catch { return json(res, 404, { error: 'image not found' }); }
          const ext = (file.split('.').pop() || '').toLowerCase();
          const mime = ext === 'png' ? 'image/png'
            : ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg'
            : ext === 'gif' ? 'image/gif'
            : ext === 'webp' ? 'image/webp'
            : 'application/octet-stream';
          res.writeHead(200, { 'content-type': mime, 'cache-control': 'no-cache' });
          res.end(buf);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/verification') {
        try {
          const topic = url.searchParams.get('topic') ?? '';
          const found = await findVerification(cwd, topic);
          if (!found) return json(res, 404, { error: 'verification not found (still generating?)' });
          json(res, 200, found);
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/verification-missing') {
        try {
          const topic = url.searchParams.get('topic') ?? '';
          const rows = await findVerificationMissing(cwd, topic);
          if (!rows) return json(res, 404, { error: 'verification not found' });
          json(res, 200, { missing: rows });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/seed-list') {
        try {
          const manifest = readSeedManifest(cwd);
          const pdfs = await listSeedPdf(cwd);
          const byFile = {};
          for (const p of (manifest.papers || [])) byFile[p.file] = p.weight || manifest.default_weight || 'core';
          const papers = pdfs.map((file) => ({
            file,
            weight: byFile[file] || manifest.default_weight || 'core',
          }));
          json(res, 200, { papers, default_weight: manifest.default_weight || 'core' });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/seed-upload' && req.method === 'POST') {
        try {
          const filename = (url.searchParams.get('filename') || '').replace(/[\\/:*?"<>|]/g, '_').trim();
          if (!filename) return json(res, 400, { error: 'filename is required' });
          const chunks = [];
          for await (const c of req) chunks.push(c);
          const buf = Buffer.concat(chunks);
          const dir = join(cwd, 'seed_papers');
          try { await stat(dir); } catch { await mkdir(dir, { recursive: true }); }
          writeFileSync(join(dir, filename), buf);
          const imported = runSeedImport(cwd, python);
          const manifest = readSeedManifest(cwd);
          if (!(manifest.papers || []).some((p) => p.file === filename)) {
            manifest.papers = manifest.papers || [];
            manifest.papers.push({ file: filename, weight: manifest.default_weight || 'core' });
            writeSeedManifest(cwd, manifest);
          }
          const meta = (imported || []).find((p) => (p.file_name || p.file) === filename) || null;
          json(res, 200, { ok: true, filename, meta });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/fulltext-upload' && req.method === 'POST') {
        try {
          const chunks = [];
          for await (const c of req) chunks.push(c);
          const buf = Buffer.concat(chunks);
          if (buf.length < 200 || buf.slice(0, 5).toString() !== '%PDF-') {
            return json(res, 400, { error: 'body is not a valid PDF' });
          }
          const dir = join(cwd, 'fulltext_papers');
          try { await stat(dir); } catch { await mkdir(dir, { recursive: true }); }
          // 任意命名（时间戳），DOI 由重跑校验时从 PDF 内部提取——无需用户重命名
          const filename = `upload_${Date.now()}_${Math.random().toString(36).slice(2, 8)}.pdf`;
          writeFileSync(join(dir, filename), buf);
          json(res, 200, { ok: true, filename });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/reverify-77' && req.method === 'POST') {
        try {
          if (reverify && reverify.running) {
            return json(res, 409, { error: 're-verify already running' });
          }
          const body = await readRequestBody(req);
          let pb = {};
          try { pb = JSON.parse(body || '{}'); } catch {}
          const topic = String(pb.topic ?? '').trim();
          const runDirArg = [];
          if (topic) {
            const found = await findReport(cwd, topic);
            if (found && found.dir) runDirArg.push(found.dir);
          }
          const p = ctx.subprocess.spawn({
            argv: [python, '_reverify_77.py', ...runDirArg],
            cwd,
            stdio: { stdin: 'ignore', stdout: 'inherit', stderr: 'inherit' },
            graceMs: 5000,
          });
          reverify = { running: true, startedAt: Date.now(), finishedAt: null, error: false };
          p.done.then(() => { reverify.running = false; reverify.finishedAt = Date.now(); })
            .catch(() => { reverify.running = false; reverify.finishedAt = Date.now(); reverify.error = true; });
          json(res, 200, { ok: true, started: true });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/reverify-status') {
        let progress = null;
        try {
          progress = JSON.parse(await readFile(join(cwd, 'reverify_progress.json'), 'utf8'));
        } catch {}
        json(res, 200, {
          running: !!(reverify && reverify.running),
          startedAt: reverify ? reverify.startedAt : null,
          finishedAt: reverify ? reverify.finishedAt : null,
          error: !!(reverify && reverify.error),
          progress,
        });
        return;
      }

      if (pathname === '/consensus-pipeline/api/pending-import') {
        if (req.method === 'POST') {
          try {
            const body = await readRequestBody(req);
            let p = {};
            try { p = JSON.parse(body || '{}'); } catch {}
            const status = String(p.status ?? '').trim();
            if (!['confirmed', 'skipped', 'paused'].includes(status)) {
              return json(res, 400, { error: 'status must be confirmed/skipped/paused' });
            }
            const path = await findPendingImportPath(cwd);
            if (!path) return json(res, 404, { error: 'no pending import' });
            const pending = JSON.parse(await readFile(path, 'utf8'));
            pending.status = status;
            pending.updated_at = Date.now();
            writeFileSync(path, JSON.stringify(pending, null, 2));
            json(res, 200, { ok: true, status });
          } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
          return;
        }
        // GET
        try {
          const path = await findPendingImportPath(cwd);
          if (!path) return json(res, 200, { pending: null });
          const pending = JSON.parse(await readFile(path, 'utf8'));
          json(res, 200, { pending });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      if (pathname === '/consensus-pipeline/api/seed-weight' && req.method === 'POST') {
        try {
          const body = await readRequestBody(req);
          let p = {};
          try { p = JSON.parse(body || '{}'); } catch {}
          const filename = String(p.file ?? '').trim();
          const weight = String(p.weight ?? '').trim();
          if (!filename || !['core', 'anchor', 'normal'].includes(weight)) {
            return json(res, 400, { error: 'file and weight (core/anchor/normal) are required' });
          }
          const manifest = readSeedManifest(cwd);
          let found = false;
          for (const item of (manifest.papers || [])) {
            if (item.file === filename) { item.weight = weight; found = true; break; }
          }
          if (!found) {
            manifest.papers = manifest.papers || [];
            manifest.papers.push({ file: filename, weight });
          }
          writeSeedManifest(cwd, manifest);
          json(res, 200, { ok: true, filename, weight });
        } catch (e) { json(res, 500, { error: e?.message ?? String(e) }); }
        return;
      }

      res.writeHead(404);
      res.end('not found');
    },
  });
  disposers.push(route);
  // Inject a floating "控制台" button + iframe panel into the DSH web shell,
  // so the panel appears INSIDE the DSH interface (not a separate tab).
  disposers.push(webServer.tapIndex(injectFloatPanel));
}

const FLOAT_PANEL_HTML = `<style>
.cp-fab{position:fixed;right:18px;bottom:18px;z-index:999999;background:#4f8cff;color:#fff;border:none;border-radius:999px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.45);font-family:system-ui,sans-serif;}
.cp-fab:hover{background:#3b74d9;}
.cp-big{position:fixed;right:18px;bottom:60px;z-index:999999;background:#171a21;color:#4f8cff;border:1px solid #262b36;border-radius:999px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.45);font-family:system-ui,sans-serif;text-decoration:none;}
.cp-big:hover{background:#262b36;}
.cp-panel{position:fixed;right:18px;bottom:68px;z-index:999998;width:480px;max-width:92vw;height:72vh;max-height:760px;background:#0f1115;border:1px solid #262b36;border-radius:12px;box-shadow:0 10px 34px rgba(0,0,0,.55);display:none;overflow:hidden;}
.cp-panel.open{display:block;}
.cp-panel iframe{width:100%;height:100%;border:0;display:block;}
</style>
<button id="cp-fab" class="cp-fab" type="button">📊 控制台</button>
<a class="cp-big" href="/consensus-pipeline/" target="_blank" rel="noopener">🖥️ 大屏版</a>
<div id="cp-panel" class="cp-panel"><iframe data-src="/consensus-pipeline/" title="Consensus Pipeline" allow="clipboard-write"></iframe></div>
<script>
(function(){var b=document.getElementById("cp-fab");var p=document.getElementById("cp-panel");var f=p?p.querySelector("iframe"):null;if(b&&p){b.addEventListener("click",function(){var o=p.classList.toggle("open");if(o&&f&&!f.src){f.src=f.getAttribute("data-src");}b.textContent=o?"✕ 关闭":"📊 控制台";});}})();
</script>`;

function injectFloatPanel(html) {
  if (typeof html !== 'string') return html;
  const marker = '</body>';
  const idx = html.lastIndexOf(marker);
  if (idx === -1) return html + FLOAT_PANEL_HTML;
  return html.slice(0, idx) + FLOAT_PANEL_HTML + html.slice(idx);
}
