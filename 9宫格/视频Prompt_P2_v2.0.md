# SHOT B 视频Prompt P2：榴弹射击+爆炸（9个SHOT）

> 版本：v2.0 | 按v3.1实测通过格式重写 | 严格对应9宫格故事板的9个格子
> 每个SHOT独立生成1-2秒视频，后期剪辑拼接为长镜头

---

## 统一场景提示词（所有SHOT共用）

电影奇幻风格，写实风格，电影级布光，PBR物理渲染，全局光照，高细节金属纹理，皮肤次表面散射，哑光金属材质，粗麻布纹理，Octane渲染，8k分辨率，杰作。黄昏荒地，暖金色（5000K）侧逆光，沙尘弥漫，高对比度，体积光，暖金冷蓝色彩对比。

## 统一负面提示词（所有SHOT共用）

变形，扭曲，鬼影，模糊，过曝，闪烁，突变，溶解，多余肢体，复制人，穿模，低质量，画面撕裂，抖动过度，3D渲染蜡像感，油腻，磨皮，卡通，水印，切镜感，叠化转场，淡入淡出，背景音乐，cat，feline，animal

全程有音效，不要有背景音乐.

## 马车空间关系

整体布局如下 [把圈红的这个顶棚扩大一点，这是马车的棚，] ，其中沿前后轴线布局，从最前端到最后端依次为：棕色马匹在最前方全力奔跑拉行整个车辆，四蹄完全伸展；紧挨马匹之后是车头开放站位，莉雅 [莉雅 三视图] 站在那里面朝前方双手握着缰绳赶马，她的背部朝向车厢方向；莉雅 [莉雅 三视图] 身后是木板结构的中间车厢，车厢内散放着货物和弩炮弹药，木板墙壁上有缝隙让沙尘涌入，车厢尾部有一面带窗口的后墙；奥梵 [奥梵 三视图] 坐在车尾窗口内侧，背对马车行进方向面朝后方，透过窗口持着奥术弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 瞄准马车后方的追击者。

整辆车上四者的位置永远保持这个前后顺序：马在最前，莉雅在马后面朝前，车厢在中间，奥梵在最后面朝后。莉雅和奥梵面朝相反方向，莉雅朝车头前方赶马，奥梵朝车尾后方迎敌。

### 参考图

| 角色 | 参考图 | 用法 |
|------|--------|------|
| 莉雅 | [莉雅 三视图] [莉亚表情2] | 出现时直接引用，不描述外貌 |
| 奥梵 | [奥梵 三视图] [奥梵 表情] | 出现时直接引用，不描述外貌 |
| 弩炮 | [[参考图1] 单独把这个魔法枪的三视图]] | 出现弩炮时直接引用 |
| 沙虫 | [图片 (4)] | 出现时直接引用 |
| 马车+马 | [把圈红的这个顶棚扩大一点，这是马车的棚，] | 出现马车时直接引用，同时作为空间位置参考 |

**⚠️ 注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。**

马车+马 [把圈红的这个顶棚扩大一点，这是马车的棚，]。注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。

接下来，你需要根据分镜表 @[全格约束 单张16:9横屏图片，3×3] 左上方标注序号，按照下面的提示词来生成连续的画面，通过运镜，根据镜头引导进行切镜和镜头间的内容补充，将每一个分镜连续到一起。

## SHOT 01 | 奥梵过肩瞄准 | 0-1s

参考分镜图：9宫格格子第一排第一个①

**运镜**：中近景，过肩构图，从奥梵肩后朝车尾窗口拍
**打光**：侧逆光，奥梵肩部轮廓光，窗外沙尘中金色微光
**引导**：视线从奥梵肩部穿过车尾窗口指向窗外——窗外沙虫模糊剪影即瞄准目标→衔接到②弩炮特写
**主体**：奥梵 [奥梵 三视图] 过肩构图，透过车尾窗口瞄准。窗外远处沙虫 [图片 (4)] 模糊剪影如暗色巨影移动。奥梵双手持弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 架在肩上对准窗外
**背景虚化**：浅景深，窗外沙虫模糊

### 正面提示词

Medium-close shot, over-the-shoulder composition from behind a girl figure's shoulder toward the wagon's rear window, shallow depth of field. A girl figure aiming through the rear window of a wooden wagon, holding a mounted weapon on her shoulder pointing outward through the window. Through the window, a sandworm's blurry dark silhouette moving in the distance like a shadow. Side-backlight with gold rim light on the shoulder, faint golden glow in the dusty window. Warm amber (5000K) side-backlight, volumetric dust, PBR rendering, cinematic grading.

### 音频描写

- 车厢内安静呼吸声
- 远处沙虫低频移动声（窗外，微弱）
- 风沙低鸣声

---

## SHOT 02 | 弩炮导能槽蓝光 | 1-2s

参考分镜图：9宫格格子第一排第二个②

**运镜**：极近特写，浅景深
**打光**：弩炮机匣微光照明，导能槽蓝光脉动作为主光源照亮画面
**引导**：导能槽蓝光脉动——蓄力视觉信号，蓝色弹药在弹膛入口准备推入→衔接到③扣扳机
**主体**：弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 极近特写——导能槽蓝光脉动如心跳节律，蓝色球形弹药悬浮在弹膛入口处等待推入，金属机匣表面微光反射
**背景虚化**：极浅景深，只有弩炮机匣清晰

### 正面提示词

Extreme close-up of the weapon's energy chamber, ultra-shallow depth of field. The weapon's energy channel pulsing with blue light in a heartbeat rhythm — a blue spherical ammo floating at the chamber entrance waiting to be loaded, metallic surface of the weapon reflecting faint light. Blue pulsing glow as the primary light source illuminating the frame. Warm amber ambient light (5000K) with blue energy glow contrast, PBR rendering, metallic textures, cinematic macro shot.

### 音频描写

- 导能槽蓝光脉动电子嗡鸣声（低频，节律感）
- 金属微震颤声

---

## SHOT 03 | 扣扳机推入弹药 | 2-3s

参考分镜图：9宫格格子第一排第三个③

**运镜**：近特写，弩炮侧面
**打光**：蓝光猛亮一闪作为瞬间照明，后坐力震颤带起沙尘微粒
**引导**：扣扳机瞬间——蓝色弹药被推入弹膛，弩炮后坐力震颤，蓄力完成即射击→衔接到④炮口射出
**主体**：扣扳机瞬间——弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 后坐力震颤，枪身微跳，蓝色弹药已推入弹膛深处发光。奥梵 [奥梵 三视图] 手指扣紧扳机，机械臂撑住后坐力
**背景虚化**：浅景深

### 正面提示词

Close-up side view of the weapon firing, shallow depth of field. The moment of trigger pull — the weapon recoils with a jolt, barrel jumping slightly, blue ammo pushed deep into the chamber glowing bright. A girl figure's finger tight on the trigger, mechanical arm bracing against the recoil. Blue flash as momentary intense illumination, dust particles kicked up by the recoil vibration. Warm amber (5000K) side-light overridden by blue flash, PBR rendering, cinematic action moment, motion blur on recoil.

### 音频描写

- 扳机扣动机械咔嗒声
- 蓝光闪爆电子音
- 弩炮后坐力金属撞击声
- 沙尘微粒飞溅声

---

## SHOT 04 | 榴弹从炮口射出 | 3-5s

参考分镜图：9宫格格子第二排第一个④

**运镜**：中近景，马车外侧后方，朝炮口方向拍
**打光**：榴弹射出瞬间红光闪烁照亮炮口周围，侧逆光勾勒马车轮廓
**引导**：榴弹从炮口射出向画面深处（车后方）飞去——红色信号灯闪烁表示已发射→衔接到⑤榴弹飞行
**主体**：马车后方外侧视角——榴弹从弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 炮口射出，红色信号灯闪烁的弹药。马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 继续向右行驶，车尾窗口奥梵 [奥梵 三视图] 刚射完身体微后仰
**背景虚化**：中浅景深

### 正面提示词

Medium-close shot from outside and behind the wagon, facing the weapon's muzzle, medium-shallow depth of field. A glowing projectile with flashing red signal light launching from the weapon's muzzle toward the deep background, red flash illuminating the muzzle area. The wagon continuing to move rightward, at the rear window a girl figure leaning back slightly from recoil. Side-backlight outlining the wagon silhouette with gold rim light. Red projectile flash contrasting with warm amber (5000K) ambient, PBR rendering, cinematic action, motion blur on projectile.

### 音频描写

- 榴弹射出爆鸣声（尖锐，短促）
- 弩炮后坐力金属回弹声
- 榴弹红色信号灯闪烁电子音
- 马车继续行驶的蹄声和轮轴声

---

## SHOT 05 | 榴弹拖着红光尾飞行 | 5-7s

参考分镜图：9宫格格子第二排第二个⑤

**运镜**：中景，跟随榴弹飞行路径
**打光**：黄昏侧逆光，榴弹红色光尾在暗色沙尘中如彗星
**引导**：榴弹拖着红色光尾向画面深处飞去——视线沿光尾追溯发现远处沙虫→衔接到⑥榴弹接近沙虫
**主体**：榴弹拖着鲜明红色光尾向画面深处（车后方）飞行，如暗夜彗星。画面远处沙虫 [图片 (4)] 巨大暗影在沙尘中若隐若现。地面沙尘被榴弹尾流搅起V字纹
**背景虚化**：中景深，榴弹清晰远处沙虫稍虚

### 正面提示词

Medium shot tracking alongside the projectile's flight path, medium depth of field. A glowing projectile trailing a vivid red comet-like tail flying deep into the distance through dark dusty air, like a comet in the night. Far in the background, the sandworm's enormous dark silhouette looming through the dust. V-shaped wake pattern in the sand below from the projectile's tailwind. Warm amber (5000K) side-backlight, the red tail stark against the dark dust, PBR rendering, cinematic tracking shot, motion blur on projectile trail.

### 音频描写

- 榴弹飞行破空尖啸声（由近到远）
- 红色光尾燃烧嘶嘶声
- 沙尘被尾流搅起的沙沙声

---

## SHOT 06 | 榴弹接近沙虫 | 7-8s

参考分镜图：9宫格格子第二排第三个⑥

**运镜**：中远景，从沙虫侧面看榴弹飞来
**打光**：侧逆光，榴弹红光照亮沙虫身躯局部
**引导**：榴弹即将命中——沙虫身躯占据画面左侧，榴弹从右侧飞来即将抵达→衔接到⑦命中爆炸
**主体**：沙虫 [图片 (4)] 身躯占据画面左侧，环形段状纹理清晰可见。榴弹从画面右侧飞来，红色光尾拖后，即将命中沙虫身躯中段。命中前1帧
**背景虚化**：中景深

### 正面提示词

Medium-wide shot from the sandworm's side, watching the projectile approach, medium depth of field. The sandworm's body filling the left side of the frame, ring-segment texture clearly visible. A glowing projectile with trailing red tail approaching from the right, about to hit the sandworm's midsection. The projectile's red glow illuminating a portion of the sandworm's body. Warm amber (5000K) side-backlight with red projectile glow on sandworm, PBR rendering, cinematic tension, motion blur on projectile, one frame before impact.

### 音频描写

- 榴弹逼近破空声（急速增强）
- 沙虫低频蠕动声

---

## SHOT 07 | 命中火球+烟柱 | 8-10s

参考分镜图：9宫格格子第三排第一个⑦

**运镜**：中景，爆炸正面
**打光**：火球橙红光作为主光源照亮全画面，黑暗被瞬间驱散
**引导**：命中！——橙红火球在沙虫身躯上爆开，黑色烟柱升腾→衔接到⑧冲击波
**主体**：榴弹命中沙虫身躯中段——巨大橙红火球在命中点爆开占据画面中心1/3，黑色浓烟柱向上升腾。沙虫 [图片 (4)] 身躯在火球两侧被炸裂外翻，环形体节断开
**背景虚化**：中浅景深，火球最清晰

### 正面提示词

Medium shot of the explosion head-on, medium-shallow depth of field. Direct hit — a massive orange-red fireball erupting at the impact point on the sandworm's midsection, occupying one-third of the frame center, thick black smoke column rising upward. The sandworm's body blown apart and peeled outward on both sides of the fireball, ring segments severed. The fireball's orange-red glow as the primary light source illuminating the entire frame, darkness instantly dispelled. PBR rendering, cinematic explosion, volumetric fire and smoke, motion blur on debris.

### 音频描写

- 榴弹命中爆炸巨响（低频冲击+高频碎裂）
- 沙虫被炸裂的嘶鸣声
- 火球燃烧轰鸣声
- 碎片飞溅声

---

## SHOT 08 | 冲击波沙尘横扫 | 10-11s

参考分镜图：9宫格格子第三排第二个⑧

**运镜**：中远景，与马车同高侧面
**打光**：冲击波扬起沙尘遮蔽光线，画面整体暗化，只有沙尘边缘金色光
**引导**：冲击波从命中点向四周横扫——大量沙尘如海啸从画面左侧扑向右侧马车→衔接到⑨沙虫哀嚎
**主体**：冲击波扬起巨量沙尘横扫画面——沙尘墙从画面左侧向右席卷如沙暴海啸。远处火球仍在燃烧。画面右侧马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 被冲击波推晃，棕色马嘶鸣，木板嘎吱
**背景虚化**：中浅景深

### 正面提示词

Medium-wide shot from the wagon's side at the same height, medium-shallow depth of field. Shockwave sweeping massive sand dust across the frame — a wall of sand surging from left to right like a sandstorm tsunami. Distant fireball still burning. The wagon on the right side being shoved and rocked by the blast, brown horse rearing and neighing, wooden planks creaking. Sand dust obscuring most light, only gold rim light on the dust wall's edge, overall darkened frame. Warm amber (5000K) heavily diffused by sand, PBR rendering, cinematic impact, motion blur on dust wall.

### 音频描写

- 冲击波低频轰鸣声（海啸般席卷）
- 沙尘墙呼啸声
- 马车被推晃木板嘎吱声
- 棕色马嘶鸣声

---

## SHOT 09 | 沙虫哀嚎+马车推晃 | 11-12s

参考分镜图：9宫格格子第三排第三个⑨

**运镜**：中景，马车侧面偏后方
**打光**：沙尘稍散，金色侧逆光重新照亮，远处火球残焰映红沙尘
**引导**：沙虫受伤后仰哀嚎——马车在前方被冲击波推晃但未翻→衔接P3沙虫反击
**主体**：沙虫 [图片 (4)] 身躯扭曲后仰哀嚎，受伤中段冒烟。画面前方马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 被冲击波推晃侧倾但正落回四轮，棕色马挣扎稳住。车尾窗口奥梵 [奥梵 三视图] 持弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 撑住车厢板
**背景虚化**：中景深

### 正面提示词

Medium shot from the wagon's side and slightly behind, medium depth of field. The sandworm's body twisted backward howling, smoke rising from the wounded midsection. The wagon ahead rocking from the shockwave but landing back on its four wheels, brown horse struggling to stabilize. At the rear window, a girl figure holding the mounted weapon bracing against the carriage wall. Sand dust settling slightly, golden side-backlight (5000K) re-emerging, distant fireball residual flames casting red glow on the dust. PBR rendering, cinematic aftermath, motion blur on settling dust.

### 音频描写

- 沙虫扭曲哀嚎嘶鸣声（痛苦，中频）
- 马车落回四轮沉重撞击声
- 棕色马挣扎蹄声
- 远处火球残焰燃烧声
- 奥梵撑住车厢板的摩擦声

---

## 全局约束

PBR物理渲染，全局光照，次表面散射（皮肤），哑光金属材质（武器），粗麻布纹理（车厢），体积光，8K超高清，电影级调色（暖金加冷蓝对比），轻微胶片颗粒感。角色外貌全程一致。9个SHOT后期剪辑拼接为一镜到底长镜头。弩炮始终指向画面深处或窗口方向，绝不指向镜头。每个SHOT只做一个动作，前景最多一个角色加一个元素，角色位置每SHOT锚定。榴弹无参考图，英文prompt中以红色信号灯闪烁的弹药描述。马车向右行驶，扬尘和场景模糊凸显速度感。
