# SHOT A 视频Prompt P11：余韵🫁最慢（9个SHOT）

> 版本：v2.0 | 按v3.1实测通过格式重写 | 严格对应9宫格故事板的9个格子
> 每个SHOT独立生成1-2秒视频，后期剪辑拼接

---

## 统一场景提示词（所有SHOT共用）
电影奇幻风格，写实风格，电影级布光，PBR物理渲染，全局光照，高细节金属纹理，皮肤次表面散射，哑光金属材质，粗麻布纹理，Octane渲染，8k分辨率，杰作。黄昏荒地，暖金色（5000K）侧逆光，沙尘弥漫，高对比度，体积光，暖金冷蓝色彩对比。

## 统一负面提示词（所有SHOT共用）
变形，扭曲，鬼影，模糊，过曝，闪烁，突变，溶解，多余肢体，复制人，穿模，低质量，画面撕裂，抖动过度，3D渲染蜡像感，油腻，磨皮，卡通，水印，切镜感，叠化转场，淡入淡出，背景音乐，爆炸，激烈动作，快速运动，cat，feline，animal

全程有音效，不要有背景音乐.

## 空间关系
P11无马车无马。地面场景，战斗结束。莉雅在画面中央偏右前方落地。远处散落金属沙虫碎块。鸵鸟站在一旁。奥梵在莉雅附近。最后几拍奥梵和鸵鸟面对面。两人+鸵鸟全程地面站位。

### 参考图

| 角色 | 参考图 | 用法 |
|------|--------|------|
| 莉雅 | [莉雅 三视图] [莉亚表情2] | 出现时直接引用，不描述外貌 |
| 奥梵 | [奥梵 三视图] [奥梵 表情] | 出现时直接引用，不描述外貌 |
| 奥梵武器 | [[参考图1] 单独把这个魔法枪的三视图] | 奥梵持武器时引用 |
| 鸵鸟乔纳森 | ⚠️无参考图 | 英文提示词中必须描述外观 |

接下来，你需要根据分镜表 @[全格约束 单张16:9横屏图片，3×3] 左上方标注序号，按照下面的提示词来生成连续的画面，通过运镜，根据镜头引导进行切镜和镜头间的内容补充，将每一个分镜连续到一起。

## SHOT 01 | 莉雅落地跪稳 | 0-1.5s
参考分镜图：9宫格格子①

**运镜**：中景，侧面低角度，缓慢推近
**打光**：暖金色侧逆光，沙尘缓缓飘落如金色雪花，光线柔和平静
**引导**：莉雅双脚着地单膝跪稳——从上方落地的惯性缓冲，尘埃缓落营造战后平静感
**主体**：莉雅 [莉雅 三视图] 双脚着地单膝跪稳姿态，一只手撑地，另一只手自然垂落。周围沙尘如金色雪花缓缓飘落。安静、疲惫但安全
**背景虚化**：中浅景深，莉雅清晰，飘落沙尘有虚化层次

### 正面提示词
Medium shot low angle side view, slow push-in, a girl figure landing on both feet and settling into a one-knee kneel, one hand on the ground, the other hand hanging naturally at her side, golden sand dust drifting down slowly like snowflakes around her, warm amber (5000K) side-backlight, soft and peaceful light, quiet exhausted but safe atmosphere, medium shallow depth of field with defocused dust layers, cinematic fantasy style, realistic, PBR rendering, global illumination, subsurface scattering skin, 8K resolution

### 音频描写
双脚着地的轻柔落地声，单膝跪地时沙土的轻微压缩声，沙尘缓缓飘落的沙沙声，微弱的风声

---

## SHOT 02 | 碎块散落 | 1.5-3s
参考分镜图：9宫格格子②

**运镜**：远景，深景深，缓慢横摇
**打光**：暖金色侧逆光，金属碎块在光线下反光，整体画面温暖安静
**引导**：远处金属沙虫碎块散落一地——战后全貌展示
**主体**：远处金属沙虫碎块散落一地——铜色金属外壳碎片、齿轮零件、红色宝石碎屑，在暖金色夕阳下反射微光。地面有弹坑和锥体残余。莉雅 [莉雅 三视图] 在画面右侧近处渺小
**背景虚化**：深景深全画面清晰

### 正面提示词
Wide shot deep depth of field, slow pan, scattered metal sandworm debris across the distant ground — copper-colored metal exoskeleton fragments, gear parts, red gemstone shards reflecting faint light in the warm sunset, crater marks and cone remnants on ground, a girl figure tiny on the right foreground, warm amber (5000K) side-backlight, metal debris reflecting soft golden glints, overall warm and quiet atmosphere, deep depth of field entire frame sharp, cinematic fantasy style, realistic, PBR rendering, global illumination, 8K resolution

### 音频描写
远处偶尔有金属碎片落地的微弱叮当声，风轻轻吹过碎块间的沙沙声，安静的环境底噪

---

## SHOT 03 | 鸵鸟从容 | 3-5s
参考分镜图：9宫格格子③

**运镜**：中景，固定机位
**打光**：暖金色侧光，鸵鸟被柔光照亮，礼帽在光线下投下小小阴影
**引导**：鸵鸟站在一旁，礼帽歪斜，神态从容——与周围毁灭场景形成反差
**主体**：鸵鸟站在画面中——戴着歪斜的礼帽，脚踝红色宝石脚环在夕阳下微光闪烁，神态从容淡定，如同刚完成一件微不足道的事。羽毛在暖金色光中柔和
**背景虚化**：中浅景深

### 正面提示词
Medium shot, static camera, an ostrich wearing a slightly tilted top hat standing calmly in the scene, red gemstone anklets on its legs glinting softly in the sunset, demeanor composed and unbothered as if it just did something trivial, feathers soft in warm golden light, warm amber (5000K) side light, the ostrich lit gently with the top hat casting a small shadow, contrast with the destruction scattered around, medium shallow depth of field, cinematic fantasy style, realistic, PBR rendering, global illumination, 8K resolution

### 音频描写
鸵鸟站定时羽毛轻微抖动的沙沙声，脚踝宝石极微弱的光芒嗡鸣，远处风声，安静而从容的环境音

---

## SHOT 04 | 奥梵看向鸵鸟 | 5-6.5s
参考分镜图：9宫格格子④

**运镜**：中近景，奥梵视角方向，缓慢跟移
**打光**：暖金色侧光照亮奥梵面部，背景鸵鸟在焦点外
**引导**：奥梵转头看向鸵鸟——视线方向引导观众也看向鸵鸟
**主体**：奥梵 [奥梵 三视图] 转头看向鸵鸟方向，目光中带着疑惑和好奇。背景中鸵鸟的虚化轮廓可见
**背景虚化**：中浅景深，奥梵清晰，鸵鸟虚化

### 正面提示词
Medium close-up, a boy figure's viewpoint direction, slow tracking, a boy figure turning his head to look toward the ostrich direction, eyes filled with curiosity and puzzlement, blurred silhouette of an ostrich wearing a slightly tilted top hat visible in the background out of focus, warm amber (5000K) side light illuminating the boy figure's face, medium shallow depth of field with the boy figure sharp and the ostrich soft, cinematic fantasy style, realistic, PBR rendering, subsurface scattering skin, 8K resolution

### 音频描写
奥梵转头时衣物的轻微摩擦声，呼吸声，远处鸵鸟偶尔的轻微脚步声

---

## SHOT 05 | 疑惑犹豫 | 6.5-8s
参考分镜图：9宫格格子⑤

**运镜**：近景，奥梵面部，缓慢推近
**打光**：暖金色柔光，面部微妙的犹豫表情被光线细腻呈现
**引导**：奥梵表情疑惑犹豫——内心挣扎是否开口，微表情是焦点
**主体**：奥梵 [奥梵 三视图][奥梵 表情] 面部近景，表情疑惑犹豫——眉头微皱，嘴唇似张似合，目光在鸵鸟和地面之间游移，想问又迟疑
**背景虚化**：浅景深，只有面部清晰

### 正面提示词
Close-up on a boy figure's face, slow push-in, expression of hesitation and doubt — brows slightly furrowed, lips between opening and closing, gaze shifting between the ostrich and the ground, wanting to ask but hesitating, warm amber soft light delicately rendering subtle facial micro-expressions, shallow depth of field only the face in focus, cinematic fantasy style, realistic, PBR rendering, subsurface scattering skin, 8K resolution

### 音频描写
微弱的呼吸声，嘴唇似张似合的极轻声，犹豫时衣物的轻微摩擦，安静的环境底噪

---

## SHOT 06 | 开口询问 | 8-9.5s
参考分镜图：9宫格格子⑥

**运镜**：中景，奥梵和鸵鸟同框，固定机位
**打光**：暖金色柔光，两人一鸟被均匀照亮
**引导**：奥梵终于开口询问——他面向鸵鸟，鸵鸟转向他，对话关系建立
**主体**：奥梵 [奥梵 三视图] 面向鸵鸟开口询问，身体微微前倾，表情中带着好奇和试探。鸵鸟面向奥梵，歪头似乎在听。两人一鸟在暖金色夕阳中形成宁静画面
**背景虚化**：中景深

### 正面提示词
Medium shot with both in frame, static camera, a boy figure turning toward an ostrich wearing a slightly tilted top hat with red gemstone anklets and speaking, body slightly leaning forward with curiosity and tentative questioning, the ostrich facing the boy figure tilting its head as if listening, warm golden (5000K) sunset light evenly illuminating both, peaceful scene in golden hour desert, medium depth of field, cinematic fantasy style, realistic, PBR rendering, global illumination, 8K resolution

### 音频描写
奥梵开口询问的极轻人声，鸵鸟歪头时羽毛轻微抖动声，暖金色夕阳下安静的环境音

---

## SHOT 07 | 鸵鸟闭眼回忆 | 9.5-10.5s
参考分镜图：9宫格格子⑦

**运镜**：中近景，鸵鸟，固定机位
**打光**：暖金色柔光，鸵鸟闭眼时面部被柔光照亮，安静如肖像
**引导**：鸵鸟闭眼像陷入短暂回忆——静默开始，画面节奏进一步放慢
**主体**：鸵鸟闭眼，像是陷入短暂的回忆，礼帽歪斜，姿态沉静。画面极其安静，连沙尘都缓缓静止
**背景虚化**：中浅景深

### 正面提示词
Medium close-up of an ostrich, static camera, an ostrich wearing a slightly tilted top hat with red gemstone anklets on its legs, eyes closed as if lost in brief reminiscence, posture serene and still like a portrait, extremely quiet scene, even the sand dust settling to stillness, warm amber (5000K) soft light gently illuminating the closed-eye face like a portrait painting, medium shallow depth of field, cinematic fantasy style, realistic, PBR rendering, 8K resolution, meditative and calm atmosphere

### 音频描写
极轻的沙尘落定声，鸵鸟闭眼时的轻微呼吸，空气几乎完全静止，远处微弱的风声

---

## SHOT 08 | 沉默 | 10.5-11s
参考分镜图：9宫格格子⑧

**运镜**：中景，奥梵和鸵鸟，固定机位
**打光**：暖金色柔光几乎无变化，画面时间仿佛凝固
**引导**：1-2秒沉默——画面中什么都没发生，只有沙尘缓缓飘落，时间被拉长
**主体**：奥梵 [奥梵 三视图] 和鸵鸟对视，但双方都沉默不语。画面中几乎没有动作，只有沙尘缓缓飘落，暖金色光线静静照亮一切。空气中充满期待
**背景虚化**：中景深

### 正面提示词
Medium shot, static camera, a boy figure and an ostrich wearing a slightly tilted top hat facing each other in complete silence, almost no movement at all, only sand dust slowly drifting down, warm golden light quietly illuminating everything without change, air filled with anticipation, time seemingly frozen, medium depth of field, cinematic fantasy style, realistic, PBR rendering, 8K resolution, extremely slow and meditative pace, the quietest moment of the entire film

### 音频描写
1-2秒近乎完全沉默，只有极微弱的沙尘飘落声，呼吸声极轻，时间凝固般的寂静

---

## SHOT 09 | "乔纳森" 🫁呼吸点3 | 11-12s
参考分镜图：9宫格格子⑨

**运镜**：中近景，鸵鸟，固定机位
**打光**：暖金色柔光，鸵鸟睁眼时光线微微变化如呼吸
**引导**：鸵鸟平静回答"乔纳森"——名字在沉静中落下的重量感，画面最后2秒以上完全静默
**主体**：鸵鸟睁开眼，平静地回答"乔纳森"——神态安详如讲述一个久远的名字。礼帽歪斜，脚踝红色宝石脚环在夕阳下微微闪光。画面在名字落地后持续2秒以上完全静默——只有沙尘、夕阳、和这个名字
**背景虚化**：中浅景深

### 正面提示词
Medium close-up of an ostrich, static camera, an ostrich wearing a slightly tilted top hat with red gemstone anklets on its legs, eyes opening, calmly responding as if speaking a name from long ago — Jonathan — expression peaceful and unhurried, the top hat slightly tilted, red gemstone anklets softly glinting in sunset, warm amber (5000K) soft light, the light subtly shifting as the ostrich opens its eyes like a breath, after the name falls the frame holds in complete silence for 2+ seconds — only sand dust, sunset, and the name, medium shallow depth of field, cinematic fantasy style, realistic, PBR rendering, 8K resolution, the most meditative and quiet ending possible

### 音频描写
鸵鸟睁眼的极细微声，平静说出"乔纳森"的轻柔声音，然后2秒以上完全静默——只有微弱的夕阳风声和沙尘落定

---

## 全局约束
PBR物理渲染，全局光照，次表面散射（皮肤），哑光金属材质（武器），粗麻布纹理（车厢），体积光，8K超高清，电影级调色（暖金加冷蓝对比），轻微胶片颗粒感。角色外貌全程一致。9个SHOT后期剪辑拼接为一镜到底长镜头。每个SHOT只做一个动作，前景最多一个角色加一个元素，角色位置每SHOT锚定。
