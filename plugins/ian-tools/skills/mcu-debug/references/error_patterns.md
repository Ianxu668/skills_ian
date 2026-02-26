# MCU 编译错误模式参考

## 语法错误 (Syntax Errors)

### 缺少分号
```
error: expected ';' before 'return'
error: expected ';' at end of declaration
```
**修复**: 在指定位置添加分号

### 括号不匹配
```
error: expected ')' before ';' token
error: expected '}' at end of input
error: too few arguments to function 'xxx'
```
**修复**: 检查并匹配括号

### 关键字拼写错误
```
error: unknown type name 'unt32_t'; did you mean 'uint32_t'?
error: implicit declaration of function 'prntf' [-Wimplicit-function-declaration]
```
**修复**: 修正拼写错误

---

## 预处理器错误 (Preprocessor Errors)

### 头文件缺失
```
fatal error: stdio.h: No such file or directory
error: 'driver/gpio.h' file not found
```
**修复**:
- 添加正确的头文件包含路径
- 安装缺失的 SDK/库

### 宏未定义
```
error: 'GPIO_NUM_25' undeclared (first use in this function)
error: 'CONFIG_WIFI_SSID' undeclared
```
**修复**:
- 添加头文件包含
- 在 sdkconfig/menuconfig 中启用配置
- 定义缺失的宏

### 头文件保护问题
```
error: redefinition of 'struct xxx'
error: redefinition of typedef 'yyy'
```
**修复**: 添加头文件保护宏
```c
#ifndef HEADER_NAME_H
#define HEADER_NAME_H
// ... 内容
#endif
```

---

## 语义错误 (Semantic Errors)

### 变量未声明
```
error: 'variable' undeclared (first use in this function)
error: use of undeclared identifier 'xxx'
```
**修复**: 声明变量或添加正确的头文件

### 函数未声明
```
error: implicit declaration of function 'function_name' [-Wimplicit-function-declaration]
error: conflicting types for 'function_name'
```
**修复**:
- 添加函数原型声明
- 包含正确的头文件

### 类型不匹配
```
error: passing argument 1 of 'xxx' makes pointer from integer without a cast
error: incompatible types when assigning to type 'xxx' from type 'yyy'
error: cannot convert 'xxx' to 'yyy' in initialization
```
**修复**: 添加类型转换或修正变量类型

---

## 链接错误 (Linker Errors) ⚠️ 复杂错误

### 未定义引用
```
undefined reference to `function_name'
undefined reference to `vTaskDelay'
undefined reference to `gpio_set_level'
```
**原因**: 缺少库文件或对象文件
**修复**:
- 添加库到链接器参数（-lxxx）
- 添加库搜索路径（-L/path）
- 检查源文件是否被编译

### 多重定义
```
multiple definition of `variable_name'
multiple definition of `function_name'
```
**原因**: 全局变量/函数在头文件中定义而非声明
**修复**:
- 头文件中使用 `extern` 声明
- 在一个源文件中定义

### 库文件缺失
```
cannot find -lxxx
cannot open linker script file: xxx.ld
```
**修复**: 安装缺失的库或修正库路径

---

## 架构相关错误 (Architecture Errors) ⚠️ 复杂错误

### 内存问题
```
error: variable 'buffer' exceeds maximum size
error: section '.text' will not fit in region 'iram0_0_seg'
error: region 'dram0_0_seg' overflowed by xxx bytes
```
**修复**:
- 优化内存使用
- 调整分区表
- 使用外部内存

### 中断问题
```
error: undefined reference to `__vector_default'
error: interrupt handler 'xxx' not defined
```
**修复**: 检查中断向量表配置

### 启动文件问题
```
error: undefined reference to `_start'
error: undefined reference to `_sbrk'
```
**修复**: 检查链接脚本和启动文件

---

## 框架配置错误 (Framework Errors) ⚠️ 复杂错误

### ESP-IDF 配置错误
```
error: Please run idf.py menuconfig to configure the project
error: CONFIG_xxx must be defined
error: sdkconfig.h: No such file or directory
```
**修复**:
- 运行 `idf.py menuconfig`
- 运行 `idf.py reconfigure`

### PlatformIO 配置错误
```
Error: Unknown board ID 'xxx'
Error: Could not find 'platform.json'
```
**修复**: 检查 platformio.ini 配置

### Arduino 框架错误
```
Error: Board definition not found
Error: Core 'arduino' not found
```
**修复**: 安装相应的 board package

---

## 警告 (Warnings)

### 未使用变量/函数
```
warning: unused variable 'xxx' [-Wunused-variable]
warning: defined but not used 'xxx' [-Wunused-function]
```
**处理**: 根据情况删除或使用

### 隐式类型转换
```
warning: implicit conversion from 'xxx' to 'yyy' changes value
warning: comparison between signed and unsigned
```
**修复**: 显式类型转换

### 指针类型不匹配
```
warning: assignment discards 'const' qualifier
warning: passing argument 1 of 'xxx' from incompatible pointer type
```
**修复**: 修正指针类型

---

## SF32 / SiFli SDK 特定错误

### 开发板名称错误
```
Error: No such board: sf32lb52-xxx
Error: board_name not specified
```
**修复**: 使用正确的板子名称，查看 `sdk/boards/` 目录

### SCons 构建错误
```
scons: *** [build_xxx] Error 2
scons: *** No SConstruct file found
```
**修复**: 确保在项目根目录运行，检查 SConstruct 文件存在

### 双核编译问题
```
error: undefined reference to `ipc_queue_init'
error: undefined reference to `mailbox_init'
```
**修复**: 需要同时编译 HCPU 和 LCPU 并正确链接

### SiFli HAL 错误
```
error: 'bf0_hal_xxx' undeclared
error: 'HAL_XXX' undeclared
```
**修复**: 包含正确的 HAL 头文件，如 `#include "bf0_hal_gpio.h"`

### 外设配置错误
```
error: EPIC clock not configured
error: LCDC initialization failed
```
**修复**: 检查 RCC 时钟配置和外设初始化代码

---

## 快速判断表

| 错误模式 | 类型 | 复杂度 |
|---------|------|-------|
| expected ';' | 语法 | 简单 |
| undeclared | 语义 | 简单 |
| No such file (头文件) | 预处理器 | 简单 |
| undefined reference | 链接器 | 复杂 |
| multiple definition | 链接器 | 复杂 |
| overflowed | 架构 | 复杂 |
| CONFIG_ 错误 | 框架 | 复杂 |
| section will not fit | 架构 | 复杂 |
| No such board | 框架 (SF32) | 复杂 |
| SCons error | 构建系统 | 复杂 |
| bf0_hal_xxx | 框架 (SF32) | 中等 |
