# 🎨 创建自定义预设

Consensus Pipeline 的核心是"预设"——定义了参与部门、辩手风格、视觉指令等所有配置。

本文档教你如何创建自己的预设。

## 预设的数据结构

```json
{
  "name": "预设名称",
  "description": "预设描述",
  "departments": {
    "部门ID": {
      "zh_name": "中文名",
      "en_name": "English Name",
      "debaters": {
        "A": {
          "zh_name": "辩手中文名",
          "en_name": "English Name",
          "zh_style": "中文风格描述（核心！决定辩手的观点和产出）",
          "en_style": "English style description"
        },
        "B": { ... },
        "C": { ... }
      }
    }
  },
  "visual_directive": {
    "zh": "视觉指令（可选，注入到所有辩手提示词头部）",
    "en": "Visual directive (optional)"
  },
  "cross_debates": [
    {"side_a": "部门A的ID", "side_b": "部门B的ID"}
  ],
  "debate_rounds": 2,
  "negative_prompts": "默认负面提示词"
}
```

## 示例：产品宣传视频预设

```json
{
  "name": "产品宣传视频",
  "description": "适合电商/科技产品宣传片，聚焦卖点展示和用户痛点",
  "departments": {
    "market": {
      "zh_name": "市场部",
      "en_name": "Marketing",
      "debaters": {
        "A": {
          "zh_name": "卖点提炼派",
          "en_name": "Selling Point",
          "zh_style": "你专注从产品参数中提炼最打动用户的卖点...",
          "en_style": "..."
        },
        "B": {
          "zh_name": "痛点共鸣派",
          "en_name": "Pain Point",
          "zh_style": "你专注用户使用场景中的痛点...",
          "en_style": "..."
        }
      }
    },
    "creative": {
      "zh_name": "创意部",
      "en_name": "Creative",
      "debaters": {
        "A": {
          "zh_name": "故事驱动派",
          "en_name": "Story-Driven",
          "zh_style": "你相信好广告就是一个好故事...",
          "en_style": "..."
        },
        "B": {
          "zh_name": "视觉冲击派",
          "en_name": "Visual Impact",
          "zh_style": "你相信3秒定生死...",
          "en_style": "..."
        }
      }
    },
    "dp": {
      "zh_name": "摄影部",
      "en_name": "Cinematography",
      "debaters": {
        "A": { "zh_name": "产品质感派", ... },
        "B": { "zh_name": "场景氛围派", ... }
      }
    },
    "editing": {
      "zh_name": "剪辑部",
      "en_name": "Editing",
      "debaters": {
        "A": { "zh_name": "快节奏派", ... },
        "B": { "zh_name": "叙事节奏派", ... }
      }
    }
  },
  "cross_debates": [
    {"side_a": "market", "side_b": "creative"},
    {"side_a": "dp", "side_b": "editing"}
  ],
  "debate_rounds": 2,
  "negative_prompts": "low quality, blurry, watermark, text overlay"
}
```

## 提示词编写技巧

### 辩手风格描述（zh_style / en_style）是核心

好的风格描述应该：
1. **明确立场** — 这个辩手信什么？看重什么？
2. **限定职责** — 只做什么，不做什么
3. **给出产出锚点** — 产出必须包含哪些要素
4. **制造冲突** — 同部门的辩手之间要有观点差异

### 反面示例
> ❌ "你是一个专业的分镜师" — 太笼统，没有立场

### 正面示例
> ✅ "你专注长镜头的叙事力——你相信一个不切断的镜头比十个快切更有沉浸感。你做三件事：第一，标注哪些时刻必须用长镜头（情绪流动/空间建立/动作连贯）；第二，为每个长镜头设计起幅落幅和内部运动；第三，质疑每一个快切的必要性——'这个切真的比不切更好吗？'"

## 提交你的预设

创建好的预设欢迎提交PR：
1. Fork本仓库
2. 在 `presets/` 目录下添加你的JSON文件
3. 提交Pull Request

我们会审核提示词质量后合并。
