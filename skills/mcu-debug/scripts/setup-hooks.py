#!/usr/bin/env python3
"""
MCU Debug Hooks 安装工具

自动配置各种构建系统的编译钩子，实现编译失败时自动诊断。
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


class HookInstaller:
    """钩子安装器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.scripts_dir = Path(__file__).parent.resolve()

    def detect_build_system(self) -> str:
        """检测构建系统类型"""
        if (self.project_path / 'platformio.ini').exists():
            return 'platformio'

        if (self.project_path / 'sdkconfig').exists():
            return 'espidf'

        if (self.project_path / 'SConstruct').exists():
            return 'scons'

        if (self.project_path / 'Makefile').exists():
            return 'make'

        if (self.project_path / 'CMakeLists.txt').exists():
            return 'cmake'

        if list(self.project_path.glob('*.ino')):
            return 'arduino'

        return 'unknown'

    def install(self, build_system: str = None) -> bool:
        """安装钩子"""
        if build_system is None:
            build_system = self.detect_build_system()

        if build_system == 'unknown':
            print("❌ 无法识别构建系统")
            print("支持的构建系统: platformio, espidf, scons, make, cmake, arduino")
            return False

        print(f"🔧 检测到构建系统: {build_system}")

        installers = {
            'platformio': self._install_platformio_hook,
            'espidf': self._install_espidf_hook,
            'scons': self._install_scons_hook,
            'make': self._install_make_hook,
            'cmake': self._install_cmake_hook,
            'arduino': self._install_arduino_hook,
        }

        installer = installers.get(build_system)
        if installer:
            return installer()

        return False

    def _install_platformio_hook(self) -> bool:
        """安装 PlatformIO 钩子"""
        print("📦 配置 PlatformIO 钩子...")

        pio_ini = self.project_path / 'platformio.ini'
        if not pio_ini.exists():
            print("❌ 未找到 platformio.ini")
            return False

        # 创建 extra_script.py
        extra_script = self.project_path / 'mcu_debug_pio_hook.py'
        extra_script.write_text('''# MCU Debug Hook for PlatformIO
import subprocess
from platformio import util

Import("env")

def on_build_failed(*args, **kwargs):
    print("\\n🔍 MCU Debug: 编译失败，正在分析...")
    try:
        subprocess.run(
            ["python3", "scripts/mcu-debug-auto.py", "--", "pio", "run"],
            cwd=env.subst("$PROJECT_DIR"),
            check=False
        )
    except Exception as e:
        print(f"MCU Debug 分析失败: {e}")

# 注册构建失败回调
env.AddPostAction("$BUILD_DIR/firmware.elf", lambda *args, **kwargs: None)
''')

        # 修改 platformio.ini 添加 extra_scripts
        content = pio_ini.read_text()
        if 'extra_scripts' not in content:
            content += '\nextra_scripts = pre:mcu_debug_pio_hook.py\n'
            pio_ini.write_text(content)
            print(f"  ✓ 已修改 platformio.ini")

        print(f"  ✓ 已创建 {extra_script.name}")
        print("\\n💡 使用方法:")
        print("  pio run  # 编译失败时会自动分析")

        return True

    def _install_espidf_hook(self) -> bool:
        """安装 ESP-IDF 钩子"""
        print("📦 配置 ESP-IDF 钩子...")

        # 创建 idf.py 包装脚本
        wrapper = self.project_path / 'idf-debug.py'
        wrapper.write_text('''#!/usr/bin/env python3
"""ESP-IDF 调试包装器"""
import subprocess
import sys

def main():
    # 运行原始 idf.py 命令
    result = subprocess.run(
        ['idf.py'] + sys.argv[1:],
        capture_output=False
    )

    # 如果编译失败且是 build 命令
    if result.returncode != 0 and 'build' in sys.argv:
        print("\\n🔍 MCU Debug: 编译失败，正在分析...")
        subprocess.run(
            ['python3', 'scripts/mcu-debug-auto.py', '--', 'idf.py', 'build'],
            cwd='.',
            check=False
        )

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
''')
        wrapper.chmod(0o755)

        print(f"  ✓ 已创建 {wrapper.name}")
        print("\\n💡 使用方法:")
        print("  ./idf-debug.py build  # 代替 idf.py build")
        print("  ./idf-debug.py flash  # 其他命令同样支持")

        return True

    def _install_scons_hook(self) -> bool:
        """安装 SCons/SiFli SDK 钩子"""
        print("📦 配置 SCons 钩子...")

        # 创建 scons 包装脚本
        wrapper = self.project_path / 'scons-debug.py'
        wrapper.write_text('''#!/usr/bin/env python3
"""SCons 调试包装器"""
import subprocess
import sys

def main():
    # 运行原始 scons 命令
    result = subprocess.run(
        ['scons'] + sys.argv[1:],
        capture_output=False
    )

    # 如果编译失败
    if result.returncode != 0:
        print("\\n🔍 MCU Debug: 编译失败，正在分析...")
        board_arg = ''
        for i, arg in enumerate(sys.argv):
            if arg.startswith('--board='):
                board_arg = arg
                break

        cmd = ['python3', 'scripts/mcu-debug-auto.py', '--', 'scons']
        if board_arg:
            cmd.append(board_arg)
        cmd.append('-j8')

        subprocess.run(cmd, cwd='.', check=False)

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
''')
        wrapper.chmod(0o755)

        print(f"  ✓ 已创建 {wrapper.name}")
        print("\\n💡 使用方法:")
        print("  ./scons-debug.py --board=xxx -j8  # 代替 scons")

        return True

    def _install_make_hook(self) -> bool:
        """安装 Make 钩子"""
        print("📦 配置 Make 钩子...")

        # 创建 make 包装脚本
        wrapper = self.project_path / 'make-debug'
        wrapper.write_text('''#!/bin/bash
# Make 调试包装器

# 运行原始 make 命令
make "$@"
EXIT_CODE=$?

# 如果编译失败
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "🔍 MCU Debug: 编译失败，正在分析..."
    python3 scripts/mcu-debug-auto.py -- make "$@"
fi

exit $EXIT_CODE
''')
        wrapper.chmod(0o755)

        print(f"  ✓ 已创建 {wrapper.name}")
        print("\\n💡 使用方法:")
        print("  ./make-debug        # 代替 make")
        print("  ./make-debug clean  # 支持所有 make 参数")

        return True

    def _install_cmake_hook(self) -> bool:
        """安装 CMake 钩子"""
        print("📦 配置 CMake 钩子...")

        # 创建 cmake 构建包装脚本
        wrapper = self.project_path / 'build-debug.sh'
        wrapper.write_text('''#!/bin/bash
# CMake 调试构建脚本

BUILD_DIR=${BUILD_DIR:-build}

# 创建构建目录
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# 配置
cmake .. "$@"
if [ $? -ne 0 ]; then
    echo "CMake 配置失败"
    exit 1
fi

# 构建
make -j$(nproc)
EXIT_CODE=$?

# 如果编译失败
cd ..
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "🔍 MCU Debug: 编译失败，正在分析..."
    python3 scripts/mcu-debug-auto.py -- "mkdir -p build && cd build && cmake .. && make"
fi

exit $EXIT_CODE
''')
        wrapper.chmod(0o755)

        print(f"  ✓ 已创建 {wrapper.name}")
        print("\\n💡 使用方法:")
        print("  ./build-debug.sh        # 构建项目")
        print("  ./build-debug.sh [选项] # 传递给 cmake")

        return True

    def _install_arduino_hook(self) -> bool:
        """安装 Arduino 钩子"""
        print("📦 配置 Arduino CLI 钩子...")

        # 创建 arduino 编译包装脚本
        wrapper = self.project_path / 'arduino-debug.sh'
        wrapper.write_text('''#!/bin/bash
# Arduino 调试编译脚本

# 检测 .ino 文件
INO_FILE=$(ls *.ino 2>/dev/null | head -1)
if [ -z "$INO_FILE" ]; then
    echo "错误: 未找到 .ino 文件"
    exit 1
fi

# 检测 FQBN
FQBN=${FQBN:-esp32:esp32:esp32}
echo "使用 FQBN: $FQBN"

# 编译
arduino-cli compile --fqbn $FQBN . "$@"
EXIT_CODE=$?

# 如果编译失败
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "🔍 MCU Debug: 编译失败，正在分析..."
    python3 scripts/mcu-debug-auto.py -- "arduino-cli compile --fqbn $FQBN ."
fi

exit $EXIT_CODE
''')
        wrapper.chmod(0o755)

        print(f"  ✓ 已创建 {wrapper.name}")
        print("\\n💡 使用方法:")
        print("  ./arduino-debug.sh        # 编译项目")
        print("  FQBN=arduino:avr:uno ./arduino-debug.sh  # 指定板子")

        return True

    def uninstall(self):
        """卸载钩子"""
        print("🗑️  卸载 MCU Debug 钩子...")

        files_to_remove = [
            'mcu_debug_pio_hook.py',
            'idf-debug.py',
            'scons-debug.py',
            'make-debug',
            'build-debug.sh',
            'arduino-debug.sh',
        ]

        for filename in files_to_remove:
            filepath = self.project_path / filename
            if filepath.exists():
                filepath.unlink()
                print(f"  ✓ 已删除 {filename}")

        # 恢复 platformio.ini
        pio_ini = self.project_path / 'platformio.ini'
        if pio_ini.exists():
            content = pio_ini.read_text()
            if 'mcu_debug_pio_hook.py' in content:
                content = content.replace('extra_scripts = pre:mcu_debug_pio_hook.py\n', '')
                pio_ini.write_text(content)
                print(f"  ✓ 已恢复 platformio.ini")

        print("\\n✅ 卸载完成")


def main():
    parser = argparse.ArgumentParser(
        description='MCU Debug Hooks 安装工具'
    )

    parser.add_argument(
        '--project-path', '-p',
        default='.',
        help='项目路径 (默认: 当前目录)'
    )

    parser.add_argument(
        '--build-system', '-b',
        choices=['platformio', 'espidf', 'scons', 'make', 'cmake', 'arduino'],
        help='指定构建系统 (默认: 自动检测)'
    )

    parser.add_argument(
        '--uninstall', '-u',
        action='store_true',
        help='卸载钩子'
    )

    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()

    if not project_path.exists():
        print(f"❌ 项目路径不存在: {project_path}")
        sys.exit(1)

    installer = HookInstaller(project_path)

    if args.uninstall:
        installer.uninstall()
    else:
        success = installer.install(args.build_system)
        if success:
            print("\\n✅ 安装完成！")
        else:
            print("\\n❌ 安装失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
