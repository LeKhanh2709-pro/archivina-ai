# ==== PHẦN CHUNG VÁCH KÍNH (nguồn: VachKinh_chung.py, chép vào công cụ bằng gop_vach_kinh.py – không sửa tay trong công cụ) ====
# Dùng chung cho nút Thống kê cửa (cửa sổ "Vách kính") và nút Định vị + tag cửa. Cần sẵn trong công cụ: khối PHẦN CHUNG FILE
# LINK, doc_in, os, clr, _RevitDB, TransactionManager; biến VK_IN_THU_MUC = chỉ số IN[] "thư mục family tag vách kính".
#   - Tên vách kính = MARK của từng curtain wall (model HQV: T1-VK.02, DVKT1-01 …). Tag = family tag TƯỜNG hiện Mark
#     "ARV_Tag Vach Kinh Mark" (dựng từ family tag Mark lan can của người dùng, đổi hạng mục sang Wall Tags vì API không tạo
#     được nhãn); dự án chưa có thì nạp bản đóng gói lib\tag_vach_kinh.
#   - Mỗi vách 1 tag, không leader, nằm theo phương vách (vách dọc trên view → tag đứng), giữa vách, phía ngoài nhà, cách mép
#     vách VK_KHE_MM giấy; vướng tag / chữ / tường khác / cửa (kể cả cánh mở) thì dịch dọc vách, hết chỗ thì đẩy ra xa dần,
#     rồi mới sang phía trong; vẫn vướng thì để chỗ đầu và báo. Phía ngoài = phía có nhiều tia dò (0°, ±30°, xa VK_TIA_M)
#     không chạm tường; bằng nhau thì phía không có room; vẫn không rõ thì theo mặt ngoài của tường.
#   - Vách đã có tag tường trong view thì không tag thêm; vách chưa có Mark thì liệt kê, không tag.
#   - Người dùng chốt 2026-11-14: cửa đi / cửa sổ NẰM TRONG vách kính (host là curtain wall, kể cả tấm vách là family cửa)
#     KHÔNG tag cửa, KHÔNG thống kê – vách kính đã có tên riêng (Mark). vk_trong_vach nhận các cửa đó.
#   - Việc có xoá (tag cửa cũ trên cửa trong vách kính, chữ + nét của bảng vẽ lại) luôn hỏi Yes / No trước (vk_hoi).
VK_TAG = u"ARV_Tag Vach Kinh Mark"
VK_KHE_MM = 1.0           # khe giữa mép vách và khung tag (mm giấy)
VK_NUA_DAY_MM = 100.0     # nửa bề dày vách kính khi tường không có Width (đố 65 x ~190)
VK_SO_NAC = 6             # số nấc đẩy tag ra xa vách khi sát vách không còn chỗ (mỗi nấc = bề dày tag + 1 mm giấy)
VK_TIA_M = 25.0           # tia dò phía ngoài nhà: đi xa chừng này mà không chạm tường khác = phía ngoài


def vk_la_vach(e):
    try:
        return e.WallType.Kind == WallKind.Curtain
    except Exception:
        return False


def vk_trong_vach(e):
    """Cửa đi / cửa sổ nằm trong vách kính: host là curtain wall (kể cả tấm vách kính là family cửa đi / cửa sổ)."""
    try:
        h = e.Host
    except Exception:
        return False
    return h is not None and vk_la_vach(h)


def vk_hoi(bien_mt, tieu_de, chinh, noi_dung, mo_rong=u""):
    """Hỏi Yes / No trước khi xoá (quy tắc: có xoá thì liệt kê + chờ xác nhận). Biến môi trường <bien_mt> = 1 / 0 trả lời
    sẵn (chạy thử nền, không hiện hộp thoại)."""
    tl = os.environ.get(bien_mt, "")
    if tl in ("1", "0"):
        return tl == "1"
    clr.AddReference("RevitAPIUI")
    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
    td = TaskDialog(tieu_de)
    td.MainInstruction = chinh
    td.MainContent = noi_dung
    if mo_rong:
        td.ExpandedContent = mo_rong
    td.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
    td.DefaultButton = TaskDialogResult.Yes
    return td.Show() == TaskDialogResult.Yes


def vk_trong_view(doc, view):
    """Curtain wall thấy trong view: model chính + file link đúng tầng (LkPT)."""
    kq = [e for e in FilteredElementCollector(doc, view.Id).OfClass(Wall) if vk_la_vach(e)]
    lv = view.GenLevel
    for li, ld, tf in lk_cac_link(doc, view):
        ids = lk_level_khop(ld, tf, lv) if lv is not None else None
        if ids is not None and not ids:
            continue
        for e in FilteredElementCollector(doc, view.Id, li.Id).OfClass(Wall):
            if vk_la_vach(e) and (ids is None or e.LevelId.Value in ids):
                kq.append(LkPT(e, li, tf))
    return kq


def vk_mark(e):
    p = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
    return (p.AsString() or u"").strip() if p is not None else u""


def vk_dat_mark(doc, json_dat, dry, bao, xem_lai):
    """Đặt Mark cho vách kính theo JSON [{"ids": [...], "moi": "T1-VK.61"}]."""
    if not json_dat:
        return
    import json
    try:
        ds = json.loads(json_dat)
    except Exception as ex:
        bao.append(u"IN[9] không phải JSON hợp lệ: %s" % ex)
        return
    if not ds:
        return
    bao.append(u"")
    bao.append(u"== ĐẶT TÊN VÁCH KÍNH (Mark) – %d dòng%s" % (len(ds), u" (DRY-RUN)" if dry else u""))
    dang_doi = set(int(i) for d in ds for i in d.get("ids", []))
    khac = {}
    for e in FilteredElementCollector(doc).OfClass(Wall):
        if vk_la_vach(e) and e.Id.Value not in dang_doi and vk_mark(e):
            khac.setdefault(vk_mark(e), []).append(e.Id.Value)
    if not dry:
        TransactionManager.Instance.EnsureInTransaction(doc)
    for d in ds:
        moi = (u"%s" % d.get("moi", u"")).strip()
        if not moi:
            continue
        n = 0
        for i in d.get("ids", []):
            e = doc.GetElement(ElementId(int(i)))
            p = e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK) if e is not None else None
            if p is None or p.IsReadOnly:
                bao.append(u"   KHÔNG đặt được Mark cho vách id %s (không có / chỉ đọc)" % i)
                continue
            if not dry:
                p.Set(moi)
            n += 1
        bao.append(u"   %s → %s  (%d vách: %s)" % (d.get("cu") or u"(trống)", moi, n,
                                                    u", ".join(u"%s" % i for i in d.get("ids", [])[:8])))
        if moi in khac:
            xem_lai.append(u"Mark '%s' đã có ở vách kính khác (id %s) – 2 vách cùng tên." % (
                moi, u", ".join(u"%d" % i for i in khac[moi][:5])))
    if not dry:
        doc.Regenerate()


def vk_thu_muc_tag():
    i_ = globals().get("VK_IN_THU_MUC")
    d = (u"%s" % (doc_in(i_) or u"")).strip() if i_ is not None else u""
    if d:
        return d
    try:
        f = globals().get("__file__")
        if f:
            return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(f)), u"..", u"..", u"..", u"lib",
                                                 u"tag_vach_kinh"))
    except Exception:
        pass
    return u""


def vk_tuy_chon_nap():
    """IFamilyLoadOptions: family đã có thì giữ nguyên. Tên lớp .NET riêng mỗi lần gọi."""
    import uuid
    ns = "ARV.VachKinh.N" + uuid.uuid4().hex

    class _Nap(_RevitDB.IFamilyLoadOptions):
        __namespace__ = ns

        def OnFamilyFound(self, familyInUse, overwriteParameterValues):
            return (True, False)

        def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
            return (True, _RevitDB.FamilySource.Family, False)

    return _Nap()


def vk_ten_kieu(s):
    p = s.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return u"%s : %s" % (s.FamilyName, p.AsString() if p is not None else u"")


def vk_kieu_tag(doc, ten_kieu, dry, bao):
    """Kiểu tag tường để tag vách: theo tên "Family : Type" (IN[11]); trống → family VK_TAG, chưa có thì nạp bản đóng gói."""
    ds = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_WallTags))
    ten_kieu = (ten_kieu or u"").strip()
    if ten_kieu:
        for s in ds:
            if vk_ten_kieu(s) == ten_kieu or s.FamilyName == ten_kieu:
                return s
        bao.append(u"Không thấy kiểu tag '%s' trong dự án → dùng '%s'." % (ten_kieu, VK_TAG))
    for s in ds:
        if s.FamilyName == VK_TAG:
            return s
    duong = os.path.join(vk_thu_muc_tag(), VK_TAG + u".rfa")
    if not os.path.isfile(duong):
        bao.append(u"CHƯA CÓ family tag '%s' trong dự án và không thấy file đóng gói '%s' → không tag." % (VK_TAG, duong))
        return None
    if dry:
        bao.append(u"Sẽ nạp family tag '%s' từ %s." % (VK_TAG, duong))
        return None
    TransactionManager.Instance.EnsureInTransaction(doc)
    try:
        doc.LoadFamily(duong, vk_tuy_chon_nap())
    except Exception as ex:
        bao.append(u"KHÔNG nạp được family tag '%s' từ %s: %s" % (VK_TAG, duong, (u"%s" % ex).splitlines()[0][:200]))
        return None
    finally:
        TransactionManager.Instance.TransactionTaskDone()
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_WallTags):
        if s.FamilyName == VK_TAG:
            bao.append(u"Nạp family tag '%s' từ %s." % (VK_TAG, duong))
            return s
    bao.append(u"Nạp '%s' xong nhưng KHÔNG thấy kiểu tag." % duong)
    return None


def vk_tag(doc, view, ten_kieu, dry, bao, xem_lai):
    vs = vk_trong_view(doc, view)
    bao.append(u"")
    bao.append(u"== TAG VÁCH KÍNH BẰNG MARK%s: %d vách kính thấy trong mặt bằng" % (u" (DRY-RUN)" if dry else u"", len(vs)))
    if not vs:
        return
    da_tag = set()
    for tg in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag):
        if tg.Category is not None and tg.Category.Id.Value == int(BuiltInCategory.OST_WallTags):
            da_tag.update(lk_khoa_tag(tg))
    da = [e for e in vs if e.Id.Value in da_tag]
    con = [e for e in vs if e.Id.Value not in da_tag]
    thieu = [e for e in con if not vk_mark(e)]
    can = [e for e in con if vk_mark(e)]
    bao.append(u"   đã có tag: %d | sẽ tag: %d | chưa có Mark (không tag): %d" % (len(da), len(can), len(thieu)))
    if thieu:
        xem_lai.append(u"%d vách kính chưa có Mark nên chưa tag (id %s) – đặt Mark (nút Thống kê cửa → cửa sổ Vách kính) rồi bấm lại." % (
            len(thieu), u", ".join(u"%s" % e.Id.Value for e in thieu[:12])))
    dem = {}
    for e in vs:
        if vk_mark(e):
            dem.setdefault(vk_mark(e), []).append(e.Id.Value)
    for mk in sorted(dem):
        if len(dem[mk]) > 1:
            xem_lai.append(u"Mark '%s' đặt cho %d vách kính (id %s)." % (mk, len(dem[mk]), u", ".join(u"%s" % i for i in dem[mk][:6])))
    try:
        if view.GetCategoryHidden(ElementId(BuiltInCategory.OST_WallTags)):
            xem_lai.append(u"Hạng mục Wall Tags đang TẮT trong view / view template – tag vách kính tạo ra sẽ không hiện.")
    except Exception:
        pass
    if not can:
        return
    kieu = vk_kieu_tag(doc, ten_kieu, dry, bao)
    if kieu is None:
        return
    bao.append(u"   kiểu tag: %s" % vk_ten_kieu(kieu))
    if dry:
        return
    sc = float(view.Scale)
    ft = lambda v_mm: UnitUtils.ConvertToInternalUnits(v_mm, UnitTypeId.Millimeters)
    R, U = view.RightDirection, view.UpDirection
    uv = lambda p: (p.DotProduct(R), p.DotProduct(U))
    z_room = (view.GenLevel.Elevation if view.GenLevel is not None else 0.0) + ft(500)

    def co_phong(p):
        q = XYZ(p.X, p.Y, z_room)
        try:
            if doc.GetRoomAtPoint(q) is not None:
                return True
        except Exception:
            pass
        return lk_room_moi_link(doc, q, view.GenLevel) is not None

    # vật cản: tag + chữ đang có (khung bao trong view), tim mọi tường thấy trong view (kèm nửa bề dày)
    hop = []          # (u0, v0, u1, v1)
    for cls in (IndependentTag, TextNote):
        for x in FilteredElementCollector(doc, view.Id).OfClass(cls):
            bb = x.get_BoundingBox(view)
            if bb is not None:
                a, b = uv(bb.Min), uv(bb.Max)
                hop.append((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows):
        for x in FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType():
            bb = x.get_BoundingBox(view)
            if bb is not None:
                a, b = uv(bb.Min), uv(bb.Max)
                hop.append((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
        # cửa trong file link: không lấy được khung bao theo view (thiếu nét cánh mở) → khung bao khối, cửa đi nới thêm bán
        # kính cánh mở ước lượng theo phương vuông góc (rộng ≤ 1100: 1 cánh = bề rộng; rộng hơn: 2 cánh = nửa bề rộng)
        for x in lk_thay(doc, view, bic, True):
            try:
                bb = x.get_BoundingBox(None)
                if bb is None:
                    continue
                a, b = uv(bb.Min), uv(bb.Max)
                u0, v0, u1, v1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
                if bic == BuiltInCategory.OST_Doors:
                    dai = max(u1 - u0, v1 - v0)
                    r_ = dai if dai <= ft(1100) else dai / 2.0
                    if (u1 - u0) >= (v1 - v0):
                        v0, v1 = v0 - r_, v1 + r_
                    else:
                        u0, u1 = u0 - r_, u1 + r_
                hop.append((u0, v0, u1, v1))
            except Exception:
                pass
    doan = []         # (id, (u, v) đầu, (u, v) cuối, nửa dày)
    tuong = list(FilteredElementCollector(doc, view.Id).OfClass(Wall)) + lk_thay(doc, view, BuiltInCategory.OST_Walls, True)
    for x in tuong:
        try:
            c = x.Location.Curve
            nd = max(x.Width / 2.0, ft(VK_NUA_DAY_MM) if vk_la_vach(x) else 0.0)
            ds_p = [c.GetEndPoint(0), c.GetEndPoint(1)] if c.GetType().Name == "Line" else list(c.Tessellate())
            for i in range(len(ds_p) - 1):
                doan.append((x.Id.Value, uv(ds_p[i]), uv(ds_p[i + 1]), nd))
        except Exception:
            pass

    def cat_doan(h, a, b, nd):
        """Hình chữ nhật h (nới nd) có chạm đoạn a-b không (Liang–Barsky)."""
        x0, y0, x1, y1 = h[0] - nd, h[1] - nd, h[2] + nd, h[3] + nd
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1 = 0.0, 1.0
        for p_, q_ in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if abs(p_) < 1e-12:
                if q_ < 0:
                    return False
                continue
            r_ = q_ / p_
            if p_ < 0:
                t0 = max(t0, r_)
            else:
                t1 = min(t1, r_)
            if t0 > t1:
                return False
        return True

    def vuong(h, bo_id):
        for k in hop:
            if h[0] < k[2] and k[0] < h[2] and h[1] < k[3] and k[1] < h[3]:
                return True
        for i, a, b, nd in doan:
            if i != bo_id and cat_doan(h, a, b, nd):
                return True
        return False

    def tia_thoat(g, hu, hv, bo_id):
        """Số tia (0°, ±30°) từ điểm g theo hướng (hu, hv) đi VK_TIA_M mét mà không chạm tường nào khác."""
        import math
        xa_ = ft(VK_TIA_M * 1000.0)
        so_ = 0
        for goc_ in (0.0, math.radians(30), -math.radians(30)):
            cu_, su_ = math.cos(goc_), math.sin(goc_)
            du_, dv_ = hu * cu_ - hv * su_, hu * su_ + hv * cu_
            cham = False
            for i, a, b, nd in doan:
                if i == bo_id:
                    continue
                ex, ey = b[0] - a[0], b[1] - a[1]
                mau = du_ * ey - dv_ * ex
                if abs(mau) < 1e-12:
                    continue
                t_ = ((a[0] - g[0]) * ey - (a[1] - g[1]) * ex) / mau
                s_ = ((a[0] - g[0]) * dv_ - (a[1] - g[1]) * du_) / mau
                if 1e-6 < t_ < xa_ and -1e-9 <= s_ <= 1 + 1e-9:
                    cham = True
                    break
            if not cham:
                so_ += 1
        return so_

    TransactionManager.Instance.EnsureInTransaction(doc)
    if not kieu.IsActive:
        kieu.Activate()
    viec = []
    for e in can:
        try:
            c = e.Location.Curve
            giua = c.Evaluate(0.5, True)
            d = c.ComputeDerivatives(0.5, True).BasisX.Normalize()
            du, dv = uv(d)
            huong = TagOrientation.Vertical if abs(dv) > abs(du) else TagOrientation.Horizontal
            tg = IndependentTag.Create(doc, kieu.Id, view.Id, lk_tham_chieu(e), False, huong, giua)
            viec.append((e, c, d, tg, giua))
        except Exception as ex:
            xem_lai.append(u"Vách id %s (Mark %s): không tag được – %s" % (e.Id.Value, vk_mark(e), (u"%s" % ex).splitlines()[0][:120]))
    doc.Regenerate()
    so, vuong_ds = 0, []
    for e, c, d, tg, giua in viec:
        bb = tg.get_BoundingBox(view)
        if bb is None:
            xem_lai.append(u"Vách id %s: tag không hiện trong view (hạng mục / template ẩn?)." % e.Id.Value)
            so += 1
            continue
        a, b = uv(bb.Min), uv(bb.Max)
        nu, nv = abs(b[0] - a[0]) / 2.0, abs(b[1] - a[1]) / 2.0            # nửa rộng / nửa cao khung tag trên view
        tam0 = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        dau0 = uv(tg.TagHeadPosition)
        lech = (tam0[0] - dau0[0], tam0[1] - dau0[1])                     # tâm khung so với điểm đặt
        n = XYZ(-d.Y, d.X, 0.0)
        nu_, nv_ = uv(n)
        nua_tag = abs(nu_) * nu + abs(nv_) * nv                           # nửa khung tag theo phương vuông góc vách
        nd = max(e.Width / 2.0, ft(VK_NUA_DAY_MM))
        xa = nd + ft(VK_KHE_MM) * sc + nua_tag
        # phía ngoài nhà: phía có nhiều tia đi xa mà không chạm tường khác; bằng nhau thì phía không có room; vẫn không rõ
        # thì theo mặt ngoài của tường
        gu, gv = uv(giua)
        le_ = nd + ft(50)
        ta = tia_thoat((gu + nu_ * le_, gv + nv_ * le_), nu_, nv_, e.Id.Value)
        tb = tia_thoat((gu - nu_ * le_, gv - nv_ * le_), -nu_, -nv_, e.Id.Value)
        if ta != tb:
            ngoai = 1.0 if ta > tb else -1.0
        else:
            pa, pb = co_phong(giua + n * ft(700)), co_phong(giua - n * ft(700))
            if pa != pb:
                ngoai = -1.0 if pa else 1.0
            else:
                try:
                    ngoai = 1.0 if e.Orientation.DotProduct(n) >= 0 else -1.0
                except Exception:
                    ngoai = 1.0
        chon = None
        ung = []
        for t_ in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.12, 0.88):
            for phia in (ngoai, -ngoai):
                ung.append((t_, phia))
        ung.sort(key=lambda k: (k[1] != ngoai, abs(k[0] - 0.5)))       # phía ngoài trước, gần giữa vách trước
        ung = [(t_, phia, xa) for t_, phia in ung]
        # vách ngắn bị cửa chiếm hết chiều dài: đẩy tag ra xa dần (vượt cung mở cửa), giữa vách, phía ngoài rồi phía trong
        buoc = 2.0 * nua_tag + ft(1.0) * sc
        for phia in (ngoai, -ngoai):
            for k_ in range(1, VK_SO_NAC + 1):
                ung.append((0.5, phia, xa + k_ * buoc))
        for t_, phia, xa_ in ung:
            p = c.Evaluate(t_, True) + n * (phia * xa_)
            pu, pv = uv(p)
            h = (pu - nu, pv - nv, pu + nu, pv + nv)
            if not vuong(h, e.Id.Value):
                chon = (p, h)
                break
        if chon is None:
            p = giua + n * (ngoai * xa)
            pu, pv = uv(p)
            chon = (p, (pu - nu, pv - nv, pu + nu, pv + nv))
            vuong_ds.append(u"%s (id %s)" % (vk_mark(e), e.Id.Value))
        p, h = chon
        # điểm đặt = tâm mong muốn - độ lệch tâm khung
        dich = XYZ(p.X, p.Y, tg.TagHeadPosition.Z) - R * lech[0] - U * lech[1]
        tg.TagHeadPosition = XYZ(dich.X, dich.Y, tg.TagHeadPosition.Z)
        hop.append(h)
        so += 1
    doc.Regenerate()
    TransactionManager.Instance.TransactionTaskDone()
    bao.append(u"   đã tag %d vách kính." % so)
    if vuong_ds:
        xem_lai.append(u"%d tag vách kính không tìm được chỗ trống (đang đè tường / tag / chữ khác), cần dời tay: %s" % (
            len(vuong_ds), u", ".join(vuong_ds[:15])))


def vk_ve_bang(doc, v, tieu_de, cot, rong_cot, dong):
    """Vẽ nội dung bảng vào drafting view v (cùng cách trình bày với lk_bang_ve)."""
    cao_dong, cao_dau = _lk_mm(8), _lk_mm(10)
    kieu = sorted(FilteredElementCollector(doc).OfClass(TextNoteType), key=lambda t: t.Id.Value)

    def diem_kieu(t):
        ten_k = (t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() or u"").lower()
        co = t.get_Parameter(BuiltInParameter.TEXT_SIZE).AsDouble()
        return (0 if u"arial" in ten_k else 1, abs(co - _lk_mm(2.5)))
    kt = min(kieu, key=diem_kieu)
    tong = sum(_lk_mm(x) for x in rong_cot)
    tao_chu = lambda x_, y_, s_: TextNote.Create(doc, v.Id, XYZ(x_, y_, 0), s_, kt.Id)
    tao_net = lambda a_, b_: doc.Create.NewDetailCurve(v, Line.CreateBound(a_, b_))
    tao_chu(_lk_mm(2), cao_dau * 1.5, tieu_de)
    xs = [0.0]
    for r_ in rong_cot:
        xs.append(xs[-1] + _lk_mm(r_))
    y_day = -cao_dong * len(dong)
    for i_ in range(len(dong) + 2):
        y_ = cao_dau if i_ == 0 else -cao_dong * (i_ - 1)
        tao_net(XYZ(0, y_, 0), XYZ(tong, y_, 0))
    for x_ in xs:
        tao_net(XYZ(x_, cao_dau, 0), XYZ(x_, y_day, 0))
    for c_ in range(len(cot)):
        tao_chu(xs[c_] + _lk_mm(2), cao_dau - _lk_mm(3), cot[c_])
    for r_i, d in enumerate(dong):
        for c_ in range(len(cot)):
            if d[c_] != u"":
                tao_chu(xs[c_] + _lk_mm(2), -cao_dong * r_i - _lk_mm(2), d[c_])


def vk_bang_ve(doc, ten_view, tieu_de, cot, rong_cot, dong):
    """Như lk_bang_ve; riêng bảng đã có mà số ô đã đổi (vd. bỏ cửa nằm trong vách kính) thì HỎI rồi vẽ lại ngay trong view
    đó: xoá chữ + nét cũ của bảng, vẽ theo số liệu mới, giữ nguyên góc phải dưới của bảng trên bản vẽ. Gọi TRONG
    transaction. Biến môi trường ARV_VE_LAI_BANG = 1 / 0 trả lời sẵn. Trả về (view, cách làm)."""
    v, cach = lk_bang_ve(doc, ten_view, tieu_de, cot, rong_cot, dong)
    if u"CHƯA cập nhật" not in cach:
        return v, cach
    chu = list(FilteredElementCollector(doc, v.Id).OfClass(TextNote))
    net = list(FilteredElementCollector(doc, v.Id).OfClass(CurveElement))
    if not vk_hoi("ARV_VE_LAI_BANG", u"Vẽ lại bảng thống kê", u"Bảng '%s' đã có nhưng số dòng đã đổi." % ten_view,
                  u"Vẽ lại bảng ngay trong view đó?\n\nYes: XOÁ %d chữ + %d nét cũ của bảng rồi vẽ lại theo số liệu mới "
                  u"(view và chỗ đặt trên bản vẽ giữ nguyên, góc phải dưới không đổi). Ctrl+Z để hoàn tác.\n"
                  u"No: giữ nguyên bảng cũ." % (len(chu), len(net)),
                  u"Id chữ: %s\nId nét: %s" % (u", ".join(u"%d" % x.Id.Value for x in chu[:200]),
                                               u", ".join(u"%d" % x.Id.Value for x in net[:200]))):
        return v, cach
    vps = [(vp, vp.GetBoxOutline()) for vp in FilteredElementCollector(doc).OfClass(Viewport)
           if vp.ViewId.Value == v.Id.Value]
    from System.Collections.Generic import List
    ids = List[ElementId]()
    for x in chu + net:
        ids.Add(x.Id)
    doc.Delete(ids)
    vk_ve_bang(doc, v, tieu_de, cot, rong_cot, dong)
    doc.Regenerate()
    for vp, o in vps:           # giữ góc phải dưới của bảng trên bản vẽ
        try:
            n = vp.GetBoxOutline()
            c = vp.GetBoxCenter()
            vp.SetBoxCenter(XYZ(c.X + (o.MaximumPoint.X - n.MaximumPoint.X), c.Y + (o.MinimumPoint.Y - n.MinimumPoint.Y), c.Z))
        except Exception:
            pass
    return v, u"vẽ lại bảng đã có (xoá %d chữ + %d nét cũ, vẽ theo số liệu mới)" % (len(chu), len(net))
# ==== HẾT PHẦN CHUNG VÁCH KÍNH ====
