---
name: mcu-debug
description: MCU 项目调试助手，自动分析编译错误并提供修复方案。当用户发送 "fix"、"修复"、"build"、"编译" 或任何 MCU 编译命令时触发，适用于嵌入式开发、Arduino、ESP32、STM32、SF32 (SiFli) 等 MCU 项目的编译问题诊断和修复。
---

# MCU Debug

## Overview

MCU Debug Skill 帮助开发者快速诊断和修复 MCU 项目的编译错误。

**核心能力：**
1. **自动触发** - 编译失败时自动诊断（无需手动输入 fix）
2. **智能识别** - 识别编译命令并监控执行结果
3. **即时修复** - 编译失败后立即分析并提供修复方案
4. **深度诊断** - 复杂问题进入 Plan 模式制定详细修复计划

---

## 🎯 触发条件

### 触发词（关键词匹配）

| 类型 | 关键词 |
|------|--------|
| **手动诊断** | `fix`, `修复`, `debug`, `调试` |
| **编译命令** | `build`, `编译`, `make`, `pio run`, `idf.py build` |
| | `scons`, `cmake`, `arduino-cli compile` |
| **编译相关** | `编译项目`, `构建`, `烧录`, `上传` |

### 自动触发逻辑

```
用户输入包含编译命令？
    ├── 是 → 执行编译 → 成功？ → 是 → ✅ 完成
    │                      └── 否 → 🔍 自动诊断
    └── 否 → 用户输入 fix/修复？
              ├── 是 → 🔍 执行诊断
              └── 否 → 忽略
```

---

## 🔄 工作流程

### 场景 1: 用户执行编译（自动诊断）

```
用户: "编译一下"
    ↓
识别为编译意图
    ↓
检测构建系统 → 执行编译
    ↓
编译成功？
    ├── 是 → ✅ 提示编译成功
    └── 否 → 🔍 立即自动诊断（无需等待用户输入 fix）
                ↓
            分析错误类型
                ├── 简单错误 → 直接修复 → 重新编译验证
                └── 复杂错误 → 进入 Plan 模式 → 制定修复计划
```

### 场景 2: 用户手动请求诊断

```
用户: "fix" 或 "修复"
    ↓
检测是否有最近的编译失败记录
    ├── 有 → 基于记录进行诊断
    └── 无 → 询问用户执行编译或手动分析
```

### 场景 3: 用户执行具体编译命令

```
用户: "pio run" 或 "make"
    ↓
直接执行命令并监控结果
    ↓
失败时立即诊断
```

---

## 📝 执行步骤

### Step 1: 识别用户意图

**判断输入类型：**
- 类型 A: 明确诊断请求 (`fix`, `修复`)
- 类型 B: 编译命令 (`make`, `pio run`, `idf.py build` 等)
- 类型 C: 编译意图 (`编译`, `build`, `构建`)

**编译关键词库：**
```python
COMPILE_TRIGGERS = [
    # 通用编译
    'build', 'compile', 'make', '编译', '构建',
    # PlatformIO
    'pio run', 'pio build', 'platformio',
    # ESP-IDF
    'idf.py build', 'idf build',
    # SiFli/SCons
    'scons', 'scons-build',
    # CMake
    'cmake', 'cmake build',
    # Arduino
    'arduino-cli compile', 'arduino compile',
    # 其他
    'upload', 'flash', '烧录', '上传',
]
```

### Step 2: 执行编译（如果是编译请求）

**流程：**
1. 检测项目构建系统
2. 构建编译命令（如用户未指定）
3. 使用 Bash 工具执行编译
4. 捕获 exit code 和输出
5. 判断是否编译成功

**编译成功标准：**
```python
# exit code == 0 且输出不包含 "error"
success = (return_code == 0) and ('error:' not in stderr.lower())
```

### Step 3: 编译失败 → 自动诊断

**立即执行诊断流程：**
1. 分析编译输出中的错误信息
2. 分类错误类型（语法/链接/配置等）
3. 生成修复建议
4. 判断是否可以自动修复
5. 执行修复或进入 Plan 模式

**诊断输出格式：**
```
❌ 编译失败 - 发现 3 个错误

📋 错误分析:
┌─────────────────────────────────────────┐
│ 1. [简单] main.c:45                     │
│    错误: 'GPIO_NUM_25' undeclared      │
│    建议: 添加 #include "driver/gpio.h"  │
├─────────────────────────────────────────┤
│ 2. [复杂] main.c:52                     │
│    错误: undefined reference to 'xxx'  │
│    建议: 需要链接库文件                  │
└─────────────────────────────────────────┘

💡 修复方案:
- 简单错误: 可自动修复（2个）
- 复杂错误: 需要手动处理（1个）

是否自动修复简单错误？[Y/n]
```

### Step 4: 修复策略

#### 简单错误（自动修复）

**可自动修复的错误：**
- 头文件缺失 → 添加正确的 `#include`
- 未声明标识符 → 添加常见宏头文件
- 缺少分号 → 在正确位置添加 `;`
- 简单拼写错误 → 修正拼写

**自动修复流程：**
```
读取错误文件
    ↓
定位错误行
    ↓
应用修复（Edit 工具）
    ↓
标记已修复
    ↓
重新编译验证
```

#### 复杂错误（Plan 模式）

**需要 Plan 模式的错误：**
- 链接错误（undefined reference）
- 内存溢出（section overflow）
- 框架配置错误
- 架构相关问题

**Plan 模式流程：**
```
收集错误上下文
    ↓
阅读相关源文件
    ↓
分析依赖关系
    ↓
使用 EnterPlanMode
    ↓
制定详细修复计划
    ↓
用户确认后执行
```

---

## 🛠️ 构建系统检测

### 自动检测逻辑

```python
def detect_build_system(project_path):
    if exists('platformio.ini'):
        return 'platformio', 'pio run'

    if exists('sdkconfig') or (exists('CMakeLists.txt') and exists('main/')):
        return 'espidf', 'idf.py build'

    if exists('SConstruct'):
        return 'scons', detect_scons_command()

    if exists('Makefile'):
        return 'make', 'make'

    if exists('CMakeLists.txt'):
        return 'cmake', 'mkdir -p build && cd build && cmake .. && make'

    if glob('*.ino'):
        return 'arduino', 'arduino-cli compile --fqbn esp32:esp32:esp32 .'

    return 'unknown', None
```

### 支持的构建系统

| 构建系统 | 检测标志 | 默认命令 |
|---------|---------|---------|
| PlatformIO | `platformio.ini` | `pio run` |
| ESP-IDF | `sdkconfig`, `main/` | `idf.py build` |
| SiFli SDK | `SConstruct` | `scons --board=<board> -j8` |
| Make | `Makefile` | `make` |
| CMake | `CMakeLists.txt` | `cmake ... && make` |
| Arduino | `*.ino` | `arduino-cli compile ...` |

---

## 📊 错误分类与处理

### 错误类型映射

| 错误模式 | 类型 | 复杂度 | 处理方式 |
|---------|------|--------|---------|
| `expected ';'` | 语法 | 简单 | 自动修复 |
| `undeclared` | 语义 | 简单 | 自动修复 |
| `No such file` (头文件) | 预处理器 | 简单 | 自动修复 |
| `implicit declaration` | 语义 | 简单 | 自动修复 |
| `undefined reference` | 链接器 | 复杂 | Plan 模式 |
| `multiple definition` | 链接器 | 复杂 | Plan 模式 |
| `overflowed` | 架构 | 复杂 | Plan 模式 |
| `CONFIG_` 错误 | 框架 | 复杂 | Plan 模式 |

### 快速修复知识库

**常见头文件缺失：**
```python
HEADER_FIXES = {
    'GPIO_NUM_25': '#include "driver/gpio.h"',
    'vTaskDelay': '#include "freertos/task.h"',
    'printf': '#include <stdio.h>',
    'malloc': '#include <stdlib.h>',
    'memset': '#include <string.h>',
    'bf0_hal_gpio': '#include "bf0_hal_gpio.h"',
}
```

---

## 💬 交互示例

### 示例 1: 编译失败自动诊断

**用户：**
```
编译一下这个项目
```

**Claude：**
```
🔧 检测到 ESP32 + PlatformIO 项目
执行: pio run

... 编译输出 ...

❌ 编译失败 - 发现 2 个错误

📋 错误分析:
┌─────────────────────────────────────────┐
│ 1. [简单] main.c:45                     │
│    error: 'GPIO_NUM_25' undeclared     │
│    修复: 添加 #include "driver/gpio.h"  │
├─────────────────────────────────────────┤
│ 2. [简单] main.c:52                     │
│    error: implicit declaration of      │
│           function 'vTaskDelay'        │
│    修复: 添加 #include "freertos/task.h"│
└─────────────────────────────────────────┘

💡 发现 2 个简单错误，可以自动修复。

是否自动修复？[Y/n]
```

**用户：**
```
y
```

**Claude：**
```
✅ 已修复 main.c:45 - 添加 #include "driver/gpio.h"
✅ 已修复 main.c:52 - 添加 #include "freertos/task.h"

重新编译验证...

✅ 编译成功！
```

### 示例 2: 复杂错误进入 Plan 模式

**用户：**
```
make
```

**Claude：**
```
执行: make

... 编译输出 ...

❌ 编译失败 - 发现 1 个错误

📋 错误分析:
┌─────────────────────────────────────────┐
│ 1. [复杂] 链接错误                      │
│    undefined reference to 'vTaskDelay' │
└─────────────────────────────────────────┘

⚠️ 这是一个复杂错误，涉及链接配置。
需要进入 Plan 模式制定详细修复计划。

是否继续？[Y/n]
```

**用户：**
```
y
```

**Claude：**
```
🔍 正在收集上下文信息...
- 阅读 main.c
- 查看 CMakeLists.txt
- 分析链接配置

📋 诊断结果:
问题: 未链接 FreeRTOS 库
方案: 在 CMakeLists.txt 中添加 target_link_libraries

🔧 修复计划:
1. 修改 CMakeLists.txt 添加库链接
2. 重新编译验证

是否执行修复？[Y/n]
```

### 示例 3: 手动触发诊断

**用户：**
```
fix
```

**Claude：**
```
🔍 检查最近的编译记录...

发现最近的编译失败记录（2分钟前）:
- 项目: /Users/ian/project/esp32-demo
- 错误: 3个

是否基于该记录进行诊断？[Y/n]
```

---

## 📁 参考文档

- [错误模式参考](references/error_patterns.md) - 详细的错误模式和修复方案
- [构建系统参考](references/build_systems.md) - 各构建系统的详细说明

---

## 🚀 高级功能

### 外部脚本工具（可选）

如需在 Claude Code 外部使用诊断功能，可使用提供的 Python 脚本：

```bash
# 自动诊断脚本
python3 scripts/mcu-debug-auto.py -- pio run

# 监视模式
python3 scripts/mcu-debug-auto.py --watch -- make

# 安装构建钩子
python3 scripts/setup-hooks.py
```

详细说明见文档上方的外部工具章节。

---

## ⚡ 快速参考

| 你想做什么 | 输入 |
|-----------|------|
| 编译并自动诊断 | `build`, `编译`, `make`, `pio run` |
| 手动诊断 | `fix`, `修复` |
| 编译 ESP32 项目 | `idf.py build` |
| 编译 SiFli 项目 | `scons --board=xxx -j8` |
