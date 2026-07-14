# SHOT A 视频Prompt P1车外：追逐长镜头（9个SHOT）

> 版本：v3.1 | ★实测通过格式 | 严格对应9宫格故事板v2.0的9个格子
> 车外9拍长镜头，车内喊话另建文件
> 每个SHOT独立生成1-2秒视频，后期剪辑拼接为长镜头

---

## 统一场景提示词（所有SHOT共用）

电影奇幻风格，写实风格，电影级布光，PBR物理渲染，全局光照，高细节金属纹理，皮肤次表面散射，哑光金属材质，粗麻布纹理，Octane渲染，8k分辨率，杰作。黄昏荒地，暖金色（5000K）侧逆光，沙尘弥漫，高对比度，体积光，暖金冷蓝色彩对比。

## 统一负面提示词（所有SHOT共用）

变形，扭曲，鬼影，模糊，过曝，闪烁，突变，溶解，多余肢体，复制人，穿模，低质量，画面撕裂，抖动过度，3D渲染蜡像感，油腻，磨皮，卡通，水印，切镜感，叠化转场，淡入淡出，背景音乐，cat，feline，animal

全程有音效，不要有背景音乐.

## 马车空间关系

整体布局如下 [把圈红的这个顶棚扩大一点，这是马车的棚，] ，其中沿前后轴线布局，从最前端到最后端依次为：棕色马匹在最前方全力奔跑拉行整个车辆，四蹄完全伸展；紧挨马匹之后是车头开放站位，莉雅 [莉雅 三视图] 站在那里面朝前方双手握着缰绳赶马，她的背部朝向车厢方向；莉雅 [莉雅 三视图] 身后是木板结构的中间车厢，车厢内散放着货物和弩炮弹药，木板墙壁上有缝隙让沙尘涌入，车厢尾部有一面带窗口的后墙；奥梵 [奥梵 三视图] 坐在车尾窗口内侧，背对马车行进方向面朝后方，透过窗口持着奥术弩炮 [[参考图1] 单独把这个魔法枪的三视图] 瞄准马车后方的追击者。

整辆车上四者的位置永远保持这个前后顺序：马在最前，莉雅在马后面朝前，车厢在中间，奥梵在最后面朝后。莉雅和奥梵面朝相反方向，莉雅朝车头前方赶马，奥梵朝车尾后方迎敌。

### 参考图

| 角色 | 参考图 | 用法 |
|------|--------|------|
| 莉雅 | [莉雅 三视图] [莉亚表情2] | 出现时直接引用，不描述外貌 |
| 奥梵 | [奥梵 三视图] [奥梵 表情]，武器[[参考图1] 单独把这个魔法枪的三视图] | 出现时直接引用，不描述外貌 |
| 沙虫 | [图片 (4)] | 出现时直接引用 |
| 马车+马 | [把圈红的这个顶棚扩大一点，这是马车的棚，] | 出现时直接引用，同时作为空间位置参考 |

**⚠️ 注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。**

马车+马 [把圈红的这个顶棚扩大一点，这是马车的棚，]。注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。

接下来，你需要根据分镜表 @[全格约束 单张16:9横屏图片，3×3] 左上方标注序号，按照下面的提示词来生成连续的画面，通过运镜，根据镜头引导进行切镜和镜头间的内容补充，将每一个分镜连续到一起。

## SHOT 01 | 破土特写 | 0-2s

参考分镜图：9宫格格子第一排第一个①

**运镜**：极近特写，浅景深，手持轻微晃动
**打光**：逆光剪影，巨口边缘金色轮廓光
**引导**：沙虫巨口从沙面向上爆裂，爆心即视线锚点，飞溅沙粒从爆心向四周辐射
**主体**：沙虫 [图片 (4)] 巨口从沙面爆裂而出占据全画面。环形三排尖齿大张，口腔深处暗红，沙粒从口器四周飞溅。马车尚不在画面内
**背景虚化**：浅景深，只有巨口清晰

### 正面提示词

Extreme close-up, shallow depth of field, handheld camera with slight shake. The sandworm's enormous circular maw bursts upward from the desert floor, filling the entire frame. Three rows of sharp teeth gaping wide, deep dark red interior of the throat visible, sand particles radiating outward from the explosion point. The maw faces slightly upper-right, backlit silhouette with gold rim light on the teeth edges. No wagon visible in frame. Warm amber backlight (5000K), volumetric dust particles, PBR rendering, cinematic grading.

### 音频描写

- 沙虫破土爆裂声（巨大，沙粒飞溅感）
- 地面震动低频轰鸣

---

## SHOT 02 | 后拉揭示体量 | 2-3s

参考分镜图：9宫格格子第一排第二个②

**运镜**：中近景急速后拉，景深渐深，手持晃动
**打光**：侧逆光，沙虫身躯轮廓光勾勒每节分段
**引导**：沙虫身躯对角线走向（左上到右下），镜头沿身躯后拉
**主体**：镜头急速后拉，沙虫 [图片 (4)] 巨口退到画面左上，黄褐色环形段状身体一节一节从沙中涌出向右下延伸，身躯占满画面左半侧。马车尚不在画面内
**背景虚化**：景深比SHOT 01深，身躯纹理开始清晰

### 正面提示词

Rapid pull-back shot, medium-close to medium, handheld camera shake. The sandworm's maw recedes to upper-left of frame as the camera pulls back rapidly — yellow-brown segmented body section by section rising from the sand, extending diagonally from upper-left to lower-right, filling the left half of the frame. Each body segment has visible ring-pattern texture, outlined by warm amber rim light (5000K). No wagon visible yet. Volumetric dust, deepening depth of field, PBR rendering, cinematic grading, motion blur on camera pull-back.

### 音频描写

- 沙虫身躯涌动低频震动声（由弱到强）
- 沙粒持续崩落声

---

## SHOT 03 | 远景体量对比 | 3-5s

参考分镜图：9宫格格子第一排第三个③

**运镜**：远景，深景深，手持轻微晃动，继续后拉至最远
**打光**：全景侧逆光，沙虫暗色巨影，马车金色轮廓光
**引导**：沙虫占满左侧三分之二，追击方向在右侧留白，视线自然从左巨影滑向右方发现马车
**主体**：继续后拉至远景。沙虫 [图片 (4)] 巨大身躯占据画面左侧三分之二如移动山丘，画面右侧远处马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 渺小如玩具。体量对比极强烈
**背景虚化**：深景深全画面清晰

### 正面提示词

Wide shot, deep depth of field, continued pull-back to maximum distance, slight handheld shake. The sandworm's enormous body fills the left two-thirds of the frame like a moving hill, dark silhouette against golden backlight. Far right of frame, the horse-drawn wagon appears tiny by comparison — gold rim light on the wagon, brown horse galloping, dust trail behind. Massive scale contrast between the sandworm and the wagon. Warm amber (5000K) side-backlight, volumetric dust, golden hour desert, PBR rendering, cinematic grading, 27mm lens.

### 音频描写

- 沙虫持续涌动低频轰鸣
- 马匹远处奔跑蹄声（远场，微弱）

---

## SHOT 04 | 侧移追踪 | 5-7s

参考分镜图：9宫格格子第二排第一个④

**运镜**：中远景，马车右侧平视跟拍，手持晃动，浅景深
**打光**：侧光，沙虫身躯纹理可见，马车轮廓光
**引导**：沙虫从左向右追，马车向右逃，两者并行同向运动，沙虫更快
**主体**：马车右侧跟拍。沙虫 [图片 (4)] 从画面左侧向右猛追，画面右侧马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 拼命逃窜，棕色马全力冲刺。两者并行但沙虫更快
**背景虚化**：中浅景深

### 正面提示词

Medium-wide shot, lateral tracking from the wagon's right side, handheld camera shake, medium-shallow depth of field. The sandworm surges rightward in pursuit from the left of frame, the wagon racing ahead on the right with brown horse at full gallop. Both moving in the same direction but the sandworm is faster, gaining ground. Warm amber (5000K) side-backlight, volumetric dust, motion blur on fast elements, PBR rendering, cinematic chase intensity.

### 音频描写

- 马蹄声（近场，节奏急促）
- 沙虫破风声（左侧，低频压迫）
- 风沙呼啸声

---

## SHOT 05 | 逼近 | 7-8s

参考分镜图：9宫格格子第二排第二个⑤

**运镜**：中景，马车右侧平视，距离缩短，手持晃动，浅景深
**打光**：侧逆光，沙虫逼近带来的阴影开始笼罩马车
**引导**：沙虫加速逼近，画面中沙虫占比急速膨胀从左侧向右挤压马车空间
**主体**：距离急速缩短。沙虫 [图片 (4)] 身躯填满画面左侧，马车变大 [把圈红的这个顶棚扩大一点，这是马车的棚，] 可辨识棕色马和木板车厢，车尾窗口奥梵 [奥梵 三视图] 剪影面朝后方持弩炮 [[参考图1] 单独把这个魔法枪的三视图] 。沙虫环形口器在画面左侧边缘张开
**背景虚化**：中浅景深

### 正面提示词

Medium shot, same side tracking from the wagon's right but much closer, handheld camera shake, medium-shallow depth of field. The sandworm's body fills the left side of frame, expanding rapidly — its circular maw gaping at the left edge. The wagon has grown larger and recognizable: brown horse, wooden carriage body, at the rear window a girl figure silhouette facing backward holding a mounted weapon, faint blue glow. The sandworm's shadow begins to fall over the wagon. Warm amber (5000K) light with sandworm casting dark shadow, volumetric dust, PBR rendering, cinematic chase intensity, motion blur.

### 音频描写

- 沙虫逼近低频声增强
- 马蹄声更急促
- 木质车厢受压嘎吱声

---

## SHOT 06 | 车尾后方视角 | 8-10s

参考分镜图：9宫格格子第二排第三个⑥

**运镜**：中景，马车正后方偏侧上方朝车头方向拍，手持晃动，浅景深
**打光**：前景沙虫暗色剪影，马车金色轮廓光，逆光中沙尘弥漫
**引导**：前景沙虫巨大头和身躯占画面左三分之一，视线穿过沙虫朝向马车
**主体**：从马车正后方偏侧看。前景沙虫 [图片 (4)] 巨大身躯和头部占据画面左三分之一，远处马车在画面右侧拼命逃窜。车尾窗口可见车尾窗口奥梵 [奥梵 三视图] 剪影面朝后方持弩炮 [[参考图1] 单独把这个魔法枪的三视图] ，表情严肃 [奥梵 表情] 。沙虫环形口器在前景左侧微张
**背景虚化**：中浅景深

### 正面提示词

Medium shot from behind the wagon and slightly above, looking forward past the sandworm toward the wagon, handheld camera shake, medium-shallow depth of field. The sandworm's massive head and body occupy the left foreground third of frame — its circular maw slightly open, dark silhouette against golden backlight. The wagon is far ahead on the right, gold rim light, at the rear window a girl figure silhouette visible holding a weapon. Volumetric dust between them, warm amber (5000K) backlight, PBR rendering, cinematic chase, motion blur on dust.

### 音频描写

- 沙虫低频压迫声（极近，前景）
- 马车远处疾驰声
- 沙尘摩擦声

---

## SHOT 07 | 沙浪掀起 | 10-12s

参考分镜图：9宫格格子第三排第一个⑦

**运镜**：中景，马车侧方，手持晃动，浅景深
**打光**：沙浪遮蔽大部分光线，画面整体暗化，只有沙浪边缘金色光和马车微弱轮廓光
**引导**：沙虫身躯侧摆掀起沙浪从左向右扑向马车，力的传导方向等于视线流向
**主体**：沙虫 [图片 (4)] 身躯侧摆掀起巨大沙浪，沙墙如海啸般从画面左侧扑向右侧马车方向，遮天蔽日。沙虫身躯在画面左侧可见。马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 在沙浪前方拼命逃避
**背景虚化**：中浅景深

### 正面提示词

Medium shot from the wagon's side, handheld camera shake, medium-shallow depth of field. The sandworm whips its body sideways, kicking up an enormous wave of sand like a tsunami surging from left toward the wagon on the right, blocking out the sky. The sandworm's body visible on the left. The wagon ahead of the sand wave trying to outrun it, brown horse at full gallop. The sand wave darkens most of the frame — only gold rim light on the sand wave's edge and faint wagon silhouette. Warm amber (5000K) heavily diffused by sand, PBR rendering, cinematic intensity, motion blur on sand wave.

### 音频描写

- 沙虫身躯侧摆破风声
- 沙浪掀起轰鸣声（海啸般，由远到近）
- 风沙呼啸骤然增强

---

## SHOT 08 | 撞击侧倾 | 12-13s

参考分镜图：9宫格格子第三排第二个⑧

**运镜**：中近景，马车侧面近，手持晃动，浅景深
**打光**：沙尘中散射光，马车被沙浪阴影笼罩
**引导**：沙浪从左侧拍击马车，左侧沙浪残影仍在画面中
**主体**：沙浪击中马车侧面，马车剧烈侧倾右侧车轮几乎离地。木板嘎吱，货物从车厢飞出。棕色马嘶鸣挣扎。车尾窗口奥梵 [奥梵 三视图] 撑住车厢板稳住身体，车头马车驾驶员 [莉雅 三视图] 低下头想要躲避。沙浪碎裂沙粒弥漫全画面
**背景虚化**：中浅景深

### 正面提示词

Medium-close shot from the wagon's side, very close, handheld camera shake, medium-shallow depth of field. The sand wave slams into the wagon's side — the wagon tilts violently, right wheels nearly lifting off ground. Wooden planks creaking, cargo flying out of the carriage. The brown horse neighs and struggles. At the rear window, a girl figure braces against the wall to stay steady. Shattered sand particles fill the entire frame. Scattered light through dust, wagon shadowed by the sand wave aftermath, warm amber (5000K) diffused, PBR rendering, cinematic impact, motion blur on flying debris.

### 音频描写

- 沙浪撞击马车侧面沉闷巨响
- 马车侧倾木板剧烈嘎吱声和货物碰撞声
- 棕色马嘶鸣声

---

## SHOT 09 | 惊险稳住 | 13-14.5s

参考分镜图：9宫格格子右下方⑨

**运镜**：中景，马车侧面稍远，手持晃动后趋于稳定，中景深
**打光**：沙尘稍散，金色侧逆光重新照亮马车轮廓，沙虫暗影投在马车上方
**引导**：马车勉强稳住但沙虫仍在车后方紧追，沙虫环形口器从马车后方右侧出现阴影笼罩马车，危机未解
**主体**：马车勉强落回四轮，剧烈颠簸但未翻。棕色马重新找到节奏继续狂奔。画面右侧沙虫 [图片 (4)] 仍在车后方紧追，环形口器更近了已经咬到车尾。危机未解
**背景虚化**：中景深

### 正面提示词

Medium shot from the wagon's side, slightly further back, handheld camera settling from shake, medium depth of field. The wagon barely lands back on all four wheels with a heavy jolt but doesn't overturn. The brown horse finds its stride again and keeps galloping desperately. On the right side of frame, the sandworm still pursuing close behind the wagon — its circular maw even closer, right at the wagon's tail. The sandworm's dark shadow falls over the wagon from above. Golden side-backlight (5000K) re-emerging as dust settles slightly, PBR rendering, cinematic tension, motion blur on horse and wheels.

### 音频描写

- 马车落回四轮沉重撞击声
- 棕色马蹄声恢复节奏
- 沙虫逼近嘶嘶声（极近，后方）

---

## 全局约束

PBR物理渲染，全局光照，次表面散射（皮肤），哑光金属材质（武器），粗麻布纹理（车厢），体积光，8K超高清，电影级调色（暖金加冷蓝对比），轻微胶片颗粒感。角色外貌全程一致。9个SHOT后期剪辑拼接为一镜到底长镜头。弩炮始终指向画面深处或窗口方向，绝不指向镜头。每个SHOT只做一个动作，前景最多一个角色加一个元素，角色位置每SHOT锚定。本文件仅车外镜头，车内另建。
