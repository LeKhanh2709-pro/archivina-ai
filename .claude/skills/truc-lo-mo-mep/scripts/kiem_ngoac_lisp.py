"""Kiểm tra cân ngoặc file LISP (bỏ qua chuỗi và chú thích ;).

Thừa hoặc thiếu ngoặc thì AutoCAD chạy script /b sẽ chờ nhập tiếp và treo, nên chạy kiểm tra này
sau mỗi lần sửa / gộp Lomo.lsp.

Cách chạy:
    python kiem_ngoac_lisp.py <file.lsp>
Kết quả: "OK" hoặc dòng có ngoặc thừa / số ngoặc còn mở.
"""
import sys


def main():
    # chạy bằng python -I thì PYTHONUTF8 bị bỏ qua: tự đặt UTF-8 để in tiếng Việt
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    s = open(sys.argv[1], encoding="utf-8").read()
    sau, i, dong, trong_chuoi, loi = 0, 0, 1, False, False
    while i < len(s):
        c = s[i]
        if c == "\n":
            dong += 1
        if trong_chuoi:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                trong_chuoi = False
        elif c == ";":
            while i < len(s) and s[i] != "\n":
                i += 1
            continue
        elif c == '"':
            trong_chuoi = True
        elif c == "(":
            sau += 1
        elif c == ")":
            sau -= 1
            if sau < 0:
                print(f"Thừa ngoặc ')' ở dòng {dong}")
                sau, loi = 0, True
        i += 1
    if sau:
        print(f"Còn {sau} ngoặc '(' chưa đóng")
    print("OK" if not (sau or loi) else "LOI")
    sys.exit(1 if (sau or loi) else 0)


if __name__ == "__main__":
    main()
