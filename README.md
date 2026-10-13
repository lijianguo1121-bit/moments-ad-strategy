# moments-ad-strategy

朋友圈广告投放策略生成 skill：输入一份企业简介，输出完整的微信朋友圈广告（腾讯广告）投放策略方案，默认交付 10 条外层文案 + 5 套详情页文案（可一键复制）、朋友圈卡片效果图、后台配图（16:9 详情页配图 / 9:16 钩子海报）、详情页落地页长页，最后全部装进一个自包含 HTML 交付页。

## 功能

- 诊断六问 → 卖点转买点 → 人群画像 → 人设出镜
- 外层文案 **10 条**（三行结构 + 7 大钩子公式 + 一天版四种开场/自检四问）
- 素材方案（五步走脚本 + 四镜头分镜 + 发布前五项检查）
- 承接设计、投放搭建、首周优化预案
- **违禁词机扫**：交付前必跑，覆盖字数/空格/微信产品功能词/诱导加联系方式/绝对化用语/教育红线等，BLOCK 归零才交付（`scripts/check_compliance.py`）
- 合规自查：平台侧硬规范（40 字上限等）+ 通用红线 + 15 行业 30 个腾讯案例避坑库（含原图）
- 广告效果图：AI 场景配图 + 卡片渲染脚本（`scripts/render_ad_mockup.py`）
- **文案一键复制页**：HTML，每条文案旁带复制按钮（`scripts/render_copy_sheet.py`）
- **后台配图**：横版 16:9（**详情页首屏配图**）+ 竖版 9:16（钩子海报），**每个版式最多 2 张 A/B 版**（HTML 排版 + Playwright 精确截图）
- **详情页文案 5 套**：钩子复述 + 主视觉 + 补充行 + 3 条卖点，可一键复制
- **详情页（落地页）长页**：首屏痛点 → 品牌区 → 能力块 → 行业覆盖 → 选择理由 → 留资表单 → 备案，产出可发布 HTML + 整页长图
- **详情页文生图提示词**：首屏人物图 + 行业格子图模板/变量 + 图标，可一键复制
- **HTML 交付页**：把上面全部装进一个自包含网页，双击即开、可单独转发（`scripts/build_report_html.py`）
- IP 短视频延伸建议

## 交付物

| 文件 | 说明 |
| --- | --- |
| `交付页.html` | **主交付物**：方案 + 外层文案 + 详情页文案 + 效果图 + 后台配图 + 详情页长图 + 合规报告，一个自包含网页 |
| `投放策略方案-<公司名>.md` | 方案全文（8 板块） |
| `文案-可复制-合规版.html` | 10 条外层文案，点按钮直接复制（做海报、给设计、填后台用） |
| `详情页文案-可复制.html` | 5 套详情页文案，一对一复制 |
| `合规审核报告-<公司名>.md` | 机扫 + 人工清单结果、原文→合规改写对照、开户资质与举证清单 |
| `广告效果图/*.png` | 朋友圈卡片效果图（**最多 2 张**，每个投放计划 1 张） |
| `后台配图-16x9-A/B.png` | 详情页首屏配图（1920×1080，A/B 两版人群） |
| `后台配图-9x16-A/B.png` | 钩子海报（1080×1920，A/B 两版人群） |
| `landing/详情页.html` + `详情页-长图.png` | **详情页（落地页）竖版长页**：可发布页 + 整页长图 |
| `详情页-文生图提示词.html` | 详情页配图的文生图提示词清单，一键复制 |
| `copy_spec*.json` / `detail_copy_spec.json` / `spec*.json` / `build.json` | 脚本入参，改内容后重跑 |

## 配套脚本

| 脚本 | 用途 |
| --- | --- |
| `scripts/check_compliance.py` | 违禁词/风险词检测（交付前必跑；`--mode outer/page` 区分外层与落地页） |
| `scripts/render_ad_mockup.py` | 场景配图 + 外层文案 → 朋友圈卡片效果图；也用于量文案行宽 |
| `scripts/render_copy_sheet.py` | 外层文案 / 详情页文案 / 文生图提示词 → 一键复制 HTML 页 |
| `scripts/build_landing_page.py` | 详情页（落地页）竖版长页 → HTML + 整页长图 |
| `scripts/build_report_html.py` | 全部产出 → 自包含 HTML 交付页（最终呈现） |
| `scripts/build_strategy_full.py` | SKILL.md + references → 合并成 `strategy-full.md` 单文件 |

## 依赖

- 违禁词检测、文案/提示词复制页、单文件合并：**纯 Python 标准库**，无需第三方包
- 后台配图 / 详情页长图 / HTML 交付页：需要 `Pillow`、`playwright`（截图）、`markdown`（Markdown 转 HTML）
- 配图与效果图会调用图像生成能力（每张约 5–10 积分，出手前会先告知消耗）

## 安装

把整个文件夹（包含 SKILL.md）放到技能目录：

- Kimi Work 桌面端（macOS）：`~/Library/Application Support/kimi-desktop/daimon-share/daimon/skills/`
- Kimi CLI：`~/.kimi/skills/` 或 `~/.config/agents/skills/`

新会话自动生效。触发示例："这是公司简介，帮我做投放策略"。

## 依赖

- 违禁词检测、文案/提示词复制页、单文件合并：**纯 Python 标准库**，无需第三方包
- 后台配图 / 详情页长图 / HTML 交付页：需要 `Pillow`、`playwright`（截图）、`markdown`（Markdown 转 HTML）
- 效果图与配图会调用图像生成能力（每张约 5–10 积分，出手前会先告知消耗）；没有该能力时自动降级为只出文字方案

## 版权说明

`references/case-images/` 内案例原图来自腾讯广告帮助中心行业案例专题，原课件标注"授权用于教学"，请控制分发范围。

## 快速直读链接

学员/其他 AI 直接读这个文件即可学习完整方法论：
`strategy-full.md`（raw 链接：`https://raw.githubusercontent.com/lijianguo1121-bit/moments-ad-strategy/main/strategy-full.md`）

> 注：`references/case-images/`（30 张腾讯案例原图）未包含在公开仓库中（原课件标注"授权用于教学"）；如需完整包请私下获取 `.skill` 文件。
