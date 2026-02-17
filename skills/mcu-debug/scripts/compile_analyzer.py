#!/usr/bin/env python3
"""
MCU 编译错误分析器
执行编译命令并解析错误输出
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ErrorType(Enum):
    """编译错误类型"""
    SYNTAX = "syntax"
    PREPROCESSOR = "preprocessor"
    LINKER = "linker"
    SEMANTIC = "semantic"
    WARNING = "warning"
    UNKNOWN = "unknown"
    FRAMEWORK = "framework"


class ErrorSeverity(Enum):
    """错误严重程度"""
    ERROR = "error"
    WARNING = "warning"
    FATAL = "fatal"
    NOTE = "note"


@dataclass
class CompileError:
    """编译错误信息"""
    type: ErrorType
    severity: ErrorSeverity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    raw_line: str = ""


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    errors: List[CompileError] = field(default_factory=list)
    warnings: List[CompileError] = field(default_factory=list)
    raw_output: str = ""
    return_code: int = 0


class MCUCompileAnalyzer:
    """MCU 编译错误分析器"""

    # GCC/Clang 错误模式
    GCC_ERROR_PATTERN = re.compile(
        r'^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+)?\s*:'
        r'\s*(?P<severity>error|warning|note|fatal error)'
        r':\s*(?P<message>.+)$',
        re.MULTILINE
    )

    # 链接错误模式
    LINKER_ERROR_PATTERNS = [
        re.compile(r'undefined reference to [`\']([^\']+)[`\']'),
        re.compile(r'multiple definition of [`\']([^\']+)[`\']'),
        re.compile(r'cannot find (-l[^\s:]+)'),
        re.compile(r'collect2:\s*error:\s*ld returned (\d+) exit status'),
    ]

    # 语法错误关键词
    SYNTAX_KEYWORDS = [
        'expected', 'unexpected', 'syntax error', 'missing', 'before',
        'after', 'undeclared', 'was not declared', 'invalid',
        'cannot convert', 'no match for', 'incomplete type'
    ]

    # 预处理器错误关键词
    PREPROCESSOR_KEYWORDS = [
        '#error', 'No such file or directory', 'cannot open',
        'permission denied', 'macro', 'redefined'
    ]

    # 框架/配置错误关键词
    FRAMEWORK_KEYWORDS = [
        'configuration', 'sdkconfig', 'menuconfig', 'Kconfig',
        'board', 'variant', 'partition', 'flash', 'memory',
        'heap', 'stack', 'interrupt', 'vector', 'scons',
        'SConstruct', 'SConscript', 'board_name'
    ]

    # SCons 特定错误模式
    SCONS_ERROR_PATTERNS = [
        re.compile(r'Error:\s*No such board:\s*(\S+)'),
        re.compile(r'Error:\s*board_name\s*not\s*specified'),
        re.compile(r'scons:\s*\*\*\*\s*(.+)'),
    ]

    # SiFli SDK 特定错误
    SIFLI_KEYWORDS = [
        'hcpu', 'lcpu', 'bf0_hal', 'sifli', 'sf32lb',
        'EPIC', 'LCDC', 'AUDCODEC', 'AUDPRC'
    ]

    def __init__(self, project_path: str, build_cmd: str):
        self.project_path = Path(project_path).resolve()
        self.build_cmd = build_cmd
        self.raw_output = ""

    def run_build(self) -> tuple[int, str, str]:
        """执行编译命令"""
        try:
            result = subprocess.run(
                self.build_cmd,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Build timeout after 300 seconds"
        except Exception as e:
            return -1, "", str(e)

    def classify_error(self, message: str) -> ErrorType:
        """分类错误类型"""
        message_lower = message.lower()

        # 检查链接错误
        for pattern in self.LINKER_ERROR_PATTERNS:
            if pattern.search(message):
                return ErrorType.LINKER

        # 检查 SCons 特定错误
        for pattern in self.SCONS_ERROR_PATTERNS:
            if pattern.search(message):
                return ErrorType.FRAMEWORK

        # 检查预处理器错误
        for keyword in self.PREPROCESSOR_KEYWORDS:
            if keyword.lower() in message_lower:
                return ErrorType.PREPROCESSOR

        # 检查框架错误
        for keyword in self.FRAMEWORK_KEYWORDS:
            if keyword.lower() in message_lower:
                return ErrorType.FRAMEWORK

        # 检查 SiFli SDK 特定错误
        for keyword in self.SIFLI_KEYWORDS:
            if keyword.lower() in message_lower:
                return ErrorType.FRAMEWORK

        # 检查语法错误
        for keyword in self.SYNTAX_KEYWORDS:
            if keyword.lower() in message_lower:
                return ErrorType.SYNTAX

        return ErrorType.UNKNOWN

    def parse_gcc_output(self, output: str) -> List[CompileError]:
        """解析 GCC/Clang 输出"""
        errors = []

        for match in self.GCC_ERROR_PATTERN.finditer(output):
            severity_str = match.group('severity').replace(' fatal', '').strip()

            try:
                severity = ErrorSeverity(severity_str)
            except ValueError:
                severity = ErrorSeverity.ERROR

            error = CompileError(
                type=self.classify_error(match.group('message')),
                severity=severity,
                message=match.group('message'),
                file=match.group('file'),
                line=int(match.group('line')) if match.group('line') else None,
                column=int(match.group('col')) if match.group('col') else None,
                raw_line=match.group(0)
            )
            errors.append(error)

        return errors

    def parse_linker_errors(self, output: str) -> List[CompileError]:
        """解析链接器错误"""
        errors = []

        for pattern in self.LINKER_ERROR_PATTERNS:
            for match in pattern.finditer(output):
                error = CompileError(
                    type=ErrorType.LINKER,
                    severity=ErrorSeverity.ERROR,
                    message=match.group(0),
                    raw_line=match.group(0)
                )
                errors.append(error)

        return errors

    def is_simple_error(self, error: CompileError) -> bool:
        """
        判断是否为简单错误（可以直接修复）

        简单错误：
        - 语法错误（缺少分号、括号等）
        - 明显的头文件缺失
        - 明显的变量/函数声明问题
        - 简单的类型错误

        复杂错误：
        - 链接错误
        - 框架配置问题
        - 架构相关问题
        - 逻辑错误
        """
        if error.type == ErrorType.LINKER:
            return False
        if error.type == ErrorType.FRAMEWORK:
            return False

        # 语义错误需要具体分析
        if error.type == ErrorType.SEMANTIC:
            # 检查是否是简单的声明问题
            simple_patterns = [
                r'was not declared',
                r'undeclared',
                r'implicit declaration',
            ]
            for pattern in simple_patterns:
                if re.search(pattern, error.message, re.IGNORECASE):
                    return True
            return False

        # 预处理器错误：头文件缺失是简单的，宏问题可能复杂
        if error.type == ErrorType.PREPROCESSOR:
            if 'No such file' in error.message:
                return True
            return False

        # 语法错误通常是简单的
        if error.type == ErrorType.SYNTAX:
            return True

        return False

    def analyze(self) -> AnalysisResult:
        """执行完整的编译分析"""
        # 执行编译
        return_code, stdout, stderr = self.run_build()

        # 合并输出
        full_output = stdout + "\n" + stderr
        self.raw_output = full_output

        result = AnalysisResult(
            success=(return_code == 0),
            raw_output=full_output,
            return_code=return_code
        )

        if return_code == 0:
            return result

        # 解析错误
        gcc_errors = self.parse_gcc_output(full_output)
        linker_errors = self.parse_linker_errors(full_output)

        all_errors = gcc_errors + linker_errors

        # 分类
        for error in all_errors:
            if error.severity == ErrorSeverity.WARNING:
                result.warnings.append(error)
            else:
                result.errors.append(error)

        return result

    def get_summary(self, result: AnalysisResult) -> dict:
        """生成分析摘要"""
        error_types = {}
        for error in result.errors:
            error_types[error.type.value] = error_types.get(error.type.value, 0) + 1

        simple_count = sum(1 for e in result.errors if self.is_simple_error(e))
        complex_count = len(result.errors) - simple_count

        return {
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
            "simple_errors": simple_count,
            "complex_errors": complex_count,
            "error_categories": list(error_types.keys()),
            "error_breakdown": error_types,
            "has_linker_errors": any(
                e.type == ErrorType.LINKER for e in result.errors
            ),
            "has_framework_errors": any(
                e.type == ErrorType.FRAMEWORK for e in result.errors
            ),
        }


def main():
    parser = argparse.ArgumentParser(
        description='MCU 编译错误分析器'
    )
    parser.add_argument(
        '--build-cmd', '-c',
        required=True,
        help='编译命令'
    )
    parser.add_argument(
        '--project-path', '-p',
        required=True,
        help='项目路径'
    )
    parser.add_argument(
        '--output-format', '-f',
        choices=['json', 'text'],
        default='json',
        help='输出格式'
    )

    args = parser.parse_args()

    analyzer = MCUCompileAnalyzer(
        project_path=args.project_path,
        build_cmd=args.build_cmd
    )

    result = analyzer.analyze()
    summary = analyzer.get_summary(result)

    if args.output_format == 'json':
        output = {
            "success": result.success,
            "errors": [
                {
                    "type": e.type.value,
                    "severity": e.severity.value,
                    "message": e.message,
                    "file": e.file,
                    "line": e.line,
                    "column": e.column,
                    "is_simple": analyzer.is_simple_error(e)
                }
                for e in result.errors
            ],
            "summary": summary,
            "raw_output": result.raw_output if not result.success else ""
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        if result.success:
            print("✅ 编译成功")
        else:
            print(f"❌ 编译失败")
            print(f"\n错误摘要:")
            print(f"  总错误数: {summary['total_errors']}")
            print(f"  简单错误: {summary['simple_errors']}")
            print(f"  复杂错误: {summary['complex_errors']}")
            print(f"  警告数: {summary['total_warnings']}")

            if summary['has_linker_errors']:
                print("\n⚠️  检测到链接错误，需要复杂修复")
            if summary['has_framework_errors']:
                print("\n⚠️  检测到框架配置错误，需要复杂修复")

            print(f"\n详细错误:")
            for error in result.errors:
                simple_marker = "[简单]" if analyzer.is_simple_error(error) else "[复杂]"
                location = f"{error.file}:{error.line}" if error.file else "unknown"
                print(f"  {simple_marker} [{error.type.value}] {location}: {error.message}")

    sys.exit(0 if result.success else 1)


if __name__ == '__main__':
    main()
