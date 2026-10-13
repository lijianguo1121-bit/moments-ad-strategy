#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""朋友圈文案「一键复制」页渲染器（moments-ad-strategy skill 配套脚本）

用途：把外层文案渲染成一个自包含的 HTML 页面，每条文案旁带「复制」按钮，
点一下直接进剪贴板，方便粘到海报 / 设计工具 / 投放后台里用。

用法：
  python3 render_copy_sheet.py --spec copy_spec.json

copy_spec.json 结构（ads 为数组）：
{
  "brand": "IMAI · AI 投放营销",       // 顶部品牌名（可省略）
  "persona": "陈斯克",                 // 人设名（可省略，用于头像单字）
  "title": "朋友圈广告外层文案",        // 页面标题（可省略，有默认值）
  "subtitle": "共 10 条 · 直接复制使用", // 副标题（可省略，自动生成）
  "out": "/abs/path/文案-可复制.html",  // 必填
  "ads": [
    {
      "no": 1,                          // 编号（可省略，按顺序自动编号）
      "formula": "提问",                 // 钩子公式（可省略）
      "pain": "获客成本越来越贵",         // 针对痛点（可省略）
      "plan": "计划B",                   // 归属投放计划（可省略）
      "copy": ["第一行钩子", "第二行利益/证据", "第三行行动指令"],   // 必填
      "dazi": [                          // 大字分段（可省略；用 accent 标强调色）
        {"t": "还在买线索的老板"},
        {"t": "，先停一下", "accent": true}
      ],
      "note": "配图：人设 + 后台大屏 + 大字"   // 配图说明（可省略）
    }
  ]
}

设计约定：
- 文案行不自动换行，建议每行 ≤22 个中文字（与 render_ad_mockup.py 同一限制）
- 复制内容一律为「纯文本」，不含任何 Markdown 符号，粘出去即可用
"""
import argparse
import html
import json
import os


def esc(s):
    return html.escape(str(s), quote=True)


def dazi_html(dazi, accent_hex, cls="dazi"):
    """把大字分段渲染成 HTML（强调色用于数字/关键词）。"""
    if not dazi:
        return ""
    parts = []
    for seg in dazi:
        t = esc(seg.get("t", ""))
        if seg.get("accent"):
            parts.append(f'<span class="hl" style="color:{accent_hex}">{t}</span>')
        else:
            parts.append(f'<span>{t}</span>')
    return f'<div class="{cls}">{"".join(parts)}</div>'


def build_html(spec):
    # 两种输入：ads（外层/详情页文案）或 items（文生图提示词清单）
    if "items" in spec:
        return build_prompt_html(spec)
    return build_copy_html(spec)


def build_prompt_html(spec):
    """文生图提示词清单：按 group 分组，每条一个复制按钮。"""
    title = spec.get("title", "文生图提示词")
    brand = spec.get("brand", "")
    accent = spec.get("accent_color", "#e8743b")
    subtitle = spec.get("subtitle") or f"共 {len(spec['items'])} 条 · 点按钮直接复制"
    items = spec["items"]

    groups, order = {}, []
    for it in items:
        g = it.get("group", "")
        if g not in groups:
            groups[g] = []
            order.append(g)
        groups[g].append(it)

    secs = []
    plain_all = []
    for gi, g in enumerate(order):
        cards = []
        for it in groups[g]:
            prompt = it["prompt"]
            plain_all.append(f"【{it.get('slot','')}】\n{prompt}")
            note = f'<div class="note">{esc(it["note"])}</div>' if it.get("note") else ""
            size = f'<span class="chip">{esc(it["size"])}</span>' if it.get("size") else ""
            cards.append(f"""
      <article class="card">
        <div class="card-head">
          <div class="avatar" style="background:{accent}">{gi + 1}</div>
          <div class="head-main">
            <div class="card-title">{esc(it.get("slot", "提示词"))}</div>
            <div class="chips">{size}</div>
          </div>
        </div>
        <div class="copybox"><div class="line prompt">{esc(prompt)}</div></div>
        {note}
        <div class="btns">
          <button class="btn btn-primary" data-g="{gi}" data-s="{len(cards)}">复制提示词</button>
        </div>
      </article>""")
        secs.append(f"""
    <section class="group">
      <h2 class="group-title">{esc(g)}</h2>
      {''.join(cards)}
    </section>""")

    rule_html = ""
    if spec.get("rules"):
        li = "".join(f"<li>{esc(r)}</li>" for r in spec["rules"])
        rule_html = f"<section class='card ruletop'><div class='card-title'>通用规范（先读这 5 条）</div><ul class='rules'>{li}</ul></section>"

    data = [[it["prompt"] for it in groups[g]] for g in order]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
  :root {{ --bg:#f4f5f7; --card:#fff; --ink:#1c1f23; --sub:#6b7280; --line:#e6e8ec; --accent:{accent}; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:32px 16px 80px; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
    -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:900px; margin:0 auto; }}
  header {{ margin-bottom:20px; }}
  .brand {{ font-size:13px; letter-spacing:.08em; color:var(--accent); font-weight:700; }}
  h1 {{ font-size:26px; margin:8px 0 6px; letter-spacing:-.01em; }}
  .sub {{ color:var(--sub); font-size:14px; }}
  .topbar {{ position:sticky; top:0; z-index:9; background:rgba(244,245,247,.92);
    backdrop-filter:saturate(180%) blur(8px); padding:12px 0; display:flex; gap:10px; flex-wrap:wrap; }}
  .group-title {{ font-size:16px; margin:24px 0 12px; padding-left:10px; border-left:4px solid var(--accent); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px 22px;
    margin-bottom:14px; box-shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px -16px rgba(16,24,40,.18); }}
  .ruletop {{ border-left:4px solid var(--accent); }}
  .card-head {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}
  .avatar {{ width:40px; height:40px; border-radius:12px; color:#fff; font-weight:700; flex:0 0 40px;
    display:flex; align-items:center; justify-content:center; font-size:16px; }}
  .card-title {{ font-size:15px; font-weight:700; }}
  .chips {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:4px; }}
  .chip {{ font-size:11px; padding:2px 8px; border-radius:999px; background:#eef0f3; color:#4b5563; }}
  .copybox {{ border:1px solid var(--line); border-radius:12px; padding:14px 16px; background:#fbfbfc; }}
  .line {{ font-size:15px; line-height:1.85; }}
  .prompt {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:13.5px; }}
  .note {{ margin-top:10px; font-size:12.5px; color:var(--sub); line-height:1.6; }}
  .btns {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }}
  .btn {{ appearance:none; border:1px solid var(--line); background:#fff; color:#374151; font-size:13px;
    padding:7px 14px; border-radius:9px; cursor:pointer; font-family:inherit; transition:.15s; }}
  .btn:hover {{ border-color:#c9ced6; background:#fafbfc; }}
  .btn-primary {{ background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }}
  .btn-primary:hover {{ filter:brightness(1.06); background:var(--accent); }}
  .rules {{ margin:10px 0 0; padding-left:20px; font-size:13.5px; color:#374151; line-height:1.8; }}
  #toast {{ position:fixed; left:50%; bottom:36px; transform:translate(-50%,20px); background:#1c1f23;
    color:#fff; font-size:13px; padding:10px 18px; border-radius:10px; opacity:0; pointer-events:none;
    transition:.22s; z-index:99; }}
  #toast.show {{ opacity:1; transform:translate(-50%,0); }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">{esc(brand)}</div>
    <h1>{esc(title)}</h1>
    <div class="sub">{esc(subtitle)}</div>
  </header>
  <div class="topbar">
    <button class="btn btn-primary" id="copyAll">复制全部 {len(items)} 条提示词</button>
  </div>
  {rule_html}
  {''.join(secs)}
</div>
<div id="toast">已复制</div>
<script id="pagedata" type="application/json">{json.dumps(data, ensure_ascii=False)}</script>
<script>
(function () {{
  var DATA = JSON.parse(document.getElementById('pagedata').textContent);
  var ALL = {json.dumps(plain_all, ensure_ascii=False)};
  var toast = document.getElementById('toast'), tid = null;
  function flash(m) {{ toast.textContent = m || '已复制'; toast.classList.add('show');
    clearTimeout(tid); tid = setTimeout(function(){{ toast.classList.remove('show') }}, 1400); }}
  function fallback(t) {{ var a=document.createElement('textarea'); a.value=t; a.style.position='fixed';
    a.style.opacity='0'; document.body.appendChild(a); a.select(); var ok=false;
    try{{ ok=document.execCommand('copy') }}catch(e){{ ok=false }} document.body.removeChild(a); return ok; }}
  function copy(t,m) {{ if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(t).then(function(){{flash(m)}},function(){{flash(fallback(t)?m:'复制失败，请手动选择')}});
    }} else {{ flash(fallback(t)?m:'复制失败，请手动选择'); }} }}
  document.querySelectorAll('.btn[data-g]').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var arr = DATA[+b.dataset.g] || [];
      copy(arr[+b.dataset.s] || '', '提示词已复制');
    }});
  }});
  var ca = document.getElementById('copyAll');
  if (ca) ca.addEventListener('click', function () {{ copy(ALL.join('\\n\\n'), '全部提示词已复制'); }});
}})();
</script>
</body>
</html>
"""


def build_copy_html(spec):
    brand = spec.get("brand", "朋友圈广告")
    persona = spec.get("persona", "")
    title = spec.get("title", "朋友圈广告外层文案")
    ads = spec.get("ads", [])
    accent = spec.get("accent_color", "#e8743b")
    subtitle = spec.get("subtitle") or f"共 {len(ads)} 条 · 点按钮直接复制"
    avatar_char = persona[:1] if persona else "广"

    # 顶部统计：公式覆盖
    formulas = [a.get("formula", "") for a in ads if a.get("formula")]
    formula_line = " ／ ".join(dict.fromkeys(formulas))

    cards = []
    plain_all = []
    for i, ad in enumerate(ads, 1):
        no = ad.get("no", i)
        copy = ad.get("copy", [])
        chips = []
        if ad.get("formula"):
            chips.append(f'<span class="chip chip-f">公式 · {esc(ad["formula"])}</span>')
        if ad.get("plan"):
            chips.append(f'<span class="chip chip-p">{esc(ad["plan"])}</span>')
        pain = f'<div class="pain">针对痛点：{esc(ad["pain"])}</div>' if ad.get("pain") else ""

        lines = "".join(f'<div class="line">{esc(l)}</div>' for l in copy)
        dazi = dazi_html(ad.get("dazi"), accent)
        dazi_copy = "".join(s.get("t", "") for s in ad.get("dazi", []))
        note = f'<div class="note">{esc(ad["note"])}</div>' if ad.get("note") else ""

        copy_plain = "\n".join(copy)
        plain_all.append(f"文案 {no}（{ad.get('formula','')}）\n{copy_plain}")

        btn_dazi = (f'<button class="btn" data-i="{i-1}" data-k="dazi">复制大字</button>'
                    if dazi_copy else "")
        btn_note = (f'<button class="btn" data-i="{i-1}" data-k="note">复制配图说明</button>'
                    if ad.get("note") else "")

        cards.append(f"""
    <section class="card">
      <div class="card-head">
        <div class="avatar" style="background:{accent}">{esc(avatar_char)}</div>
        <div class="head-main">
          <div class="card-title">文案 {no}</div>
          <div class="chips">{''.join(chips)}</div>
        </div>
      </div>
      {pain}
      <div class="copybox">
        {lines}
      </div>
      {dazi}
      {note}
      <div class="btns">
        <button class="btn btn-primary" data-i="{i-1}" data-k="copy">复制文案</button>
        {btn_dazi}
        {btn_note}
        <button class="btn" data-i="{i-1}" data-k="all">复制这一条全部</button>
      </div>
    </section>""")

    data_json = json.dumps(
        [
            {
                "copy": "\n".join(a.get("copy", [])),
                "dazi": "".join(s.get("t", "") for s in a.get("dazi", [])),
                "note": a.get("note", ""),
                "all": "\n".join(
                    [f"【文案 {a.get('no', i)}】"]
                    + ([f"公式：{a['formula']}"] if a.get("formula") else [])
                    + ([f"痛点：{a['pain']}"] if a.get("pain") else [])
                    + a.get("copy", [])
                    + ([f"大字：{''.join(s.get('t','') for s in a.get('dazi',[]))}"] if a.get("dazi") else [])
                    + ([f"配图：{a['note']}"] if a.get("note") else [])
                ),
            }
            for i, a in enumerate(ads, 1)
        ],
        ensure_ascii=False,
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {esc(brand)}</title>
<style>
  :root {{
    --bg:#f4f5f7; --card:#ffffff; --ink:#1c1f23; --sub:#6b7280;
    --line:#e6e8ec; --accent:{accent};
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; padding:32px 16px 80px; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
      "Microsoft YaHei","Noto Sans CJK SC",sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:880px; margin:0 auto; }}
  header {{ margin-bottom:24px; }}
  .brand {{ font-size:13px; letter-spacing:.08em; color:var(--accent); font-weight:700; }}
  h1 {{ font-size:26px; margin:8px 0 6px; letter-spacing:-.01em; }}
  .sub {{ color:var(--sub); font-size:14px; }}
  .formula-line {{ margin-top:8px; font-size:12px; color:var(--sub); }}
  .topbar {{ position:sticky; top:0; z-index:9; background:rgba(244,245,247,.92);
    backdrop-filter:saturate(180%) blur(8px); padding:12px 0; display:flex; gap:10px; flex-wrap:wrap; }}
  .card {{
    background:var(--card); border:1px solid var(--line); border-radius:16px;
    padding:20px 22px; margin-bottom:16px;
    box-shadow:0 1px 2px rgba(16,24,40,.04), 0 8px 24px -16px rgba(16,24,40,.18);
  }}
  .card-head {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}
  .avatar {{
    width:40px; height:40px; border-radius:50%; color:#fff; font-weight:700;
    display:flex; align-items:center; justify-content:center; font-size:17px; flex:0 0 auto;
  }}
  .card-title {{ font-size:15px; font-weight:700; }}
  .chips {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:4px; }}
  .chip {{ font-size:11px; padding:2px 8px; border-radius:999px; background:#eef0f3; color:#4b5563; }}
  .chip-f {{ background:rgba(232,116,59,.10); color:#c2542a; }}
  .chip-p {{ background:#e8f0fe; color:#2f5bd0; }}
  .pain {{ font-size:12px; color:var(--sub); margin:2px 0 10px; }}
  .copybox {{
    border:1px solid var(--line); border-radius:12px; padding:14px 16px; background:#fbfbfc;
  }}
  .line {{ font-size:17px; line-height:1.9; font-weight:500; }}
  .line + .line {{ margin-top:2px; }}
  .dazi {{
    margin-top:12px; font-size:14px; color:#8a8f98;
  }}
  .dazi .hl {{ font-weight:700; }}
  .note {{ margin-top:8px; font-size:12px; color:var(--sub); line-height:1.6; }}
  .btns {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }}
  .btn {{
    appearance:none; border:1px solid var(--line); background:#fff; color:#374151;
    font-size:13px; padding:7px 14px; border-radius:9px; cursor:pointer;
    font-family:inherit; transition:.15s;
  }}
  .btn:hover {{ border-color:#c9ced6; background:#fafbfc; }}
  .btn:active {{ transform:translateY(1px); }}
  .btn-primary {{ background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }}
  .btn-primary:hover {{ filter:brightness(1.06); background:var(--accent); }}
  footer {{ margin-top:28px; font-size:12px; color:var(--sub); line-height:1.8; }}
  #toast {{
    position:fixed; left:50%; bottom:36px; transform:translate(-50%,20px);
    background:#1c1f23; color:#fff; font-size:13px; padding:10px 18px; border-radius:10px;
    opacity:0; pointer-events:none; transition:.22s; z-index:99;
  }}
  #toast.show {{ opacity:1; transform:translate(-50%,0); }}
  @media (max-width:560px) {{ .line {{ font-size:16px; }} h1 {{ font-size:22px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">{esc(brand)}</div>
    <h1>{esc(title)}</h1>
    <div class="sub">{esc(subtitle)}</div>
    <div class="formula-line">{esc(formula_line)}</div>
  </header>
  <div class="topbar">
    <button class="btn btn-primary" id="copyAll">复制全部 {len(ads)} 条</button>
    <button class="btn" id="copyAllLines">只复制全部三行文案</button>
  </div>
  {''.join(cards)}
  <footer>
    ⚠️ 文案中的数字、名额、案例数据上线前须确认真实性与可核验口径；<br>
    造稀缺类表述必须真实且按期兑现；行业资质与出镜人授权齐备后才可投放。
  </footer>
</div>
<div id="toast">已复制</div>
<script id="pagedata" type="application/json">{data_json}</script>
<script>
(function () {{
  const DATA = JSON.parse(document.getElementById('pagedata').textContent);
  const ALL = {json.dumps(plain_all, ensure_ascii=False)};
  const toast = document.getElementById('toast');
  let tid = null;
  function flash(msg) {{
    toast.textContent = msg || '已复制';
    toast.classList.add('show');
    clearTimeout(tid);
    tid = setTimeout(() => toast.classList.remove('show'), 1400);
  }}
  function fallbackCopy(text) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {{ ok = document.execCommand('copy'); }} catch (e) {{ ok = false; }}
    document.body.removeChild(ta);
    return ok;
  }}
  function copy(text, msg) {{
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(
        () => flash(msg),
        () => flash(fallbackCopy(text) ? msg : '复制失败，请手动选择')
      );
    }} else {{
      flash(fallbackCopy(text) ? msg : '复制失败，请手动选择');
    }}
  }}
  document.querySelectorAll('.btn[data-k]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const ad = DATA[Number(btn.dataset.i)];
      if (!ad) return;
      const k = btn.dataset.k;
      if (k === 'copy') copy(ad.copy, '文案已复制');
      else if (k === 'dazi') copy(ad.dazi, '大字已复制');
      else if (k === 'note') copy(ad.note, '配图说明已复制');
      else if (k === 'all') copy(ad.all, '整条已复制');
    }});
  }});
  const allBtn = document.getElementById('copyAll');
  if (allBtn) allBtn.addEventListener('click', () => copy(ALL.join('\\n\\n'), '全部 ' + ALL.length + ' 条已复制'));
  const allLines = document.getElementById('copyAllLines');
  if (allLines) allLines.addEventListener('click', () => {{
    copy(DATA.map(d => d.copy).join('\\n\\n'), '全部三行文案已复制');
  }});
}})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="copy_spec.json 路径")
    args = ap.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    out = spec["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build_html(spec))
    print("saved:", out, f"({len(spec.get('ads') or spec.get('items', []))} 条)")


if __name__ == "__main__":
    main()
