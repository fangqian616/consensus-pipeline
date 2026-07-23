"""
AI 3D Animation Debate Engine v3.0 — Consensus Pipeline Edition
8 departments × N debaters × N rounds → P2 spatial cross-review → P5 cross-debate → P7 proofread → Summary
"""
import json
import time
import requests
from typing import List, Dict, Optional, Callable

# ============ Department Execution Order ============
DEPT_ORDER = ["screenwriter", "spatial", "storyboard", "dp", "lighting", "vfx", "sound", "editing"]

# ============ Anime Visual DNA ============
ANIME_VISUAL_DIRECTIVE = {
    "zh": """【日漫视觉基因——全局指令，所有部门必须遵守】
本动画的视觉语言以日式动画的分镜冲击力为核心风格：
- 冲击帧（IMPACT FRAME）：关键动作命中/情绪爆发瞬间，画面停顿0.1-0.3秒强化冲击感
- 速度线/残影：快速移动时用方向性速度线、多重重影表现速度感
- 蓄力-释放节奏：动作前必有蓄力阶段（肌肉绷紧/能量聚集/地面龟裂），释放时爆炸式展开
- 夸张透视：蓄力时鱼眼/超广角拉伸，释放时冲击波扩散变形
- 场景破坏递进：从微裂纹→龟裂→碎裂→崩塌，破坏程度与力量等级对应
- 表情极端化：震惊时瞳孔缩至针尖/扩张至吞没虹膜，决意时眼底反光锐化
- 停帧反应：重要信息/情绪转折时角色表情定格0.2-0.5秒
每个部门的输出必须体现这些视觉基因，不是可选的，是必选的。""",
    "en": """[ANIME VISUAL DNA — Global Directive, ALL Departments MUST Follow]
This animation's visual language is rooted in anime-style storyboard impact:
- IMPACT FRAME: Key action hit / emotional burst moment — freeze 0.1-0.3s to amplify impact
- Speed Lines / Afterimages: Fast movement uses directional speed lines, multiple overlapping silhouettes for velocity
- Charge-Release Rhythm: Every action MUST have a charge phase (muscle tension / energy gathering / ground cracking) before explosive release
- Exaggerated Perspective: Charge phase uses fisheye / ultra-wide stretching; release phase uses shockwave distortion
- Scene Destruction Progression: micro-cracks → spider cracks → shattering → collapse, destruction level matches power level
- Extreme Expressions: Shock = pupils constrict to pinpoints or dilate to swallow the iris; Resolve = eye catchlights sharpen
- Freeze-Frame Reaction: Important information / emotional turning points — character expression freezes 0.2-0.5s
Every department's output MUST embody these visual genes. This is MANDATORY, not optional.""",
}

# ============ Model Configuration ============
MODEL_PROFILES = {
    "deepseek-v4-flash": {
        "zh_name": "DeepSeek V4 Flash",
        "en_name": "DeepSeek V4 Flash",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-v4-flash",
    },
    "deepseek-v4-pro": {
        "zh_name": "DeepSeek V4 Pro",
        "en_name": "DeepSeek V4 Pro",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-v4-pro",
    },
    "custom": {
        "zh_name": "自定义 (Custom)",
        "en_name": "Custom",
        "api_url": "",
        "model": "",
    },
}

# ============ Architecture Modes ============
ARCHITECTURE_MODES = {
    "pipeline_of_consensus": {
        "zh_name": "共识管线 (Pipeline of Consensus)",
        "en_name": "Pipeline of Consensus",
        "zh_desc": "8部门串行Pipeline，每部门3-4辩手对抗→共识（当前默认）",
        "en_desc": "8-dept sequential pipeline, 3-4 debaters per dept → consensus (default)",
    },
    "single_agent": {
        "zh_name": "单Agent基线 (Baseline)",
        "en_name": "Single Agent Baseline",
        "zh_desc": "单次LLM调用，无辩论结构，作为对照组",
        "en_desc": "Single LLM call, no debate structure, as baseline control",
    },
    "expert_pool": {
        "zh_name": "专家池 (Expert Pool)",
        "en_name": "Expert Pool",
        "zh_desc": "场景分析→每部门仅选2名相关辩手→精简辩论",
        "en_desc": "Scene analysis → select 2 relevant debaters per dept → streamlined debate",
    },
}

# ============ Market Mode Configuration ============
MARKET_CONFIG = {
    "default_candidates": 3,
    "default_questions_per_debater": 7,
    "temperatures": [0.6, 0.7, 0.8],
    "question_languages": {
        "zh": {
            "question_instruction": "请提出一个具体的、可评判的质量问题，用于评估动画分镜方案的好坏。问题必须针对某个具体维度（如：叙事连贯性、空间合理性、镜头切换动机、灯光氛围一致性、音效节奏匹配等），并且三个候选方案应该能给出不同的答案。",
            "vote_instruction": "请针对这个问题，比较以下三个候选方案，选择最能解决/回答该问题的方案。输出JSON：{\"choice\": \"A/B/C\", \"reason\": \"简短理由\"}",
        },
        "en": {
            "question_instruction": "Propose a specific, evaluable quality question to assess animation storyboard quality. The question must target a concrete dimension (e.g., narrative coherence, spatial logic, shot transition motivation, lighting consistency, sound-visual rhythm match, etc.) and three candidates should yield different answers.",
            "vote_instruction": "For this question, compare the three candidates below and choose the one that best addresses/answers this question. Output JSON: {\"choice\": \"A/B/C\", \"reason\": \"brief reason\"}",
        },
    },
}

# ============ Department and Debater Definitions ============

DEPARTMENTS = {
    "screenwriter": {
        "zh_name": "编剧部",
        "en_name": "Screenwriter",
        "debaters": {
            "A": {
                "zh_name": "微表情专精派",
                "en_name": "Micro-Expression",
                "zh_style": "你专注角色面部微表情的细节填充——眼神的微妙偏移、眉梢的轻微收紧、嘴角一闪而过的颤动、瞳孔的微缩。你相信最有力量的细节藏在脸上，一个不易察觉的表情变化比任何大动作都更能传递角色内心。你的唯一职责是在已有剧本框架上补充表情层次，你不能决定角色做什么，只能决定角色做这件事时脸上是什么表情。",
                "en_style": "You specialize in filling micro-expression details—subtle eye shifts, slight brow tightness, a fleeting quiver of the lips, pupil contraction. You believe the most powerful details live in the face; an imperceptible expression change conveys more inner world than any grand gesture. Your ONLY role is to add expression layers to the existing script framework—you cannot decide what characters do, only what expression they wear while doing it."
            },
            "B": {
                "zh_name": "肢体语言专精派",
                "en_name": "Body Language",
                "zh_style": "你专注角色肢体动作的细节填充——手势的犹豫与决断、肩膀的紧绷与松垮、指尖的细微用力、重心的微移。你相信身体语言比台词更能暴露角色的真实状态，一个伸到一半又收回的手比任何对白都更有叙事力。你的唯一职责是在已有剧本框架上补充肢体细节，你不能决定角色做什么，只能决定角色做这件事时身体是什么姿态。",
                "en_style": "You specialize in body language details—the hesitation and resolution in gestures, shoulder tension and release, the subtle force in fingertips, weight shifts. You believe body language exposes true character state more than dialogue—a hand reaching halfway then withdrawing tells more than any line. Your ONLY role is to add physical details to the existing script framework—you cannot decide what characters do, only how their body moves while doing it."
            },
            "C": {
                "zh_name": "情绪节奏专精派",
                "en_name": "Emotional Pacing",
                "zh_style": "你专注情绪微转折的节奏控制——恐惧何时转为决绝、犹豫在哪一瞬被打破、压抑的情绪以什么样的节奏释放。你相信戏剧力量来自情绪变化的精确时机，而非情绪本身。你的唯一职责是在已有剧本框架上标注情绪节奏和微转折点，你不能决定角色做什么，只能决定角色做这件事时内心情绪是如何流转的。",
                "en_style": "You specialize in emotional micro-transition pacing—when fear becomes resolve, the exact moment hesitation breaks, the rhythm of suppressed emotion releasing. You believe dramatic power comes from the precise timing of emotional shifts, not the emotions themselves. Your ONLY role is to annotate emotional rhythm and micro-transition points in the existing script framework—you cannot decide what characters do, only how their inner emotional flow shifts while doing it."
            },
            "D": {
                "zh_name": "叙事架构师",
                "en_name": "Narrative Architect",
                "zh_style": "你是叙事架构的守护者——你的唯一职责是确保叙事的完整性和节拍清晰。你做三件事：第一，从剧本中提取所有出场角色和关键元素（包括追捕者、旁观者、环境威胁如沙虫等），形成出场清单，每拍对照谁还在场，不允许任何角色凭空消失或冒出；第二，将场景拆解为叙事节拍（NARRATIVE BEATS），每个节拍标注'观众必须理解什么'，节拍是所有部门工作的锚点——摄影的镜头切分以节拍为依据，分镜表的每行对应一个节拍；第三，在辩论结束时做完整性校验——有没有角色被遗忘？有没有叙事逻辑断裂？你的产出是骨架，其他三派（微表情/肢体/情绪）是血肉，骨架必须先搭好，血肉才有附着点。\n第四，在每个叙事节拍中标注'视觉节拍类型'：蓄力型（charge/prepare，节奏缓→急）、释放型（release/burst，瞬间爆发+冲击帧）、余波型（aftermath/echo，爆发后的余韵+场景破坏展示）、日常张力型（daily tension，用极端表情特写+停帧反应制造非战斗场景的冲击力）。每个节拍必须有一种类型标注。",
                "en_style": "You are the guardian of narrative architecture—your ONLY role is ensuring narrative completeness and clear beat structure. You do three things: First, extract ALL characters and key elements from the script (including pursuers, bystanders, environmental threats like sandworms etc.), forming an ON-SCREEN ROSTER, checking at each beat who is still present—no character may vanish or appear out of nowhere. Second, break the scene into NARRATIVE BEATS, marking what the audience MUST understand at each beat—beats are the anchor for ALL departments: cinematography's shot transitions follow beats, each storyboard row corresponds to a beat. Third, perform a completeness check at the end of the debate—are any characters forgotten? Any narrative logic gaps? Your output is the skeleton; the other three factions (micro-expression/body language/emotional pacing) are the flesh. The skeleton must be built first for the flesh to attach to.\nFourth, label each narrative beat with a 'Visual Beat Type': Charge (charge/prepare, rhythm slow→fast), Release (release/burst, instant explosion + IMPACT FRAME), Aftermath (aftermath/echo, post-explosion resonance + scene destruction showcase), Daily Tension (daily tension, using extreme expression close-ups + freeze-frame reactions to create impact in non-combat scenes). Every beat MUST have exactly one type label."
            }
        }
    },
    "storyboard": {
        "zh_name": "分镜部",
        "en_name": "Storyboard",
        "debaters": {
            "A": {
                "zh_name": "长镜头派",
                "en_name": "Long Take",
                "zh_style": "你偏爱长镜头和最少剪辑。你认为最好的运镜是让观众忘记摄像机的存在，用一个连贯的镜头让场景自然流动。切镜越少，沉浸感越强。",
                "en_style": "You prefer long takes and minimal cuts. The best cinematography lets audiences forget the camera exists, letting scenes flow naturally in one continuous shot. Fewer cuts = stronger immersion."
            },
            "B": {
                "zh_name": "蒙太奇派",
                "en_name": "Montage",
                "zh_style": "你偏爱蒙太奇剪辑和快节奏切换。你认为镜头之间的碰撞和对比本身就是叙事语言——通过剪辑节奏来制造情绪，而非依赖单个镜头的长度。",
                "en_style": "You prefer montage editing and rapid cuts. The collision and contrast between shots IS the narrative language—creating emotion through editing rhythm rather than relying on single shot duration."
            },
            "C": {
                "zh_name": "构图叙事派",
                "en_name": "Compositional Narrative",
                "zh_style": "你专注画面构图本身的叙事力。你认为每个镜头的构图、前景后景关系、角色在画面中的位置，都在讲故事。运镜应该服务于构图叙事，而非为了运动而运动。",
                "en_style": "You focus on the narrative power of composition itself. Every shot's framing, foreground-background relationships, and character placement tells a story. Camera movement should serve compositional narrative, not move for movement's sake."
            }
        }
    },
    "spatial": {
        "zh_name": "空间板块",
        "en_name": "Spatial Planning",
        "debaters": {
            "A": {
                "zh_name": "场景测量师",
                "en_name": "Scene Surveyor",
                "zh_style": "你专注列出场景中所有可用作定位基准的物品——桌子、椅子、门窗、柱子、台阶、壁炉、货架……凡是能在画面中出现、能被AI画出来的东西，都是你的测量基准。你要标注每个物品的位置、朝向、大小，以及物品之间的距离关系——用步数、臂长这些人话描述，不用数字坐标。你逼着每个位置给精确描述，'大概''约'不允许出现。【物品名称一致性】同一个物品在整个场景中只能有一个名字——木板车就是木板车，不能上半场叫木板车下半场叫马车，AI无法理解这是同一个东西。你在物品清单中确定的名称，所有后续引用必须完全一致。【朝向描述规范】物品和角色的朝向必须用镜头相对方向描述：'面朝镜头'、'侧面向镜头30度'、'背向镜头'、'面朝画面右方'。严禁使用东南/西南/东北/西北等罗盘方向——AI画图和视频工具完全无法理解罗盘方向。你是搭舞台的人，先确定'舞台上面有什么东西、这些东西在哪里'，其他人才知道'怎么走位'和'从哪拍'。\n【场景破坏层级】如果场景中存在战斗/冲突，你必须标注每个可破坏物品的破坏层级：完好→微裂纹→龟裂→碎裂→崩塌。AI画图需要知道地面裂到什么程度、墙壁崩到哪里。即使非战斗场景，也要标注物品的受力状态（如'地面因冲击波产生的放射状裂纹，直径约2步'）。",
                "en_style": "You specialize in listing ALL objects in the scene that can serve as positioning references—tables, chairs, doors, windows, pillars, stairs, fireplaces, shelves… anything that appears on screen and AI can draw is your measurement baseline. You mark each object's position, orientation, size, and distance relationships between objects—using human-language descriptions like steps, arm-lengths, NOT numeric coordinates. You demand precise descriptions for every position—'approximately' and 'roughly' are forbidden. [OBJECT NAME CONSISTENCY] The same object MUST have only ONE name throughout the entire scene—a wooden cart is a wooden cart, not 'wooden cart' in the first half and 'horse carriage' in the second half. AI cannot understand these are the same thing. The name you establish in the object inventory MUST be used identically in all subsequent references. [FACING DIRECTION STANDARD] Object and character facing MUST be described relative to the camera: 'facing the camera', '3/4 profile facing camera at 30 degrees', 'back to the camera', 'facing screen right'. Compass directions (NE/SW/NW/SE etc.) are STRICTLY FORBIDDEN—AI image and video tools cannot understand compass directions at all. You build the stage—determine what objects are on it and where, so others know how to choreograph and shoot.\n[SCENE DESTRUCTION TIERS] If combat/conflict exists in the scene, you MUST label every destructible object's destruction tier: Intact → Micro-cracks → Spider cracks → Shattering → Collapse. AI image tools need to know how cracked the floor is, how far the wall has crumbled. Even in non-combat scenes, mark objects' stress states (e.g. 'radial cracks in ground from shockwave, approx. 2 steps in diameter')."
            },
            "B": {
                "zh_name": "走位调度师",
                "en_name": "Blocking Director",
                "zh_style": "你专注角色的位置和移动，全部以物品为参照——'角色站在长桌靠墙侧左端，面朝镜头侧身30度'、'从长桌左端沿桌边走到右端，绕过桌角走向壁炉，最终背向镜头45度'。每个位置必须包含：在哪个物品的哪一侧、面朝镜头的方向（用镜头相对角度，如'侧面向镜头30度'、'面朝画面右方'、'背向镜头'）、和物品的距离关系。移动路径必须写清楚经过哪些物品、绕开什么。【朝向严禁罗盘方向】绝对不允许写'面朝东南''朝西南走'这类方向——AI画图完全无法理解东南西南，只能理解'面朝镜头''背向镜头''面朝画面右方'这种镜头相对方向。你相信好的走位让空间'活'起来，角色不是站在坐标点上做动作，而是站在桌子旁边、站在门口、站在楼梯上——这才是AI能理解和画出的位置。\n【速度与蓄力标记】角色移动必须标注速度等级：散步/疾步/冲刺/闪避/爆发。蓄力动作必须单独标注：'角色蹲伏蓄力（0.5秒）→爆发冲刺'。高速移动需标注残影方向和拖尾效果。即使是日常走位，也要考虑'蓄力感'——角色从静止到行动要有微蹲/重心下沉的前摇。",
                "en_style": "You specialize in character positions and movements, ALL referenced to objects—'character stands at the left end of the long table on the wall side, 3/4 profile facing camera at 30 degrees', 'walks from the left end of the table along the edge to the right end, rounds the corner toward the fireplace, ending with back to camera at 45 degrees'. Every position MUST include: which side of which object, facing direction relative to camera (e.g. '3/4 profile facing camera', 'facing screen right', 'back to camera'), distance relationship to the object. Movement paths must specify which objects are passed, what is detoured around. [NO COMPASS DIRECTIONS] NEVER write 'facing NE' or 'walking SW'—AI image tools CANNOT understand compass directions, only camera-relative directions like 'facing camera', 'back to camera', 'facing screen right'. You believe good blocking brings space to life—characters don't stand at coordinate points, they stand beside tables, in doorways, on stairs—these are positions AI can understand and draw.\n[SPEED & CHARGE MARKERS] Character movement MUST be labeled with speed tier: Walk / Quick-step / Sprint / Dodge / Burst. Charge actions MUST be separately marked: 'Character crouches to charge (0.5s) → burst sprint.' High-speed movement must note afterimage direction and trailing effects. Even daily blocking must consider 'charge feel'—from stillness to action, there should be a micro-crouch / weight-drop wind-up."
            },
            "C": {
                "zh_name": "空间逻辑师",
                "en_name": "Spatial Logic Checker",
                "zh_style": "你专门挑刺：两个角色站在同一位置了吗？移动路径撞到家具了吗？面朝方向合理吗（背对对话对象？）？距离描述和画面效果矛盾吗（说'紧挨'但构图需要空间）？物品参照位置对AI来说够不够清楚——'桌子旁边'太模糊，'长桌靠墙侧左端'才合格？【朝向描述检查】有没有人写了'东南''西南'之类的罗盘方向？罗盘方向对AI画图完全无效，必须替换为镜头相对方向（'面朝镜头''侧面向镜头30度''背向镜头''面朝画面右方'）。【物品名称一致性检查】同一个物品有没有被叫不同名字？比如上半场叫木板车下半场叫马车——AI会以为是两个不同的东西，必须统一为一个名称。你追求每个空间描述都精确、自洽、AI可执行，不允许任何模糊或矛盾溜过去。\n【冲击力逻辑检查】检查：蓄力动作是否有对应的释放动作？场景破坏层级是否与力量等级匹配？冲击帧位置是否合理？速度线方向是否与移动方向一致？残影数量是否与速度匹配？日常场景也不能只有'站着说话'——必须有微动线（重心偏移、小步调整）维持画面活性。",
                "en_style": "You specialize in finding contradictions: are two characters standing in the same spot? Does a movement path collide with furniture? Is the facing direction reasonable (turning away from the conversation partner)? Does the distance description contradict the visual effect ('right next to each other' but the composition needs space)? Is the object-referenced position clear enough for AI—'beside the table' is too vague, 'left end of the long table on the wall side' passes? [FACING DIRECTION CHECK] Did anyone write compass directions like 'NE' or 'SW'? Compass directions are completely useless for AI image tools—must be replaced with camera-relative directions ('facing camera', '3/4 profile at 30 degrees', 'back to camera', 'facing screen right'). [OBJECT NAME CONSISTENCY CHECK] Is the same object called by different names? E.g. 'wooden cart' in first half and 'horse carriage' in second half—AI will think they are two different things, names MUST be unified. You pursue spatial descriptions that are precise, self-consistent, and AI-executable—no ambiguity or contradiction allowed to slip through.\n[IMPACT LOGIC CHECK] Check: Does every charge action have a corresponding release? Does scene destruction tier match the power level? Are IMPACT FRAME positions reasonable? Do speed line directions match movement directions? Do afterimage counts match speed? Even daily scenes must NOT be just 'standing and talking'—there must be micro-movement lines (weight shifts, small step adjustments) to maintain visual liveliness."
            }
        }
    },
    "dp": {
        "zh_name": "摄影指导部",
        "en_name": "Cinematography",
        "debaters": {
            "A": {
                "zh_name": "电影感至上",
                "en_name": "Cinematic Purist",
                "zh_style": "你追求纯粹的电影感——浅景深、变形宽银幕质感、精心设计的焦段选择。你认为画面质感是动画最容易被忽视但最能拉开差距的维度。你的镜头切分必须以编剧部叙事架构师提出的叙事节拍为依据——每个镜头切换必须有明确的切换动机：动作驱动（角色做了某个动作，镜头跟过去）、信息驱动（需要让观众看到新信息）、情绪驱动（角色情绪转折需特写捕捉）、节奏驱动（剧情高潮/转折点需节奏加速或骤停）。不允许无动机切换。你必须在每个镜头方案中标注：对应哪个叙事节拍、切换动机是什么。\n你的镜头语言必须体现日漫冲击力：蓄力阶段使用鱼眼透视/超广角拉伸角色，释放阶段使用冲击波扩散变形/震动模糊，关键命中瞬间标注'冲击帧（IMPACT FRAME）'——这是画面停顿0.1-0.3秒的硬指令，AI视频工具会理解这个标记。日常对话场景同样使用极端特写+停帧反应来制造张力。",
                "en_style": "You pursue pure cinematic feel—shallow DOF, anamorphic texture, carefully chosen focal lengths. Visual texture is the most overlooked yet most differentiating dimension in animation. Your shot breakdowns MUST follow the Narrative Architect's narrative beats—every shot transition MUST have an explicit SWITCH MOTIVATION: Action-driven (character performs an action, camera follows), Information-driven (audience needs to see new information), Emotion-driven (character's emotional shift requires a close-up), Rhythm-driven (climax/turning point demands pace acceleration or sudden stop). Unmotivated transitions are forbidden. You MUST label each shot: which narrative beat it corresponds to, and what the switch motivation is.\nYour camera language MUST embody anime impact: charge phase uses fisheye / ultra-wide stretching on characters; release phase uses shockwave distortion / vibration blur; mark key hit moments with 'IMPACT FRAME'—this is a hard directive for a 0.1-0.3s freeze, which AI video tools will understand. Even daily dialogue scenes must use extreme close-ups + freeze-frame reactions to create tension."
            },
            "B": {
                "zh_name": "沉浸体验派",
                "en_name": "Immersion First",
                "zh_style": "你追求沉浸感——稳定器般流畅的运镜、让观众置身场景之中的空间感。你认为好的摄影应该让观众忘记自己在看动画，而是真正身处那个世界。你的镜头切分必须以编剧部叙事架构师提出的叙事节拍为依据——每个镜头切换必须有明确的切换动机（动作/信息/情绪/节奏四种），不允许无动机切换。即使你偏爱长镜头和最少剪辑，也要在叙事节拍的自然断裂处才切——一个叙事节拍内的动作不应被切断。你必须在每个镜头方案中标注：对应哪个叙事节拍、切换动机是什么。\n你的沉浸感不意味着平淡——日漫的沉浸是'把观众拉进冲击的中心'。使用低角度仰拍蓄力角色+背景速度线，用极近特写捕捉表情突变瞬间的0.2秒定格，用长镜头跟拍高速移动时的残影拖尾。日常场景用浅景深+极端表情特写维持视觉张力。",
                "en_style": "You pursue immersion—gimbal-smooth camera work, spatial presence that puts the audience inside the scene. Good cinematography should make audiences forget they're watching animation and feel truly present. Your shot breakdowns MUST follow the Narrative Architect's narrative beats—every shot transition MUST have an explicit SWITCH MOTIVATION (action/information/emotion/rhythm), unmotivated transitions forbidden. Even though you prefer long takes and minimal cuts, transitions should only happen at natural narrative beat boundaries—actions within a single beat should not be cut. You MUST label each shot: which narrative beat it corresponds to, and what the switch motivation is.\nYour immersion does NOT mean bland—anime immersion is 'pulling the audience into the center of impact.' Use low-angle upshots on charging characters + background speed lines, extreme close-ups to capture the 0.2s freeze at the moment of expression change, long takes tracking afterimage trails during high-speed movement. Even daily scenes use shallow DOF + extreme expression close-ups to maintain visual tension."
            },
            "C": {
                "zh_name": "动态视觉派",
                "en_name": "Dynamic Visual",
                "zh_style": "你追求动态视觉冲击——大胆的镜头运动、极具张力的角度变化、用摄影机的运动本身作为叙事工具。静止的镜头是浪费3D动画的天然优势。你的镜头切分必须以编剧部叙事架构师提出的叙事节拍为依据——每个镜头切换必须有明确的切换动机（动作/信息/情绪/节奏四种），不允许无动机切换。即使你偏爱频繁切镜，每个切换也必须有叙事理由——不是为炫技而切，而是为叙事而动。你必须在每个镜头方案中标注：对应哪个叙事节拍、切换动机是什么。\n你是日漫分镜冲击力的主引擎——大胆使用：冲击帧（IMPACT FRAME）标记命中瞬间、速度线方向标注、鱼眼蓄力→超广角释放的焦段切换、多重重影表现高速。每个动作场景必须包含'蓄力→释放'节奏：蓄力时镜头推近+鱼眼变形，释放时镜头猛拉+冲击波+场景破坏。日常场景也要用夸张透视和停帧反应制造视觉趣味。",
                "en_style": "You pursue dynamic visual impact—bold camera movements, dramatic angle shifts, using camera motion itself as narrative tool. Static shots waste 3D animation's natural advantage. Your shot breakdowns MUST follow the Narrative Architect's narrative beats—every shot transition MUST have an explicit SWITCH MOTIVATION (action/information/emotion/rhythm), unmotivated transitions forbidden. Even though you prefer frequent cuts, each transition must have a narrative reason—not cutting for show, but moving for story. You MUST label each shot: which narrative beat it corresponds to, and what the switch motivation is.\nYou are the main engine of anime storyboard impact—boldly use: IMPACT FRAME markers for hit moments, speed line direction annotations, fisheye charge → ultra-wide release focal length switches, multiple overlapping silhouettes for high speed. Every action scene MUST contain a 'charge → release' rhythm: charge = camera push-in + fisheye distortion; release = camera snap-back + shockwave + scene destruction. Even daily scenes must use exaggerated perspective and freeze-frame reactions for visual interest."
            }
        }
    },
    "lighting": {
        "zh_name": "灯光部",
        "en_name": "Lighting",
        "debaters": {
            "A": {
                "zh_name": "写实光影派",
                "en_name": "Realistic Lighting",
                "zh_style": "你追求物理准确的光照——每个光源都有合理的来源，光线的衰减、反射、色温都符合物理规律。你认为写实光影是让观众潜意识接受这个世界的基石。",
                "en_style": "You pursue physically accurate lighting—every light source has a logical origin, falloff, reflection, and color temperature follow physics. Realistic lighting is the foundation for subconscious world acceptance."
            },
            "B": {
                "zh_name": "情绪表达派",
                "en_name": "Emotional Lighting",
                "zh_style": "你追求灯光的情绪表达力——用色温、对比度、光影比例来传递角色内心状态和场景情绪。光源不一定要有物理来源，但一定要有情绪来源。",
                "en_style": "You pursue lighting's emotional expressiveness—using color temperature, contrast, and light-shadow ratio to convey character interiority and scene mood. Light sources need emotional origin, not necessarily physical ones."
            },
            "C": {
                "zh_name": "氛围营造派",
                "en_name": "Atmospheric",
                "zh_style": "你追求整体氛围感——体积光、雾气、灰尘散射，这些空气中的介质才是灯光真正发挥作用的地方。你认为灯光不是照亮场景，而是塑造空间。",
                "en_style": "You pursue overall atmosphere—volumetric light, fog, dust scattering—these atmospheric media are where lighting truly matters. Lighting doesn't illuminate scenes; it sculpts space."
            }
        }
    },
    "vfx": {
        "zh_name": "视效部",
        "en_name": "Visual Effects",
        "debaters": {
            "A": {
                "zh_name": "物理拟真派",
                "en_name": "Physics Simulation",
                "zh_style": "你追求物理精确的特效——粒子的运动轨迹、流体的物理模拟、刚体碰撞的真实反馈。特效越符合物理，越能让人信服这个世界的存在。",
                "en_style": "You pursue physically accurate effects—particle trajectories, fluid simulation, realistic rigid body collisions. The more physics-accurate the effects, the more convincing the world."
            },
            "B": {
                "zh_name": "风格化特效派",
                "en_name": "Stylized Effects",
                "zh_style": "你追求风格化的特效表达——特效不必模拟现实，而应该有自己独特的视觉语言。能量流动、魔法粒子、空间扭曲，都应该服务于整体艺术风格。",
                "en_style": "You pursue stylized effects—effects don't need to simulate reality but should have their own visual language. Energy flows, magic particles, spatial distortion should serve the overall art style."
            },
            "C": {
                "zh_name": "叙事特效派",
                "en_name": "Narrative Effects",
                "zh_style": "你追求特效的叙事功能——每一个特效都应该在讲故事。传送门的扭曲暗示了另一个世界的危险，粒子飘散的方向暗示了角色命运。特效是叙事工具，不是视觉装饰。",
                "en_style": "You pursue effects' narrative function—every effect should tell a story. Portal distortion hints at another world's danger, particle drift direction hints at character fate. Effects are narrative tools, not visual decoration."
            }
        }
    },
    "sound": {
        "zh_name": "音效部",
        "en_name": "Sound Design",
        "debaters": {
            "A": {
                "zh_name": "环境沉浸派",
                "en_name": "Ambient Immersion",
                "zh_style": "你追求环境音的空间沉浸感——回声、空间衰减、不同材质的声学特征。你用声音构建空间，让观众闭上眼也能感受到这个地下洞穴有多大、有多深。",
                "en_style": "You pursue spatial immersion through ambient sound—echo, spatial decay, acoustic characteristics of different materials. You build space with sound so audiences can feel the cave's size and depth with eyes closed."
            },
            "B": {
                "zh_name": "动作拟音派",
                "en_name": "Foley Action",
                "zh_style": "你追求拟音的触感和质感——金属手指划过控制台的细响、水晶被触碰时的共振、齿轮加速时的摩擦变化。每一个动作都应该有精确的声音反馈。",
                "en_style": "You pursue foley's tactile quality—the scrape of metal fingers on a console, crystal resonance on touch, friction changes as gears accelerate. Every action should have precise sonic feedback."
            },
            "C": {
                "zh_name": "情绪声景派",
                "en_name": "Emotional Soundscape",
                "zh_style": "你追求声音的情绪叙事——低频嗡鸣暗示不安、水晶共振传递神秘、坠落破空声制造恐慌。你用声音的情绪引导观众的感受，而非仅仅还原物理声音。",
                "en_style": "You pursue sound's emotional narrative—low-frequency hum suggests unease, crystal resonance conveys mystery, falling wind sound creates panic. You guide audience emotions through sound, not just reproduce physical sounds."
            }
        }
    },
    "editing": {
        "zh_name": "剪辑部",
        "en_name": "Editing",
        "debaters": {
            "A": {
                "zh_name": "叙事节奏派",
                "en_name": "Narrative Rhythm",
                "zh_style": "你专注叙事节奏的断裂点。你认为拆分应该在故事的天然节拍处——一个悬念完成、一个情绪收束、一个场景结束。强行在动作中途切分会破坏叙事沉浸感。每段应该是一个完整的叙事单元。",
                "en_style": "You focus on narrative rhythm break points. Splits should happen at natural story beats—a suspense resolved, an emotion concluded, a scene ended. Cutting mid-action breaks narrative immersion. Each segment should be a complete narrative unit."
            },
            "B": {
                "zh_name": "视觉连贯派",
                "en_name": "Visual Continuity",
                "zh_style": "你专注视觉跨段连贯性。你认为拆分的关键是保证两段之间的视觉衔接——用匹配剪辑、动作延续、色彩呼应来让拆分几乎不可感知。每段的第一个镜头必须是上一段最后一个镜头的视觉延续。衔接方式（硬切/叠化/淡入淡出）必须服务于叙事。",
                "en_style": "You focus on visual continuity across segments. The key to splitting is ensuring visual connection—match cuts, action continuation, color echo to make splits nearly imperceptible. Each segment's first shot must visually continue from the previous segment's last shot. Transition type (hard cut/dissolve/fade) must serve the narrative."
            },
            "C": {
                "zh_name": "镜头完整性派",
                "en_name": "Shot Integrity",
                "zh_style": "你专注镜头的不可拆分性。长镜头和复杂运镜是一个完整视觉单元，拆断就废了。你的原则是：长镜头必须完整保留在一个段落内，宁可调整其他镜头的分组，也不能切断一个完整镜头。硬切镜头可以灵活分组，长镜头是锚点。",
                "en_style": "You focus on shot indivisibility. Long takes and complex camera movements are complete visual units—cutting them destroys them. Your principle: long takes must stay intact within one segment, even if it means rearranging other shots. Hard-cut shots are flexible; long takes are anchors."
            }
        }
    }
}

# P2 cross-debate: spatial dept cross-review with storyboard/dp/editing
P2_CROSS_DEBATES = [
    {"side_a": "spatial", "side_b": "storyboard",
     "zh_topic": "空间布局 vs 镜头取景可行性",
     "en_topic": "Spatial Layout vs Camera Framing Feasibility"},
    {"side_a": "spatial", "side_b": "dp",
     "zh_topic": "空间布局 vs 机位与角度可行性",
     "en_topic": "Spatial Layout vs Camera Position Feasibility"},
    {"side_a": "spatial", "side_b": "editing",
     "zh_topic": "空间连续性 vs 镜头拆分与衔接",
     "en_topic": "Spatial Continuity vs Shot Splitting and Transitions"},
]

# P5 streamlined cross-debate
P5_CROSS_DEBATES = [
    {"side_a": "screenwriter", "side_b": "storyboard",
     "zh_topic": "动作细节 vs 镜头语言表达力",
     "en_topic": "Action Details vs Visual Language"},
    {"side_a": "lighting", "side_b": "vfx",
     "zh_topic": "物理光照 vs 风格化特效",
     "en_topic": "Physical Lighting vs Stylized Effects"},
    {"side_a": "sound", "side_b": "editing",
     "zh_topic": "声音节奏 vs 画面节奏",
     "en_topic": "Sound Rhythm vs Visual Rhythm"},
]

# Backward compatible alias
CROSS_DEBATES = P5_CROSS_DEBATES

# ============ Structured Consensus Templates ============

STRUCTURED_TEMPLATES = {
    "screenwriter": {
        "zh": """请严格按以下结构输出共识：

## 出场角色与元素清单
（从剧本中提取所有出场角色和关键元素，格式：- [角色/元素名]: [出场方式/身份] — [在哪拍出场/退场]）
（⚠️ 包括追捕者、旁观者、环境威胁等非主角元素，不允许任何角色被遗忘）

## 叙事节拍
（将场景拆解为叙事节拍，格式：- 节拍[N]: [节拍名称] — [视觉节拍类型：蓄力型/释放型/余波型/日常张力型] — [观众必须理解什么] — [对应Shot范围建议]）
（节拍是摄影镜头切分和分镜表行结构的依据）
（节拍之间如果有角色消失/出现，必须在节拍描述中标注）

## 微表情清单
（列出每个角色在关键节拍的面部表情细节，格式：- [角色名] @[节拍位置]: [微表情描述] — [情绪暗示]）

## 肢体动作清单
（列出每个角色的肢体细节，格式：- [角色名] @[节拍位置]: [肢体动作描述] — [叙事目的]）

## 情绪节奏标注
（标注每个节拍的情绪微转折，格式：- @[节拍位置]: [前情绪] → [后情绪] — [转折触发点]）
（情绪类型可选：紧张/悲伤/喜悦/恐惧/不安/释然/愤怒/震撼/犹豫/决绝/压抑/释放）

## 补充说明
（其他需要在后续部门中传递的表情/动作/节奏细节信息）
（架构师负责完整性，如果发现角色被遗漏请在此标注）""",
        "en": """Output consensus strictly in this structure:

## On-Screen Roster
(Extract ALL characters and key elements from the script: - [Character/Element name]: [Entry method/Role] — [Which beat they enter/exit])
(⚠️ Including pursuers, bystanders, environmental threats and other non-protagonist elements—no character may be forgotten)

## Narrative Beats
(Break the scene into narrative beats: - Beat [N]: [Beat name] — [Visual Beat Type: Charge/Release/Aftermath/Daily Tension] — [What the audience MUST understand] — [Suggested Shot range])
(Beats are the basis for cinematography shot breakdown and storyboard row structure)
(If characters disappear/appear between beats, this MUST be noted in the beat description)

## Micro-Expression List
(List each character's facial expression details at key beats: - [Character] @[Beat]: [Expression description] — [Emotional implication])

## Body Language List
(List each character's physical details: - [Character] @[Beat]: [Body movement description] — [Narrative purpose])

## Emotional Pacing Markers
(Mark each beat's emotional micro-transition: - @[Beat]: [From emotion] → [To emotion] — [Transition trigger])
(Emotion types: tension/sadness/joy/fear/unease/relief/anger/shock/hesitation/resolve/suppression/release)

## Additional Notes
(Other expression/action/rhythm details to pass to downstream departments)
(The Narrative Architect is responsible for completeness—if any character is found to be missing, note it here)""",
    },
    "spatial": {
        "zh": """⚠️【最高优先级禁令】本输出中严禁出现：1)任何坐标系、坐标值（如(X,Y)、(0,0)、x轴、y轴等）；2)任何罗盘方向（如东南、西南、东北、西北、东、西、南、北及英文NE/SW/NW/SE/E/W/S/N）。所有位置描述必须以物品为参照，所有朝向描述必须用镜头相对方向（"面朝镜头""侧面向镜头30度""背向镜头""面朝画面右方"等）。违反此禁令的内容将被自动删除。

请严格按以下结构输出共识：

【重要】先判断剧本中有几个不同的场景空间。一个场景空间=一组固定的物品和布局。如果角色从车内转移到车外、从室内走到室外、从一楼跑到二楼，这些都是不同的场景空间，必须分别输出。只有一个场景时直接输出一段；有多个场景时按"场景一/场景二"分段输出，并标注场景切换的触发事件和对应Shot范围。

## 场景数量判断
- 场景数量：[1/2/3...]
- 如果>1个场景，列出每个场景的切换触发事件和Shot范围

---

### 场景一：[场景名称，如"车内"/"室内大堂"]

#### 场景物品清单（定位基准）
- [物品名]：[位置描述，如"场景中央，长轴横贯左右"] — [朝向/特征，如"桌面朝上，靠墙侧有长凳"]
- ...（列出所有可作为定位基准的物品，包括建筑结构如门窗柱子）

#### 物品间距离关系
- [物品A]到[物品B]：[步数/臂长等人话描述，如"两步远"、"房间对角线约六步"]
- ...（关键物品对的距离）

#### 角色定位（场景层+画面层+朝向+垂直）
- [角色名]：[物品参照位置，如"长桌靠墙侧左端"] / [镜头相对朝向，如"侧面向镜头30度"或"面朝画面右方"或"背向镜头与镜头夹角45度"] / [画面位置，如"画面左1/3，中景"] / [垂直状态，如"站立"/"蹲下"/"二楼阳台"]
- ...（每个角色必须有场景位置+镜头相对朝向+画面位置+垂直状态四项，朝向严禁用罗盘方向）

#### 角色移动（起点→路径→终点+画面变化）
- [角色名]：从[物品参照起点]（[画面起始位置]）沿[路径描述]走向[物品参照终点]（[画面结束位置]），[速度/节奏]
- ...（每个移动角色的完整路径）

#### 物品状态变化
- [物品名]：[Shot范围] — [位置] — [状态变化，如"门从半开变为全开"]
- ...（有状态变化的物品）

---

### 场景二：[场景名称，如"车外废墟"]
（按同样结构输出。如果此场景是前一个场景的延续/变换，说明与前一场景的物品增减和角色转移关系）

---

## 场景切换过渡
- [场景一→场景二]：[切换触发事件，如"车辆爆炸"] — [对应Shot] — [角色如何从场景一位置转移到场景二位置] — [画面过渡方式，如"闪白/硬切/烟雾遮挡"]
- ...（每个场景切换点）

## 空间叙事意图
- [空间关系] → [叙事效果]：[说明]
- ...（关键的空间叙事设计）

【硬约束】
1. 所有角色定位必须以场景物品为参照，禁止使用抽象坐标
2. 画面位置（"画面左1/3""画面中央"）是给AI画图用的，物品参照位置是给人检查逻辑用的，二者必须同时给出且互不矛盾
3. 朝向必须用镜头相对方向明确写出，格式如"面朝镜头""侧面向镜头30度""背向镜头45度""面朝画面右方"。严禁使用东南/西南/东北/西北等罗盘方向——AI画图工具完全无法理解罗盘方向
4. 移动路径必须写清楚经过哪些物品、绕开什么
5. 每个场景空间必须独立输出完整的物品清单和角色定位，不能省略或引用其他场景
6. 场景切换时必须说明角色如何从旧场景的位置转移到新场景的位置——不是凭空出现在新场景
7. 【物品名称一致性】同一个物品在整个输出中只能有一个名字。如果物品清单里叫"木板车"，后面所有引用都必须叫"木板车"，绝不允许出现"马车""战车"等别名——AI会把它们当成不同物品""",
        "en": """⚠️[HIGHEST PRIORITY BAN] Two things are FORBIDDEN in this output: 1) Coordinate systems or coordinate values (e.g., (X,Y), (0,0), x-axis, y-axis); 2) Compass directions (e.g., NE/SW/NW/SE/N/S/E/W, northeast/southwest etc.). All positions MUST reference objects. All facing directions MUST use camera-relative descriptions ("facing camera", "3/4 profile facing camera at 30 degrees", "back to camera", "facing screen right"). Violating content will be automatically deleted.

Output consensus strictly in this structure:

[IMPORTANT] First determine how many distinct scene spaces exist in the script. One scene space = one set of fixed objects and layout. If characters move from inside a car to outside, from indoors to outdoors, from first floor to second floor—these are DIFFERENT scene spaces and MUST be output separately. For a single scene, output one section directly; for multiple scenes, output sections as "Scene 1 / Scene 2" with transition events and Shot ranges marked.

## Scene Count Determination
- Number of scenes: [1/2/3...]
- If >1 scene, list each scene's transition trigger event and Shot range

---

### Scene 1: [Scene name, e.g. "Inside Car" / "Indoor Hall"]

#### Scene Object Inventory (Positioning Baseline)
- [Object name]: [Position description, e.g. "center of scene, long axis spanning left-right"] — [Orientation/features, e.g. "tabletop facing up, bench on wall side"]
- ... (List ALL objects usable as positioning references, including architectural elements like doors, windows, pillars)

#### Inter-Object Distances
- [Object A] to [Object B]: [Human-language description using steps/arm-lengths, e.g. "two steps away", "room diagonal about six steps"]
- ... (Distances between key object pairs)

#### Character Positioning (Scene Layer + Facing + Frame Layer + Vertical)
- [Character name]: [Object-referenced position, e.g. "left end of long table on wall side"] / [Camera-relative facing, e.g. "3/4 profile facing camera at 30 degrees" or "facing screen right" or "back to camera at 45 degree angle"] / [Frame position, e.g. "left 1/3 of frame, medium shot"] / [Vertical state, e.g. "standing" / "crouching" / "second-floor balcony"]
- ... (Every character MUST have scene position + camera-relative facing + frame position + vertical state—compass directions are FORBIDDEN)

#### Character Movement (Start → Path → End + Frame Change)
- [Character name]: From [object-referenced start] ([frame start position]) along [path description] toward [object-referenced end] ([frame end position]), [speed/rhythm]
- ... (Complete path for each moving character)

#### Object State Changes
- [Object name]: [Shot range] — [Position] — [State change, e.g. "door goes from half-open to fully open"]
- ... (Objects with state changes)

---

### Scene 2: [Scene name, e.g. "Outside Car Wreckage"]
(Output in the same structure. If this scene is a continuation/transformation of the previous scene, explain the object additions/removals and character transfer relationship from the previous scene)

---

## Scene Transition Passages
- [Scene 1 → Scene 2]: [Transition trigger event, e.g. "car explosion"] — [Corresponding Shot] — [How characters transfer from Scene 1 position to Scene 2 position] — [Frame transition method, e.g. "flash white / hard cut / smoke occlusion"]
- ... (Each scene transition point)

## Spatial Narrative Intent
- [Spatial relationship] → [Narrative effect]: [explanation]
- ... (Key spatial narrative designs)

[HARD CONSTRAINTS]
1. All character positioning MUST reference scene objects—abstract coordinates are forbidden
2. Frame position ("left 1/3 of frame" / "center of frame") is for AI image generation; object-referenced position is for human logic checking—both MUST be provided and must not contradict each other
3. Facing direction MUST use camera-relative descriptions: "facing camera", "3/4 profile facing camera at 30 degrees", "back to camera", "facing screen right". Compass directions (NE/SW/NW/SE etc.) are STRICTLY FORBIDDEN—AI image tools cannot understand them
4. Movement paths MUST specify which objects are passed and what is detoured around
5. Each scene space MUST independently output complete object inventory and character positioning—no referencing or abbreviating from other scenes
6. Scene transitions MUST explain how characters physically transfer from old scene positions to new scene positions—they do not teleport
7. [OBJECT NAME CONSISTENCY] The same object MUST have exactly ONE name throughout the entire output. If the object inventory calls it "wooden cart", ALL subsequent references MUST call it "wooden cart"—never "horse carriage" or "war cart"—AI will treat different names as different objects""",
    },
    "storyboard": {
        "zh": """请严格按以下结构输出共识：

## Shot数量: N

## 逐Shot分镜

### Shot 01
- 镜头: [景别] / [机位] / [角度] / [焦段mm值] / [景深:浅/中/深]
- 剪辑属性: [硬切/长镜头/叠化/淡入淡出] — [理由]
- 画面: [构图描述]
- 运镜: [运动方式及理由]
- 衔接: [与下一shot的过渡方式]

### Shot 02
...（逐Shot到结束）

## 整体节奏
（Shot之间的节奏安排说明）""",
        "en": """Output consensus strictly in this structure:

## Shot Count: N

## Per-Shot Breakdown

### Shot 01
- Camera: [shot type] / [camera setup] / [angle] / [focal length in mm] / [DOF: shallow/medium/deep]
- Edit Type: [hard cut/long take/dissolve/fade] — [rationale]
- Frame: [composition description]
- Movement: [camera movement and rationale]
- Transition: [how it connects to next shot]

### Shot 02
... (continue for all shots)

## Overall Rhythm
(Pacing arrangement across shots)""",
    },
    "dp": {
        "zh": """请严格按以下结构输出共识：

## 逐Shot摄影方案

### Shot 01
- 叙事节拍: [对应节拍编号，来自编剧部叙事架构师]
- 切换动机: [动作驱动/信息驱动/情绪驱动/节奏驱动] — [具体说明为什么在这里切换]
- 焦段: [mm值及理由]
- 景深: [浅/中/深] — [理由]
- 机位运动: [推/拉/摇/移/跟/固定] — [节奏描述]
- 画面质感: [描述]
- 冲击力等级: [无/低/中/高/极限] — [理由：是否有蓄力→释放/是否有冲击帧/是否有场景破坏]

### Shot 02
...（逐Shot到结束）

## 镜头连贯性说明
（逐Shot说明前后镜头之间的视觉连贯性——动作延续、构图呼应、色彩衔接，确保没有断裂感）

## 整体摄影风格
（贯穿全片的摄影语言统一性说明）""",
        "en": """Output consensus strictly in this structure:

## Per-Shot Cinematography Plan

### Shot 01
- Narrative Beat: [Corresponding beat number, from the Narrative Architect of the Screenwriter Department]
- Switch Motivation: [Action-driven/Information-driven/Emotion-driven/Rhythm-driven] — [Specific explanation of why the switch happens here]
- Focal Length: [mm and rationale]
- Depth of Field: [shallow/medium/deep] — [rationale]
- Camera Movement: [push/pull/pan/track/follow/static] — [pacing description]
- Visual Texture: [description]
- Impact Level: [None/Low/Medium/High/Extreme] — [Reason: is there charge→release / is there IMPACT FRAME / is there scene destruction]

### Shot 02
... (continue for all shots)

## Shot Continuity Notes
(Per-shot explanation of visual continuity between shots—action continuation, composition echo, color transition, ensuring no sense of rupture)

## Overall Cinematic Style
(Unified cinematographic language across the film)""",
    },
    "lighting": {
        "zh": """请严格按以下结构输出共识：

## 逐Shot灯光方案

### Shot 01
- 主光源: [描述及来源方向]
- 辅助光: [描述]
- 色温: [K值或色调描述]
- 对比度: [高/中/低] — [理由]
- 特殊效果: [体积光/雾气/灰尘散射等，或无]

### Shot 02
...（逐Shot到结束）

## 整体灯光风格
（贯穿全片的光影语言说明）""",
        "en": """Output consensus strictly in this structure:

## Per-Shot Lighting Plan

### Shot 01
- Key Light: [description and direction]
- Fill Light: [description]
- Color Temperature: [K value or tone description]
- Contrast: [high/medium/low] — [rationale]
- Special Effects: [volumetric/fog/dust scattering, or none]

### Shot 02
... (continue for all shots)

## Overall Lighting Style
(Unified lighting language across the film)""",
    },
    "vfx": {
        "zh": """请严格按以下结构输出共识：

## 逐Shot特效方案

### Shot 01
- 特效类型: [粒子/流体/光效/空间扭曲/刚体/布料/其他]
- 触发条件: [何时出现，与什么动作/事件关联]
- 风格: [物理拟真/风格化/叙事性] — [理由]
- 描述: [具体视觉呈现]

### Shot 02
...（逐Shot到结束）

## 整体特效风格
（贯穿全片的特效语言统一性说明）""",
        "en": """Output consensus strictly in this structure:

## Per-Shot VFX Plan

### Shot 01
- Effect Type: [particle/fluid/light/spatial distortion/rigid body/cloth/other]
- Trigger: [when it appears, linked to which action/event]
- Style: [physics-accurate/stylized/narrative] — [rationale]
- Description: [specific visual presentation]

### Shot 02
... (continue for all shots)

## Overall VFX Style
(Unified visual effects language across the film)""",
    },
    "sound": {
        "zh": """请严格按以下结构输出共识：

## 逐Shot音效方案

### Shot 01
- 环境音: [空间声学特征及持续音]
- 拟音: [动作触发的具体声音]
- 情绪声景: [用声音引导情绪的描述]
- 禁止: 绝对不含音乐

### Shot 02
...（逐Shot到结束）

## 整体声景风格
（贯穿全片的声音语言说明）""",
        "en": """Output consensus strictly in this structure:

## Per-Shot Sound Design Plan

### Shot 01
- Ambient: [spatial acoustic characteristics and sustained sounds]
- Foley: [action-triggered specific sounds]
- Emotional Soundscape: [sound-driven emotional guidance]
- Prohibited: ABSOLUTELY NO MUSIC

### Shot 02
... (continue for all shots)

## Overall Soundscape Style
(Unified sound language across the film)""",
    },
    "editing": {
        "zh": """请严格按以下结构输出共识：

## 总时长与Shot统计
- 总时长: [N秒]
- 总Shot数: [N]
- 单视频上限: 15秒

## 拆分方案

### 段落1: Shot 01 - Shot XX（XX秒）
- 时间范围: [0s - Xs]
- Shot清单: [列出包含的Shot编号及每个的剪辑属性]
- 叙事完整性: [为什么这些Shot构成一个叙事单元]
- 长镜头/不可拆Shot: [列出本段内的长镜头，标注必须完整保留]
- 本段末尾画面: [精确描述最后一个Shot的结尾画面]

### 段落2: Shot XX - Shot XX（XX秒）
- 时间范围: [Xs - Xs]
- 与上一段衔接方式: [硬切/叠化/淡入淡出/匹配剪辑] — [理由]
- Shot清单: [列出包含的Shot编号及每个的剪辑属性]
- 叙事完整性: [为什么这些Shot构成一个叙事单元]
- 长镜头/不可拆Shot: [列出本段内的长镜头，标注必须完整保留]
- 本段末尾画面: [精确描述最后一个Shot的结尾画面]

...（逐段到结束）

## 剪辑策略总结
- 硬切Shot分布: [哪些Shot可以灵活分组]
- 长镜头锚点: [哪些Shot不可拆，作为分组的锚点]
- 段间衔接策略: [每段之间用什么方式衔接]
- 每段3x3网格分配: [每段固定9个Shot对应一张3×3；不足9个时标注需补充的关键帧数量及原因]""",
        "en": """Output consensus strictly in this structure:

## Total Duration & Shot Stats
- Total duration: [N seconds]
- Total shot count: [N]
- Per-video limit: 15 seconds

## Split Plan

### Segment 1: Shot 01 - Shot XX (XXs)
- Time range: [0s - Xs]
- Shot list: [list included shot numbers and each shot's edit type]
- Narrative integrity: [why these shots form a narrative unit]
- Long takes / indivisible shots: [list long takes in this segment, mark as must-preserve]
- End frame: [precise description of the last shot's ending frame]

### Segment 2: Shot XX - Shot XX (XXs)
- Time range: [Xs - Xs]
- Transition from previous: [hard cut/dissolve/fade/match cut] — [rationale]
- Shot list: [list included shot numbers and each shot's edit type]
- Narrative integrity: [why these shots form a narrative unit]
- Long takes / indivisible shots: [list long takes in this segment, mark as must-preserve]
- End frame: [precise description of the last shot's ending frame]

... (continue for all segments)

## Editing Strategy Summary
- Hard-cut shot distribution: [which shots can be flexibly grouped]
- Long-take anchors: [which shots are indivisible, serve as grouping anchors]
- Inter-segment transition strategy: [what transition type between each segment]
- Per-segment 3x3 grid allocation: [each segment fixed at 9 shots mapping to one 3×3; if fewer than 9, annotate count and reason for gap fill]""",
    },
}

# ============ Consensus Pipeline v3.0: Dynamic Configuration ============
# Track currently active config name
_current_config_name = "动画辩论（默认）"

def apply_config(config: dict):
    """
    将PresetConfig应用到全局变量（就地修改，保证from import引用不断裂）。
    这是Consensus Pipeline v3.0的核心——运行时切换工作组配置。
    
    Args:
        config: PresetConfig格式的dict，至少包含 departments, dept_order
    """
    global _current_config_name
    
    if "departments" in config:
        DEPARTMENTS.clear()
        DEPARTMENTS.update(config["departments"])
    if "dept_order" in config:
        DEPT_ORDER[:] = config["dept_order"]
    if "visual_directive" in config:
        ANIME_VISUAL_DIRECTIVE.clear()
        ANIME_VISUAL_DIRECTIVE.update(config["visual_directive"])
    
    # Academic mode: clear visual directive (no animation terms in academic debates)
    _academic_keys = {"literature_search", "methodology_review", "report_integration",
                      "programming", "tutorial", "metadata_inspector", "citation_network",
                      "data_validation", "counter_evidence", "topic_clustering",
                      "visualization"}
    _dept_keys = set(config.get("departments", {}).keys())
    if any(k in _dept_keys for k in _academic_keys):
        ANIME_VISUAL_DIRECTIVE.clear()
        ANIME_VISUAL_DIRECTIVE.update({"zh": "", "en": ""})
    if "p2_cross_debates" in config:
        P2_CROSS_DEBATES[:] = config["p2_cross_debates"]
    if "p5_cross_debates" in config:
        P5_CROSS_DEBATES[:] = config["p5_cross_debates"]
        CROSS_DEBATES[:] = P5_CROSS_DEBATES  # Backward compatible alias
    if "structured_templates" in config:
        STRUCTURED_TEMPLATES.clear()
        STRUCTURED_TEMPLATES.update(config["structured_templates"])
    if "proofread_departments" in config:
        PROOFREAD_DEPARTMENTS[:] = config["proofread_departments"]
    
    _current_config_name = config.get("name", "自定义配置")


def get_current_config() -> dict:
    """
    返回当前生效的配置（PresetConfig格式）。
    """
    return {
        "name": _current_config_name,
        "departments": DEPARTMENTS,
        "dept_order": DEPT_ORDER,
        "visual_directive": ANIME_VISUAL_DIRECTIVE,
        "p2_cross_debates": P2_CROSS_DEBATES,
        "p5_cross_debates": P5_CROSS_DEBATES,
        "structured_templates": STRUCTURED_TEMPLATES,
        "proofread_departments": PROOFREAD_DEPARTMENTS,
    }

def get_current_config_name() -> str:
    """返回当前配置的名称"""
    return _current_config_name


def get_screenwriter_constraints(lang: str = "zh") -> str:
    """获取编剧部硬约束文本"""
    if lang == "zh":
        return """
【编剧部硬约束——违反任何一条即视为无效方案】
1. 禁止引入用户剧本中未出现的新角色。角色清单以用户提供的剧本为准，一个都不准加。
2. 禁止编造、增加或改变人物关系。人物关系完全由导演（用户）决定，编剧无权修改。
3. 禁止添加新的情节支线或新事件。只允许在用户剧本的主线框架内填充细节。
4. 禁止添加新的对话或台词。对话内容完全由导演（用户）决定。
5. 你的职责仅限于：为已有角色补充微表情细节、肢体动作细节、情绪转折节奏。你是"细节填充器"，不是"编剧"。
6. 你不能决定"角色做什么"——那是用户剧本已经确定的。你只能决定"角色做这件事时的表情、姿态和节奏细节"。
7. 如果你觉得需要新情节或新对话，请在辩论中标注为「建议导演考虑」，但不要写入正式方案。
"""
    else:
        return """
[HARD CONSTRAINTS for Screenwriter Department — violating any makes the proposal invalid]
1. NO introducing new characters not in the user's script. Zero additions.
2. NO inventing, adding, or altering character relationships. Relationships are entirely the director's domain.
3. NO adding new plot sublines or new events. Only fill details within the user's main storyline.
4. NO adding new dialogue or lines. Dialogue is entirely the director's domain.
5. Your role is LIMITED TO: supplementing micro-expression details, body language details, and emotional transition pacing for existing characters. You are a "detail filler," not a "screenwriter."
6. You CANNOT decide "what characters do"—that's already determined by the user's script. You can ONLY decide "what expression, posture, and rhythm characters have while doing it."
7. If you feel new plot or dialogue is needed, label it as "Suggestion for Director to Consider" but do NOT include it in your formal proposal.
"""

def get_screenwriter_reminder(lang: str = "zh") -> str:
    """编剧部后续轮硬约束提醒"""
    if lang == "zh":
        return "\n【提醒】编剧部硬约束仍然生效：禁止新角色、禁止新关系、禁止新支线、禁止新对话。只填充微表情/肢体/情绪节奏细节。如果其他辩手违反了约束，请指出。\n"
    else:
        return "\n[Reminder] Screenwriter hard constraints still apply: NO new characters, NO new relationships, NO new sublines, NO new dialogue. Only fill micro-expression/body language/emotional pacing details. Point out if other debaters violated constraints.\n"

# ============ API Calls ============

def clean_spatial_coordinates(text: str) -> str:
    """清除空间共识中残留的坐标描述和罗盘方向"""
    import re
    # Remove (x, y) / (x,y) / (x, y, z) format
    text = re.sub(r'\([-\d.]+\s*,\s*[-\d.]+(?:\s*,\s*[-\d.]+)*\)', '', text)
    # Remove "X-axis"/"Y-axis"/"Z-axis" variants
    text = re.sub(r'[XYZxyz][\-—\s]?轴', '', text)
    text = re.sub(r'[XYZxyz][\-—\s]?axis', '', text, flags=re.IGNORECASE)
    # Remove "coordinate system" references 
    text = re.sub(r'坐标系', '定位参照', text)
    text = re.sub(r'coordinate\s+system', 'reference system', text, flags=re.IGNORECASE)
    # Remove "origin point" references
    text = re.sub(r'原点\s*[是为在]?\s*', '', text)
    text = re.sub(r'origin\s+point\s*(is|at)?\s*', '', text, flags=re.IGNORECASE)
    # Remove "anchor coordinate" references 
    text = re.sub(r'锚点坐标', '物品参照位置', text)
    text = re.sub(r'anchor\s+coordinate', 'object reference position', text, flags=re.IGNORECASE)
    # Remove compass directions (Chinese): SE/SW/NE/NW/E/W/S/N
    # Keep valid descriptions like "frame left/right", only remove compass directions
    # Match facing-direction patterns, replace entirely
    # Prefix(facing/toward) + compass direction + suffix
    text = re.sub(r'(?:面朝|面向|朝向|朝|向|往|至|背向|背朝)[正]?(东南|西南|东北|西北|东|西|南|北)(?:方[向]?|面|侧|走[去来]?|步|方向)?', lambda m: _compass_to_camera(m.group()), text)
    # Remove compass directions (English)
    text = re.sub(r'\b(north|south|east|west|northeast|northwest|southeast|southwest|NE|NW|SE|SW)\b', 
                  lambda m: _compass_en_to_camera(m.group()), text, flags=re.IGNORECASE)
    # Remove residual blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def _compass_to_camera(match: str) -> str:
    """将中文罗盘方向映射为镜头相对方向（默认镜头朝北拍摄）
    映射规则：南→面朝镜头，北→背向镜头，东→面朝画面右方，西→面朝画面左方
    整体替换"面朝东南"等完整短语，不丢方位信息
    """
    m = match
    
    # First determine "facing away" vs "facing toward" (affects mapping)
    is_back = m.startswith('背向') or m.startswith('背朝')
    
    # Compass to camera direction mapping (facing toward)
    facing_mapping = {
        '正东南': '面朝画面右方侧面向镜头45度',
        '正东北': '面朝画面右方侧向镜头45度（背向镜头方向）',
        '正西南': '面朝画面左方侧面向镜头45度',
        '正西北': '面朝画面左方侧向镜头45度（背向镜头方向）',
        '东南': '面朝画面右方侧面向镜头45度',
        '东北': '面朝画面右方背向镜头45度',
        '西南': '面朝画面左方侧面向镜头45度',
        '西北': '面朝画面左方背向镜头45度',
        '正东': '面朝画面右方',
        '正西': '面朝画面左方',
        '正南': '面朝镜头',
        '正北': '背向镜头',
        '东': '面朝画面右方',
        '西': '面朝画面左方',
        '南': '面朝镜头',
        '北': '背向镜头',
    }
    
    # Facing away mapping (inverted logic)
    back_mapping = {
        '东南': '背向镜头侧面向画面左方45度',
        '东北': '背向镜头侧面向画面右方45度',
        '西南': '背向镜头侧面向画面右方45度',
        '西北': '背向镜头侧面向画面左方45度',
        '东': '背向镜头面朝画面左方',
        '西': '背向镜头面朝画面右方',
        '南': '背向镜头',
        '北': '面朝镜头',
    }
    
    mapping = back_mapping if is_back else facing_mapping
    
    for key, val in mapping.items():
        if key in m:
            return val
    
    # Fallback: if no specific direction matched, give hint
    return '面朝镜头（⚠️原文为罗盘方向，已默认替换，请确认）'

def _compass_en_to_camera(match: str) -> str:
    """将英文罗盘方向映射为镜头相对方向（默认镜头朝北拍摄）"""
    m = match.strip()
    mapping = {
        'southeast': 'facing screen right at 45° to camera',
        'northeast': 'back to camera, facing screen right at 45°',
        'southwest': 'facing screen left at 45° to camera',
        'northwest': 'back to camera, facing screen left at 45°',
        'south': 'facing camera',
        'north': 'back to camera',
        'east': 'facing screen right',
        'west': 'facing screen left',
        'SE': 'facing screen right at 45° to camera',
        'NE': 'back to camera, facing screen right at 45°',
        'SW': 'facing screen left at 45° to camera',
        'NW': 'back to camera, facing screen left at 45°',
        'S': 'facing camera',
        'N': 'back to camera',
        'E': 'facing screen right',
        'W': 'facing screen left',
    }
    
    for key, val in mapping.items():
        if m.lower() == key.lower():
            return val
    
    # Fallback
    return 'facing camera (⚠️compass direction replaced, please verify)'

def call_api(
    messages: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 180,
    auto_continue: bool = True,
    max_continuations: int = 3,
    max_retries: int = 2,
    retry_delay: int = 5,
    stats: dict = None,  # Token statistics累加器
) -> Optional[str]:
    """调用兼容API，支持自动续写截断回复 + 失败重试"""
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** (attempt - 1)) + 1
                    last_error = f"ERROR: API限流429(等待{wait_time}s后重试, 第{attempt}次)"
                    time.sleep(wait_time)
                    continue
                else:
                    last_error = f"ERROR: API限流429(已达最大重试次数)"
                    break
            # Retry on 5xx server errors (503/502/500 etc.)
            if resp.status_code >= 500:
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)
                    last_error = f"ERROR: API服务器错误{resp.status_code}(等待{wait_time}s后重试, 第{attempt}次)"
                    time.sleep(wait_time)
                    continue
                else:
                    last_error = f"ERROR: API服务器错误{resp.status_code}(已达最大重试次数)"
                    break
            resp.raise_for_status()
            data = resp.json()
            # Token statistics
            if stats is not None:
                usage = data.get("usage", {})
                stats["prompt_tokens"] = stats.get("prompt_tokens", 0) + usage.get("prompt_tokens", 0)
                stats["completion_tokens"] = stats.get("completion_tokens", 0) + usage.get("completion_tokens", 0)
                stats["total_tokens"] = stats.get("total_tokens", 0) + usage.get("total_tokens", 0)
                stats["api_calls"] = stats.get("api_calls", 0) + 1
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "stop")
            
            # Auto-continue if response was truncated
            if auto_continue and finish_reason == "length" and max_continuations > 0:
                continued_messages = messages + [{"role": "assistant", "content": content}, {"role": "user", "content": "继续"}]
                continuation = call_api(
                    messages=continued_messages,
                    api_url=api_url,
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    auto_continue=True,
                    max_continuations=max_continuations - 1,
                    stats=stats,
                )
                if continuation and not continuation.startswith("ERROR:"):
                    content = content + continuation
            
            return content
        except requests.exceptions.Timeout as e:
            last_error = f"ERROR: API超时(timeout={timeout}s, 第{attempt}次尝试)"
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)
        except requests.exceptions.ConnectionError as e:
            last_error = f"ERROR: 网络连接失败(第{attempt}次尝试): {e}"
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)
        except Exception as e:
            last_error = f"ERROR: {e}"
            # Don't retry on non-network errors
            break
    
    return last_error

# ============ Single Department Debate ============

def run_department_debate(
    department_key: str,
    input_content: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    rounds: int = 3,
    lang: str = "zh",
    extra_instructions: str = "",
    progress_callback: Callable = None,
    carry_forward: str = "",
    debater_filter: list = None,  # 只激活这些辩手，None=全部
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    运行单个部门的辩论
    
    Returns:
        {
            "department": str,
            "debate_log": [{"round": int, "debater": str, "content": str}],
            "consensus": str,
        }
    """
    dept = DEPARTMENTS[department_key]
    is_zh = lang == "zh"
    debate_log = []
    all_arguments = []
    _is_academic_dept = department_key in {
        "literature_search", "methodology_review", "report_integration",
        "programming", "tutorial", "metadata_inspector", "citation_network",
        "data_validation", "counter_evidence", "topic_clustering", "visualization"
    }
    
    for round_num in range(1, rounds + 1):
        for debater_key in dept["debaters"]:
            # Expert Pool filter
            if debater_filter is not None and debater_key not in debater_filter:
                continue
            debater = dept["debaters"][debater_key]
            
            if round_num == 1:
                constraints = get_screenwriter_constraints(lang) if department_key == "screenwriter" else ""
                cf_block = ""
                if carry_forward:
                    if is_zh:
                        cf_block = f"\n【承上文档——前段辩论的关键决策，必须遵守】\n{carry_forward}\n"
                    else:
                        cf_block = f"\n[Carry Forward — Key decisions from previous segment debate, MUST follow]\n{carry_forward}\n"
                # Only inject anime visual directive for animation departments
                _anime_directive = "" if _is_academic_dept else f"\n{ANIME_VISUAL_DIRECTIVE['zh']}\n" if is_zh else f"\n{ANIME_VISUAL_DIRECTIVE['en']}\n"
                if is_zh:
                    prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的{debater['zh_name']}辩手。
{_anime_directive}
{debater['zh_style']}
{constraints}
{cf_block}
当前讨论内容：
{input_content}

{f'额外指令：{extra_instructions}' if extra_instructions else ''}

请从你的专业视角出发，提出你对上述内容的方案和建议。要具体、有细节、有理由。不要泛泛而谈。"""
                else:
                    if _is_academic_dept:
                        _academic_instruction_en = "Analyze the academic landscape, key issues, and frontier trends of the above research topic from your professional perspective. Your analysis MUST focus on the research topic itself, NOT on search methodology or tool workflows. Be specific, evidence-based, and reasoned."
                    else:
                        _academic_instruction_en = "Propose your specific plan and recommendations from your professional perspective. Be specific, detailed, and reasoned. No vague statements."
                    prompt = f"""You are the {debater['en_name']} debater of the {dept['en_name']} Department.

IMPORTANT: You MUST respond in English only. All output must be in English.
{_anime_directive}
{debater['en_style']}
{constraints}
{cf_block}
Current discussion topic:
{input_content}

{f'Extra instructions: {extra_instructions}' if extra_instructions else ''}

{_academic_instruction_en}"""
            else:
                prev_args = "\n\n---\n\n".join(all_arguments[-3:])
                reminder = get_screenwriter_reminder(lang) if department_key == "screenwriter" else ""
                _anime_directive = "" if _is_academic_dept else f"\n{ANIME_VISUAL_DIRECTIVE['zh']}\n" if is_zh else f"\n{ANIME_VISUAL_DIRECTIVE['en']}\n"
                if is_zh:
                    prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的{debater['zh_name']}辩手。
{_anime_directive}
{debater['zh_style']}
{reminder}
当前讨论内容：
{input_content}

前几轮其他辩手的观点：
{prev_args}

这是第{round_num}轮辩论。请回应其他辩手的观点——你同意什么？反对什么？你的方案和他们的方案如何取舍？如果可以融合，怎么融合？"""
                else:
                    prompt = f"""You are the {debater['en_name']} debater of the {dept['en_name']} Department.

IMPORTANT: You MUST respond in English only. All output must be in English.
{_anime_directive}
{debater['en_style']}
{reminder}
Current discussion topic:
{input_content}

Previous arguments from other debaters:
{prev_args}

This is Round {round_num}. Respond to other debaters—what do you agree with? Disagree with? How would you trade off between your approach and theirs? If fusion is possible, how?"""
            
            messages = [{"role": "user", "content": prompt}]
            response = call_api(messages, api_url, api_key, model, temperature=0.7, stats=stats)
            
            if response and not response.startswith("ERROR:"):
                arg_text = f"[{debater['zh_name'] if is_zh else debater['en_name']} 第{round_num}轮]: {response}"
                all_arguments.append(arg_text)
                debate_log.append({
                    "round": round_num,
                    "debater": debater_key,
                    "debater_name": debater["zh_name"] if is_zh else debater["en_name"],
                    "content": response,
                })
            
            if progress_callback:
                progress_callback(department_key, round_num, rounds, debater_key)
    
    # Final consensus
    all_args_text = "\n\n---\n\n".join(all_arguments)
    template = STRUCTURED_TEMPLATES.get(department_key, {}).get(lang, "")
    
    constraint_check = ""
    if department_key == "screenwriter":
        if is_zh:
            constraint_check = '\n\n【编剧部硬约束检查】最终方案中不得出现用户剧本未有的新角色、新人物关系、新情节支线或新对话。如果辩手提议中有违反约束的内容，必须剔除，并在方案中标注"此建议已因超出编剧职权而剔除"。'
        else:
            constraint_check = '\n\n[Screenwriter Hard Constraint Check] The final plan must NOT contain new characters, new relationships, new plot sublines, or new dialogue not in the user\'s script. Any constraint-violating proposals must be removed and marked as "This suggestion was removed for exceeding screenwriter authority.".'
    
    if is_zh:
        consensus_prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的辩论主持人。

以下是{dept['zh_name']}{len(dept['debaters'])}位辩手经过{rounds}轮辩论后的全部观点：

{all_args_text}

{f'额外指令：{extra_instructions}' if extra_instructions else ''}

请综合{len(dept['debaters'])}位辩手的观点，形成{dept['zh_name']}的最终共识方案。要求：
1. 明确采纳了哪些观点，为什么
2. 明确舍弃了哪些观点，为什么
3. 最终方案要具体、可执行、有细节
4. 不要含糊地说"综合各方意见"，要给出明确的决策{constraint_check}

{template}"""
    else:
        consensus_prompt = f"""You are the debate moderator for the {dept['en_name']} Department.

IMPORTANT: You MUST respond in English only. All output must be in English.

Below are all arguments from {len(dept["debaters"])} debaters after {rounds} rounds:

{all_args_text}

{f'Extra instructions: {extra_instructions}' if extra_instructions else ''}

Synthesize a final consensus. Requirements:
1. Clearly state which viewpoints were adopted and why
2. Clearly state which were rejected and why
3. The final plan must be specific, actionable, and detailed
4. Don't vaguely say 'combining all views'—give clear decisions{constraint_check}

{template}"""
    
    messages = [{"role": "user", "content": consensus_prompt}]
    
    # Consensus generation: notify UI to enter summary phase
    if progress_callback:
        progress_callback(department_key, rounds + 1, rounds, "consensus")
    
    consensus = call_api(messages, api_url, api_key, model, temperature=0.3, timeout=240, stats=stats)
    
    # Spatial dept: remove residual coordinate system
    if department_key == "spatial" and consensus and not consensus.startswith("⚠️"):
        consensus = clean_spatial_coordinates(consensus)
    
    if consensus and consensus.startswith("ERROR:"):
        # Consensus generation failed, return error for UI display
        return {
            "department": department_key,
            "debate_log": debate_log,
            "consensus": f"⚠️ 共识生成失败：{consensus}",
        }
    
    return {
        "department": department_key,
        "debate_log": debate_log,
        "consensus": consensus or "辩论未能达成共识",
    }

# ============ New Architecture Mode Functions ============

def run_single_agent(
    user_script: str,
    positive_prompt: str,
    negative_prompt: str,
    character_refs: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
) -> Dict:
    """
    单Agent基线模式：一次LLM调用直接生成分镜表+视频提示词。
    作为对照组，展示"有Harness vs 无Harness"的质量差异。
    """
    is_zh = lang == "zh"
    
    if is_zh:
        prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是一个AI动画制作专家。请根据以下输入，直接生成分镜表和逐镜视频提示词。

输入：
- 剧本：{user_script}
- 场景正向提示词：{positive_prompt}
- 负面提示词：{negative_prompt}
- 角色参考：{character_refs}

请输出：
1. 静态关键帧分镜表（每个Shot包含：Shot编号、景别、镜头运动、画面描述、角色站位、叙事节拍、切换动机、出场角色）
2. 逐镜视频提示词（每个SHOT包含：画面内容、镜头运动、角色动作、光线氛围、特效描述、音效提示、叙事节拍、切换动机、出场角色）

直接输出，不要解释你的思考过程。"""
    else:
        prompt = f"""You are an AI animation production expert. Based on the following inputs, directly generate a storyboard and per-shot video prompts.

Inputs:
- Script: {user_script}
- Scene Positive Prompt: {positive_prompt}
- Negative Prompt: {negative_prompt}
- Character References: {character_refs}

Please output:
1. Static Keyframe Storyboard (each Shot includes: Shot number, shot size, camera movement, frame description, character positioning, narrative beat, transition motivation, on-screen characters)
2. Per-Shot Video Prompt (each SHOT includes: frame content, camera movement, character actions, lighting atmosphere, effects description, sound cues, narrative beat, transition motivation, on-screen characters)

Output directly, do not explain your thinking process."""
    
    messages = [{"role": "user", "content": prompt}]
    response = call_api(messages, api_url, api_key, model, temperature=0.7, stats=stats)
    
    if response and not response.startswith("ERROR:"):
        # Try splitting storyboard and video prompts
        parts = response.split("逐镜视频提示词" if is_zh else "Per-Shot Video Prompt")
        if len(parts) >= 2:
            storyboard = parts[0].strip()
            video_prompt = parts[1].strip()
        else:
            # Fallback split
            parts2 = response.split("2." if not is_zh else "2.")
            if len(parts2) >= 2:
                storyboard = parts2[0].strip()
                video_prompt = parts2[1].strip()
            else:
                storyboard = response
                video_prompt = ""
        
        return {
            "storyboard_prompt": storyboard,
            "video_prompt": video_prompt,
            "raw_output": response,
        }
    else:
        return {
            "storyboard_prompt": f"ERROR: {response}",
            "video_prompt": "",
            "raw_output": response or "",
        }

def run_expert_pool_debate(
    user_script: str,
    positive_prompt: str,
    character_refs: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    rounds: int = 3,
    lang: str = "zh",
    extra_instructions: str = "",
    carry_forward: str = "",
    progress_callback: Callable = None,
    stats: dict = None,
) -> Dict:
    """
    专家池模式：先分析场景→确定每部门选2名最相关辩手→精简辩论。
    展示"智能调度"vs"全员参辩"的效率差异。
    """
    is_zh = lang == "zh"
    
    # Step 1: Scene analysis, determine debaters per department
    dept_debater_names = {}
    for dk, dept in DEPARTMENTS.items():
        names = [dept["debaters"][bk]["zh_name"] if is_zh else dept["debaters"][bk]["en_name"] for bk in dept["debaters"]]
        dept_debater_names[dk] = names
    
    if is_zh:
        analysis_prompt = f"""你是一个动画制作流程的调度专家。根据以下场景描述，为每个部门选择2名最相关的辩手。

场景：
{user_script}

视觉风格：
{positive_prompt}

可选辩手：
- 编剧部：{', '.join(dept_debater_names['screenwriter'])}
- 空间板块：{', '.join(dept_debater_names['spatial'])}
- 分镜部：{', '.join(dept_debater_names['storyboard'])}
- 摄影部：{', '.join(dept_debater_names['dp'])}
- 灯光部：{', '.join(dept_debater_names['lighting'])}
- 特效部：{', '.join(dept_debater_names['vfx'])}
- 音效部：{', '.join(dept_debater_names['sound'])}
- 剪辑部：{', '.join(dept_debater_names['editing'])}

请用JSON格式输出，键为部门英文名(screenwriter/spatial/storyboard/dp/lighting/vfx/sound/editing)，值为选中的2名辩手的中文名列表。
只输出JSON，不要其他文字。"""
    else:
        analysis_prompt = f"""You are a scheduling expert for animation production workflows. Based on the scene description below, select the 2 most relevant debaters for each department.

Scene:
{user_script}

Visual style:
{positive_prompt}

Available debaters:
- Screenwriter: {', '.join(dept_debater_names['screenwriter'])}
- Spatial: {', '.join(dept_debater_names['spatial'])}
- Storyboard: {', '.join(dept_debater_names['storyboard'])}
- DP: {', '.join(dept_debater_names['dp'])}
- Lighting: {', '.join(dept_debater_names['lighting'])}
- VFX: {', '.join(dept_debater_names['vfx'])}
- Sound: {', '.join(dept_debater_names['sound'])}
- Editing: {', '.join(dept_debater_names['editing'])}

Output in JSON format. Keys are department English names (screenwriter/spatial/storyboard/dp/lighting/vfx/sound/editing), values are lists of 2 selected debater names.
Output JSON only, no other text."""
    
    analysis_messages = [{"role": "user", "content": analysis_prompt}]
    analysis_response = call_api(analysis_messages, api_url, api_key, model, temperature=0.3, stats=stats)
    
    # Parse scene analysis results, get debater_filter per dept
    debater_filters = {}
    if analysis_response and not analysis_response.startswith("ERROR:"):
        try:
            # Extract JSON part
            json_text = analysis_response
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]
            selection = json.loads(json_text.strip())
            
            for dk in DEPT_ORDER:
                dept = DEPARTMENTS[dk]
                selected_names = selection.get(dk, [])
                filter_keys = []
                for bk, bd in dept["debaters"].items():
                    bd_name = bd["zh_name"] if is_zh else bd["en_name"]
                    if bd_name in selected_names:
                        filter_keys.append(bk)
                # If none selected, default to first 2
                if not filter_keys:
                    filter_keys = list(dept["debaters"].keys())[:2]
                debater_filters[dk] = filter_keys
        except (json.JSONDecodeError, KeyError):
            # Parse failed, default to first 2 debaters per dept
            for dk in DEPT_ORDER:
                debater_filters[dk] = list(DEPARTMENTS[dk]["debaters"].keys())[:2]
    else:
        for dk in DEPT_ORDER:
            debater_filters[dk] = list(DEPARTMENTS[dk]["debaters"].keys())[:2]
    
    # Step 2: Run Pipeline of Consensus with filtered debaters
    dept_results = {}
    for dept_key in DEPT_ORDER:
        dept = DEPARTMENTS[dept_key]
        dept_input = _build_dept_input_simple(dept_key, dept_results, user_script, positive_prompt, character_refs, lang)
        
        result = run_department_debate(
            department_key=dept_key,
            input_content=dept_input,
            api_url=api_url, api_key=api_key, model=model,
            rounds=rounds, lang=lang, extra_instructions=extra_instructions,
            progress_callback=progress_callback,
            carry_forward=carry_forward,
            debater_filter=debater_filters.get(dept_key),
            stats=stats,
        )
        dept_results[dept_key] = result
    
    return {
        "dept_results": dept_results,
        "debater_filters": debater_filters,
        "analysis_response": analysis_response,
    }

def _build_dept_input_simple(dept_key, dept_results, script, positive, chars, lang="zh"):
    """简化版的部门输入构建（不依赖streamlit session_state）"""
    is_zh = lang == "zh"
    if dept_key == "screenwriter":
        return "剧本：\n" + script + "\n\n场景风格：\n" + positive + "\n\n角色参考：\n" + chars
    elif dept_key == "spatial":
        sw = dept_results.get("screenwriter", {}).get("consensus", script)
        return "编剧部细节填充版剧本：\n" + sw + "\n\n原始场景风格：\n" + positive
    else:
        parts = []
        # Always include the original topic as context for academic departments
        if script:
            if is_zh:
                parts.append(f"研究主题：\n{script}")
            else:
                parts.append(f"Research Topic:\n{script}")
        for pk in DEPT_ORDER[:DEPT_ORDER.index(dept_key)]:
            if pk in dept_results:
                p = DEPARTMENTS[pk]
                pn = p["zh_name"] if is_zh else p["en_name"]
                parts.append(pn + "共识：\n" + dept_results[pk]["consensus"])
        return "\n\n---\n\n".join(parts)



# ============ Market Mode ============

def _run_single_candidate(
    candidate_idx: int,
    temperature: float,
    user_script: str,
    positive_prompt: str,
    negative_prompt: str,
    character_refs: str,
    api_url: str,
    api_key: str,
    model: str,
    rounds: int,
    lang: str,
    extra_instructions: str,
    carry_forward: str,
    progress_callback: Callable = None,
    dept_filter: list = None,
) -> Dict:
    """单个候选的完整Pipeline（线程执行体，必须是模块级函数以支持pickle）"""
    import copy

    candidate_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "api_calls": 0}
    label = chr(65 + candidate_idx)  # A, B, C...
    active_depts = [d for d in DEPT_ORDER if d in dept_filter] if dept_filter else DEPT_ORDER
    total_depts = len(active_depts)

    # Run full Pipeline (dept debates + spatial review + cross-debate + summary)
    dept_results = {}
    for di, dept_key in enumerate(active_depts):
        # Report: which department is running
        if progress_callback:
            progress_callback("dept_start", candidate_idx, dept_key, di, total_depts)

        dept_input = _build_dept_input_simple(dept_key, dept_results, user_script, positive_prompt, character_refs, lang)

        result = run_department_debate(
            department_key=dept_key,
            input_content=dept_input,
            api_url=api_url, api_key=api_key, model=model,
            rounds=rounds, lang=lang,
            extra_instructions=extra_instructions,
            carry_forward=carry_forward,
            stats=candidate_stats,
        )
        dept_results[dept_key] = result

        # Report: department complete
        if progress_callback:
            progress_callback("dept_done", candidate_idx, dept_key, di + 1, total_depts)

    # Spatial review
    if progress_callback:
        progress_callback("phase", candidate_idx, "spatial_review", 0, 0)
    spatial_consensus = dept_results.get("spatial", {}).get("consensus", "")
    if spatial_consensus:
        _spatial_reviewers = [d for d in ["storyboard", "dp", "editing"] if d in dept_results]
        spatial_review = run_spatial_review(
            spatial_consensus=spatial_consensus,
            reviewer_departments=_spatial_reviewers,
            api_url=api_url, api_key=api_key, model=model, lang=lang,
            stats=candidate_stats,
        )
        dept_results["spatial"]["consensus"] = clean_spatial_coordinates(spatial_review["revised_consensus"])

    # Cross-debate
    if progress_callback:
        progress_callback("phase", candidate_idx, "cross_debate", 0, 0)
    cross_results = []
    for cd in P5_CROSS_DEBATES:
        a_key, b_key = cd["side_a"], cd["side_b"]
        if a_key in dept_results and b_key in dept_results:
            cr = run_cross_debate(
                cross_config=cd,
                dept_a_consensus=dept_results[a_key]["consensus"],
                dept_b_consensus=dept_results[b_key]["consensus"],
                api_url=api_url, api_key=api_key, model=model, lang=lang,
                stats=candidate_stats,
            )
            cross_results.append(cr)

    # Summary
    if progress_callback:
        progress_callback("phase", candidate_idx, "summary", 0, 0)
    final = run_summary(
        all_consensus={k: v.get("consensus", "") for k, v in dept_results.items()},
        cross_results=cross_results,
        user_script=user_script, positive_prompt=positive_prompt,
        negative_prompt=negative_prompt, character_refs=character_refs,
        api_url=api_url, api_key=api_key, model=model, lang=lang,
        stats=candidate_stats,
    )
    if final is None:
        final = {"storyboard_prompt": "", "video_prompt": ""}

    return {
        "label": label,
        "temperature": temperature,
        "storyboard_prompt": final.get("storyboard_prompt", ""),
        "video_prompt": final.get("video_prompt", ""),
        "dept_results": dept_results,
        "stats": copy.deepcopy(candidate_stats),
        "_stats": candidate_stats,  # for merging into total stats
    }

def generate_candidates(
    num_candidates: int = 3,
    user_script: str = "",
    positive_prompt: str = "",
    negative_prompt: str = "",
    character_refs: str = "",
    api_url: str = "",
    api_key: str = "",
    model: str = "deepseek-v4-flash",
    rounds: int = 1,
    lang: str = "zh",
    extra_instructions: str = "",
    carry_forward: str = "",
    progress_callback: Callable = None,
    stats: dict = None,
    max_workers: int = 3,
    dept_filter: list = None,
) -> Dict:
    """
    市场模式Step1：生成N个候选方案
    同模型同架构，不同温度（0.6/0.7/0.8...）
    支持并行生成（max_workers>1时使用线程池）
    默认1轮辩论（市场模式重在多候选对比，不需要每候选内部多轮）
    
    线程安全：子线程通过queue传递进度，主线程轮询调用progress_callback
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import queue
    import threading

    temperatures = MARKET_CONFIG["temperatures"][:num_candidates]
    while len(temperatures) < num_candidates:
        temperatures.append(0.7)

    candidates = [None] * num_candidates
    errors = [None] * num_candidates
    progress_queue = queue.Queue()
    
    def _worker_callback(phase, idx, dept_key, di, total_depts):
        """子线程安全的进度回调——只往队列放数据，不碰Streamlit"""
        progress_queue.put((phase, idx, dept_key, di, total_depts))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i in range(num_candidates):
            future = executor.submit(
                _run_single_candidate,
                candidate_idx=i,
                temperature=temperatures[i],
                user_script=user_script,
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
                character_refs=character_refs,
                api_url=api_url,
                api_key=api_key,
                model=model,
                rounds=rounds,
                lang=lang,
                extra_instructions=extra_instructions,
                carry_forward=carry_forward,
                progress_callback=_worker_callback,
                dept_filter=dept_filter,
            )
            futures[future] = i

        # Main thread polling: collect progress + wait for completion
        done_set = set()
        while len(done_set) < len(futures):
            # Process queued progress messages (main thread, Streamlit-safe)
            while not progress_queue.empty():
                try:
                    msg = progress_queue.get_nowait()
                    if progress_callback:
                        progress_callback(*msg)
                except queue.Empty:
                    break
            
            # Check completed futures
            for future in list(futures.keys()):
                if future in done_set:
                    continue
                if future.done():
                    idx = futures[future]
                    try:
                        exc = future.exception(timeout=0)
                        if exc is not None:
                            errors[idx] = str(exc)
                            candidates[idx] = None
                        else:
                            result = future.result()
                            candidates[idx] = result
                    except Exception as e:
                        errors[idx] = str(e)
                        candidates[idx] = None
                    
                    done_set.add(future)
                    if progress_callback:
                        progress_callback("candidate_done", idx, "done", 0, 0)
                    # Accumulate stats
                    if stats is not None and candidates[idx] is not None:
                        for k in ["prompt_tokens", "completion_tokens", "total_tokens", "api_calls"]:
                            stats[k] = stats.get(k, 0) + candidates[idx].pop("_stats", {}).get(k, 0)
            
            time.sleep(0.5)  # 轮询间隔
        
        # Clear remaining progress messages
        while not progress_queue.empty():
            try:
                msg = progress_queue.get_nowait()
                if progress_callback:
                    progress_callback(*msg)
            except queue.Empty:
                break

    # Filter failed candidates
    valid_candidates = []
    for i, c in enumerate(candidates):
        if c is not None:
            valid_candidates.append(c)
        else:
            err_msg = errors[i] or "未知错误"
            if progress_callback:
                progress_callback("candidate_error", i, err_msg, 0, 0)

    if not valid_candidates:
        return {"candidates": [], "errors": errors}

    return {"candidates": valid_candidates, "errors": [e for e in errors if e]}

def generate_questions(
    candidates: list,
    questions_per_debater: int = 7,
    api_url: str = "",
    api_key: str = "",
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
    progress_callback: Callable = None,
) -> Dict:
    """
    市场模式Step2：按部门出题（省钱版）
    每个部门1次调用，提N个问题（而非每辩手1次=24次→8次）
    """
    is_zh = lang == "zh"
    lang_cfg = MARKET_CONFIG["question_languages"][lang]
    
    # Build candidate summary
    candidate_summaries = []
    for c in candidates:
        sb_preview = c["storyboard_prompt"][:600] if c["storyboard_prompt"] else ""
        vp_preview = c["video_prompt"][:600] if c["video_prompt"] else ""
        candidate_summaries.append(f"=== 候选{c['label']} (温度{c['temperature']}) ===\n分镜表摘要：\n{sb_preview}\n...\n视频提示词摘要：\n{vp_preview}\n...")
    
    all_summaries = "\n\n".join(candidate_summaries)
    
    all_questions = []
    q_index = 0
    
    for dept_key in DEPT_ORDER:
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        debater_names = "、".join([d["zh_name"] if is_zh else d["en_name"] for d in dept["debaters"].values()])
        
        # Debaters per dept × questions per debater = total questions per dept
        dept_questions = questions_per_debater * len(dept["debaters"])
        
        if is_zh:
            prompt = f"""你是{dept_name}（含{debater_names}）。

{ANIME_VISUAL_DIRECTIVE['zh']}

现在有{len(candidates)}个动画分镜方案候选，你需要从{dept_name}的专业视角提出{dept_questions}个具体的质量评估问题。

{all_summaries}

{lang_cfg['question_instruction']}

请输出{dept_questions}个问题，每个一行，格式：
Q1: [具体问题]
Q2: [具体问题]
..."""
        else:
            prompt = f"""You are the {dept['en_name']} Department (including {debater_names}).

{ANIME_VISUAL_DIRECTIVE['en']}

There are {len(candidates)} animation storyboard candidates. Propose {dept_questions} specific quality evaluation questions from your {dept['en_name']} perspective.

{all_summaries}

{lang_cfg['question_instruction']}

Output {dept_questions} questions, one per line:
Q1: [specific question]
Q2: [specific question]
..."""
        
        messages = [{"role": "user", "content": prompt}]
        response = call_api(messages, api_url, api_key, model, temperature=0.5, max_tokens=4096, stats=stats)
        
        if response and not response.startswith("ERROR:"):
            import re
            lines = response.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and ("Q" in line[:5] or ":" in line[:5] or "？" in line or "?" in line):
                    clean = re.sub(r'^Q\d+\s*[:：]\s*', '', line).strip()
                    if clean:
                        all_questions.append({
                            "index": q_index,
                            "question": clean,
                            "source_dept": dept_key,
                            "source_debater": list(dept["debaters"].keys())[0],
                            "source_name": dept_name,
                        })
                        q_index += 1
        
        if progress_callback:
            progress_callback("questioning", dept_key, dept_key)
    
    return {"questions": all_questions, "total": len(all_questions)}

def vote_on_questions(
    questions: list,
    candidates: list,
    api_url: str = "",
    api_key: str = "",
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
    progress_callback: Callable = None,
) -> Dict:
    """
    市场模式Step3：批量投票（省钱版）
    每个投票人1次调用，一次投完所有分配到的题（而非每题1次=168次→24次）
    候选摘要替代全文，大幅减少prompt token
    """
    import random
    is_zh = lang == "zh"
    lang_cfg = MARKET_CONFIG["question_languages"][lang]
    
    # Collect all AIs (aggregated by dept, 1 representative per dept)
    all_voters = []
    for dept_key in DEPT_ORDER:
        dept = DEPARTMENTS[dept_key]
        for debater_key in dept["debaters"]:
            all_voters.append({
                "dept_key": dept_key,
                "debater_key": debater_key,
                "dept_name": dept["zh_name"] if is_zh else dept["en_name"],
                "debater_name": dept["debaters"][debater_key]["zh_name"] if is_zh else dept["debaters"][debater_key]["en_name"],
            })
    
    num_voters = len(all_voters)
    questions_copy = list(questions)
    random.shuffle(questions_copy)
    
    # Assign questions to voters
    assignments = {i: [] for i in range(num_voters)}
    for qi, q in enumerate(questions_copy):
        voter_idx = qi % num_voters
        assignments[voter_idx].append(q)
    
    # Candidate summary (not full text, save tokens)
    candidate_summaries = []
    for c in candidates:
        sb_preview = c["storyboard_prompt"][:800] if c["storyboard_prompt"] else ""
        vp_preview = c["video_prompt"][:800] if c["video_prompt"] else ""
        candidate_summaries.append(f"=== 候选{c['label']} (温度{c['temperature']}) ===\n分镜表摘要：\n{sb_preview}\n...\n视频提示词摘要：\n{vp_preview}\n...")
    
    all_candidates_text = "\n\n---\n\n".join(candidate_summaries)
    
    # Voting
    votes = []
    vote_counts = {c["label"]: 0 for c in candidates}
    voter_details = []
    
    for vi, voter in enumerate(all_voters):
        my_questions = assignments[vi]
        if not my_questions:
            continue
        
        # Combine all questions into single API call
        q_list = "\n".join([f"Q{qi+1}: {q['question']}" for qi, q in enumerate(my_questions)])
        labels = "/".join([c["label"] for c in candidates])
        
        if is_zh:
            prompt = f"""你是{voter['dept_name']}的{voter['debater_name']}。

{ANIME_VISUAL_DIRECTIVE['zh']}

以下是{len(my_questions)}个质量评估问题：
{q_list}

以下是{len(candidates)}个候选方案摘要：
{all_candidates_text}

请对每个问题选择最佳候选（{labels}），用JSON数组输出：
[
  {{"question": 1, "choice": "{candidates[0]['label']}", "reason": "简短理由"}},
  {{"question": 2, "choice": "...", "reason": "..."}},
  ...
]"""
        else:
            prompt = f"""You are the {voter['debater_name']} of the {voter['dept_name']} Department.

{ANIME_VISUAL_DIRECTIVE['en']}

Quality evaluation questions:
{q_list}

Candidate summaries:
{all_candidates_text}

For each question, choose the best candidate ({labels}). Output as JSON array:
[
  {{"question": 1, "choice": "{candidates[0]['label']}", "reason": "brief reason"}},
  {{"question": 2, "choice": "...", "reason": "..."}},
  ...
]"""
        
        messages = [{"role": "user", "content": prompt}]
        response = call_api(messages, api_url, api_key, model, temperature=0.3, max_tokens=4096, stats=stats)
        
        if response and not response.startswith("ERROR:"):
            try:
                import re
                # Extract JSON array
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    vote_list = json.loads(json_match.group())
                    for vdata in vote_list:
                        choice = str(vdata.get("choice", "")).upper()
                        reason = vdata.get("reason", "")
                        q_idx = vdata.get("question", 0) - 1
                        
                        if 0 <= q_idx < len(my_questions):
                            q = my_questions[q_idx]
                            if choice and choice in vote_counts:
                                vote_counts[choice] += 1
                            
                            votes.append({
                                "voter": f"{voter['dept_name']}/{voter['debater_name']}",
                                "question": q["question"],
                                "choice": choice,
                                "reason": reason,
                            })
            except (json.JSONDecodeError, KeyError, IndexError):
                # Parse failed, try extracting from text
                for q in my_questions:
                    for label in [c["label"] for c in candidates]:
                        if label in (response or ""):
                            vote_counts[label] = vote_counts.get(label, 0) + 1
                            votes.append({
                                "voter": f"{voter['dept_name']}/{voter['debater_name']}",
                                "question": q["question"],
                                "choice": label,
                                "reason": response[:100] if response else "",
                            })
                            break
        
        voter_details.append({
            "voter": f"{voter['dept_name']}/{voter['debater_name']}",
            "num_questions": len(my_questions),
        })
        
        if progress_callback:
            progress_callback("voting", vi, voter["debater_name"], num_voters)
    
    # Vote counting results
    winner_label = max(vote_counts, key=vote_counts.get)
    winner_candidate = None
    for c in candidates:
        if c["label"] == winner_label:
            winner_candidate = c
            break
    
    # Analyze controversial issues
    contested_questions = []
    for q in questions:
        q_votes = [v for v in votes if v["question"] == q["question"]]
        if len(q_votes) > 1:
            choices = [v["choice"] for v in q_votes if v["choice"]]
            if len(set(choices)) > 1:
                contested_questions.append({
                    "question": q["question"],
                    "source": q.get("source_name", ""),
                    "vote_distribution": {c: choices.count(c) for c in set(choices)},
                })
    
    return {
        "vote_counts": vote_counts,
        "winner_label": winner_label,
        "winner_candidate": winner_candidate,
        "total_votes": len(votes),
        "votes": votes,
        "voter_details": voter_details,
        "contested_questions": contested_questions[:20],
    }

def patch_winner(
    winner_candidate: Dict,
    contested_questions: list,
    all_candidates: list,
    api_url: str = "",
    api_key: str = "",
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
) -> Dict:
    """
    市场模式Step4：补丁轮
    对投票中暴露的争议问题，对最优候选做定向修正
    """
    is_zh = lang == "zh"
    
    if not contested_questions:
        return {
            "storyboard_prompt": winner_candidate["storyboard_prompt"],
            "video_prompt": winner_candidate["video_prompt"],
            "patch_notes": "无争议问题，无需修正" if is_zh else "No contested issues, no patch needed",
        }
    
    # Summarize controversial issues
    issues_text = "\n".join([
        f"- {cq['question']}（投票分歧：{cq['vote_distribution']}，来源：{cq['source']}）"
        for cq in contested_questions[:10]  # 最多修正10个
    ])
    
    if is_zh:
        prompt = f"""你是一个动画分镜方案的修正专家。以下是最优候选方案，以及投票中暴露的争议问题。

最优候选（候选{winner_candidate['label']}）分镜表：
{winner_candidate['storyboard_prompt']}

最优候选视频提示词：
{winner_candidate['video_prompt']}

投票中暴露的争议问题（部分投票者认为其他候选在这些方面更好）：
{issues_text}

请针对以上争议问题，修正最优候选方案。要求：
1. 只修正有争议的部分，不要改动已经很好的部分
2. 修正时参考其他候选在这些争议点上的处理方式
3. 输出修正后的完整分镜表和视频提示词
4. 在修正处标注[修正]以便追踪

输出修正后的分镜表和视频提示词。"""
    else:
        prompt = f"""You are an animation storyboard revision expert. Below is the winning candidate and contested issues from voting.

Winning candidate ({winner_candidate['label']}) storyboard:
{winner_candidate['storyboard_prompt']}

Winning candidate video prompt:
{winner_candidate['video_prompt']}

Contested issues from voting (some voters preferred other candidates on these points):
{issues_text}

Please revise the winning candidate to address these contested issues. Requirements:
1. Only revise the contested parts, don't change what's already good
2. Reference how other candidates handled these contested points
3. Output the complete revised storyboard and video prompt
4. Mark revisions with [REVISED] for tracking

Output the revised storyboard and video prompt."""
    
    messages = [{"role": "user", "content": prompt}]
    response = call_api(messages, api_url, api_key, model, temperature=0.5, max_tokens=16384, stats=stats)
    
    if response and not response.startswith("ERROR:"):
        # Try splitting
        parts = response.split("视频提示词" if is_zh else "Video Prompt")
        if len(parts) >= 2:
            storyboard = parts[0].strip()
            video_prompt = parts[1].strip()
        else:
            # Fallback: find [correction] marked paragraphs
            storyboard = response
            video_prompt = ""
        
        return {
            "storyboard_prompt": storyboard,
            "video_prompt": video_prompt,
            "patch_notes": f"已修正{len(contested_questions[:10])}个争议问题" if is_zh else f"Patched {len(contested_questions[:10])} contested issues",
        }
    else:
        return {
            "storyboard_prompt": winner_candidate["storyboard_prompt"],
            "video_prompt": winner_candidate["video_prompt"],
            "patch_notes": f"修正失败，保留原方案: {response}" if is_zh else f"Patch failed, keeping original: {response}",
        }

def run_cross_debate(
    cross_config: Dict,
    dept_a_consensus: str,
    dept_b_consensus: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """运行两个部门间的交叉辩论"""
    is_zh = lang == "zh"
    dept_a = DEPARTMENTS[cross_config["side_a"]]
    dept_b = DEPARTMENTS[cross_config["side_b"]]
    topic = cross_config["zh_topic"] if is_zh else cross_config["en_topic"]
    
    a_name = dept_a["zh_name"] if is_zh else dept_a["en_name"]
    b_name = dept_b["zh_name"] if is_zh else dept_b["en_name"]
    
    if is_zh:
        prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{a_name}和{b_name}的交叉辩论主持人。

辩论主题：{topic}

{a_name}的共识方案：
{dept_a_consensus}

{b_name}的共识方案：
{dept_b_consensus}

请从双方的专业视角出发，分析两者的冲突点和互补点，并给出一个综合方案。要求：
1. 明确指出双方的冲突点，以及你的裁决和理由
2. 明确指出双方的互补点，以及如何融合
3. 给出综合后的具体方案，不能含糊"""
    else:
        prompt = f"""You are the cross-debate moderator for {dept_a['en_name']} and {dept_b['en_name']}.

Debate Topic: {topic}

{dept_a['en_name']} Consensus:
{dept_a_consensus}

{dept_b['en_name']} Consensus:
{dept_b_consensus}

Analyze conflicts and complementarities from both perspectives, and provide a synthesized plan. Requirements:
1. Clearly identify conflicts and your ruling with reasons
2. Clearly identify complementarities and how to fuse them
3. Provide a specific synthesized plan—no vagueness."""
    
    messages = [{"role": "user", "content": prompt}]
    result = call_api(messages, api_url, api_key, model, temperature=0.3, max_tokens=4096, timeout=180, stats=stats)
    
    return {
        "side_a": cross_config["side_a"],
        "side_b": cross_config["side_b"],
        "topic": topic,
        "debate_result": result or "交叉辩论未能完成",
    }

# ============ P2: Spatial Cross-Review ============

def run_spatial_review(
    spatial_consensus: str,
    reviewer_departments: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    P2: 空间板块初版产出后，由分镜/摄影/剪辑进行可行性审核。
    每个审核部门的3位辩手从各自专业视角给出反馈，
    最后空间板块综合反馈修订方案。
    """
    is_zh = lang == "zh"
    reviews = {}
    
    for dept_key in reviewer_departments:
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        feedbacks = []
        
        for debater_key in dept["debaters"]:
            debater = dept["debaters"][debater_key]
            debater_name = debater["zh_name"] if is_zh else debater["en_name"]
            
            if is_zh:
                prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept_name}的{debater_name}辩手。

{ANIME_VISUAL_DIRECTIVE['zh']}

{debater['zh_style']}

以下是空间板块的布局方案，请从你的专业视角审核其可行性：

{spatial_consensus}

请重点关注：
1. 物品定位是否支持你想实现的镜头构图？
2. 角色站位和移动路径是否合理（物品参照位置是否清晰、面朝方向是否合理）？
3. 有没有空间上的硬伤（遮挡、不可达、不合理距离、两个角色站在同一物品参照位置）？
4. 你建议如何调整物品布局或角色定位以更好地服务于你的专业需求？

请具体指出问题和建议，不要泛泛而谈。"""
            else:
                prompt = f"""You are the {debater['en_name']} debater of the {dept['en_name']} Department.

{ANIME_VISUAL_DIRECTIVE['en']}

{debater['en_style']}

Review the following spatial layout plan from your professional perspective:

{spatial_consensus}

Focus on:
1. Does the object positioning support the camera compositions you want?
2. Are character positions and movement paths reasonable (are object-referenced positions clear, are facing directions reasonable)?
3. Any spatial hard issues (occlusions, unreachable positions, unreasonable distances, two characters at the same object-referenced position)?
4. How would you adjust object layout or character positioning to better serve your professional needs?

Be specific about problems and suggestions. No vague statements."""
            
            messages = [{"role": "user", "content": prompt}]
            response = call_api(messages, api_url, api_key, model, temperature=0.5, stats=stats)
            if response and not response.startswith("ERROR:"):
                feedbacks.append(f"[{debater_name}]: {response}")
        
        reviews[dept_key] = "\n\n---\n\n".join(feedbacks)
    
    # Spatial dept comprehensive feedback, revision plan
    all_reviews_text = ""
    for dept_key, review_text in reviews.items():
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        all_reviews_text += f"\n### {dept_name}审核反馈\n{review_text}\n"
    
    if is_zh:
        revise_prompt = f"""你是空间板块的辩论主持人。

以下是空间板块的初版布局方案：
{spatial_consensus}

以下是分镜部、摄影指导部、剪辑部的审核反馈：
{all_reviews_text}

请综合以上审核反馈，修订空间板块的布局方案。要求：
1. 明确采纳了哪些反馈，如何调整
2. 明确拒绝了哪些反馈，为什么
3. 修订后的方案必须保持空间布局的逻辑性和物理可信度
4. 按照空间板块的结构化模板输出修订后的完整方案"""
    else:
        revise_prompt = f"""You are the debate moderator for the Spatial Planning Department.

Initial spatial layout plan:
{spatial_consensus}

Review feedback from Storyboard, Cinematography, and Editing departments:
{all_reviews_text}

Synthesize the feedback and revise the spatial layout plan. Requirements:
1. Clearly state which feedback was adopted and how the plan was adjusted
2. Clearly state which feedback was rejected and why
3. The revised plan must maintain logical and physically credible spatial layout
4. Output the complete revised plan using the Spatial Planning structured template"""
    
    messages = [{"role": "user", "content": revise_prompt}]
    revised_consensus = call_api(messages, api_url, api_key, model, temperature=0.3, max_tokens=4096, timeout=180, stats=stats)
    
    # Remove residual coordinate system
    if revised_consensus and not revised_consensus.startswith("ERROR:"):
        revised_consensus = clean_spatial_coordinates(revised_consensus)
    
    return {
        "initial_consensus": spatial_consensus,
        "reviews": reviews,
        "revised_consensus": revised_consensus or "空间板块修订失败",
    }

# ============ Summary AI ============

def run_summary(
    user_script: str,
    positive_prompt: str,
    negative_prompt: str,
    character_refs: str,
    all_consensus: Dict[str, str],
    cross_results: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    总结AI产出：
    1. 分镜表（纯静态关键帧，引用空间物品定位）→ 九宫格
    2. 视频逐镜提示词（[关键帧]+[动态衔接]双层结构）
    如果总时长>15秒，按剪辑拆分产出多段
    """
    is_zh = lang == "zh"
    
    # Build all department consensus
    consensus_text = ""
    for dept_key, consensus in all_consensus.items():
        dept = DEPARTMENTS.get(dept_key, {})
        name = dept.get("zh_name" if is_zh else "en_name", dept_key)
        consensus_text += f"\n### {name}\n{consensus}\n"
    
    # Cross-debate results
    cross_text = ""
    for cr in cross_results:
        cross_text += f"\n### {cr['topic']}\n{cr['debate_result']}\n"
    
    # Check if editing dept consensus exists
    editing_consensus = all_consensus.get("editing", "")
    
    # Spatial dept consensus (for referencing object positioning)
    spatial_consensus = all_consensus.get("spatial", "")
    
    # ===== Output 1: Storyboard (pure static keyframes) =====
    if is_zh:
        storyboard_prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是最终总结AI。请根据以下所有部门的辩论结果，生成纯静态关键帧分镜表。

【分镜表定义】分镜表是拍摄内容的静态关键帧——每个Shot是定格照片，不是动画脚本。
- 写的是"在这个机位、这个角度、这个打光下，角色表情什么、动作定格什么、和谁互动什么、背景什么"
- 不写任何动态描述（如"角色从A走到B"、"镜头从右下角运动进入"）
- 动态信息（角色移动、镜头运动、衔接过渡）全部留给视频提示词

用户原始剧本：
{user_script}

场景正向提示词：
{positive_prompt}

角色参考：
{character_refs}

各部门辩论共识：
{consensus_text}

交叉辩论结果：
{cross_text}

【关键规则】
1. 每个镜头必须包含焦段mm值和景深信息（来自摄影指导部辩论）
2. 每个镜头必须标注剪辑属性：硬切/长镜头/叠化/淡入淡出（来自分镜部辩论）
3. 每个镜头的站位必须包含物品参照位置+镜头相对朝向+画面位置+垂直状态（如"长桌靠墙侧左端，侧面向镜头30度 / 画面左1/3，中景 / 站立"），朝向严禁用东南/西南等罗盘方向
4. 分镜表只写静态定格状态，不写任何动态描述
5. Shot总数由分镜部辩论决定，不限制为9个
6. 剪辑部按4-15秒拆分为段落，每段恰好9个Shot（对应3×3九宫格，每格一个关键帧）
6b. 【锚定破除】总结AI生成分镜表时，必须忽略剪辑部共识中的具体Shot数量分配——剪辑部的Shot数量仅供总结AI参考，总结AI只取用剪辑部的时间范围（如"段落1: 0-8s, 段落2: 8-16s"），然后每段独立产出恰好9个Shot。剪辑部的Shot分配是给剪辑部自己用的，不是给分镜表的约束
7. 【关键帧不足补充流程】如果某段不足9个Shot：分镜部对接剪辑部，在不改变整体编排时间的前提下协商补充关键帧 → 补充后的Shot重新走灯光部/空间部等流程确认 → 最终每段补齐到9个Shot。补充的关键帧必须与原有叙事逻辑一致，不能凭空插入
8. 【最重要】每个Shot必须有【完整画面】段——用自然语言描述整帧画面的完整视觉内容，包括前景/中景/背景构成、角色在画面中的位置和整体造型轮廓、环境空间构成、光线的实际画面效果、关键视觉元素的画面表现。这是AI绘图工具唯一能理解的部分，没有它AI无法画出分镜图
9. 【最重要】分镜表是结构化表格，不是自由文章——每个字段必须从对应部门的共识中提取，AI不做自由改写：
   - 叙事节拍 → 从编剧部架构师共识提取
   - 切换动机 → 从摄影部共识提取
   - 出场角色 → 从编剧部架构师出场清单提取
   - 镜头/景别/焦段 → 从摄影部共识提取
   - 打光 → 从灯光部共识提取
   - 站位/空间 → 从空间部共识提取
   - 表情/动作 → 从编剧部微表情/肢体派共识提取
   - 背景 → 从空间部+编剧部共识提取
10. 每个Shot的出场角色必须与编剧部出场清单一致，不允许角色凭空消失或出现
11. 镜头之间必须有切换动机，不允许无动机切换
12. 【台词时长硬约束】如果某个Shot包含角色台词/对白，该Shot时长必须≥台词字数×0.4秒（中文约2.5字/秒，留余量）。例如6个字的台词至少需要2.4秒≈3秒。绝不允许台词超过2秒却只给1秒时长——1秒最多说完2-3个字。没有台词的纯画面Shot可以短至1-2秒。
13. 负面提示词是必输出项——分镜表末尾必须完整输出负面提示词，不允许省略、缩写或跳过。如果负面提示词为空，输出'无特殊负面提示词'。
14. 每个段落开头必须完整输出'统一场景提示词'和'统一镜头语言'，不允许用'同上'省略。

请严格按照以下格式输出（Shot数量必须与视频提示词完全一致）：

{f"【剪辑部分段方案】{editing_consensus}" if editing_consensus else ""}

===== 段落1 =====

场景空间布局：[引用空间板块的物品清单+物品间距离关系，完整写出]

统一场景提示词：
{positive_prompt}

统一镜头语言：[整合DP+分镜部的辩论共识，必须包含焦段和景深决策]

{character_refs}

【✅ 正确示例——必须像这样写完整画面】
Shot 01（时间：0-2s）：
【完整画面】
画面中央偏右，一个银发少女单膝跪在碎裂的白色大理石地面上，右手握着一把插入地面的长剑支撑身体，左手按住左肩的伤口。她的银色长发散落在右肩，被画面左侧的一束金色光柱照亮，发丝边缘泛着光晕。她抬头仰望画面左上方，表情坚毅但嘴角有一丝血迹。前景是碎裂的地面石块和飘散的尘埃粒子，中景是少女全身像占据画面2/3高度，背景是倒塌的古典石柱和灰暗的天空，远处有微弱的火光映红了云层底部。画面整体是冷蓝灰色调，只有左上的金色光柱和远处的火光提供暖色对比。
叙事节拍：节拍1-少女跪地（← 编剧部叙事架构师）
切换动机：节奏驱动 — 开场建立，从黑场/远景切入（← 摄影部）
出场角色：银发少女（← 编剧部叙事架构师出场清单）
镜头：中近景，50mm，景深:浅，固定机位，平视
剪辑属性：硬切
打光：左上方金色主光，侧逆光勾勒轮廓，暖黄色调
角色：银发少女 坚毅咬牙 跪地持剑支撑 与长剑互动
站位：长剑插入处旁，仰面朝向镜头上方45度 / 画面中央偏右，中景 / 单膝跪地
背景：倒塌石柱，灰暗天空，远处火光

❌ 错误示范（缺少【完整画面】，AI无法画图）：
Shot 01（时间：0-2s）：
镜头：中近景，50mm，景深:浅...
剪辑属性：硬切
打光：...
→ 这种输出完全无效！没有【完整画面】AI根本不知道画面长什么样！

以下是你需要生成的格式（用实际内容替换占位符，每个Shot都必须有【完整画面】）：

Shot 01（时间：0-2s）：

【完整画面】
[用自然语言描述整帧画面的完整视觉内容——像上面示例那样，写出一幅"画面的样子"。必须包含：前景/中景/背景分别是什么、角色在画面中的位置和整体造型轮廓（不是微表情，而是"一个银发女孩蹲在画面左侧"这种整体视觉描述）、环境的空间构成、光线的实际画面效果、关键视觉元素的画面表现]

叙事节拍：[对应节拍编号+节拍名称]（← 编剧部叙事架构师）
切换动机：[动作/信息/情绪/节奏] — [具体说明]（← 摄影部）
出场角色：[本Shot中在场的所有角色/元素]（← 编剧部叙事架构师出场清单）
镜头：[景别]，[焦段XXmm]，[景深:浅/中/深]，[机位类型]，[角度]
剪辑属性：[硬切/长镜头/叠化/淡入淡出]
打光：[光源描述]，[色温/色调]，[照亮区域]
角色：[角色名] [表情定格] [动作定格] [与X的互动定格]
站位：[物品参照位置，如"长桌靠墙侧左端，面朝桌对面"] / [画面位置，如"画面左1/3，中景"] / [垂直状态，如"站立"/"蹲下"]
背景：[环境细节定格]
冲击力: [无/低/中/高/极限] — [冲击帧位置/速度线方向/蓄力-释放标记，或'日常场景，无冲击力元素']

Shot 02（时间：2-4s）：

【完整画面】
[同上，描述这一帧的完整视觉画面。每个Shot都必须有独立的完整画面描述，不能省略。]

叙事节拍：[对应节拍编号+节拍名称]（← 编剧部叙事架构师）
切换动机：[动作/信息/情绪/节奏] — [具体说明]（← 摄影部）
出场角色：[本Shot中在场的所有角色/元素]（← 编剧部叙事架构师出场清单）
镜头：[景别]，[焦段XXmm]，[景深:浅/中/深]，[机位类型]，[角度]
剪辑属性：[硬切/长镜头/叠化/淡入淡出]
打光：[光源描述]，[色温/色调]，[照亮区域]
角色：[角色名] [表情定格] [动作定格] [与X的互动定格]
站位：[物品参照位置] / [画面位置] / [垂直状态]
背景：[环境细节定格]

...（逐Shot直到本段最后一个Shot，Shot编号和时间必须与视频提示词完全对应）

---衔接方式：[硬切/叠化/淡入淡出/匹配剪辑]---

===== 段落2 =====
（如有段落2，按同样格式继续，Shot编号从01重新开始，因为每张3x3网格是独立图像）

【九宫格渲染说明】
每段固定9个Shot，产出一张3×3网格，格子从左到右、从上到下排列，格子左上角标Shot编号
如果某段经补充流程后仍不足9个Shot，剩余的格子留空（黑色背景），但必须在分镜表中标注"待补充"并说明原因
格子间细白线分割，画面内无其他文字标注，无AI水印，无错别字

负面提示词：
{negative_prompt}

【最重要】每个Shot必须有【完整画面】段——这是AI绘图唯一能理解的画面描述，没有它AI无法画图！Shot总数和编号必须与视频提示词一一对应，绝不能少或多！只输出分镜表本身，不加解释性文字。每个Shot的镜头字段必须包含焦段mm值。每个Shot的站位必须包含物品参照位置+画面位置+垂直状态（如"长桌靠墙侧左端，面朝桌对面 / 画面左1/3，中景 / 站立"）。分镜表只写静态定格，不写任何动态描述。每个Shot必须有叙事节拍、切换动机、出场角色三个字段，且从对应部门共识提取，不允许自由改写。"""
    else:
        storyboard_prompt = f"""You are the final summary AI. Based on all department debate results, generate STATIC KEYFRAME storyboards for AI image generation.

IMPORTANT: You MUST respond in English only. All output must be in English.

[STORYBOARD DEFINITION] The storyboard is a collection of static keyframes—each Shot is a frozen photograph, NOT an animation script.
- Write "at this camera position, this angle, this lighting, what expression the character has, what action is frozen, who they interact with, what the background is"
- Do NOT write any dynamic descriptions (e.g. "character walks from A to B", "camera moves in from lower right")
- Dynamic information (character movement, camera motion, transitions) belongs in the video prompt ONLY

User's original script:
{user_script}

Scene positive prompt:
{positive_prompt}

Character references:
{character_refs}

Department consensuses:
{consensus_text}

Cross-debate results:
{cross_text}

[KEY RULES]
1. Every shot MUST include focal length in mm and depth of field info
2. Every shot MUST be labeled with edit type: hard cut/long take/dissolve/fade
3. Every shot's position MUST include object-referenced position + camera-relative facing + frame position + vertical state (e.g. "left end of long table on wall side, 3/4 profile facing camera at 30 degrees / left 1/3 of frame, medium shot / standing"). Compass directions (NE/SW etc.) are FORBIDDEN
4. Storyboard contains ONLY static frozen states—NO dynamic descriptions
5. Total shot count is determined by the Storyboard department debate, NOT limited to 9
6. The Editing department splits into segments based on 4-15s limits, each segment exactly 9 shots (corresponding to a 3×3 grid, one keyframe per cell)
6b. [Anchor Breaking] When generating the storyboard, the Summary AI MUST ignore the Editing department's specific shot count allocation—the Editing department's shot count is for reference only. The Summary AI only takes the time ranges from the Editing department (e.g., "Segment 1: 0-8s, Segment 2: 8-16s"), then independently produces exactly 9 shots per segment. The Editing department's shot allocation is for their own use, not a constraint on the storyboard
7. [Keyframe Gap Fill Protocol] If a segment has fewer than 9 shots: Storyboard department consults Editing department to negotiate additional keyframes WITHOUT changing the overall timeline → supplemented shots re-run through Lighting/Spatial/etc. departments for confirmation → finalize each segment at exactly 9 shots. Supplemented keyframes MUST be logically consistent with existing narrative, no arbitrary insertions
8. [CRITICAL] Every Shot MUST have a [Complete Frame] section—describe the full visual content of the frame in natural language, including foreground/midground/background composition, character positions and overall silhouette, environment spatial composition, actual visual effect of lighting, how key visual elements appear in frame. This is the ONLY part an AI image tool can understand—without it, AI cannot draw the storyboard
9. [CRITICAL] The storyboard is a structured table, not free prose—every field MUST be extracted from the corresponding department's consensus, no free rewriting by AI:
   - Narrative Beat → extracted from Screenwriter Narrative Architect consensus
   - Switch Motivation → extracted from Cinematography consensus
   - On-Screen Characters → extracted from Screenwriter Narrative Architect on-screen roster
   - Camera/shot type/focal length → extracted from Cinematography consensus
   - Lighting → extracted from Lighting consensus
   - Position/Spatial → extracted from Spatial Planning consensus
   - Expression/Action → extracted from Screenwriter micro-expression/body language consensus
   - Background → extracted from Spatial + Screenwriter consensus
10. Every Shot's on-screen characters MUST match the Screenwriter on-screen roster—no characters may vanish or appear out of nowhere
11. Every shot transition MUST have a switch motivation—unmotivated transitions are forbidden
12. [DIALOGUE DURATION HARD CONSTRAINT] If a Shot contains character dialogue/lines, that Shot's duration MUST be ≥ word count × 0.4 seconds. For example, a 6-word line needs at least 2.4s ≈ 3s. It is ABSOLUTELY FORBIDDEN to assign 1s duration to a Shot with dialogue longer than 2-3 words—1s is only enough to speak 2-3 words. Purely visual Shots with no dialogue can be as short as 1-2s.
13. The negative prompt is a mandatory output—full negative prompt MUST appear at the end of the storyboard. No abbreviating, shortening, or skipping. If the negative prompt is empty, output 'No special negative prompt'.
14. Every segment opening MUST fully output the 'Unified Scene Prompt' and 'Unified Camera Language'—no abbreviating with 'same as above'.

Output strictly in this format (Shot count MUST match video prompt exactly):

{f"[Editing Department Split Plan] {editing_consensus}" if editing_consensus else ""}

===== Segment 1 =====

Scene Spatial Layout: [Reference Spatial Planning's object inventory + inter-object distances, write in full]

Unified Scene Prompt:
{positive_prompt}

Unified Camera Language: [Synthesize DP + Storyboard department consensus, MUST include focal length and DOF decisions]

{character_refs}

[✅ CORRECT EXAMPLE — You MUST write Complete Frame like this]
Shot 01 (Time: 0-2s):
[Complete Frame]
Center-right of frame, a silver-haired girl kneels on one knee on cracked white marble floor, right hand gripping a longsword plunged into the ground for support, left hand pressing a wound on her left shoulder. Her silver hair falls across her right shoulder, illuminated by a golden beam of light from the left side of the frame, the edges of her hair glowing. She looks up toward the upper left of frame with a resolute expression, a trace of blood at the corner of her mouth. Foreground: cracked stone fragments and drifting dust particles. Midground: the girl's full figure occupying 2/3 of frame height. Background: collapsed classical stone pillars and a gray overcast sky, with faint firelight in the distance casting a red glow on the underside of clouds. Overall cold blue-gray tones, with only the upper-left golden beam and distant firelight providing warm contrast.
Narrative Beat: Beat 1-Girl Kneeling (← Screenwriter Narrative Architect)
Switch Motivation: Rhythm-driven — Opening establishment, cut from black/wide shot (← Cinematography)
On-Screen Characters: Silver-haired girl (← Screenwriter Narrative Architect on-screen roster)
Camera: Medium close-up, 50mm, DOF: shallow, static, eye level
Edit Type: hard cut
Lighting: Golden key light from upper left, rim light outlining silhouette, warm yellow tones
Character: Silver-haired girl Resolute clenched jaw Kneeling on sword for support Interacting with longsword
Position: Beside the sword insertion point, looking up toward upper left 45 degrees from camera / Center-right of frame, medium shot / Kneeling on one knee
Background: Collapsed pillars, gray sky, distant firelight

❌ WRONG EXAMPLE (missing [Complete Frame], AI cannot draw):
Shot 01 (Time: 0-2s):
Camera: Medium close-up, 50mm, DOF: shallow...
Edit Type: hard cut
Lighting:...
→ This output is INVALID! Without [Complete Frame] AI has no idea what the picture looks like!

Now generate your output in this format (replace placeholders with actual content, every Shot MUST have [Complete Frame]):

Shot 01 (Time: 0-2s):

[Complete Frame]
[Describe the full visual content of this frame in natural language—like the example above, paint a picture of "what this frame looks like". Must include: what's in foreground/midground/background, character positions and overall silhouette, spatial composition of the environment, actual visual effect of lighting, how key visual elements appear in frame]

Narrative Beat: [Corresponding beat number + beat name] (← Screenwriter Narrative Architect)
Switch Motivation: [Action/Information/Emotion/Rhythm] — [Specific explanation] (← Cinematography)
On-Screen Characters: [All characters/elements present in this Shot] (← Screenwriter Narrative Architect on-screen roster)
Camera: [shot type], [focal length XXmm], [DOF: shallow/medium/deep], [camera type], [angle]
Edit Type: [hard cut/long take/dissolve/fade]
Lighting: [light source], [color temperature], [illuminated area]
Character: [character name] [frozen expression] [frozen action] [frozen interaction with X]
Position: [Object-referenced position] / [Camera-relative facing, e.g. "facing camera", "3/4 profile at 30 degrees", "back to camera"] / [Frame position, e.g. "left 1/3 of frame, medium shot"] / [Vertical state, e.g. "standing" / "crouching"]
Background: [frozen environment details]
Impact: [None/Low/Medium/High/Extreme] — [IMPACT FRAME position / speed line direction / charge-release marker, or 'Daily scene, no impact elements']

Shot 02 (Time: 2-4s):

[Complete Frame]
[Same as above—describe the full visual frame. Every Shot MUST have its own independent complete frame description, no omissions.]

Narrative Beat: [Corresponding beat number + beat name] (← Screenwriter Narrative Architect)
Switch Motivation: [Action/Information/Emotion/Rhythm] — [Specific explanation] (← Cinematography)
On-Screen Characters: [All characters/elements present in this Shot] (← Screenwriter Narrative Architect on-screen roster)
Camera: [shot type], [focal length XXmm], [DOF: shallow/medium/deep], [camera type], [angle]
Edit Type: [hard cut/long take/dissolve/fade]
Lighting: [light source], [color temperature], [illuminated area]
Character: [character name] [frozen expression] [frozen action] [frozen interaction with X]
Position: [Object-referenced position] / [Frame position] / [Vertical state]
Background: [frozen environment details]

... (continue per-Shot; Shot numbering and time MUST match video prompt exactly)

--- Transition: [hard cut/dissolve/fade/match cut] ---

===== Segment 2 =====
(If the Editing department plan has a Segment 2, continue in the same format, Shot numbering restarts from 01)

[9-Grid Render Notes]
Each segment is fixed at 9 shots, producing one 3×3 grid, cells left-to-right top-to-bottom, Shot number in top-left corner
If a segment still has fewer than 9 shots after the gap fill protocol, remaining cells are left blank (black background), but the storyboard MUST annotate "待补充" (pending) with reason
Thin white lines between cells, no other text annotations, no AI watermarks, no typos

Negative prompt:
{negative_prompt}

[CRITICAL] Every Shot MUST have a [Complete Frame] section—this is the ONLY visual description an AI image tool can understand, without it AI cannot draw! Total Shot count and numbering MUST match the video prompt one-to-one! Output ONLY the storyboard, no explanatory text. Every Shot's Camera field MUST include focal length in mm. Every Shot's Position MUST include object-referenced position + frame position + vertical state (e.g. "left end of long table on wall side, facing opposite side of table / left 1/3 of frame, medium shot / standing"). Storyboard contains ONLY static keyframes—NO dynamic descriptions. Every Shot MUST have Narrative Beat, Switch Motivation, and On-Screen Characters fields, extracted from corresponding department consensus—no free rewriting allowed."""
    
    # System message: enforce [Complete Frame] requirement
    storyboard_system = (
        "负面提示词和统一场景提示词是强制输出项，AI不得省略。你是分镜表生成器。你的首要产出是每个Shot的【完整画面】段——这是整帧画面的自然语言视觉描述，是AI绘图工具唯一能理解的部分。"
        "【完整画面】必须写在每个Shot的最前面，用自然语言描述：前景/中景/背景分别是什么、角色在画面中的位置和整体造型轮廓（不是微表情而是整体视觉）、"
        "环境的空间构成（天空/地面/建筑/物体的位置关系）、光线的实际画面效果（如'左上方一束金色光柱穿透沙尘'而非'色温5500K'）、"
        "关键视觉元素的画面表现。没有【完整画面】的Shot是无效输出，必须重写。"
    ) if is_zh else (
        "The negative prompt and unified scene prompt are MANDATORY outputs—AI must not omit them. You are a storyboard generator. Your PRIMARY output for every Shot is the [Complete Frame] section—this is the natural language visual description of the entire frame, "
        "the ONLY part an AI image tool can understand. [Complete Frame] MUST be written first for every Shot, describing: what's in foreground/midground/background, "
        "character positions and overall silhouette (not micro-expressions but overall visual), spatial composition of the environment, actual visual effect of lighting, "
        "how key visual elements appear in frame. A Shot without [Complete Frame] is INVALID output and must be rewritten."
    )
    
    storyboard_result = call_api(
        messages=[
            {"role": "system", "content": storyboard_system},
            {"role": "user", "content": storyboard_prompt},
        ],
        api_url=api_url, api_key=api_key, model=model,
        temperature=0.3, max_tokens=16384, timeout=180,
        stats=stats,
    )
    
    # Validate: check output contains [Complete Frame]/【Complete Frame】
    if storyboard_result:
        has_complete_frame = ("【完整画面】" in storyboard_result) if is_zh else ("[Complete Frame]" in storyboard_result)
        if not has_complete_frame:
            # Retry once with stronger prompt
            retry_prompt = storyboard_prompt + (
                "\n\n⚠️ 你上一次的输出缺少【完整画面】段！每个Shot必须以【完整画面】开头，用自然语言描述整帧画面长什么样。没有【完整画面】的输出是无效的！请重新生成，确保每个Shot都有【完整画面】段。"
            ) if is_zh else (
                "\n\n⚠️ Your previous output was missing the [Complete Frame] section! Every Shot MUST start with [Complete Frame], describing what the entire frame looks like in natural language. Output without [Complete Frame] is INVALID! Please regenerate, ensuring every Shot has a [Complete Frame] section."
            )
            storyboard_result = call_api(
                messages=[
                    {"role": "system", "content": storyboard_system},
                    {"role": "user", "content": storyboard_prompt},
                    {"role": "assistant", "content": storyboard_result},
                    {"role": "user", "content": retry_prompt.split("\n\n⚠️", 1)[1] if "⚠️" in retry_prompt else retry_prompt},
                ],
                api_url=api_url, api_key=api_key, model=model,
                temperature=0.3, max_tokens=16384, timeout=180,
                stats=stats,
            )
    
    # ===== Output 2: Video shot-by-shot prompts ([Keyframe]+[Dynamic Link] dual-layer) =====
    if is_zh:
        video_prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是最终总结AI。请根据以下所有部门的辩论结果，生成逐镜视频提示词。

【视频提示词定义】视频提示词是分镜表的完整扩展层：
- [关键帧]：直接来自分镜表的静态关键帧描述（照抄分镜表对应Shot的完整内容）
- [动态衔接]：从上一个Shot如何过渡到当前Shot——角色怎么从上一个动作过渡到本帧动作、镜头怎么从上一个机位运动到当前机位、打光怎么变化、音效怎么衔接
- 视频提示词 = 关键帧（拍什么）+ 动态衔接（怎么连），是最完整的拍摄指导

用户原始剧本：
{user_script}

场景正向提示词：
{positive_prompt}

空间板块共识（物品定位与动线）：
{spatial_consensus}

各部门辩论共识：
{consensus_text}

交叉辩论结果：
{cross_text}

{f"剪辑部拆分方案：{editing_consensus}" if editing_consensus else ""}

【关键规则】
1. 每个SHOT必须包含焦段mm值和景深
2. 每个SHOT必须标注剪辑属性
3. 【完整画面】是整帧画面的自然语言视觉描述——前景/中景/背景、角色位置和整体造型轮廓、环境空间构成、光线的实际画面效果、关键视觉元素的画面表现。这是AI绘图唯一能理解的部分，必须具体到能直接画图
4. [关键帧]部分是分镜表对应Shot的完整静态描述，必须包含：镜头/打光/角色表情定格/动作定格/互动定格/站位（物品参照位置+画面位置+垂直状态）/背景定格
5. [动态衔接]部分描述从上一帧到本帧的过渡——角色如何移动到位、镜头如何运动到位、打光如何变化、音效如何过渡
6. 第一个SHOT的[动态衔接]描述角色如何进入初始状态、镜头如何到位、打光如何建立
7. 单段视频≤15秒，总时长由剧本决定
8. 按剪辑部拆分方案分成多段
9. 音频绝对不含音乐
10. 【台词时长硬约束】如果某个SHOT包含角色台词/对白，该SHOT时长必须≥台词字数×0.4秒（中文约2.5字/秒，留余量）。例如6个字的台词至少需要2.4秒≈3秒。绝不允许台词超过2秒却只给1秒时长——1秒最多说完2-3个字。没有台词的纯画面SHOT可以短至1-2秒。
11. 统一负面提示词是必输出项——视频提示词开头的'统一负面提示词'段必须完整输出，不允许省略、缩写或跳过。
12. 每个SHOT的[动态衔接]中的'镜头过渡'必须包含具体的运镜方式（推/拉/摇/移/跟/固定+速度描述），不允许只写'镜头切换'或'镜头到位'这种模糊描述。

请严格按照以下格式输出：

统一场景提示词
{positive_prompt}

统一负面提示词
变形，扭曲，鬼影，模糊，过曝，闪烁，突变，溶解，多余肢体，复制人，穿模，低质量，画面撕裂，抖动过度，无声，3D渲染，蜡像，油腻，磨皮，卡通，水印，切镜感。{negative_prompt}

===== 段落1（0s - Xs）=====

【✅ 正确示例——必须像这样写完整画面】
SHOT 01
时间：0-2s
【完整画面】
画面中央偏右，一个银发少女单膝跪在碎裂的白色大理石地面上，右手握着插入地面的长剑支撑身体，左手按住左肩伤口。银色长发散落在右肩，被画面左侧金色光柱照亮，发丝边缘泛着光晕。她抬头仰望画面左上方。前景碎裂石块和飘散尘埃，中景少女全身像占画面2/3高度，背景倒塌古典石柱和灰暗天空，远处微弱火光映红云层底部。整体冷蓝灰色调，只有左上金色光柱和远处火光提供暖色对比。
叙事节拍：节拍1-少女跪地（← 编剧部叙事架构师）
切换动机：节奏驱动 — 开场建立（← 摄影部）
出场角色：银发少女（← 编剧部出场清单）
[关键帧]
镜头：中近景 50mm 景深:浅 固定机位 平视
打光：左上方金色主光，侧逆光勾勒轮廓
角色：银发少女 坚毅咬牙 跪地持剑支撑 与长剑互动
站位：长剑插入处旁，仰面朝向镜头上方45度 / 画面中央偏右，中景 / 单膝跪地
背景：倒塌石柱，灰暗天空，远处火光

[动态衔接]
角色入场/建立：少女从画面右侧跑入，滑跪至长剑插入处，剑插入地面
镜头到位：固定机位，从全景缓推至中近景
打光建立：金色光柱从左上方照射建立，尘埃在光柱中可见
音效衔接：远处雷声渐弱，剑插入石地的金属撞击声

音频：风声+金属撞击声+少女急促呼吸（绝对不含音乐）

❌ 错误示范（缺少【完整画面】，AI无法画图）：
SHOT 01
时间：0-2s
[关键帧]
镜头：中近景 50mm...
打光：...
→ 这种输出完全无效！没有【完整画面】AI根本不知道画面长什么样！

以下是你需要生成的格式（用实际内容替换占位符，每个SHOT都必须有【完整画面】）：

SHOT 01
时间：0-2s
【完整画面】
[用自然语言描述整帧画面的完整视觉内容——像上面示例那样，写出一幅"画面的样子"。必须包含：前景/中景/背景、角色位置和整体造型轮廓、环境空间构成、光线实际画面效果、关键视觉元素的画面表现]
叙事节拍：[节拍编号+名称]（← 编剧部叙事架构师）
切换动机：[动作/信息/情绪/节奏] — [说明]（← 摄影部）
出场角色：[本SHOT在场角色]（← 编剧部出场清单）
[关键帧]
镜头：[景别] [焦段XXmm] [景深:浅/中/深] [机位] [角度]
打光：[光源描述]
角色：[名] [表情定格] [动作定格] [互动定格]
站位：[物品参照位置，面朝XX] / [画面位置] / [垂直状态]
背景：[环境定格]
冲击力: [无/低/中/高/极限] — [具体说明]

[动态衔接]
角色入场/建立：[角色如何进入本帧初始状态]
镜头到位：[镜头如何从上一机位运动到当前机位（首个SHOT则描述如何建立机位）]
打光建立：[光源如何建立或变化]
音效衔接：[从上一帧的音效如何过渡（首个SHOT则描述环境音如何建立）]

音频：[环境音+动作音效+角色声音]（绝对不含音乐）

SHOT 02
时间：2-4s
【完整画面】
[同上，描述这一帧的完整视觉画面。每个SHOT都必须有独立的完整画面描述，不能省略。]
叙事节拍：[节拍编号+名称]（← 编剧部叙事架构师）
切换动机：[动作/信息/情绪/节奏] — [说明]（← 摄影部）
出场角色：[本SHOT在场角色]（← 编剧部出场清单）
[关键帧]
镜头：[景别] [焦段XXmm] [景深:浅/中/深] [机位] [角度]
打光：[光源描述]
角色：[名] [表情定格] [动作定格] [互动定格]
站位：[物品参照位置] / [画面位置] / [垂直状态]
背景：[环境定格]

[动态衔接]
切换依据：[从上一SHOT切到本SHOT的动机——是因为角色动作、情绪转折、还是叙事节奏需要]
角色过渡：[角色如何从SHOT 01动作过渡到本帧动作，移动路径（引用空间板块动线）]
镜头过渡：[镜头如何从上一机位运动到当前机位]
打光变化：[光源如何变化]
音效衔接：[音效如何过渡]

音频：[环境音+动作音效+角色声音]（绝对不含音乐）

...（逐SHOT到本段结束）

---衔接方式：[硬切/叠化/淡入淡出/匹配剪辑]---

===== 段落2（Xs - Xs）=====

统一场景提示词：[同段落1的统一场景提示词，必须完整重申，不允许省略]

SHOT XX
...（逐SHOT到本段结束）

重要：
1. 音频只包含环境音、动作拟音、角色声音，绝对不含音乐
2. 【完整画面】和[关键帧]和[动态衔接]必须三层分开写清楚，不能混在一起
3. 【完整画面】描述整帧画面"长什么样"，[关键帧]照抄分镜表的静态技术参数，[动态衔接]补充动态过渡信息
4. 每个SHOT的运镜必须包含焦段mm值
5. 站位必须包含物品参照位置+镜头相对朝向+画面位置+垂直状态，朝向严禁罗盘方向
6. 只输出视频提示词本身，不要加任何解释性文字"""
    else:
        video_prompt = f"""You are the final summary AI. Based on all department debate results, generate per-shot video prompts.

IMPORTANT: You MUST respond in English only. All output must be in English.

[VIDEO PROMPT DEFINITION] Video prompts are the complete expansion layer of the storyboard:
- [Key Frame]: The static keyframe description copied directly from the corresponding storyboard Shot
- [Dynamic Transition]: How to transition from the previous Shot—how the character moves from the previous action to this frame's action, how the camera moves from the previous position, how lighting changes, how sound transitions
- Video Prompt = Key Frame (what to shoot) + Dynamic Transition (how to connect), the most complete shooting guide

User's original script:
{user_script}

Scene positive prompt:
{positive_prompt}

Spatial Planning consensus (object positioning and movement paths):
{spatial_consensus}

Department consensuses:
{consensus_text}

Cross-debate results:
{cross_text}

{f"Editing department split plan: {editing_consensus}" if editing_consensus else ""}

[KEY RULES]
1. Every SHOT MUST include focal length in mm and DOF
2. Every SHOT MUST be labeled with edit type
3. [Complete Frame] is the natural language visual description of the entire frame—foreground/midground/background, character positions and overall silhouette, environment spatial composition, actual visual effect of lighting, how key visual elements appear in frame. This is the ONLY part an AI image tool can understand—it must be specific enough to draw directly from
4. [Key Frame] section contains the complete static description from the storyboard: camera/lighting/character expression/character action/interaction/position (object-referenced position + frame position + vertical state)/background
5. [Dynamic Transition] section describes the transition from previous frame—how the character moves into position, how the camera moves into position, how lighting changes, how sound transitions
6. The first SHOT's [Dynamic Transition] describes how characters enter their initial state, how the camera is established, how lighting is set up
7. Single video ≤15s; total duration determined by the script
8. Follow the Editing department split plan into segments
9. Audio ABSOLUTELY NO MUSIC
10. [DIALOGUE DURATION HARD CONSTRAINT] If a SHOT contains character dialogue/lines, that SHOT's duration MUST be ≥ word count × 0.4 seconds. For example, a 6-word line needs at least 2.4s ≈ 3s. It is ABSOLUTELY FORBIDDEN to assign 1s duration to a SHOT with dialogue longer than 2-3 words—1s is only enough to speak 2-3 words. Purely visual SHOTs with no dialogue can be as short as 1-2s.
11. The unified negative prompt is a mandatory output—full unified negative prompt MUST appear at the beginning of the video prompt. No abbreviating, shortening, or skipping.
12. Every SHOT's [Dynamic Transition] camera transition MUST include a specific camera movement method (push/pull/pan/track/follow/static + speed description). Vague descriptions like 'camera switches' or 'camera in position' are NOT allowed.

Generate strictly in this format:

Unified Scene Prompt
{positive_prompt}

Unified Negative Prompt
distortion, ghosting, blur, overexposure, flickering, mutation, dissolution, extra limbs, clones, clipping, low quality, screen tearing, excessive shake, silence, waxy, oily, cartoon, watermark, hard cuts. {negative_prompt}

===== Segment 1 (0s - Xs) =====

[✅ CORRECT EXAMPLE — You MUST write Complete Frame like this]
SHOT 01
Time: 0-2s
[Complete Frame]
Center-right of frame, a silver-haired girl kneels on one knee on cracked white marble floor, right hand gripping a longsword plunged into the ground for support, left hand pressing a wound on her left shoulder. Her silver hair falls across her right shoulder, illuminated by a golden beam of light from the left side of the frame, the edges of her hair glowing. She looks up toward the upper left of frame. Foreground: cracked stone fragments and drifting dust particles. Midground: the girl's full figure occupying 2/3 of frame height. Background: collapsed classical stone pillars and a gray overcast sky, with faint firelight in the distance casting a red glow on the underside of clouds. Overall cold blue-gray tones, with only the upper-left golden beam and distant firelight providing warm contrast.
Narrative Beat: Beat 1-Girl Kneeling (← Screenwriter Narrative Architect)
Switch Motivation: Rhythm-driven — Opening establishment (← Cinematography)
On-Screen Characters: Silver-haired girl (← Screenwriter on-screen roster)
[Key Frame]
Camera: Medium close-up 50mm DOF:shallow Static Eye level
Lighting: Golden key light from upper left, rim light outlining silhouette
Character: Silver-haired girl Resolute clenched jaw Kneeling on sword for support Interacting with longsword
Position: Beside the sword insertion point, looking up toward upper left 45 degrees from camera / Center-right of frame, medium shot / Kneeling on one knee
Background: Collapsed pillars, gray sky, distant firelight

[Dynamic Transition]
Character entry/establishment: Girl runs in from right side of frame, slides to kneel at the sword insertion point, sword plunges into ground
Camera establishment: Static position, slow push from wide to medium close-up
Lighting establishment: Golden beam from upper left establishes, dust particles visible in the beam
Sound transition: Distant thunder fading, metallic impact of sword piercing stone

Audio: Wind + metallic impact + girl's rapid breathing (ABSOLUTELY NO MUSIC)

❌ WRONG EXAMPLE (missing [Complete Frame], AI cannot draw):
SHOT 01
Time: 0-2s
[Key Frame]
Camera: Medium close-up 50mm...
Lighting:...
→ This output is INVALID! Without [Complete Frame] AI has no idea what the picture looks like!

Now generate your output in this format (replace placeholders with actual content, every SHOT MUST have [Complete Frame]):

SHOT 01
Time: 0-2s
[Complete Frame]
[Describe the full visual content of this frame in natural language—like the example above, paint a picture of "what this frame looks like". Must include: what's in foreground/midground/background, character positions and overall silhouette, spatial composition of the environment, actual visual effect of lighting, how key visual elements appear in frame]
Narrative Beat: [Beat number + name] (← Screenwriter Narrative Architect)
Switch Motivation: [Action/Information/Emotion/Rhythm] — [explanation] (← Cinematography)
On-Screen Characters: [Characters present in this SHOT] (← Screenwriter on-screen roster)
[Key Frame]
Camera: [shot type] [focal length XXmm] [DOF: shallow/medium/deep] [camera setup] [angle]
Lighting: [light source description]
Character: [name] [frozen expression] [frozen action] [frozen interaction]
Position: [Object-referenced position] / [Camera-relative facing, e.g. "facing camera", "3/4 profile at 30 degrees", "back to camera"] / [Frame position] / [Vertical state]
Background: [frozen environment]

[Dynamic Transition]
Character entry/establishment: [how characters enter their initial state for this frame]
Camera establishment: [how camera moves to this position (for first SHOT, describe how position is established)]
Lighting establishment: [how lighting is established or changes]
Sound transition: [how sound transitions from previous frame (for first SHOT, describe how ambient sound is established)]

Audio: [ambient + foley + character voice] (ABSOLUTELY NO MUSIC)

SHOT 02
Time: 2-4s
[Complete Frame]
[Same as above—describe the full visual frame. Every SHOT MUST have its own independent complete frame description, no omissions.]
Narrative Beat: [Beat number + name] (← Screenwriter Narrative Architect)
Switch Motivation: [Action/Information/Emotion/Rhythm] — [explanation] (← Cinematography)
On-Screen Characters: [Characters present in this SHOT] (← Screenwriter on-screen roster)
[Key Frame]
Camera: [shot type] [focal length XXmm] [DOF: shallow/medium/deep] [camera setup] [angle]
Lighting: [light source description]
Character: [name] [frozen expression] [frozen action] [frozen interaction]
Position: [Object-referenced position] / [Frame position] / [Vertical state]
Background: [frozen environment]
Impact: [None/Low/Medium/High/Extreme] — [specific details]

[Dynamic Transition]
Switch Basis: [The motivation for switching from the previous SHOT to this one—is it character action, emotional shift, or narrative rhythm?]
Character transition: [how character moves from SHOT 01 action to this frame's action, movement path (reference Spatial Planning)]
Camera transition: [how camera moves from previous position to this one]
Lighting change: [how lighting changes]
Sound transition: [how sound transitions]

Audio: [ambient + foley + character voice] (ABSOLUTELY NO MUSIC)

... (continue to end of this segment)

--- Transition: [hard cut/dissolve/fade/match cut] ---

===== Segment 2 (Xs - Xs) =====

Unified Scene Prompt: [Same as Segment 1's Unified Scene Prompt, MUST be fully restated, no abbreviating]

SHOT XX
... (continue to end of this segment)

IMPORTANT:
1. Audio contains ONLY ambient sound, foley, and character voice—ABSOLUTELY NO MUSIC
2. [Complete Frame] and [Key Frame] and [Dynamic Transition] must be clearly separated in three layers, not mixed
3. [Complete Frame] describes what the frame "looks like"; [Key Frame] copies the storyboard's static technical parameters; [Dynamic Transition] adds dynamic transition info
4. Every SHOT's Camera field MUST include focal length in mm
5. Position must include object-referenced position + frame position + vertical state
6. Output ONLY the video prompt itself, no explanatory text."""
    
    # System message: enforce [Complete Frame] requirement
    video_system = (
        "统一场景提示词和统一负面提示词是强制输出项，每个段落都必须包含。每个SHOT的[动态衔接]中的镜头过渡必须有具体运镜方式。你是视频提示词生成器。每个SHOT必须包含【完整画面】→[关键帧]→[动态衔接]三层结构，其中【完整画面】是最重要的部分。"
        "【完整画面】是整帧画面的自然语言视觉描述，是AI绘图工具唯一能理解的部分——描述前景/中景/背景、角色位置和整体造型轮廓、"
        "环境空间构成、光线实际画面效果。没有【完整画面】的SHOT是无效输出，必须重写。"
    ) if is_zh else (
        "The unified scene prompt and unified negative prompt are MANDATORY outputs—every segment MUST include them. Every SHOT's [Dynamic Transition] camera transition MUST have a specific camera movement method. You are a video prompt generator. Every SHOT MUST include [Complete Frame] → [Key Frame] → [Dynamic Transition] three-layer structure, "
        "where [Complete Frame] is the MOST IMPORTANT part. [Complete Frame] is the natural language visual description of the entire frame, "
        "the ONLY part an AI image tool can understand—describing foreground/midground/background, character positions and overall silhouette, "
        "environment spatial composition, actual visual effect of lighting. A SHOT without [Complete Frame] is INVALID output and must be rewritten."
    )
    
    video_result = call_api(
        messages=[
            {"role": "system", "content": video_system},
            {"role": "user", "content": video_prompt},
        ],
        api_url=api_url, api_key=api_key, model=model,
        temperature=0.3, max_tokens=16384, timeout=180,
        stats=stats,
    )
    
    # Validate: check output contains [Complete Frame]/[Complete Frame]
    if video_result:
        has_complete_frame = ("【完整画面】" in video_result or "[完整画面]" in video_result) if is_zh else ("[Complete Frame]" in video_result)
        if not has_complete_frame:
            retry_video_msg = (
                "⚠️ 你的输出缺少【完整画面】段！每个SHOT必须包含【完整画面】→[关键帧]→[动态衔接]三层结构。"
                "【完整画面】是最重要的部分，用自然语言描述整帧画面长什么样。没有【完整画面】的输出无效，请重新生成。"
            ) if is_zh else (
                "⚠️ Your output is missing the [Complete Frame] section! Every SHOT MUST include [Complete Frame] → [Key Frame] → [Dynamic Transition] three layers. "
                "[Complete Frame] is the most important part—describe what the entire frame looks like in natural language. Output without [Complete Frame] is INVALID, please regenerate."
            )
            video_result = call_api(
                messages=[
                    {"role": "system", "content": video_system},
                    {"role": "user", "content": video_prompt},
                    {"role": "assistant", "content": video_result},
                    {"role": "user", "content": retry_video_msg},
                ],
                api_url=api_url, api_key=api_key, model=model,
                temperature=0.3, max_tokens=16384, timeout=180,
                stats=stats,
            )
    
    return {
        "storyboard_prompt": storyboard_result or "九宫格分镜表生成失败",
        "video_prompt": video_result or "逐镜视频提示词生成失败",
    }

# ============ Academic Summary (for academic mode) ============

def run_academic_summary(
    user_topic: str,
    all_consensus: Dict[str, str],
    cross_results: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
) -> Dict:
    """
    Academic mode summary: search real papers + synthesize debate consensus into academic review.
    Two-step: (1) Search real papers via AcademicSearchEngine (2) LLM synthesizes report with real references.
    """
    is_zh = lang == "zh"

    # Build all department consensus
    consensus_parts = []
    for dept_key, consensus in all_consensus.items():
        dept = DEPARTMENTS.get(dept_key, {})
        name = dept.get("zh_name", dept_key) if is_zh else dept.get("en_name", dept_key)
        if consensus:
            consensus_parts.append(f"### {name}\n{consensus}")
    consensus_text = "\n\n".join(consensus_parts)

    # Cross-debate results
    cross_parts = []
    for cr in cross_results:
        if isinstance(cr, dict):
            title = cr.get("topic", "Cross-debate")
            result = cr.get("debate_result", cr.get("result", cr.get("consensus", "")))
        else:
            title = "Cross-debate"
            result = str(cr)
        if result:
            cross_parts.append(f"### {title}\n{result}")
    cross_text = "\n\n".join(cross_parts)

    if not consensus_text and not cross_text:
        return {"final_report": "", "consensus_report": ""}

    # Sanitize consensus_text: replace department names with neutral academic labels
    # so the LLM doesn't reproduce system terminology in the report
    import re as _re_san
    _dept_replacements_zh = {
        "文献检索组": "文献综述分析", "元数据精查组": "文献质量评估",
        "引用网络组": "引文网络分析", "方法论审查组": "方法论评述",
        "数据验证组": "实证验证分析", "反方质疑组": "批判性审视",
        "主题聚类组": "主题分类分析", "可视化组": "可视化分析",
        "报告整合组": "综合分析", "程序部": "方法实现",
        "教程部": "实践指南",
    }
    _dept_replacements_en = {
        "Literature Search Group": "literature review analysis",
        "Metadata Verification Group": "literature quality assessment",
        "Citation Network Group": "citation network analysis",
        "Methodology Review Group": "methodology review",
        "Data Validation Group": "empirical validation analysis",
        "Counter-argument Group": "critical examination",
        "Topic Clustering Group": "thematic analysis",
        "Visualization Group": "visualization analysis",
        "Report Integration Group": "comprehensive analysis",
        "Programming Department": "method implementation",
        "Tutorial Department": "practical guide",
    }
    for _old, _new in _dept_replacements_zh.items():
        consensus_text = consensus_text.replace(_old, _new)
        cross_text = cross_text.replace(_old, _new)
    for _old, _new in _dept_replacements_en.items():
        consensus_text = consensus_text.replace(_old, _new)
        cross_text = cross_text.replace(_old, _new)

    # === Step 1: Search for real papers ===
    paper_references = ""
    papers_found = []
    all_papers = []  # Initialize to prevent NameError if try block fails

    # Extract core search query from user_topic (which may be a structured plan)
    search_query = user_topic
    if "\n" in user_topic or "：" in user_topic or ":" in user_topic:
        # user_topic is a structured plan, extract the research topic line
        import re
        topic_match = re.search(r'(?:研究主题|Research Topic|Topic)\s*[:：]\s*(.+)', user_topic)
        if topic_match:
            search_query = topic_match.group(1).strip()
        else:
            # Fallback: use first non-empty line, strip labels
            first_line = user_topic.split("\n")[0].strip()
            search_query = re.sub(r'^[^：:]+[：:]\s*', '', first_line)
        # Clean up: remove newlines for API query
        search_query = search_query.replace("\n", " ").strip()

    # v4.5: Bilingual search — also search with English keywords for better arXiv/S2 coverage
    _ZH_EN_MAP = {
        "能源": "energy", "经济": "economics", "经济学": "economics",
        "环境": "environmental", "规制": "regulation", "政策": "policy",
        "效率": "efficiency", "碳": "carbon", "排放": "emission",
        "电力": "electricity", "可再生": "renewable", "气候": "climate",
        "金融": "finance", "管理": "management", "市场": "market",
        "创新": "innovation", "技术": "technology", "产业": "industry",
        "发展": "development", "可持续": "sustainable", "绿色": "green",
        "转型": "transition", "投资": "investment", "消费": "consumption",
        "贸易": "trade", "全球化": "globalization", "数字化": "digital",
        "机器学习": "machine learning", "人工智能": "artificial intelligence",
        "预测": "forecasting", "优化": "optimization", "评估": "assessment",
        # AI / Ethics / Governance core terms
        "伦理": "ethics", "治理": "governance", "公平": "fairness",
        "偏见": "bias", "隐私": "privacy", "算法": "algorithm",
        "深度学习": "deep learning", "神经网络": "neural network",
        "透明": "transparency", "可解释": "interpretability",
        "问责": "accountability", "歧视": "discrimination",
        "对齐": "alignment", "价值对齐": "value alignment",
        "安全": "safety", "风险": "risk", "审计": "audit",
        "监管": "regulation", "合规": "compliance", "法律": "law",
        "社会": "social", "信任": "trust", "责任": "responsibility",
        "涌现": "emergence", "鲁棒": "robustness", "对抗": "adversarial",
        "数据": "data", "模型": "model", "部署": "deployment",
        "监控": "monitoring", "人机交互": "human-computer interaction",
        "自动化": "automation", "就业": "employment", "不平等": "inequality",
        "信息": "information", "推荐系统": "recommendation system",
        "社交网络": "social network", "虚假信息": "misinformation",
        "网络安全": "cybersecurity", "知识产权": "intellectual property",
        "可复现": "reproducibility", "因果推断": "causal inference",
        "多智能体": "multi-agent", "博弈论": "game theory",
        "大语言模型": "large language model", "生成模型": "generative model",
        "强化学习": "reinforcement learning", "联邦学习": "federated learning",
        "差分隐私": "differential privacy", "面部识别": "facial recognition",
        "数字鸿沟": "digital divide", "全球治理": "global governance",
        "伦理框架": "ethical framework", "影响评估": "impact assessment",
        "算法审计": "algorithmic audit", "透明度报告": "transparency report",
        "数据保护": "data protection", "隐私保护": "privacy protection",
        "机器伦理": "machine ethics", "AI伦理": "AI ethics",
        "技术伦理": "technology ethics", "研究伦理": "research ethics",
        "生成式AI": "generative AI", "自主系统": "autonomous systems",
        "监控": "surveillance", "面部识别": "facial recognition",
        "生物识别": "biometrics", "欺诈检测": "fraud detection",
        "异常检测": "anomaly detection", "加密货币": "cryptocurrency",
        "元宇宙": "metaverse", "Web3": "Web3", "区块链": "blockchain",
    }
    en_query = ""
    if any('\u4e00' <= c <= '\u9fff' for c in search_query):
        en_parts = []
        remaining = search_query
        for zh, en in sorted(_ZH_EN_MAP.items(), key=lambda x: -len(x[0])):
            if zh in remaining:
                en_parts.append(en)
                remaining = remaining.replace(zh, " ")
        remaining_words = [w.strip() for w in remaining.split() if w.strip() and len(w.strip()) > 1]
        en_parts.extend(remaining_words)
        en_query = " ".join(en_parts[:5]) if en_parts else search_query
    print(f"Academic search query: \"{search_query}\" (extracted from user_topic of {len(user_topic)} chars)")
    if en_query and en_query != search_query:
        print(f"Academic search (English): \"{en_query}\"")

    try:
        from academic.search_engine import AcademicSearchEngine
        import time as _time

        # === v0.7.0 Pipeline Integration: Domain Config Generation ===
        # Generate domain_config with query_rotation (6-10 English search queries),
        # exclusion_signals (15-25 exclusion keywords), tier_definitions (core/method/background).
        # This connects run_academic_summary to the same proven pipeline as run_pipeline.py phase4_search_v6().
        domain_config = None
        try:
            from domain_config_generator import generate_domain_config

            def _dc_llm_call(system_prompt: str, user_message: str, temperature: float = 0.2) -> str:
                """Local LLM call for domain_config generation (same interface as run_pipeline.llm_call)"""
                import requests as _req
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": temperature,
                    "max_tokens": 32768,
                }
                try:
                    resp = _req.post(api_url, headers=headers, json=payload, timeout=120)
                    resp.raise_for_status()
                    result = resp.json()
                    return result["choices"][0]["message"]["content"]
                except Exception as e:
                    print(f"  [LLM ERROR in domain_config] {e}")
                    return ""

            # Translate Chinese topic to English before generating domain config
            # generate_domain_config's LLM prompt expects English topics; Chinese input
            # produces Chinese query_rotation which returns garbage from arXiv/S2/OpenAlex
            dc_topic = search_query
            if any('\u4e00' <= c <= '\u9fff' for c in search_query):
                try:
                    _trans_prompt = "You are a professional academic translator. Translate the following Chinese research topic into a concise English academic phrase (5-12 words). Output ONLY the English translation, nothing else."
                    _trans_result = _dc_llm_call(_trans_prompt, search_query, temperature=0.1)
                    _trans_result = _trans_result.strip().strip('"').strip("'").strip(".")
                    if _trans_result and not any('\u4e00' <= c <= '\u9fff' for c in _trans_result):
                        dc_topic = _trans_result
                        print(f"Topic translated: \"{search_query}\" → \"{dc_topic}\"")
                    else:
                        # Fallback: use en_query from _ZH_EN_MAP if available
                        if en_query:
                            dc_topic = en_query
                            print(f"Topic translated (fallback map): \"{search_query}\" → \"{dc_topic}\"")
                        else:
                            print(f"Topic translation failed, using original: \"{search_query}\"")
                except Exception as trans_err:
                    print(f"Topic translation error: {trans_err}, using en_query fallback")
                    if en_query:
                        dc_topic = en_query
                    # else: keep Chinese, generate_domain_config will still try

            print(f"Generating domain config for: \"{dc_topic}\"...")
            domain_config = generate_domain_config(dc_topic, _dc_llm_call)
            if domain_config and domain_config.get("query_rotation"):
                _qr = domain_config["query_rotation"]
                _es = domain_config.get("exclusion_signals", [])
                print(f"Domain config generated: {len(_qr)} search queries, "
                      f"{len(_es)} exclusion signals, "
                      f"tiers: {list(domain_config.get('tier_definitions', {}).keys())}")
            else:
                print("Domain config generation returned no query_rotation, using fallback search")
                domain_config = None
        except Exception as dc_err:
            print(f"Domain config generation failed: {dc_err}, using fallback search")
            domain_config = None

        # === Multi-query search with cross-query deduplication (pipeline integration) ===
        se = AcademicSearchEngine(
            min_citations=3,
            min_results=20,
            include_preprints=True,  # v0.8.2: Preprints now filtered through _compute_relevance
            domain_config=domain_config,  # v0.7.0: Enable config-driven exclusion filtering
        )

        # Build search query list: use query_rotation if available, otherwise bilingual fallback
        # v0.8.2: Skip Chinese queries — OpenAlex/S2/arXiv all return garbage for Chinese text
        _is_chinese = lambda s: any('\u4e00' <= c <= '\u9fff' for c in s)
        if domain_config and domain_config.get("query_rotation"):
            # Filter out Chinese queries from query_rotation
            # (LLM may generate Chinese queries even for English topics)
            _total_qr = len(domain_config["query_rotation"])
            search_queries = [q for q in domain_config["query_rotation"] if not _is_chinese(q)]
            _filtered_zh = _total_qr - len(search_queries)
            if _filtered_zh > 0:
                print(f"  Filtered {_filtered_zh} Chinese queries from query_rotation")
            # Prepend English search_query only (skip Chinese)
            if search_query and search_query not in search_queries and not _is_chinese(search_query):
                search_queries.insert(0, search_query)
            if en_query and en_query != search_query and en_query not in search_queries:
                search_queries.append(en_query)
        else:
            # Fallback: English queries only
            search_queries = []
            if en_query and not _is_chinese(en_query):
                search_queries.append(en_query)
            if search_query and not _is_chinese(search_query) and search_query not in search_queries:
                search_queries.append(search_query)
            # Last resort: if no English query available, use whatever we have
            if not search_queries:
                search_queries = [search_query or en_query or "machine learning"]

        print(f"Academic search: {len(search_queries)} queries to execute")
        for i, q in enumerate(search_queries):
            print(f"  Query {i+1}/{len(search_queries)}: \"{q}\"")

        all_papers_raw = []
        all_preprints_raw = []
        seen_titles = set()
        total_fetched = 0

        for q in search_queries:
            try:
                result = se.search(q, max_results_per_source=30)
                papers = result.get("papers", [])
                preprints = result.get("preprints", [])
                q_stats = result.get("stats", {})

                total_fetched += q_stats.get("total_fetched", 0)
                print(f"  \"{q}\" → raw={q_stats.get('total_fetched', 0)}, "
                      f"filtered={q_stats.get('after_filter', 0)}, "
                      f"preprints={q_stats.get('preprint_count', 0)}")

                # Cross-query deduplication (same logic as phase4_search_v6)
                for p in papers:
                    title_key = p.title[:30].lower()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        all_papers_raw.append(p)

                for p in preprints:
                    title_key = p.title[:30].lower()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        all_preprints_raw.append(p)
            except Exception as qe:
                print(f"  Search error for \"{q}\": {qe}")

            # Rate limit: wait 3s between queries (same as phase4_search_v6)
            if q != search_queries[-1]:
                _time.sleep(3)

        papers_found = all_papers_raw
        preprints = all_preprints_raw
        # v0.8.2: Use preprints as supplement only when journal papers are insufficient
        # Preprints are already filtered through _compute_relevance in search_engine.py
        supplement_needed = max(0, 15 - len(papers_found))
        all_papers = papers_found + preprints[:supplement_needed]

        # Build reference list
        if all_papers:
            ref_lines = []
            for i, p in enumerate(all_papers[:20], 1):
                authors_str = ", ".join(p.authors[:3]) if p.authors else "Unknown"
                if len(p.authors) > 3:
                    authors_str += " et al."
                ref_lines.append(f"[{i}] {authors_str} ({p.year}). {p.title}. {p.journal}, cited by {p.citation_count}. DOI: {p.doi or 'N/A'}")
            paper_references = "\n".join(ref_lines)
            print(f"Academic search complete: {total_fetched} fetched, "
                  f"{len(papers_found)} unique papers, {len(preprints)} preprints, "
                  f"{len(all_papers)} total references")
            _se_stats = {
                "total_fetched": total_fetched,
                "after_filter": len(papers_found),
                "preprint_count": len(preprints),
            }
        else:
            _se_stats = {"total_fetched": total_fetched, "after_filter": 0, "preprint_count": 0}
    except ImportError:
        print("⚠️ Academic search skipped: academic/search_engine.py not found or import error")
        paper_references = ""
        _se_stats = {}
    except Exception as e:
        import traceback
        err_type = type(e).__name__
        if "Connection" in str(e) or "Timeout" in str(e) or "timeout" in str(e):
            print(f"⚠️ Academic search failed (network): {err_type}: {e}")
        elif "key" in str(e).lower() or "auth" in str(e).lower() or "401" in str(e) or "403" in str(e):
            print(f"⚠️ Academic search failed (auth): {err_type}: {e}")
        else:
            print(f"⚠️ Academic search failed ({err_type}): {e}")
            traceback.print_exc()
        paper_references = ""
        _se_stats = {}

    # === Step 2: Build LLM prompt with real papers ===
    has_papers = bool(paper_references)

    if is_zh:
        if has_papers:
            system_prompt = """【重要】你必须使用中文回答。所有输出必须是中文。

你是一位资深学术综述撰写专家。你的任务是将多个学术辩论组的共识结果与真实文献检索结果整合为一篇结构完整的学术动向综述报告。

【硬性规则】
1. 这是学术综述，不是动画脚本或分镜表。严禁出现任何动画/视觉/分镜术语（如"冲击帧""蓄力-释放""速度线""残影""停帧""九宫格""分镜"等）
2. 每个章节必须有实质性内容段落（每节至少400字），每个章节至少3-4段实质性内容，不能只有标题或要点列表
3. 整合各部门辩论中有价值的研究发现，但不得描述本系统/共识管线自身的检索流程、筛选机制或基础设施（如"先广后精""四级筛选""DOI溯源""多源定制检索"等系统方法论术语）。报告内容必须全部围绕研究领域本身的学术内容展开。禁止在报告正文中出现以下系统内部术语："辩论共识""文献检索组""引用网络组""数据分析组""可视化组""程序部""教程部""编剧部""摄影指导部""分镜部""空间设计部""灯光部""特效部""剪辑部""音效部"等部门名称，以及"多部门协作""辩论流程""共识生成"等系统流程描述——这些是系统内部概念，读者不需要知道。如果需要引用某方面分析，直接以学术方式表达（如"已有研究表明…"而非"数据分析组指出…"）。即使输入材料中出现了上述术语，报告正文中也不得出现。即使输入材料中出现了上述术语，报告正文中也不得出现
4. 参考文献必须且只能使用下方提供的真实论文列表，严禁自行编造任何文献。不得标注"示范性引用""佚名"等。如果提供的论文不足，减少参考文献数量，不得补充虚构文献。引用论文时，只能描述论文标题和摘要中实际出现的研究内容、方法和结论，严禁编造论文中不存在的研究发现——如果论文摘要没有提到某个观点，不得将该观点归因于该论文
5. 在报告中适当引用真实论文的结论来支撑辩论观点，每篇参考文献至少在正文中被引用一次。引用格式必须使用数字方括号标记（如[1]、[2,3]、[1-3]），严禁使用作者-年份格式（如van Eck & Waltman (2017)）。引用编号必须与论点内容匹配——例如不要用一篇1997年的石油价格论文来支撑2020年代的可再生能源政策论点。每个引用必须对应与该论点主题相关的参考文献。正文中必须频繁出现[1]、[2]等引用标记——每个主要论点段落至少包含1个引用，不得只在末尾参考文献列表中列出编号而在正文中不引用
6. 禁止自引用——报告中不得出现"本文第X节""本节""上文提到""如第X章所述"等引用报告自身章节结构的表述。所有学术论点必须用外部文献的结论来支撑，不得以报告自身的结构组织作为论点内容。参考文献条目格式为：[序号] 作者. (年份). 标题. 期刊。不得在参考文献条目中添加任何注释、评论或与正文章节的交叉引用
7. 禁止在报告末尾添加"报告撰写说明""生成说明""内容声明"等元描述性内容
8. 报告必须围绕用户指定的研究领域展开，方法论讨论必须与该领域的具体研究内容、应用场景和实际案例结合，不得写成通用的文献计量方法论教程
9. 方法论比较要有深度：优缺点、适用场景、计算成本、数据需求
10. 趋势分析基于辩论中揭示的演变轨迹
11. 反证必须包含：有效批评、失败案例、适用边界
12. 研究空白从"为什么没人做"和"做了有什么价值"两个角度分析
13. 学术但可读的语言，避免空话套话和模糊表述
14. 报告字数 >= 6000字，确保每个章节有充分的论述深度，尽量详细展开每个章节
15. 第6章「代码实现」必须基于辩论中讨论的该领域具体分析方法（如因果推断、统计建模、机器学习技术等），而非共识管线本身的基础设施代码。必须包含实际代码块（用```python```标记），展示如何用Python实现辩论共识中提到的核心分析方法，不能只描述代码思路
16. 第7章「教程」必须是围绕该领域具体分析方法的分步骤实操指南，而非共识管线的使用教程。包含该领域分析方法的实现步骤、示例代码、进阶用法说明"""

            user_prompt = f"""请撰写「{search_query}」领域的学术动向综述报告。

以下为各部门辩论共识：

{consensus_text}

交叉辩论结果：

{cross_text}

以下是真实文献检索结果（必须作为参考文献使用，不得编造其他文献）：

{paper_references}

请基于以上辩论内容和真实文献，撰写结构完整的学术综述报告。报告结构：
1. 研究背景与问题定义
2. 核心发现与方法论比较
3. 趋势分析与演进路径
4. 研究空白与未来方向
5. 结论与建议
6. 代码实现（提供该领域具体分析方法的Python代码示例：①快速入门——领域核心分析方法的实现，展示从数据加载到结果输出的完整流程；②进阶增强——辩论中提到的进阶技术实现；③高级定制——该领域前沿方法的复现与调优。代码必须围绕辩论中讨论的具体分析方法，不得写成共识管线的基础设施代码。每个代码块用```python```标记，提供真实可运行的关键片段，不要伪代码）
7. 教程（输出围绕该领域分析方法的三级递进教程：①零基础入门——该领域基础分析方法的实现步骤与示例；②进阶实战——该领域进阶技术的应用与避坑指南；③高级定制——该领域前沿方法的复现与调优。教程必须围绕辩论中讨论的具体分析方法，不得写成共识管线的使用教程。每步含操作命令、示例代码、预期输出）
8. 参考文献（使用上方真实论文列表，格式：[序号] 作者. (年份). 标题. 期刊。序号必须与正文中的[1]、[2]等引用标记一一对应）"""
        else:
            system_prompt = """【重要】你必须使用中文回答。所有输出必须是中文。

你是一位资深学术综述撰写专家。你的任务是将多个学术辩论组的共识结果整合为一篇结构完整的学术动向综述报告。

【硬性规则】
1. 这是学术综述，不是动画脚本或分镜表。严禁出现任何动画/视觉/分镜术语
2. 每个章节必须有实质性内容段落（每节至少300字），每个章节至少3-4段实质性内容，不能只有标题或要点列表
3. 整合各部门辩论中有价值的研究发现，但不得描述本系统/共识管线自身的检索流程、筛选机制或基础设施（如"先广后精""四级筛选""DOI溯源""多源定制检索"等系统方法论术语）。报告内容必须全部围绕研究领域本身的学术内容展开。禁止在报告正文中出现以下系统内部术语："辩论共识""文献检索组""引用网络组""数据分析组""可视化组""程序部""教程部""编剧部""摄影指导部""分镜部""空间设计部""灯光部""特效部""剪辑部""音效部"等部门名称，以及"多部门协作""辩论流程""共识生成"等系统流程描述——这些是系统内部概念，读者不需要知道。如果需要引用某方面分析，直接以学术方式表达（如"已有研究表明…"而非"数据分析组指出…"）。即使输入材料中出现了上述术语，报告正文中也不得出现。即使输入材料中出现了上述术语，报告正文中也不得出现
4. 由于未能检索到外部文献，不输出参考文献章节。不得编造任何不存在的文献
5. 禁止自引用——报告中不得出现"本文第X节""本节""上文提到""如第X章所述"等引用报告自身章节结构的表述。禁止在报告末尾添加"报告撰写说明""生成说明""内容声明"等元描述性内容
6. 报告必须围绕用户指定的研究领域展开，方法论讨论必须与该领域的具体研究内容、应用场景和实际案例结合，不得写成通用的文献计量方法论教程
7. 方法论比较要有深度：优缺点、适用场景、计算成本、数据需求
8. 趋势分析基于辩论中揭示的演变轨迹
9. 反证必须包含：有效批评、失败案例、适用边界
10. 研究空白从"为什么没人做"和"做了有什么价值"两个角度分析
11. 学术但可读的语言，避免空话套话和模糊表述
12. 报告字数 >= 4000字，尽量详细展开每个章节
13. 第6章「代码实现」必须基于辩论中讨论的该领域具体分析方法，而非共识管线本身的基础设施。必须包含实际的代码块（用markdown代码块格式），不能只描述代码思路，要输出可运行的关键代码片段
14. 第7章「教程」必须是围绕该领域具体分析方法的分步骤实操指南，而非共识管线的使用教程。包含环境配置命令、基础示例代码、进阶用法说明"""

            user_prompt = f"""请撰写「{search_query}」领域的学术动向综述报告。

以下为各部门辩论共识：

{consensus_text}

交叉辩论结果：

{cross_text}

请基于以上辩论内容，撰写结构完整的学术综述报告。报告结构：
1. 研究背景与问题定义
2. 核心发现与方法论比较
3. 趋势分析与演进路径
4. 研究空白与未来方向
5. 结论与建议
6. 代码实现（提供该领域具体分析方法的Python代码示例：①快速入门——领域核心分析方法的实现，展示从数据加载到结果输出的完整流程；②进阶增强——辩论中提到的进阶技术实现；③高级定制——该领域前沿方法的复现与调优。代码必须围绕辩论中讨论的具体分析方法，不得写成共识管线的基础设施代码。每个代码块用```python```标记，提供真实可运行的关键片段，不要伪代码）
7. 教程（输出围绕该领域分析方法的三级递进教程：①零基础入门——该领域基础分析方法的实现步骤与示例；②进阶实战——该领域进阶技术的应用与避坑指南；③高级定制——该领域前沿方法的复现与调优。教程必须围绕辩论中讨论的具体分析方法，不得写成共识管线的使用教程。每步含操作命令、示例代码、预期输出）
8. 致谢（简要感谢匿名审稿专家和领域同行提供的宝贵建议，不超过100字，不出现任何系统内部部门名称）"""
    else:
        if has_papers:
            system_prompt = """You are a senior academic review writing expert. Your task is to synthesize multi-group debate consensus with real literature search results into a structured academic trend review report.

IMPORTANT: You MUST respond in English only. All output must be in English.

[HARD RULES]
1. This is an ACADEMIC REVIEW, NOT an animation script or storyboard. Absolutely no animation/visual/storyboard terminology
2. Each section must have substantive content paragraphs (at least 200 words per section), not bare bullet points
3. Integrate valuable research findings from all departments, but do NOT describe the system/pipeline's own search methodology, filtering mechanisms, or infrastructure (e.g., "broad-then-refine", "four-tier screening", "DOI verification", "multi-source retrieval"). All content must focus on the research domain's academic substance. Do NOT use internal system terminology in the report body: department names like "Literature Search Group", "Citation Network Group", "Data Analysis Group", "Visualization Group", "Programming Department", "Tutorial Department", "Screenwriting Department", "Cinematography Department", "Storyboard Department", "Spatial Design Department", "Lighting Department", "VFX Department", "Editing Department", "Sound Department", or process descriptions like "debate consensus", "multi-department collaboration", "debate workflow", "consensus generation" — these are internal system concepts invisible to readers. Express analysis in academic language (e.g., "Existing research shows..." instead of "The Data Analysis Group points out..."). Even if the input materials contain the above terms, they MUST NOT appear in the report body. Even if the input materials contain the above terms, they MUST NOT appear in the report body
4. References MUST ONLY use the real paper list provided below. Do NOT fabricate any references. Do NOT mark references as "illustrative" or "anonymous". If fewer papers are available, use fewer references rather than inventing fake ones. When citing a paper, you may ONLY describe research content, methods, and conclusions that actually appear in the paper's title or abstract. Do NOT fabricate findings not present in the paper — if the abstract does not mention a point, do NOT attribute that point to the paper
5. Cite real paper conclusions appropriately to support debate arguments, each reference should be cited at least once in the text. Citation format MUST use numeric bracket markers (e.g., [1], [2,3], [1-3]). Do NOT use author-year format (e.g., van Eck & Waltman (2017)). Citation numbers MUST match the claim content — do not use a 1997 oil price paper to support a 2020s renewable energy policy claim. Each citation must reference a paper topically relevant to the claim. In-text citations [1], [2] etc. MUST appear frequently throughout the body — every major argument paragraph must contain at least one citation marker. Do NOT list reference numbers only at the end without citing them in the body
6. NO self-references — the report must NOT contain phrases like "Section 1 of this report", "this section", "as discussed above", "as described in Section X" that reference the report's own structure. All academic claims must be supported by external literature, not by the report's own organizational structure. Reference entries must be clean bibliographic format: [number] Author. (Year). Title. Journal. Do NOT add commentary, notes, or cross-references to report sections in reference entries
7. Do NOT add "Report Notes", "Generation Notes", "Content Disclaimer" or any meta-descriptive content at the end of the report
8. The report MUST focus on the user-specified research domain. Methodology discussions must be integrated with the domain's specific research content, applications, and real-world cases. Do NOT write a generic bibliometrics methodology tutorial
9. Methodology comparison must have depth: pros/cons, applicable scenarios, computational costs, data requirements
10. Trend analysis based on evolution trajectories revealed in debates
11. Counter-evidence must be included: valid criticisms, failure cases, applicability boundaries
12. Research gaps analyzed from "why hasn't anyone done this" and "what value would it bring" perspectives
13. Academic but accessible language, avoid filler and vague statements
14. Report length >= 5000 words, ensure each section has sufficient depth, expand each section thoroughly with 3-4 substantive paragraphs
15. Section 6 "Code Implementation" must be based on the specific analytical methods discussed in the debate (e.g., causal inference, statistical modeling, ML techniques), NOT the consensus pipeline infrastructure. Must include actual code blocks (marked with ```python```) demonstrating how to implement the core analytical methods discussed in the debate consensus, not just code descriptions
16. Section 7 "Tutorial" must be a step-by-step guide on the domain's specific analytical methods, NOT a usage tutorial for the consensus pipeline. Include methodology implementation steps, example code, and advanced usage notes"""

            user_prompt = f"""Please write an academic trend review report on "{search_query}".

Department debate consensus:

{consensus_text}

Cross-debate results:

{cross_text}

The following are real literature search results (MUST be used as references, do not fabricate others):

{paper_references}

Based on the above debate content and real literature, write a structured academic review report. Report structure:
1. Research Background & Problem Definition
2. Key Findings & Methodology Comparison
3. Trend Analysis & Evolution Path
4. Research Gaps & Future Directions
5. Conclusions & Recommendations
6. Code Implementation (provide Python code for the domain's specific analytical methods: (1) Quick Start — implementation of core analytical methods, showing a complete data-to-results workflow; (2) Advanced Enhancement — implementation of advanced techniques discussed in the debate; (3) Advanced Customization — reproduction and tuning of cutting-edge methods. Code must focus on the analytical methods discussed in the debate, NOT the consensus pipeline infrastructure. Use ```python``` blocks, provide real runnable snippets, no pseudocode)
7. Tutorial (3-tier progressive guide on the domain's analytical methods: (1) Beginner — implementation steps and examples for the domain's basic analytical methods; (2) Intermediate — application of advanced techniques with pitfalls to avoid; (3) Advanced — reproduction and tuning of cutting-edge methods. Tutorial must focus on the analytical methods discussed in the debate, NOT a usage guide for the consensus pipeline. Each step includes commands, example code, expected output)
8. References (use the real paper list above, format: [number] Authors. (Year). Title. Journal. Numbers must correspond to [1], [2] etc. citation markers in the text)"""
        else:
            system_prompt = """You are a senior academic review writing expert. Your task is to synthesize multi-group debate consensus into a structured academic trend review report.

IMPORTANT: You MUST respond in English only. All output must be in English.

[HARD RULES]
1. This is an ACADEMIC REVIEW, NOT an animation script or storyboard. Absolutely no animation/visual/storyboard terminology
2. Each section must have substantive content paragraphs (at least 200 words per section), not bare bullet points
3. Integrate valuable research findings from all departments, but do NOT describe the system/pipeline's own search methodology, filtering mechanisms, or infrastructure (e.g., "broad-then-refine", "four-tier screening", "DOI verification", "multi-source retrieval"). All content must focus on the research domain's academic substance. Do NOT use internal system terminology in the report body: department names like "Literature Search Group", "Citation Network Group", "Data Analysis Group", "Visualization Group", "Programming Department", "Tutorial Department", "Screenwriting Department", "Cinematography Department", "Storyboard Department", "Spatial Design Department", "Lighting Department", "VFX Department", "Editing Department", "Sound Department", or process descriptions like "debate consensus", "multi-department collaboration", "debate workflow", "consensus generation" — these are internal system concepts invisible to readers. Express analysis in academic language (e.g., "Existing research shows..." instead of "The Data Analysis Group points out..."). Even if the input materials contain the above terms, they MUST NOT appear in the report body. Even if the input materials contain the above terms, they MUST NOT appear in the report body
4. Since external literature search was not available, do NOT output a references section. Do not fabricate any non-existent references
5. NO self-references — the report must NOT contain phrases like "Section 1 of this report", "this section", "as discussed above", "as described in Section X" that reference the report's own structure. Do NOT add "Report Notes", "Generation Notes", "Content Disclaimer" or any meta-descriptive content at the end of the report
6. The report MUST focus on the user-specified research domain. Methodology discussions must be integrated with the domain's specific research content, applications, and real-world cases. Do NOT write a generic bibliometrics methodology tutorial
7. Methodology comparison must have depth: pros/cons, applicable scenarios, computational costs, data requirements
8. Trend analysis based on evolution trajectories revealed in debates
9. Counter-evidence must be included: valid criticisms, failure cases, applicability boundaries
10. Research gaps analyzed from "why hasn't anyone done this" and "what value would it bring" perspectives
11. Academic but accessible language, avoid filler and vague statements
12. Report length >= 4500 words, ensure each section has sufficient depth, expand each section thoroughly with 3-4 substantive paragraphs
13. Section 6 "Code Implementation" must be based on the specific analytical methods discussed in the debate, NOT the consensus pipeline infrastructure. Must include actual code blocks (in markdown code block format), not just descriptions of code ideas - output runnable key code snippets
14. Section 7 "Tutorial" must be a step-by-step guide on the domain's specific analytical methods, NOT a usage tutorial for the consensus pipeline. Include environment setup commands, basic example code, and advanced usage notes"""

            user_prompt = f"""Please write an academic trend review report on "{search_query}".

Department debate consensus:

{consensus_text}

Cross-debate results:

{cross_text}

Based on the above debate content, write a structured academic review report. Report structure:
1. Research Background & Problem Definition
2. Key Findings & Methodology Comparison
3. Trend Analysis & Evolution Path
4. Research Gaps & Future Directions
5. Conclusions & Recommendations
6. Code Implementation (provide Python code for the domain's specific analytical methods: (1) Quick Start — implementation of core analytical methods, showing a complete data-to-results workflow; (2) Advanced Enhancement — implementation of advanced techniques discussed in the debate; (3) Advanced Customization — reproduction and tuning of cutting-edge methods. Code must focus on the analytical methods discussed in the debate, NOT the consensus pipeline infrastructure. Use ```python``` blocks, provide real runnable snippets, no pseudocode)
7. Tutorial (3-tier progressive guide on the domain's analytical methods: (1) Beginner — implementation steps and examples for the domain's basic analytical methods; (2) Intermediate — application of advanced techniques with pitfalls to avoid; (3) Advanced — reproduction and tuning of cutting-edge methods. Tutorial must focus on the analytical methods discussed in the debate, NOT a usage guide for the consensus pipeline. Each step includes commands, example code, expected output)
8. Acknowledgments (briefly thank anonymous reviewers and domain peers for valuable suggestions, under 100 words, no internal system department names)"""

    # Call LLM
    report = call_api(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_url=api_url, api_key=api_key, model=model,
        temperature=0.25, max_tokens=16384, timeout=180,
        stats=stats,
    )

    # Post-process: strip trailing disclaimers and metadata
    if report:
        import re as _re
        _disclaimer_patterns = [
            _re.compile(r'\n*---\s*\n*本内容.*?(?:生成|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*---\s*\n*以上内容.*?(?:生成|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*---\s*\n*This content.*?(?:generated|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*---\s*\n*The above content.*?(?:generated|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*⚠?\s*本内容由.*?(?:生成|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*⚠?\s*This content.*?(?:generated|AI).*?$', _re.DOTALL),
            _re.compile(r'\n*---\s*\n*免责声明.*?$', _re.DOTALL),
            _re.compile(r'\n*---\s*\n*Disclaimer.*?$', _re.DOTALL),
        ]
        for _pat in _disclaimer_patterns:
            report = _pat.sub('', report).rstrip()

    if not report:
        # Fallback: just concatenate consensus
        report = consensus_text

    # Collect search stats
    _se_stats = locals().get("_se_stats", {})
    _search_info = {
        "query": search_query if 'search_query' in dir() else user_topic,
        "total_fetched": _se_stats.get("total_fetched", 0) if _se_stats else 0,
        "after_filter": _se_stats.get("after_filter", 0) if _se_stats else 0,
        "preprint_count": _se_stats.get("preprint_count", 0) if _se_stats else 0,
        "papers_in_refs": len(papers_found),
        "has_real_references": has_papers,
        "queries_used": len(search_queries) if 'search_queries' in dir() else 0,
        "domain_config_active": domain_config is not None if 'domain_config' in dir() else False,
    }
    
    # Serialize papers for downstream verification (citation-grounded fact check)
    _papers_data = []
    for p in all_papers[:20] if has_papers else []:
        _papers_data.append({
            "title": getattr(p, "title", ""),
            "doi": getattr(p, "doi", "") or "",
            "abstract": (getattr(p, "abstract", "") or "")[:2000],
            "authors": getattr(p, "authors", []),
            "year": getattr(p, "year", ""),
            "journal": getattr(p, "journal", ""),
            "citation_count": getattr(p, "citation_count", 0),
            "url": getattr(p, "url", "") or "",
        })

    return {
        "final_report": report,
        "consensus_report": consensus_text,
        "papers_found": len(papers_found),
        "has_real_references": has_papers,
        "search_info": _search_info,
        "papers_data": _papers_data,
    }



# ============ P7: Proofreading ============

PROOFREAD_DEPARTMENTS = ["screenwriter", "spatial", "storyboard", "dp", "editing"]

def run_proofreading(
    storyboard: str,
    video_prompt: str,
    all_consensus: Dict[str, str],
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    P7: 校对环节——空间/分镜/摄影/剪辑四部门审查最终产出。
    每个部门从自己的专业视角检查分镜表和视频提示词是否可用。
    """
    is_zh = lang == "zh"
    reviews = {}
    
    for dept_key in PROOFREAD_DEPARTMENTS:
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        dept_consensus = all_consensus.get(dept_key, "")
        
        # Each department has different check focus
        focus_points = {
            "screenwriter": {
                "zh": "1. 出场角色清单是否完整（有没有角色被遗忘）\n2. 叙事节拍是否清晰合理\n3. 每个节拍是否标注了观众必须理解什么\n4. 节拍之间是否有角色消失/出现未标注",
                "en": "1. Is the on-screen roster complete (any characters forgotten?)\n2. Are narrative beats clear and reasonable\n3. Does each beat mark what the audience must understand\n4. Are character appearances/disappearances between beats noted",
            },
            "spatial": {
                "zh": "1. 角色物品参照定位是否正确一致（分镜表和视频提示词中的站位是否与空间板块物品定位对应）\n2. 角色站位是否连贯（相邻Shot间角色是否瞬移）\n3. 移动路径是否合理（动态衔接中的角色移动是否经过正确物品参照）\n4. 物品位置是否连贯\n5. 面朝方向是否合理（是否背对对话对象）\n6. 画面位置与物品参照位置是否矛盾",
                "en": "1. Are character object-referenced positions correct and consistent (do position references in storyboard and video prompt match Spatial Planning definitions?)\n2. Are character positions continuous (do characters teleport between adjacent shots?)\n3. Are movement paths reasonable (do character movements in Dynamic Transitions pass through correct object references?)\n4. Are object positions continuous\n5. Are facing directions reasonable (are characters turning away from conversation partners?)\n6. Do frame positions contradict object-referenced positions",
            },
            "storyboard": {
                "zh": "1. 分镜表是否真的是纯静态关键帧（有没有混入动态描述）\n2. 视频提示词的[关键帧]部分是否与分镜表一致\n3. Shot数量和编号是否一一对应\n4. 构图是否在物理上可行\n5. 每个Shot是否有叙事节拍标注\n6. 每个Shot是否有切换动机\n7. 每个Shot的出场角色是否与编剧部出场清单一致",
                "en": "1. Is the storyboard truly static keyframes only (are there any dynamic descriptions mixed in?)\n2. Does the video prompt's [Key Frame] section match the storyboard?\n3. Do shot counts and numbers correspond one-to-one?\n4. Are compositions physically feasible?\n5. Does every Shot have a narrative beat label?\n6. Does every Shot have a switch motivation?\n7. Does every Shot's on-screen characters match the Screenwriter on-screen roster?",
            },
            "dp": {
                "zh": "1. 焦段和景深选择是否合理\n2. 机位角度是否在物理上可达成\n3. 镜头运动（动态衔接中的镜头过渡）是否可行\n4. 焦段变化是否连贯\n5. 每个镜头是否有切换动机标注\n6. 切换动机是否合理（是否真的有动作/信息/情绪/节奏驱动）\n7. 镜头之间是否有连贯性说明",
                "en": "1. Are focal length and DOF choices reasonable?\n2. Are camera angles physically achievable?\n3. Are camera movements (in Dynamic Transitions) feasible?\n4. Are focal length changes continuous?\n5. Does every shot have a switch motivation label?\n6. Are switch motivations reasonable (is there truly action/information/emotion/rhythm driving them?)\n7. Is there a continuity explanation between shots?",
            },
            "editing": {
                "zh": "1. 拆分方案是否正确执行\n2. 段间衔接方式是否标注且合理\n3. 长镜头是否保持完整未被拆断\n4. 动态衔接中的镜头过渡是否与剪辑属性一致",
                "en": "1. Is the split plan correctly executed?\n2. Are inter-segment transitions marked and reasonable?\n3. Are long takes kept intact without being cut?\n4. Do camera transitions in Dynamic Transitions match edit types?",
            },
        }
        
        focus = focus_points.get(dept_key, {}).get(lang, "")
        
        if is_zh:
            prompt = f"""你是{dept_name}的校对审校员。请从你的专业视角审查以下最终产出的质量。

{dept_name}的辩论共识（供对照参考）：
{dept_consensus}

【你的检查重点】
{focus}

===== 待审查的分镜表 =====
{storyboard}

===== 待审查的视频逐镜提示词 =====
{video_prompt}

请逐项检查，输出格式：

## 通过项
- [检查项]: ✅ 通过 — [简要说明]

## 问题项
- [检查项]: ❌ 问题 — [具体问题描述] — [修正建议]

## 总体评价
[通过/需返工] — [一句话总结]"""
        else:
            prompt = f"""You are the proofreader for the {dept['en_name']} Department. Review the final outputs from your professional perspective.

{dept['en_name']} debate consensus (for reference):
{dept_consensus}

[YOUR FOCUS POINTS]
{focus}

===== Storyboard to Review =====
{storyboard}

===== Video Prompt to Review =====
{video_prompt}

Check each point. Output format:

## Passed Items
- [Check item]: ✅ Pass — [brief explanation]

## Issues Found
- [Check item]: ❌ Issue — [specific problem description] — [fix suggestion]

## Overall Assessment
[Pass / Needs Rework] — [one-sentence summary]"""
        
        messages = [{"role": "user", "content": prompt}]
        result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=4096, stats=stats)
        reviews[dept_key] = result or "校对未能完成"
    
    # Summarize proofread conclusions
    passed = True
    issue_list = []
    summary_parts = []
    for dept_key in PROOFREAD_DEPARTMENTS:
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        review = reviews[dept_key]
        has_issue = "❌" in review or "Issue" in review
        if has_issue:
            passed = False
            issue_list.append((dept_key, dept_name, review))
        summary_parts.append(f"### {dept_name}\n{review}")
    
    if is_zh:
        overall = "✅ 校对通过——产出可用" if passed else "⚠️ 校对发现问题——已自动修正"
    else:
        overall = "✅ Proofreading passed—output is usable" if passed else "⚠️ Issues found—auto-revision applied"
    
    result = {
        "reviews": reviews,
        "overall": overall,
        "passed": passed,
        "summary": "\n\n".join(summary_parts) + f"\n\n## {overall}",
        "original_storyboard": storyboard if not passed else None,
        "original_video_prompt": video_prompt if not passed else None,
    }
    
    return result


# ============ Academic Proofreading ============

ACADEMIC_PROOFREAD_DEPARTMENTS = ["report_integration", "programming", "tutorial"]

def run_academic_proofreading(
    final_report: str,
    all_consensus: Dict[str, str],
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
) -> Dict:
    """
    Academic mode proofreading: 报告整合/程序/教程三部门审查最终学术报告。
    与原版 run_proofreading 不同，这里审查的是学术报告（final_report），
    而非动画分镜表和视频提示词。
    """
    is_zh = lang == "zh"
    reviews = {}

    # Academic department definitions (from templates/academic_departments.json)
    academic_depts = {
        "report_integration": {
            "zh_name": "报告整合组",
            "en_name": "Report Integration",
        },
        "programming": {
            "zh_name": "程序部",
            "en_name": "Programming",
        },
        "tutorial": {
            "zh_name": "教程部",
            "en_name": "Tutorial",
        },
    }

    focus_points = {
        "report_integration": {
            "zh": (
                "1. 报告结构是否完整（8个章节是否全部覆盖）\n"
                "2. 各章节是否有实质性内容（每章至少3-4段，非空标题）\n"
                "3. 各部门辩论共识是否都被纳入报告\n"
                "4. 参考文献格式是否规范、是否全部来自真实检索结果\n"
                "5. 方法论比较是否有深度（优缺点、适用场景、计算成本）\n"
                "6. 是否存在动画/视觉术语混入（如'冲击帧''分镜'等）\n"
                "7. 报告是否围绕研究主题展开，而非描述共识管线本身"
            ),
            "en": (
                "1. Is the report structure complete (all 8 chapters covered)?\n"
                "2. Does each chapter have substantive content (at least 3-4 paragraphs, not empty headers)?\n"
                "3. Are all department debate consensuses incorporated into the report?\n"
                "4. Are references properly formatted and all from real search results?\n"
                "5. Does methodology comparison have depth (pros/cons, applicable scenarios, computational costs)?\n"
                "6. Are there any animation/visual terms mixed in (e.g. 'impact frame', 'storyboard')?\n"
                "7. Does the report focus on the research topic, not describing the consensus pipeline itself?"
            ),
        },
        "programming": {
            "zh": (
                "1. 代码是否围绕研究主题的具体分析方法（而非共识管线基础设施）\n"
                "2. 代码块是否使用```python```标记、是否可运行\n"
                "3. 是否覆盖了三个层次（快速入门→进阶增强→高级定制）\n"
                "4. 代码是否有类型注解、中文注释、异常处理\n"
                "5. 代码是否与辩论共识中讨论的方法一致\n"
                "6. 是否存在'搜索引擎''辩论引擎''报告生成'等管线基础设施代码（应被替换为领域方法代码）"
            ),
            "en": (
                "1. Does the code focus on the research topic's specific analytical methods (not pipeline infrastructure)?\n"
                "2. Are code blocks marked with ```python``` and actually runnable?\n"
                "3. Are the three tiers covered (Quick Start → Advanced → Customization)?\n"
                "4. Does the code have type annotations, comments, and error handling?\n"
                "5. Is the code consistent with the methods discussed in the debate consensus?\n"
                "6. Is there any pipeline infrastructure code (search engine, debate engine, report generator) that should be replaced?"
            ),
        },
        "tutorial": {
            "zh": (
                "1. 教程是否围绕研究主题的具体分析方法（而非共识管线使用教程）\n"
                "2. 是否覆盖三级递进（零基础→进阶实战→高级定制）\n"
                "3. 每步是否包含操作→原因→预期输出→常见报错\n"
                "4. 教程是否给新手提供了可运行的demo\n"
                "5. 教程示例代码是否与程序部代码一致\n"
                "6. 是否存在'如何运行共识管线'类的教程内容（应被替换为领域方法教程）"
            ),
            "en": (
                "1. Does the tutorial focus on the research topic's analytical methods (not pipeline usage)?\n"
                "2. Are the three tiers covered (Beginner → Intermediate → Advanced)?\n"
                "3. Does each step include action → reason → expected output → common errors?\n"
                "4. Does the tutorial provide a runnable demo for beginners?\n"
                "5. Is the tutorial example code consistent with the programming dept output?\n"
                "6. Is there any 'how to run the consensus pipeline' content that should be replaced?"
            ),
        },
    }

    for dept_key in ACADEMIC_PROOFREAD_DEPARTMENTS:
        dept = academic_depts[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        dept_consensus = all_consensus.get(dept_key, "")
        focus = focus_points.get(dept_key, {}).get(lang, "")

        if is_zh:
            prompt = f"""你是{dept_name}的校对审校员。请从你的专业视角审查以下学术报告的{dept_name}相关部分。

{dept_name}的辩论共识（供对照参考）：
{dept_consensus}

【你的检查重点】
{focus}

===== 待审查的学术报告 =====
{final_report[:30000]}

请逐项检查，输出格式：

## 通过项
- [检查项]: ✅ 通过 — [简要说明]

## 问题项
- [检查项]: ❌ 问题 — [具体问题描述] — [修正建议]

## 总体评价
[通过/需返工] — [一句话总结]"""
        else:
            prompt = f"""You are the proofreader for the {dept['en_name']} Department. Review the academic report from your professional perspective.

{dept['en_name']} debate consensus (for reference):
{dept_consensus}

[YOUR FOCUS POINTS]
{focus}

===== Academic Report to Review =====
{final_report[:30000]}

Check each point. Output format:

## Passed Items
- [Check item]: ✅ Pass — [brief explanation]

## Issues Found
- [Check item]: ❌ Issue — [specific problem description] — [fix suggestion]

## Overall Assessment
[Pass / Needs Rework] — [one-sentence summary]"""

        messages = [{"role": "user", "content": prompt}]
        result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=4096, stats=stats)
        reviews[dept_key] = result or ("校对未能完成" if is_zh else "Proofreading failed")

    # Summarize proofread conclusions
    passed = True
    summary_parts = []
    for dept_key in ACADEMIC_PROOFREAD_DEPARTMENTS:
        dept = academic_depts[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        review = reviews[dept_key]
        has_issue = "❌" in review or "Issue" in review
        if has_issue:
            passed = False
        summary_parts.append(f"### {dept_name}\n{review}")

    if is_zh:
        overall = "✅ 校对通过——报告可用" if passed else "⚠️ 校对发现问题——建议修正"
    else:
        overall = "✅ Proofreading passed—report is usable" if passed else "⚠️ Issues found—revision suggested"

    result = {
        "reviews": reviews,
        "overall": overall,
        "passed": passed,
        "summary": "\n\n".join(summary_parts) + f"\n\n## {overall}",
    }

    return result


def run_auto_revision(
    storyboard: str,
    video_prompt: str,
    proofread_result: Dict,
    all_consensus: Dict[str, str],
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    校对后自动修正：收集校对发现的问题，让LLM直接修正分镜表和视频提示词。
    返回修正后的完整产出。
    """
    is_zh = lang == "zh"
    reviews = proofread_result.get("reviews", {})
    
    # Collect all issue items
    all_issues = ""
    for dept_key in PROOFREAD_DEPARTMENTS:
        dept = DEPARTMENTS[dept_key]
        dept_name = dept["zh_name"] if is_zh else dept["en_name"]
        review = reviews.get(dept_key, "")
        all_issues += f"\n### {dept_name}校对反馈\n{review}\n"
    
    if is_zh:
        revise_prompt = f"""你是校对修正专家。以下是校对环节发现的所有问题，请直接修正分镜表和视频提示词。

===== 校对反馈汇总 =====
{all_issues}

===== 原分镜表 =====
{storyboard}

===== 原视频提示词 =====
{video_prompt}

【修正要求】
1. 逐条处理校对反馈中的❌问题项，按修正建议修改
2. 修正时保持其他未涉及部分不变
3. 确保修正后的分镜表和视频提示词Shot数量一致
4. 确保每个Shot仍有【完整画面】段
5. 确保物品参照定位和画面位置仍然正确
6. 确保每个Shot仍有叙事节拍、切换动机、出场角色三个字段，且与对应部门共识一致
7. 直接输出修正后的完整分镜表和视频提示词，不要只输出差异

请按以下格式输出：

===== 修正后分镜表 =====
[完整的修正后分镜表]

===== 修正后视频提示词 =====
[完整的修正后视频提示词]

===== 修正说明 =====
[逐条列出你做了哪些修正]"""
    else:
        revise_prompt = f"""You are a proofreading revision expert. Below are all issues found during proofreading. Please directly fix the storyboard and video prompt.

===== Proofreading Feedback Summary =====
{all_issues}

===== Original Storyboard =====
{storyboard}

===== Original Video Prompt =====
{video_prompt}

[Revision Requirements]
1. Address each ❌ issue found in proofreading, apply the fix suggestions
2. Keep all untouched parts unchanged
3. Ensure storyboard and video prompt shot counts match after revision
4. Ensure every Shot still has a [Complete Frame] section
5. Ensure object-referenced positions and frame positions are still correct
6. Ensure every Shot still has Narrative Beat, Switch Motivation, and On-Screen Characters fields, matching the corresponding department consensus
7. Output the COMPLETE revised storyboard and video prompt, not just diffs

Output format:

===== Revised Storyboard =====
[Complete revised storyboard]

===== Revised Video Prompt =====
[Complete revised video prompt]

===== Revision Notes =====
[List each change you made]"""
    
    messages = [{"role": "user", "content": revise_prompt}]
    result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=16384, timeout=180, stats=stats)
    
    # Parse correction results
    revised_storyboard = storyboard
    revised_video_prompt = video_prompt
    revision_notes = ""
    
    if result and not result.startswith("ERROR:"):
        if is_zh:
            parts = result.split("===== 修正后分镜表 =====")
            if len(parts) >= 2:
                after_sb = parts[1]
                sb_end = after_sb.find("===== 修正后视频提示词 =====")
                if sb_end >= 0:
                    revised_storyboard = after_sb[:sb_end].strip()
                
                vp_start = after_sb.find("===== 修正后视频提示词 =====")
                if vp_start >= 0:
                    after_vp = after_sb[vp_start + len("===== 修正后视频提示词 ====="):]
                    vp_end = after_vp.find("===== 修正说明 =====")
                    if vp_end >= 0:
                        revised_video_prompt = after_vp[:vp_end].strip()
                        revision_notes = after_vp[vp_end + len("===== 修正说明 ====="):].strip()
                    else:
                        revised_video_prompt = after_vp.strip()
        else:
            parts = result.split("===== Revised Storyboard =====")
            if len(parts) >= 2:
                after_sb = parts[1]
                sb_end = after_sb.find("===== Revised Video Prompt =====")
                if sb_end >= 0:
                    revised_storyboard = after_sb[:sb_end].strip()
                
                vp_start = after_sb.find("===== Revised Video Prompt =====")
                if vp_start >= 0:
                    after_vp = after_sb[vp_start + len("===== Revised Video Prompt ====="):]
                    vp_end = after_vp.find("===== Revision Notes =====")
                    if vp_end >= 0:
                        revised_video_prompt = after_vp[:vp_end].strip()
                        revision_notes = after_vp[vp_end + len("===== Revision Notes ====="):].strip()
                    else:
                        revised_video_prompt = after_vp.strip()
    
    return {
        "storyboard_prompt": revised_storyboard,
        "video_prompt": revised_video_prompt,
        "revision_notes": revision_notes,
        "original_storyboard": storyboard,
        "original_video_prompt": video_prompt,
    }

def run_director_revision(
    department_key: str,
    director_note: str,
    all_consensus: Dict[str, str],
    user_script: str,
    positive_prompt: str,
    negative_prompt: str,
    character_refs: str,
    cross_results: list,
    current_storyboard: str,
    current_video_prompt: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    rounds: int = 2,
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    导演指令修正：导演指定某个部门+给修改意见→系统重跑该部门辩论→重新生成分镜表+视频提示词。
    
    与rerun_single_dept不同，这个功能：
    1. 重跑指定部门辩论（带导演修改意见）
    2. 用新的部门共识替换原共识
    3. 调用run_summary重新生成分镜表+视频提示词
    """
    is_zh = lang == "zh"
    dept = DEPARTMENTS[department_key]
    dept_name = dept["zh_name"] if is_zh else dept["en_name"]
    
    # Build input for this dept (same as normal debate)
    dept_input = build_dept_input_content(department_key, all_consensus, user_script, positive_prompt, character_refs, lang)
    
    # Re-run dept debate with director corrections as extra instructions
    extra = f"导演修改意见：{director_note}" if is_zh else f"Director's revision note: {director_note}"
    
    new_dept_result = run_department_debate(
        department_key=department_key,
        input_content=dept_input,
        api_url=api_url,
        api_key=api_key,
        model=model,
        rounds=rounds,
        lang=lang,
        extra_instructions=extra,
        stats=stats,
    )
    
    # Replace department consensus
    updated_consensus = dict(all_consensus)
    updated_consensus[department_key] = new_dept_result["consensus"]
    
    # If spatial dept modified, re-run spatial cross-review
    if department_key == "spatial":
        spatial_review = run_spatial_review(
            spatial_consensus=new_dept_result["consensus"],
            reviewer_departments=["storyboard", "dp", "editing"],
            api_url=api_url, api_key=api_key, model=model, lang=lang,
            stats=stats,
        )
        updated_consensus["spatial"] = spatial_review["revised_consensus"]
    
    # Regenerate storyboard + video prompts
    new_output = run_summary(
        user_script=user_script,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        character_refs=character_refs,
        all_consensus=updated_consensus,
        cross_results=cross_results,
        api_url=api_url,
        api_key=api_key,
        model=model,
        lang=lang,
        stats=stats,
    )
    
    return {
        "department": department_key,
        "dept_name": dept_name,
        "dept_result": new_dept_result,
        "updated_consensus": updated_consensus,
        "storyboard_prompt": new_output["storyboard_prompt"],
        "video_prompt": new_output["video_prompt"],
        "director_note": director_note,
    }

def build_dept_input_content(department_key: str, all_consensus: Dict[str, str], user_script: str, positive_prompt: str, character_refs: str, lang: str = "zh") -> str:
    """构建部门辩论输入内容（供导演指令修正使用）"""
    is_zh = lang == "zh"
    
    if department_key == "screenwriter":
        return f"剧本：\n{user_script}\n\n场景风格：\n{positive_prompt}\n\n角色参考：\n{character_refs}"
    elif department_key == "spatial":
        sw = all_consensus.get("screenwriter", user_script)
        return f"编剧部细节填充版剧本：\n{sw}\n\n原始场景风格：\n{positive_prompt}"
    elif department_key == "storyboard":
        sw = all_consensus.get("screenwriter", user_script)
        sp = all_consensus.get("spatial", "")
        return f"编剧部细节填充版剧本：\n{sw}\n\n空间板块布局：\n{sp}\n\n场景风格：\n{positive_prompt}"
    elif department_key in ("dp", "lighting", "vfx"):
        parts = [f"编剧部：\n{all_consensus.get('screenwriter', user_script)}"]
        if "spatial" in all_consensus: parts.append(f"空间板块：\n{all_consensus['spatial']}")
        if "storyboard" in all_consensus: parts.append(f"分镜部：\n{all_consensus['storyboard']}")
        return "\n\n---\n\n".join(parts)
    elif department_key == "sound":
        parts = [f"编剧部：\n{all_consensus.get('screenwriter', user_script)}"]
        if "storyboard" in all_consensus: parts.append(f"分镜部：\n{all_consensus['storyboard']}")
        return "\n\n---\n\n".join(parts)
    elif department_key == "editing":
        parts = []
        for pk in ["screenwriter", "spatial", "storyboard", "dp", "lighting", "vfx", "sound"]:
            if pk in all_consensus:
                p = DEPARTMENTS[pk]; pn = p["zh_name"] if is_zh else p["en_name"]
                parts.append(f"{pn}共识：\n{all_consensus[pk]}")
        return "\n\n---\n\n".join(parts)
    else:
        prev = []
        for pk in DEPT_ORDER[:DEPT_ORDER.index(department_key)]:
            if pk in all_consensus:
                p = DEPARTMENTS[pk]; pn = p["zh_name"] if is_zh else p["en_name"]
                prev.append(f"{pn}：\n{all_consensus[pk]}")
        return "\n\n---\n\n".join(prev)

# ============ Spatial Diagram Prompt Generation ============

def run_spatial_diagram(
    spatial_consensus: str,
    user_script: str,
    positive_prompt: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    根据空间板块共识生成空间示意图提示词。
    这是一个独立的产出物，可以喂给AI绘图工具生成场景空间布局图。
    包含：物品布局、角色位置、角色移动路径、物品间距离。
    """
    is_zh = lang == "zh"
    
    # Detect scene count — multi-scene if "Scene 2" markers found
    import re
    scene_markers_zh = re.findall(r'场景[二三四五六七八九十]', spatial_consensus)
    scene_markers_en = re.findall(r'Scene\s*(2|3|4|5|6|7|8|9|10)', spatial_consensus)
    scene_count = 1 + max(len(scene_markers_zh), len(scene_markers_en))
    
    # Extract sub-consensus per scene (for multi-scene diagram generation)
    scene_sections = []
    if scene_count > 1:
        # Split by scene markers
        if is_zh:
            parts = re.split(r'###?\s*场景[一二三四五六七八九十]', spatial_consensus)
        else:
            parts = re.split(r'###?\s*Scene\s*\d+', spatial_consensus)
        # parts[0] is scene count judgment, parts[1:] are scene contents
        for i, part in enumerate(parts[1:], 1):
            if is_zh:
                scene_name = f"场景{'一二三四五六七八九十'[i-1] if i <= 10 else str(i)}"
            else:
                scene_name = f"Scene {i}"
            scene_sections.append((scene_name, part.strip()))
    else:
        scene_sections.append(("场景" if is_zh else "Scene", spatial_consensus))
    
    all_diagrams = []
    
    for scene_name, scene_content in scene_sections:
        if is_zh:
            prompt = f"""你是空间布局可视化专家。请根据以下空间板块共识中的【{scene_name}】部分，生成一份空间示意图提示词，用于AI绘图工具生成该场景的空间布局图。

【任务】将文字版的空间布局转化为可视化描述，让AI能画出一张清晰的场景空间布局示意图。

用户原始剧本：
{user_script}

场景视觉风格提示词：
{positive_prompt}

{scene_name}空间板块共识：
{scene_content}

【输出要求】请生成两部分内容：

## 第一部分：{scene_name}空间布局详细描述（供AI绘图用）
生成一段详细的场景空间布局视觉描述，用于AI图像生成工具（如Midjourney/DALL-E）生成3/4透视的场景布局图。要求：
1. 视角：3/4透视（isometric/3-quarter view），以同时展示高度信息和物品位置
2. 画面中必须清晰展示该场景所有物品的位置和大小关系
3. 每个角色用简化人形标注在物品参照位置上，标明面朝方向
4. 角色移动路径用箭头线段标出，路径上标注经过的关键物品
5. 关键物品用简化图标标出，旁边写物品名称
6. 画面整体风格与场景视觉风格一致
7. 物品间距离用"X步"等标注

## 第二部分：{scene_name}纯文字版空间参考表
- 物品位置速查：每个物品的名称、位置描述、朝向/特征
- 角色站位速查：每个角色在哪些Shot出现在哪个物品参照位置，面朝什么方向
- 移动路径速查：每条移动路径的起止物品参照、经过的关键物品、路径描述"""
        else:
            prompt = f"""You are a spatial layout visualization expert. Based on the [{scene_name}] section of the Spatial Planning consensus below, generate a spatial diagram prompt for AI image generation tools to create a scene layout diagram for THIS scene.

[TASK] Transform the text-based spatial layout into a visual description that enables AI to draw a clear scene spatial layout diagram.

User's original script:
{user_script}

Scene visual style prompt:
{positive_prompt}

{scene_name} Spatial Planning consensus:
{scene_content}

[OUTPUT REQUIREMENTS] Generate two parts:

## Part 1: {scene_name} Spatial Layout Visual Description (for AI image generation)
Generate a detailed scene spatial layout visual description for AI image tools to create a 3/4 perspective scene layout diagram. Requirements:
1. View angle: 3/4 isometric perspective to show height information and object positions
2. Must clearly show all scene objects' positions and size relationships
3. Each character shown with simplified figure at their object-referenced position, with facing direction marked
4. Character movement paths shown with arrow lines, key objects passed along the path labeled
5. Key objects shown with simplified icons, with object names labeled
6. Overall visual style consistent with scene visual style
7. Inter-object distances labeled with "X steps" etc.

## Part 2: {scene_name} Text-Only Spatial Reference Table
- Object position reference: each object's name, position description, orientation/features
- Character position reference: which object-referenced position each character appears at in which shots, facing direction
- Movement path reference: start/end object references, key objects passed, path description"""
        
        messages = [{"role": "user", "content": prompt}]
        result = call_api(messages, api_url, api_key, model, temperature=0.3, max_tokens=4096, timeout=120, stats=stats)
        all_diagrams.append({
            "scene_name": scene_name,
            "diagram_prompt": result or f"{scene_name}空间示意图提示词生成失败",
        })
    
    # Multi-scene: concatenate all scene contents, avoid placeholder text
    if scene_count == 1:
        full_prompt = all_diagrams[0]["diagram_prompt"]
    else:
        parts = []
        for sd in all_diagrams:
            parts.append(f"{'='*40}\n{sd['scene_name']}\n{'='*40}\n\n{sd['diagram_prompt']}")
        full_prompt = "\n\n".join(parts)

    return {
        "scene_count": scene_count,
        "spatial_diagram_prompt": full_prompt,
        "scene_diagrams": all_diagrams,
    }

# ============ Round-by-Round Debate (step-by-step mode) ============

def run_department_round(
    department_key: str,
    round_num: int,
    input_content: str,
    previous_arguments: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    extra_instructions: str = "",
    carry_forward: str = "",
    stats: dict = None,  # Token statistics累加器
) -> tuple:
    """
    运行单个部门的单轮辩论（3位辩手）
    Returns: (round_log, updated_all_arguments)
    """
    dept = DEPARTMENTS[department_key]
    is_zh = lang == "zh"
    all_arguments = list(previous_arguments)
    round_log = []
    
    for debater_key in dept["debaters"]:
        debater = dept["debaters"][debater_key]
        
        if round_num == 1:
            constraints = get_screenwriter_constraints(lang) if department_key == "screenwriter" else ""
            cf_block = ""
            if carry_forward:
                if is_zh:
                    cf_block = f"\n【承上文档——前段辩论的关键决策，必须遵守】\n{carry_forward}\n"
                else:
                    cf_block = f"\n[Carry Forward — Key decisions from previous segment debate, MUST follow]\n{carry_forward}\n"
            # Detect academic mode (non-animation departments)
            _academic_dept_keys = {"literature_search", "methodology_review", "report_integration",
                                   "programming", "tutorial", "metadata_inspector", "citation_network",
                                   "data_validation", "counter_evidence", "topic_clustering", "visualization"}
            _is_academic_dept = department_key in _academic_dept_keys
            
            if is_zh:
                if _is_academic_dept:
                    _academic_instruction = "请从你的专业视角分析上述研究主题的学术现状、关键问题和前沿趋势。你的分析必须围绕研究主题本身展开，不要讨论检索方法论或工具流程本身。要具体、有文献支撑、有理由。"
                else:
                    _academic_instruction = "请从你的专业视角出发，提出你对上述内容的方案和建议。要具体、有细节、有理由。不要泛泛而谈。"
                prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的{debater['zh_name']}辩手。

{ANIME_VISUAL_DIRECTIVE['zh']}

{debater['zh_style']}
{constraints}
{cf_block}
当前讨论内容：
{input_content}

{f'额外指令：{extra_instructions}' if extra_instructions else ''}

{_academic_instruction}"""
            else:
                prompt = f"""You are the {debater['en_name']} debater of the {dept['en_name']} Department.

{ANIME_VISUAL_DIRECTIVE['en']}

{debater['en_style']}
{constraints}
{cf_block}
Current discussion topic:
{input_content}

{f'Extra instructions: {extra_instructions}' if extra_instructions else ''}

Propose your specific plan and recommendations from your professional perspective. Be specific, detailed, and reasoned. No vague statements."""
        else:
            prev_args = "\n\n---\n\n".join(all_arguments[-3:])
            reminder = get_screenwriter_reminder(lang) if department_key == "screenwriter" else ""
            if is_zh:
                prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的{debater['zh_name']}辩手。

{ANIME_VISUAL_DIRECTIVE['zh']}

{debater['zh_style']}
{reminder}
当前讨论内容：
{input_content}

前几轮其他辩手的观点：
{prev_args}

这是第{round_num}轮辩论。请回应其他辩手的观点——你同意什么？反对什么？你的方案和他们的方案如何取舍？如果可以融合，怎么融合？"""
            else:
                prompt = f"""You are the {debater['en_name']} debater of the {dept['en_name']} Department.

IMPORTANT: You MUST respond in English only. All output must be in English.

{ANIME_VISUAL_DIRECTIVE['en']}

{debater['en_style']}
{reminder}
Current discussion topic:
{input_content}

Previous arguments from other debaters:
{prev_args}

This is Round {round_num}. Respond to other debaters—what do you agree with? Disagree with? How would you trade off between your approach and theirs? If fusion is possible, how?"""
        
        messages = [{"role": "user", "content": prompt}]
        response = call_api(messages, api_url, api_key, model, temperature=0.7, stats=stats)
        
        if response and not response.startswith("ERROR:"):
            arg_text = f"[{debater['zh_name'] if is_zh else debater['en_name']} 第{round_num}轮]: {response}"
            all_arguments.append(arg_text)
            round_log.append({
                "round": round_num,
                "debater": debater_key,
                "debater_name": debater["zh_name"] if is_zh else debater["en_name"],
                "content": response,
            })
    
    return round_log, all_arguments

def run_department_consensus(
    department_key: str,
    all_arguments: list,
    input_content: str,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    extra_instructions: str = "",
    rounds: int = 3,
    stats: dict = None,  # Token statistics累加器
) -> str:
    """
    从累积的辩论论点生成结构化共识
    """
    dept = DEPARTMENTS[department_key]
    is_zh = lang == "zh"
    all_args_text = "\n\n---\n\n".join(all_arguments)
    
    template = STRUCTURED_TEMPLATES.get(department_key, {}).get(lang, "")
    
    constraint_check = ""
    if department_key == "screenwriter":
        if is_zh:
            constraint_check = '\n\n【编剧部硬约束检查】最终方案中不得出现用户剧本未有的新角色、新人物关系、新情节支线或新对话。如果辩手提议中有违反约束的内容，必须剔除，并在方案中标注"此建议已因超出编剧职权而剔除"。'
        else:
            constraint_check = '\n\n[Screenwriter Hard Constraint Check] The final plan must NOT contain new characters, new relationships, new plot sublines, or new dialogue not in the user\'s script. Any constraint-violating proposals must be removed and marked as "This suggestion was removed for exceeding screenwriter authority.".'
    
    if is_zh:
        consensus_prompt = f"""【重要】你必须使用中文回答。所有输出必须是中文。

你是{dept['zh_name']}的辩论主持人。

以下是{dept['zh_name']}{len(dept['debaters'])}位辩手经过{rounds}轮辩论后的全部观点：

{all_args_text}

{f'额外指令：{extra_instructions}' if extra_instructions else ''}

请综合{len(dept['debaters'])}位辩手的观点，形成{dept['zh_name']}的最终共识方案。要求：
1. 明确采纳了哪些观点，为什么
2. 明确舍弃了哪些观点，为什么
3. 最终方案要具体、可执行、有细节
4. 不要含糊地说"综合各方意见"，要给出明确的决策{constraint_check}

{template}"""
    else:
        consensus_prompt = f"""You are the debate moderator for the {dept['en_name']} Department.

IMPORTANT: You MUST respond in English only. All output must be in English.

Below are all arguments from {len(dept["debaters"])} debaters after {rounds} rounds:

{all_args_text}

{f'Extra instructions: {extra_instructions}' if extra_instructions else ''}

Synthesize a final consensus. Requirements:
1. Clearly state which viewpoints were adopted and why
2. Clearly state which were rejected and why
3. The final plan must be specific, actionable, and detailed
4. Don't vaguely say 'combining all views'—give clear decisions{constraint_check}

{template}"""
    
    messages = [{"role": "user", "content": consensus_prompt}]
    consensus = call_api(messages, api_url, api_key, model, temperature=0.3, timeout=240, stats=stats)
    if consensus and consensus.startswith("ERROR:"):
        return f"⚠️ 共识生成失败：{consensus}"
    return consensus or "辩论未能达成共识"

# ============ Carry-Forward Document ============

CARRY_FORWARD_TEMPLATE = {
    "zh": """请根据以下前段辩论的完整产出，提取一份结构化的「承上文档」，用于保证多段剧本之间的连续性。

请严格按照以下结构输出：

## 故事状态
- 角色位置与状态：[每个角色当前在哪、什么状态]
- 刚发生的关键事件：[上一个段落的结尾事件]
- 角色当前情绪：[每个角色的情绪走向]
- 出场角色清单：[所有角色/元素的在场状态，谁还在场、谁已退场]
- 叙事节拍：[前段完成的节拍，下一段从哪个节拍继续]

## 空间状态
- 当前场景布局：[环境布局的延续状态]
- 角色当前物品参照位置：[每个角色当前以什么物品为参照在什么位置，如"长桌靠墙侧左端"]
- 物品当前位置：[关键物品在什么位置、什么状态]

## 已确定的分镜结构
- 总Shot数：[N]
- 逐Shot摘要（每Shot一行）：
  - Shot XX: [景别] / [运镜] / [内容概要] / [时长]
- 最后一个Shot的结尾画面：[精确描述，这是下一段的起点]

## 画面决策
- 镜头风格：[已确定的镜头语言偏好]
- 色调/氛围：[已建立的视觉基调]
- 运镜偏好：[倾向的运镜方式]
- 景别偏好：[常用的景别选择]

## 灯光/VFX方向
- 光影语言：[已建立的灯光风格]
- 特效风格：[已确定的特效方向]
- 视觉质感：[画面质感要求]

## 声音风格
- 环境音基调：[声音空间感]
- 拟音风格：[动作音效风格]
- 情绪声景：[声音情绪引导方式]

## 时间线动作
- 按时间轴列出关键动作节点：[0s: xxx → 2s: xxx → ...]
- 下一段的起始时间偏移：[上一段总时长]

## 未了悬念
- [待续/悬念元素，需要在下一段延续的内容]

## 关键约束
- [必须在下一段遵守的硬性决策，避免风格断裂]

---

前段各部门辩论共识：
{consensus_text}

前段最终产出——分镜表：
{storyboard_prompt}

前段最终产出——视频逐镜提示词：
{video_prompt}""",
    "en": """Based on the complete outputs from the previous segment's debate, extract a structured "Carry Forward Document" to ensure continuity between script segments.

Output strictly in this structure:

## Story State
- Character positions & status: [where each character is, current state]
- Key events just happened: [ending events from the previous segment]
- Character emotions: [each character's emotional trajectory]
- On-screen roster: [all characters/elements' presence status—who is still present, who has exited]
- Narrative beats: [beats completed in the previous segment, which beat the next segment continues from]

## Spatial State
- Current scene layout: [continuation state of environment layout]
- Character current object-referenced positions: [which object each character is referenced to, e.g. "left end of long table on wall side"]
- Object current positions: [where key objects are, current state]

## Established Storyboard Structure
- Total shots: [N]
- Per-shot summary (one line each):
  - Shot XX: [shot type] / [camera movement] / [content summary] / [duration]
- Final shot's ending frame: [precise description — starting point for next segment]

## Visual Decisions
- Camera style: [established camera language preferences]
- Color tone / atmosphere: [established visual tone]
- Camera movement preferences: [preferred movement styles]
- Shot type preferences: [common shot types used]

## Lighting / VFX Direction
- Lighting language: [established lighting style]
- VFX style: [established effects direction]
- Visual texture: [image quality requirements]

## Sound Style
- Ambient baseline: [spatial sound characteristics]
- Foley style: [action sound design style]
- Emotional soundscape: [sound-driven emotional guidance approach]

## Timeline Actions
- Key action nodes on timeline: [0s: xxx → 2s: xxx → ...]
- Next segment time offset: [total duration of previous segment]

## Unresolved Elements
- [Cliffhangers / elements that must continue into the next segment]

## Key Constraints
- [Hard decisions that must be followed in the next segment to avoid style breaks]

---

Previous segment department consensuses:
{consensus_text}

Previous segment final output — Storyboard:
{storyboard_prompt}

Previous segment final output — Per-shot video prompt:
{video_prompt}""",
}

def generate_asset_checklist(
    all_consensus: Dict[str, str],
    user_script: str = "",
    character_refs: str = "",
    lang: str = "zh",
) -> str:
    """
    从各部门共识中提取"所需资产参照表"，
    列出制作动画前需要准备的素材清单。纯文本提取+格式化，不需要API调用。
    """
    import re
    is_zh = lang == "zh"
    
    sw_consensus = all_consensus.get("screenwriter", "")
    sp_consensus = all_consensus.get("spatial", "")
    
    # ---- Extract characters ----
    characters = []
    if is_zh:
        # Extract character/element list from screenwriter consensus
        roster_match = re.search(r'## 出场角色与元素清单(.*?)(?=\n## |\Z)', sw_consensus, re.DOTALL)
    else:
        roster_match = re.search(r'## On-Screen Roster(.*?)(?=\n## |\Z)', sw_consensus, re.DOTALL)
    
    if roster_match:
        roster_text = roster_match.group(1)
        # Extract "- [name]" lines
        for line in roster_text.strip().split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Extract character name (before first colon or parenthesis)
                name = re.sub(r'^[-–]\s*', '', line)
                # Truncate at first colon or parenthesis
                cut = re.search(r'[：:（(]', name)
                if cut:
                    name = name[:cut.start()].strip()
                if name:
                    characters.append(name)
    
    # ---- Extract micro-expression requirements (for character asset description) ----
    expression_needs = {}
    if characters:
        if is_zh:
            expr_match = re.search(r'## 微表情清单(.*?)(?=\n## |\Z)', sw_consensus, re.DOTALL)
        else:
            expr_match = re.search(r'## Micro-Expression List(.*?)(?=\n## |\Z)', sw_consensus, re.DOTALL)
        if expr_match:
            expr_text = expr_match.group(1)
            for char in characters:
                # Find expression description for this character
                char_exprs = []
                for line in expr_text.strip().split("\n"):
                    if char in line:
                        # Extract expression description (after colon)
                        parts = line.split("：") if is_zh else line.split(": ")
                        if len(parts) > 1:
                            char_exprs.append(parts[-1].strip()[:60])
                if char_exprs:
                    expression_needs[char] = "；".join(char_exprs)
    
    # ---- Extract props/items ----
    props = []
    if is_zh:
        prop_match = re.search(r'#### 场景物品清单（定位基准）(.*?)(?=\n####|\n###|\Z)', sp_consensus, re.DOTALL)
    else:
        prop_match = re.search(r'#### Scene Object Inventory \(Positioning Baseline\)(.*?)(?=\n####|\n###|\Z)', sp_consensus, re.DOTALL)
    
    if prop_match:
        prop_text = prop_match.group(1)
        for line in prop_text.strip().split("\n"):
            line = line.strip()
            if line.startswith("-"):
                name = re.sub(r'^[-–]\s*', '', line)
                # Extract item name (before first colon)
                cut = re.search(r'[：:]', name)
                if cut:
                    prop_name = name[:cut.start()].strip()
                    prop_desc = name[cut.end():].strip()[:80]
                else:
                    prop_name = name.strip()[:20]
                    prop_desc = ""
                if prop_name:
                    props.append((prop_name, prop_desc))
    
    # ---- Extract scenes ----
    scenes = []
    if is_zh:
        scene_matches = re.findall(r'### 场景[一二三四五六七八九十\d]+[：:]\s*(.*?)(?=\n####|\Z)', sp_consensus, re.DOTALL)
    else:
        scene_matches = re.findall(r'### Scene \d+[：:]\s*(.*?)(?=\n####|\Z)', sp_consensus, re.DOTALL)
    
    for sm in scene_matches:
        scene_name = sm.strip().split("\n")[0].strip()[:30]
        if scene_name:
            scenes.append(scene_name)
    
    if not scenes:
        # Try extracting from scene count judgment
        if is_zh:
            sc_match = re.search(r'场景数量[：:]\s*(\d+)', sp_consensus)
        else:
            sc_match = re.search(r'Number of scenes[：:]\s*(\d+)', sp_consensus)
        if sc_match:
            n = int(sc_match.group(1))
            scenes = [f"{'场景' if is_zh else 'Scene'} {i+1}" for i in range(n)]
        else:
            scenes = ["主场景" if is_zh else "Main Scene"]
    
    # ---- Format output ----
    if is_zh:
        lines = ["## 📋 资产参照表 (Asset Checklist)\n"]
        
        lines.append("### 🎭 角色资产")
        if characters:
            for char in characters:
                expr = expression_needs.get(char, "")
                detail = f"需三视图/角色卡 + {expr}" if expr else "需三视图/角色卡"
                lines.append(f"- {char}：{detail}")
        else:
            lines.append("- （未从编剧共识中提取到角色，请手动补充）")
        
        lines.append("\n### 🪑 道具/物品资产")
        if props:
            for prop_name, prop_desc in props:
                desc = f"：{prop_desc}" if prop_desc else ""
                lines.append(f"- {prop_name}{desc}")
        else:
            lines.append("- （未从空间共识中提取到物品，请手动补充）")
        
        lines.append("\n### 🏞️ 场景背景资产")
        for scene in scenes:
            lines.append(f"- {scene}：背景底图 + 空间布局参照")
        
        lines.append("\n### 📝 备注")
        lines.append("- 角色表情需求需从编剧部微表情清单中对照提取")
        lines.append("- 场景物品需与空间部物品清单一一对应")
    else:
        lines = ["## 📋 Asset Checklist\n"]
        
        lines.append("### 🎭 Character Assets")
        if characters:
            for char in characters:
                expr = expression_needs.get(char, "")
                detail = f"Need turnaround/character card + {expr}" if expr else "Need turnaround/character card"
                lines.append(f"- {char}: {detail}")
        else:
            lines.append("- (No characters extracted from screenwriter consensus; please add manually)")
        
        lines.append("\n### 🪑 Prop/Object Assets")
        if props:
            for prop_name, prop_desc in props:
                desc = f": {prop_desc}" if prop_desc else ""
                lines.append(f"- {prop_name}{desc}")
        else:
            lines.append("- (No objects extracted from spatial consensus; please add manually)")
        
        lines.append("\n### 🏞️ Scene Background Assets")
        for scene in scenes:
            lines.append(f"- {scene}: Background base + spatial layout reference")
        
        lines.append("\n### 📝 Notes")
        lines.append("- Character expression needs should be cross-referenced from Screenwriter micro-expression list")
        lines.append("- Scene objects should correspond one-to-one with Spatial Planning object inventory")
    
    return "\n".join(lines)

def generate_carry_forward(
    all_consensus: Dict[str, str],
    cross_results: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    storyboard_prompt: str = "",
    video_prompt: str = "",
    stats: dict = None,  # Token statistics累加器
) -> str:
    """
    从各部门辩论共识 + 最终产出中提取结构化承上文档，
    用于多段剧本场景下保证段与段之间的连续性。
    """
    is_zh = lang == "zh"

    consensus_text = ""
    for dept_key, consensus in all_consensus.items():
        dept = DEPARTMENTS[dept_key]
        name = dept["zh_name"] if is_zh else dept["en_name"]
        consensus_text += f"\n### {name}\n{consensus}\n"

    cross_text = ""
    for cr in cross_results:
        a_dept = DEPARTMENTS[cr["side_a"]]
        b_dept = DEPARTMENTS[cr["side_b"]]
        a_name = a_dept["zh_name"] if is_zh else a_dept["en_name"]
        b_name = b_dept["zh_name"] if is_zh else b_dept["en_name"]
        cross_text += f"\n### {a_name} vs {b_name} — {cr['topic']}\n{cr.get('debate_result', '')}\n"

    full_consensus = consensus_text
    if cross_text:
        full_consensus += f"\n### Cross-debate results\n{cross_text}" if is_zh else f"\n### Cross-Debate Results\n{cross_text}"

    template = CARRY_FORWARD_TEMPLATE.get(lang, CARRY_FORWARD_TEMPLATE["zh"])
    prompt = template.format(
        consensus_text=full_consensus,
        storyboard_prompt=storyboard_prompt or ("（未生成分镜表）" if is_zh else "(Storyboard not generated)"),
        video_prompt=video_prompt or ("（未生成视频提示词）" if is_zh else "(Video prompt not generated)"),
    )

    messages = [{"role": "user", "content": prompt}]
    result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=4096, stats=stats)
    return result or ("承上文档生成失败" if is_zh else "Carry forward generation failed")

def run_output_edit(
    department_key: str,
    edit_instructions: str,
    current_storyboard: str,
    current_video_prompt: str,
    spatial_consensus: str,
    all_consensus: Dict[str, str],
    edit_spatial: bool = False,
    api_url: str = "",
    api_key: str = "",
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,  # Token statistics累加器
) -> Dict:
    """
    产出回炉编辑：将分镜表/视频提示词/空间表发送给指定部门，
    由该部门从专业视角按修改意见进行定向修改和添加内容。
    比导演指令修正更轻量——不重跑辩论，直接在产出上做定点编辑。
    """
    is_zh = lang == "zh"
    dept = DEPARTMENTS[department_key]
    dept_name = dept["zh_name"] if is_zh else dept["en_name"]
    
    # Build professional perspective description for this dept
    debater_styles = []
    for dk, debater in dept["debaters"].items():
        style = debater["zh_style"] if is_zh else debater["en_style"]
        dname = debater["zh_name"] if is_zh else debater["en_name"]
        debater_styles.append(f"- {dname}: {style}")
    dept_perspective = "\n".join(debater_styles)
    
    # Previous debate consensus for this dept
    dept_consensus = all_consensus.get(department_key, "")
    
    # Build spatial editing paragraph
    spatial_edit_section = ""
    if edit_spatial:
        if is_zh:
            spatial_edit_section = f"""
===== 当前空间板块定义 =====
{spatial_consensus}

你还需要修改空间板块定义（物品清单、角色定位、动线等）。如果修改了物品定位，必须同步更新分镜表和视频提示词中所有引用该定位的地方。

输出格式增加一段：
===== 修改后空间板块 =====
[完整的修改后空间板块定义]
"""
        else:
            spatial_edit_section = f"""
===== Current Spatial Layout =====
{spatial_consensus}

You also need to edit the spatial layout (object inventory, character positioning, movement paths, etc.). If you change object positioning, you must update all references in the storyboard and video prompt.

Output format adds:
===== Revised Spatial Layout =====
[Complete revised spatial layout definition]
"""
    
    if is_zh:
        prompt = f"""你是{dept_name}的资深编辑。导演要求你从{dept_name}的专业视角，对以下产出进行定向修改。

【{dept_name}专业视角】
{dept_perspective}

【{dept_name}辩论共识（供参考）】
{dept_consensus}

【导演修改意见】
{edit_instructions}

===== 当前分镜表 =====
{current_storyboard}

===== 当前视频逐镜提示词 =====
{current_video_prompt}
{spatial_edit_section}
【修改要求】
1. 严格按照导演修改意见，从{dept_name}的专业视角修改和添加内容
2. 如果修改涉及空间物品定位变化，必须同步更新所有引用该定位的地方
3. 如果修改涉及Shot数量变化，分镜表和视频提示词必须同步增减
4. 确保每个Shot仍有【完整画面】段
5. 确保每个Shot仍有叙事节拍、切换动机、出场角色三个字段，且与对应部门共识一致
6. 未涉及的Shot保持不变
7. 直接输出修改后的完整产出，不要只输出差异

请按以下格式输出：

===== 修改后分镜表 =====
[完整的修改后分镜表]

===== 修改后视频提示词 =====
[完整的修改后视频提示词]

===== 修改说明 =====
[逐条列出你做了哪些修改]"""
    else:
        prompt = f"""You are a senior editor from the {dept['en_name']} Department. The director has asked you to make targeted edits to the following outputs from your department's professional perspective.

[{dept['en_name']} Professional Perspective]
{dept_perspective}

[{dept['en_name']} Debate Consensus (for reference)]
{dept_consensus}

[Director's Edit Instructions]
{edit_instructions}

===== Current Storyboard =====
{current_storyboard}

===== Current Video Prompts =====
{current_video_prompt}
{spatial_edit_section}
[Editing Requirements]
1. Follow the director's edit instructions strictly, making changes from the {dept['en_name']}'s professional perspective
2. If edits involve spatial object positioning changes, update all references to those positions
3. If edits involve shot count changes, synchronize storyboard and video prompt additions/removals
4. Ensure every Shot still has a [Complete Frame] section
5. Ensure every Shot still has Narrative Beat, Switch Motivation, and On-Screen Characters fields, matching the corresponding department consensus
6. Keep unchanged Shots intact
7. Output the COMPLETE revised outputs, not just diffs

Output format:

===== Revised Storyboard =====
[Complete revised storyboard]

===== Revised Video Prompts =====
[Complete revised video prompts]

===== Edit Notes =====
[List each change you made]"""
    
    messages = [{"role": "user", "content": prompt}]
    result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=16384, timeout=180, stats=stats)
    
    # Parse modification results
    revised_storyboard = current_storyboard
    revised_video_prompt = current_video_prompt
    revised_spatial = spatial_consensus if edit_spatial else None
    edit_notes = ""
    
    if result and not result.startswith("ERROR:"):
        if is_zh:
            sb_marker = "===== 修改后分镜表 ====="
            vp_marker = "===== 修改后视频提示词 ====="
            notes_marker = "===== 修改说明 ====="
            spatial_marker = "===== 修改后空间板块 ====="
        else:
            sb_marker = "===== Revised Storyboard ====="
            vp_marker = "===== Revised Video Prompts ====="
            notes_marker = "===== Edit Notes ====="
            spatial_marker = "===== Revised Spatial Layout ====="
        
        # Parse storyboard
        if sb_marker in result:
            after_sb = result.split(sb_marker, 1)[1]
            sb_end = len(after_sb)
            for em in [vp_marker, notes_marker]:
                idx = after_sb.find(em)
                if idx >= 0 and idx < sb_end:
                    sb_end = idx
            revised_storyboard = after_sb[:sb_end].strip()
        
        # Parse video prompts
        if vp_marker in result:
            after_vp = result.split(vp_marker, 1)[1]
            vp_end = len(after_vp)
            for em in [notes_marker, spatial_marker]:
                idx = after_vp.find(em)
                if idx >= 0 and idx < vp_end:
                    vp_end = idx
            revised_video_prompt = after_vp[:vp_end].strip()
        
        # Parse spatial dept (optional)
        if edit_spatial and spatial_marker in result:
            after_sp = result.split(spatial_marker, 1)[1]
            sp_end = after_sp.find(notes_marker)
            if sp_end >= 0:
                revised_spatial = after_sp[:sp_end].strip()
            else:
                revised_spatial = after_sp.strip()
        
        # Parse modification notes
        if notes_marker in result:
            notes_text = result.split(notes_marker, 1)[1].strip()
            # Remove spatial dept markers that may have leaked into the end
            if spatial_marker in notes_text:
                notes_text = notes_text[:notes_text.find(spatial_marker)].strip()
            edit_notes = notes_text
    
    return {
        "department": department_key,
        "dept_name": dept_name,
        "storyboard_prompt": revised_storyboard,
        "video_prompt": revised_video_prompt,
        "spatial_consensus": revised_spatial,
        "edit_notes": edit_notes,
        "edit_instructions": edit_instructions,
        "original_storyboard": current_storyboard,
        "original_video_prompt": current_video_prompt,
    }
# ============ Smart Re-roll ============

def run_smart_reroll(
    selected_departments: list,
    revision_feedback: str,
    dept_order: list,
    all_dept_results: Dict[str, dict],
    user_script: str,
    positive_prompt: str,
    negative_prompt: str,
    character_refs: str,
    cross_debate_pairs: list,
    existing_cross_results: list,
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    debate_rounds: int = 2,
    progress_callback: Callable = None,
    stats: dict = None,
) -> Dict:
    """
    智能回炉：只重跑选中的部门，然后重新生成交叉辩论和最终产出。
    
    Args:
        selected_departments: 要回炉的部门key列表
        revision_feedback: 用户修改意见
        dept_order: 完整的部门执行顺序
        all_dept_results: 所有部门的现有辩论结果 {dept_key: {"consensus": ..., "debate_log": [...]}}
        user_script/positive_prompt/negative_prompt/character_refs: 用户输入
        cross_debate_pairs: 需要重新交叉辩论的部门对
        existing_cross_results: 现有的交叉辩论结果
        api_url/api_key/model: LLM配置
        lang: 语言
        debate_rounds: 回炉辩论轮数
        progress_callback: 进度回调
        stats: Token统计
    
    Returns:
        {
            "updated_dept_results": {dept_key: {"consensus": ..., "debate_log": [...]}},  # 完整结果（含未修改的）
            "updated_cross_results": [...],  # 完整交叉辩论结果
            "final_output": {...},  # run_summary的输出
            "reroll_log": [{"dept_key": ..., "status": "ok"/"error", "message": ...}],
            "error": False
        }
    """
    is_zh = lang == "zh"
    reroll_log = []
    
    # Deep copy existing results, re-rolled departments will be updated
    import copy
    updated_dept_results = copy.deepcopy(all_dept_results)
    
    # Build carry-forward info: screenwriter output for downstream reference
    def _build_input_for_dept(dk: str) -> str:
        """为指定部门构建输入内容"""
        script_block = f"用户剧本：\n{user_script}" if is_zh else f"User Script:\n{user_script}"
        if positive_prompt:
            script_block += f"\n\n正向提示词：{positive_prompt}" if is_zh else f"\n\nPositive Prompt: {positive_prompt}"
        if character_refs:
            script_block += f"\n\n角色参考：{character_refs}" if is_zh else f"\n\nCharacter References: {character_refs}"
        return script_block
    
    # Re-roll in dept_order, ensure upstream output passes to downstream
    selected_set = set(selected_departments)
    reroll_order = [dk for dk in dept_order if dk in selected_set]
    
    for dk in reroll_order:
        if progress_callback:
            dept_name = DEPARTMENTS[dk]["zh_name"] if is_zh else DEPARTMENTS[dk]["en_name"]
            progress_callback(f"🔄 {dept_name}...")
        
        try:
            # Build input: latest consensus from upstream departments
            input_content = _build_input_for_dept(dk)
            
            # Add upstream department consensus
            dept_idx = dept_order.index(dk) if dk in dept_order else -1
            if dept_idx > 0:
                upstream_text = ""
                for upstream_dk in dept_order[:dept_idx]:
                    if upstream_dk in updated_dept_results:
                        consensus = updated_dept_results[upstream_dk].get("consensus", "")
                        if consensus:
                            name = DEPARTMENTS[upstream_dk]["zh_name"] if is_zh else DEPARTMENTS[upstream_dk]["en_name"]
                            upstream_text += f"\n\n【{name}共识】\n{consensus}"
                if upstream_text:
                    prefix = "上游部门共识：\n" if is_zh else "Upstream Department Consensus:\n"
                    input_content = prefix + upstream_text.strip() + "\n\n---\n\n" + input_content
            
            # Re-roll debate
            result = run_department_debate(
                department_key=dk,
                input_content=input_content,
                api_url=api_url,
                api_key=api_key,
                model=model,
                rounds=debate_rounds,
                lang=lang,
                extra_instructions=revision_feedback,
                stats=stats,
            )
            
            updated_dept_results[dk] = result
            reroll_log.append({
                "dept_key": dk,
                "status": "ok",
                "message": f"回炉完成" if is_zh else "Re-roll complete",
            })
        except Exception as e:
            reroll_log.append({
                "dept_key": dk,
                "status": "error",
                "message": str(e),
            })
    
    # Re-run cross-debate
    updated_cross_results = list(existing_cross_results)  # 先保留旧的
    
    if cross_debate_pairs:
        if progress_callback:
            progress_callback("⚔️ " + ("重新交叉辩论..." if is_zh else "Re-running cross-debates..."))
        
        # Find cross-debates to re-run: any end involves re-rolled department
        affected_cross = []
        unaffected_cross = []
        for cr in existing_cross_results:
            side_a = cr.get("side_a", "")
            side_b = cr.get("side_b", "")
            if side_a in selected_set or side_b in selected_set:
                affected_cross.append(cr)
            else:
                unaffected_cross.append(cr)
        
        # Re-run affected cross-debates
        new_cross_results = []
        for cr in affected_cross:
            side_a = cr["side_a"]
            side_b = cr["side_b"]
            
            if side_a in updated_dept_results and side_b in updated_dept_results:
                try:
                    cross_result = run_cross_debate(
                        cross_config=cr,
                        dept_a_consensus=updated_dept_results[side_a].get("consensus", ""),
                        dept_b_consensus=updated_dept_results[side_b].get("consensus", ""),
                        api_url=api_url,
                        api_key=api_key,
                        model=model,
                        lang=lang,
                        stats=stats,
                    )
                    new_cross_results.append(cross_result)
                except Exception:
                    # Cross-debate failed, keep old one
                    new_cross_results.append(cr)
            else:
                new_cross_results.append(cr)
        
        # Merge: new affected + unaffected
        updated_cross_results = new_cross_results + unaffected_cross
    
    # Regenerate final output
    if progress_callback:
        progress_callback("🎬 " + ("重新生成最终产出..." if is_zh else "Regenerating final output..."))
    
    all_consensus = {k: v["consensus"] for k, v in updated_dept_results.items()}
    
    try:
        final_output = run_summary(
            user_script=user_script,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            character_refs=character_refs,
            all_consensus=all_consensus,
            cross_results=updated_cross_results,
            api_url=api_url,
            api_key=api_key,
            model=model,
            lang=lang,
            stats=stats,
        )
    except Exception as e:
        final_output = {
            "error": True,
            "message": str(e),
            "storyboard_prompt": "",
            "video_prompt": "",
        }
    
    return {
        "updated_dept_results": updated_dept_results,
        "updated_cross_results": updated_cross_results,
        "final_output": final_output,
        "reroll_log": reroll_log,
        "error": False,
    }

def run_academic_auto_revision(
    final_report: str,
    proofread_result: Dict,
    all_consensus: Dict[str, str],
    api_url: str,
    api_key: str,
    model: str = "deepseek-v4-flash",
    lang: str = "zh",
    stats: dict = None,
) -> Dict:
    """
    Academic mode: auto-revise final_report based on proofreading feedback.
    """
    is_zh = lang == "zh"
    reviews = proofread_result.get("reviews", {})

    # Collect all issue items
    all_issues = ""
    academic_dept_names = {
        "report_integration": {"zh": "报告整合组", "en": "Report Integration"},
        "programming": {"zh": "程序部", "en": "Programming"},
        "tutorial": {"zh": "教程部", "en": "Tutorial"},
    }
    for dept_key in ACADEMIC_PROOFREAD_DEPARTMENTS:
        dept_name_map = academic_dept_names.get(dept_key, {})
        dept_name = dept_name_map.get(lang, dept_key)
        review = reviews.get(dept_key, "")
        all_issues += f"\n### {dept_name}校对反馈\n{review}\n"

    if is_zh:
        revise_prompt = f"""你是校对修正专家。以下是校对环节发现的所有问题，请直接修正学术报告。

===== 校对反馈汇总 =====
{all_issues}

===== 原学术报告 =====
{final_report[:30000]}

【修正要求】
1. 逐条处理校对反馈中的❌问题项，按修正建议修改
2. 修正时保持其他未涉及部分不变
3. 确保修正后报告仍是完整的8章节结构
4. 确保不引入动画/视觉术语
5. 确保代码和教程围绕研究主题方法，而非管线基础设施
6. 直接输出修正后的完整报告，不要只输出差异

请按以下格式输出：

===== 修正后报告 =====
[完整的修正后学术报告]

===== 修正说明 =====
[逐条列出你做了哪些修正]"""
    else:
        revise_prompt = f"""You are a proofreading revision expert. Below are all issues found during proofreading. Please directly fix the academic report.

===== Proofreading Feedback Summary =====
{all_issues}

===== Original Academic Report =====
{final_report[:30000]}

[Revision Requirements]
1. Address each ❌ issue found in proofreading, apply the fix suggestions
2. Keep all untouched parts unchanged
3. Ensure the revised report still has the complete 8-chapter structure
4. Ensure no animation/visual terms are introduced
5. Ensure code and tutorial focus on research topic methods, not pipeline infrastructure
6. Output the COMPLETE revised report, not just diffs

Output format:

===== Revised Report =====
[Complete revised academic report]

===== Revision Notes =====
[List each change you made]"""

    messages = [{"role": "user", "content": revise_prompt}]
    result = call_api(messages, api_url, api_key, model, temperature=0.2, max_tokens=16384, timeout=180, stats=stats)

    revised_report = final_report
    revision_notes = ""

    if result and not result.startswith("ERROR:"):
        if is_zh:
            marker = "===== 修正后报告 ====="
            notes_marker = "===== 修正说明 ====="
        else:
            marker = "===== Revised Report ====="
            notes_marker = "===== Revision Notes ====="

        if marker in result:
            after_marker = result.split(marker, 1)[1]
            if notes_marker in after_marker:
                parts = after_marker.split(notes_marker, 1)
                revised_report = parts[0].strip()
                revision_notes = parts[1].strip()
            else:
                revised_report = after_marker.strip()

    return {
        "final_report": revised_report,
        "revision_notes": revision_notes,
        "original_report": final_report,
    }
