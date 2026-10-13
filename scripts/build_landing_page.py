#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「详情页（落地页）」：竖版长页，结构照原生落地页模板。

结构：首屏痛点（4 个痛点气泡围绕人物）→ 品牌区（4 个能力块）→ 覆盖行业网格
      → 选择我们的理由 → 留资表单 → 底部备案

输出：
  landing/详情页.html       —— 可直接打开/发布的长页
  landing/详情页-长图.png   —— 整页长图（750 × 自动高度），用于预览与后台配图

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
WIDTH = 750
FONT = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'

# ---------------------------------------------------------------- 内容（改这里即可）
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
    """裁掉底部水印后转 base64。"""
    im = Image.open(SRC / "pain_man.png").convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, int(h * 0.90)))          # 去掉右下角水印
    im = im.resize((int(im.width * 0.78), int(im.height * 0.78)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def build_html():
    img = pain_img()
    pain_left = PAINS[0::2]
    pain_right = PAINS[1::2]

    def card(p, side, top):
        return f"""<div class="pcard {side}" style="top:{top}px">
          <div class="pt">{p[0]}</div><div class="pd">{p[1]}</div></div>"""

    pains_html = (
        card(pain_left[0], "left", 0) + card(pain_right[0], "right", 12) +
        card(pain_left[1], "left", 246) + card(pain_right[1], "right", 236)
    )
    abil = "".join(
        f"""<div class="ab">
          <div class="abn">{n}</div>
          <div class="abt">{t}</div><div class="abd">{d}</div>
        </div>""" for n, t, d in ABILITIES
    )
    inds = "".join(f'<div class="ind">{i}</div>' for i in INDUSTRIES)
    reasons = "".join(
        f"""<div class="rs">
          <div class="rsb"><span>{a}</span><em>{b}</em></div>
          <div class="rsd">{c}</div>
        </div>""" for a, b, c in REASONS
    )

    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:750px;background:#EEF3F9;font-family:__FONT__;color:__INK__;
  -webkit-font-smoothing:antialiased}
.page{width:750px;overflow:hidden;background:
  linear-gradient(180deg,#DCE9F7 0%,#EDF4FB 22%,#F6F9FC 46%,#EEF4FA 74%,#E6EEF7 100%)}

/* 通用 */
.sec{padding:0 34px}
.tag{display:inline-block;font-size:22px;font-weight:700;letter-spacing:.12em;color:__ACCENT__}
.h2{font-size:46px;font-weight:800;line-height:1.24;letter-spacing:-.01em}
.h2 em{font-style:normal;color:__ACCENT__}
.sub{font-size:26px;color:#5A6B80;line-height:1.6}
.mark{display:inline-block;width:34px;height:4px;border-radius:2px;background:__ACCENT__;
  vertical-align:middle;margin-right:14px}

/* 一、首屏 + 痛点 */
.hero{padding-top:52px;text-align:center}
.hero .h2{font-size:44px;margin-top:16px}
.hero .sub{margin-top:18px}
.painbox{position:relative;height:706px;margin-top:34px}
.person{position:absolute;left:50%;transform:translateX(-50%);bottom:0;width:392px;
  border-radius:26px;overflow:hidden;
  box-shadow:0 30px 60px -30px rgba(22,35,58,.42)}
.person img{display:block;width:100%}
.pcard{position:absolute;width:246px;padding:20px 20px 22px;border-radius:20px;
  background:rgba(255,255,255,.86);border:1px solid rgba(255,255,255,.9);
  backdrop-filter:blur(8px);box-shadow:0 16px 34px -18px rgba(31,60,102,.40)}
.pcard.left{left:0} .pcard.right{right:0}
.pcard::after{content:"";position:absolute;width:14px;height:14px;background:inherit;
  border-radius:3px;transform:rotate(45deg)}
.pcard.left::after{right:-6px;top:44px} .pcard.right::after{left:-6px;top:44px}
.pt{font-size:28px;font-weight:800;color:__ACCENT__}
.pd{font-size:22px;color:#4A5A70;line-height:1.55;margin-top:8px}

/* 二、品牌区 + 能力块 */
.brand{margin-top:58px;text-align:center}
.logo{display:inline-flex;align-items:center;gap:12px;font-size:30px;font-weight:800;
  color:__INK__;background:#fff;padding:14px 28px;border-radius:999px;
  box-shadow:0 12px 28px -14px rgba(31,60,102,.35)}
.logo i{width:34px;height:34px;border-radius:11px;display:block;
  background:linear-gradient(135deg,__ACCENT__,__ACCENT2__)}
.brand .h2{margin-top:24px;font-size:48px}
.brand .sub{margin-top:16px}
.abs{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:36px}
.ab{background:#fff;border-radius:20px;padding:24px 22px 26px;
  box-shadow:0 16px 34px -22px rgba(31,60,102,.40);border:1px solid #fff}
.abn{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,__ACCENT__,__ACCENT2__);
  color:#fff;font-size:26px;font-weight:800;display:flex;align-items:center;justify-content:center}
.abt{font-size:28px;font-weight:800;margin-top:16px}
.abd{font-size:22px;color:#5A6B80;line-height:1.55;margin-top:8px}

/* 三、行业覆盖 */
.sec-title{text-align:center;margin-top:64px}
.sec-title .h2{font-size:44px;margin-top:12px}
.inds{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:32px}
.ind{height:132px;border-radius:18px;display:flex;align-items:center;justify-content:center;
  font-size:25px;font-weight:700;color:#fff;letter-spacing:.02em;
  background:linear-gradient(150deg,#3E5B84,#22344F);
  box-shadow:0 14px 28px -18px rgba(22,35,58,.55)}
.ind:nth-child(3n+2){background:linear-gradient(150deg,#4A6B99,#2C3F5C)}
.ind:nth-child(3n+3){background:linear-gradient(150deg,#56789F,#33476A)}

/* 四、选择理由 */
.rss{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:32px}
.rs{background:#fff;border-radius:20px;padding:26px 24px 28px;text-align:center;
  box-shadow:0 16px 34px -22px rgba(31,60,102,.40);border:1px solid #fff}
.rsb{font-size:30px;font-weight:800;line-height:1.3}
.rsb em{font-style:normal;display:block;color:__ACCENT__;margin-top:4px}
.rsd{font-size:21px;color:#5A6B80;line-height:1.55;margin-top:12px}

/* 五、表单 */
.formwrap{margin-top:64px;padding:0 34px 34px}
.form{background:#fff;border-radius:26px;padding:36px 30px 38px;
  box-shadow:0 24px 50px -28px rgba(31,60,102,.45)}
.form .h2{font-size:38px;text-align:center}
.form .sub{text-align:center;margin-top:12px;font-size:23px}
.field{margin-top:20px;background:#F4F6F9;border-radius:14px;padding:22px 24px;
  display:flex;align-items:center;justify-content:space-between;font-size:26px;color:#93A0B0}
.field .fill{font-size:24px;color:__ACCENT__;font-weight:600;border-left:1px solid #E1E7EE;padding-left:22px}
.agree{display:flex;align-items:flex-start;gap:12px;margin-top:22px;font-size:21px;color:#5A6B80;line-height:1.5}
.box{width:30px;height:30px;border-radius:7px;border:2px solid #C6D0DC;flex:0 0 30px;margin-top:2px}
.box.on{border-color:__ACCENT__;background:__ACCENT__;position:relative}
.box.on::after{content:"";position:absolute;left:9px;top:5px;width:8px;height:14px;
  border-right:3px solid #fff;border-bottom:3px solid #fff;transform:rotate(42deg)}
.submit{margin-top:26px;height:92px;border-radius:16px;background:linear-gradient(135deg,#D8451F,__ACCENT__);
  color:#fff;font-size:32px;font-weight:800;letter-spacing:.06em;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 18px 34px -18px rgba(216,69,31,.65)}
.foot{margin-top:26px;text-align:center;font-size:20px;color:#7C8A9B;line-height:1.7;padding-bottom:40px}
.foot b{font-weight:600;color:#5A6B80}
""".replace("__FONT__", FONT).replace("__INK__", INK).replace("__ACCENT2__", ACCENT_2) \
   .replace("__ACCENT__", ACCENT)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=750">
<title>IMAI · AI 投放营销 · 详情页</title>
<style>{css}</style></head>
<body><div class="page">

  <!-- 一、首屏 + 痛点 -->
  <section class="sec hero">
    <div class="tag">IMAI · AI 投放营销</div>
    <div class="h2">还在花钱买线索的老板，<em>注意了</em></div>    <div class="sub">广告费花出去了，是不是卡在这四件事？</div>
    <div class="painbox">
      <div class="person"><img src="{img}" alt=""></div>
      {pains_html}
    </div>
  </section>

  <!-- 二、品牌区 + 能力块 -->
  <section class="sec brand">
    <div class="logo"><i></i>IMAI · AI 投放营销</div>
    <div class="h2">让 AI <em>替你投广告</em></div>
    <div class="sub">腾讯广告同一账户体系 · 名单导进去，AI 自动跑</div>
    <div class="abs">{abil}</div>
  </section>

  <!-- 三、行业覆盖 -->
  <section class="sec sec-title">
    <div class="tag"><span class="mark"></span>覆盖各类企业需求</div>
    <div class="h2">只要有名单，就能跑起来</div>
    <div class="inds">{inds}</div>
  </section>

  <!-- 四、选择理由 -->
  <section class="sec sec-title">
    <div class="tag"><span class="mark"></span>选择我们的理由</div>
    <div class="h2">便宜、精准、可控</div>
    <div class="rss">{reasons}</div>
  </section>

  <!-- 五、留资表单 -->
  <section class="formwrap">
    <div class="form">
      <div class="h2">先算一遍，再决定</div>
      <div class="sub">留个联系方式，1 对 1 帮你算投放账</div>
      <div class="field"><span>姓名</span></div>
      <div class="field"><span>手机号</span><span class="fill">一键填写</span></div>
      <div class="field"><span>贵公司名称</span></div>
      <div class="agree"><span class="box"></span>
        <span>授权并同意《个人信息与隐私保护条款》，同意将信息用于本次咨询与后续服务联系</span></div>
      <div class="submit">预约 1 对 1 演示</div>
    </div>
    <div class="foot">
      页面信息及服务由 <b>IMAI · AI 投放营销</b> 提供<br>
      本页图片含 AI 生成示意素材，仅用于版式说明
    </div>
  </section>

</div></body></html>"""


def main():
    html = build_html()
    page_path = OUT / "详情页.html"
    page_path.write_text(html, encoding="utf-8")
    print("saved:", page_path)

    long_png = OUT / "详情页-长图.png"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": WIDTH, "height": 1400},
                           device_scale_factor=2).new_page()
        pg.goto(page_path.as_uri())
        pg.wait_for_timeout(900)
        h = pg.evaluate("document.querySelector('.page').getBoundingClientRect().height")
        pg.set_viewport_size({"width": WIDTH, "height": int(h)})
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(long_png), full_page=True)
        b.close()
    print("saved:", long_png, Image.open(long_png).size)


if __name__ == "__main__":
    main()
