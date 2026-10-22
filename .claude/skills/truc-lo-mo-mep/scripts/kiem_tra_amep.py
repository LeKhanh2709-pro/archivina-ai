"""Kiểm tra bản sao DWG sau khi chèn A-MEP (đọc file DXF xuất từ bản sao).

Đếm A-MEP chèn thẳng trong Model hoặc nằm trong block gom "LO MO MEP*", in layer của chúng
(phải là A-MEP), rồi so khung từng A-MEP với các khung "da_chen" trong file CSV kết quả.

Cách chạy:
    python kiem_tra_amep.py <ban_sao.dxf> [<ket_qua_amep.csv>]
"""
import csv
import sys
from collections import Counter

import ezdxf


def main():
    # chạy bằng python -I thì PYTHONUTF8 bị bỏ qua: tự đặt UTF-8 để in tiếng Việt
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    d = ezdxf.readfile(sys.argv[1])
    br_amep = d.block_records.get("A-MEP")
    if br_amep is None:
        raise SystemExit("Bản vẽ không có block A-MEP")
    rep = br_amep.dxf.handle

    def la_amep(ten):
        # A-MEP đã kéo giãn mang tên *U.., trỏ về A-MEP qua xdata AcDbBlockRepBTag
        br = d.block_records.get(ten)
        return ten == "A-MEP" or (br is not None and br.has_xdata("AcDbBlockRepBTag")
                                  and br.get_xdata("AcDbBlockRepBTag")[1].value == rep)

    khung, gom = [], []

    def quet(ds_insert, m_cha, noi):
        for i in ds_insert:
            ten = i.dxf.name
            m = i.matrix44() * m_cha if m_cha is not None else i.matrix44()
            if la_amep(ten):
                for e in d.blocks[ten]:
                    if e.dxftype() == "LWPOLYLINE" and e.closed:
                        ps = [m.transform((p[0], p[1], 0)) for p in e.get_points()]
                        khung.append((min(p.x for p in ps), min(p.y for p in ps),
                                      max(p.x for p in ps), max(p.y for p in ps), noi, i.dxf.layer))
            elif ten.upper().startswith("LO MO MEP"):
                gom.append((ten, i.dxf.layer, tuple(i.dxf.insert)))
                quet(d.blocks[ten].query("INSERT"), m, "trong " + ten)

    quet(d.modelspace().query("INSERT"), None, "Model")
    print("Block gom:", gom)
    print("A-MEP theo vị trí:", dict(Counter(k[4] for k in khung)))
    print("Layer của A-MEP:", dict(Counter(k[5] for k in khung)))

    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8", newline="") as f:
            hang = [h for h in csv.DictReader(f) if h["trang_thai"] == "da_chen"]
        lech_max, khong_khop = 0.0, 0
        for h in hang:
            cx, cy, w, ht = (float(h[k]) for k in ("cx", "cy", "rong", "dai"))
            k = (cx - w / 2, cy - ht / 2, cx + w / 2, cy + ht / 2)
            lech = min((max(abs(a - b) for a, b in zip(k, q[:4])) for q in khung), default=1e9)
            if lech > 10:
                khong_khop += 1
                print(f"  Không khớp: STT {h['stt']} tâm ({cx:.0f}, {cy:.0f}), lệch {lech:.1f} mm")
            lech_max = max(lech_max, lech)
        print(f"Khung đã chèn: {len(hang)} | không khớp: {khong_khop} | lệch lớn nhất: {lech_max:.2f} mm")


if __name__ == "__main__":
    main()
