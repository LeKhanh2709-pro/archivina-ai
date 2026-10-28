# -*- coding: utf-8 -*-
"""Sinh lisp\\VK.lsp từ lisp\\vk_nguon.lsp: mọi chữ có dấu trong CHUỖI đổi thành mã \\U+XXXX.

Lý do (người dùng báo lỗi font 28/10/2026): AutoCAD đặt LISPSYS = 0 đọc file LISP theo bảng mã ANSI, chữ
UTF-8 trong chuỗi / hộp thoại bị vỡ. Mã \\U+XXXX chỉ gồm ký tự ASCII, AutoCAD tự hiển thị đúng ở dòng lệnh
và hộp thoại DCL với cả LISPSYS = 0 và 1. Chú thích (;) giữ nguyên tiếng Việt.

Chạy: python gop_vk.py   (sửa vk_nguon.lsp, không sửa tay VK.lsp; sinh xong chép VK.lsp sang <gốc>\\scripts\\lisp)
"""
import os
import sys


def ma_hoa(src):
    out, i, trong_chuoi, chu_thich = [], 0, False, False
    while i < len(src):
        c = src[i]
        if chu_thich:
            out.append(c)
            if c == "\n":
                chu_thich = False
        elif trong_chuoi:
            if c == "\\":
                out.append(src[i:i + 2])
                i += 2
                continue
            if c == '"':
                trong_chuoi = False
                out.append(c)
            elif ord(c) > 127:
                # trong chuỗi LISP "\\" là 1 dấu \ -> lúc chạy chuỗi chứa \U+XXXX
                out.append("\\\\U+%04X" % ord(c))
            else:
                out.append(c)
        else:
            if c == ";":
                chu_thich = True
            elif c == '"':
                trong_chuoi = True
            out.append(c)
        i += 1
    return "".join(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nguon = os.path.join(skill, "lisp", "vk_nguon.lsp")
    dich = os.path.join(skill, "lisp", "VK.lsp")
    s = open(nguon, encoding="utf-8").read()
    dau = (";;; FILE SINH TỰ ĐỘNG từ vk_nguon.lsp bằng scripts\\gop_vk.py — KHÔNG SỬA TAY.\n"
           ";;; Chữ có dấu trong chuỗi đã đổi thành mã \\U+XXXX để hiện đúng với cả LISPSYS = 0 và 1.\n")
    # dữ liệu block nhúng (scripts\nhung_block.ps1 sinh từ assets\VK_thu_vien.dwg), đặt cuối file;
    # (princ) cuối cùng để APPLOAD không in cả danh sách dữ liệu ra dòng lệnh
    du_lieu = open(os.path.join(skill, "lisp", "vk_du_lieu.lsp"), encoding="utf-8").read()
    s = (dau + ma_hoa(s.split("\n", 1)[1]).rstrip() + "\n\n"
         ";;; ---------------------------------------------------------------- dữ liệu block nhúng (sinh tự động)\n"
         + du_lieu.strip() + "\n(princ)\n")
    con_lai = [ln for ln in ma_hoa(s).splitlines() if not ln.lstrip().startswith(";")
               and any(ord(ch) > 127 for ch in ln.split(";")[0])]
    with open(dich, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(s)
    print(dich, "| dòng code còn ký tự ngoài ASCII:", len(con_lai))
    for ln in con_lai[:5]:
        print("  ", ln)


if __name__ == "__main__":
    main()
