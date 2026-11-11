# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/tools/check_comments.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

"""检查 Python 注释是否在复述代码。

默认只看相对 HEAD 有改动的行，避免拿旧代码的注释风格挡提交。
用法：

    uv run python tools/check_comments.py
    uv run python tools/check_comments.py path/to/file.py
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SHALLOW = re.compile(
    r"^(获取|设置|判断|返回|处理|初始化|创建|更新|删除|保存|调用)[^。\n]{0,20}[。.]?$"
)
_REASON = ("避免", "防止", "否则", "只有", "失败", "因为", "跳过", "用来", "以免", "不能")
_SECTION = re.compile(
    r"^(Args|Arguments|Parameters|Returns|Return|Yields|Raises|Attributes|参数|返回|异常)\b",
    re.IGNORECASE,
)
_ENGLISH_WORD = re.compile(r"\b[A-Za-z]{3,}\b")
_CODE_TOKEN = re.compile(r"`[^`]+`|\b[A-Za-z_][A-Za-z0-9_]*_[A-Za-z0-9_]+\b|\b[A-Z][A-Za-z0-9]+\b")


@dataclass(frozen=True)
class Issue:
    """一条注释问题。行号从 1 开始，方便和编辑器跳转对齐。"""

    path: str
    line: int
    message: str

    def format(self) -> str:
        """拼成 path:line: message，终端和钩子可以直接贴回对话。"""
        return f"{self.path}:{self.line}: {self.message}"


def check_source(source: str, *, path: str = "<memory>", lines: set[int] | None = None) -> list[Issue]:
    """检查一份源码。lines 为 None 时检查全文，否则只检查这些行号。"""
    issues: list[Issue] = []
    banner = _banner_end(source)
    scope = None if lines is None else lines

    def in_scope(line: int) -> bool:
        return scope is None or line in scope

    issues.extend(_comment_issues(source, path, banner, in_scope))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        issues.append(Issue(path, exc.lineno or 1, f"无法解析，跳过文档字符串检查: {exc.msg}"))
        return issues

    for node in _public_definitions(tree):
        if node.name.startswith("_") or node.name.startswith("test_"):
            continue
        if not in_scope(node.lineno):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None:
            kind = "类" if isinstance(node, ast.ClassDef) else "函数"
            issues.append(Issue(path, node.lineno, f"公开{kind} {node.name} 缺少文档字符串"))
            continue
        doc_line = _docstring_lineno(node)
        if doc_line is not None and in_scope(doc_line):
            issues.extend(_docstring_issues(doc, node, path, doc_line))
    return issues


def _public_definitions(tree: ast.AST):
    """模块和类体里的定义。函数内部的辅助函数不要求文档字符串。"""
    nodes = list(getattr(tree, "body", []))
    index = 0
    while index < len(nodes):
        node = nodes[index]
        index += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node
        if isinstance(node, ast.ClassDef):
            nodes.extend(node.body)


def _banner_end(source: str) -> int:
    """文件开头连续的注释和空行，版权声明不算业务注释。"""
    last = 0
    for index, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            last = index
            continue
        break
    return last


def _comment_issues(source: str, path: str, banner: int, in_scope) -> list[Issue]:
    issues: list[Issue] = []
    physical = source.splitlines()
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        comments = [
            (token.start[0], token.string.lstrip("#").strip())
            for token in tokens
            if token.type == tokenize.COMMENT
        ]
    except tokenize.TokenError:
        return issues

    for line_no, text in comments:
        if line_no <= banner or not in_scope(line_no):
            continue
        if text.startswith(("noqa", "type:", "pragma", "pylint", "fmt:")):
            continue
        if _is_echo(text, _next_code_line(physical, line_no)):
            issues.append(Issue(path, line_no, "行内注释在复述下一行代码"))
        if _is_mixed_prose(text):
            issues.append(Issue(path, line_no, "同一条注释里中英文句子混写"))
    return issues


def _next_code_line(lines: list[str], comment_line: int) -> str:
    for line in lines[comment_line:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _is_echo(comment: str, code: str) -> bool:
    # 带因果词的注释即使和下一行用词重合，也是在解释原因，不算复述
    if any(marker in comment for marker in _REASON):
        return False
    comment_tokens = _words(comment)
    code_tokens = _words(code)
    if len(comment_tokens) < 2 or not code_tokens:
        return False
    overlap = comment_tokens & code_tokens
    return len(overlap) / len(comment_tokens) >= 0.8


def _words(text: str) -> set[str]:
    return {item.lower() for item in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}", text)}


def _is_mixed_prose(text: str) -> bool:
    """中文句子旁边再写一串英文句子。标识符、蛇形命名和反引号里的代码不算。

    要凑满四个英文单词才算一句英文，避免误伤注释里的短英文片段。
    """
    stripped = _CODE_TOKEN.sub(" ", text)
    if not re.search(r"[\u4e00-\u9fff]", stripped):
        return False
    return len(_ENGLISH_WORD.findall(stripped)) >= 4


def _docstring_lineno(node: ast.AST) -> int | None:
    body = getattr(node, "body", [])
    if not body:
        return None
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant):
        if isinstance(first.value.value, str):
            return first.lineno
    return None


def _docstring_issues(doc: str, node: ast.AST, path: str, line: int) -> list[Issue]:
    issues: list[Issue] = []
    first = re.split(r"[。.!]", doc.strip())[0].strip()
    if _is_shallow(first):
        issues.append(Issue(path, line, "文档字符串第一句只是在翻译函数名"))
    if _is_annotation_restatement(doc, node):
        issues.append(Issue(path, line, "文档字符串只在复述参数注解"))
    if _is_mixed_prose(doc):
        issues.append(Issue(path, line, "文档字符串里中英文句子混写"))
    return issues


def _is_shallow(sentence: str) -> bool:
    if any(marker in sentence for marker in _REASON):
        return False
    return bool(_SHALLOW.match(sentence.strip()))


def _is_annotation_restatement(doc: str, node: ast.AST) -> bool:
    prose: list[str] = []
    entries: list[str] = []
    in_section = False
    for raw in doc.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _SECTION.match(line):
            in_section = True
            continue
        if in_section:
            entries.append(line)
        else:
            prose.append(line)

    prose_text = "".join(prose)
    if len(prose_text) > 24 and not _is_shallow(prose[0] if prose else ""):
        return False
    if not entries:
        return False

    names = _param_names(node)
    thin = 0
    for line in entries:
        matched = re.match(r"^([A-Za-z_]\w*)\s*(\([^)]*\))?\s*[:：]\s*(.*)$", line)
        if matched is None:
            return False
        name, _, description = matched.group(1), matched.group(2), matched.group(3).strip()
        if name not in names and name.lower() not in {"return", "returns", "none"}:
            return False
        if len(description) <= 16:
            thin += 1
    return thin == len(entries) and thin > 0


def _param_names(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return set()
    names = {arg.arg for arg in node.args.args + node.args.kwonlyargs}
    if node.args.vararg is not None:
        names.add(node.args.vararg.arg)
    if node.args.kwarg is not None:
        names.add(node.args.kwarg.arg)
    return names


def changed_python_files() -> dict[Path, set[int] | None]:
    """相对 HEAD 的改动行。未跟踪文件返回 None，表示整文件都算新增。"""
    files: dict[Path, set[int] | None] = {}
    diff = _git("diff", "-U0", "HEAD", "--", "*.py")
    for path, lines in _parse_added_lines(diff).items():
        files[path] = lines

    untracked = _git("ls-files", "--others", "--exclude-standard", "--", "*.py")
    for raw in untracked.splitlines():
        if raw.strip():
            files[REPO_ROOT / raw.strip()] = None
    return files


def _parse_added_lines(diff: str) -> dict[Path, set[int]]:
    files: dict[Path, set[int]] = {}
    current: Path | None = None
    new_line = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = REPO_ROOT / line[6:]
            files.setdefault(current, set())
            continue
        matched = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if matched and current is not None:
            new_line = int(matched.group(1))
            continue
        if current is None or not line.startswith("+") or line.startswith("+++"):
            continue
        files[current].add(new_line)
        new_line += 1
    return {path: lines for path, lines in files.items() if lines}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git 命令失败")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    """检查参数里的文件；没有参数时检查相对 HEAD 的 Python 改动。"""
    args = list(sys.argv[1:] if argv is None else argv)
    issues: list[Issue] = []
    if args:
        targets = [(Path(arg), None) for arg in args]
    else:
        targets = list(changed_python_files().items())
        if not targets:
            print("没有改动过的 Python 文件。")
            return 0

    for path, lines in targets:
        file_path = path if path.is_absolute() else REPO_ROOT / path
        if file_path.suffix != ".py" or not file_path.is_file():
            continue
        source = file_path.read_text(encoding="utf-8")
        relative = file_path.relative_to(REPO_ROOT).as_posix()
        issues.extend(check_source(source, path=relative, lines=lines))

    if not issues:
        print("注释检查通过。")
        return 0
    for issue in issues:
        print(issue.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
