#!/usr/bin/env python3
"""
MCU Debug Auto - 自动编译诊断工具

用法:
    # 直接包装编译命令
    mcu-debug-auto.py -- make
    mcu-debug-auto.py -- pio run
    mcu-debug-auto.py -- idf.py build

    # 监视模式 - 文件变化自动编译
    mcu-debug-auto.py --watch -- make

    # 与 Claude Code 集成
    mcu-debug-auto.py --claude -- make
"""

import argparse
import os
import subprocess
import sys
import json
import time
from pathlib import Path
from typing import List, Optional, Tuple
from compile_analyzer import MCUCompileAnalyzer, AnalysisResult


class MCULogger:
    """简单的日志记录器"""

    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
    }

    @classmethod
    def info(cls, msg: str):
        print(f"{cls.COLORS['cyan']}[MCU-DEBUG]{cls.COLORS['reset']} {msg}")

    @classmethod
    def success(cls, msg: str):
        print(f"{cls.COLORS['green']}[MCU-DEBUG]{cls.COLORS['reset']} {msg}")

    @classmethod
    def warning(cls, msg: str):
        print(f"{cls.COLORS['yellow']}[MCU-DEBUG]{cls.COLORS['reset']} {msg}")

    @classmethod
    def error(cls, msg: str):
        print(f"{cls.COLORS['red']}[MCU-DEBUG]{cls.COLORS['reset']} {msg}")


class MCUDiagnosisEngine:
    """MCU 诊断引擎 - 生成修复建议"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()

    def diagnose(self, result: AnalysisResult) -> List[dict]:
        """生成诊断建议"""
        suggestions = []

        for error in result.errors:
            suggestion = self._analyze_error(error)
            if suggestion:
                suggestions.append(suggestion)

        return suggestions

    def _analyze_error(self, error) -> Optional[dict]:
        """分析单个错误并生成建议"""
        msg = error.message.lower()

        # 头文件缺失
        if 'no such file or directory' in msg or 'file not found' in msg:
            return self._fix_header_missing(error)

        # 未声明的标识符
        if 'undeclared' in msg or 'was not declared' in msg:
            return self._fix_undeclared(error)

        # 缺少分号
        if 'expected' in msg and "';'" in msg:
            return self._fix_missing_semicolon(error)

        # 函数未声明
        if 'implicit declaration' in msg:
            return self._fix_implicit_function(error)

        # 未定义引用（链接错误）
        if 'undefined reference' in msg:
            return self._fix_undefined_reference(error)

        return None

    def _fix_header_missing(self, error) -> dict:
        """生成头文件缺失的修复建议"""
        # 从头文件路径中提取文件名
        import re
        match = re.search(r"['\"]([^'\"]+)['\"]", error.message)
        header = match.group(1) if match else "unknown"

        # 尝试找到正确的头文件路径
        possible_fixes = []

        # 常见 MCU 头文件映射
        header_mapping = {
            'driver/gpio.h': '#include "driver/gpio.h"  // ESP32 GPIO',
            'driver/uart.h': '#include "driver/uart.h"  // ESP32 UART',
            'driver/i2c.h': '#include "driver/i2c.h"  // ESP32 I2C',
            'driver/spi.h': '#include "driver/spi_master.h"  // ESP32 SPI',
            'freertos/FreeRTOS.h': '#include "freertos/FreeRTOS.h"\n#include "freertos/task.h"',
            'Arduino.h': '#include "Arduino.h"  // Arduino core',
            'bf0_hal_gpio.h': '#include "bf0_hal_gpio.h"  // SiFli HAL',
            'bf0_hal_uart.h': '#include "bf0_hal_uart.h"  // SiFli HAL',
        }

        if header in header_mapping:
            possible_fixes.append(header_mapping[header])
        else:
            possible_fixes.append(f'#include "{header}"')

        return {
            'type': 'header_missing',
            'file': error.file,
            'line': error.line,
            'message': error.message,
            'suggestion': f'添加头文件包含: {header}',
            'fixes': possible_fixes,
            'auto_fixable': True
        }

    def _fix_undeclared(self, error) -> dict:
        """生成未声明标识符的修复建议"""
        import re
        match = re.search(r"['\"](\w+)['\"]", error.message)
        identifier = match.group(1) if match else "unknown"

        # 常见宏和变量映射
        common_fixes = {
            'GPIO_NUM_25': '#include "driver/gpio.h"',
            'GPIO_NUM_26': '#include "driver/gpio.h"',
            'GPIO_NUM_27': '#include "driver/gpio.h"',
            'vTaskDelay': '#include "freertos/task.h"',
            'pdMS_TO_TICKS': '#include "freertos/task.h"',
            'configTICK_RATE_HZ': '#include "freertos/FreeRTOS.h"',
        }

        fix = common_fixes.get(identifier, f'// TODO: 声明变量或添加头文件: {identifier}')

        return {
            'type': 'undeclared',
            'file': error.file,
            'line': error.line,
            'message': error.message,
            'suggestion': f'标识符 "{identifier}" 未声明',
            'fixes': [fix],
            'auto_fixable': identifier in common_fixes
        }

    def _fix_missing_semicolon(self, error) -> dict:
        """生成缺少分号的修复建议"""
        return {
            'type': 'syntax',
            'file': error.file,
            'line': error.line,
            'message': error.message,
            'suggestion': f'在 {error.file}:{error.line} 末尾添加分号',
            'fixes': ['在上一行末尾添加 ;'],
            'auto_fixable': False  # 需要精确分析
        }

    def _fix_implicit_function(self, error) -> dict:
        """生成隐式函数声明的修复建议"""
        import re
        match = re.search(r"function ['\"](\w+)['\"]", error.message)
        func = match.group(1) if match else "unknown"

        common_headers = {
            'printf': '#include <stdio.h>',
            'sprintf': '#include <stdio.h>',
            'malloc': '#include <stdlib.h>',
            'free': '#include <stdlib.h>',
            'memset': '#include <string.h>',
            'memcpy': '#include <string.h>',
            'strcpy': '#include <string.h>',
        }

        fix = common_headers.get(func, f'// TODO: 添加函数声明或头文件: {func}')

        return {
            'type': 'implicit_function',
            'file': error.file,
            'line': error.line,
            'message': error.message,
            'suggestion': f'函数 "{func}" 隐式声明',
            'fixes': [fix],
            'auto_fixable': func in common_headers
        }

    def _fix_undefined_reference(self, error) -> dict:
        """生成未定义引用的修复建议"""
        import re
        match = re.search(r"`([^']+)'", error.message)
        symbol = match.group(1) if match else "unknown"

        return {
            'type': 'linker',
            'file': None,
            'line': None,
            'message': error.message,
            'suggestion': f'链接错误: 符号 "{symbol}" 未定义',
            'fixes': [
                f'// 检查是否缺少库文件链接',
                f'// 例如: target_link_libraries(your_target {symbol})',
                f'// 或检查源文件是否被编译'
            ],
            'auto_fixable': False
        }


class MCUDiagnosisReporter:
    """诊断报告生成器"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.diagnosis_file = self.project_path / '.mcu-diagnosis.json'

    def save(self, result: AnalysisResult, suggestions: List[dict]):
        """保存诊断结果到文件"""
        data = {
            'timestamp': time.time(),
            'project_path': str(self.project_path),
            'success': result.success,
            'error_count': len(result.errors),
            'warning_count': len(result.warnings),
            'errors': [
                {
                    'type': e.type.value,
                    'severity': e.severity.value,
                    'message': e.message,
                    'file': e.file,
                    'line': e.line,
                    'column': e.column,
                }
                for e in result.errors
            ],
            'suggestions': suggestions
        }

        with open(self.diagnosis_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> Optional[dict]:
        """加载最近的诊断结果"""
        if not self.diagnosis_file.exists():
            return None

        try:
            with open(self.diagnosis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


class FileWatcher:
    """文件监视器 - 用于 watch 模式"""

    def __init__(self, project_path: str, patterns: List[str] = None):
        self.project_path = Path(project_path)
        self.patterns = patterns or ['*.c', '*.cpp', '*.h', '*.hpp', '*.ino']
        self.file_mtimes = {}

    def scan(self) -> List[Path]:
        """扫描所有匹配的文件"""
        files = []
        for pattern in self.patterns:
            files.extend(self.project_path.rglob(pattern))
        return files

    def get_changed_files(self) -> List[Path]:
        """获取变化的文件列表"""
        changed = []
        current_files = self.scan()

        for file in current_files:
            try:
                mtime = file.stat().st_mtime
                if str(file) not in self.file_mtimes:
                    changed.append(file)
                elif self.file_mtimes[str(file)] != mtime:
                    changed.append(file)
                self.file_mtimes[str(file)] = mtime
            except Exception:
                pass

        return changed

    def wait_for_changes(self, interval: float = 1.0) -> List[Path]:
        """等待文件变化"""
        while True:
            time.sleep(interval)
            changed = self.get_changed_files()
            if changed:
                return changed


class MCUDiagnosisCLI:
    """MCU 诊断命令行界面"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.analyzer = None
        self.engine = MCUDiagnosisEngine(project_path)
        self.reporter = MCUDiagnosisReporter(project_path)

    def run_build(self, build_cmd: str, auto_fix: bool = False, claude_mode: bool = False) -> bool:
        """运行编译并诊断"""
        MCULogger.info(f"执行编译: {build_cmd}")
        MCULogger.info(f"项目路径: {self.project_path}")

        # 运行编译分析
        self.analyzer = MCUCompileAnalyzer(
            project_path=str(self.project_path),
            build_cmd=build_cmd
        )

        result = self.analyzer.analyze()

        if result.success:
            MCULogger.success("✅ 编译成功！")
            self.reporter.save(result, [])
            return True

        # 编译失败，进行诊断
        MCULogger.error(f"❌ 编译失败 - 发现 {len(result.errors)} 个错误")

        # 生成修复建议
        suggestions = self.engine.diagnose(result)

        # 保存诊断结果
        self.reporter.save(result, suggestions)

        # 显示诊断报告
        self._display_diagnosis(result, suggestions)

        # 自动修复（如果启用）
        if auto_fix:
            self._apply_auto_fixes(suggestions)

        # Claude Code 模式
        if claude_mode:
            self._trigger_claude_diagnosis()

        return False

    def _display_diagnosis(self, result: AnalysisResult, suggestions: List[dict]):
        """显示诊断报告"""
        print("\n" + "=" * 60)
        print("📋 MCU 编译诊断报告")
        print("=" * 60)

        # 显示错误摘要
        summary = self.analyzer.get_summary(result)
        print(f"\n错误摘要:")
        print(f"  总错误数: {summary['total_errors']}")
        print(f"  简单错误: {summary['simple_errors']}")
        print(f"  复杂错误: {summary['complex_errors']}")
        print(f"  警告数: {summary['total_warnings']}")

        # 显示修复建议
        if suggestions:
            print(f"\n💡 修复建议:")
            for i, sug in enumerate(suggestions[:5], 1):  # 最多显示5个
                auto_tag = "[可自动修复]" if sug['auto_fixable'] else "[需手动修复]"
                print(f"\n  {i}. {auto_tag}")
                print(f"     位置: {sug['file']}:{sug['line']}")
                print(f"     问题: {sug['suggestion']}")
                if sug['fixes']:
                    print(f"     建议:")
                    for fix in sug['fixes']:
                        print(f"       → {fix}")

        # 提示使用 Claude Code
        print(f"\n🤖 使用 Claude Code 进行深度诊断:")
        print(f"   在项目目录运行: claude")
        print(f"   然后输入: fix")

        print("\n" + "=" * 60)

    def _apply_auto_fixes(self, suggestions: List[dict]):
        """应用自动修复"""
        MCULogger.info("应用自动修复...")

        fixed_count = 0
        for sug in suggestions:
            if sug['auto_fixable'] and sug['type'] == 'header_missing':
                if self._apply_header_fix(sug):
                    fixed_count += 1

        if fixed_count > 0:
            MCULogger.success(f"✅ 自动修复了 {fixed_count} 个问题")
            MCULogger.info("请重新编译验证...")
        else:
            MCULogger.warning("没有可以自动修复的问题")

    def _apply_header_fix(self, suggestion: dict) -> bool:
        """应用头文件修复"""
        file_path = self.project_path / suggestion['file']
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 在第一行后添加头文件包含
            if suggestion['fixes']:
                header_include = suggestion['fixes'][0] + '\n'

                # 找到合适的插入位置（在其他 include 之后）
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('#include'):
                        insert_pos = i + 1

                lines.insert(insert_pos, header_include)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                MCULogger.success(f"  ✓ 修复: {file_path}")
                return True

        except Exception as e:
            MCULogger.error(f"  ✗ 修复失败: {e}")

        return False

    def _trigger_claude_diagnosis(self):
        """触发 Claude Code 诊断"""
        # 生成用于 Claude 的诊断提示
        diagnosis = self.reporter.load()
        if not diagnosis:
            return

        # 创建临时提示文件
        prompt_file = self.project_path / '.mcu-claude-prompt.txt'

        prompt = f"""# MCU 编译诊断请求

项目路径: {self.project_path}

## 错误摘要
- 错误数: {diagnosis['error_count']}
- 警告数: {diagnosis['warning_count']}

## 错误详情
"""

        for err in diagnosis['errors'][:10]:
            prompt += f"\n- [{err['type']}] {err['file']}:{err['line']}: {err['message']}\n"

        prompt += """
## 请执行以下操作:
1. 分析错误根因
2. 提供修复方案
3. 应用修复
4. 验证编译

输入 "fix" 开始自动修复流程。
"""

        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        MCULogger.info(f"Claude 诊断提示已保存到: {prompt_file}")

    def watch_mode(self, build_cmd: str, interval: float = 2.0):
        """监视模式 - 文件变化自动编译"""
        watcher = FileWatcher(str(self.project_path))

        MCULogger.info("👀 启动监视模式...")
        MCULogger.info(f"   监视文件类型: *.c, *.cpp, *.h, *.hpp, *.ino")
        MCULogger.info(f"   按 Ctrl+C 退出")
        MCULogger.info(f"   初始编译中...")

        # 初始编译
        self.run_build(build_cmd)

        # 监视循环
        try:
            while True:
                changed = watcher.wait_for_changes(interval)
                if changed:
                    MCULogger.info(f"检测到 {len(changed)} 个文件变化:")
                    for f in changed[:3]:
                        MCULogger.info(f"  - {f.name}")
                    if len(changed) > 3:
                        MCULogger.info(f"  ... 和其他 {len(changed) - 3} 个文件")

                    # 延迟编译，避免频繁保存触发多次编译
                    time.sleep(0.5)
                    self.run_build(build_cmd)

        except KeyboardInterrupt:
            MCULogger.info("👋 退出监视模式")


def detect_build_system(project_path: str) -> Optional[str]:
    """自动检测构建系统并返回编译命令"""
    path = Path(project_path)

    if (path / 'platformio.ini').exists():
        return 'pio run'

    if (path / 'sdkconfig').exists() or (
        (path / 'CMakeLists.txt').exists() and (path / 'main').is_dir()
    ):
        return 'idf.py build'

    if (path / 'SConstruct').exists():
        # 尝试检测 board 名称
        boards_dir = path / 'sdk' / 'boards'
        if boards_dir.exists():
            boards = list(boards_dir.glob('*'))
            if boards:
                board_name = boards[0].name
                return f'scons --board={board_name} -j8'
        return 'scons -j8'

    if (path / 'Makefile').exists():
        return 'make'

    if (path / 'CMakeLists.txt').exists():
        return 'mkdir -p build && cd build && cmake .. && make'

    ino_files = list(path.glob('*.ino'))
    if ino_files:
        # 尝试检测 FQBN
        return 'arduino-cli compile --fqbn esp32:esp32:esp32 .'

    return None


def main():
    parser = argparse.ArgumentParser(
        description='MCU Debug Auto - 自动编译诊断工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 直接包装编译命令
  %(prog)s -- make
  %(prog)s -- pio run
  %(prog)s -- idf.py build

  # 自动检测构建系统
  %(prog)s --auto-detect

  # 监视模式
  %(prog)s --watch -- make

  # 自动修复简单错误
  %(prog)s --auto-fix -- make

  # 与 Claude Code 集成
  %(prog)s --claude -- make
        """
    )

    parser.add_argument(
        '--project-path', '-p',
        default='.',
        help='项目路径 (默认: 当前目录)'
    )

    parser.add_argument(
        '--auto-detect', '-d',
        action='store_true',
        help='自动检测构建系统'
    )

    parser.add_argument(
        '--watch', '-w',
        action='store_true',
        help='监视模式 - 文件变化自动编译'
    )

    parser.add_argument(
        '--auto-fix', '-f',
        action='store_true',
        help='自动修复简单错误'
    )

    parser.add_argument(
        '--claude', '-c',
        action='store_true',
        help='Claude Code 集成模式'
    )

    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=2.0,
        help='监视模式检查间隔 (秒, 默认: 2)'
    )

    parser.add_argument(
        'build_cmd',
        nargs='?',
        help='编译命令 (例如: make, pio run)'
    )

    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()

    if not project_path.exists():
        MCULogger.error(f"项目路径不存在: {project_path}")
        sys.exit(1)

    # 自动检测构建系统
    if args.auto_detect:
        build_cmd = detect_build_system(project_path)
        if build_cmd:
            MCULogger.info(f"检测到构建系统: {build_cmd}")
            args.build_cmd = build_cmd
        else:
            MCULogger.error("无法自动检测构建系统，请手动指定")
            sys.exit(1)

    if not args.build_cmd:
        # 尝试自动检测
        build_cmd = detect_build_system(project_path)
        if build_cmd:
            MCULogger.info(f"自动检测到构建系统: {build_cmd}")
            args.build_cmd = build_cmd
        else:
            MCULogger.error("请指定编译命令或使用 --auto-detect")
            parser.print_help()
            sys.exit(1)

    # 创建 CLI 实例
    cli = MCUDiagnosisCLI(project_path)

    # 运行模式
    if args.watch:
        cli.watch_mode(args.build_cmd, args.interval)
    else:
        success = cli.run_build(
            args.build_cmd,
            auto_fix=args.auto_fix,
            claude_mode=args.claude
        )
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
