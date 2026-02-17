# MCU 构建系统参考

## PlatformIO

### 识别标志
- `platformio.ini` 文件

### 常用命令
```bash
# 编译项目
pio run

# 编译特定环境
pio run -e esp32dev

# 清理并重新编译
pio run -t clean
pio run

# 上传固件
pio run -t upload

# 查看串口输出
pio device monitor
```

### 常见配置
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    xxx/yyy@^1.0.0
```

### 故障排除
- 环境未找到: 检查 `platformio.ini` 中的 `[env:xxx]` 定义
- 库依赖问题: 使用 `pio lib install` 安装依赖

---

## ESP-IDF

### 识别标志
- `sdkconfig` 文件
- `CMakeLists.txt` 包含 project()
- `main/` 目录结构

### 常用命令
```bash
# 配置项目
idf.py menuconfig

# 编译项目
idf.py build

# 清除编译
idf.py fullclean

# 烧录固件
idf.py flash

# 查看串口输出
idf.py monitor

# 一次性编译烧录监控
idf.py flash monitor
```

### 项目结构
```
project/
├── CMakeLists.txt
├── sdkconfig
├── sdkconfig.defaults
├── main/
│   ├── CMakeLists.txt
│   └── main.c
└── components/
```

### 故障排除
- sdkconfig 缺失: 运行 `idf.py reconfigure`
- Python 依赖问题: 运行 `install.sh` 或使用 ESP-IDF Docker

---

## Make (GNU Make)

### 识别标志
- `Makefile` 文件

### 常用命令
```bash
# 编译
make

# 并行编译
make -j$(nproc)

# 清理
make clean

# 指定目标
make all
make flash
```

### 典型 Makefile 结构
```makefile
CC = gcc
CFLAGS = -Wall -Wextra
TARGET = firmware
SRCS = main.c utils.c

all: $(TARGET)

clean:
	rm -f $(TARGET) *.o
```

### 故障排除
- 目标未找到: 检查 Makefile 中的目标定义
- 命令未找到: 检查工具链路径

---

## CMake

### 识别标志
- `CMakeLists.txt` 文件
- 通常需要 `build/` 目录

### 常用命令
```bash
# 创建构建目录
mkdir build && cd build

# 生成构建系统
cmake ..

# 编译
cmake --build .
# 或
make

# 并行编译
cmake --build . --parallel
```

### 嵌入式 CMake 配置
```cmake
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(my_project)
```

### 故障排除
- 缓存问题: 删除 `build/` 目录重新配置
- 找不到编译器: 设置 `CC` 和 `CXX` 环境变量

---

## Arduino CLI

### 识别标志
- `.ino` 文件
- `sketch.json` (可选)

### 常用命令
```bash
# 编译
arduino-cli compile --fqbn esp32:esp32:esp32 .

# 上传
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 .

# 安装板支持
arduino-cli core install esp32:esp32

# 安装库
arduino-cli lib install "Library Name"
```

### 常用 FQBN (Fully Qualified Board Name)
- ESP32 DevKit: `esp32:esp32:esp32`
- ESP32-S2: `esp32:esp32:esp32s2`
- ESP32-C3: `esp32:esp32:esp32c3`
- Arduino Uno: `arduino:avr:uno`

---

## Keil MDK

### 识别标志
- `.uvprojx` 文件 (项目文件)
- `.uvoptx` 文件 (选项文件)

### 说明
Keil 是 Windows GUI 工具，主要需要手动操作。但可以使用命令行:
```bash
# 编译项目 (Windows)
UV4.exe -b project.uvprojx -j0 -o build_log.txt

# 烧录
UV4.exe -f project.uvprojx
```

### 故障排除
- 需要 Windows 环境
- 通常需要安装相应 Device Family Pack

---

## IAR Embedded Workbench

### 识别标志
- `.ewp` 文件 (项目文件)
- `.eww` 文件 (工作区文件)

### 说明
IAR 也是 GUI 工具，命令行支持:
```bash
# 编译
iarbuild.exe project.ewp -build Debug -log all

# 清理
iarbuild.exe project.ewp -clean Debug
```

---

## STM32CubeIDE / STM32CubeMX

### 识别标志
- `.cproject` 文件
- `.project` 文件
- `.ioc` 文件 (CubeMX 配置)

### 常用命令 (STM32CubeIDE 基于 Eclipse)
```bash
# 使用 headless 模式编译
stm32cubeidec.exe -nosplash -application org.eclipse.cdt.managedbuilder.core.headlessbuild \
    -import . -build project/Debug
```

### 生成的项目结构
```
project/
├── Core/
│   ├── Inc/
│   └── Src/
├── Drivers/
├── Middlewares/ (可选)
└── .ioc (CubeMX 配置文件)
```

---

## SiFli SDK (SF32)

### 识别标志
- `SConstruct` 文件
- `sdk/` 目录（SiFli SDK）
- 项目结构包含 `project/` 目录

### 常用命令
```bash
# 编译项目（需要指定开发板）
scons --board=sf32lb52-lcd_n16r8 -j8

# 其他常用板子名称
# sf32lb52-lcd_52d
# sf32lb56-lcd_n16r12n1
# sf32lb58-lcd_n16r32n1_dpi
# sf32lb55-canvas

# 配置项目
scons --board=<board_name> --menuconfig

# 清理编译
scons --board=<board_name> -c

# 编译 LCPU（低功耗 CPU）
scons --board=sf32lb52-lcd_n16r8_lcpu -j8
```

### 项目结构
```
project/
├── SConstruct
├── project/
│   ├── SConscript
│   └── main.c
├── build_sf32lb52-lcd_n16r8_hcpu/  # 编译输出目录
│   ├── uart_download.bat           # Windows 下载脚本
│   ├── uart_download.sh            # Linux/macOS 下载脚本
│   └── *.bin
```

### 故障排除
- 板子名称错误: 查看 `sdk/boards/` 目录获取可用板子列表
- 环境未配置: 运行 SDK 的 env 设置脚本
- 双核项目: 需要分别编译 HCPU 和 LCPU

---

## 自动检测逻辑

```
if platformio.ini exists:
    return "pio run"

if sdkconfig exists or (CMakeLists.txt and main/):
    return "idf.py build"

if SConstruct exists:
    # 需要检测或询问 board 名称
    return "scons --board=<detect_board> -j8"

if Makefile exists:
    return "make"

if CMakeLists.txt exists:
    return "mkdir -p build && cd build && cmake .. && make"

if *.ino files exist:
    return "arduino-cli compile --fqbn <detect_board> ."

if *.uvprojx exists:
    return "keil_gui"  # 提示手动操作

if *.ewp exists:
    return "iar_gui"  # 提示手动操作

if .cproject exists:
    return "stm32cubeide"  # 提示手动操作
```

---

## 环境变量检查

检查以下环境变量来确定工具链:

| 变量 | 说明 |
|------|------|
| `IDF_PATH` | ESP-IDF 路径 |
| `PLATFORMIO_CORE_DIR` | PlatformIO 核心目录 |
| `ARDUINO_PATH` | Arduino IDE 路径 |
| `GCC_ARM_PATH` | ARM GCC 工具链 |
| `KEIL_PATH` | Keil 安装路径 |
| `SF32_SDK_PATH` | SiFli SDK 路径 |
| `SIFLI_SDK` | SiFli SDK 路径（替代） |
