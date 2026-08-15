#!/usr/bin/env python3
"""
Setup script for v2 Full Pipeline (HTTP 版本)
==============================================
从 GitHub main 分支下载 v1 管线文件到当前目录,与 v2 文件共存。
不需要 git,直接用 HTTPS 下载。

用法:
    python setup_v2_full.py
    python setup_v2_full.py --force   # 强制覆盖已存在的 v1 文件
"""

import os
import sys
import json
import time

REPO_OWNER = "fang616"
REPO_NAME = "consensus-pipeline"
BRANCH = "main"
BASE_RAW = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"
BASE_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error

V1_FILES = [
    "run_pipeline.py",
    "quality_controller.py",
    "domain_config_generator.py",
    "config_manager.py",
    "router.py",
    "app.py",
    "docx_exporter.py",
    "pdf_exporter.py",
    "requirements.txt",
    "domain_config.json",
]

V1_DIRS = [
    "requirement",
    "academic",
    "templates",
    "presets",
    "user_profiles",
]

V2_PROTECTED = [
    "stance_quant_v2.py",
    "mock_experiment.py",
    "real_experiment.py",
    "real_experiment_C.py",
    "real_experiment_batch1.py",
    "calibrate_thresholds.py",
    "integration_guide.py",
    "analyze_stance_log.py",
    "experiment_config.json",
    "run_pipeline_v2.py",
    "setup_v2_full.py",
]


def http_get_json(url):
    if HAS_REQUESTS:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"HTTP {resp.status_code}: {url}")
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "consensus-pipeline-setup"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))


def http_download_text(url):
    if HAS_REQUESTS:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 404:
            return None
        else:
            raise Exception(f"HTTP {resp.status_code}: {url}")
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "consensus-pipeline-setup"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise


def list_github_dir(api_path):
    url = f"{BASE_API}/contents/{api_path}?ref={BRANCH}"
    items = http_get_json(url)
    files = []
    for item in items:
        if item["type"] == "file":
            files.append(item["path"])
        elif item["type"] == "dir":
            try:
                sub_files = list_github_dir(item["path"])
                files.extend(sub_files)
            except Exception:
                pass
    return files


def download_file(rel_path, target_path):
    url = f"{BASE_RAW}/{rel_path}"
    content = http_download_text(url)
    if content is None:
        return False
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def setup(force=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 50)
    print("Consensus Pipeline v2 — Full Pipeline Setup (HTTP)")
    print("=" * 50)
    print(f"工作目录: {script_dir}")
    print(f"仓库: {REPO_OWNER}/{REPO_NAME} @ {BRANCH}")
    print(f"HTTP 库: {'requests' if HAS_REQUESTS else 'urllib'}")
    print()

    print("[1/4] 检查 GitHub 连通性...")
    try:
        http_get_json(f"{BASE_API}/git/ref/heads/{BRANCH}")
        print("  [OK] GitHub 可访问")
    except Exception as e:
        print(f"  [ERROR] 无法连接 GitHub: {e}")
        print("  请检查网络(可能需要代理)")
        sys.exit(1)

    print("[2/4] 下载 v1 顶层文件...")
    extracted = 0
    skipped = 0

    for fname in V1_FILES:
        target = os.path.join(script_dir, fname)
        if os.path.exists(target) and not force:
            if fname in V2_PROTECTED:
                print(f"  [SKIP] {fname} (v2 保护文件)")
                skipped += 1
                continue
            print(f"  [EXIST] {fname} (跳过)")
            skipped += 1
            continue

        print(f"  下载 {fname}...", end=" ")
        try:
            ok = download_file(fname, target)
            if ok:
                print("OK")
                extracted += 1
            else:
                print("MISS")
        except Exception as e:
            print(f"FAIL ({e})")

    print("[3/4] 下载 v1 子目录...")

    for dirname in V1_DIRS:
        print(f"  扫描 {dirname}/...")
        try:
            files = list_github_dir(dirname)
        except Exception as e:
            print(f"    [WARN] 无法列出 {dirname}/: {e}")
            continue

        if not files:
            print(f"    [WARN] {dirname}/ 为空或不存在")
            continue

        dir_extracted = 0
        for fpath in files:
            target = os.path.join(script_dir, fpath)
            if os.path.exists(target) and not force:
                continue
            try:
                ok = download_file(fpath, target)
                if ok:
                    dir_extracted += 1
                    extracted += 1
            except Exception as e:
                print(f"    [FAIL] {fpath}: {e}")

        print(f"    [OK] {dirname}/ — {dir_extracted} 个新文件")
        time.sleep(0.3)

    print("[4/4] 验证...")
    missing = []
    for fname in ["run_pipeline.py", "quality_controller.py",
                  "domain_config_generator.py"]:
        if not os.path.exists(os.path.join(script_dir, fname)):
            missing.append(fname)
    for dirname in ["requirement", "academic", "templates"]:
        if not os.path.isdir(os.path.join(script_dir, dirname)):
            missing.append(dirname + "/")

    if missing:
        print(f"  [WARN] 缺少: {missing}")
    else:
        print("  [OK] 所有必需文件就位")

    v2_ok = all(
        os.path.exists(os.path.join(script_dir, f))
        for f in ["stance_quant_v2.py", "run_pipeline_v2.py"]
    )
    if not v2_ok:
        print("  [WARN] v2 核心文件缺失!")
    else:
        print("  [OK] v2 核心文件就位")

    print()
    print("=" * 50)
    print(f"Setup 完成: 提取 {extracted} 个文件, 跳过 {skipped} 个")
    print()
    print("运行完整管线:")
    print('  python run_pipeline_v2.py --topic "你的研究课题"')
    print('  python run_pipeline_v2.py --topic "..." --shadow')
    print('  python run_pipeline_v2.py --topic "..." --real-stop --max-rounds 8')
    print("=" * 50)


if __name__ == "__main__":
    force = "--force" in sys.argv
    setup(force=force)
