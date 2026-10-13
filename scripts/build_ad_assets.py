#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「后台配图」：每个版式最多 2 张（A/B 两版，各打一个不同人群）。

- 横版 16:9（1920×1080）→ **详情页首屏配图**：人设条 → 复述钩子 → 主利益 → 三个卖点 → 信任条
- 竖版 9:16（1080×1920）→ **钩子海报**：痛点钩子 → 主视觉 → 三个卖点 → 人设收口

输出：assets/后台配图-16x9-A.png、-16x9-B.png、-9x16-A.png、-9x16-B.png
用法：python3 build_ad_assets.py
"""
import base64
import io
import os
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
SRC = HERE / "assets_src"
OUT = HERE / "assets"
# 注意：沙箱下对已存在目录调用 mkdir(exist_ok=True) 仍会抛 EEXIST，必须先判断
if not OUT.exists():
    os.makedirs(OUT)

ACCENT = "#FF8A3D"
FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'

PERSON = {"name": "陈斯克", "role": "AI 营销实战讲师", "initial": "陈"}
BRAND = "IMAI · AI 投放营销"

# A 版 = 中小企业老板（获客成本焦虑）；B 版 = 实体门店老板（存量会员沉睡）
VARIANTS = {
    "A": {
        "hook": ("广告费花了，", "客户一个没来？"),
        "big": ("3分钱", "一次曝光"),
        "rule": "看到才扣，没看到不扣",
        "points": ["名单导进去就能投", "成交一个，停投一个", "覆盖 15 个腾讯系点位"],
        "kicker": "AI 自动投放",
        "tall_hook": ("广告费花了，", "客户没来？"),
        "tall_big": ("3分钱", "一次曝光"),
        "tall_small": "看到才扣，没看到不扣",
        "tall_points": ["名单导进去就能投", "成交一个，停投一个", "覆盖 15 个腾讯系点位"],
    },
    "B": {
        "hook": ("店里几千个会员，", "还睡着？"),
        "big": ("成交一个", "停投一个"),
        "rule": "名单导进去，AI 替你天天跟",
        "points": ["老客自己回店预约", "不用群发，不用打电话", "3分钱一次曝光"],
        "kicker": "老客唤醒",
        "tall_hook": ("老客户为什么，", "不再来了？"),
        "tall_big": ("名单导进去", "就能投"),
        "tall_small": "不用群发，不用打电话",
        "tall_points": ["老客自己回店预约", "成交一个，停投一个", "3分钱一次曝光"],
    },
}


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
def html_wide(bg, v):
    pts = "".join(f'<div class="li"><span class="dot"></span>{p}</div>' for p in v["points"])
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1920px;height:1080px;overflow:hidden}}
body{{font-family:{FONT};background:#0d1420}}
.stage{{position:relative;width:1920px;height:1080px;overflow:hidden}}
.bg{{position:absolute;inset:0;background:url('{bg}') center/cover no-repeat}}
.shade{{position:absolute;inset:0;background:
  linear-gradient(90deg,rgba(9,14,22,.97) 0%,rgba(9,14,22,.93) 38%,rgba(9,14,22,.62) 58%,rgba(9,14,22,.10) 80%,rgba(9,14,22,.28) 100%)}}
.glow{{position:absolute;left:-180px;top:-240px;width:920px;height:920px;border-radius:50%;
  background:radial-gradient(circle,{ACCENT}30 0%,transparent 68%)}}
.box{{position:absolute;left:112px;top:92px;width:1010px;color:#fff}}
.who{{display:flex;align-items:center;gap:18px;margin-bottom:42px}}
.avatar{{width:74px;height:74px;border-radius:50%;background:{ACCENT};display:flex;align-items:center;
  justify-content:center;font-size:33px;font-weight:800;color:#161d26;flex:0 0 74px}}
.wname{{font-size:29px;font-weight:700;line-height:1.2}}
.wrole{{font-size:20px;color:#9fadbe;margin-top:5px}}
.hook{{font-size:37px;color:#c2cddb;font-weight:600}}
.hook b{{color:#fff}}
h1{{margin-top:14px;font-size:100px;line-height:1.1;font-weight:800;letter-spacing:-.02em}}
h1 em{{font-style:normal;color:{ACCENT}}}
h1 .br{{font-size:74px}}
.rule{{margin-top:22px;font-size:34px;color:#e3eaf3;font-weight:600}}
.list{{margin-top:46px;display:flex;flex-direction:column;gap:15px}}
.li{{display:flex;align-items:center;gap:16px;font-size:28px;color:#f0f4f9;font-weight:600}}
.dot{{width:11px;height:11px;border-radius:50%;background:{ACCENT};flex:0 0 11px}}
.trust{{position:absolute;left:112px;right:112px;bottom:62px;display:flex;align-items:center;
  justify-content:space-between;padding-top:24px;border-top:1px solid rgba(255,255,255,.18)}}
.tleft{{display:flex;gap:30px;font-size:21px;color:#c3cedd;font-weight:500}}
.tleft span::before{{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;
  background:{ACCENT};margin-right:10px;vertical-align:middle}}
.tright{{font-size:21px;color:#8d9aab;letter-spacing:.06em}}
</style></head><body><div class="stage">
  <div class="bg"></div><div class="shade"></div><div class="glow"></div>
  <div class="box">
    <div class="who">
      <div class="avatar">{PERSON['initial']}</div>
      <div><div class="wname">{PERSON['name']}</div><div class="wrole">{PERSON['role']}</div></div>
    </div>
    <div class="hook">{v['hook'][0]}<b>{v['hook'][1]}</b></div>
    <h1><em>{v['big'][0]}</em><span class="br"> {v['big'][1]}</span></h1>
    <div class="rule">{v['rule']}</div>
    <div class="list">{pts}</div>
  </div>
  <div class="trust">
    <div class="tleft"><span>腾讯广告同一账户体系</span><span>正规开户通道</span></div>
    <div class="tright">{BRAND}</div>
  </div>
</div></body></html>"""


# ------------------------------------------------- 9:16 钩子海报
def html_tall(bg, v):
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
.eyebrow{{font-size:26px;letter-spacing:.2em;color:{ACCENT};font-weight:700}}
h2{{margin-top:28px;font-size:76px;line-height:1.18;font-weight:800;letter-spacing:-.02em}}
.hook{{position:absolute;left:78px;right:78px;top:1078px;color:#fff}}
.kicker{{display:inline-block;font-size:25px;font-weight:700;color:#12181f;background:{ACCENT};
  padding:10px 22px;border-radius:8px;letter-spacing:.04em}}
.big{{margin-top:28px;font-size:98px;line-height:1.1;font-weight:800;letter-spacing:-.03em}}
.big em{{font-style:normal;color:{ACCENT}}}
.bigsmall{{margin-top:20px;font-size:38px;color:#e7edf5;font-weight:600;line-height:1.4}}
.list{{margin-top:46px;display:flex;flex-direction:column;gap:16px}}
.li{{display:flex;align-items:center;gap:16px;font-size:31px;color:#fff;font-weight:600}}
.dot{{width:12px;height:12px;border-radius:50%;background:{ACCENT};flex:0 0 12px}}
.foot{{position:absolute;left:78px;right:78px;bottom:92px;display:flex;align-items:center;
  justify-content:space-between;color:#fff}}
.who{{display:flex;align-items:center;gap:18px}}
.avatar{{width:78px;height:78px;border-radius:50%;background:{ACCENT};display:flex;align-items:center;
  justify-content:center;font-size:36px;font-weight:800;color:#161d26}}
.fname{{font-size:30px;font-weight:700}} .frole{{font-size:20px;color:#a9b6c7;margin-top:3px}}
.brand{{font-size:22px;color:#8d9aab;letter-spacing:.06em;text-align:right}}
.rule{{position:absolute;left:78px;right:78px;bottom:226px;height:1px;background:rgba(255,255,255,.16)}}
</style></head><body><div class="stage">
  <div class="bg"></div><div class="shade"></div>
  <div class="top">
    <div class="eyebrow">{BRAND}</div>
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
      <div class="avatar">{PERSON['initial']}</div>
      <div><div class="fname">{PERSON['name']}</div><div class="frole">{PERSON['role']}</div></div>
    </div>
    <div class="brand">腾讯广告<br>同一账户体系</div>
  </div>
</div></body></html>"""


def shot(pw, html, out, w, h):
    tmp = OUT / "_tmp.html"
    tmp.write_text(html, encoding="utf-8")
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1).new_page()
    pg.goto(tmp.as_uri())
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
    b.close()
    tmp.unlink(missing_ok=True)
    print("saved:", out.name, Image.open(out).size)


def main():
    bg_wide = data_uri(SRC / "bg_wide.png", 1920, 1080, focus=(0.55, 0.42))
    bg_tall = data_uri(SRC / "bg_tall.png", 1080, 1920, focus=(0.5, 0.30))
    # 先清掉旧命名，避免混淆
    for old in OUT.glob("后台配图-*.png"):
        old.unlink()
    with sync_playwright() as pw:
        for k, v in VARIANTS.items():
            shot(pw, html_wide(bg_wide, v), OUT / f"后台配图-16x9-{k}.png", 1920, 1080)
            shot(pw, html_tall(bg_tall, v), OUT / f"后台配图-9x16-{k}.png", 1080, 1920)


if __name__ == "__main__":
    main()
