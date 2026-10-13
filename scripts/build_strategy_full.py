#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 SKILL.md + references/*.md 合并成一个「全量方法论」单文件（供不支持技能包的 AI 直读）。

用法：
  python3 build_strategy_full.py            # 输出到 skill 根目录的 strategy-full.md
  python3 build_strategy_full.py --out x.md

为什么要有这个脚本：之前这个单文件是手工合并的，规则一更新就过期（曾停留在「5 条文案 / 60 字上限 / 加我微信」的旧版）。
每次改完 SKILL.md 或 references/，跑一次本脚本即可保持一致。
"""
import argparse
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SKILL_DIR = HERE.parent
SKILL_MD = SKILL_DIR / "SKILL.md"
REF_DIR = SKILL_DIR / "references"

# 合并顺序（与 SKILL.md 的参考文件索引一致）
ORDER = [
    "diagnosis-persona.md",
    "copy-creative.md",
    "hooks-creative-bootcamp.md",
    "ad-mockup-render.md",
    "copy-sheet.md",
    "html-delivery.md",
    "landing-delivery.md",
    "compliance.md",
    "compliance-scan.md",
    "industry-cases.md",
    "ip-video.md",
    "plan-template.md",
]

HEADER = """# 朋友圈广告投放策略 · 全量方法论（AI 直读版）

> 使用方法：把本文件的链接发给你的 AI，再说一句「读完这个链接，之后我发你公司简介，你按这套方法出朋友圈广告投放策略方案」。
> 本文件由 moments-ad-strategy skill 合并生成，供不支持技能包的 AI 工具直接阅读。
> ⚠️ 规则以正文为准：外层文案 **≤40 字 / ≤4 行 / 不允许空格**，行动指令只用「加企微 / 加客服」。

---
"""


def strip_frontmatter(text):
    """去掉 SKILL.md 的 YAML frontmatter。"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return text


def build(out_path):
    if not SKILL_MD.exists():
        sys.exit(f"找不到 {SKILL_MD}")

    chunks = [HEADER, strip_frontmatter(SKILL_MD.read_text(encoding="utf-8")).strip(), "\n\n---\n\n"]

    existing = {p.name for p in REF_DIR.glob("*.md")}
    missing = [n for n in ORDER if n not in existing]
    extra = sorted(existing - set(ORDER))

    for name in ORDER:
        p = REF_DIR / name
        if not p.exists():
            print(f"  ! 跳过（不存在）：{name}")
            continue
        body = p.read_text(encoding="utf-8")
        body = re.sub(r"^# ", "## ", body, count=1, flags=re.M)   # 降一级，保持文档层级
        chunks.append(body.strip())
        chunks.append("\n\n---\n\n")

    for name in extra:                                            # 索引里没提到的一并带上
        p = REF_DIR / name
        body = re.sub(r"^# ", "## ", p.read_text(encoding="utf-8"), count=1, flags=re.M)
        chunks.append(body.strip())
        chunks.append("\n\n---\n\n")
        print(f"  · 附加未列入索引的文档：{name}")

    text = "".join(chunks).rstrip() + "\n"
    out_path.write_text(text, encoding="utf-8")
    kb = out_path.stat().st_size / 1024
    print(f"saved: {out_path}  ({kb:.0f} KB, {len(text.splitlines())} 行)")
    if missing:
        print("  提示：索引里列出但文件不存在 →", ", ".join(missing))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SKILL_DIR / "strategy-full.md"))
    build(pathlib.Path(ap.parse_args().out))
