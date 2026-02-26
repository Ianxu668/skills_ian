# Ian CC Plugin

个人 Claude Code 插件市场，收录实用的开发辅助技能。

## 安装

在 Claude Code 中执行：

```bash
# 1. 添加 marketplace
/plugin marketplace add ~/ian-cc-plugin

# 2. 安装插件
/plugin install ian-tools@ian-plugins
```

## 使用

安装成功后，通过 `插件名:技能名` 调用：

```
/ian-tools:smart-hardware-research 智能药盒
/ian-tools:mcu-debug
```

## 收录技能

| 技能 | 调用命令 | 描述 |
|------|--------|------|
| **smart-hardware-research** | `/ian-tools:smart-hardware-research` | 智能硬件产品用户调研分析专家。通过网络搜索和数据分析，深入挖掘用户对智能硬件产品的需求、痛点和讨论热点。 |
| **mcu-debug** | `/ian-tools:mcu-debug` | MCU 项目调试助手，自动分析编译错误并提供修复方案。支持 Arduino、ESP32、STM32、SiFli (SF32) 等平台。 |

## 开发资源

- [创建插件](https://code.claude.com/docs/zh-CN/plugins)
- [创建市场](https://code.claude.com/docs/zh-CN/plugin-marketplaces)
- [技能开发指南](https://code.claude.com/docs/zh-CN/skills)

---

**作者：** Ian Xu