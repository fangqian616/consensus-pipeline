# SHOT C 视频Prompt P3：沙虫撞击（9个SHOT）

> 版本：v2.1 | 按v3.1实测通过格式重写 | 严格对应9宫格故事板的9个格子
> P3是P2沙虫被击伤后的愤怒反击
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

## SHOT 01 | 沙虫从烟尘愤怒冲出 | 0-1s

参考分镜图：9宫格格子第一排第一个①

**运镜**：中远景，马车后方视角
**打光**：侧逆光，爆炸烟尘橙红余光，沙虫轮廓光从烟尘中勾勒
**引导**：沙虫从爆炸烟尘中愤怒冲出——烟尘炸裂向四周，沙虫破烟而出→衔接到②沙虫身躯横砸
**主体**：沙虫 [图片 (4)] 从画面左侧爆炸烟尘中愤怒冲出——环形口器大张嘶吼，身躯破开黑烟如巨兽出笼。烟尘橙红余烬仍在画面左侧升腾
**背景虚化**：中浅景深

### 正面提示词

Medium-wide shot from behind the wagon's position, medium-shallow depth of field. The sandworm bursting out of explosion smoke and dust from the left — circular maw gaping wide roaring, body breaking through black smoke like a caged beast unleashed. Orange-red embers still rising from the smoke on the left. Side-backlight with orange-red glow from residual smoke, the sandworm's silhouette outlined by rim light emerging from the dust. Warm amber (5000K) side-backlight with residual fire glow, PBR rendering, cinematic emergence, motion blur on bursting smoke.

### 音频描写

- 沙虫破烟而出嘶吼声（愤怒，巨大）
- 烟尘炸裂向四周的沙沙声
- 余烬燃烧噼啪声

---

## SHOT 02 | 身躯如鞭横砸 | 1-2s

参考分镜图：9宫格格子第一排第二个②

**运镜**：中景，马车侧面，朝沙虫身躯横扫方向拍
**打光**：侧逆光，沙虫身躯弧线运动中轮廓光勾勒
**引导**：沙虫长身躯从左向右横扫砸向马车侧面——中段高拱尾段急速下砸→衔接到③同一段身躯继续横扫砸中马车
**主体**：沙虫 [图片 (4)] 长身躯从左向右水平弧线扫来——中段身躯高高拱起，尾段身急速向下甩出砸向右侧马车。身躯沿路拖起沙尘尾迹清晰可见
**背景虚化**：中浅景深，运动残影稍虚

### 正面提示词

Medium shot from the wagon's side, facing the sandworm's sweeping direction, medium-shallow depth of field. The sandworm's long body sweeping horizontally from left to right in a wide arc — mid-body arched high, tail segment swinging down toward the wagon on the right, dragging sand dust trails along the arc. Side-backlight outlining the horizontal sweep with rim light. Warm amber (5000K) side-backlight, PBR rendering, cinematic sweeping motion, motion blur on tail sweep.

### 音频描写

- 沙虫身躯横扫破风声（由蓄力到爆发）
- 沙尘被身躯搅起的呼啸声
- 木质马车远处嘎吱预警声

---

## SHOT 03 | 撞击马车侧面 | 2-3s

参考分镜图：9宫格格子第一排第三个③

**运镜**：中近景，撞击点侧面
**打光**：撞击瞬间沙尘爆起遮蔽光线，画面闪暗后散射光恢复
**引导**：②中横扫的同一段身躯继续运动砸中马车侧面——从左向右的横扫惯性带入撞击→衔接到④马车侧倾
**主体**：沙虫 [图片 (4)] 同一段身躯继续从左向右横扫砸中马车侧面——身躯仍在水平弧线运动中，撞击点木板碎裂，沙尘从接触点向四周爆起。马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 被撞向一侧，侧面木板可见凹陷变形
**背景虚化**：中浅景深

### 正面提示词

Medium-close shot from the impact point's side, medium-shallow depth of field. The same body segment of the sandworm continuing its left-to-right horizontal sweep and slamming into the wagon's side — the body still in horizontal arc motion, wood cracking at impact point, sand dust bursting from contact outward, wagon pushed sideways with visible dent deformation on the side planks. Impact momentary darkness as dust obscures light, then scattered light returns. Warm amber (5000K) light disrupted by impact dust, PBR rendering, cinematic impact, motion blur on debris.

### 音频描写

- 沙虫撞击马车侧面沉闷巨响
- 木板碎裂声（尖锐）
- 沙尘爆起声
- 棕色马惊恐嘶鸣声

---

## SHOT 04 | 马车剧烈侧倾 | 3-4s

参考分镜图：9宫格格子第二排第一个④

**运镜**：中景，马车侧面
**打光**：沙尘中散射光，马车在阴影中侧倾
**引导**：撞击力传导——马车剧烈侧倾，右侧车轮几乎离地→衔接到⑤莉雅险被甩出
**主体**：马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 剧烈侧倾向左，右侧车轮几乎离地——木板嘎吱作响，车厢板变形可见。棕色马四蹄挣扎维持。车厢内货物滑动
**背景虚化**：中浅景深

### 正面提示词

Medium shot from the wagon's side, medium-shallow depth of field. The wagon tilting violently to the left, right wheels nearly lifting off the ground — wooden planks creaking, carriage wall deformation visible. Brown horse struggling to keep footing with all four hooves. Cargo sliding inside the carriage. Scattered light through dust, wagon shadowed in the tilt. Warm amber (5000K) diffused by dust, PBR rendering, cinematic tilt, motion blur on tilting wagon.

### 音频描写

- 马车侧倾木板剧烈嘎吱声
- 车轮离地摩擦声
- 货物在车厢内滑动碰撞声
- 棕色马四蹄挣扎声

---

## SHOT 05 | 莉雅差点被甩出 | 4-5s

参考分镜图：9宫格格子第二排第二个⑤

**运镜**：近景，车头侧面
**打光**：侧逆光，莉雅轮廓光，沙尘微粒在光中飞舞
**引导**：马车侧倾→莉雅在车头差点被甩出——一只手抓缰绳一只手撑车沿→衔接到⑥龙尾拍板
**主体**：莉雅 [莉雅 三视图] 在车头差点被甩出——身体向左倾出车沿半悬空，一只手死死抓住缰绳，另一只手撑住车沿木板。表情惊险 [莉亚表情2]。棕色马在下方嘶鸣
**背景虚化**：浅景深，莉雅最清晰

### 正面提示词

Close-up from the wagon front's side, shallow depth of field with a girl figure sharpest. A girl figure with a long dragon tail extending from her lower back nearly thrown off the wagon front — body tilting out over the edge half-suspended, one hand gripping reins desperately, the other hand bracing against the wagon edge board. Brown horse below neighing. Side-backlight with rim light on the figure, sand dust particles dancing in the light. Warm amber (5000K) side-backlight, PBR rendering, cinematic danger moment, motion blur on dust particles.

### 音频描写

- 莉雅惊呼声（短促）
- 缰绳拉紧皮革摩擦声
- 手撑木板撞击声
- 棕色马嘶鸣声

---

## SHOT 06 | 龙尾拍板维持平衡 | 5-6s

参考分镜图：9宫格格子第二排第三个⑥

**运镜**：近景，车厢板上方
**打光**：侧光，龙尾拍击的动态光影
**引导**：莉雅身后长尾巴猛砸车厢木板借力稳住身体→衔接到⑦车内货物滑动
**主体**：莉雅 [莉雅 三视图] 身体后仰，身后长尾巴从腰部延伸而出猛然向下砸在车厢木板上——木板被砸出凹陷溅起沙尘。莉雅借反弹力将身体拉回车内，双手重新抓住缰绳
**背景虚化**：浅景深

### 正面提示词

Close-up from above the carriage floor, shallow depth of field. The girl figure with a long dragon tail extending from her lower back — she leans back, her long tail swinging down hard from behind her and smashing into the wooden carriage floor to regain balance, wood denting at impact point, sand dust splashing up from the hit. She uses the bounce-back force to pull herself back into the wagon, both hands regripping the reins. Side-light with dynamic shadow from the tail strike. Warm amber (5000K) side-light, PBR rendering, cinematic recovery motion, motion blur on tail impact.

### 音频描写

- 龙尾拍击木板沉闷打击声
- 木板凹陷嘎吱声
- 沙尘从拍击点溅起声
- 莉雅用力拉回身体的喘息声

---

## SHOT 07 | 货物滑动沙尘涌入 | 6-7s

参考分镜图：9宫格格子第三排第一个⑦

**运镜**：中近景，车厢内部
**打光**：车内昏暗，缝隙透入金色侧光光束，沙尘在光束中飞舞
**引导**：车厢内——货物因侧倾滑动碰撞，沙尘从缝隙喷入→衔接到⑧奥梵稳住
**主体**：车厢内部——货物和箱子因侧倾在车厢地板上向左滑动碰撞，沙尘从木板缝隙中喷入如金色雾气。弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 在支架上摇晃。画面深处奥梵 [奥梵 三视图] 扶住车厢板维持站立
**背景虚化**：中浅景深

### 正面提示词

Medium-close shot inside the carriage, medium-shallow depth of field. Cargo and crates sliding and colliding on the carriage floor due to the tilt, sand dust spraying in through the wooden plank gaps like golden mist. The mounted weapon swaying on its mount. In the background, a girl figure with cat-ear hair bracing against the carriage wall staying upright. Interior dim, golden side-light beams slanting through gaps, dust particles flying in the light beams. Warm amber (5000K) side-light through gaps, PBR rendering, cinematic interior chaos, motion blur on sliding cargo.

### 音频描写

- 货物在地板上滑动碰撞声（多声源）
- 沙尘从缝隙喷入嘶嘶声
- 弩炮在支架上摇晃金属碰撞声
- 木板嘎吱声

---

## SHOT 08 | 奥梵撑住弩炮支架 | 7-7.5s

参考分镜图：9宫格格子第三排第二个⑧

**运镜**：中近景，车厢后方
**打光**：侧光，奥梵轮廓光，沙尘在光中弥漫
**引导**：奥梵撑住弩炮支架稳住身体——在颠簸中维持战斗姿态→衔接到⑨马车勉强前行
**主体**：奥梵 [奥梵 三视图] 在车厢后方单手撑住弩炮 [[参考图1] 单独把这个魔法枪的三视图]] 支架稳住身体，另一只手扶住车厢板。面朝车尾窗口方向保持警惕。车厢仍在轻微晃动
**背景虚化**：中浅景深

### 正面提示词

Medium-close shot at the carriage rear, medium-shallow depth of field. A girl figure with cat-ear hair bracing against the weapon mount with one hand to steady herself, the other hand gripping the carriage wall. Facing the rear window direction maintaining combat vigilance. The carriage still swaying slightly. Side-light with rim light on the figure, sand dust弥漫 in the light. Warm amber (5000K) side-light, PBR rendering, cinematic stabilization, motion blur on slight carriage sway.

### 音频描写

- 奥梵撑住支架金属摩擦声
- 车厢轻微晃动木板声
- 奥梵平稳呼吸声

---

## SHOT 09 | 马车勉强继续前行 | 7.5-8s

参考分镜图：9宫格格子第三排第三个⑨

**运镜**：中远景，马车侧面
**打光**：沙尘弥漫中散射光，金色侧逆光微弱穿透沙尘
**引导**：沙尘弥漫中马车勉强继续前行——危机暂缓但未解→衔接P4假喘息
**主体**：沙尘弥漫全画面如金色雾海——马车 [把圈红的这个顶棚扩大一点，这是马车的棚，] 在沙尘中勉强继续向右前行，车身仍有残余晃动。棕色马低头奋力拉车。车头莉雅 [莉雅 三视图] 抓住缰绳重新坐稳。车尾窗口奥梵 [奥梵 三视图] 剪影面朝后方
**背景虚化**：中景深

### 正面提示词

Medium-wide shot from the wagon's side, medium depth of field. Thick golden dust haze filling the entire frame — the wagon barely continuing forward through the sand dust, residual sway still visible. Brown horse pulling hard with head down. At the wagon front, a girl figure with a long dragon tail gripping reins seated again. At the rear window, a girl figure with cat-ear hair silhouette facing backward. Golden side-backlight (5000K) weakly penetrating the dust, scattered diffused light. PBR rendering, cinematic aftermath, motion blur on dust and wagon.

### 音频描写

- 沙尘弥漫低频环境音
- 棕色马奋力拉车喘息声
- 马车轮轴吱嘎声
- 远处沙虫低频嘶嘶声（微弱，暗示仍在）

---

## 全局约束

PBR物理渲染，全局光照，次表面散射（皮肤），哑光金属材质（武器），粗麻布纹理（车厢），体积光，8K超高清，电影级调色（暖金加冷蓝对比），轻微胶片颗粒感。角色外貌全程一致。9个SHOT后期剪辑拼接为一镜到底长镜头。弩炮始终指向画面深处或窗口方向，绝不指向镜头。每个SHOT只做一个动作，前景最多一个角色加一个元素，角色位置每SHOT锚定。马车向右行驶，扬尘和场景模糊凸显速度感。
