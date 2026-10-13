#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""朋友圈广告效果图渲染器（moments-ad-strategy skill 配套脚本）

用法：
  python3 render_ad_mockup.py --spec spec.json

spec.json 结构（ads 为数组，可一次渲染多条）：
{
  "ads": [
    {
      "scene": "/abs/path/scene.png",          // AI 生成或实拍的场景图（方形优先）
      "nickname": "橙意烘焙·橙橙",              // 广告头像昵称（= 人设名）
      "subtitle": "烘焙工作室主理人",           // 昵称下小字（可省略）
      "avatar_image": "/abs/path/face.png",     // 真人头像图（可省略；传了就用它，圆形裁切）
      "avatar_text": "橙",                     // 头像单字（avatar_image 缺省时生效，默认取昵称首字）
      "avatar_color": [232, 126, 62],           // 头像底色（avatar_image 缺省时生效）
      "accent_color": [150, 205, 158],          // 大字强调色（可省略，默认暖橙）
      "copy": ["第一行钩子", "第二行证据", "第三行行动指令"],
      "dazi": [                                 // 配图上的大字，分段以支持强调色
        {"t": "168元", "accent": true},
        {"t": " · 当天取"}
      ],
      "dazi_pos": "top",                        // 大字位置：top（默认）| bottom；人物头部靠上时用 bottom，避免压脸
      "scene_crop": {"size": 0.62, "cx": 0.5, "cy": 0.0},  // 可选：再裁一层。size=保留边长占比；cx/cy=在剩余空间中的位置（0=靠左/靠上，1=靠右/靠下）
      "out": "/abs/path/效果图.png"
    }
  ]
}
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RUNTIME_FONTS = "/Users/lijianguo/Library/Application Support/kimi-desktop/daimon-share/daimon/runtime/python/fonts"
BOLD_CANDIDATES = [
    (os.path.join(RUNTIME_FONTS, "NotoSansCJKsc-Bold.otf"), 0),
    (os.path.join(RUNTIME_FONTS, "NotoSansSC-Bold.ttf"), 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1),
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
]
REGULAR_CANDIDATES = [
    (os.path.join(RUNTIME_FONTS, "NotoSansCJKsc-Regular.otf"), 0),
    (os.path.join(RUNTIME_FONTS, "NotoSansSC-Regular.ttf"), 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
]

W, PAD = 750, 28
IMG_W = W - PAD * 2
ACCENT = (255, 192, 105)      # 大字强调色（暖橙，深浅底上都清晰）
INK = (26, 26, 26)
NICK_BLUE = (87, 107, 149)
GRAY = (160, 160, 160)


def load_font(size, bold=False):
    for path, idx in (BOLD_CANDIDATES if bold else REGULAR_CANDIDATES):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=idx)
            except Exception:
                continue
    raise RuntimeError("找不到可用中文字体，请确认 NotoSansCJKsc 或 Hiragino Sans GB 存在")


def draw_dazi(img_rgba, segments, accent=None, pos="top"):
    """在配图顶部（或底部）绘制大字：渐变压暗带 + 圆角深色底衬 + 分段强调色 + 细描边。

    accent: 强调色 RGB 元组，用于适配品牌色；不传则用默认暖橙 ACCENT。
    pos:    "top"（默认，压在画面顶部）| "bottom"（压底部）。
            出镜人的头在画面上方时应改用 "bottom"，否则大字会挡住脸。
    """
    accent = tuple(accent) if accent else ACCENT
    bottom = (pos == "bottom")
    overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    band_h = 240
    for y in range(band_h):
        alpha = int(150 * (1 - y / band_h))
        yy = (IMG_W - 1 - y) if bottom else y
        od.line([(0, yy), (IMG_W, yy)], fill=(0, 0, 0, alpha))
    img_rgba.alpha_composite(overlay)

    d = ImageDraw.Draw(img_rgba)
    x0, pad_x, pad_y = 40, 30, 18
    y0 = 56 if not bottom else None
    # 可用宽度：右侧再留 10px 安全边距，避免大字被裁切
    max_chip_w = IMG_W - (x0 - pad_x) - 10
    # 自动缩放字号，保证大字完整落在卡片内（76 起，最小 40）
    size, f, total_w, heights = 76, None, 0, []
    while size >= 40:
        f = load_font(size, bold=True)
        total_w, heights = 0, []
        for seg in segments:
            bb = d.textbbox((0, 0), seg["t"], font=f, stroke_width=2)
            total_w += bb[2] - bb[0]
            heights.append(bb[3] - bb[1])
        if total_w + pad_x * 2 <= max_chip_w:
            break
        size -= 2
    chip_w = total_w + pad_x * 2
    chip_h = max(heights) + pad_y * 2 + 8
    if y0 is None:                      # 底部版式：底边留 56px 安全区
        y0 = IMG_W - 56 - chip_h + pad_y
    # 圆角深色底衬（半透明，像手机贴纸）
    chip = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    ImageDraw.Draw(chip).rounded_rectangle(
        [x0 - pad_x, y0 - pad_y, x0 - pad_x + chip_w, y0 - pad_y + chip_h],
        radius=20, fill=(0, 0, 0, 96))
    img_rgba.alpha_composite(chip)

    x = x0
    for seg in segments:
        color = accent if seg.get("accent") else (255, 255, 255)
        d.text((x, y0), seg["t"], font=f, fill=color,
               stroke_width=2, stroke_fill=(0, 0, 0, 110))
        bb = d.textbbox((0, 0), seg["t"], font=f, stroke_width=2)
        x += bb[2] - bb[0]


def rounded_avatar(size, text, color, image_path=None):
    """圆形头像。传 image_path 时用真人照片（自动方形居中裁切），否则用单字色块。"""
    if image_path and os.path.exists(image_path):
        src = Image.open(image_path).convert("RGBA")
        side = min(src.size)
        src = src.crop(((src.width - side) // 2, (src.height - side) // 2,
                        (src.width + side) // 2, (src.height + side) // 2))
        src = src.resize((size * 4, size * 4), Image.LANCZOS).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        av = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        av.paste(src, (0, 0), mask)
        return av
    av = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(av)
    d.ellipse([0, 0, size - 1, size - 1], fill=tuple(color) + (255,))
    f = load_font(int(size * 0.5), bold=True)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]),
           text, font=f, fill="white")
    return av


def render_ad(spec):
    img = Image.open(spec["scene"]).convert("RGBA")
    sc = spec.get("scene_crop") or {}
    size_r = min(max(float(sc.get("size", 1.0)), 0.05), 1.0)
    side = int(round(min(img.size) * size_r))
    if size_r >= 1.0:
        left, top = (img.width - side) // 2, (img.height - side) // 2
    else:
        fx = min(max(float(sc.get("cx", 0.0)), 0.0), 1.0)   # 0=靠左  1=靠右
        fy = min(max(float(sc.get("cy", 0.0)), 0.0), 1.0)   # 0=靠上  1=靠下
        left = int(round((img.width - side) * fx))
        top = int(round((img.height - side) * fy))
    img = img.crop((left, top, left + side, top + side)).resize((IMG_W, IMG_W), Image.LANCZOS)
    draw_dazi(img, spec["dazi"], spec.get("accent_color"), spec.get("dazi_pos", "top"))
    img = img.convert("RGB")

    f_copy, f_meta = load_font(31), load_font(24)
    f_nick = load_font(32, bold=True)
    line_h = 46
    copy_h = len(spec["copy"]) * line_h + 10
    H = PAD + 88 + 18 + copy_h + 14 + IMG_W + 16 + 40 + PAD
    card = Image.new("RGB", (W, H), (255, 255, 255))
    cd = ImageDraw.Draw(card)

    y = PAD
    av = rounded_avatar(88, spec.get("avatar_text") or spec["nickname"][0],
                        spec.get("avatar_color", [232, 126, 62]),
                        spec.get("avatar_image"))
    card.paste(av, (PAD, y), av)
    cd.text((PAD + 106, y + 8), spec["nickname"], font=f_nick, fill=NICK_BLUE)
    if spec.get("subtitle"):
        cd.text((PAD + 106, y + 50), spec["subtitle"], font=f_meta, fill=GRAY)
    tag = "广告"
    f_tag = load_font(22)
    tb = cd.textbbox((0, 0), tag, font=f_tag)
    tw = tb[2] - tb[0]
    cd.rounded_rectangle([W - PAD - tw - 22, y + 6, W - PAD, y + 40],
                         radius=6, outline=(200, 200, 200), width=2)
    cd.text((W - PAD - tw - 11, y + 11), tag, font=f_tag, fill=(150, 150, 150))
    y += 106

    for ln in spec["copy"]:
        cd.text((PAD, y), ln, font=f_copy, fill=INK)
        y += line_h
    y += 14

    card.paste(img, (PAD, y))
    y += IMG_W + 16

    cd.text((PAD, y), "1小时前", font=f_meta, fill=GRAY)
    hx, hy = W - PAD - 170, y + 4          # 手绘点赞图标（避免 emoji 缺字形）
    cd.ellipse([hx, hy, hx + 12, hy + 12], outline=GRAY, width=2)
    cd.ellipse([hx + 10, hy, hx + 22, hy + 12], outline=GRAY, width=2)
    cd.polygon([(hx + 1, hy + 8), (hx + 21, hy + 8), (hx + 11, hy + 22)], outline=GRAY, width=2)
    cd.text((hx + 32, y), "赞", font=f_meta, fill=GRAY)
    bx = hx + 80                            # 手绘评论图标
    cd.rounded_rectangle([bx, hy, bx + 24, hy + 18], radius=5, outline=GRAY, width=2)
    cd.polygon([(bx + 6, hy + 17), (bx + 6, hy + 25), (bx + 13, hy + 17)], fill=GRAY)
    cd.text((bx + 34, y), "评论", font=f_meta, fill=GRAY)

    os.makedirs(os.path.dirname(spec["out"]), exist_ok=True)
    card.save(spec["out"], quality=92)
    print("saved:", spec["out"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="spec.json 路径")
    args = ap.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        ads = json.load(fh)["ads"]
    for ad in ads:
        render_ad(ad)
    print("DONE", len(ads))


if __name__ == "__main__":
    main()
