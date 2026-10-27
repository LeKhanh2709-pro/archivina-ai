# -*- coding: utf-8 -*-
# Sinh các nút pyRevit (ARVTools.extension) từ bộ graph Dynamo ARV_*_v1.
#
# Cách chạy:
#   python build_from_dynamo.py <thư mục chứa ARV_*_v1.dyn + .py> [thư mục extension] [--chi <Nút>[,<Nút>]]
# Mặc định thư mục extension = ARVTools.extension cạnh file này. --chi: chỉ sinh lại các nút được nêu.
# Nguồn bắt đầu bằng "../" (vd. ../dynamo/ChongTham_VeVenChanTuong) tính từ thư mục của file này.
#
# Mỗi nút: core.py (chép nguyên văn ARV_<Tên>_v1.py), inputs.json (IN[i] từ chú thích đầu file + Input node
# trong .dyn), script.py, bundle.yaml. File sinh tự động → sửa thì sửa .py / .dyn gốc rồi chạy lại script này.
# core.py lấy từ file .py (bản .dyn có thể cũ hơn, vd. ARV_TaoCotVachTuCAD_v1); .dyn chỉ dùng để lấy giá trị đầu vào.

import io
import os
import re
import sys
import json
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# Tên tool → (panel, tên nút, tiêu đề hiện trên ribbon)
BUTTONS = [
    ("KetCau", "TaoTrucTuCAD", u"Tạo trục\ntừ CAD", "ARV_TaoTrucTuCSV_v1"),
    ("KetCau", "TaoCotVachTuCAD", u"Cột vách\ntừ CAD", "ARV_TaoCotVachTuCAD_v1"),
    ("KetCau", "TaoDamTuCAD", u"Dầm\ntừ CAD", "ARV_TaoDamTuCAD_v1"),
    ("KetCau", "VeBaoSanTuCAD", u"Bao sàn\ntừ CAD", "ARV_VeBaoSanTuCAD_v1"),
    ("KetCau", "CatTuongTheoDamSan", u"Cắt tường\ntheo dầm sàn", "ARV_CatTuongTheoDamSan_v1"),
    ("KienTruc", "TaoTuongTuCAD", u"Tường\ntừ CAD", "ARV_TaoTuongTuCAD_v1"),
    ("KienTruc", "TaoCuaTuCAD", u"Cửa đi\ntừ CAD", "ARV_TaoCuaTuCAD_v1"),
    ("KienTruc", "TaoCuaSoTuCAD", u"Cửa sổ\ntừ CAD", "ARV_TaoCuaSoTuCAD_v1"),
    ("KienTruc", "TaoGoLogia", u"Gờ\nlogia", "ARV_TaoGoLogia_v1"),
    ("KienTruc", "TaoLanCanLouverLogia", u"Lan can\nlouver logia", "ARV_TaoLanCanLouverLogia_v1"),
    ("HoanThien", "TaoSanHoanThien", u"Sàn hoàn thiện\n(có hatch)", "ARV_TaoSanHoanThien_v1"),
    ("HoanThien", "TaoSanCanHoTuCAD", u"Sàn căn hộ\ntừ CAD", "ARV_TaoSanCanHoTuCAD_v1"),
    ("HoanThien", "TaoTranCanHo", u"Trần\ncăn hộ", "ARV_TaoTranCanHo_v1"),
    ("HoanThien", "OpTuongWC", u"Ốp tường\nWC", "ARV_OpTuongWC_v1"),
    ("HoanThien", "TaoLenGo", u"Len\ngỗ", "ARV_TaoLenGo_v1"),
    ("HoanThien", "TaoLenGachLogia", u"Len gạch\nlogia", "ARV_TaoLenGachLogia_v1"),
    ("HoanThien", "DanTrangCanHo", u"Dàn trang\ncăn hộ", "ARV_DanTrangCanHo_v1"),
    ("MEP", "TaoThietBiWCTuCAD", u"Thiết bị WC\ntừ CAD", "ARV_TaoThietBiWCTuCAD_v1"),
    ("MEP", "TaoOngThoatNuocWC", u"Ống thoát\nnước WC", "ARV_TaoOngThoatNuocWC_v1"),
    ("MEP", "TaoOngThoatNuocTuCAD", u"Ống thoát nước\ntừ CAD", "ARV_TaoOngThoatNuocTuCAD_v1"),
    ("MEP", "TaoOngGioTuCAD", u"Ống gió\ntừ CAD", "ARV_TaoOngGioTuCAD_v1"),
    ("HoSo", "ChongTham", u"Chống\nthấm", "../dynamo/ChongTham_VeVenChanTuong"),
]
PANEL_TITLES = {"KetCau": u"Kết cấu", "KienTruc": u"Kiến trúc", "HoanThien": u"Hoàn thiện", "MEP": u"MEP",
                "HoSo": u"Hồ sơ"}
TAB = "ARV Tools.tab"

IN_RE = re.compile(r"^#\s*IN\[(\d+)\]\s*(?:\(([^)]*)\))?\s*(.*)$")
DYN_TYPES = {"StringInputNode": "str", "NumberInputNode": "float", "BooleanInputNode": "bool"}
DESTRUCTIVE_RE = re.compile(u"xoá|xóa|làm lại|tạo lại|thay lần chạy trước", re.I)

SCRIPT_PY = u'''#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""{doc}"""
__title__ = "{title}"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
'''


def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig") as f:
        return f.read().replace(u"\r\n", u"\n")


def parse_header(src):
    """Đọc khối chú thích đầu file: mô tả + IN[i] (kể cả dòng tiếp nối)."""
    lines = src.split(u"\n")
    summary, items, cur, section = [], {}, None, "desc"
    for ln in lines:
        if not ln.startswith(u"#"):
            if ln.strip() == u"" and section != "desc":
                continue
            if ln.strip() == u"":
                continue
            break
        body = ln[1:].strip()
        m = IN_RE.match(ln)
        if m:
            section = "in"
            cur = int(m.group(1))
            items[cur] = {"decl": (m.group(2) or u"").strip(), "text": m.group(3).strip()}
            continue
        up = body.upper()
        if up.startswith(u"INPUT") or up.startswith(u"ĐẦU VÀO"):
            section = "in"
            cur = None
            continue
        if up.startswith(u"OUTPUT") or up.startswith(u"ĐẦU RA"):
            section = "out"
            cur = None
            continue
        if section == "in" and cur is not None and body:
            items[cur]["text"] += u" " + body
        elif section == "desc" and body and not body.startswith(u"TRẠNG THÁI") \
                and not re.match(u"Revit 20\\d\\d / Dynamo", body) \
                and not body.startswith(u"Mã nguồn của Python node"):
            summary.append(body)
    return u" ".join(summary), items


def dyn_inputs(dyn_path):
    d = json.loads(read_text(dyn_path))
    nodes = {n["Id"]: n for n in d["Nodes"]}
    owner = {}
    for n in d["Nodes"]:
        for p in n.get("Outputs", []):
            owner[p["Id"]] = n["Id"]
    conn = {c["End"]: c["Start"] for c in d["Connectors"]}
    py = [n for n in d["Nodes"] if "PythonNode" in n.get("ConcreteType", "")]
    if len(py) != 1:
        raise Exception(u"{}: cần đúng 1 Python node, có {}".format(dyn_path, len(py)))
    res = []
    for port in py[0]["Inputs"]:
        st = conn.get(port["Id"])
        if not st:
            res.append(None)
            continue
        n = nodes[owner[st]]
        res.append((DYN_TYPES.get(n.get("NodeType"), "str"), n.get("InputValue")))
    return res


def transaction_name(src, fallback):
    m = re.search(r'^TRANSACTION_NAME\s*=\s*u?"([^"]+)"', src, re.M)
    return m.group(1) if m else fallback


def build_spec(key, title, py_path, dyn_path):
    src = read_text(py_path)
    summary, items = parse_header(src)
    dins = dyn_inputs(dyn_path)
    inputs, warn = [], []
    # Ô có trong chú thích .py nhưng .dyn chưa nối (bản .py mới hơn) → vẫn hiện, mặc định trống
    count = max([len(dins)] + [k + 1 for k in items])
    dins = dins + [None] * (count - len(dins))
    for i, dv in enumerate(dins):
        h = items.get(i, {"decl": u"", "text": u""})
        if dv is None and i in items:
            decl = h["decl"].lower()
            typ = "bool" if decl == "bool" else ("float" if decl in ("float", "num", "int") else "str")
            val = None
        elif dv is None:
            warn.append(u"IN[{}] không nối Input node".format(i))
            typ, val = "str", None
        else:
            typ, val = dv
        if typ == "float" and val is not None:
            val = float(val)
        if typ == "bool":
            val = bool(val) if not isinstance(val, str) else val.lower() == "true"
        label = h["text"] or u"(không có chú thích)"
        kind = "normal"
        if typ == "bool" and u"dry-run" in label.lower():
            kind = "dry_run"
        elif typ == "bool" and DESTRUCTIVE_RE.search(label):
            kind = "destructive"
        inputs.append({"index": i, "type": typ, "decl": h["decl"], "label": label, "default": val, "kind": kind})
    if not items:
        warn.append(u"không đọc được chú thích IN[i]")
    spec = {"key": key, "title": title.replace(u"\n", u" "), "summary": summary,
            "transaction": transaction_name(src, u"ARV - " + title.replace(u"\n", u" ")),
            "source": os.path.basename(py_path), "inputs": inputs}
    return spec, warn


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline=u"\n") as f:
        f.write(text)


def main():
    args = list(sys.argv[1:])
    chi = None
    if "--chi" in args:
        k = args.index("--chi")
        chi = set(args[k + 1].split(","))
        del args[k:k + 2]
    src_dir = args[0]
    ext = args[1] if len(args) > 1 else os.path.join(HERE, "ARVTools.extension")
    tab = os.path.join(ext, TAB)
    panels = []
    for panel, name, title, tool in BUTTONS:
        if panel not in panels:
            panels.append(panel)
        if chi and name not in chi:
            continue
        base = os.path.normpath(os.path.join(HERE, tool)) if tool.startswith("..") else os.path.join(src_dir, tool)
        tool = os.path.basename(tool)
        py_path = base + ".py"
        dyn_path = base + ".dyn"
        spec, warn = build_spec(name, title, py_path, dyn_path)
        bdir = os.path.join(tab, panel + ".panel", name + ".pushbutton")
        if not os.path.isdir(bdir):
            os.makedirs(bdir)
        shutil.copyfile(py_path, os.path.join(bdir, "core.py"))
        write(os.path.join(bdir, "inputs.json"), json.dumps(spec, ensure_ascii=False, indent=1))
        doc = (spec["summary"] or title).replace(u'"""', u"'''").replace(u"\\", u"/")
        tip = u"{} Mặc định chạy thử (dry-run). Nguồn: {}. TRẠNG THÁI: CHƯA DUYỆT.".format(
            spec["summary"][:400], tool + ".dyn")
        write(os.path.join(bdir, "script.py"), SCRIPT_PY.format(doc=doc, title=title.replace(u"\n", u"\\n")))
        write(os.path.join(bdir, "bundle.yaml"),
              u"title: {}\ntooltip: {}\nauthor: Archivina BIM\n".format(json.dumps(title, ensure_ascii=False),
                                                                       json.dumps(tip, ensure_ascii=False)))
        kinds = u", ".join(u"IN[{}]={}".format(it["index"], it["kind"]) for it in spec["inputs"]
                           if it["kind"] != "normal")
        print(u"{:24s} {:2d} đầu vào | {} {}".format(name, len(spec["inputs"]), kinds,
                                                     (u"| CẢNH BÁO: " + u"; ".join(warn)) if warn else u""))
    for panel in panels:
        if chi and not any(p == panel and n in chi for p, n, _, _ in BUTTONS):
            continue
        pdir = os.path.join(tab, panel + ".panel")
        order = [n for p, n, _, _ in BUTTONS if p == panel]
        write(os.path.join(pdir, "bundle.yaml"), u"title: {}\nlayout:\n{}".format(
            PANEL_TITLES[panel], u"".join(u"  - {}\n".format(n) for n in order)))
    write(os.path.join(tab, "bundle.yaml"), u"layout:\n{}".format(u"".join(u"  - {}\n".format(p) for p in panels)))


if __name__ == "__main__":
    main()
