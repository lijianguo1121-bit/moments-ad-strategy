#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""朋友圈广告文案「违禁词 / 风险词」检测器（moments-ad-strategy skill 配套脚本）

交付前必跑。机审最容易秒拒的几类都在这里：绝对化用语、诱导加联系方式、
微信产品功能词、保证承诺、教育行业红线、禁用字符与超字数。

规则依据（2026-10 核对，最终以平台当期规则为准）：
- 微信广告制作规范 / 朋友圈广告外层文案规范：
  文字 ≤40 字、≤4 行、不允许空格、不允许破折号「——」、连接号仅限「~」、
  不得混用中英文标点、单个词语不得单独成行。
- 腾讯广告基础审核规则：禁绝对化用语；**不得诱导添加微信/公众号等联系方式**；
  但**支持**「加企微、加企微群、加客服微信、加客服、加客服群」相关描述
  （须通过平台自带落地页的【商家微信】/加企微组件承接）。
- 微信广告：未经官方授权，禁用「朋友圈、点赞、评论、公众号、微信、红包」等产品功能词汇。
- 腾讯广告用户体验规范：不得模仿功能性消息提示；不得出现电话/微信号/QQ/URL/二维码。
- 教育行业审核规则：不得对培训效果作保证性承诺；不得暗示增收；
  不支持「教你赚钱 / 引流 / 加粉 / 涨粉 / 养号」类营销描述。

用法：
  python3 check_compliance.py                       # 扫描当前目录 copy_spec.json
  python3 check_compliance.py --spec a.json b.json   # 扫描指定 spec
  python3 check_compliance.py --file 方案.md          # 扫描文本/Markdown
  python3 check_compliance.py --quiet                # 只输出汇总与拒审项

退出码：发现 BLOCK 级问题返回 1（便于脚本化卡口），否则 0。
"""
import argparse
import json
import os
import re
import sys

# (严重度, 类别, 词表)  BLOCK=必拒审  WARN=高风险须改  NOTE=需备案或举证
RULES = [
    ("BLOCK", "微信产品功能词", ["朋友圈", "公众号", "视频号", "小程序", "红包", "点赞", "评论", "微信"]),
    ("BLOCK", "诱导添加联系方式", ["加我微信", "加微信", "加微", "加V", "加v", "VX", "vx", "微信号",
                                 "扫码", "二维码", "私信我", "加我好友", "加好友"]),
    ("BLOCK", "绝对化用语", ["最好", "最强", "最便宜", "最专业", "最低价", "最大", "最高级", "最优", "最高",
                            "第一", "唯一", "独家", "顶级", "极品", "至尊", "国家级", "全网", "领先", "首创",
                            "销量第一", "排名第一"]),
    ("BLOCK", "保证/承诺类", ["保证", "包过", "包治", "稳赚", "一定", "确保", "绝对", "100%", "无效退款",
                             "立竿见影", "一次见效", "永不", "百分百", "零风险", "无风险"]),
    ("BLOCK", "教育行业红线·承诺效果或增收", ["教你赚钱", "教你如何赚钱", "教你变现", "月入", "年入", "日入",
                                              "副业", "额外收入", "轻松赚", "躺赚", "暴富", "风口行业",
                                              "高收益", "红利爆发", "稳赚不赔"]),
    ("BLOCK", "教育行业红线·引流类描述", ["涨粉", "加粉", "引流", "养号", "刷粉", "爆粉", "起号"]),
    ("BLOCK", "命令/挑衅/誓言语气", ["你该", "必须买", "非买不可", "不买", "敢不敢", "不看后悔", "不点后悔",
                                     "我发誓", "发誓", "还不赶快", "赶紧买"]),
    ("BLOCK", "官方背书暗示", ["官方推荐", "腾讯推荐", "微信认证", "火爆", "HOT", "央视", "国家级认证",
                               "权威认证", "政府指定"]),
    ("BLOCK", "虚假对比/夸大", ["前后对比", "亲测有效", "神效", "瞬间", "秒变", "包你"]),
    ("WARN", "敏感词·免费", ["免费", "0元", "零元", "不花钱", "白送", "免费领"]),
    ("WARN", "实时性/稀缺诱导", ["仅限今天", "仅此一天", "最后一天", "限时", "即将涨", "即将结束", "即将售罄",
                                 "明日涨价", "错过", "名额有限", "抢购", "倒计时", "仅剩", "马上没"]),
    ("WARN", "价格夸张描述", ["白菜价", "击破底价", "0利润", "太狠了", "1顶5", "1顶10", "超低价", "史上最低",
                              "跳楼价"]),
    ("WARN", "功效/疗效词", ["根治", "治疗", "痊愈", "见效", "疗效", "药到病除", "消炎", "祛痘"]),
    ("WARN", "负面情绪用词", ["亏死", "出大事", "疯了", "喝多了", "血亏", "惨不忍睹"]),
    ("WARN", "指向性/贬低群体", ["你的年龄", "你这个年龄", "你的存款", "你这个年纪", "40岁的你", "90后",
                                 "宝妈注意", "所有人注意", "大龄", "剩女", "低学历", "穷"]),
    ("WARN", "价格/金额赠送类", ["赠送金额", "返现", "返利", "全场", "折"]),
    ("NOTE", "涉及数据(需数据证明)", ["元", "万", "亿", "倍", "%"]),
    ("NOTE", "涉及名额/活动(需活动备案)", ["名额", "本月", "只接", "只带", "开放", "限"]),
]

# 禁用字符（外层文案排版规范）
# 注：英文句点「.」不列入——小数（0.03元）里是数字的一部分，不是标点混用，避免误报。
FORBIDDEN_CHARS = [
    ("空格", " "),
    ("破折号", "—"),
    ("连接号-半角", "-"),
    ("直角引号", "「"),
    ("直角引号", "」"),
    ("方括号", "【"),
    ("方括号", "】"),
    ("英文冒号", ":"),
    ("英文逗号", ","),
    ("省略号(非规范)", "..."),
]

MAX_CHARS = 40   # 外层文案上限：文字个数不超过 40 个字（三行合计，含标点）
MAX_LINES = 4    # 不超过 4 行
MAX_DAZI = 15    # 配图大字建议上限（渲染脚本 76→40 号自动缩，超了会被压到最小字号）


def find_chars(s):
    hits = []
    for name, ch in FORBIDDEN_CHARS:
        if ch in s:
            hits.append(name)
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", s):
        hits.append("emoji")
    return sorted(set(hits))


def scan_line(line, allow=(), mode="outer"):
    """扫描一行文本。allow 为白名单短语（如『加企微』『加客服微信』），命中则跳过。

    mode="outer" —— 朋友圈外层文案：套用全部排版规范（空格/禁用字符/字数）
    mode="page"  —— 详情页/落地页文案：**不套用外层排版规范**（网页不受 40 字与无空格限制），
                    只查词表（极限词、承诺、微信产品词、诱导加联系方式、教育红线等）
    """
    tmp = line
    for phrase in allow:
        tmp = tmp.replace(phrase, "")
    issues = []
    for level, cat, words in RULES:
        for w in words:
            if w in tmp:
                issues.append((level, cat, w))
                break
    if mode == "outer":
        for c in find_chars(line):
            issues.append(("WARN", "禁用字符/排版", c))
    return issues


# 平台明确支持的加企微/加客服表述，检测时视为白名单
ALLOWLIST = ["加企微群", "加企微", "加客服微信", "加客服群", "加客服"]


def scan_copy(copy, dazi, mode="outer"):
    out = []
    if mode == "outer":
        total = sum(len(x) for x in copy)
        if total > MAX_CHARS:
            out.append(("BLOCK", "字数超限", f"三行合计 {total} 字 > {MAX_CHARS} 字上限（微信广告制作规范）"))
        if len(copy) > MAX_LINES:
            out.append(("BLOCK", "行数超限", f"{len(copy)} 行 > {MAX_LINES} 行上限"))
    for i, ln in enumerate(copy, 1):
        for lv, cat, w in scan_line(ln, ALLOWLIST, mode):
            out.append((lv, cat, f"第{i}行「{w}」 → {ln}"))
    for seg in dazi:
        for lv, cat, w in scan_line(seg.get("t", ""), ALLOWLIST, mode):
            out.append((lv, cat, f"大字「{w}」"))
    if dazi and len("".join(s.get("t", "") for s in dazi)) > MAX_DAZI:
        out.append(("WARN", "大字过长", f"大字超 {MAX_DAZI} 字，渲染时会被压到最小字号"))
    return out


MARK = {"BLOCK": "🔴 必拒审", "WARN": "🟠 高风险", "NOTE": "🟡 需备案/举证"}
ORDER = {"BLOCK": 0, "WARN": 1, "NOTE": 2}


def report(title, items, quiet=False):
    if not items:
        if not quiet:
            print(f"\n{title}\n  ✅ 未命中任何词表")
        return
    if quiet and not any(lv == "BLOCK" for lv, _, _ in items):
        return
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    for lv, cat, detail in sorted(items, key=lambda x: ORDER[x[0]]):
        print(f"  {MARK[lv]} [{cat}] {detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", nargs="*", default=None, help="copy_spec.json 路径（默认 ./copy_spec.json）")
    ap.add_argument("--file", nargs="*", default=None, help="要扫描的文本/Markdown 文件")
    ap.add_argument("--quiet", action="store_true", help="只输出有拒审风险的部分")
    ap.add_argument("--mode", choices=["outer", "page"], default="outer",
                    help="outer=朋友圈外层文案（默认，套用 40 字/无空格等排版规范）；"
                         "page=详情页/落地页文案（只查词表，不套外层排版规范）")
    args = ap.parse_args()

    specs = args.spec if args.spec else ["copy_spec.json"]
    files = args.file or []
    stat = {"BLOCK": 0, "WARN": 0, "NOTE": 0}

    for sp in specs:
        if not os.path.exists(sp):
            print(f"跳过（不存在）：{sp}")
            continue
        with open(sp, encoding="utf-8") as fh:
            data = json.load(fh)
        for i, ad in enumerate(data.get("ads", []), 1):
            items = scan_copy(ad.get("copy", []), ad.get("dazi", []), args.mode)
            for lv, _, _ in items:
                stat[lv] += 1
            report(f"文案 {ad.get('no', i)}　公式：{ad.get('formula', '-')}　计划：{ad.get('plan', '-')}",
                   items, args.quiet)

    for fp in files:
        if not os.path.exists(fp):
            print(f"跳过（不存在）：{fp}")
            continue
        with open(fp, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        items = []
        for n, ln in enumerate(lines, 1):
            for lv, cat, w in scan_line(ln, ALLOWLIST, args.mode):
                items.append((lv, cat, f"L{n}「{w}」 → {ln.strip()[:80]}"))
        for lv, _, _ in items:
            stat[lv] += 1
        report(f"文件：{fp}", items, args.quiet)

    print(f"\n{'=' * 78}")
    print(f"扫描模式：{args.mode}　｜　汇总：必拒审 {stat['BLOCK']} 处 ｜ 高风险 {stat['WARN']} 处 ｜ 需备案/举证 {stat['NOTE']} 处")
    if args.mode == "page":
        print("说明：page 模式不套用外层排版规范（40 字/无空格），只查违禁词与风险词。")
    print("说明：词表覆盖机审高频命中项，不等于平台最终判定；")
    print("      涉及活动、数据、资质、肖像的须另行备案举证；最终以平台当期规则为准。")
    return 1 if stat["BLOCK"] else 0


if __name__ == "__main__":
    sys.exit(main())
