#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「后台配图」：每个版式最多 2 张（A/B 两版，各打一个不同人群）。

- 横版 16:9（1920×1080）→ **详情页首屏配图**：人设条 → 复述钩子 → 主利益 → 三个卖点 → 信任条
- 竖版 9:16（1080×1920）→ **钩子海报**：痛点钩子 → 主视觉 → 三个卖点 → 人设收口

做法：HTML 排版 + Playwright 精确截图。背景图由 spec 指定（图像生成得来），
A/B **复用同一张背景图 → 零额外积分**。

用法：
    python3 build_ad_assets.py --spec assets_spec.json
    python3 build_ad_assets.py --spec assets_spec.json --out /abs/output/dir

spec 结构见 references/html-delivery.md 第二节。输出默认写到**当前工作目录**下的
`assets/`（不再写进技能目录）：
    assets/后台配图-16x9-A.png、-16x9-B.png、-9x16-A.png、-9x16-B.png
"""
import argparse
import base64
import io
import json
import os
import pathlib
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'
DEFAULT_ACCENT = "#FF8A3D"

# spec 里用户必须给全的字段（缺了直接报错，别默默出一张错图）
REQUIRED_VARIANT = ("hook", "big", "rule", "points", "kicker",
                    "tall_hook", "tall_big", "tall_small", "tall_points")


def die(msg):
    sys.exit("spec 有误：" + msg)


def load_spec(path):
    p = pathlib.Path(path)
    if not p.exists():
        die(f"找不到 spec 文件 {p}")
    spec = json.loads(p.read_text(encoding="utf-8"))

    for key in ("person", "variants"):
        if key not in spec:
            die(f"缺少顶层字段 `{key}`")
    for key in ("name", "role", "initial"):
        if key not in spec["person"]:
            die(f"`person` 缺少 `{key}`")
    if not spec.get("brand"):
        die("缺少 `brand`（横版右下角 / 竖版顶部品牌名）")

    variants = spec["variants"]
    if not isinstance(variants, dict) or not variants:
        die("`variants` 必须是非空对象，键为 A / B")
    if len(variants) > 2:
        die(f"`variants` 最多 2 个（A/B），当前给了 {len(variants)} 个")

    for k, v in variants.items():
        missing = [f for f in REQUIRED_VARIANT if f not in v]
        if missing:
            die(f"变体 {k} 缺少字段：{', '.join(missing)}")
        for f in ("hook", "big", "tall_hook", "tall_big"):
            if len(v[f]) != 2:
                die(f"变体 {k} 的 `{f}` 必须是 2 个元素的数组（前段 / 强调段）")

    # 背景图：顶层默认，变体可覆盖
    for k, v in variants.items():
        v.setdefault("bg_wide", spec.get("bg_wide"))
        v.setdefault("bg_tall", spec.get("bg_tall"))
        for which in ("bg_wide", "bg_tall"):
            if not v.get(which):
                die(f"变体 {k} 缺少背景图 `{which}`（可写在变体里，或写在顶层做默认）")
            if not pathlib.Path(v[which]).exists():
                die(f"变体 {k} 的 `{which}` 指向的文件不存在：{v[which]}")
    return spec


def data_uri(path, target_w, target_h, focus=(0.5, 0.5)):
    """按目标比例 cover 裁切 + 转 base64。"""
    im = Image.open(path).convert("RGB")
    tr = target_w / target_h
    w, h = im.size
    if w / h > tr:
        nw = int(h * tr)
        left = int((w - nw) * focus[0])
        im = im.crop((left, 0, left + nw, h))
    else:
        nh = int(w / tr)
        top = int((h - nh) * focus[1])
        im = im.crop((0, top, w, top + nh))
    scale = max(1.0, (target_w * 2) / im.width)
    if scale > 1:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------- 16:9 详情页首屏
def html_wide(bg, v, cfg, accent):
    pts = "".join(f'<div class="li"><span class="dot"></span>{p}</div>' for p in v["points"])
    trust = "".join(f"<span>{t}</span>" for t in cfg["trust"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden}}
body{{font-family:{FONT};background:#0d1420}}
.stage{{position:relative;width:1920px;height:1080px;overflow:hidden}}
.bg{{position:absolute;inset:0;background:url('{bg}') center/cover no-repeat}}
.shade{{position:absolute;inset:0;background:
  linear-gradient(90deg,rgba(9,14,22,.97) 0%,rgba(9,14,22,.93) 38%,rgba(9,14,22,.62) 58%,rgba(9,14,22,.10) 80%,rgba(9,14,22,.28) 100%)}}
.glow{{position:absolute;left:-180px;top:-240px;width:920px;height:920px;border-radius:50%;
  background:radial-gradient(circle,{accent}30 0%,transparent 68%)}}
.box{{position:absolute;left:112px;top:92px;width:1010px;color:#fff}}
.who{{display:flex;align-items:center;gap:18px;margin-bottom:42px}}
.avatar{{width:74px;height:74px;border-radius:50%;background:{accent};display:flex;align-items:center;
  justify-content:center;font-size:33px;font-weight:800;color:#161d26;flex:0 0 74px}}
.wname{{font-size:29px;font-weight:700;line-height:1.2}}
.wrole{{font-size:20px;color:#9fadbe;margin-top:5px}}
.hook{{font-size:37px;color:#c2cddb;font-weight:600}}
.hook b{{color:#fff}}
h1{{margin-top:14px;font-size:100px;line-height:1.1;font-weight:800;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:{accent}}}
h1 .br{{font-size:74px}}
.rule{{margin-top:22px;font-size:34px;color:#e3eaf3;font-weight:600}}
.list{{margin-top:46px;display:flex;flex-direction:column;gap:15px}}
.li{{display:flex;align-items:center;gap:16px;font-size:28px;color:#f0f4f9;font-weight:600}}
.dot{{width:11px;height:11px;border-radius:50%;background:{accent};flex:0 0 11px}}
.trust{{position:absolute;left:112px;right:112px;bottom:62px;display:flex;align-items:center;
  justify-content:space-between;padding-top:24px;border-top:1px solid rgba(255,255,255,.18)}}
.tleft{{display:flex;gap:30px;font-size:21px;color:#c3cedd;font-weight:500}}
.tleft span::before{{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;
  background:{accent};margin-right:10px;vertical-align:middle}}
.tright{{font-size:21px;color:#8d9aab;letter-spacing:.06em}}
</style></head><body><div class="stage">
  <div class="bg"></div><div class="shade"></div><div class="glow"></div>
  <div class="box">
    <div class="who">
      <div class="avatar">{cfg['person']['initial']}</div>
      <div><div class="wname">{cfg['person']['name']}</div><div class="wrole">{cfg['person']['role']}</div></div>
    </div>
    <div class="hook">{v['hook'][0]}<b>{v['hook'][1]}</b></div>
    <h1><em>{v['big'][0]}</em><span class="br"> {v['big'][1]}</span></h1>
    <div class="rule">{v['rule']}</div>
    <div class="list">{pts}</div>
  </div>
  <div class="trust">
    <div class="tleft">{trust}</div>
    <div class="tright">{cfg['brand']}</div>
  </div>
</div></body></html>"""


# ------------------------------------------------- 9:16 钩子海报
def html_tall(bg, v, cfg, accent):
    pts = "".join(f'<div class="li"><span class="dot"></span>{p}</div>' for p in v["tall_points"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden}}
body{{font-family:{FONT};background:#0d1420}}
.stage{{position:relative;width:1080px;height:1920px;overflow:hidden}}
.bg{{position:absolute;inset:0;background:url('{bg}') center 28%/cover no-repeat}}
.shade{{position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(9,14,22,.94) 0%,rgba(9,14,22,.70) 18%,rgba(9,14,22,.16) 36%,
  rgba(9,14,22,.34) 52%,rgba(9,14,22,.87) 68%,rgba(9,14,22,.97) 100%)}}
.top{{position:absolute;left:78px;top:84px;right:78px;color:#fff}}
.eyebrow{{font-size:26px;letter-spacing:.2em;color:{accent};font-weight:700}}
h2{{margin-top:28px;font-size:76px;line-height:1.18;font-weight:800;letter-spacing:-.02em}}
.hook{{position:absolute;left:78px;right:78px;top:1078px;color:#fff}}
.kicker{{display:inline-block;font-size:25px;font-weight:700;color:#12181f;background:{accent};
  padding:10px 22px;border-radius:8px;letter-spacing:.04em}}
.big{{margin-top:28px;font-size:98px;line-height:1.1;font-weight:800;letter-spacing:-.03em}}
.big em{{font-style:normal;color:{accent}}}
.bigsmall{{margin-top:20px;font-size:38px;color:#e7edf5;font-weight:600;line-height:1.4}}
.list{{margin-top:46px;display:flex;flex-direction:column;gap:16px}}
.li{{display:flex;align-items:center;gap:16px;font-size:31px;color:#fff;font-weight:600}}
.dot{{width:12px;height:12px;border-radius:50%;background:{accent};flex:0 0 12px}}
.foot{{position:absolute;left:78px;right:78px;bottom:92px;display:flex;align-items:center;
  justify-content:space-between;color:#fff}}
.who{{display:flex;align-items:center;gap:18px}}
.avatar{{width:78px;height:78px;border-radius:50%;background:{accent};display:flex;align-items:center;
  justify-content:center;font-size:36px;font-weight:800;color:#161d26}}
.fname{{font-size:30px;font-weight:700}} .frole{{font-size:20px;color:#a9b6c7;margin-top:3px}}
.brand{{font-size:22px;color:#8d9aab;letter-spacing:.06em;text-align:right}}
.rule{{position:absolute;left:78px;right:78px;bottom:226px;height:1px;background:rgba(255,255,255,.16)}}
</style></head><body><div class="stage">
  <div class="bg"></div><div class="shade"></div>
  <div class="top">
    <div class="eyebrow">{cfg['brand']}</div>
    <h2>{v['tall_hook'][0]}<br>{v['tall_hook'][1]}</h2>
  </div>
  <div class="hook">
    <div class="kicker">{v['kicker']}</div>
    <div class="big"><em>{v['tall_big'][0]}</em><br>{v['tall_big'][1]}</div>
    <div class="bigsmall">{v['tall_small']}</div>
    <div class="list">{pts}</div>
  </div>
  <div class="rule"></div>
  <div class="foot">
    <div class="who">
      <div class="avatar">{cfg['person']['initial']}</div>
      <div><div class="fname">{cfg['person']['name']}</div><div class="frole">{cfg['person']['role']}</div></div>
    </div>
    <div class="brand">{cfg.get('brand_foot', '')}</div>
  </div>
</div></body></html>"""


def sanity_check_css(html):
    """CSS 静默失效自查。

    ⚠️ 一个未闭合的引号会让 CSS 解析器把其后所有规则当成字符串吞掉，
    版面全乱但**不报任何错**（踩过：FONT 常量末尾多一个 `"`）。
    这里对即将送进浏览器的 HTML 先卡一道。
    """
    m = re.search(r"<style>(.*?)</style>", html, re.S)
    if not m:
        die("生成的 HTML 里找不到 <style> 块")
    css = m.group(1)
    nq = css.count('"')
    if nq % 2:
        die(f"CSS 双引号数量为奇数（{nq} 个），整段样式会被浏览器丢弃——检查 FONT 等拼接常量")
    if css.count("{") != css.count("}"):
        die(f"CSS 花括号不配对：{css.count('{')} 个 {{ / {css.count('}')} 个 }}")
    left = re.findall(r"__[A-Z0-9_]+__", css)
    if left:
        die(f"CSS 里还有未替换的占位符：{sorted(set(left))}")


def shot(pw, html, out, w, h):
    sanity_check_css(html)
    tmp = out.parent / "_tmp.html"
    tmp.write_text(html, encoding="utf-8")
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1).new_page()
    pg.goto(tmp.as_uri())
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
    b.close()
    tmp.unlink(missing_ok=True)
    size = Image.open(out).size
    if size != (w, h):
        sys.exit(f"❌ {out.name} 尺寸是 {size[0]}×{size[1]}，应为 {w}×{h}")
    print("saved:", out, size)


def main():
    ap = argparse.ArgumentParser(description="后台配图（16:9 详情页配图 + 9:16 钩子海报）")
    ap.add_argument("--spec", required=True, help="assets_spec.json 路径")
    ap.add_argument("--out", default=None, help="输出目录（默认 <当前工作目录>/assets）")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    out_dir = pathlib.Path(args.out) if args.out else (spec.get("out_dir") or pathlib.Path.cwd() / "assets")
    out_dir = pathlib.Path(out_dir)
    if not out_dir.exists():
        os.makedirs(out_dir)

    accent = spec.get("accent", DEFAULT_ACCENT)
    cfg = {"person": spec["person"], "brand": spec["brand"],
           "brand_foot": spec.get("brand_foot", ""), "trust": spec.get("trust", [])}
    if not cfg["trust"]:
        print("提示：未提供 `trust`，横版底部信任条将为空")

    for old in out_dir.glob("后台配图-*.png"):
        old.unlink()

    with sync_playwright() as pw:
        for k, v in spec["variants"].items():
            fw = v.get("focus_wide", spec.get("focus_wide", [0.62, 0.40]))
            ft = v.get("focus_tall", spec.get("focus_tall", [0.5, 0.30]))
            bg_wide = data_uri(v["bg_wide"], 1920, 1080, focus=tuple(fw))
            bg_tall = data_uri(v["bg_tall"], 1080, 1920, focus=tuple(ft))
            shot(pw, html_wide(bg_wide, v, cfg, accent), out_dir / f"后台配图-16x9-{k}.png", 1920, 1080)
            shot(pw, html_tall(bg_tall, v, cfg, accent), out_dir / f"后台配图-9x16-{k}.png", 1080, 1920)
    print(f"\n✅ 后台配图已输出到 {out_dir}")


if __name__ == "__main__":
    main()
