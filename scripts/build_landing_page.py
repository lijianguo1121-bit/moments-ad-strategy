#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「详情页（落地页）」：**两张 9:16**（1080×1920），上屏 + 下屏。

客户：银川 · 老徐装饰装修（摩恩卫浴）
- 上屏：钩子 + 4 个痛点围绕人物 → 品牌区（Logo + 主口号）
- 下屏：4 个能力块 → 区域覆盖 12 格 → 选择理由 2×2
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
    ("买贵了", "同款差价能到一半，你不知道"),
    ("买到假货", "不是标着牌子的都是正品"),
    ("装得不专业", "漏水返味，多半是安装的问题"),
    ("没人管售后", "装完两年出问题，找谁都不认"),
]
ABILITIES = [
    ("1", "先上门看现场", "尺寸、水压、排水一次看明白"),
    ("2", "帮你验货", "进货凭证和包装当场核对"),
    ("3", "帮你盯安装", "下料、安装、验收我都到"),
    ("4", "出问题我上门", "不推给厂家，我先去"),
]
AREAS = ["兴庆区", "金凤区", "西夏区", "贺兰县", "永宁县", "灵武市",
         "新交房小区", "二手房翻新", "老房换卫浴", "全屋整装", "局部改造", "商铺工装"]
REASONS = [
    ("30年", "店一直在这儿", "在银川做装修卫浴，没换过地方"),
    ("签约价", "即结算价", "增项先签字，不临时加钱"),
    ("自己师傅", "不外包", "装完出问题，我上门"),
    ("现货", "就在店里", "仓库有货，可当场看实物"),
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
    inds = "".join(f'<div class="ind">{i}</div>' for i in AREAS)
    reasons = "".join(f'<div class="rs"><div class="rsb"><span>{a}</span>'
                      f'<em>{b}</em></div><div class="rsd">{c}</div></div>'
                      for a, b, c in REASONS)
    css = CSS.replace("__FONT__", FONT).replace("__ACCENT2__", ACCENT_2).replace("__ACCENT__", ACCENT)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=1080">
<title>银川装修老徐 · 详情页（两屏 9:16）</title>
<style>{css}</style></head>
<body>

<!-- ===== 上屏（第一张 9:16）===== -->
<div class="screen" id="s1">
  <div class="pad s1-head">
    <div class="tag">银川 · 老徐装饰装修</div>
    <div class="h1">装完了出问题，<em>你还找得到人吗</em></div>
    <div class="sub">在银川做装修卫浴30年，店就在这儿</div>
  </div>
  <div class="pad painbox" style="padding-left:46px;padding-right:46px">
    <div class="person"><img src="{img}" alt=""></div>
    {pains}
  </div>
  <div class="brand">
    <div class="logo"><i></i>银川装修老徐</div>
    <div class="h2">装了30年，<em>出问题我上门</em></div>
    <div class="sub">银川本地门店 · 自己的师傅 · 签约价即结算价</div>
  </div>
</div>

<!-- ===== 下屏（第二张 9:16）===== -->
<div class="screen s2" id="s2">
  <div class="pad">
    <div class="abs">{abil}</div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>银川这些地方我们都跑</div>
      <div class="h2">兴庆金凤西夏，都能上门</div>
      <div class="inds">{inds}</div>
    </div>

    <div class="blk">
      <div class="tag"><span class="mark"></span>为什么找老徐</div>
      <div class="h2">30年、本地、自己人</div>
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
