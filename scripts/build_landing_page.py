#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「详情页（落地页）」：**两张 9:16**（1080×1920），上屏 + 下屏。

- 上屏：钩子 + 4 个痛点围绕人物 → 品牌区（Logo + 主口号）
- 下屏：4 个能力块 → 行业覆盖 12 格 → 选择理由 2×2
- 两屏共用同一套浅蓝→白渐变与橙色点缀，**前后色调呼应、可无缝连排**
- 不做留资表单（走投放后台的【表单】/【商家微信】组件）

输出：
  landing/详情页.html              —— 两屏叠放的页面（可直接打开）
  landing/详情页-上屏-9x16.png      —— 1080 × 1920
  landing/详情页-下屏-9x16.png      —— 1080 × 1920

配套提示词只有 2 条，见 landing_prompts.json。
用法：python3 build_landing_page.py
"""
import base64
import io
import os
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
SRC = HERE / "assets_src"
OUT = HERE / "landing"
if not OUT.exists():
    os.makedirs(OUT)

ACCENT = "#E8722F"
ACCENT_2 = "#FF9A52"
INK = "#16233A"
W, H = 1080, 1920
FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'

PAINS = [
    ("获客成本高", "投流越投越贵，钱是按「动作」花的，不是按「结果」花的"),
    ("同行内卷", "几百个同行同一天说一样的话，平台一眼就识破"),
    ("不敢试新渠道", "怕投进去打水漂，一次次错过窗口期"),
    ("没人跟得住", "业务员跟三次就放弃，客户第 30 天才想起来"),
]
ABILITIES = [
    ("1", "让 AI 替你找人", "名单导进去，自动建模定向"),
    ("2", "让 AI 替你投放", "0.03元一次曝光，看到才扣"),
    ("3", "让 AI 替你跟单", "每天出现一次，跟满 60 天"),
    ("4", "让 AI 替你复盘", "每一笔花在哪，后台都看得见"),
]
INDUSTRIES = ["餐饮门店", "美业连锁", "教育培训", "家装建材", "汽车服务", "健身运动",
              "本地生活", "电商零售", "批发贸易", "制造工业", "连锁加盟", "企业服务"]
REASONS = [
    ("0.03元", "一次曝光", "看到才扣，没看到不扣"),
    ("成交一个", "停投一个", "不打扰老客户，也不多花钱"),
    ("15 个", "腾讯系点位", "手机、电脑、大屏都能刷到"),
    ("你只出", "一份名单", "诊断、素材、开户我们走"),
]


def pain_img():
    im = Image.open(SRC / "pain_man.png").convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, int(h * 0.90)))              # 去掉右下角水印
    im = im.resize((int(im.width * 1.05), int(im.height * 1.05)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


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


def build_html():
    img = pain_img()
    left, right = PAINS[0::2], PAINS[1::2]

    def pcard(p, side, top):
        return (f'<div class="pcard {side}" style="top:{top}px">'
                f'<div class="pt">{p[0]}</div><div class="pd">{p[1]}</div></div>')

    pains = (pcard(left[0], "left", 0) + pcard(right[0], "right", 18) +
             pcard(left[1], "left", 330) + pcard(right[1], "right", 316))
    abil = "".join(f'<div class="ab"><div class="abn">{n}</div>'
                   f'<div class="abt">{t}</div><div class="abd">{d}</div></div>'
                   for n, t, d in ABILITIES)
    inds = "".join(f'<div class="ind">{i}</div>' for i in INDUSTRIES)
    reasons = "".join(f'<div class="rs"><div class="rsb"><span>{a}</span>'
                      f'<em>{b}</em></div><div class="rsd">{c}</div></div>'
                      for a, b, c in REASONS)
    css = CSS.replace("__FONT__", FONT).replace("__ACCENT2__", ACCENT_2).replace("__ACCENT__", ACCENT)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=1080">
<title>IMAI · AI 投放营销 · 详情页（两屏 9:16）</title>
<style>{css}</style></head>
<body>

<!-- ===== 上屏（第一张 9:16）===== -->
<div class="screen" id="s1">
  <div class="pad s1-head">
    <div class="tag">IMAI · AI 投放营销</div>
    <div class="h1">还在花钱买线索的老板，<em>注意了</em></div>
    <div class="sub">广告费花出去了，是不是卡在这四件事？</div>
  </div>
  <div class="pad painbox" style="padding-left:46px;padding-right:46px">
    <div class="person"><img src="{img}" alt=""></div>
    {pains}
  </div>
  <div class="brand">
    <div class="logo"><i></i>IMAI · AI 投放营销</div>
    <div class="h2">让 AI <em>替你投广告</em></div>
    <div class="sub">腾讯广告同一账户体系 · 名单导进去，AI 自动跑</div>
  </div>
</div>

<!-- ===== 下屏（第二张 9:16）===== -->
<div class="screen s2" id="s2">
  <div class="pad">
    <div class="abs">{abil}</div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>覆盖各类企业需求</div>
      <div class="h2">只要有名单，就能跑起来</div>
      <div class="inds">{inds}</div>
    </div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>选择我们的理由</div>
      <div class="h2">便宜、精准、可控</div>
      <div class="rss">{reasons}</div>
    </div>
  </div>
  <!-- 留资表单：不做进图；表单/隐私勾选/提交按钮走投放后台的【表单】/【商家微信】组件 -->
</div>

</body></html>"""


def main():
    page_path = OUT / "详情页.html"
    page_path.write_text(build_html(), encoding="utf-8")
    print("saved:", page_path)

    shots = [("s1", "详情页-上屏-9x16.png"), ("s2", "详情页-下屏-9x16.png")]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1).new_page()
        pg.goto(page_path.as_uri())
        pg.wait_for_timeout(1000)
        for sid, name in shots:
            el = pg.locator(f"#{sid}")
            el.screenshot(path=str(OUT / name))
            print("saved:", OUT / name, Image.open(OUT / name).size)
        b.close()


if __name__ == "__main__":
    main()
