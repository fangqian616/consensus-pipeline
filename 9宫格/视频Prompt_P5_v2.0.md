# SHOT A 视频Prompt P5：装填+追上（9个SHOT）

> 版本：v2.2 | 按v3.1实测通过格式重写 | 严格对应9宫格故事板的9个格子
> 每个SHOT独立生成1-2秒视频，后期剪辑拼接
> v2.2更新：①-⑥英文加no sandworm；⑦⑧⑨英文改the SAME single sandworm；马车空间关系加CRITICAL单沙虫声明；⑧构图改为莉雅驾马+沙虫笼罩+马车向远离镜头行进；⑨改为"镜头后方"；统一负面提示词加防多沙虫

---

## 统一场景提示词（所有SHOT共用）
电影奇幻风格，写实风格，电影级布光，PBR物理渲染，全局光照，高细节金属纹理，皮肤次表面散射，哑光金属材质，粗麻布纹理，Octane渲染，8k分辨率，杰作。黄昏荒地，暖金色（5000K）侧逆光，沙尘弥漫，高对比度，体积光，暖金冷蓝色彩对比。

## 统一负面提示词（所有SHOT共用）
变形，扭曲，鬼影，模糊，过曝，闪烁，突变，溶解，多余肢体，复制人，穿模，低质量，画面撕裂，抖动过度，3D渲染蜡像感，油腻，磨皮，卡通，水印，切镜感，叠化转场，淡入淡出，背景音乐，cat，feline，animal，multiple sandworms，extra sandworms，second sandworm

全程有音效，不要有背景音乐.

## 马车空间关系
整体布局如下 [把圈红的这个顶棚扩大一点，这是马车的棚，] ，其中沿前后轴线布局——最前方棕色马→莉雅 [莉雅 三视图]（面朝前赶马）→车厢→奥梵 [奥梵 三视图]（面朝后持弩炮 [[参考图1] 单独把这个魔法枪的三视图]]）。**CRITICAL: There is only ONE sandworm in the entire sequence. It is always the SAME single sandworm. SHOT 01-06: no sandworm visible. SHOT 07-09: the SAME single sandworm appearing from behind. Never a second sandworm.** 沙虫在马车后方追来——沙虫永远在马车尾部方向，绝不在马车前方。奥梵面朝车尾窗口向后瞄准沙虫，莉雅面朝车头向前赶马逃跑。沙虫逐格逼近：SHOT 01-06沙虫不在画面内，SHOT 07远处追来，SHOT 08逼近车尾，SHOT 09正后方。

### 参考图
| 角色 | 参考图 | 用法 |
|------|--------|------|
| 莉雅 | [莉雅 三视图] [莉亚表情2] | 出现时直接引用，不描述外貌 |
| 奥梵 | [奥梵 三视图] [奥梵 表情] | 出现时直接引用，不描述外貌 |
| 奥梵武器 | [[参考图1] 单独把这个魔法枪的三视图]] | 弩炮/魔法枪出现时直接引用 |
| 沙虫 | [图片 (4)] | 出现时直接引用 |
| 马车+马 | [把圈红的这个顶棚扩大一点，这是马车的棚，] | 出现马车时直接引用，同时作为空间位置参考 |

**⚠️ 注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。**

马车+马 [把圈红的这个顶棚扩大一点，这是马车的棚，]。注意，马车要向马匹行进的方向行动，通过扬尘和场景模糊来凸显其速度感。

接下来，你需要根据分镜表 @[全格约束 单张16:9横屏图片，3×3] 左上方标注序号，按照下面的提示词来生成连续的画面，通过运镜，根据镜头引导进行切镜和镜头间的内容补充，将每一个分镜连续到一起。

## SHOT 01 | 奥梵装填弹药 | 0-1.3s
参考分镜图：9宫格格子①

**运镜**：中近景，车尾窗口内，微幅跟手
**打光**：暖金色侧逆光从窗口射入，照亮双手和弩炮表面
**引导**：奥梵双手向弩炮装填爆震弹药，视线聚焦在装填动作上，弹药是视觉锚点→衔接到②弹体特写
**主体**：奥梵 [奥梵 三视图] 双手往弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 装填爆震弹药，蓝色弹体在双手间正在推入弹膛方向
**背景虚化**：浅景深，双手和弹药清晰，车厢内壁虚化

### 正面提示词
Medium close-up from inside the wagon rear window, slight camera follow on hands. A girl figure's hands loading blue spherical ammo with pulsing energy veins into the chamber of a mounted magical weapon, the blue round glowing between fingers being pushed toward the chamber. Warm amber 5000K side-backlight streaming through the window illuminating hands and weapon surface. Shallow depth of field, hands and ammo sharp, wagon interior walls blurred. No sandworm. PBR rendering, subsurface scattering, volumetric light, cinematic grading, 8K.

### 音频描写
金属弹药推入弹膛的咔嗒声，手指摩擦金属的细微声，马车行进中木板吱嘎声

---

## SHOT 02 | 蓝色弹体入膛 | 1.3-2.7s
参考分镜图：9宫格格子②

**运镜**：极近特写，弹膛区域，静止微幅颤动
**打光**：弹体自发光蓝色照亮手指和弹膛内壁，暖金环境光从后方渗入
**引导**：蓝色弹体推入弹膛，弹体表面能量纹路脉动是核心视觉，蓝色光与暖金环境光形成冷暖对比→衔接到③导能槽脉动
**主体**：蓝色弹体推入弹膛特写——弹体表面蓝色能量纹路如血管般脉动发出脉动蓝光，照亮弹膛内壁金属反射
**背景虚化**：极浅景深，只有弹体和弹膛口清晰

### 正面提示词
Extreme close-up of the weapon chamber area, minimal camera vibration. Blue spherical ammo with pulsing energy veins being pushed into the metal chamber, the ammo surface has vein-like blue energy lines pulsing rhythmically casting blue glow onto the chamber interior walls with metallic reflections. Warm amber ambient light seeping from behind creating cold-warm contrast. Extremely shallow depth of field, only the ammo and chamber opening sharp. No sandworm. PBR rendering, metallic texture, volumetric light, cinematic grading, 8K.

### 音频描写
弹体滑入弹膛的低沉金属摩擦声，能量脉动的嗡嗡低鸣

---

## SHOT 03 | 导能槽蓝光脉动 | 2.7-4s
参考分镜图：9宫格格子③

**运镜**：中近景，弩炮侧面，微幅横移
**打光**：导能槽蓝色脉动光是主光源，暖金环境光从远处渗入，冷暖交织
**引导**：弩炮导能槽蓝光随弹药入膛急速脉动，光线从弹膛沿导能槽向前传导→衔接到④奥梵回头
**主体**：弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 侧面，导能槽内蓝色光芒急速脉动，从弹膛位置沿槽道向前涌动如能量河流，弩炮金属表面反射蓝色光斑
**背景虚化**：中浅景深，弩炮和导能槽清晰，车尾虚化

### 正面提示词
Medium close-up of the weapon side profile, slight lateral camera movement. Blue energy pulsing rapidly along a glowing channel on the weapon side, energy flowing forward from the chamber position along the channel like an energy river, blue light spots reflecting on the metallic weapon surface. Warm amber ambient light from distance, cold-warm color interplay. Medium-shallow depth of field, weapon and channel sharp, wagon rear blurred. No sandworm. PBR rendering, metallic texture, subsurface scattering, volumetric light, cinematic grading, 8K.

### 音频描写
能量沿导能槽传导的升频嗡鸣声，弩炮金属框架轻微震颤声

---

## SHOT 04 | 奥梵回头 | 4-5.3s
参考分镜图：9宫格格子④

**运镜**：中景，车尾窗口外侧偏侧，跟转
**打光**：暖金色侧逆光，奥梵侧脸被金色轮廓光勾勒，身后沙尘弥漫
**引导**：奥梵一边瞄准后方一边回头，视线从弩炮方向转向莉雅方向→衔接到⑤过肩喊话
**主体**：奥梵 [奥梵 三视图] 半转身，一手握弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 瞄向车后方，表情紧张专注。沙虫仍在远处
**背景虚化**：中浅景深

### 正面提示词
Medium shot from outside the wagon rear window offset to the side, camera follows the turning motion. A girl figure half-turned, one hand gripping a magical weapon aiming backward, head turning toward the wagon front direction, tense focused expression. Warm amber 5000K side-backlight rim-lighting her profile, dust billowing behind. The sandworm is still far behind not yet in frame. Medium-shallow depth of field. PBR rendering, subsurface scattering, volumetric light, cinematic grading, 8K.

### 音频描写
衣物转动摩擦声，沙尘呼啸声，远处马蹄声

---

## SHOT 05 | 朝莉雅喊话过肩 | 5.3-6.7s
参考分镜图：9宫格格子⑤

**运镜**：过肩构图，奥梵肩部前景，朝车头方向拍，微幅前推
**打光**：暖金色侧光，奥梵肩部剪影在前景，远处莉雅和马车前部被金色光勾勒
**引导**：奥梵朝莉雅方向喊话，视线从前景奥梵穿过车厢向车头莉雅→衔接到⑥莉雅赶马
**主体**：过肩构图——前景奥梵 [奥梵 三视图] 肩部和部分侧脸（嘴型配合喊出「又来了！莉雅！做好迎击准备！」），透过车厢空间看到远处车头位置莉雅 [莉雅 三视图] 背影
**背景虚化**：中浅景深，前景肩部虚，莉雅相对清晰

### 正面提示词
Over-the-shoulder composition from a girl figure shoulder looking toward the wagon front, slight forward dolly. Foreground shoulder silhouette with partial side of face mouth open as if shouting a warning command, through the wagon interior space a girl figure back visible at the far front driving position. Warm amber side-light, foreground shoulder silhouette, distant figure rim-lit by golden light. No sandworm visible (camera faces forward away from the rear). Medium-shallow depth of field, foreground shoulder soft, distant figure relatively sharp. PBR rendering, volumetric light, cinematic grading, 8K.

### 音频描写
奥梵喊话声：「又来了！莉雅！做好迎击准备！」，车厢内回响，马车行进吱嘎声

---

## SHOT 06 | 莉雅赶马 | 6.7-8s
参考分镜图：9宫格格子⑥

**运镜**：中景，车头侧面，跟行
**打光**：暖金色侧逆光，沙尘弥漫中莉雅和棕色马被金色光勾勒轮廓
**引导**：莉雅在车头拼命赶马，沙尘弥漫强调紧迫感，马匹方向暗示逃跑→衔接到⑦沙虫远处逼近
**主体**：莉雅 [莉雅 三视图] 在车头位置赶马，棕色马全力奔跑，沙尘从马蹄下扬起弥漫画面，马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 前部可见
**背景虚化**：中浅景深，沙尘造成空气透视

### 正面提示词
Medium shot from the wagon front side, camera tracking alongside. A girl figure at the front driving position urging the brown horse forward, the horse at full gallop, dust billowing up from hooves filling the frame, the wagon front section visible. Warm amber 5000K side-backlight rim-lighting the figure and horse silhouette, dust-filled air creating atmospheric perspective. The wagon moves in the direction the horse is running, speed emphasized by dust trails and background motion blur. No sandworm (camera faces side-front, sandworm is behind the wagon out of frame). Medium-shallow depth of field. PBR rendering, volumetric light, cinematic grading, 8K.

### 音频描写
马蹄重踏沙地声，鞭绳挥动声，马匹嘶鸣，沙尘呼啸

---

## SHOT 07 | 沙虫远处逼近 | 8-9.3s
参考分镜图：9宫格格子⑦

**运镜**：远景，马车后方广角，微幅后拉
**打光**：暖金色侧逆光，沙虫暗色巨影从沙尘中显现
**引导**：沙虫巨口从远处快速逼近，视线从画面中心马车向后方远处沙虫滑去→衔接到⑧沙虫追到车尾
**主体**：远景中，马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 在画面前方向右逃跑，沙虫 [图片 (4)] 在马车后方远处从沙尘中快速逼近，环形巨口大张朝向车尾方向，身躯在沙尘中若隐若现。沙虫在马车后面追，不在前面
**背景虚化**：深景深全画面清晰

### 正面提示词
Wide shot from behind the wagon, wide-angle lens, slight camera pull-back. The wagon in the foreground fleeing to the right, the SAME single sandworm far behind on the LEFT pursuing, rapidly approaching through dust with its circular maw wide open facing toward the wagon's rear. The sandworm is BEHIND the wagon chasing it, NEVER in front. Warm amber 5000K side-backlight, the sandworm dark silhouette materializing from dust. Deep depth of field, entire frame sharp. The wagon moves forward with dust trails, speed emphasized by motion blur on background. PBR rendering, volumetric light, cinematic grading, 8K.

### 音频描写
远处沙虫的低沉咆哮，沙地被巨躯搅动的隆隆声，沙尘呼啸

---

## SHOT 08 | 沙虫追到车尾 | 9.3-10.7s
参考分镜图：9宫格格子⑧

**运镜**：中景，马车侧后方，马车向远离镜头方向行进，微幅上仰
**打光**：暖金色侧逆光被沙虫身躯遮蔽部分，沙虫带来阴影笼罩马车尾部
**引导**：沙虫追到车尾几节身体距离，危机极度升级，沙虫已近在咫尺→衔接到⑨奥梵瞄准扣扳机
**主体**：沙虫在马车后方，环形巨口从车尾方向逼近几乎可以触及车尾。车厢在沙虫阴影笼罩下莉雅驾马在镜头右方，为侧对镜头
**背景虚化**：中浅景深

### 正面提示词
Medium shot from the wagon side-rear, the wagon moving away from camera, slight upward tilt. The SAME single sandworm has closed to within a few body segments of the wagon tail coming from the LEFT/REAR, its circular maw wide open nearly touching the wagon rear from behind. The sandworm is BEHIND the wagon, NOT in front. The wagon body under the sandworm looming shadow from behind. A girl figure visible at the front driving the horse on the RIGHT side of frame facing sideways to camera. Warm amber side-backlight partially blocked by the sandworm body, shadow engulfing the wagon rear. The wagon moving away from camera with dust trails emphasizing speed. Medium-shallow depth of field. PBR rendering, volumetric light, cinematic grading, 8K.

### 音频描写
沙虫巨口张开的压迫性低频轰鸣，马车木板在震波中嘎吱作响，风声加剧

---

## SHOT 09 | 奥梵瞄准扣扳机 | 10.7-12s
参考分镜图：9宫格格子⑨

**运镜**：中近景，透过车尾窗口看奥梵，微幅推近
**打光**：暖金色侧逆光，奥梵面部被弩炮蓝色微光和暖金环境光双重照亮
**引导**：透过车尾窗口奥梵瞄准扣下扳机，动作定格在扣扳机瞬间→衔接P6爆震弹药射出
**主体**：透过车尾窗口看到奥梵 [奥梵 三视图] 瞄准镜头后方，弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 蓝色导能槽脉动达到最亮，手指扣下扳机瞬间
**背景虚化**：中浅景深

### 正面提示词
Medium close-up through the wagon rear window looking at a girl figure, slight dolly-in. The girl figure aiming the weapon backward toward camera (toward the SAME single sandworm behind the wagon), the weapon blue energy channel pulsing at peak brightness, finger pulling the trigger at the decisive moment. The sandworm is BEHIND the wagon in the direction she aims, NOT in front. Warm amber side-backlight, face illuminated by both the weapon blue glow and warm ambient light. Medium-shallow depth of field. PBR rendering, subsurface scattering, volumetric light, cinematic grading, 8K.

### 音频描写
弩炮充能达到峰值的尖锐升调，扳机扣下的金属咔嚓声，蓝色能量释放的爆鸣前兆

---

## 全局约束
PBR物理渲染，全局光照，次表面散射（皮肤），哑光金属材质（武器），粗麻布纹理（车厢），体积光，8K超高清，电影级调色（暖金加冷蓝对比），轻微胶片颗粒感。角色外貌全程一致。9个SHOT后期剪辑拼接为一镜到底长镜头。弩炮始终指向画面深处或窗口方向，绝不指向镜头。每个SHOT只做一个动作，前景最多一个角色加一个元素，角色位置每SHOT锚定。
