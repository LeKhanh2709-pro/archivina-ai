# ==== PHẦN CHUNG ĐẶT SHEET (nguồn: DatSheet_chung.py, chép vào file công cụ bằng gop_dat_sheet.py – sửa ở nguồn) ====
# Đặt mặt bằng vừa vẽ lên bản vẽ (người dùng yêu cầu 2026-11-03 cho Chống thấm + Ngăn cháy lan, cùng cách nút Tag cửa):
#   - Tạo sheet: khung tên theo khổ (A1 / A0), số hiệu (trống = tiếp theo trong hạng mục), tên, gán giai đoạn / hạng mục
#     theo cách nhóm sheet trong Project Browser của dự án (giống cap_thu_muc_sheet / ts_giai_doan của TagCua_TuDong.py).
#   - Mặt bằng đặt GIỮA vùng vẽ, giữ nguyên tỉ lệ của view (không sửa view template), "Title on Sheet" = tên sheet nếu
#     đang trống. View đã nằm trên sheet thì không đặt thêm.
#   - Thu trục của file hiện tại trong view về sát quanh nhà (đầu trục ViewSpecific, cách mép tường SH_TRUC_DU_MM giấy)
#     để khung viewport không bị trục dài đẩy lệch / tràn khổ (thử G19: trục A, X1 làm khung rộng 720 > 681 mm).
#   - Chú thích (ô mẫu hatch / nét + chữ) vẽ trong drafting view "CHÚ THÍCH - <tên sheet>" cùng tỉ lệ mặt bằng (mẫu
#     hatch theo model co giãn đúng như trên mặt bằng), đặt sát góc phải dưới vùng vẽ. Chữ chỉ là tên vùng, không ghi
#     vật liệu / chiều cao vén (chưa có số liệu).
# Tạo view khi tầng chưa có (người dùng yêu cầu 2026-11-04, "tạo view, đặt template như MB định vị cửa"): sh_tao_view
#   nhân bản mặt bằng tầng đang mở (không kèm chú thích) thành "<MẪU> - <tầng>", loại view riêng (mục riêng trong
#   Project Browser), gán view template có chữ khoá trong tên (vd. G19 "1.7 Mặt Bằng Chống thấm"); chưa có thì tạo
#   template mới từ template của view gốc: sàn Halftone + tắt mẫu tô, ẩn nội thất / thiết bị cơ điện / ký hiệu mặt
#   đứng, mặt cắt; tường / cột / vách + ẩn trục link như MB định vị cửa (sh_trinh_bay_template, cũng bổ sung cho
#   template công cụ đã tạo trước). KHÔNG ẩn hạng mục thiết bị vệ sinh (công cụ ẩn từng cái, giữ phễu thoát sàn).
#   Template mới: kiểu hiển thị Hidden Line, TẮT các filter chép theo view gốc (thử G19: filter vật liệu sàn tô đặc cả mặt bằng), không xoá filter.
#   View mới: crop = khung bao tường + SH_CROP_DU_MM giấy (view gốc G19 crop rất lớn → mặt bằng trôi ra ngoài khổ).
#   Template đã có thì dùng nguyên, không sửa. Không sửa view gốc / template gốc.
#   ĐỔI 2026-11-05 (người dùng yêu cầu): KHÔNG tạo / sửa view template nữa (bỏ phần tạo template ở trên). Hộp thoại nút
#   hỏi View template + Tỉ lệ → sh_ap_tpl_tl gán đúng template đã chọn (hoặc bỏ template) + tỉ lệ cho view (mới hoặc đã
#   có); template khoá tỉ lệ thì giữ tỉ lệ template, chỉ báo. sh_chuan_template không còn làm gì.
# Hàm, hằng ở khối này có tiền tố sh_ / SH_ để không trùng tên với file công cụ.
SH_BIEN_MM = 8.0             # lề trong vùng vẽ của khung tên (mm giấy)
SH_TIEU_DE_MM = 15.0         # chỗ tên view dưới viewport
SH_O_MAU_MM = (16.0, 7.0)    # ô mẫu chú thích (rộng, cao) mm giấy
SH_DONG_MM = 11.0            # khoảng cách dòng chú thích
SH_KHE_CHU_MM = 4.0          # khe giữa ô mẫu và chữ
SH_AN_VIEW_MOI = ("OST_Furniture", "OST_FurnitureSystems", "OST_Casework", "OST_SpecialityEquipment",
                  "OST_MechanicalEquipment", "OST_Elev", "OST_Sections")   # hạng mục ẩn trong template mới
SH_HALFTONE_VIEW_MOI = ("OST_Floors",)          # tường: theo filter tường xây / vách BTCT như MB định vị cửa
# Tường / cột / vách + ẩn trục link như template MB định vị cửa (người dùng yêu cầu 2026-11-04; chép từ
# TagCua_TuDong.py, cùng tên filter nên các công cụ dùng chung filter)
SH_FILTER_TRUC_LINK = u"ARV_Ẩn trục file link"
SH_FILTER_BTCT = u"ARV_Vách BTCT"
SH_FILTER_XAY = u"ARV_Tường xây"
SH_FILTER_COT = u"ARV_Cột BTCT"
SH_TU_KHOA_BTCT = (u"BTCT", u"VBT", u"WS_", u"Concrete", u"Bê tông")
SH_MAU_TO_BTCT = (100, 100, 100)
SH_COT_BTCT = ("OST_StructuralColumns", "OST_Columns")
SH_CROP_DU_MM = 35.0         # view mới: crop = khung bao tường + lề này (mm giấy), đủ chỗ bóng trục đã thu (20 mm)
SH_TRUC_DU_MM = 20.0         # đầu trục cách mép nhà (mm giấy) khi thu trục (như nút Tag cửa, người dùng duyệt 2026-11-03)


def sh_ft(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def sh_mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def sh_kd(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def sh_ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        pass
    try:
        return e.Name
    except Exception:
        return u"?"


def sh_ts(e, pid):
    for prm in e.Parameters:
        if prm.Id.Value == pid.Value:
            return prm
    return None


def sh_gt(prm):
    try:
        return (prm.AsString() or u"") if prm.StorageType == StorageType.String else (prm.AsValueString() or u"")
    except Exception:
        return u""


def sh_cap_thu_muc(doc):
    """Id tham số các cấp nhóm sheet trong Project Browser (vd. giai đoạn → hạng mục), đọc từ sheet đầu tiên có thư mục."""
    try:
        bo = BrowserOrganization.GetCurrentBrowserOrganizationForSheets(doc)
    except Exception:
        return []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        try:
            items = list(bo.GetFolderItems(s.Id))
        except Exception:
            continue
        if items:
            return [it.ElementId for it in items]
    return []


def sh_gd_hm(doc, cap):
    """(id tham số giai đoạn, id tham số hạng mục). Browser 2 cấp: cấp 1 = giai đoạn, cấp 2 = hạng mục. 1 cấp: cấp đó là
    hạng mục, giai đoạn = tham số sheet có chữ "giai đoạn" dùng nhiều nhất."""
    if len(cap) >= 2:
        return cap[0], cap[1]
    hm = cap[0] if cap else None
    dem = {}
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        for prm in s.Parameters:
            if prm.Definition is not None and prm.StorageType == StorageType.String and \
                    u"giai doan" in sh_kd(prm.Definition.Name) and (hm is None or prm.Id.Value != hm.Value):
                k = prm.Id.Value
                dem.setdefault(k, [prm.Id, 0])
                if prm.AsString():
                    dem[k][1] += 1
    gd = max(dem.values(), key=lambda x: x[1])[0] if dem else None
    return gd, hm


def sh_so_tiep(doc, pid_gd, gd, pid_hm, hm, mac_dinh):
    """Số hiệu tiếp theo trong cùng hạng mục (tăng phần số cuối, giữ số chữ số); hạng mục chưa có sheet thì mac_dinh."""
    import re
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    cung = []
    for s in FilteredElementCollector(doc).OfClass(ViewSheet):
        if pid_hm is not None and hm:
            p_ = sh_ts(s, pid_hm)
            if p_ is None or sh_gt(p_) != hm:
                continue
            if pid_gd is not None and gd:
                q_ = sh_ts(s, pid_gd)
                if q_ is not None and sh_gt(q_) and sh_gt(q_) != gd:
                    continue
            cung.append(s.SheetNumber)
    goc = None
    for so in sorted(cung):
        if re.search(r"\d+$", so):
            goc = so
    if goc is None:
        goc = mac_dinh
    m = re.search(r"(\d+)$", goc)
    dau, n, w = (goc[:m.start()], int(m.group(1)), len(m.group(1))) if m else (goc + u".", 0, 2)
    while True:
        n += 1
        ung = u"%s%0*d" % (dau, w, n)
        if ung not in dung:
            return ung


def sh_khung_ten(doc, kho, khung):
    ds = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks))
    if khung:
        for s in ds:
            if khung in (u"%s : %s" % (s.FamilyName, sh_ten(s)), sh_ten(s), s.FamilyName):
                return s
    k = sh_kd(kho or u"A1").replace(u" ", u"")
    ung = [s for s in ds if k in sh_kd(s.FamilyName + u" " + sh_ten(s)).replace(u" ", u"")
           and u"bia" not in sh_kd(s.FamilyName + u" " + sh_ten(s))]
    ung.sort(key=lambda s: (0 if u"khung" in sh_kd(s.FamilyName) else 1, s.FamilyName))
    return ung[0] if ung else None


def sh_net_khung(doc, tb_sym):
    """Nét đứng [(x, dài)] / ngang [(y, dài)] của family khung tên (toạ độ family), đọc trong file family (đóng không lưu)
    vì hình học khung tên trên sheet trả về rỗng. Gọi NGOÀI transaction."""
    dung, ngang = [], []
    fd = None
    try:
        TransactionManager.Instance.ForceCloseTransaction()
        fd = doc.EditFamily(tb_sym.Family)
        for c in FilteredElementCollector(fd).OfClass(CurveElement):
            try:
                g = c.GeometryCurve
                if g is None or not g.IsBound or g.GetType().Name != "Line":
                    continue
                a, b_ = g.GetEndPoint(0), g.GetEndPoint(1)
                if abs(a.X - b_.X) < 1e-6:
                    dung.append((a.X, abs(a.Y - b_.Y)))
                elif abs(a.Y - b_.Y) < 1e-6:
                    ngang.append((a.Y, abs(a.X - b_.X)))
            except Exception:
                pass
    except Exception:
        pass
    finally:
        if fd is not None:
            try:
                fd.Close(False)
            except Exception:
                pass
    return dung, ngang


def sh_vung_ve(sheet, tb_inst, net):
    """Vùng vẽ (x0, y0, x1, y1) trên sheet: trong khung trong, bên trái dải khung tên phải (đo từ nét dài của family
    khung tên; không đo được thì khung bao trừ lề 25 / 15 mm và 1/6 bên phải)."""
    tf = tb_inst.GetTotalTransform()
    dung = [(tf.OfPoint(XYZ(x, 0, 0)).X, l) for x, l in net[0]]
    ngang = [(tf.OfPoint(XYZ(0, y, 0)).Y, l) for y, l in net[1]]
    bb = tb_inst.get_BoundingBox(sheet)
    X0, Y0, X1, Y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
    W, H = X1 - X0, Y1 - Y0
    d40 = sh_ft(40.0)
    dai_d = [x for x, l in dung if l > 0.6 * H]
    dai_n = [y for y, l in ngang if l > 0.6 * W]
    x0 = max([x for x in dai_d if x < X0 + d40] or [X0 + sh_ft(25.0)])
    x1 = max([x for x in dai_d if X0 + d40 < x < X1 - d40] or [X1 - W / 6.0])
    y0 = max([y for y in dai_n if y < Y0 + d40] or [Y0 + sh_ft(15.0)])
    y1 = min([y for y in dai_n if y > Y1 - d40] or [Y1 - sh_ft(15.0)])
    return x0, y0, x1, y1


def sh_kieu_viewport(doc, co_tieu_de):
    """Kiểu viewport: co_tieu_de = có nhãn tên view (ưu tiên kiểu không phải 'no scale' / 'detail'); không thì kiểu tắt
    tên (Show Title = No). Không có kiểu phù hợp → None (giữ mặc định)."""
    kieu = []
    for et in FilteredElementCollector(doc).OfClass(ElementType):
        try:
            if et.FamilyName != "Viewport":
                continue
            hien = et.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_SHOW_LABEL)
            nhan = et.get_Parameter(BuiltInParameter.VIEWPORT_ATTR_LABEL_TAG)
            n = sh_kd(sh_ten(et))
            if co_tieu_de:
                if nhan is None or nhan.AsElementId() == ElementId.InvalidElementId or (hien is not None and hien.AsInteger() == 0):
                    continue
                kieu.append((0 if u"no scale" not in n and u"detail" not in n else 1, sh_ten(et), et))
            elif hien is not None and hien.AsInteger() == 0:
                kieu.append((0 if u"no title" in n else 1, sh_ten(et), et))
        except Exception:
            pass
    kieu.sort(key=lambda k: (k[0], k[1]))
    return kieu[0][2] if kieu else None


def sh_kieu_chu(doc):
    """Kiểu chữ chú thích: Arial cao 2–3 mm (gần 2.5 nhất), không có thì kiểu mặc định của dự án."""
    ung = []
    for t in FilteredElementCollector(doc).OfClass(TextNoteType):
        try:
            cao = sh_mm(t.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble())
            font = sh_kd(t.get_Parameter(BuiltInParameter.TEXT_FONT).AsString())
            if u"arial" in font and 1.9 <= cao <= 3.1:
                ung.append((abs(cao - 2.5), -cao, sh_ten(t), t.Id))
        except Exception:
            pass
    ung.sort(key=lambda k: (k[0], k[1], k[2]))
    return ung[0][3] if ung else doc.GetDefaultElementTypeId(ElementTypeGroup.TextNoteType)


def sh_thu_truc(doc, view):
    """Đầu trục của file hiện tại trong view → ViewSpecific, cắt theo khung bao tường + SH_TRUC_DU_MM × tỉ lệ. Chỉ đổi
    hiển thị trục trong view này (không đổi trục 3D / view khác); trục của link không sửa. Gọi TRONG transaction."""
    xs, ys = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(view)
        if bb is not None:
            xs += [bb.Min.X, bb.Max.X]
            ys += [bb.Min.Y, bb.Max.Y]
    if not xs:
        return u"Không có tường trong view – không thu trục."
    goc_bb = [XYZ(x, y, 0) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    du = sh_ft(SH_TRUC_DU_MM * view.Scale)
    n = 0
    for g in FilteredElementCollector(doc, view.Id).OfClass(Grid):
        try:
            if g.IsCurved:
                continue
            ds = g.GetCurvesInView(DatumExtentType.ViewSpecific, view)
            if ds is None or ds.Count != 1:
                continue
            cv = ds[0]
            p0, p1 = cv.GetEndPoint(0), cv.GetEndPoint(1)
            d = (p1 - p0).Normalize()
            ts = [(q.X - p0.X) * d.X + (q.Y - p0.Y) * d.Y for q in goc_bb]
            a, b = p0 + d * (min(ts) - du), p0 + d * (max(ts) + du)
            a, b = XYZ(a.X, a.Y, p0.Z), XYZ(b.X, b.Y, p1.Z)
            for dau in (DatumEnds.End0, DatumEnds.End1):
                if g.GetDatumExtentTypeInView(dau, view) != DatumExtentType.ViewSpecific:
                    g.SetDatumExtentType(dau, view, DatumExtentType.ViewSpecific)
            g.SetCurveInView(DatumExtentType.ViewSpecific, view, Line.CreateBound(a, b))
            n += 1
        except Exception:
            pass
    return u"Thu trục: %d trục cắt sát nhà (cách mép tường %g mm giấy)." % (n, SH_TRUC_DU_MM)


def sh_chu_thich(doc, ten_view, ti_le, muc):
    """Drafting view chú thích. muc: [{"vung": id kiểu Filled Region, "vien": id line style | None, "chu": u"..."} |
    {"net": GraphicsStyle, "chu": u"..."}]. Trả về (view, báo cáo). Gọi TRONG transaction."""
    for v in FilteredElementCollector(doc).OfClass(ViewDrafting):
        if not v.IsTemplate and v.Name == ten_view:
            sh_ = v.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
            if sh_ is not None and sh_.AsString() and sh_.AsString() not in (u"---", u"-"):
                return None, u"Chú thích '%s' đã nằm trên sheet %s – không đặt thêm." % (ten_view, sh_.AsString())
            return v, u"dùng lại view chú thích '%s'" % ten_view
    vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.Drafting]
    if not vft:
        return None, u"Dự án không có kiểu Drafting View – không vẽ chú thích."
    v = ViewDrafting.Create(doc, vft[0].Id)
    v.Name = ten_view
    v.Scale = ti_le
    s = float(ti_le)
    w, h = sh_ft(SH_O_MAU_MM[0] * s), sh_ft(SH_O_MAU_MM[1] * s)
    dong, khe = sh_ft(SH_DONG_MM * s), sh_ft(SH_KHE_CHU_MM * s)
    kc = sh_kieu_chu(doc)
    opt = TextNoteOptions(kc)
    opt.HorizontalAlignment = HorizontalTextAlignment.Left
    opt.VerticalAlignment = VerticalTextAlignment.Middle
    TextNote.Create(doc, v.Id, XYZ(0, 0, 0), u"CHÚ THÍCH:", opt)
    y = -dong
    for m in muc:
        yc = y
        if "vung" in m:
            cl = CurveLoop()
            p = [XYZ(0, yc - h / 2, 0), XYZ(w, yc - h / 2, 0), XYZ(w, yc + h / 2, 0), XYZ(0, yc + h / 2, 0)]
            for i in range(4):
                cl.Append(Line.CreateBound(p[i], p[(i + 1) % 4]))
            ds = NetList[CurveLoop]()
            ds.Add(cl)
            fr = FilledRegion.Create(doc, m["vung"], v.Id, ds)
            if m.get("vien") is not None:
                fr.SetLineStyleId(m["vien"])
        else:
            dc = doc.Create.NewDetailCurve(v, Line.CreateBound(XYZ(0, yc, 0), XYZ(w, yc, 0)))
            dc.LineStyle = m["net"]
        TextNote.Create(doc, v.Id, XYZ(w + khe, yc, 0), m["chu"], opt)
        y -= dong
    return v, u"tạo view chú thích '%s' (%d mục)" % (ten_view, len(muc))


SH_KHONG_TPL = u"<Không dùng view template>"    # giá trị ô View template của hộp thoại = bỏ template


def sh_tim_tpl(doc, ten_tpl):
    """View template mặt bằng theo tên (đúng tên, không thì không phân biệt hoa thường / dấu)."""
    ds = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if v.IsTemplate]
    for v in ds:
        if v.Name == ten_tpl:
            return v
    for v in ds:
        if sh_kd(v.Name).strip() == sh_kd(ten_tpl).strip():
            return v
    return None


def sh_tpl_khoa_tl(tpl):
    """Template điều khiển tỉ lệ (View Scale có trong template và đang được điều khiển)."""
    try:
        co = set(i.Value for i in tpl.GetTemplateParameterIds())
        nc = set(i.Value for i in tpl.GetNonControlledTemplateParameterIds())
    except Exception:
        return False
    for b in (BuiltInParameter.VIEW_SCALE_PULLDOWN_METRIC, BuiltInParameter.VIEW_SCALE):
        v = ElementId(b).Value
        if v in co and v not in nc:
            return True
    return False


def sh_ap_tpl_tl(doc, view, ten_tpl, ti_le):
    """Gán view template + tỉ lệ đã chọn trong hộp thoại (người dùng yêu cầu 2026-11-05). Gọi TRONG transaction.
    ten_tpl: trống = giữ template đang có; SH_KHONG_TPL = bỏ template; tên = gán template đó (không tạo, không sửa
    template). ti_le: mẫu số (0 = giữ); template khoá tỉ lệ thì tỉ lệ theo template, chỉ báo."""
    bao = []
    ten_tpl = (ten_tpl or u"").strip()
    if ten_tpl == SH_KHONG_TPL:
        if view.ViewTemplateId != ElementId.InvalidElementId:
            view.ViewTemplateId = ElementId.InvalidElementId
            bao.append(u"Bỏ view template của '%s'." % view.Name)
    elif ten_tpl:
        tpl = sh_tim_tpl(doc, ten_tpl)
        if tpl is None:
            bao.append(u"CẦN XEM LẠI: không có view template '%s' – giữ template đang có của '%s'." % (ten_tpl, view.Name))
        elif view.ViewTemplateId.Value != tpl.Id.Value:
            view.ViewTemplateId = tpl.Id
            bao.append(u"Gán view template '%s' cho '%s'." % (tpl.Name, view.Name))
        else:
            bao.append(u"View '%s' đã dùng template '%s'." % (view.Name, tpl.Name))
    try:
        ti_le = int(round(float(ti_le or 0)))
    except Exception:
        ti_le = 0
    if ti_le > 0:
        tpl = doc.GetElement(view.ViewTemplateId) if view.ViewTemplateId != ElementId.InvalidElementId else None
        if tpl is not None and sh_tpl_khoa_tl(tpl):
            if tpl.Scale != ti_le:
                bao.append(u"Template '%s' khoá tỉ lệ 1:%d → giữ 1:%d (không sửa template), không dùng 1:%d." % (
                    tpl.Name, tpl.Scale, tpl.Scale, ti_le))
        elif view.Scale != ti_le:
            view.Scale = ti_le
            bao.append(u"Tỉ lệ '%s': 1:%d." % (view.Name, ti_le))
    doc.Regenerate()
    return bao


def sh_tao_view(doc, goc, tu_khoa, ten_mau, dry, ten_tpl=u"", ti_le=0):
    """View mặt bằng mới cho tầng của view goc (xem chú thích đầu khối). tu_khoa: chữ khoá không dấu (vd. "chong tham")
    để nhận template có sẵn khi không chọn template; ten_mau: tên in hoa (vd. "MẶT BẰNG CHỐNG THẤM") = tên loại view và
    tiền tố tên view. ten_tpl / ti_le: template + tỉ lệ chọn trong hộp thoại (sh_ap_tpl_tl). KHÔNG tạo / sửa view template
    (người dùng chốt 2026-11-05): không chọn template thì dùng template có chữ khoá nếu có, không thì giữ template của
    view gốc. Trả về (view, [báo cáo]); dry: chỉ báo, trả về goc."""
    bao = []
    tang = goc.GenLevel.Name
    ten_moi = u"%s - %s" % (ten_mau, tang)
    ten_tpl = (ten_tpl or u"").strip()
    if not ten_tpl:
        for v in FilteredElementCollector(doc).OfClass(View):
            if v.IsTemplate and v.ViewType == ViewType.FloorPlan and tu_khoa in sh_kd(v.Name):
                if not ten_tpl or v.Name == ten_mau:
                    ten_tpl = v.Name
    if dry:
        bao.append(u"Sẽ tạo view '%s' (nhân bản '%s'), view template '%s'%s – Dry-run tính trên view gốc." % (
            ten_moi, goc.Name, ten_tpl or u"của view gốc",
            u", tỉ lệ 1:%d" % int(float(ti_le)) if ti_le else u""))
        return goc, bao
    TransactionManager.Instance.EnsureInTransaction(doc)
    moi = doc.GetElement(goc.Duplicate(ViewDuplicateOption.Duplicate))
    ten_dat, k = ten_moi, 1
    dung = set(v.Name for v in FilteredElementCollector(doc).OfClass(View) if not v.IsTemplate)
    while ten_dat in dung:
        k += 1
        ten_dat = u"%s (%d)" % (ten_moi, k)
    moi.Name = ten_dat
    bao.append(u"Tạo view '%s' (nhân bản '%s', không kèm chú thích)." % (ten_dat, goc.Name))
    try:          # loại view riêng → mục "Floor Plans (<MẪU>)" trong Project Browser, như Tag cửa
        vft = None
        for t_ in FilteredElementCollector(doc).OfClass(ViewFamilyType):
            if t_.ViewFamily == ViewFamily.FloorPlan and sh_ten(t_) == ten_mau:
                vft = t_
        if vft is None:
            vft = doc.GetElement(moi.GetTypeId()).Duplicate(ten_mau)
            bao.append(u"Tạo loại view '%s' (mục riêng trong Project Browser)." % ten_mau)
        if moi.GetTypeId().Value != vft.Id.Value:
            moi.ChangeTypeId(vft.Id)
    except Exception as ex:
        bao.append(u"Không gán được loại view '%s': %s" % (ten_mau, (u"%s" % ex).splitlines()[0][:150]))
    bao.extend(sh_ap_tpl_tl(doc, moi, ten_tpl, ti_le))
    try:
        bao.append(sh_crop_theo_tuong(doc, moi))
    except Exception as ex:
        bao.append(u"Không đặt được crop: %s" % (u"%s" % ex).splitlines()[0][:150])
    TransactionManager.Instance.TransactionTaskDone()
    return moi, bao


def sh_chuan_template(doc, view, ten_mau):
    """Trước 2026-11-05: bổ sung template công cụ tạo. Nay các nút không sửa view template nữa → không làm gì."""
    return []


def sh_trinh_bay_template(doc, tpl):
    """Template công cụ tạo: ẩn trục link + tường / cột / vách như MB định vị cửa; bật lại các filter ARV_. Gọi TRONG
    transaction."""
    bao = []
    for ham, nhan in ((sh_an_truc_link, u"ẩn trục file link"), (sh_trinh_bay_btct, u"tường / cột / vách")):
        try:
            bao.append(ham(doc, tpl))
        except Exception as ex:
            bao.append(u"Không chỉnh được %s: %s" % (nhan, (u"%s" % ex).splitlines()[0][:150]))
    for fid in list(tpl.GetFilters()):
        try:
            if sh_ten(doc.GetElement(fid)).startswith(u"ARV_") and not tpl.GetIsFilterEnabled(fid):
                tpl.SetIsFilterEnabled(fid, True)
        except Exception:
            pass
    return bao


def sh_bo_dieu_khien(tpl, bip):
    """Bỏ tham số bip khỏi danh sách KHÔNG điều khiển của template (để template điều khiển nó)."""
    try:
        pid = ElementId(bip)
        nc = list(tpl.GetNonControlledTemplateParameterIds())
        if any(i.Value == pid.Value for i in nc):
            ds = NetList[ElementId]()
            for i in nc:
                if i.Value != pid.Value:
                    ds.Add(i)
            tpl.SetNonControlledTemplateParameterIds(ds)
    except Exception:
        pass


def sh_an_truc_link(doc, tpl):
    """Ẩn trục của file link, giữ trục file hiện tại: filter Grids "Type Name khác mọi loại trục của file hiện tại", ẩn
    trong template (API 2027.3 không tắt riêng Grids của link theo view). Như an_truc_link của TagCua_TuDong.py."""
    loai_truc = sorted(set(sh_ten(doc.GetElement(g.GetTypeId())) for g in FilteredElementCollector(doc).OfClass(Grid)))
    if not loai_truc:
        return u"File không có trục riêng – không tạo filter ẩn trục link."
    cats = NetList[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Grids))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    pid = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            pid = ElementId(b_)
            break
    if pid is None:
        return u"Không có tham số tên loại lọc được cho Grids – chưa ẩn trục link (ẩn tay: V/G → Revit Links)."
    f_ = None
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name == SH_FILTER_TRUC_LINK:
            f_ = x
    loc = [ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(pid, t_)) for t_ in loai_truc]
    loc_net = NetList[ElementFilter]()
    for x in loc:
        loc_net.Add(x)
    bo = loc[0] if len(loc) == 1 else LogicalAndFilter(loc_net)
    if f_ is None:
        f_ = ParameterFilterElement.Create(doc, SH_FILTER_TRUC_LINK, cats, bo)
    else:
        f_.SetElementFilter(bo)
    sh_bo_dieu_khien(tpl, BuiltInParameter.VIS_GRAPHICS_FILTERS)
    if not any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        tpl.AddFilter(f_.Id)
    tpl.SetFilterVisibility(f_.Id, False)
    return u"Ẩn trục file link: filter '%s' (Grids, loại trục khác %s)." % (SH_FILTER_TRUC_LINK, u", ".join(loai_truc))


def sh_ghi_de_btct(dac):
    o = OverrideGraphicSettings()
    o.SetCutLineColor(Color(0, 0, 0))
    o.SetProjectionLineColor(Color(0, 0, 0))
    if dac is not None:
        o.SetCutForegroundPatternId(dac)
        o.SetCutForegroundPatternColor(Color(*SH_MAU_TO_BTCT))
        o.SetCutForegroundPatternVisible(True)
    return o


def sh_trinh_bay_btct(doc, tpl):
    """Tường xây Halftone không tô, cột + vách BTCT tô đặc xám đậm viền đen bằng 3 filter (như trinh_bay_btct của
    TagCua_TuDong.py: màu nét ghi đè theo hạng mục Walls không ăn trong Revit 2027.3). Template đã có filter vách BTCT
    thì giữ nguyên (người dùng có thể đã chỉnh tay)."""
    fs = {}
    for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
        if x.Name in (SH_FILTER_BTCT, SH_FILTER_XAY, SH_FILTER_COT):
            fs[x.Name] = x
    f_ = fs.get(SH_FILTER_BTCT)
    if f_ is not None and any(i.Value == f_.Id.Value for i in tpl.GetFilters()):
        return u"Tường / cột / vách: template đã có filter '%s', giữ nguyên." % SH_FILTER_BTCT
    dac = None
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        try:
            p_ = fp.GetFillPattern()
            if p_.IsSolidFill and p_.Target == FillPatternTarget.Drafting:
                dac = fp.Id
                break
        except Exception:
            pass
    sh_bo_dieu_khien(tpl, BuiltInParameter.VIS_GRAPHICS_FILTERS)
    o = OverrideGraphicSettings()          # thay cả ghi đè cũ của hạng mục Walls (bản trước để Halftone cả hạng mục)
    o.SetCutForegroundPatternVisible(False)
    o.SetCutBackgroundPatternVisible(False)
    tpl.SetCategoryOverrides(ElementId(BuiltInCategory.OST_Walls), o)
    cats = NetList[ElementId]()
    cats.Add(ElementId(BuiltInCategory.OST_Walls))
    loc_duoc = [p_.Value for p_ in ParameterFilterUtilities.GetFilterableParametersInCommon(doc, cats)]
    co, khong = [], []
    b_kc = BuiltInParameter.WALL_STRUCTURAL_USAGE_PARAM
    if int(b_kc) in loc_duoc:
        co.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0)))
        khong.append(ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(b_kc), 0), True))
    b_ten = None
    for b_ in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        if int(b_) in loc_duoc:
            b_ten = b_
            break
    for k in (SH_TU_KHOA_BTCT if b_ten is not None else ()):
        r_ = ParameterFilterRuleFactory.CreateContainsRule(ElementId(b_ten), k)
        co.append(ElementParameterFilter(r_))
        khong.append(ElementParameterFilter(r_, True))
    if not co:
        return u"Không có tham số lọc được để nhận vách BTCT – chỉnh tay trong V/G."

    def gop(ds_, lop):
        if len(ds_) == 1:
            return ds_[0]
        net = NetList[ElementFilter]()
        for x in ds_:
            net.Add(x)
        return lop(net)

    def dat(ten_f, cats_, bo, ghi_de):
        f = fs.get(ten_f)
        if f is None:
            f = (ParameterFilterElement.Create(doc, ten_f, cats_, bo) if bo is not None
                 else ParameterFilterElement.Create(doc, ten_f, cats_))
        elif bo is not None:
            f.SetElementFilter(bo)
        if not any(i.Value == f.Id.Value for i in tpl.GetFilters()):
            tpl.AddFilter(f.Id)
        tpl.SetFilterOverrides(f.Id, ghi_de)

    dat(SH_FILTER_BTCT, cats, gop(co, LogicalOrFilter), sh_ghi_de_btct(dac))
    o = OverrideGraphicSettings()
    o.SetHalftone(True)
    dat(SH_FILTER_XAY, cats, gop(khong, LogicalAndFilter), o)
    cats_cot = NetList[ElementId]()
    for n in SH_COT_BTCT:
        cats_cot.Add(ElementId(getattr(BuiltInCategory, n)))
    dat(SH_FILTER_COT, cats_cot, None, sh_ghi_de_btct(dac))
    return (u"Tường xây Halftone, không tô (filter '%s'); vách BTCT (filter '%s') + cột (filter '%s') tô đặc xám %s viền "
            u"đen, như MB định vị cửa." % (SH_FILTER_XAY, SH_FILTER_BTCT, SH_FILTER_COT, SH_MAU_TO_BTCT))


def sh_crop_theo_tuong(doc, view):
    """Crop view = khung bao tường trong view + SH_CROP_DU_MM × tỉ lệ (toạ độ theo hệ của CropBox), khung crop ẩn."""
    cb = view.CropBox
    tf = cb.Transform
    inv = tf.Inverse
    xs, ys = [], []
    for w in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
        bb = w.get_BoundingBox(None)
        if bb is None:
            continue
        for x in (bb.Min.X, bb.Max.X):
            for y in (bb.Min.Y, bb.Max.Y):
                q = inv.OfPoint(XYZ(x, y, 0))
                xs.append(q.X)
                ys.append(q.Y)
    if not xs:
        return u"Không có tường trong view – giữ crop của view gốc."
    du = sh_ft(SH_CROP_DU_MM * view.Scale)
    moi = BoundingBoxXYZ()
    moi.Transform = tf
    moi.Min = XYZ(min(xs) - du, min(ys) - du, cb.Min.Z)
    moi.Max = XYZ(max(xs) + du, max(ys) + du, cb.Max.Z)
    view.CropBox = moi
    view.CropBoxActive = True
    view.CropBoxVisible = False
    return u"Crop view mới = khung bao tường + %g mm giấy (%d x %d mm giấy)." % (
        SH_CROP_DU_MM, sh_mm(moi.Max.X - moi.Min.X) / view.Scale, sh_mm(moi.Max.Y - moi.Min.Y) / view.Scale)


def dat_mat_bang_len_sheet(doc, view, gd, hm, kho, khung, so_hieu, ten_sheet, so_mac_dinh, muc_chu_thich):
    """Tạo sheet + đặt mặt bằng giữa vùng vẽ + chú thích góc phải dưới. Trả về [báo cáo]."""
    bao = []
    try:
        dang = view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER)
        if dang is not None and dang.AsString() and dang.AsString() not in (u"---", u"-"):
            return [u"View '%s' đã nằm trên sheet %s – không đặt thêm." % (view.Name, dang.AsString())]
    except Exception:
        pass
    cap = sh_cap_thu_muc(doc)
    pid_gd, pid_hm = sh_gd_hm(doc, cap)
    so = (so_hieu or u"").strip() or sh_so_tiep(doc, pid_gd, gd, pid_hm, hm, so_mac_dinh)
    # Số hiệu trùng sheet TRỐNG có sẵn (vd. G19 dựng sẵn A.4-201 MẶT BẰNG CHỐNG THẤM) → đặt vào sheet đó, giữ nguyên
    # tên / khung tên / tham số người dùng đã đặt
    trong = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet)
             if s.SheetNumber == so and not s.IsPlaceholder and s.GetAllPlacedViews().Count == 0
             and not any(True for _ in FilteredElementCollector(doc, s.Id).OfClass(ScheduleSheetInstance)
                         if not _.IsTitleblockRevisionSchedule)]
    if trong:
        tbs = [t for t in FilteredElementCollector(doc, trong[0].Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsNotElementType()]
        if tbs:
            return sh_dat_vao(doc, view, trong[0], tbs[0], doc.GetElement(tbs[0].GetTypeId()), muc_chu_thich,
                              [u"Dùng sheet trống có sẵn %s – %s (giữ tên, khung tên, tham số)." % (
                                  so, trong[0].Name)], ten_sheet, cap, None)
    tb = sh_khung_ten(doc, kho, khung)
    if tb is None:
        return [u"Không có family khung tên khổ %s trong dự án (tên family / type có chữ '%s') – chưa đặt lên sheet. "
                u"Load khung tên rồi bấm lại." % (kho, kho)]
    dung = set(s.SheetNumber for s in FilteredElementCollector(doc).OfClass(ViewSheet))
    if so in dung:
        import re
        cu = so
        m = re.search(r"(\d+)$", so)
        dau, n, w = (so[:m.start()], int(m.group(1)), len(m.group(1))) if m else (so + u"-", 0, 1)
        while so in dung:
            n += 1
            so = u"%s%0*d" % (dau, w, n)
        bao.append(u"Số hiệu '%s' đã có – dùng '%s'." % (cu, so))
    TransactionManager.Instance.EnsureInTransaction(doc)
    sh = ViewSheet.Create(doc, tb.Id)
    sh.SheetNumber = so
    sh.Name = ten_sheet
    for pid, gt_, nhan in ((pid_gd, gd, u"giai đoạn"), (pid_hm, hm, u"hạng mục")):
        if pid is None or not gt_:
            continue
        prm = sh_ts(sh, pid)
        if prm is not None and not prm.IsReadOnly:
            prm.Set(gt_)
        else:
            bao.append(u"Không gán được %s '%s' (tham số không ghi được)." % (nhan, gt_))
    doc.Regenerate()
    tb_inst = [t for t in FilteredElementCollector(doc, sh.Id).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsNotElementType()][0]
    TransactionManager.Instance.TransactionTaskDone()
    return sh_dat_vao(doc, view, sh, tb_inst, tb, muc_chu_thich, bao, ten_sheet, cap, kho)


def sh_dat_vao(doc, view, sh, tb_inst, tb, muc_chu_thich, bao, ten_sheet, cap, kho):
    """Đặt chú thích (góc phải dưới vùng vẽ) + mặt bằng (giữa vùng vẽ, giữ tỉ lệ view) lên sheet sh. Trả về [báo cáo]."""
    net = sh_net_khung(doc, tb)          # mở family khung tên: phải ngoài transaction
    TransactionManager.Instance.EnsureInTransaction(doc)
    x0, y0, x1, y1 = sh_vung_ve(sh, tb_inst, net)
    b = sh_ft(SH_BIEN_MM)
    o_ct = None
    if muc_chu_thich:
        try:
            vct, msg = sh_chu_thich(doc, u"CHÚ THÍCH - %s" % ten_sheet, view.Scale, muc_chu_thich)
            bao.append(u"Chú thích: %s." % msg)
            if vct is not None:
                doc.Regenerate()
                vp_ct = Viewport.Create(doc, sh.Id, vct.Id, XYZ(x1, y0, 0))
                k_ = sh_kieu_viewport(doc, False)
                if k_ is not None:
                    vp_ct.ChangeTypeId(k_.Id)
                doc.Regenerate()
                o_ = vp_ct.GetBoxOutline()
                wc, hc = o_.MaximumPoint.X - o_.MinimumPoint.X, o_.MaximumPoint.Y - o_.MinimumPoint.Y
                vp_ct.SetBoxCenter(XYZ(x1 - b - wc / 2.0, y0 + b + hc / 2.0, 0))
                o_ct = (x1 - b - wc, y0 + b, x1 - b, y0 + b + hc)
        except Exception as ex:
            bao.append(u"Không vẽ được chú thích: %s" % (u"%s" % ex).splitlines()[0][:150])
    try:
        prm = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
        if prm is not None and not prm.IsReadOnly and not (prm.AsString() or u"").strip():
            prm.Set(ten_sheet)
    except Exception:
        pass
    vx0, vy0, vx1, vy1 = x0 + b, y0 + b + sh_ft(SH_TIEU_DE_MM), x1 - b, y1 - b
    bao.append(sh_thu_truc(doc, view))
    doc.Regenerate()
    vp = Viewport.Create(doc, sh.Id, view.Id, XYZ((vx0 + vx1) / 2.0, (vy0 + vy1) / 2.0, 0))
    k_ = sh_kieu_viewport(doc, True)
    if k_ is not None:
        vp.ChangeTypeId(k_.Id)
    doc.Regenerate()
    o = vp.GetBoxOutline()
    w, h = o.MaximumPoint.X - o.MinimumPoint.X, o.MaximumPoint.Y - o.MinimumPoint.Y
    cx = (vx0 + vx1) / 2.0 if w <= vx1 - vx0 else vx0 + w / 2.0
    cy = (vy0 + vy1) / 2.0 if h <= vy1 - vy0 else vy1 - h / 2.0
    vp.SetBoxCenter(XYZ(cx, cy, 0))
    TransactionManager.Instance.TransactionTaskDone()
    if w > vx1 - vx0 + 1e-6 or h > vy1 - vy0 + 1e-6:
        bao.append(u"CẦN XEM LẠI: mặt bằng 1:%d (kể cả trục, chú thích) %d x %d mm lớn hơn vùng vẽ %d x %d mm – chọn khổ "
                   u"lớn hơn hoặc thu crop view." % (view.Scale, sh_mm(w), sh_mm(h), sh_mm(vx1 - vx0), sh_mm(vy1 - vy0)))
    elif o_ct is not None and cx + w / 2.0 > o_ct[0] and cy - h / 2.0 < o_ct[3]:
        bao.append(u"CẦN XEM LẠI: khung mặt bằng có thể chạm chú thích góc phải dưới – dời tay nếu cần.")
    bao.append(u"ĐÃ ĐẶT lên sheet %s – %s (khung %s : %s%s), mặt bằng 1:%d giữa vùng vẽ, kiểu viewport '%s'." % (
        sh.SheetNumber, sh.Name, tb.FamilyName, sh_ten(tb), u", khổ %s" % kho if kho else u"", view.Scale,
        sh_ten(k_) if k_ is not None else u"mặc định"))
    if not cap:
        bao.append(u"Project Browser không nhóm sheet theo tham số – không gán giai đoạn / hạng mục.")
    return bao
# ==== HẾT PHẦN CHUNG ĐẶT SHEET ====
