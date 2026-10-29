"""Sinh scripts\\lisp\\K-TOOL.lsp từ K-TOOL_nguon.lsp: chữ có dấu trong dòng lệnh (không phải dòng chú thích)
đổi thành \\U+XXXX để AutoLISP hiện đúng cả khi LISPSYS = 0. Chạy: python gop_ktool.py <file đích>."""
import sys
from pathlib import Path

nguon = Path(__file__).resolve().parent / 'K-TOOL_nguon.lsp'
dich = Path(sys.argv[1])

ra = []
for dong in nguon.read_text(encoding='utf-8').split('\n'):
    if dong.lstrip().startswith(';') or all(ord(c) < 128 for c in dong):
        ra.append(dong)
    else:
        ra.append(''.join(c if ord(c) < 128 else '\\U+%04X' % ord(c) for c in dong))
dich.write_text('\n'.join(ra), encoding='utf-8', newline='\n')
so_dong = sum(1 for d in ra if '\\U+' in d)
print(f'{dich}: {so_dong} dong da doi chu co dau')
