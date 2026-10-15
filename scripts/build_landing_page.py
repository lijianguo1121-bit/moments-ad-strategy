#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「详情页（落地页）」：**两张 9:16**（1080×1920），上屏 + 下屏。

- 上屏：钩子 + 4 个痛点围绕人物 → 品牌区（Logo + 主口号）
- 下屏：4 个能力块 → 区域覆盖 12 格 → 选择理由 2×2
- 两屏共用同一套浅蓝→白渐变与橙色点缀，**前后色调呼应、可无缝连排**
- 不做留资表单（走投放后台的【表单】/【商家微信】组件）

用法：
    python3 build_landing_page.py --spec landing_spec.json
    python3 build_landing_page.py --spec landing_spec.json --out /abs/landing/dir

spec 结构见 references/html-delivery.md 第三节。输出默认写到**当前工作目录**下的
`landing/`（不再写进技能目录）：
    landing/详情页.html                 —— 两屏叠放的页面（可直接打开）
    landing/详情页-上屏-9x16.png         —— 1080 × 1920
    landing/详情页-下屏-9x16.png         —— 1080 × 1920

配套提示词只有 2 条，见 landing_prompts.json。
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

ACCENT_DEFAULT = "#E8722F"
ACCENT2_DEFAULT = "#FF9A52"
INK_DEFAULT = "#16233A"
W, H = 1080, 1920
FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'


def die(msg):
    sys.exit("spec 有误：" + msg)


def load_spec(path):
    p = pathlib.Path(path)
    if not p.exists():
        die(f"找不到 spec 文件 {p}")
    spec = json.loads(p.read_text(encoding="utf-8"))

    s1, s2 = spec.get("screen1"), spec.get("screen2")
    if not isinstance(s1, dict):
        die("缺少 `screen1`")
    if not isinstance(s2, dict):
        die("缺少 `screen2`")

    for key in ("tag", "title", "subtitle", "pains", "brand_logo", "brand_title", "brand_sub"):
        if key not in s1:
            die(f"`screen1` 缺少 `{key}`")
    if len(s1["title"]) != 2:
        die("`screen1.title` 必须是 2 个元素的数组（前段 / 强调段）")
    if len(s1["brand_title"]) != 2:
        die("`screen1.brand_title` 必须是 2 个元素的数组")
    if len(s1["pains"]) != 4:
        die(f"`screen1.pains` 必须正好 4 条（版面是按 4 张痛点卡定位的），当前 {len(s1['pains'])} 条")
    for i, pit in enumerate(s1["pains"]):
        if not (isinstance(pit, (list, tuple)) and len(pit) == 2):
            die(f"`screen1.pains[{i}]` 必须是 [标题, 说明] 两个元素")

    for key in ("abilities", "area_tag", "area_title", "areas",
                "reason_tag", "reason_title", "reasons"):
        if key not in s2:
            die(f"`screen2` 缺少 `{key}`")
    if len(s2["abilities"]) != 4:
        die(f"`screen2.abilities` 必须正好 4 条，当前 {len(s2['abilities'])} 条")
    for i, ab in enumerate(s2["abilities"]):
        if not (isinstance(ab, (list, tuple)) and len(ab) == 3):
            die(f"`screen2.abilities[{i}]` 必须是 [序号, 标题, 说明] 三个元素")
    if len(s2["reasons"]) != 4:
        die(f"`screen2.reasons` 必须正好 4 条（2×2 版式），当前 {len(s2['reasons'])} 条")
    for i, rs in enumerate(s2["reasons"]):
        if not (isinstance(rs, (list, tuple)) and len(rs) == 3):
            die(f"`screen2.reasons[{i}]` 必须是 [主词, 副词, 说明] 三个元素")
    if len(s2["areas"]) % 3 != 0:
        print(f"提示：`screen2.areas` 有 {len(s2['areas'])} 项，3 列网格会留下空位（推荐 12 项）")

    # 人物图可选：没有就跳过人物块（不崩）
    pi = s1.get("person_image")
    if pi and not pathlib.Path(pi).exists():
        print(f"提示：`screen1.person_image` 指向的文件不存在（{pi}），本次不放人物图")
        s1["person_image"] = None
    return spec


def person_uri(path, crop_bottom):
    """人物图裁切 + 转 base64。

    crop_bottom < 1.0 会裁掉底部（旧做法用它去掉生成水印）——⚠️ 若用的是 AI 生成人物图，
    **不要靠裁图去掉「AI 生成」标注**，那属于刻意规避标注；改用实拍，或保留标注。
    默认 1.0（不裁）。
    """
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if crop_bottom < 1.0:
        im = im.crop((0, 0, w, int(h * crop_bottom)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def sanity_check_css(css):
    """CSS 静默失效自查。

    ⚠️ 一个未闭合的引号会让 CSS 解析器把**其后所有规则**当成字符串吞掉，
    表现是「同一条规则里 width 生效、height 消失」——版面全乱但不报任何错。
    （本脚本踩过：FONT 常量末尾多一个 `"`，导致 .screen 的 height:1920px 失效，
    截图出来只有 1298px 高。）所以出图前后都卡一道。
    """
    nq = css.count('"')
    if nq % 2:
        die(f"CSS 双引号数量为奇数（{nq} 个），整段样式会被浏览器丢弃——检查 FONT 等拼接常量")
    if css.count("{") != css.count("}"):
        die(f"CSS 花括号不配对：{css.count('{')} 个 {{ / {css.count('}')} 个 }}")
    left = re.findall(r"__[A-Z0-9_]+__", css)
    if left:
        die(f"CSS 里还有未替换的占位符：{sorted(set(left))}")


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#E9EFF6;font-family:__FONT__;color:__INK__;-webkit-font-smoothing:antialiased}
.screen{position:relative;width:1080px;height:1920px;overflow:hidden;
  background:linear-gradient(180deg,#DCE9F7 0%,#EDF4FB 34%,#F6F9FC 62%,#EEF4FA 100%)}
.screen + .screen{margin-top:40px}
.pad{padding:0 62px}
.tag{display:inline-block;font-size:26px;font-weight:700;letter-spacing:.14em;color:__ACCENT__}
.h1{font-size:68px;font-weight:800;line-height:1.22;letter-spacing:-.015em}
.h1 em{font-style:normal;color:__ACCENT__}
.h2{font-size:56px;font-weight:800;line-height:1.24;letter-spacing:-.01em}
.h2 em{font-style:normal;color:__ACCENT__}
.sub{font-size:31px;color:#54657C;line-height:1.55}
.mark{display:inline-block;width:44px;height:5px;border-radius:3px;background:__ACCENT__;
  vertical-align:middle;margin-right:18px}

/* 上屏 */
.s1-head{padding-top:96px;text-align:center}
.s1-head .h1{margin-top:26px}
.s1-head .sub{margin-top:24px}
.painbox{position:relative;height:940px;margin-top:44px}
.person{position:absolute;left:50%;transform:translateX(-50%);bottom:0;width:620px;
  border-radius:36px;overflow:hidden;box-shadow:0 42px 84px -42px rgba(22,35,58,.46)}
.person img{display:block;width:100%}
.pcard{position:absolute;width:372px;padding:30px 30px 32px;border-radius:28px;
  background:rgba(255,255,255,.88);border:1px solid rgba(255,255,255,.92);
  box-shadow:0 22px 46px -24px rgba(31,60,102,.42)}
.pcard.left{left:0} .pcard.right{right:0}
.pt{font-size:39px;font-weight:800;color:__ACCENT__}
.pd{font-size:28px;color:#47586E;line-height:1.55;margin-top:12px}

.brand{position:absolute;left:62px;right:62px;bottom:138px;text-align:center}
.logo{display:inline-flex;align-items:center;gap:16px;font-size:38px;font-weight:800;
  background:#fff;padding:20px 38px;border-radius:999px;
  box-shadow:0 16px 38px -18px rgba(31,60,102,.38)}
.logo i{width:44px;height:44px;border-radius:14px;display:block;
  background:linear-gradient(135deg,__ACCENT__,__ACCENT2__)}
.brand .h2{margin-top:34px;font-size:60px}
.brand .sub{margin-top:20px}

/* 下屏 */
.s2{padding-top:74px}
.abs{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:0}
.ab{background:#fff;border-radius:24px;padding:26px 26px 28px;
  box-shadow:0 20px 44px -28px rgba(31,60,102,.42);border:1px solid #fff}
.abn{width:52px;height:52px;border-radius:16px;background:linear-gradient(135deg,__ACCENT__,__ACCENT2__);
  color:#fff;font-size:30px;font-weight:800;display:flex;align-items:center;justify-content:center}
.abt{font-size:33px;font-weight:800;margin-top:16px}
.abd{font-size:25px;color:#54657C;line-height:1.5;margin-top:8px}

.blk{margin-top:44px;text-align:center}
.inds{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.ind{height:106px;border-radius:20px;display:flex;align-items:center;justify-content:center;
  font-size:29px;font-weight:700;color:#fff;letter-spacing:.02em;
  background:linear-gradient(150deg,#3E5B84,#22344F);
  box-shadow:0 16px 32px -20px rgba(22,35,58,.55)}
.ind:nth-child(3n+2){background:linear-gradient(150deg,#4A6B99,#2C3F5C)}
.ind:nth-child(3n+3){background:linear-gradient(150deg,#56789F,#33476A)}

.rss{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:28px}
.rs{background:#fff;border-radius:24px;padding:26px 24px 28px;text-align:center;
  box-shadow:0 20px 44px -28px rgba(31,60,102,.42);border:1px solid #fff}
.rsb{font-size:35px;font-weight:800;line-height:1.28}
.rsb em{font-style:normal;display:block;color:__ACCENT__;margin-top:4px;font-size:32px}
.rsd{font-size:24px;color:#54657C;line-height:1.5;margin-top:12px}
"""


def build_html(spec, person_data_uri):
    s1, s2 = spec["screen1"], spec["screen2"]
    accent = spec.get("accent", ACCENT_DEFAULT)
    accent2 = spec.get("accent2", ACCENT2_DEFAULT)
    ink = spec.get("ink", INK_DEFAULT)

    def pcard(p, side, top):
        return (f'<div class="pcard {side}" style="top:{top}px">'
                f'<div class="pt">{p[0]}</div><div class="pd">{p[1]}</div></div>')

    pains = (pcard(s1["pains"][0], "left", 0) + pcard(s1["pains"][1], "right", 18) +
             pcard(s1["pains"][2], "left", 330) + pcard(s1["pains"][3], "right", 316))
    abil = "".join(f'<div class="ab"><div class="abn">{n}</div>'
                   f'<div class="abt">{t}</div><div class="abd">{d}</div></div>'
                   for n, t, d in s2["abilities"])
    inds = "".join(f'<div class="ind">{i}</div>' for i in s2["areas"])
    reasons = "".join(f'<div class="rs"><div class="rsb"><span>{a}</span>'
                      f'<em>{b}</em></div><div class="rsd">{c}</div></div>'
                      for a, b, c in s2["reasons"])

    person = (f'<div class="person"><img src="{person_data_uri}" alt=""></div>'
              if person_data_uri else "")
    css = (CSS.replace("__FONT__", FONT).replace("__ACCENT2__", accent2)
              .replace("__ACCENT__", accent).replace("__INK__", ink))
    sanity_check_css(css)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=1080">
<title>{spec.get('page_title', '详情页（两屏 9:16）')}</title>
<style>{css}</style></head>
<body>

<!-- ===== 上屏（第一张 9:16）===== -->
<div class="screen" id="s1">
  <div class="pad s1-head">
    <div class="tag">{s1['tag']}</div>
    <div class="h1">{s1['title'][0]}<em>{s1['title'][1]}</em></div>
    <div class="sub">{s1['subtitle']}</div>
  </div>
  <div class="pad painbox" style="padding-left:46px;padding-right:46px">
    {person}
    {pains}
  </div>
  <div class="brand">
    <div class="logo"><i></i>{s1['brand_logo']}</div>
    <div class="h2">{s1['brand_title'][0]}<em>{s1['brand_title'][1]}</em></div>
    <div class="sub">{s1['brand_sub']}</div>
  </div>
</div>

<!-- ===== 下屏（第二张 9:16）===== -->
<div class="screen s2" id="s2">
  <div class="pad">
    <div class="abs">{abil}</div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>{s2['area_tag']}</div>
      <div class="h2">{s2['area_title']}</div>
      <div class="inds">{inds}</div>
    </div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>{s2['reason_tag']}</div>
      <div class="h2">{s2['reason_title']}</div>
      <div class="rss">{reasons}</div>
    </div>
  </div>
  <!-- 留资表单：不做进图；表单/隐私勾选/提交按钮走投放后台的【表单】/【商家微信】组件 -->
</div>

</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="详情页（落地页）两屏 9:16")
    ap.add_argument("--spec", required=True, help="landing_spec.json 路径")
    ap.add_argument("--out", default=None, help="输出目录（默认 <当前工作目录>/landing）")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    out_dir = pathlib.Path(args.out) if args.out else pathlib.Path(spec.get("out_dir") or pathlib.Path.cwd() / "landing")
    if not out_dir.exists():
        os.makedirs(out_dir)

    person_data_uri = None
    if spec["screen1"].get("person_image"):
        person_data_uri = person_uri(spec["screen1"]["person_image"],
                                     spec["screen1"].get("person_crop_bottom", 1.0))

    page_path = out_dir / "详情页.html"
    page_path.write_text(build_html(spec, person_data_uri), encoding="utf-8")
    print("saved:", page_path)

    shots = [("s1", "详情页-上屏-9x16.png"), ("s2", "详情页-下屏-9x16.png")]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1).new_page()
        pg.goto(page_path.as_uri())
        pg.wait_for_timeout(1000)
        for sid, name in shots:
            el = pg.locator(f"#{sid}")
            el.screenshot(path=str(out_dir / name))
            size = Image.open(out_dir / name).size
            if size != (W, H):
                b.close()
                sys.exit(f"❌ {name} 尺寸是 {size[0]}×{size[1]}，应为 {W}×{H}。\n"
                         f"   多半是 CSS 没生效（见 sanity_check_css 的说明），检查 .screen 规则是否被丢弃。")
            print("saved:", out_dir / name, size)
        b.close()
    print(f"\n✅ 详情页已输出到 {out_dir}")


if __name__ == "__main__":
    main()
