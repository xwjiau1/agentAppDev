"""Build the repository catalog and validate repository-owned Markdown links."""

from pathlib import Path
import argparse
import os
import re
import sys
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "doc" / "内容索引.md"
LAYERS = (
    ("application", "应用案例", "*/*/案例说明.md"),
    ("Python-appc", "框架技术解析", "*/*.md"),
    ("Python-base", "Python 基础知识点", "*/*.md"),
)


def entries():
    return [(folder, title, sorted((ROOT / folder).glob(pattern)))
            for folder, title, pattern in LAYERS]


def incubating_projects():
    return sorted((ROOT / "incubator").glob("*/README.md"))


def link(path):
    relative = Path(os.path.relpath(path, INDEX.parent)).as_posix()
    return re.sub(r"[\s()\[\]#?%<>]", lambda m: quote(m.group(0), safe=""), relative)


def build_index():
    groups = entries()
    lines = ["# 内容索引", "",
             "> 由 `python scripts/maintain.py index` 生成，请修改源文档后重新生成。", "",
             "按业务找实现、按技术找机制、按语言知识点复习。第三方项目内部文档和资源不逐文件列入本索引。", "",
             "## 仓库入口", "",
             "| 入口 | 内容 |", "|---|---|",
             "| [首页](../README.md) | 应用用途、技术栈与技术解析的交叉导航 |",
             "| [维护规则](维护规则.md) | 归档、验证、提交及本地与远程同步流程 |",
             "| [Agent 工作规则](../AGENTS.md) | 后续 Agent 修改仓库时的执行约束 |",
             "| [Python 基础速查](../Python-base/README.md) | 复习顺序、分类与优先级 |", "",
             "## 内容规模", "", "| 层级 | 条目数 |", "|---|---:|"]
    for folder, title, files in groups:
        lines.append(f"| `{folder}/`：{title} | {len(files)} |")
    projects = incubating_projects()
    lines.append(f"| `incubator/`：孵化项目 | {len(projects)} |")
    lines += ["", "统计单位分别为案例说明、技术解析、知识点和孵化项目 README；不等于源码文件数。", "",
              "## 孵化项目", "",
              "孵化项目与已归档案例分开统计，实际实现状态以各项目 README 为准。", ""]
    for project in projects:
        heading = next((s[2:].strip() for s in project.read_text(encoding="utf-8-sig").splitlines()
                        if s.startswith("# ")), project.parent.name)
        lines.append(f"- [{heading}]({link(project)})")
    lines.append("")
    for folder, title, files in groups:
        lines += [f"## {title}（{folder}）", ""]
        for category in sorted({f.parent.name for f in files} if folder != "application"
                               else {f.parent.parent.name for f in files}):
            lines += [f"### {category}", ""]
            for f in files:
                group = f.parent.parent.name if folder == "application" else f.parent.name
                if group != category:
                    continue
                heading = next((s[2:].strip() for s in f.read_text(encoding="utf-8-sig").splitlines()
                                if s.startswith("# ")), f.stem)
                lines.append(f"- [{heading}]({link(f)})")
            lines.append("")
    lines += ["## 使用与验证文档", ""]
    for f in sorted((ROOT / "doc").glob("*.md")):
        if f != INDEX:
            lines.append(f"- [{f.stem}]({link(f)})")
    return "\n".join(lines) + "\n"


def owned_docs():
    docs = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "Python-base" / "README.md"]
    docs.extend((ROOT / "doc").glob("*.md"))
    for project in incubating_projects():
        docs.append(project)
        docs.extend((project.parent / "docs").glob("*.md"))
    for _, _, files in entries():
        docs.extend(files)
    return sorted(set(docs))


def check():
    errors = []
    total = 0
    if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != build_index():
        errors.append("内容索引未更新：请运行 python scripts/maintain.py index")
    docs = owned_docs()
    for doc in docs:
        if not doc.exists():
            errors.append(f"缺少入口文件：{doc.relative_to(ROOT)}")
            continue
        content = doc.read_text(encoding="utf-8-sig")
        # Ignore fenced examples; source snapshots and their internal docs are excluded.
        content = re.sub(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", "", content,
                         flags=re.MULTILINE | re.DOTALL)
        for raw in re.findall(r"\]\((<[^>]+>|[^\n]*?)\)(?=\s|[。，、；：]|$|\|)", content):
            target = raw.strip()
            target = target[1:-1] if target.startswith("<") else target.split(' "', 1)[0]
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            total += 1
            dest = (doc.parent / unquote(url.path)).resolve()
            if not dest.is_relative_to(ROOT):
                errors.append(f"{doc.relative_to(ROOT)}：链接越出仓库 {target}")
            elif not dest.exists():
                errors.append(f"{doc.relative_to(ROOT)}：链接目标不存在 {target}")
            elif re.fullmatch(r"L\d+(?:-L\d+)?", url.fragment) and dest.is_file():
                bounds = [int(n) for n in re.findall(r"\d+", url.fragment)]
                size = len(dest.read_text(encoding="utf-8-sig").splitlines())
                if min(bounds) < 1 or max(bounds) > size or bounds != sorted(bounds):
                    errors.append(f"{doc.relative_to(ROOT)}：源码行号越界 {target}")
    for error in errors:
        print(error)
    print(f"检查 {len(docs)} 篇维护文档、{total} 处本地文件链接；错误 {len(errors)} 项。")
    print("范围：仓库入口、案例说明、技术解析、Python 知识点、doc 文档和孵化项目 README/docs；"
          "不检查第三方内部文档、远程 URL、标题锚点或代码摘录一致性。")
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["index", "check"])
    args = parser.parse_args()
    if args.command == "index":
        INDEX.parent.mkdir(exist_ok=True)
        INDEX.write_text(build_index(), encoding="utf-8", newline="\n")
        print("已更新 doc/内容索引.md")
        return 0
    return int(check())


if __name__ == "__main__":
    sys.exit(main())
