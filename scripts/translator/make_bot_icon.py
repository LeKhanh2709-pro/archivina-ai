# -*- coding: utf-8 -*-
"""Vẽ hình bot (theo ảnh mẫu người dùng gửi) ra PNG cho app dịch.

Chỉ cần chạy lại khi muốn đổi hình. App (translator.py) chỉ đọc PNG, không cần Pillow.
Nền PNG là màu khoá KEY_COLOR: app đặt màu này trong suốt.
  python make_bot_icon.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

KEY_COLOR = (140, 150, 160)  # phải trùng KEY_COLOR trong translator.py
S = 4                        # vẽ to gấp 4 rồi thu nhỏ cho mịn cạnh
W, H = 100, 150              # cỡ hình bot (px)

WHITE = (255, 255, 255)
EDGE = (196, 206, 216)
SCREEN = (28, 28, 30)
EYE = (33, 150, 243)
EYE_HI = (190, 228, 255)
MOUTH = (140, 146, 156)
SHINE = (232, 238, 244)
HEADER_BG = (0, 104, 255)    # = HEADER_BG trong translator.py


def s(*v):
    return [x * S for x in v]


def draw_bot(blink=False, bg=KEY_COLOR):
    img = Image.new("RGB", (W * S, H * S), bg)
    d = ImageDraw.Draw(img)
    # Thân hình trứng + vệt sáng
    d.ellipse(s(14, 70, 86, 147), fill=WHITE, outline=EDGE, width=2 * S)
    d.chord(s(22, 78, 58, 136), 150, 250, fill=SHINE)
    # Đầu
    d.rounded_rectangle(s(6, 3, 94, 63), radius=26 * S, fill=WHITE, outline=EDGE, width=2 * S)
    # Màn hình mặt + đuôi bóng thoại
    d.rounded_rectangle(s(17, 13, 83, 51), radius=16 * S, fill=SCREEN)
    d.polygon(s(25, 44, 40, 47, 24, 60), fill=SCREEN)
    # Mắt
    for cx in (38, 62):
        if blink:
            d.line(s(cx - 5, 31, cx + 5, 31), fill=EYE, width=3 * S)
        else:
            d.ellipse(s(cx - 5.5, 25.5, cx + 5.5, 36.5), fill=EYE)
            d.ellipse(s(cx - 3.2, 27.5, cx - 0.8, 29.9), fill=EYE_HI)
    # Miệng
    d.line(s(45, 41, 55, 41), fill=MOUTH, width=int(1.5 * S))
    return img.resize((W, H), Image.LANCZOS)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for name, blink in (("bot.png", False), ("bot_blink.png", True)):
        draw_bot(blink).save(os.path.join(ASSETS, name))
    # Hình nhỏ cho thanh tiêu đề khung chat (chỉ phần đầu bot, nền xanh của thanh)
    head = draw_bot(bg=HEADER_BG).crop((0, 0, W, 66)).resize((46, 30), Image.LANCZOS)
    head.save(os.path.join(ASSETS, "bot_head.png"))
    print("Đã vẽ hình bot vào", ASSETS)


if __name__ == "__main__":
    main()
