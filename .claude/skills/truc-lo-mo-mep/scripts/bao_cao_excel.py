"""Đổi file CSV kết quả của lệnh amep:chay sang Excel có nhãn tiếng Việt, in tóm tắt số ô.

Cách chạy:
    python bao_cao_excel.py <ket_qua_amep.csv> <ket_qua_amep.xlsx>
In ra các dòng TONG_SO_O, DA_CHEN, DA_CO, XEM_LAI, VUOT_GIOI_HAN (dùng cho log).
"""
import csv
import sys
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

NHAN_TT = {
    "da_chen": "Đã chèn",
    "se_chen": "Chưa chèn (lỗi chèn)",
    "da_co": "Đã có A-MEP",
    "xem_lai": "Không tách được thành chữ nhật - Cần xác nhận lại",
    "vuot": "Vượt giới hạn block - Cần xác nhận lại",
}
NHAN_KIEU = {
    "X": "Dấu X trục / hộp",
    "LOMO_ONG": "Lỗ mở có ống đứng",
    "KHUNG_ONG": "Khung lỗ mở MEP có ống (không có X)",
    "KHAC": "Khác",
    "X_XOAY": "Dấu X trục / hộp, xoay xiên",
    "LOMO_ONG_XOAY": "Lỗ mở có ống đứng, xoay xiên",
    "KHUNG_ONG_XOAY": "Khung lỗ mở MEP có ống (không có X), xoay xiên",
}
COT = [
    ("stt", "STT"), ("trang_thai", "Trạng thái"), ("cx", "Tâm X"), ("cy", "Tâm Y"),
    ("rong", "Rộng ô (X)"), ("dai", "Cao ô (Y)"), ("d1", "Distance1 (cạnh dài)"),
    ("d2", "Distance2 (cạnh ngắn)"), ("goc", "Góc chèn"), ("ins_x", "Điểm chèn X"),
    ("ins_y", "Điểm chèn Y"), ("lech", "Lệch do làm tròn (mm)"), ("ti_le", "Tỉ lệ chữ nhật"),
    ("so_ong", "Số ống đứng"), ("kieu", "Kiểu"), ("vung", "Vùng trục / hộp"),
    ("so_khung", "Số khung bo của vùng"),
]


def main():
    if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if dst.exists():
        raise SystemExit(f"Đã tồn tại, không ghi đè: {dst}")
    with src.open(encoding="utf-8", newline="") as f:
        hang = list(csv.DictReader(f))

    wb = Workbook()
    ws = wb.active
    ws.title = "A-MEP"
    ws.append([t for _, t in COT])
    for c in ws[1]:
        c.font = Font(bold=True)
    for h in hang:
        dong = []
        for k, _ in COT:
            v = h.get(k, "")
            if k == "trang_thai":
                v = NHAN_TT.get(v, v)
            elif k == "kieu":
                v = NHAN_KIEU.get(v, v)
            else:
                try:
                    v = float(v)
                    v = int(v) if v.is_integer() else v
                except ValueError:
                    pass
            dong.append(v)
        ws.append(dong)
    ws.freeze_panes = "A2"
    for i, (_, t) in enumerate(COT, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = max(10, len(t) + 2)
    wb.save(dst)

    dem = Counter(h["trang_thai"] for h in hang)
    if hang and "vung" in hang[0]:
        print(f"TONG_SO_VUNG {len({h['vung'] for h in hang})}")
        print(f"VUNG_TACH_NHIEU_KHUNG {len({h['vung'] for h in hang if int(h['so_khung']) > 1})}")
    print(f"TONG_SO_O {len(hang)}")
    print(f"DA_CHEN {dem['da_chen']}")
    print(f"CHUA_CHEN_LOI {dem['se_chen']}")
    print(f"DA_CO {dem['da_co']}")
    print(f"XEM_LAI {dem['xem_lai']}")
    print(f"VUOT_GIOI_HAN {dem['vuot']}")
    print(dst)


if __name__ == "__main__":
    main()
