# Ian 插件先用起来 + Marketplace 教程

## 本工程结构

本仓库是一个本地插件市场工程，核心结构如下：

```text
ian-cc-plugin/
├── .claude-plugin/
│   └── marketplace.json                # 市场配置（市场名、插件列表、插件路径）
├── plugins/
│   └── ian-plugins/
│       ├── .claude-plugin/
│       │   └── plugin.json             # 插件配置（插件名、版本、描述）
│       └── skills/
│           ├── ian-smart-hardware-research/
│           │   └── SKILL.md            # Skill 定义
│           ├── ian-competitive-analysis/
│           │   └── SKILL.md
│           ├── ian-competitive-single/
│           │   └── SKILL.md
│           └── ian-hardware-technical-analysis/
│               └── SKILL.md
└── README.md
```

配置关系说明：
- `.claude-plugin/marketplace.json` 定义市场 `ian-plugins`，并声明插件来源 `./plugins/ian-plugins`
- `plugins/ian-plugins/.claude-plugin/plugin.json` 定义插件 `ian-plugins`
- `plugins/ian-plugins/skills/*/SKILL.md` 是插件内可调用的 skills

## 先安装并使用当前仓库插件

当前仓库的配置为：
- marketplace 名称：`ian-plugins`
- plugin 名称：`ian-plugins`
- 已包含 skills：`ian-smart-hardware-research`、`ian-competitive-analysis`、`ian-competitive-single`、`ian-hardware-technical-analysis`

### 1. 安装

在 Claude Code 中执行：

```bash
/plugin marketplace add ~/ian-cc-plugin
/plugin install ian-plugins@ian-plugins
```

### 2. 使用

安装后可直接调用：

```text
/ian-plugins:ian-smart-hardware-research   # 智能硬件调研
/ian-plugins:ian-competitive-analysis      # 竞争分析
/ian-plugins:ian-competitive-single       # 单品竞品调研报告
/ian-plugins:ian-hardware-technical-analysis  # 硬件技术分析
```

## Marketplace 教程（分开写）

下面将两个不同场景拆分为两个独立教程：
- 教程 A：一个插件包含两个 skills（整体安装）
- 教程 B：两个 skills 分别做成两个插件（可单独安装）

## 教程 A：一个插件包含两个 Skills

适用场景：希望用户安装一次插件后直接获得两个 skills。

### 1. 目录结构

```text
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── my-plugin/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            ├── skill-one/
            │   └── SKILL.md
            └── skill-two/
                └── SKILL.md
```

### 2. marketplace.json

文件路径：`my-marketplace/.claude-plugin/marketplace.json`

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Your Name" },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "包含两个 skills 的插件"
    }
  ]
}
```

### 3. plugin.json

文件路径：`my-marketplace/plugins/my-plugin/.claude-plugin/plugin.json`

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "包含两个 skills 的插件"
}
```

### 4. 安装命令

```bash
/plugin marketplace add ./my-marketplace
/plugin install my-plugin@my-marketplace
```

说明：该安装方式会把 `my-plugin` 下的全部组件一起安装（包含两个 skills）。

## 教程 B：每个 Skill 一个独立插件

适用场景：希望用户可以按需单独安装 `skill-one` 或 `skill-two`。

### 1. 目录结构

```text
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    ├── skill-one/
    │   ├── .claude-plugin/
    │   │   └── plugin.json
    │   └── skills/
    │       └── skill-one/
    │           └── SKILL.md
    └── skill-two/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            └── skill-two/
                └── SKILL.md
```

### 2. marketplace.json

文件路径：`my-marketplace/.claude-plugin/marketplace.json`

```json
{
  "name": "your-marketplace",
  "owner": { "name": "Your Name" },
  "plugins": [
    {
      "name": "skill-one",
      "source": "./plugins/skill-one"
    },
    {
      "name": "skill-two",
      "source": "./plugins/skill-two"
    }
  ]
}
```

### 3. 各插件的 plugin.json

`skill-one` 的 `plugin.json` 示例：

```json
{
  "name": "skill-one",
  "version": "1.0.0",
  "description": "Skill One plugin"
}
```

`skill-two` 的 `plugin.json` 示例：

```json
{
  "name": "skill-two",
  "version": "1.0.0",
  "description": "Skill Two plugin"
}
```

### 4. 安装命令

```bash
/plugin marketplace add ./my-marketplace
/plugin install skill-one@your-marketplace
/plugin install skill-two@your-marketplace
```

说明：Claude Code 当前是按插件安装。将每个 skill 拆成独立插件后，用户才能单独安装。

## 参考文档

- [创建插件市场](/zh-CN/plugin-marketplaces)
- [插件参考](/zh-CN/plugins-reference)
- [插件开发](/zh-CN/plugins)
