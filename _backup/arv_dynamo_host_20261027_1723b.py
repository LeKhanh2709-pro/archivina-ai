# -*- coding: utf-8 -*-
# Chạy mã Python node của các graph Dynamo ARV_*_v1 trong pyRevit (engine CPython 3).
#
# Mỗi nút pyRevit gồm:
#   core.py      – nguyên văn mã Python node của graph Dynamo (chép từ ARV_<Tên>_v1.py, không sửa tay)
#   inputs.json  – danh sách IN[i]: nhãn, kiểu, giá trị mặc định (lấy từ Input node trong .dyn)
#   script.py    – gọi run_button() của module này
#
# Thay phần Dynamo bằng phần tương đương của pyRevit:
#   IN[i]                                  → giá trị người dùng nhập trong hộp thoại
#   DocumentManager.Instance.*             → document / UIApplication đang mở
#   TransactionManager.Instance.*          → Transaction tự quản (ForceCloseTransaction không làm gì)
#   OUT                                    → in ra cửa sổ báo cáo của pyRevit
#   ProtoGeometry / DynamoRevitDS          → không có; các đoạn dùng chúng trong core.py đều nằm trong try
#
# Giá trị đã nhập được nhớ theo từng máy tại %APPDATA%\pyRevit\ARVTools\<nút>.json.
# Ô Dry-run luôn bật lại mỗi lần mở hộp thoại; ô xoá / làm lại luôn tắt lại và phải xác nhận khi bật.

import io
import os
import re
import sys
import json
import types
import datetime
import traceback

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import Transaction, TransactionStatus

# Các assembly chỉ có trong Dynamo: core.py gọi clr.AddReference ở cấp module → bỏ qua
_DYNAMO_ASSEMBLIES = ("RevitServices", "DynamoCore", "DynamoRevitDS", "ProtoGeometry", "RevitNodes")
_ADDREF_RE = re.compile(r'clr\.AddReference\(\s*[uU]?["\'](RevitServices|RevitNodes)["\']\s*\)')
_LIST_IMPORT_RE = re.compile(r'^([ \t]*)from System\.Collections\.Generic import List[ \t]*$', re.M)
# Dòng báo của core.py chỉ có nghĩa trong Dynamo (đánh dấu node chạy lại) → không in ra
_DYNAMO_ONLY_NOTE = u"LƯU Ý: Không đánh dấu được node chạy lại"


class _TypedList(object):
    """Thay System.Collections.Generic.List: pythonnet của pyRevit không tự đổi list Python sang
    IEnumerable<T> (vd. List[BuiltInCategory]([...]) báo lỗi) → tạo List rỗng rồi Add từng phần tử."""

    def __init__(self, generic):
        self._generic = generic

    def __getitem__(self, item_type):
        real = self._generic[item_type]

        def make(*args):
            if len(args) == 1 and not isinstance(args[0], int) and hasattr(args[0], "__iter__"):
                lst = real()
                for x in args[0]:
                    lst.Add(x)
                return lst
            return real(*args)
        return make

SETTINGS_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools")


# ---------------------------------------------------------------- giả lập RevitServices

class _DocumentManager(object):
    def __init__(self, uiapp):
        self._uiapp = uiapp

    @property
    def CurrentUIApplication(self):
        return self._uiapp

    @property
    def CurrentUIDocument(self):
        return self._uiapp.ActiveUIDocument

    @property
    def CurrentDBDocument(self):
        return self._uiapp.ActiveUIDocument.Document


class _TransactionManager(object):
    """Thay TransactionManager của Dynamo: EnsureInTransaction mở 1 Transaction có tên, TransactionTaskDone ghi."""

    def __init__(self, name):
        self._name = name
        self._tx = None

    def ForceCloseTransaction(self):
        # Trong Dynamo dùng để đóng transaction của Dynamo trước khi mở Transaction riêng; ở pyRevit không có gì để đóng
        self.TransactionTaskDone()

    def EnsureInTransaction(self, doc):
        if self._tx is None or self._tx.GetStatus() != TransactionStatus.Started:
            self._tx = Transaction(doc, self._name)
            self._tx.Start()

    def TransactionTaskDone(self):
        if self._tx is not None and self._tx.GetStatus() == TransactionStatus.Started:
            self._tx.Commit()
        self._tx = None

    def rollback_open(self):
        if self._tx is not None and self._tx.GetStatus() == TransactionStatus.Started:
            self._tx.RollBack()
        self._tx = None


class _Holder(object):
    def __init__(self, inst):
        self.Instance = inst


def _install_revitservices(uiapp, tx_name):
    dm, tm = _DocumentManager(uiapp), _TransactionManager(tx_name)
    pkg = types.ModuleType("RevitServices")
    per = types.ModuleType("RevitServices.Persistence")
    trs = types.ModuleType("RevitServices.Transactions")
    per.DocumentManager = _Holder(dm)
    trs.TransactionManager = _Holder(tm)
    pkg.Persistence, pkg.Transactions = per, trs
    saved = {k: sys.modules.get(k) for k in ("RevitServices", "RevitServices.Persistence",
                                             "RevitServices.Transactions")}
    sys.modules["RevitServices"] = pkg
    sys.modules["RevitServices.Persistence"] = per
    sys.modules["RevitServices.Transactions"] = trs
    return tm, saved


def _restore_modules(saved):
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


# ---------------------------------------------------------------- chạy core.py

def load_core(core_path):
    with io.open(core_path, "r", encoding="utf-8-sig") as f:
        src = f.read()
    # clr.AddReference("RevitServices") sẽ lỗi vì Revit không nạp assembly này ngoài Dynamo → đổi thành RevitAPI
    src = _ADDREF_RE.sub(u'clr.AddReference("RevitAPI")', src)
    # Giữ nguyên dòng import, gán lại List ngay sau đó (cùng dòng để không đổi số dòng khi báo lỗi)
    return _LIST_IMPORT_RE.sub(u'\\1from System.Collections.Generic import List; List = __arv_typed_list__(List)', src)


def run_core(core_path, inputs, uiapp, tx_name):
    """Chạy core.py với IN = inputs. Trả về OUT (hoặc danh sách dòng lỗi)."""
    src = load_core(core_path)
    tm, saved = _install_revitservices(uiapp, tx_name)
    g = {"__name__": "__arv_core__", "__file__": core_path, "IN": list(inputs), "__arv_typed_list__": _TypedList}
    try:
        code = compile(src, core_path, "exec")
        exec(code, g)
        return g.get("OUT", [u"core.py không gán OUT."])
    except Exception as ex:
        return [u"LỖI: {}".format(ex), traceback.format_exc()]
    finally:
        tm.rollback_open()
        _restore_modules(saved)


def flatten_report(out):
    """OUT của Dynamo: list[str] hoặc [list[str], preview]; lấy phần chữ."""
    if isinstance(out, (list, tuple)) and out and isinstance(out[0], (list, tuple)):
        out = out[0]
    if not isinstance(out, (list, tuple)):
        out = [out]
    lines = []
    for x in out:
        if isinstance(x, (list, tuple)):
            lines.extend(u"{}".format(y) for y in x)
        else:
            lines.append(u"{}".format(x))
    return [ln for ln in lines if not ln.startswith(_DYNAMO_ONLY_NOTE)]


# ---------------------------------------------------------------- nhớ giá trị đã nhập

def _settings_path(key):
    return os.path.join(SETTINGS_DIR, key + ".json")


def load_saved(key):
    try:
        with io.open(_settings_path(key), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_values(key, values):
    try:
        if not os.path.isdir(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR)
        with io.open(_settings_path(key), "w", encoding="utf-8") as f:
            f.write(json.dumps(values, ensure_ascii=False, indent=1))
    except Exception:
        pass


def is_dry_run(item):
    return item["kind"] == "dry_run"


def is_destructive(item):
    return item["kind"] == "destructive"


def initial_values(spec, key):
    """Giá trị khởi đầu: lần nhập trước (nếu có) → mặc định trong .dyn. Dry-run luôn bật, ô xoá luôn tắt."""
    saved = load_saved(key)
    vals = []
    for it in spec["inputs"]:
        v = saved.get(str(it["index"]), it["default"])
        if is_dry_run(it):
            v = True
        elif is_destructive(it):
            v = False
        vals.append(v)
    return vals


def convert(item, raw):
    t = item["type"]
    if t == "bool":
        return bool(raw)
    if raw is None:
        return None
    if t == "float":
        s = u"{}".format(raw).strip().replace(u",", u".")
        if s == u"":
            return None
        return float(s)
    return u"{}".format(raw)


# ---------------------------------------------------------------- hộp thoại WinForms

def ask_inputs(spec, values):
    """Hộp thoại nhập IN[i]. Trả về list giá trị, hoặc None nếu bấm Huỷ."""
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Windows.Forms import (Form, Label, TextBox, CheckBox, Button, Panel, DialogResult,
                                      FormBorderStyle, FormStartPosition, AnchorStyles, DockStyle,
                                      MessageBox, MessageBoxButtons, MessageBoxIcon)
    from System.Drawing import Size, Point, Font, FontStyle, Color

    form = Form()
    form.Text = spec["title"]
    form.StartPosition = FormStartPosition.CenterScreen
    form.FormBorderStyle = FormBorderStyle.Sizable
    form.MinimizeBox = False
    form.MaximizeBox = True
    form.Size = Size(760, 720)
    form.Font = Font("Segoe UI", 9.0)

    body = Panel()
    body.Dock = DockStyle.Fill
    body.AutoScroll = True
    bottom = Panel()
    bottom.Dock = DockStyle.Bottom
    bottom.Height = 48

    width = 700
    y = 8
    head = Label()
    head.Text = spec.get("summary", u"")
    head.Location = Point(10, y)
    head.MaximumSize = Size(width, 0)
    head.AutoSize = True
    head.ForeColor = Color.DimGray
    body.Controls.Add(head)
    y += head.PreferredHeight + 12

    controls = []
    for it, v in zip(spec["inputs"], values):
        lab = Label()
        lab.Text = u"IN[{}]  {}".format(it["index"], it["label"])
        lab.Location = Point(10, y)
        lab.MaximumSize = Size(width, 0)
        lab.AutoSize = True
        if is_dry_run(it) or is_destructive(it):
            lab.Font = Font(form.Font, FontStyle.Bold)
        if is_destructive(it):
            lab.ForeColor = Color.DarkRed
        body.Controls.Add(lab)
        y += lab.PreferredHeight + 2
        if it["type"] == "bool":
            c = CheckBox()
            c.Text = u"Bật" if not is_dry_run(it) else u"Dry-run (chỉ báo cáo, không ghi vào mô hình)"
            c.AutoSize = True
            c.Checked = bool(v)
        else:
            c = TextBox()
            c.Width = width - 10
            c.Text = u"" if v is None else (u"{:g}".format(v) if isinstance(v, float) else u"{}".format(v))
        c.Location = Point(14, y)
        body.Controls.Add(c)
        controls.append(c)
        y += 30

    ok = Button()
    ok.Text = u"Chạy"
    ok.Size = Size(100, 30)
    ok.Location = Point(530, 9)
    ok.Anchor = AnchorStyles.Right | AnchorStyles.Top
    cancel = Button()
    cancel.Text = u"Huỷ"
    cancel.Size = Size(100, 30)
    cancel.Location = Point(640, 9)
    cancel.Anchor = AnchorStyles.Right | AnchorStyles.Top
    cancel.DialogResult = DialogResult.Cancel
    bottom.Controls.Add(ok)
    bottom.Controls.Add(cancel)
    form.AcceptButton = ok
    form.CancelButton = cancel

    result = {"values": None}

    def on_ok(sender, e):
        vals = []
        for it, c in zip(spec["inputs"], controls):
            raw = c.Checked if it["type"] == "bool" else c.Text
            try:
                vals.append(convert(it, raw))
            except Exception:
                MessageBox.Show(u"IN[{}] phải là số: '{}'".format(it["index"], raw), spec["title"],
                                MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
        result["values"] = vals
        form.DialogResult = DialogResult.OK
        form.Close()

    ok.Click += on_ok
    form.Controls.Add(body)
    form.Controls.Add(bottom)
    form.ShowDialog()
    return result["values"]


def confirm(title, message):
    clr.AddReference("System.Windows.Forms")
    from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult
    return MessageBox.Show(message, title, MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes


# ---------------------------------------------------------------- nút pyRevit

def _print_report(title, inputs, spec, lines):
    try:
        from pyrevit import script
        out = script.get_output()
        out.set_title(title)
        md = out.print_md
    except Exception:
        md = print
    md(u"## {}".format(title))
    md(u"Chạy lúc {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    for it, v in zip(spec["inputs"], inputs):
        print(u"  IN[{}] {} = {}".format(it["index"], it["label"][:60], v))
    print(u"-" * 60)
    for ln in lines:
        print(ln)


def _auto_report(spec, button_dir, uiapp):
    """Chạy thử tự động (biến môi trường ARV_TOOLS_AUTO_REPORT = file báo cáo): không hộp thoại, dry-run,
    giá trị mặc định trong inputs.json, ghi thêm kết quả vào file báo cáo."""
    path = os.environ.get("ARV_TOOLS_AUTO_REPORT")
    t0 = datetime.datetime.now()
    try:
        lines = run_button(button_dir, uiapp, ask=False)
    except Exception:
        lines = [u"LỖI WRAPPER", traceback.format_exc()]
    with io.open(path, "a", encoding="utf-8") as f:
        f.write(u"=== {} ({:.1f} s) | Python {}\n".format(spec["key"], (datetime.datetime.now() - t0).total_seconds(),
                                                         sys.version.split()[0]))
        for ln in lines[:12]:
            f.write(u"   " + ln[:3000].replace(u"\n", u"\n   ") + u"\n")


def run_button(button_dir, uiapp, ask=True, overrides=None):
    """Gọi từ script.py của nút. ask=False: không hiện hộp thoại (dùng khi chạy thử tự động)."""
    with io.open(os.path.join(button_dir, "inputs.json"), "r", encoding="utf-8") as f:
        spec = json.load(f)
    if ask and os.environ.get("ARV_TOOLS_AUTO_REPORT"):
        return _auto_report(spec, button_dir, uiapp)
    key = spec["key"]
    values = initial_values(spec, key)
    if overrides:
        for i, v in overrides.items():
            values[int(i)] = v
    if ask:
        values = ask_inputs(spec, values)
        if values is None:
            return None
        save_values(key, {str(it["index"]): v for it, v in zip(spec["inputs"], values)
                          if not is_dry_run(it) and not is_destructive(it)})
        dry = any(v for it, v in zip(spec["inputs"], values) if is_dry_run(it))
        bad = [it for it, v in zip(spec["inputs"], values) if is_destructive(it) and v]
        if bad and not dry:
            msg = u"Đã bật tuỳ chọn có XOÁ phần tử trong mô hình:\n\n{}\n\nTiếp tục?".format(
                u"\n".join(u"- IN[{}] {}".format(it["index"], it["label"]) for it in bad))
            if not confirm(spec["title"], msg):
                return None
    out = run_core(os.path.join(button_dir, "core.py"), values, uiapp, spec["transaction"])
    lines = flatten_report(out)
    if ask:
        _print_report(spec["title"], values, spec, lines)
    return lines
