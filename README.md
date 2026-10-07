# moments-ad-strategy

朋友圈广告投放策略生成 skill：输入一份企业简介，输出完整的微信朋友圈广告（腾讯广告）投放策略方案，并默认渲染每条外层文案的朋友圈卡片效果图。

## 功能

- 诊断六问 → 卖点转买点 → 人群画像 → 人设出镜
- 外层文案（三行结构 + 7 大钩子公式 + 一天版四种开场/自检四问）
- 素材方案（五步走脚本 + 四镜头分镜 + 发布前五项检查）
- 承接设计、投放搭建、首周优化预案
- 合规自查：通用红线 + 15 行业 30 个腾讯案例避坑库（含原图）
- 广告效果图：AI 场景配图 + 卡片渲染脚本（`scripts/render_ad_mockup.py`）
- IP 短视频延伸建议

## 安装

把整个文件夹（包含 SKILL.md）放到技能目录：

- Kimi Work 桌面端（macOS）：`~/Library/Application Support/kimi-desktop/daimon-share/daimon/skills/`
- Kimi CLI：`~/.kimi/skills/` 或 `~/.config/agents/skills/`

新会话自动生效。触发示例："这是公司简介，帮我做投放策略"。

## 依赖

- 效果图生成依赖图像生成插件；没有该插件时自动降级为只出文字方案
- 渲染脚本依赖 Pillow 与中文字体（Noto Sans CJK Bold 优先，回退 Hiragino Sans GB）

## 版权说明

`references/case-images/` 内案例原图来自腾讯广告帮助中心行业案例专题，原课件标注"授权用于教学"，请控制分发范围。
