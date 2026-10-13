#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把投放策略方案 + 合规审核报告 + 文案 + 效果图，组装成一个自包含 HTML 交付页。

用法：
  python3 build_report_html.py --config build.json

build.json 结构：
{
  "title": "朋友圈广告投放策略方案",
  "brand": "IMAI · AI 投放营销",
  "persona": "陈斯克",
  "out": "/abs/path/交付页.html",
  "docs": [
    {"key": "plan", "label": "投放策略方案", "path": "投放策略方案-XXX.md"},
    {"key": "audit", "label": "合规审核报告", "path": "合规审核报告-XXX.md"}
  ],
  "copy_spec": "copy_spec_compliant.json",
  "effects": [
    {"image": "ad_effects/x.png", "caption": "文案 1 · 广告费花了，客户没来"}
  ]
}
"""
import argparse
import base64
import html as _html
import io
import json
import os
import re

import markdown
from PIL import Image

ACCENT = "#e8743b"
NAVY = "#16233a"


def esc(s):
    return _html.escape(str(s), quote=True)


def md_to_html(text, prefix):
    """Markdown → HTML，并给标题 id 加前缀避免多文档冲突。"""
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
        extension_configs={"toc": {"slugify": lambda v, s: prefix + "-" + re.sub(r"[^\w\u4e00-\u9fff]+", "-", v).strip("-")}},
    )
    body = md.convert(text)
    return body, md.toc_tokens


def img_to_data_uri(path, max_w=760, quality=86):
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def collect_level(tokens, level=2):
    """toc_tokens 是嵌套结构，递归收集指定层级的标题。"""
    out = []
    for t in tokens:
        if t["level"] == level:
            out.append(t)
        if t.get("children"):
            out.extend(collect_level(t["children"], level))
    return out


def build(config_path):
    base = os.path.dirname(os.path.abspath(config_path))
    cfg = json.load(open(config_path, encoding="utf-8"))

    def P(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    # ---------- 文档 ----------
    doc_sections, nav_docs = [], []
    for i, doc in enumerate(cfg["docs"]):
        raw = open(P(doc["path"]), encoding="utf-8").read()
        body, tokens = md_to_html(raw, doc["key"])
        doc_sections.append(
            f'<section class="doc" id="sec-{doc["key"]}"><h1 class="sec-title">{esc(doc["label"])}</h1>{body}</section>'
        )
        subs = collect_level(tokens, 2)
        nav_docs.append({"key": doc["key"], "label": doc["label"], "subs": subs})

    # ---------- 文案卡（外层文案 / 详情页文案 共用） ----------
    def make_cards(spec_path, start_idx, unit="文案"):
        spec = json.load(open(P(spec_path), encoding="utf-8"))
        ads = spec["ads"]
        cards, blocks = [], []
        for i, ad in enumerate(ads, 1):
            idx = start_idx + i - 1
            chips = ""
            if ad.get("formula"):
                chips += f'<span class="chip chip-f">{esc(ad["formula"])}</span>'
            if ad.get("plan"):
                chips += f'<span class="chip chip-p">{esc(ad["plan"])}</span>'
            lines = "".join(f'<div class="cl">{esc(l)}</div>' for l in ad["copy"])
            dazi = "".join(
                f'<span style="color:{ACCENT};font-weight:700">{esc(s["t"])}</span>' if s.get("accent")
                else f'<span>{esc(s["t"])}</span>'
                for s in ad.get("dazi", [])
            )
            total = sum(len(x) for x in ad["copy"])
            note = f'<div class="cnote">{esc(ad["note"])}</div>' if ad.get("note") else ""
            btn_copy = "复制文案" if unit == "文案" else "复制这一套"
            cards.append(f"""
      <article class="ccard">
        <div class="chead">
          <div class="cno">{ad.get("no", i)}</div>
          <div><div class="ctitle">{unit} {ad.get("no", i)}</div><div class="chips">{chips}</div></div>
          <div class="cmeta">{total} 字</div>
        </div>
        <div class="cbox">{lines}</div>
        <div class="cdazi">大字：{dazi}</div>
        {note}
        <div class="cbtns">
          <button class="btn btn-p" data-i="{idx}" data-k="copy">{btn_copy}</button>
          <button class="btn" data-i="{idx}" data-k="dazi">复制大字</button>
          <button class="btn" data-i="{idx}" data-k="all">复制含说明全部</button>
        </div>
      </article>""")
            blocks.append({
                "copy": "\n".join(ad["copy"]),
                "dazi": "".join(s["t"] for s in ad.get("dazi", [])),
                "all": "\n".join(
                    [f"【{unit} {ad.get('no', i)}】"]
                    + ([f"{ad['formula']}"] if ad.get("formula") else [])
                    + ([f"归属：{ad['plan']}"] if ad.get("plan") else [])
                    + ad["copy"]
                    + ([f"大字：{''.join(s['t'] for s in ad.get('dazi', []))}"] if ad.get("dazi") else [])
                    + ([f"说明：{ad['note']}"] if ad.get("note") else [])
                ),
            })
        return cards, blocks

    cards, copy_data = make_cards(cfg["copy_spec"], 0, "文案")
    detail_cards, detail_blocks = [], []
    if cfg.get("detail_spec"):
        detail_cards, detail_blocks = make_cards(cfg["detail_spec"], len(copy_data), "方案")
    all_blocks = copy_data + detail_blocks

    # ---------- 效果图 ----------
    gal = []
    for e in cfg.get("effects", []):
        uri = img_to_data_uri(P(e["image"]))
        gal.append(f"""
      <figure class="shot">
        <img src="{uri}" alt="{esc(e['caption'])}" loading="lazy">
        <figcaption>{esc(e['caption'])}</figcaption>
      </figure>""")

    # ---------- 后台配图 ----------
    assets = cfg.get("assets", [])
    asset_cards = []
    for a in assets:
        uri = img_to_data_uri(P(a["image"]), max_w=a.get("max_w", 1180), quality=88)
        rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in a.get("spec", {}).items())
        asset_cards.append(f"""
      <article class="acard">
        <div class="atitle">{esc(a['title'])}<span class="aratio">{esc(a.get('ratio',''))}</span></div>
        <figure class="aframe"><img src="{uri}" alt="{esc(a['title'])}" loading="lazy" class="zoom"></figure>
        <table class="aspec">{rows}</table>
        <div class="anote">{esc(a.get('note',''))}</div>
      </article>""")

    # ---------- 详情页（落地页） ----------
    landing = cfg.get("landing")
    landing_html = ""
    if landing:
        paths = landing.get("images") or ([landing["image"]] if landing.get("image") else [])
        frames = "".join(
            f'<figure class="lframe"><img src="{img_to_data_uri(P(p), max_w=landing.get("max_w", 560), quality=84)}"'
            f' alt="{esc(os.path.basename(p))}" loading="lazy" class="zoom"></figure>'
            for p in paths
        )
        rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in landing.get("spec", {}).items())
        landing_html = f"""
    <section id="sec-landing" class="block">
      <h2 class="sec-title">六、详情页（落地页）</h2>
      <p style="color:var(--sub);font-size:13.5px;margin-top:0">
        详情页做成<strong>两张 9:16</strong>（上屏 + 下屏，可上下连排），两屏共用同一套色调。
        页面文件见 <code>landing/详情页.html</code>。点图可放大。
      </p>
      <!--PROMPT_SLOT-->""" + (
            f"""
      <div class="lscreens" style="grid-template-columns:repeat({len(paths)},1fr)">{frames}</div>
      <div class="lside" style="position:static;margin-top:20px">
        <table class="aspec">{rows}</table>
        <div class="anote">{esc(landing.get('note',''))}</div>
      </div>""" if paths else "") + """
    </section>"""

    # ---------- 详情页 · 文生图提示词 ----------
    prompt_html, prompt_data, prompt_copy_all = "", [], []
    if cfg.get("landing_prompts"):
        pdata = json.load(open(P(cfg["landing_prompts"]), encoding="utf-8"))
        items = pdata.get("items", [])
        g_order, g_map = [], {}
        for it in items:
            g = it.get("group", "")
            if g not in g_map:
                g_map[g] = []
                g_order.append(g)
            g_map[g].append(it)
        idx, secs = 0, []
        for g in g_order:
            pcards = []          # 注意：不要复用 cards 这个名字，否则会覆盖外层文案卡
            for it in g_map[g]:
                cp = it.get("copy") or []
                cp_plain = "\n".join(f'{c.get("label", "")}：{c.get("text", "")}' for c in cp)
                whole = "\n".join(
                    [f'【{it.get("slot", "")}】', it["prompt"], ""]
                    + ([f'—— 这一屏要写的文案（{len(cp)} 处）——']
                       + [f'{c.get("label", "")}：{c.get("text", "")}' for c in cp] if cp else []))
                prompt_data.append({"p": it["prompt"], "c": cp_plain, "a": whole})
                if cp_plain:
                    prompt_copy_all.append(f'【{it.get("slot", "")} · 文案】\n{cp_plain}')

                pnote = f'<div class="pnote">{esc(it["note"])}</div>' if it.get("note") else ""
                cp_html, extra = "", ""
                if cp:
                    rows = "".join(
                        f'<div class="cprow"><span class="cplabel">{esc(c.get("label", ""))}</span>'
                        f'<span class="cptext">{esc(c.get("text", ""))}</span></div>' for c in cp)
                    cp_html = (f'<div class="copysec"><div class="copysec-t">'
                               f'这一屏要写的文案（{len(cp)} 处）</div>'
                               f'<div class="cprows">{rows}</div></div>')
                    extra = (f'<button class="btn" data-pc="{idx}">复制这一屏文案</button>'
                             f'<button class="btn" data-pa="{idx}">复制整屏</button>')
                pcards.append(f"""
          <article class="pcard">
            <div class="phead"><span class="pslot">{esc(it.get('slot',''))}</span>
              <span class="psize">{esc(it.get('size',''))}</span></div>
            <div class="pbox">{esc(it['prompt'])}</div>
            {pnote}
            {cp_html}
            <div class="cbtns"><button class="btn btn-p" data-p="{idx}">复制提示词</button>{extra}</div>
          </article>""")
                idx += 1
            secs.append(f'<h4 class="pgroup">{esc(g)}</h4><div class="cgrid">{"".join(pcards)}</div>')
        rules = "".join(f"<li>{esc(r)}</li>" for r in pdata.get("rules", []))
        copy_all_btn = ('<button class="btn" data-p-copy-all="1">复制全部落地页文案</button>'
                        if prompt_copy_all else "")
        prompt_html = f"""
      <h3 class="sub-title">配图提示词 + 该屏文案（{len(items)} 条 · 都可一键复制）</h3>
      <p style="color:var(--sub);font-size:13.5px;margin:0 0 14px">
        每条 = <strong>AI 出「视觉底」的提示词</strong> + <strong>这一屏实际要写的文案</strong>。
        图片只当背景（提示词里不要求 AI 写中文），文字与卡片一律用 HTML/CSS 叠上去。
        两者常交给不同的人做（生图的 / 排版的），所以分开给、分别可复制。
      </p>
      <div style="margin-bottom:16px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-p" data-p-all="1">复制全部 {len(items)} 条提示词</button>
        {copy_all_btn}
      </div>
      {''.join(secs)}
      <blockquote style="margin-top:18px"><strong>通用规范</strong><ul style="margin:8px 0 0;padding-left:20px">{rules}</ul></blockquote>
      <h3 class="sub-title" style="margin-top:34px">详情页两屏图（9:16）</h3>"""

    if prompt_html:
        if landing_html and "<!--PROMPT_SLOT-->" in landing_html:
            landing_html = landing_html.replace("<!--PROMPT_SLOT-->", prompt_html, 1)
        else:
            landing_html = (f'<section id="sec-landing" class="block">'
                            f'<h2 class="sec-title">六、详情页（落地页）</h2>{prompt_html}</section>')

    # ---------- 导航 ----------
    groups = [("概览", "sec-overview", []),
              ("可投放文案", "sec-copy", [])]
    if detail_cards:
        groups.append(("详情页文案（5 套）", "sec-detail", []))
    groups += [("广告效果图", "sec-shots", [])]
    if asset_cards:
        groups.append(("后台配图（素材）", "sec-assets", []))
    if landing:
        groups.append(("详情页（落地页）", "sec-landing", []))
    for nd in nav_docs:
        groups.append((nd["label"], f'sec-{nd["key"]}', nd["subs"]))
    groups.append(("交付清单", "sec-deliver", []))

    nav_html = []
    for label, anchor, subs in groups:
        sub_html = "".join(
            f'<a class="nav-sub" href="#{esc(s["id"])}">{esc(s["name"])}</a>' for s in subs
        )
        nav_html.append(
            f'<div class="nav-g"><a class="nav-top" href="#{anchor}">{esc(label)}</a>{sub_html}</div>'
        )

    total_ads = len(copy_data)
    total_detail = len(detail_blocks)
    total_shots = len(cfg.get("effects", []))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(cfg['title'])} · {esc(cfg['brand'])}</title>
<style>
  :root {{
    --accent:{ACCENT}; --navy:{NAVY}; --ink:#1b1f24; --sub:#6b7280;
    --line:#e6e8ec; --bg:#f6f7f9; --card:#fff;
  }}
  *{{box-sizing:border-box}}
  html{{scroll-behavior:smooth}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
    -webkit-font-smoothing:antialiased;line-height:1.7}}
  a{{color:inherit;text-decoration:none}}

  /* 顶部 */
  .hero{{background:linear-gradient(135deg,#16233a 0%,#22344f 55%,#2c3f5c 100%);color:#fff;
    padding:44px 40px 38px}}
  .hero .brand{{font-size:13px;letter-spacing:.14em;color:#f0a878;font-weight:700}}
  .hero h1{{margin:10px 0 8px;font-size:32px;letter-spacing:-.01em;line-height:1.3}}
  .hero p{{margin:0;color:#c3cddb;font-size:14px}}
  .kpis{{display:flex;gap:14px;flex-wrap:wrap;margin-top:26px}}
  .kpi{{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);
    border-radius:12px;padding:12px 18px;min-width:132px}}
  .kpi b{{display:block;font-size:24px;line-height:1.2}}
  .kpi span{{font-size:12px;color:#b9c5d6}}

  /* 布局 */
  .layout{{display:flex;align-items:flex-start;max-width:1400px;margin:0 auto;gap:0}}
  .side{{position:sticky;top:0;width:250px;flex:0 0 250px;height:100vh;overflow:auto;
    padding:22px 14px 60px;border-right:1px solid var(--line);background:var(--bg)}}
  .side::-webkit-scrollbar{{width:6px}} .side::-webkit-scrollbar-thumb{{background:#d3d8e0;border-radius:3px}}
  .nav-g{{margin-bottom:14px}}
  .nav-top{{display:block;font-weight:700;font-size:13.5px;padding:7px 10px;border-radius:8px}}
  .nav-top:hover{{background:#eceef2}}
  .nav-sub{{display:block;font-size:12.5px;color:var(--sub);padding:4px 10px 4px 20px;
    border-left:2px solid transparent;border-radius:0 6px 6px 0}}
  .nav-sub:hover{{color:var(--accent);background:#fff5f0}}
  .main{{flex:1;min-width:0;padding:28px 34px 90px}}

  section{{scroll-margin-top:20px}}
  .sec-title{{font-size:22px;margin:0 0 4px}}
  .block{{background:var(--card);border:1px solid var(--line);border-radius:16px;
    padding:26px 30px;margin-bottom:22px;
    box-shadow:0 1px 2px rgba(16,24,40,.04),0 10px 28px -20px rgba(16,24,40,.22)}}

  /* 文案卡 */
  .cgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px}}
  .ccard{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
  .chead{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
  .cno{{width:34px;height:34px;flex:0 0 34px;border-radius:50%;background:var(--accent);color:#fff;
    font-weight:700;display:flex;align-items:center;justify-content:center;font-size:15px}}
  .ctitle{{font-size:14px;font-weight:700}}
  .chips{{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}}
  .chip{{font-size:11px;padding:2px 8px;border-radius:99px;background:#eef0f3;color:#4b5563}}
  .chip-f{{background:rgba(232,116,59,.11);color:#c2542a}}
  .chip-p{{background:#e8f0fe;color:#2f5bd0}}
  .cmeta{{margin-left:auto;font-size:11.5px;color:var(--sub)}}
  .cbox{{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#fbfbfc}}
  .cl{{font-size:16px;line-height:1.85;font-weight:500}}
  .cdazi{{margin-top:10px;font-size:12.5px;color:var(--sub)}}
  .cnote{{margin-top:8px;font-size:12px;color:var(--sub);line-height:1.6;
    background:#f8f9fb;border-radius:8px;padding:8px 10px}}
  .cbtns{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}

  .btn{{appearance:none;border:1px solid var(--line);background:#fff;color:#374151;font-size:12.5px;
    padding:6px 13px;border-radius:8px;cursor:pointer;font-family:inherit;transition:.15s}}
  .btn:hover{{border-color:#c9ced6;background:#fafbfc}}
  .btn-p{{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}}
  .btn-p:hover{{filter:brightness(1.06);background:var(--accent)}}

  /* 效果图 */
  .gal{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}}
  .shot{{margin:0;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden}}
  .shot img{{display:block;width:100%;cursor:zoom-in}}
  .shot figcaption{{font-size:12.5px;color:var(--sub);padding:10px 14px 14px}}

  /* Markdown 正文 */
  .doc h1{{display:none}}
  .doc h2{{font-size:20px;margin:34px 0 10px;padding-top:8px;border-top:1px solid var(--line)}}
  .doc h2:first-of-type{{border-top:none;margin-top:0}}
  .doc h3{{font-size:16px;margin:22px 0 8px}}
  .doc h4{{font-size:14.5px;margin:18px 0 6px;color:#374151}}
  .doc p{{margin:10px 0}}
  .doc ul,.doc ol{{margin:10px 0;padding-left:22px}}
  .doc li{{margin:4px 0}}
  .doc blockquote{{margin:12px 0;padding:12px 16px;background:#f8f9fb;border-left:3px solid var(--accent);
    border-radius:0 10px 10px 0;color:#374151;font-size:13.5px}}
  .doc blockquote p{{margin:5px 0}}
  .doc table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px}}
  .doc th,.doc td{{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}}
  .doc th{{background:#f3f5f8;font-weight:700;white-space:nowrap}}
  .doc tr:nth-child(even) td{{background:#fcfcfd}}
  .doc code{{background:#f1f3f6;padding:1px 6px;border-radius:5px;font-size:12.5px;
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
  .doc pre{{background:#1e2733;color:#e6edf5;padding:14px 16px;border-radius:10px;overflow:auto;font-size:12.5px}}
  .doc pre code{{background:none;color:inherit;padding:0}}
  .doc hr{{border:none;border-top:1px solid var(--line);margin:26px 0}}
  .doc strong{{color:#111}}
  .doc table code{{white-space:nowrap}}

  /* 后台配图 */
  .agrid{{display:grid;grid-template-columns:1.55fr 1fr;gap:22px;align-items:start}}
  .acard{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 16px 18px}}
  .atitle{{font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px;margin-bottom:12px}}
  .aratio{{font-size:11px;font-weight:600;color:#c2542a;background:rgba(232,116,59,.11);
    padding:2px 8px;border-radius:99px}}
  .aframe{{margin:0;border-radius:10px;overflow:hidden;background:#0d1420;line-height:0}}
  .aframe img{{display:block;width:100%;cursor:zoom-in}}
  .aspec{{width:100%;border-collapse:collapse;margin-top:14px;font-size:12.5px}}
  .aspec th{{text-align:left;color:var(--sub);font-weight:600;padding:5px 0;width:78px;
    border-bottom:1px solid #f2f4f7;vertical-align:top}}
  .aspec td{{padding:5px 0;border-bottom:1px solid #f2f4f7;color:#374151}}
  .anote{{margin-top:12px;font-size:12.5px;color:var(--sub);line-height:1.65}}
  @media (max-width:1000px){{.agrid{{grid-template-columns:1fr}}}}

  /* 详情页（两屏 9:16） */
  .lscreens{{display:grid;gap:20px;margin-top:6px;align-items:start}}
  .lframe{{margin:0;border-radius:14px;overflow:hidden;border:1px solid var(--line);line-height:0;background:#fff}}
  .lframe img{{display:block;width:100%;cursor:zoom-in}}
  .lside{{position:static}}
  @media (max-width:700px){{.lscreens{{grid-template-columns:1fr !important}}}}

  /* 文生图提示词 */
  .sub-title{{font-size:16px;margin:34px 0 0;padding-left:10px;border-left:4px solid var(--accent)}}
  .pgroup{{font-size:14px;margin:22px 0 12px;color:#374151}}
  .pcard{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
  .phead{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}}
  .pslot{{font-size:13.5px;font-weight:700}}
  .psize{{font-size:11px;color:var(--sub);background:#eef0f3;padding:2px 8px;border-radius:99px;white-space:nowrap}}
  .pbox{{background:#fbfbfc;border:1px solid var(--line);border-radius:10px;padding:12px 14px;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;line-height:1.8;
    color:#374151;word-break:break-word}}
  .pnote{{margin-top:9px;font-size:12px;color:var(--sub);line-height:1.6}}
  .copysec{{margin-top:12px;border:1px solid rgba(232,114,47,.30);border-radius:12px;
    background:rgba(232,114,47,.045);padding:12px 14px 6px}}
  .copysec-t{{font-size:12.5px;font-weight:700;color:var(--accent);margin-bottom:8px}}
  .cprows{{display:flex;flex-direction:column}}
  .cprow{{display:flex;gap:10px;align-items:flex-start;padding:7px 0;
    border-top:1px dashed rgba(232,114,47,.22);font-size:13.5px;line-height:1.7}}
  .cprow:first-child{{border-top:none}}
  .cplabel{{flex:0 0 118px;color:#8a8f98;font-size:12px;padding-top:2px}}
  .cptext{{flex:1;color:#1c1f23;word-break:break-word}}
  @media (max-width:700px){{.cprow{{flex-direction:column;gap:2px}}.cplabel{{flex:none}}}}

  /* 交付清单 */
  .deliver li{{margin:6px 0}}

  #toast{{position:fixed;left:50%;bottom:34px;transform:translate(-50%,18px);background:#16233a;color:#fff;
    font-size:13px;padding:10px 18px;border-radius:10px;opacity:0;pointer-events:none;transition:.22s;z-index:99}}
  #toast.show{{opacity:1;transform:translate(-50%,0)}}

  #lb{{position:fixed;inset:0;background:rgba(12,16,22,.88);display:none;align-items:center;
    justify-content:center;z-index:200;padding:30px;cursor:zoom-out}}
  #lb.on{{display:flex}}
  #lb img{{max-width:100%;max-height:100%;border-radius:10px;box-shadow:0 24px 60px rgba(0,0,0,.5)}}

  @media (max-width:900px){{
    .side{{display:none}} .main{{padding:20px 16px 70px}} .hero{{padding:30px 20px}}
    .hero h1{{font-size:24px}} .block{{padding:18px 16px}}
    /* 窄屏：宽表格改为区块内横向滚动，避免整页左右溢出 */
    .block{{overflow-x:auto}}
    .doc table{{min-width:620px}} .doc th{{white-space:normal}}
    .cgrid{{grid-template-columns:1fr}}
  }}
  @media print{{
    .side,.cbtns,.hero .kpis{{display:none}} body{{background:#fff}}
    .block{{box-shadow:none;border:none;padding:0}} .hero{{background:#fff;color:#000;padding:0 0 16px}}
    .hero .brand{{color:#c2542a}} .hero p{{color:#444}} .doc table{{font-size:11px}}
  }}
</style>
</head>
<body>
<header class="hero">
  <div class="brand">{esc(cfg['brand'])}</div>
  <h1>{esc(cfg['title'])}</h1>
  <p>{esc(cfg.get('subtitle', ''))}</p>
  <div class="kpis">
    <div class="kpi"><b>{total_ads}</b><span>条朋友圈外层文案</span></div>
    <div class="kpi"><b>{total_detail}</b><span>套详情页文案</span></div>
    <div class="kpi"><b>{total_shots}</b><span>张广告效果图</span></div>
    <div class="kpi"><b>0</b><span>违禁词必拒审项</span></div>
    <div class="kpi"><b>2</b><span>个投放计划</span></div>
  </div>
</header>

<div class="layout">
  <nav class="side">{''.join(nav_html)}</nav>
  <main class="main">

    <section id="sec-overview" class="block">
      <h2 class="sec-title">一、这份交付里有什么</h2>
      <table>
        <tr><th>板块</th><th>内容</th></tr>
        <tr><td>朋友圈外层文案</td><td>{total_ads} 条，已通过违禁词机扫（0 处必拒审），可直接复制投放到广告后台</td></tr>
        <tr><td>详情页配图文案</td><td>5 套（钩子复述 + 主视觉 + 补充行 + 3 条卖点），对应 16:9 详情页首屏，可一键复制给设计</td></tr>
        <tr><td>广告效果图</td><td>{total_shots} 张朋友圈卡片效果图（每个计划 1 张），用于确认方向（正式投放请换真人实拍）</td></tr>
        <tr><td>后台配图</td><td>横版 16:9 <strong>详情页首屏配图</strong> × 2（A/B 两版人群）+ 竖版 9:16 <strong>钩子海报</strong> × 2</td></tr>
        <tr><td>投放策略方案</td><td>诊断 → 人设 → 文案 → 素材 → 承接 → 投放计划 → 优化预案 → 合规 → IP 建议 → 行动清单</td></tr>
        <tr><td>合规审核报告</td><td>机扫结果、原文→合规改写逐条对照、开户类目建议与资质举证清单</td></tr>
      </table>
      <blockquote><strong>投放前必读</strong>：本页文案已按《微信广告制作规范》压到 40 字内、去掉禁用字符与微信产品功能词，动作指令统一为「加企微」。正式投放前仍需补齐：落地页 ICP 备案、可勾选隐私协议、出镜人肖像授权、客户数据授权，以及金额类数据的证明材料。</blockquote>
    </section>

    <section id="sec-copy" class="block">
      <h2 class="sec-title">二、朋友圈外层文案（{total_ads} 条）</h2>
      <p style="color:var(--sub);font-size:13.5px;margin-top:0">
        点按钮直接复制纯文本，粘到设计工具或投放后台即可，不带 Markdown 符号。
        每条已按《微信广告制作规范》压到 40 字内、去掉禁用字符与微信产品功能词。
      </p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">
        <button class="btn btn-p" data-range="0,{len(copy_data)}">复制全部 {total_ads} 条</button>
        <button class="btn" data-range-lines="0,{len(copy_data)}">只复制全部文案行</button>
      </div>
      <div class="cgrid">{''.join(cards)}</div>
    </section>

    {''.join(f'''
    <section id="sec-detail" class="block">
      <h2 class="sec-title">三、详情页（16:9）配图文案 · 5 套</h2>
      <p style="color:var(--sub);font-size:13.5px;margin-top:0">
        每套 = <strong>钩子复述 + 主视觉 + 补充行 + 3 条卖点</strong>，直接对应详情页首屏的排布顺序；
        人设条（陈斯克 · AI 营销实战讲师）与信任条（腾讯广告同一账户体系 · 正规开户通道）五套通用。
        详情页是网页，不受外层 40 字限制，但仍须避开极限词与承诺。
      </p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">
        <button class="btn btn-p" data-range="{len(copy_data)},{len(all_blocks)}">复制全部 5 套</button>
      </div>
      <div class="cgrid">{''.join(detail_cards)}</div>
      <blockquote style="margin-top:18px">
        想把这 5 套做成成品图：在 <code>build_ad_assets.py</code> 的 <code>VARIANTS</code> 里替换
        <code>hook / big / rule / points</code> 四个字段重跑即可，<strong>复用同一张背景图，零额外积分</strong>。
      </blockquote>
    </section>''' if detail_cards else '')}

    <section id="sec-shots" class="block">
      <h2 class="sec-title">四、广告效果图（{total_shots} 张）</h2>
      <p style="color:var(--sub);font-size:13.5px;margin-top:0">
        点图可放大。图为 AI 生成示意 + 卡片合成，<strong>仅用于确认方向</strong>；正式投放必须换成陈斯克本人实拍素材。
      </p>
      <div class="gal">{''.join(gal)}</div>
    </section>

    {''.join(f'''
    <section id="sec-assets" class="block">
      <h2 class="sec-title">五、后台配图（投放素材）</h2>
      <p style="color:var(--sub);font-size:13.5px;margin-top:0">
        每个版式各 <strong>2 张（A/B 两版）</strong>：<strong>横版 16:9 是详情页（落地页）首屏配图</strong>，
        按「人设 → 钩子 → 利益 → 证据 → 信任」排布；<strong>竖版 9:16 是钩子海报</strong>，用于私聊/群发引流。点图可放大。
      </p>
      <div class="agrid">{''.join(asset_cards)}</div>
      <blockquote style="margin-top:20px">
        <strong>素材合规提醒</strong>：四张图均<strong>未放二维码、电话、微信号、按钮元素</strong>（平台禁止，OCR 会抓）；
        图片文字占比压在低位，不做"大字报"。详情页的真实按钮放在图片下方，不要画在图里。
        正式投放建议把 AI 图换成<strong>陈斯克本人实拍</strong>——真人才是信任核心。
      </blockquote>
    </section>''' if asset_cards else '')}

    {landing_html}

    {''.join(f'<div class="block">{s}</div>' for s in doc_sections)}

    <section id="sec-deliver" class="block">
      <h2 class="sec-title">交付清单</h2>
      <ul class="deliver">
        <li><code>IMAI-朋友圈广告投放方案.html</code> —— 本页（自包含，可单独发送）</li>
        <li><code>投放策略方案-IMAI-AI投放营销.md</code> —— 方案原文</li>
        <li><code>合规审核报告-IMAI-AI投放营销.md</code> —— 审核与改写对照</li>
        <li><code>文案-可复制-合规版.html</code> —— 纯文案复制页</li>
        <li><code>ad_effects/*.png</code> —— 效果图原图（{total_shots} 张）</li>
        <li><code>copy_spec_compliant.json</code> —— 文案数据，改完重跑本页即可</li>
      </ul>
      <h3>上线前 checklist</h3>
      <ul>
        <li>☐ 开户类目确认（建议「软件工具 / 商务服务」）与资质补齐</li>
        <li>☐ 落地页 ICP 备案 + 可勾选隐私协议</li>
        <li>☐ 出镜人肖像授权书、客户数据与回单授权</li>
        <li>☐ 金额类数据证明（140万 / 0.03元 / 1万次300块）与活动备案</li>
        <li>☐ 正式素材换真人实拍，重拍 3 场景 × 5 动作 × 2 尺寸 = 30 张</li>
        <li>☐ 企微承接：昵称统一、自动首句、5 条话术进快捷回复、10 分钟内真人回复</li>
      </ul>
    </section>

  </main>
</div>

<div id="lb"><img alt="放大预览"></div>
<div id="toast">已复制</div>

<script id="pagedata" type="application/json">{json.dumps(all_blocks, ensure_ascii=False)}</script>
<script id="promptdata" type="application/json">{json.dumps(prompt_data, ensure_ascii=False)}</script>
<script>
(function(){{
  var DATA = JSON.parse(document.getElementById('pagedata').textContent);
  var toast = document.getElementById('toast'), tid = null;
  function flash(m){{toast.textContent=m||'已复制';toast.classList.add('show');
    clearTimeout(tid);tid=setTimeout(function(){{toast.classList.remove('show')}},1400);}}
  function fallback(t){{var a=document.createElement('textarea');a.value=t;a.style.position='fixed';
    a.style.opacity='0';document.body.appendChild(a);a.select();var ok=false;
    try{{ok=document.execCommand('copy')}}catch(e){{ok=false}}document.body.removeChild(a);return ok;}}
  function copy(t,m){{if(navigator.clipboard&&navigator.clipboard.writeText){{
      navigator.clipboard.writeText(t).then(function(){{flash(m)}},function(){{
        flash(fallback(t)?m:'复制失败，请手动选择')}});
    }}else{{flash(fallback(t)?m:'复制失败，请手动选择')}}}}
  document.querySelectorAll('.btn[data-k]').forEach(function(b){{
    b.addEventListener('click',function(){{
      var ad=DATA[+b.dataset.i]; if(!ad) return;
      var k=b.dataset.k;
      if(k==='copy') copy(ad.copy,'文案已复制');
      else if(k==='dazi') copy(ad.dazi,'大字已复制');
      else if(k==='all') copy(ad.all,'整条已复制');
    }});
  }});
  document.querySelectorAll('.btn[data-range]').forEach(function(b){{
    b.addEventListener('click',function(){{
      var p=b.dataset.range.split(','), s=+p[0], e=+p[1];
      var sel=DATA.slice(s,e);
      copy(sel.map(function(d){{return d.all}}).join('\\n\\n'),'已复制 '+sel.length+' 条');
    }});
  }});
  document.querySelectorAll('.btn[data-range-lines]').forEach(function(b){{
    b.addEventListener('click',function(){{
      var p=b.dataset.rangeLines.split(','), s=+p[0], e=+p[1];
      var sel=DATA.slice(s,e);
      copy(sel.map(function(d){{return d.copy}}).join('\\n\\n'),'已复制 '+sel.length+' 条文案');
    }});
  }});

  var P = JSON.parse((document.getElementById('promptdata')||{{textContent:'[]'}}).textContent);
  document.querySelectorAll('.btn[data-p]').forEach(function(b){{
    b.addEventListener('click',function(){{ var it=P[+b.dataset.p]||{{}}; copy(it.p||'','提示词已复制'); }});
  }});
  document.querySelectorAll('.btn[data-pc]').forEach(function(b){{
    b.addEventListener('click',function(){{ var it=P[+b.dataset.pc]||{{}}; copy(it.c||'','这一屏文案已复制'); }});
  }});
  document.querySelectorAll('.btn[data-pa]').forEach(function(b){{
    b.addEventListener('click',function(){{ var it=P[+b.dataset.pa]||{{}}; copy(it.a||'','整屏（提示词 + 文案）已复制'); }});
  }});
  document.querySelectorAll('.btn[data-p-all]').forEach(function(b){{
    b.addEventListener('click',function(){{
      copy(P.map(function(x){{return x.p}}).join('\\n\\n'),'全部 '+P.length+' 条提示词已复制'); }});
  }});
  document.querySelectorAll('.btn[data-p-copy-all]').forEach(function(b){{
    b.addEventListener('click',function(){{
      var s=P.filter(function(x){{return x.c}}).map(function(x){{return x.c}}).join('\\n\\n');
      copy(s,'全部落地页文案已复制'); }});
  }});

  var lb=document.getElementById('lb'), lbi=lb.querySelector('img');
  document.querySelectorAll('.shot img,.aframe img').forEach(function(im){{
    im.addEventListener('click',function(){{lbi.src=im.src;lb.classList.add('on')}});
  }});
  lb.addEventListener('click',function(){{lb.classList.remove('on');lbi.src=''}});
  document.addEventListener('keydown',function(e){{if(e.key==='Escape'){{lb.classList.remove('on');lbi.src=''}}}});
}})();
</script>
</body>
</html>
"""
    out = P(cfg["out"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    size = os.path.getsize(out) / 1024 / 1024
    print(f"saved: {out}  ({size:.2f} MB, 文案 {total_ads} 条, 效果图 {total_shots} 张)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    build(ap.parse_args().config)
