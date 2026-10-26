# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoOngThoatNuocWC_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Dựng ống thoát nước WC (uPVC) theo TUYẾN ĐÃ DUYỆT nhập dạng toạ độ – không đọc CAD:
#   - Ống đứng (IN[1]): xí / rửa / thông hơi trong HKT, từ level + IN[2] (dưới) tới level + IN[2] (trên),
#     cắt tại chỗ nhánh vào, đặt tê u.PVC_BEND TEE 90 (rule Junctions của pipe type).
#   - Tuyến nhánh (IN[0]): polyline mặt bằng x,y (mm, toạ độ Revit của mô hình đang mở), điểm cuối là tâm một ống
#     đứng hoặc một đỉnh của tuyến khác (→ Y 45°, tuyến kia phải đi thẳng qua đỉnh đó).
#     Đầu tuyến: '@' = ống xuống từ connector Sanitary của thiết bị (kể cả trong file link) gần điểm đầu ≤ 150 mm;
#     số = cao độ (mm so với level) đỉnh ống xuống tại điểm đầu; 'PHEU=-15' = đặt phễu thu IN[8] tại điểm đầu,
#     chân ở cao độ −15, ống nối vào connector phễu; 'PHEUD=-15' = phễu ĐẤU TỪ TRÊN XUỐNG: tuyến 2 điểm
#     "phễu;điểm Y", phễu nằm ngay trên ống chính, thượng lưu điểm Y ≥ 137 mm – ống xuống → co 45° → nhánh nghiêng
#     45° theo phương đứng vào Y (cho phễu đặt sát góc tường, KTS 2026-10-21); 'TT' = thông tắc: nút bịt (Caps của pipe type) ở điểm đầu;
#     trống = không có ống xuống.
#   - Cao độ: dốc IN[4] % về ống đứng; điểm cao nhất của mỗi cây nhánh có tâm ống = level − IN[3].
#   - Co 45° / 90° bằng NewElbowFitting (rule Elbows); Y / tê đặt thủ công, mỗi phụ kiện một SubTransaction.
#   Không nối được với thiết bị trong file link (Revit không cho) → đầu ống đặt trùng connector thiết bị.
#
#   IN[0] (str)   Tuyến nhánh, mỗi dòng: "Tên|System|DN|Đầu|x,y;x,y;…[|Vào=z]" – DN theo từng đoạn: "60/75" (thiếu = lặp
#                 số cuối); 'Vào=-700' = tuyến vào ống đứng bằng tê riêng ở cao độ −700 (không theo cao độ chung)
#   IN[1] (str)   Ống đứng, mỗi dòng: "Tên|System|DN|x,y"
#   IN[2] (str)   Đoạn ống đứng so với level: "-3300>3300" (dưới>trên, mm)
#   IN[3] (float) Level → tâm ống tại điểm cao nhất của nhánh (mm), mặc định 400
#   IN[4] (float) Độ dốc nhánh (%), mặc định 2
#   IN[5] (str)   Pipe type (phải có sẵn), mặc định "AV_u.PVC PN6"
#   IN[6] (str)   Level (trống = level của view đang mở)
#   IN[7] (str)   Màu trong view đang mở theo chuỗi con tên system: "Thông hơi=128,0,128;Xí=255,255,0;Rửa=0,0,255"
#   IN[8] (str)   Phễu thu "Family : Type" – chưa có trong mô hình thì chép từ file link
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo (mặc định True)
#   IN[11] (float) Cao độ tâm ống thông hơi ngang (mm so với level), mặc định −220 – đầu tuyến 'THX' = thông hơi
#                 từ ống xuống bệt (tê cắt vào ống xuống), 'THR' = thông hơi từ đầu ống rửa (tê + ống đứng lên, thông tắc
#                 lùi ra sau tê); thông hơi gấp 90° được, nhập nhau bằng tê, 1 tê vào ống đứng TH (mẫu HN Garden City).
#                 Trường 'TT=x,y' của tuyến = thông tắc ở chỗ gấp x,y: Y + ống chạy thẳng tới nút bịt, nhánh rẽ vào trục.
#   IN[10] (bool) Thay lần chạy trước: True = xoá ống / phễu có Comments ARV-THOATWC + phụ kiện nối vào chúng rồi
#                 dựng lại (cùng một Undo); False = gặp lần chạy trước thì dừng
# Đầu ra: OUT = danh sách dòng báo cáo.
# Tác giả: Claude (cho dungbn@archivina.com) – 2026-10-21 – Revit 2026, Dynamo CPython3.

import math
import collections

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, Line, Transaction, SubTransaction, BuiltInParameter,
                                   Level, FamilySymbol, FamilyInstance, ElementTransformUtils, Color,
                                   OverrideGraphicSettings, FillPatternElement, RoutingPreferenceRuleGroupType,
                                   RevitLinkInstance, Transform, CopyPasteOptions, ElementId, Domain,
                                   IFailuresPreprocessor, FailureProcessingResult, FailureSeverity, TransactionStatus,
                                   BuiltInCategory)
    from Autodesk.Revit.DB.Plumbing import Pipe, PipeType, PipingSystemType, PipeSystemType, PlumbingUtils
    from Autodesk.Revit.DB.Structure import StructuralType
    from System.Collections.Generic import List

    import uuid
    # Dynamo giữ phiên Python giữa các lần Run → tên kiểu .NET phải khác nhau mỗi lần
    _NS = "ARV_TaoOngThoatNuocWC_" + uuid.uuid4().hex

    class CommitFailures(IFailuresPreprocessor):
        """Lỗi lúc commit → cách xử lý mặc định của Revit; cảnh báo thì xoá và trả Continue
        (trả ProceedWithCommit sau khi chỉ xoá cảnh báo sẽ lặp rồi Revit hủy transaction)."""
        __namespace__ = _NS

        def __init__(self):
            self.resolved = collections.Counter()
            self.all = collections.Counter()
            self.warnings = collections.Counter()
            self.calls = 0

        def PreprocessFailures(self, fa):
            self.calls += 1
            resolved_any = False
            for f in list(fa.GetFailureMessages()):
                text = f.GetDescriptionText()
                if f.GetSeverity() == FailureSeverity.Warning:
                    self.warnings[text[:100]] += 1
                    fa.DeleteWarning(f)
                    continue
                self.all[(str(f.GetSeverity()), text[:120])] += 1
                if f.HasResolutions():
                    self.resolved[text[:80]] += 1
                    fa.ResolveFailure(f)
                    resolved_any = True
            if resolved_any and self.calls < 20:
                return FailureProcessingResult.ProceedWithCommit
            return FailureProcessingResult.Continue

    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo ống thoát nước WC"
COMMENT = u"ARV-THOATWC"
SNAP_MM = 5.0          # điểm cuối tuyến trùng tâm ống đứng / đỉnh tuyến khác
FIX_SNAP_MM = 150.0    # điểm đầu '@' tìm connector thiết bị
MIN_LEN_MM = 20.0      # ống còn lại sau khi đặt phụ kiện
DRAINV_MIN_H = 137.0   # PHEUD: phễu cách điểm Y (mặt bằng) – nhánh Y 60 dài 136 + co 45° 38 + ống 20, nghiêng 45°
DRAINV_MAX_TOP = -215.0  # PHEUD: co 45° dưới phễu phải thấp hơn thân phễu (đáy −165) + bán kính co
TT_END_STUB = 200.0    # thông tắc cuối: ống chính chạy thẳng quá chỗ gấp tới nút bịt (Y 75 nhánh thẳng 169 + 20 + dư;
                       # 220 thì nút bịt WC mẫu chạm ống phễu tắm y 300 – MCP 2026-10-22)
TT_END_MIN_OUT = 302.0  # thông tắc cuối: đoạn sau chỗ gấp ≥ nhánh Y 75 (161) + tê ống đứng (121) + 20
THR_STUB = 150.0       # THR: đoạn thông tắc lùi sau tê đầu ống rửa (tê 60 nhánh thẳng 66/92 + 20)
VENT_MIN_RISE_X = 150.0  # THX: tê 110/60 trên ống xuống bệt cách nhánh xí (chân 117 + co)
VENT_MIN_RISE_R = 165.0  # THR: ống đứng thông hơi từ đầu ống rửa (tê 60 nhánh 94 + co 90° D60 + 20)

# Mặc định = WC mẫu G19 (CH, bệt tại x 15364, y 1459 – KTS duyệt tuyến 2026-10-21). Mỗi ống đứng chỉ 1 tê (KTS: vị trí
# đấu nối chỉ dùng 1 Y); KTS bỏ phương án đổi trục xí ↔ rửa, giữ trục cũ.
# WC mẫu (sàn 1043712) – các quy tắc KTS chốt:
#   Xí: đấu thẳng vào trục đứng gần nhất, hạ cao độ (Vào=-560) chui dưới co ống thoát sàn cạnh xí (tâm cách 52).
#   Phễu thu tắm: ở góc khu tắm (thoát nhanh), ống đi vòng ra khu tắm (KTS phác), Y vào rửa chính; đoạn chéo cuối
#     ≥ 212 vì nhánh Y 60 chiếm 136.
#   Rửa chính: bắt đầu bằng thông tắc (nút bịt); Y lavabo / thoát sàn cạnh xí / phễu tắm; sau Y phễu tắm lên D75;
#     1 tê vào ống đứng rửa.
#   Lavabo: ống xuống trong tường (tim tường 100). Thoát sàn cạnh xí: vào hệ rửa, vòng lên bắc qua sau đầu ống xí.
# Nhóm A = WC lật đối xứng của WC mẫu (HKT 150×800 cạnh khu tắm): 1043721 (lật x), 1044664 (lật y), CH04 (chưa có sàn,
#   lật x + y) – tuyến lật theo mẫu, đầu ống xí = connector bệt thật, ống xuống lavabo theo y connector lavabo thật
#   (sinh bằng scratchpad gen_wc.py 2026-10-21).
# Nhóm B / C / D – Claude phác theo quy tắc WC mẫu, KTS duyệt 2026-10-21 (sinh bằng 03_DU-AN\G19\thoat-nuoc-WC\
#   gen_nhom-BCD.py, lật trong nhóm):
#   Phễu thoát sàn LUÔN ở góc tường, cách mặt tường ~100 (KTS sửa 2026-10-21) → khi góc sát ống đứng không đủ chỗ Y
#   ngang thì đấu từ trên xuống (PHEUD): ống chính đi ngay dưới phễu.
#   B (HKT sau két bệt): 1043703, 1043730, 1044655, 1044673 – ống chính bắt đầu từ phễu tắm góc ĐN khu tắm, đi bắc,
#     ngay dưới thoát sàn cạnh xí (góc tường két / vách kính, PHEUD), vào ống đứng rửa ở ĐẦU BẮC HKT; ống đứng xí đầu
#     nam, xí hạ vào tê −600 chui dưới ống rửa.
#   C (HKT 800×300 ngang): 1044323, 1044314 – ống đứng xí / thông hơi / rửa theo phương x; phễu tắm góc vách kính /
#     tường HKT; xí hạ vào tê −560.
#   D (HKT 200×900): 1044346 – ống đứng xí phía bắc, rửa xuống y 16015; rửa chính dọc x 26900 rồi chạy dọc y 16015
#     ngay dưới phễu tắm góc TN khu tắm (PHEUD); xí hạ vào tê −560.
# WC không có HKT trong WC (20 WC): KTS hướng dẫn sau.
DEF_ROUTES = u"\n".join([
    u"WC-1043712 Xí|AV_P_Nước Thải Xí|110|@|15364,1459;15150,850|Vào=-560",
    u"WC-1043712 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|15450,300;16000,300;16100,400;16100,850;16000,950;15750,950;15600,800",
    u"WC-1043712 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|15600,2100;15600,1750;15600,1500;15600,800;15600,600;15350,350;15150,350|TT=15600,600",
    u"WC-1043712 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|15364,1459;15364,1100;15364,600;15150,600",
    u"WC-1043712 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|15600,2100;15600,1100;15364,1100",
    u"WC-1043712 Lavabo|AV_P_Nước Thải Rửa|60|465|15025,2325;15600,1750",
    u"WC-1043712 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|15200,1150;15200,1550;15300,1650;15450,1650;15600,1500",
    u"WC-1043721 Xí|AV_P_Nước Thải Xí|110|@|49286,1439;49500,850|Vào=-560",
    u"WC-1043721 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|49200,300;48650,300;48550,400;48550,850;48650,950;48900,950;49050,800",
    u"WC-1043721 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|49050,2100;49050,1750;49050,1500;49050,800;49050,600;49300,350;49500,350|TT=49050,600",
    u"WC-1043721 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|49286,1439;49286,1100;49286,600;49500,600",
    u"WC-1043721 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|49050,2100;49050,1100;49286,1100",
    u"WC-1043721 Lavabo|AV_P_Nước Thải Rửa|60|465|49625,2325;49050,1750",
    u"WC-1043721 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|49450,1150;49450,1550;49350,1650;49200,1650;49050,1500",
    u"WC-1044664 Xí|AV_P_Nước Thải Xí|110|@|15364,30111;15150,30700|Vào=-560",
    u"WC-1044664 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|15450,31250;16000,31250;16100,31150;16100,30700;16000,30600;15750,30600;15600,30750",
    u"WC-1044664 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|15600,29450;15600,29800;15600,30050;15600,30750;15600,30950;15350,31200;15150,31200|TT=15600,30950",
    u"WC-1044664 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|15364,30111;15364,30450;15364,30950;15150,30950",
    u"WC-1044664 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|15600,29450;15600,30450;15364,30450",
    u"WC-1044664 Lavabo|AV_P_Nước Thải Rửa|60|465|15025,29225;15600,29800",
    u"WC-1044664 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|15200,30400;15200,30000;15300,29900;15450,29900;15600,30050",
    u"WC-CH04 Xí|AV_P_Nước Thải Xí|110|@|49296,30091;49500,30700|Vào=-560",
    u"WC-CH04 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|49200,31250;48650,31250;48550,31150;48550,30700;48650,30600;48900,30600;49050,30750",
    u"WC-CH04 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|49050,29450;49050,29800;49050,30050;49050,30750;49050,30950;49300,31200;49500,31200|TT=49050,30950",
    u"WC-CH04 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|49296,30091;49296,30450;49296,30950;49500,30950",
    u"WC-CH04 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|49050,29450;49050,30450;49296,30450",
    u"WC-CH04 Lavabo|AV_P_Nước Thải Rửa|60|465|49625,29215;49050,29800",
    u"WC-CH04 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|49450,30400;49450,30000;49350,29900;49200,29900;49050,30050",
    u"WC-1043703 Xí|AV_P_Nước Thải Xí|110|@|6536,1540;7000,1350|Vào=-600",
    u"WC-1043703 Phễu thu tắm|AV_P_Nước Thải Rửa|60/75/75/75/75/75|PHEU=-15|6960,265;6960,650;6960,800;6700,1060;6700,1335;6700,1550;7000,1850|TT=6700,1550",
    u"WC-1043703 Rửa chính|AV_P_Nước Thải Rửa|60|TT|5400,450;5925,450;6760,450;6960,650",
    u"WC-1043703 Lavabo|AV_P_Nước Thải Rửa|60|465|5550,75;5925,450",
    u"WC-1043703 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEUD=-15|6700,1185;6700,1335",
    u"WC-1043703 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|6536,1540;6800,1540;7000,1540",
    u"WC-1043703 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|5400,450;5400,1300;6800,1300;6800,1540",
    u"WC-1043730 Xí|AV_P_Nước Thải Xí|110|@|58114,1560;57650,1350|Vào=-600",
    u"WC-1043730 Phễu thu tắm|AV_P_Nước Thải Rửa|60/75/75/75/75/75|PHEU=-15|57690,265;57690,650;57690,800;57950,1060;57950,1335;57950,1550;57650,1850|TT=57950,1550",
    u"WC-1043730 Rửa chính|AV_P_Nước Thải Rửa|60|TT|59250,450;58725,450;57890,450;57690,650",
    u"WC-1043730 Lavabo|AV_P_Nước Thải Rửa|60|465|59100,75;58725,450",
    u"WC-1043730 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEUD=-15|57950,1185;57950,1335",
    u"WC-1043730 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|58114,1560;57850,1560;57650,1560",
    u"WC-1043730 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|59250,450;59250,1300;57850,1300;57850,1560",
    u"WC-1044655 Xí|AV_P_Nước Thải Xí|110|@|6536,29990;7000,30200|Vào=-600",
    u"WC-1044655 Phễu thu tắm|AV_P_Nước Thải Rửa|60/75/75/75/75/75|PHEU=-15|6960,31285;6960,30900;6960,30750;6700,30490;6700,30215;6700,30000;7000,29700|TT=6700,30000",
    u"WC-1044655 Rửa chính|AV_P_Nước Thải Rửa|60|TT|5400,31100;5925,31100;6760,31100;6960,30900",
    u"WC-1044655 Lavabo|AV_P_Nước Thải Rửa|60|465|5550,31475;5925,31100",
    u"WC-1044655 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEUD=-15|6700,30365;6700,30215",
    u"WC-1044655 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|6536,29990;6800,29990;7000,29990",
    u"WC-1044655 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|5400,31100;5400,30250;6800,30250;6800,29990",
    u"WC-1044673 Xí|AV_P_Nước Thải Xí|110|@|58114,30010;57650,30200|Vào=-600",
    u"WC-1044673 Phễu thu tắm|AV_P_Nước Thải Rửa|60/75/75/75/75/75|PHEU=-15|57690,31285;57690,30900;57690,30750;57950,30490;57950,30215;57950,30000;57650,29700|TT=57950,30000",
    u"WC-1044673 Rửa chính|AV_P_Nước Thải Rửa|60|TT|59250,31100;58725,31100;57890,31100;57690,30900",
    u"WC-1044673 Lavabo|AV_P_Nước Thải Rửa|60|465|59100,31475;58725,31100",
    u"WC-1044673 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEUD=-15|57950,30365;57950,30215",
    u"WC-1044673 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|58114,30010;57850,30010;57650,30010",
    u"WC-1044673 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|59250,31100;59250,30250;57850,30250;57850,30010",
    u"WC-1044323 Xí|AV_P_Nước Thải Xí|110|@|30858,13711;31600,13850|Vào=-560",
    u"WC-1044323 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|30400,13300;30715,13300;31430,13300;31665,13300;31850,13300;32100,13550;32100,13850|TT=31850,13300",
    u"WC-1044323 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|30400,13300;30858,13300;31850,13300;31850,13850",
    u"WC-1044323 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|30858,13711;30858,13300",
    u"WC-1044323 Lavabo|AV_P_Nước Thải Rửa|60|465|29940,14075;30715,13300",
    u"WC-1044323 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|31250,13850;31250,13480;31430,13300",
    u"WC-1044323 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|31480,13485;31665,13300",
    u"WC-1044314 Xí|AV_P_Nước Thải Xí|110|@|33811,13711;33050,13850|Vào=-560",
    u"WC-1044314 Rửa chính|AV_P_Nước Thải Rửa|60/60/60/75/75/75|TT|34250,13300;33935,13300;33220,13300;32985,13300;32800,13300;32550,13550;32550,13850|TT=32800,13300",
    u"WC-1044314 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|34250,13300;33811,13300;32800,13300;32800,13850",
    u"WC-1044314 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|33811,13711;33811,13300",
    u"WC-1044314 Lavabo|AV_P_Nước Thải Rửa|60|465|34710,14075;33935,13300",
    u"WC-1044314 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|33400,13850;33400,13480;33220,13300",
    u"WC-1044314 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEU=-15|33170,13485;32985,13300",
    u"WC-1044346 Xí|AV_P_Nước Thải Xí|110|@|26514,17269;26325,16600|Vào=-560",
    u"WC-1044346 Rửa chính|AV_P_Nước Thải Rửa|60/60/75/75/75/75|TT|26980,18000;26980,17370;26980,16800;26980,16115;26880,16015;26530,16015;26325,16015|TT=26880,16015",
    u"WC-1044346 Lavabo|AV_P_Nước Thải Rửa|60|465|26150,18200;26980,17370",
    u"WC-1044346 Thoát sàn cạnh xí|AV_P_Nước Thải Rửa|60|PHEU=-15|26340,17000;26780,17000;26980,16800",
    u"WC-1044346 Phễu thu tắm|AV_P_Nước Thải Rửa|60|PHEUD=-15|26680,16015;26530,16015",
    u"WC-1044346 Thông hơi xí|AV_P_Thông hơi Xí|60|THX|26514,17269;26514,17000;26514,16300;26325,16300",
    u"WC-1044346 Thông hơi rửa|AV_P_Thông hơi Xí|60|THR|26980,18000;26980,17000;26514,17000",
])
# Thông hơi ở giữa xí và rửa (KTS sửa 2026-10-21), cách đều 250 trong HKT lòng 150×800
DEF_STACKS = u"\n".join([
    u"WC-1043712 Ống đứng xí|AV_P_Nước Thải Xí|110|15150,850",
    u"WC-1043712 Thông hơi|AV_P_Thông hơi Xí|75|15150,600",
    u"WC-1043712 Ống đứng rửa|AV_P_Nước Thải Rửa|90|15150,350",
    u"WC-1043721 Ống đứng xí|AV_P_Nước Thải Xí|110|49500,850",
    u"WC-1043721 Thông hơi|AV_P_Thông hơi Xí|75|49500,600",
    u"WC-1043721 Ống đứng rửa|AV_P_Nước Thải Rửa|90|49500,350",
    u"WC-1044664 Ống đứng xí|AV_P_Nước Thải Xí|110|15150,30700",
    u"WC-1044664 Thông hơi|AV_P_Thông hơi Xí|75|15150,30950",
    u"WC-1044664 Ống đứng rửa|AV_P_Nước Thải Rửa|90|15150,31200",
    u"WC-CH04 Ống đứng xí|AV_P_Nước Thải Xí|110|49500,30700",
    u"WC-CH04 Thông hơi|AV_P_Thông hơi Xí|75|49500,30950",
    u"WC-CH04 Ống đứng rửa|AV_P_Nước Thải Rửa|90|49500,31200",
    u"WC-1043703 Ống đứng rửa|AV_P_Nước Thải Rửa|90|7000,1850",
    u"WC-1043703 Thông hơi|AV_P_Thông hơi Xí|75|7000,1540",
    u"WC-1043703 Ống đứng xí|AV_P_Nước Thải Xí|110|7000,1350",
    u"WC-1043730 Ống đứng rửa|AV_P_Nước Thải Rửa|90|57650,1850",
    u"WC-1043730 Thông hơi|AV_P_Thông hơi Xí|75|57650,1560",
    u"WC-1043730 Ống đứng xí|AV_P_Nước Thải Xí|110|57650,1350",
    u"WC-1044655 Ống đứng rửa|AV_P_Nước Thải Rửa|90|7000,29700",
    u"WC-1044655 Thông hơi|AV_P_Thông hơi Xí|75|7000,29990",
    u"WC-1044655 Ống đứng xí|AV_P_Nước Thải Xí|110|7000,30200",
    u"WC-1044673 Ống đứng rửa|AV_P_Nước Thải Rửa|90|57650,29700",
    u"WC-1044673 Thông hơi|AV_P_Thông hơi Xí|75|57650,30010",
    u"WC-1044673 Ống đứng xí|AV_P_Nước Thải Xí|110|57650,30200",
    u"WC-1044323 Ống đứng xí|AV_P_Nước Thải Xí|110|31600,13850",
    u"WC-1044323 Thông hơi|AV_P_Thông hơi Xí|75|31850,13850",
    u"WC-1044323 Ống đứng rửa|AV_P_Nước Thải Rửa|90|32100,13850",
    u"WC-1044314 Ống đứng xí|AV_P_Nước Thải Xí|110|33050,13850",
    u"WC-1044314 Thông hơi|AV_P_Thông hơi Xí|75|32800,13850",
    u"WC-1044314 Ống đứng rửa|AV_P_Nước Thải Rửa|90|32550,13850",
    u"WC-1044346 Ống đứng xí|AV_P_Nước Thải Xí|110|26325,16600",
    u"WC-1044346 Thông hơi|AV_P_Thông hơi Xí|75|26325,16300",
    u"WC-1044346 Ống đứng rửa|AV_P_Nước Thải Rửa|90|26325,16015",
])


def arg(i, default):
    if not DYNAMO or len(IN) <= i or IN[i] is None or (isinstance(IN[i], str) and not IN[i].strip()):
        return default
    return IN[i]


routes_txt = arg(0, DEF_ROUTES)
stacks_txt = arg(1, DEF_STACKS)
stack_range = arg(2, u"-3300>3300")
h_top_mm = float(arg(3, 400.0))
slope = float(arg(4, 2.0)) / 100.0
pipe_type_name = arg(5, u"AV_u.PVC PN6").strip()
level_name = (arg(6, u"") or u"").strip()
color_txt = arg(7, u"Thông hơi=128,0,128;Xí=255,255,0;Rửa=0,0,255")
drain_name = arg(8, u"AV-Phễu thoát sàn : 100").strip()
dry_run = bool(arg(9, True))
replace = bool(arg(10, False))
z_vent = float(arg(11, -220.0))      # cao độ tâm ống thông hơi ngang (THX / THR), mm so với level


def is_vent(r):
    return bool(r["head"] and r["head"][0] in ("thx", "thr"))


# ---------------------------------------------------------------- phần hình học (chạy được ngoài Revit)

def lines_of(txt):
    return [l.strip() for l in txt.replace(u"\r", u"\n").split(u"\n") if l.strip() and not l.strip().startswith(u"#")]


def pt(s):
    a = s.split(u",")
    return float(a[0]), float(a[1])


def d2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def parse(routes_txt, stacks_txt):
    stacks = []
    for l in lines_of(stacks_txt):
        f = [x.strip() for x in l.split(u"|")]
        if len(f) != 4:
            raise Exception(u"Ống đứng sai định dạng 'Tên|System|DN|x,y': " + l)
        stacks.append({"name": f[0], "system": f[1], "dn": float(f[2]), "xy": pt(f[3]), "joins": []})
    routes = []
    for l in lines_of(routes_txt):
        f = [x.strip() for x in l.split(u"|")]
        if len(f) < 5:
            raise Exception(u"Tuyến sai định dạng 'Tên|System|DN|Đầu|x,y;…[|Vào=z][|TT=x,y]': " + l)
        zend, tt_end = None, None
        for opt in f[5:]:
            k, _, v = opt.partition(u"=")
            if k.strip().upper() == u"TT":
                tt_end = pt(v)
            elif opt.strip():
                zend = float(v if u"=" in opt else opt)
        pts = [pt(q) for q in f[4].split(u";") if q.strip()]
        if len(pts) < 2:
            raise Exception(u"Tuyến '{}' cần ≥ 2 điểm".format(f[0]))
        head = f[3]
        if head.upper().startswith(u"PHEUD"):
            head = ("drainv", float(head.partition(u"=")[2] or 0))
        elif head.upper().startswith(u"PHEU"):
            head = ("drain", float(head.partition(u"=")[2] or 0))
        elif head == u"@":
            head = ("fixture", None)
        elif head.upper() == u"TT":
            head = ("cap", None)
        elif head.upper() in (u"THX", u"THR"):
            head = (head.lower(), None)      # thông hơi từ ống xuống bệt / từ đầu ống rửa (cùng điểm đầu)
        elif head:
            head = ("z", float(head))
        else:
            head = None
        dns = [float(x) for x in f[2].split(u"/") if x.strip()]
        dns += [dns[-1]] * (len(pts) - 1 - len(dns))
        routes.append({"name": f[0], "system": f[1], "dn": dns[0], "dns": dns[:len(pts) - 1], "head": head, "pts": pts,
                       "zend": zend, "tt_end": tt_end})
    return routes, stacks


def turn_deg(a, b, c):
    u = (b[0] - a[0], b[1] - a[1])
    v = (c[0] - b[0], c[1] - b[1])
    cos = (u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def plan(routes, stacks):
    """Nơi xả của mỗi tuyến + cao độ tương đối (mm so với level) của mọi đỉnh. Trả về danh sách cảnh báo."""
    notes = []
    for r in routes:
        end = r["pts"][-1]
        st = [s for s in stacks if d2(s["xy"], end) <= SNAP_MM]
        if st:
            r["to"] = ("stack", st[0])
            r["pts"][-1] = st[0]["xy"]
            if st[0]["system"] != r["system"]:
                notes.append(u"Tuyến '{}' ({}) xả vào ống đứng '{}' ({}) – khác system".format(
                    r["name"], r["system"], st[0]["name"], st[0]["system"]))
            continue
        hit = None
        for o in routes:
            if o is r:
                continue
            for i, q in enumerate(o["pts"][1:-1], 1):
                if d2(q, end) <= SNAP_MM:
                    hit = (o, i)
        if hit is None:
            raise Exception(u"Tuyến '{}': điểm cuối {:.0f},{:.0f} không trùng tâm ống đứng hay đỉnh giữa tuyến khác".format(
                r["name"], end[0], end[1]))
        o, i = hit
        if turn_deg(o["pts"][i - 1], o["pts"][i], o["pts"][i + 1]) > 1.0:
            raise Exception(u"Tuyến '{}' nhập vào '{}' tại đỉnh có gấp khúc – Y cần tuyến chính đi thẳng".format(
                r["name"], o["name"]))
        if r["head"] and r["head"][0] == "drainv":
            # phễu đấu từ trên xuống: phễu nằm trên đoạn ống chính ngay thượng lưu đỉnh i, cách ≥ DRAINV_MIN_H
            a, b = o["pts"][i - 1], o["pts"][i]
            p = r["pts"][0]
            L = d2(a, b)
            t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)
            off = abs((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) / L
            if len(r["pts"]) != 2 or off > SNAP_MM or t < -1e-6 or t > 1:
                raise Exception(u"Tuyến '{}' (PHEUD): phễu phải nằm trên đoạn ống '{}' ngay trước đỉnh {:.0f},{:.0f}".format(
                    r["name"], o["name"], b[0], b[1]))
            if d2(p, b) < DRAINV_MIN_H:
                raise Exception(u"Tuyến '{}' (PHEUD): phễu cách điểm Y {:.0f} mm < {:.0f} (nhánh Y 136 + co 45°)".format(
                    r["name"], d2(p, b), DRAINV_MIN_H))
        else:
            ang = turn_deg(r["pts"][-2], end, o["pts"][i + 1])
        if not (r["head"] and r["head"][0] == "drainv") and not is_vent(r) and abs(ang - 45) > 1.0:
            notes.append(u"Tuyến '{}' nhập vào '{}' lệch {:.0f}° (Y cần 45°)".format(r["name"], o["name"], ang))
        r["to"] = ("route", o, i)
        r["pts"][-1] = o["pts"][i]
        if o["system"] != r["system"]:
            notes.append(u"Tuyến '{}' nhập vào '{}' khác system".format(r["name"], o["name"]))
    for r in routes:
        for i, (a, b, c) in enumerate(zip(r["pts"], r["pts"][1:], r["pts"][2:]), 1):
            t = turn_deg(a, b, c)
            if t > 1.0 and abs(t - 45) > 1.0 and not is_vent(r):     # thông hơi được gấp 90° (như mẫu CTN)
                notes.append(u"Tuyến '{}' gấp {:.0f}° tại {:.0f},{:.0f} (quy định gấp 45°)".format(r["name"], t, b[0], b[1]))
            if t <= 1.0 and not any(o["to"][0] == "route" and o["to"][1] is r and o["to"][2] == i for o in routes):
                # đỉnh thẳng hàng không có nhánh nhập → hai ống không có gì nối (không co, không Y)
                raise Exception(u"Tuyến '{}': đỉnh {:.0f},{:.0f} thẳng hàng mà không có tuyến nào nhập vào – bỏ đỉnh này".format(
                    r["name"], b[0], b[1]))

    # khoảng cách tới ống đứng theo đường ống (mm) tại mỗi đỉnh
    def dist_to_stack(r, depth=0):
        if depth > len(routes):
            raise Exception(u"Tuyến nối vòng")
        if "dist" in r:
            return r["dist"]
        segs = [d2(a, b) for a, b in zip(r["pts"], r["pts"][1:])]
        if r["to"][0] == "stack":
            base, stack, root = 0.0, r["to"][1], r
        else:
            o, i = r["to"][1], r["to"][2]
            base, stack, root = dist_to_stack(o, depth + 1)[i], o["stack"], o["root"]
        r["stack"], r["root"] = stack, root
        out = [base]
        for L in reversed(segs):
            out.insert(0, out[0] + L)
        r["dist"] = out
        return out

    for r in routes:
        dist_to_stack(r)
    # mỗi ống đứng: điểm xa nhất của các nhánh vào nó có tâm = −h_top; tuyến có 'Vào=z' (trường 6) vào ống đứng
    # ở đúng cao độ z (tê riêng, VD thoát sàn thả sâu dưới tê nhánh xí) – cả cây nhánh của nó tính từ z đó
    for s in stacks:
        rs = [r for r in routes if r["stack"] is s]
        if not rs:
            continue
        free = [r for r in rs if r["root"]["zend"] is None and not (r["head"] and r["head"][0] == "drainv")]
        if free:
            s["entry_z"] = -h_top_mm - slope * max(r["dist"][0] for r in free)
        for r in rs:
            if is_vent(r):
                r["z"] = [z_vent] * len(r["pts"])        # thông hơi ngang phẳng ở z_vent
            else:
                base = s["entry_z"] if r["root"]["zend"] is None else r["root"]["zend"]
                r["z"] = [base + slope * d for d in r["dist"]]
            if r["to"][0] == "stack":
                s["joins"].append(r)
        zs = sorted(r["z"][-1] for r in s["joins"])
        for z1, z2 in zip(zs, zs[1:]):
            if z2 - z1 < 250:
                notes.append(u"Ống đứng '{}': hai tê ở {:+.0f} và {:+.0f} cách {:.0f} mm – dễ chồng phụ kiện (nên ≥ 280)".format(
                    s["name"], z1, z2, z2 - z1))
    for r in routes:
        if r["head"] and r["head"][0] == "drainv":
            # nhánh nghiêng 45° theo phương đứng: co 45° ngay dưới phễu cao hơn điểm Y đúng bằng khoảng cách mặt bằng
            o, i = r["to"][1], r["to"][2]
            h = d2(r["pts"][0], o["pts"][i])
            r["z"] = [o["z"][i] + h, o["z"][i]]
            if r["z"][0] > DRAINV_MAX_TOP:
                notes.append(u"Tuyến '{}' (PHEUD): co dưới phễu ở {:+.0f} – sát thân phễu (đáy ≈ −165)".format(r["name"], r["z"][0]))
    for r in routes:
        h = r["head"]
        if h and h[0] == "z" and h[1] < r["z"][0] + MIN_LEN_MM:
            raise Exception(u"Tuyến '{}': đầu ống xuống {:.0f} thấp hơn tâm nhánh {:.0f}".format(r["name"], h[1], r["z"][0]))
        if is_vent(r):
            # THX: tuyến xí cùng điểm đầu (tê trên ống xuống bệt); THR: tuyến có thông tắc đầu (TT) cùng điểm đầu
            want = "fixture" if h[0] == "thx" else "cap"
            src = [o for o in routes if o is not r and o["head"] and o["head"][0] == want and d2(o["pts"][0], r["pts"][0]) <= SNAP_MM]
            if not src:
                raise Exception(u"Tuyến '{}' ({}): không có tuyến {} cùng điểm đầu {:.0f},{:.0f}".format(
                    r["name"], h[0].upper(), u"xí '@'" if want == "fixture" else u"thông tắc 'TT'", r["pts"][0][0], r["pts"][0][1]))
            r["src"] = src[0]
            src[0]["vent"] = r
            gap = z_vent - src[0]["z"][0]
            if h[0] == "thx" and gap < VENT_MIN_RISE_X:
                notes.append(u"Tuyến '{}': tê thông hơi trên ống xuống bệt chỉ cao hơn nhánh xí {:.0f} mm (nên ≥ {:.0f})".format(
                    r["name"], gap, VENT_MIN_RISE_X))
            if h[0] == "thr" and gap < VENT_MIN_RISE_R:
                notes.append(u"Tuyến '{}': ống đứng thông hơi ở đầu ống rửa chỉ cao {:.0f} mm (tê 94 + co 90° + 20 ≈ {:.0f})".format(
                    r["name"], gap, VENT_MIN_RISE_R))
        if r["tt_end"] is not None:
            ks = [k for k in range(1, len(r["pts"]) - 1) if d2(r["pts"][k], r["tt_end"]) <= SNAP_MM]
            if not ks or turn_deg(r["pts"][ks[0] - 1], r["pts"][ks[0]], r["pts"][ks[0] + 1]) < 1.0:
                raise Exception(u"Tuyến '{}': TT={:.0f},{:.0f} phải là một đỉnh gấp khúc của tuyến".format(
                    r["name"], r["tt_end"][0], r["tt_end"][1]))
            r["tt_k"] = ks[0]
            out_len = d2(r["pts"][ks[0]], r["pts"][ks[0] + 1])
            if out_len < TT_END_MIN_OUT:
                notes.append(u"Tuyến '{}': sau thông tắc cuối chỉ còn {:.0f} mm ống (nhánh Y 75 dài 161 + phụ kiện kế tiếp)".format(
                    r["name"], out_len))
    return notes


def describe(routes, stacks):
    out = []
    for s in stacks:
        out.append(u"Ống đứng '{}' D{:.0f} tại {:.0f},{:.0f} ({}){}".format(
            s["name"], s["dn"], s["xy"][0], s["xy"][1], s["system"],
            u" – tê ở " + u", ".join(u"{:+.0f}".format(r["z"][-1]) for r in s["joins"]) if s["joins"] else u" – không có nhánh"))
    for r in routes:
        L = sum(d2(a, b) for a, b in zip(r["pts"], r["pts"][1:]))
        to = r["to"][1]["name"]
        head = {None: u"không ống xuống", "fixture": u"ống xuống từ thiết bị", "z": u"ống xuống từ {:+.0f}",
                "drain": u"phễu thu (chân {:+.0f})", "drainv": u"phễu thu đấu từ trên xuống (chân {:+.0f})",
                "cap": u"thông tắc (nút bịt)", "thx": u"thông hơi từ ống xuống bệt (tê)",
                "thr": u"thông hơi từ đầu ống rửa (ống đứng + tê)"}[r["head"][0] if r["head"] else None]
        if r.get("tt_k"):
            head += u", thông tắc cuối tại {:.0f},{:.0f}".format(*r["pts"][r["tt_k"]])
        if r["head"] and r["head"][1] is not None:
            head = head.format(r["head"][1])
        out.append(u"Tuyến '{}' D{} dài {:.0f} mm, tâm {:+.0f} → {:+.0f}, {} → '{}' ({})".format(
            r["name"], u"/".join(u"{:.0f}".format(d) for d in r["dns"]), L, r["z"][0], r["z"][-1], head, to, u"Y 45°" if r["to"][0] == "route" else u"tê"))
    return out


# ---------------------------------------------------------------- phần Revit

def mm2ft(v):
    return v / 304.8


def ft2mm(v):
    return v * 304.8


def get_name(e):
    """CPython3 (Python.NET) không đọc được e.Name của PipeType / PipingSystemType ('property cannot be read')
    → đọc qua reflection của Element.Name, cuối cùng mới lấy tham số tên type (Dynamo 2026-10-21)."""
    try:
        return e.Name
    except Exception:
        pass
    try:
        from Autodesk.Revit.DB import Element
        return clr.GetClrType(Element).GetProperty("Name").GetValue(e, None)
    except Exception:
        pass
    for bip in (BuiltInParameter.ALL_MODEL_TYPE_NAME, BuiltInParameter.SYMBOL_NAME_PARAM):
        p = e.get_Parameter(bip)
        if p is not None and p.AsString():
            return p.AsString()
    return u""


class Builder(object):
    def __init__(self, level, pipe_type, systems, fits):
        self.level, self.pt, self.systems, self.fits = level, pipe_type, systems, fits
        self.z0 = level.Elevation
        self.made = []          # (element, system)
        self.min_len = mm2ft(MIN_LEN_MM)

    def xyz(self, p, z):
        return XYZ(mm2ft(p[0]), mm2ft(p[1]), self.z0 + mm2ft(z))

    def pipe(self, sysname, dn, a, b, name):
        p = Pipe.Create(doc, self.systems[sysname].Id, self.pt.Id, self.level.Id, a, b)
        p.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(mm2ft(dn))
        p.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | {}".format(COMMENT, name))
        self.made.append((p, sysname))
        return p

    @staticmethod
    def con(p, q):
        return min(list(p.ConnectorManager.Connectors), key=lambda c: c.Origin.DistanceTo(q))

    @staticmethod
    def far(p, q):
        return max(list(p.ConnectorManager.Connectors), key=lambda c: c.Origin.DistanceTo(q)).Origin

    def ok(self, pipes, dirs):
        for p, d in zip(pipes, dirs):
            if not p.IsValidObject:
                return False
            c = p.Location.Curve
            if c.Length < self.min_len or c.GetEndPoint(1).Subtract(c.GetEndPoint(0)).Normalize().DotProduct(d) < 0.99:
                return False
        return True

    def guarded(self, pipes, fn):
        """Phụ kiện trong SubTransaction: ống bị cắt lẹm / đổi chiều → hoàn tác. Trả về lý do lỗi hoặc None."""
        dirs = [p.Location.Curve.GetEndPoint(1).Subtract(p.Location.Curve.GetEndPoint(0)).Normalize() for p in pipes]
        st = SubTransaction(doc)
        st.Start()
        why, fi = None, None
        try:
            fi = fn()
            doc.Regenerate()
            if not self.ok(pipes, dirs):
                why = u"ống quá ngắn / đổi chiều"
        except Exception as ex:
            why = u"{}".format(ex)
        if why is None:
            cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) if fi is not None else None
            if cm is not None and not cm.IsReadOnly:
                cm.Set(u"{} | phụ kiện".format(COMMENT))
            st.Commit()
            self.made.append((fi, self.sys_of(pipes[0])))
        else:
            st.RollBack()
        return why

    def sys_of(self, p):
        for e, s in self.made:
            if e.Id == p.Id:
                return s
        return u""

    def elbow(self, p1, p2, q):
        return self.guarded([p1, p2], lambda: doc.Create.NewElbowFitting(self.con(p1, q), self.con(p2, q)))

    def place3(self, sym, N, legA, legB, br):
        """Y / tê: legA → +X (C2), legB → −X (C1), nhánh → C3 (giống ARV_TaoOngThoatNuocTuCAD_v1)."""
        def run():
            uA = self.far(legA, N).Subtract(N).Normalize()
            uB = self.far(legB, N).Subtract(N).Normalize()
            ub = self.far(br, N).Subtract(N).Normalize()
            X = uA.Subtract(uB).Normalize()
            Yp = ub.Subtract(X.Multiply(ub.DotProduct(X)))
            if Yp.GetLength() < 0.05:
                raise Exception(u"nhánh thẳng hàng ống chính")
            Y = Yp.Normalize().Negate()
            Z = X.CrossProduct(Y)
            fi = doc.Create.NewFamilyInstance(N, sym, self.level, StructuralType.NonStructural)
            for k, p in ((u"Nominal Radius 1", legB), (u"Nominal Radius 2", legA), (u"Nominal Radius 3", br)):
                if fi.LookupParameter(k) is not None:
                    fi.LookupParameter(k).Set(p.Diameter / 2)
            if fi.LookupParameter(u"Nominal Radius 1") is None and fi.LookupParameter(u"Nominal Radius") is not None:
                fi.LookupParameter(u"Nominal Radius").Set(legB.Diameter / 2)
            tr = X.X + Y.Y + Z.Z
            ang = math.acos(max(-1.0, min(1.0, (tr - 1) / 2)))
            if ang > 1e-9:
                if math.pi - ang < 1e-6:
                    k = 0 if (X.X >= Y.Y and X.X >= Z.Z) else (1 if Y.Y >= Z.Z else 2)
                    ax = [XYZ(X.X + 1, X.Y, X.Z), XYZ(Y.X, Y.Y + 1, Y.Z), XYZ(Z.X, Z.Y, Z.Z + 1)][k]
                else:
                    ax = XYZ(Y.Z - Z.Y, Z.X - X.Z, X.Y - Y.X)
                ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateUnbound(N, ax.Normalize()), ang)
            doc.Regenerate()
            lp = fi.Location.Point
            if lp.DistanceTo(N) > 1e-6:
                ElementTransformUtils.MoveElement(doc, fi.Id, N.Subtract(lp))
                doc.Regenerate()
            cs = list(fi.MEPModel.ConnectorManager.Connectors)
            todo = []
            for p, u in ((legA, uA), (legB, uB), (br, ub)):
                c = max(cs, key=lambda k: k.CoordinateSystem.BasisZ.DotProduct(u))
                f = self.far(p, N)
                if f.Subtract(c.Origin).DotProduct(u) < self.min_len:
                    raise Exception(u"ống quá ngắn cho phụ kiện")
                todo.append((p, c, f))
            for p, c, f in todo:
                end1 = p.Location.Curve.GetEndPoint(1).IsAlmostEqualTo(f)
                p.Location.Curve = Line.CreateBound(c.Origin, f) if end1 else Line.CreateBound(f, c.Origin)
                self.con(p, c.Origin).ConnectTo(c)
            return fi
        return self.guarded([legA, legB, br], run)


def sanitary_connectors():
    """Connector Sanitary của thiết bị vệ sinh trong mô hình + mọi file link (toạ độ mô hình đang mở)."""
    out = []
    srcs = [(doc, Transform.Identity)]
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        ld = li.GetLinkDocument()
        if ld is not None:
            srcs.append((ld, li.GetTotalTransform()))
    for d, tf in srcs:
        # OfClass(FamilyInstance): Python.NET trả đúng kiểu FamilyInstance → có MEPModel (2026-10-21 bệt trong link
        # không được nhận khi lọc theo category)
        for e in FilteredElementCollector(d).OfClass(FamilyInstance).OfCategory(BuiltInCategory.OST_PlumbingFixtures).ToElements():
            mep = getattr(e, "MEPModel", None)
            if mep is None or mep.ConnectorManager is None:
                continue
            for c in mep.ConnectorManager.Connectors:
                if c.Domain == Domain.DomainPiping and is_sanitary(c):
                    out.append((tf.OfPoint(c.Origin), e, d.Title))
    return out


def previous_run():
    """Id phần tử của lần chạy trước: ống / phễu / phụ kiện có Comments ARV-THOATWC + phụ kiện nối vào ống đó
    (bản trước 2026-10-21 chưa ghi Comments cho phụ kiện)."""
    def tagged(e):
        p = e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        return p is not None and (p.AsString() or u"").startswith(COMMENT)
    fit_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_PipeFitting).Id.Value
    ids = {}
    for cat in (BuiltInCategory.OST_PipeCurves, BuiltInCategory.OST_PipeFitting, BuiltInCategory.OST_PlumbingFixtures):
        for e in FilteredElementCollector(doc).OfCategory(cat).WhereElementIsNotElementType().ToElements():
            if not tagged(e):
                continue
            ids[e.Id.Value] = e.Id
            if isinstance(e, Pipe):
                for c in e.ConnectorManager.Connectors:
                    for r in c.AllRefs:
                        o = r.Owner
                        if o is not None and o.Category is not None and o.Category.Id.Value == fit_cat:
                            ids[o.Id.Value] = o.Id
    return [ids[k] for k in sorted(ids)]


def is_sanitary(c):
    # str(enum) trên Python.NET không chắc ra "Sanitary" (Dynamo 2026-10-21: bệt trong link không được nhận) → so enum
    try:
        if c.PipeSystemType == PipeSystemType.Sanitary:
            return True
    except Exception:
        pass
    return u"Sanitary" in u"{}".format(c.PipeSystemType)


def drain_symbol():
    fam, _, typ = [s.strip() for s in drain_name.partition(u":")]
    def find(d):
        for s in FilteredElementCollector(d).OfClass(FamilySymbol).ToElements():
            if s.FamilyName == fam and (not typ or get_name(s) == typ):
                return s
        return None
    s = find(doc)
    if s is not None:
        return s, u"có sẵn"
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        ld = li.GetLinkDocument()
        src = find(ld) if ld is not None else None
        if src is not None:
            ids = List[ElementId]()
            ids.Add(src.Id)
            new = ElementTransformUtils.CopyElements(ld, ids, doc, Transform.Identity, CopyPasteOptions())
            return doc.GetElement(list(new)[0]), u"chép từ " + ld.Title
    raise Exception(u"Không có phễu thu '{}' trong mô hình hay file link".format(drain_name))


def junctions(pt):
    rpm = pt.RoutingPreferenceManager
    wye = tee = None
    for i in range(rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Junctions)):
        s = doc.GetElement(rpm.GetRule(RoutingPreferenceRuleGroupType.Junctions, i).MEPPartId)
        if not isinstance(s, FamilySymbol):
            continue
        if u"WYE" in s.FamilyName.upper():
            wye = wye or s
        else:
            tee = tee or s
    for s in (wye, tee):
        if s is not None and not s.IsActive:
            s.Activate()
    return wye, tee


def apply_colors(made):
    rules = []
    for item in color_txt.split(u";"):
        k, _, v = item.partition(u"=")
        try:
            r, g, b = [int(x) for x in v.split(u",")]
        except ValueError:
            continue
        rules.append((k.strip().lower(), Color(r, g, b)))
    if not rules:
        return u"không tô màu"
    view = doc.ActiveView
    solid = [f for f in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements() if f.GetFillPattern().IsSolidFill]
    n = 0
    for e, sysname in made:
        if e is None or not e.IsValidObject:
            continue
        for k, col in rules:
            if k in sysname.lower():
                og = OverrideGraphicSettings()
                og.SetProjectionLineColor(col)
                og.SetCutLineColor(col)
                if solid:
                    og.SetSurfaceForegroundPatternId(solid[0].Id)
                    og.SetSurfaceForegroundPatternColor(col)
                view.SetElementOverrides(e.Id, og)
                n += 1
                break
    return u"tô màu {} phần tử trong view '{}'".format(n, get_name(view))


def build(routes, stacks, level, ptype, systems, fits, lines):
    b = Builder(level, ptype, systems, fits)
    fail = []
    fixtures = sanitary_connectors()
    route_pipes = {}
    # 1. nhánh: ống xuống + các đoạn ngang
    for r in routes:
        nodes = [b.xyz(p, z) for p, z in zip(r["pts"], r["z"])]
        segs = [b.pipe(r["system"], dn, a, c, r["name"]) for a, c, dn in zip(nodes, nodes[1:], r["dns"])]
        route_pipes[id(r)] = (nodes, segs)
        h = r["head"]
        top, drain_conn = None, None
        if h and h[0] == "z":
            top = b.xyz(r["pts"][0], h[1])
        elif h and h[0] == "fixture":
            near = [f for f in fixtures if d2((ft2mm(f[0].X), ft2mm(f[0].Y)), r["pts"][0]) <= FIX_SNAP_MM]
            if not near:
                dmin = min([d2((ft2mm(f[0].X), ft2mm(f[0].Y)), r["pts"][0]) for f in fixtures] or [-1])
                fail.append(u"Tuyến '{}': không thấy connector thiết bị ≤ {:.0f} mm quanh điểm đầu "
                            u"({} connector Sanitary trong mô hình + link, gần nhất {:.0f} mm)".format(
                                r["name"], FIX_SNAP_MM, len(fixtures), dmin))
            else:
                c = min(near, key=lambda f: d2((ft2mm(f[0].X), ft2mm(f[0].Y)), r["pts"][0]))
                top = XYZ(nodes[0].X, nodes[0].Y, c[0].Z)
                lines.append(u"Tuyến '{}': connector {} Id {} ({}) z {:+.0f}, lệch {:.0f} mm".format(
                    r["name"], c[1].Symbol.FamilyName, c[1].Id.Value, c[2], ft2mm(c[0].Z - b.z0),
                    d2((ft2mm(c[0].X), ft2mm(c[0].Y)), r["pts"][0])))
        elif h and h[0] in ("drain", "drainv"):     # drainv: nodes[0] đã ở cao độ co 45° dưới phễu (plan)
            sym, how = drain_symbol()
            if not sym.IsActive:
                sym.Activate()
            fi = doc.Create.NewFamilyInstance(b.xyz(r["pts"][0], h[1]), sym, level, StructuralType.NonStructural)
            fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | {}".format(COMMENT, r["name"]))
            doc.Regenerate()
            b.made.append((fi, r["system"]))
            cs = [c for c in fi.MEPModel.ConnectorManager.Connectors if c.Domain == Domain.DomainPiping]
            drain_conn = cs[0]
            top = XYZ(nodes[0].X, nodes[0].Y, drain_conn.Origin.Z)
            lines.append(u"Phễu thu '{}' ({}) tại {:.0f},{:.0f}, chân {:+.0f}".format(drain_name, how, r["pts"][0][0], r["pts"][0][1], h[1]))
        elif h and h[0] == "thr":
            # ống đứng thông hơi: từ đầu ống rửa (tuyến TT cùng điểm đầu) lên cao độ thông hơi
            src = r["src"]
            top = b.xyz(src["pts"][0], src["z"][0])
        if top is not None:
            if abs(top.Z - nodes[0].Z) < b.min_len:
                fail.append(u"Tuyến '{}': đầu ống xuống không cao hơn nhánh".format(r["name"]))
            elif h[0] == "fixture" and r.get("vent") is not None:
                # THX: ống xuống bệt cắt đôi tại cao độ thông hơi để đặt tê
                pv = XYZ(top.X, top.Y, b.z0 + mm2ft(z_vent))
                upper = b.pipe(r["system"], r["dn"], top, pv, r["name"])
                lower = b.pipe(r["system"], r["dn"], pv, nodes[0], r["name"])
                r["thx_upper"], r["thx_pv"] = upper, pv
                route_pipes[id(r)] = (nodes, [lower] + segs)
                r["has_drop"] = True
            else:
                drop = b.pipe(r["system"], r["dn"], top, nodes[0], r["name"])
                if drain_conn is not None:
                    b.con(drop, drain_conn.Origin).ConnectTo(drain_conn)
                route_pipes[id(r)] = (nodes, [drop] + segs)
                r["has_drop"] = True
    # 1b. THR: đoạn thông tắc lùi sau đầu ống rửa (nút bịt ở đây thay cho đầu ống)
    for r in routes:
        if r["head"] and r["head"][0] == "cap" and r.get("vent") is not None:
            nodes, segs = route_pipes[id(r)]
            a, c = r["pts"][0], r["pts"][1]
            L = d2(a, c)
            back = (a[0] + (a[0] - c[0]) / L * THR_STUB, a[1] + (a[1] - c[1]) / L * THR_STUB)
            r["thr_stub"] = b.pipe(r["system"], r["dns"][0], nodes[0], b.xyz(back, r["z"][0]), r["name"])
    # 2. ống đứng, cắt tại các cao độ nhánh vào
    stack_pipes = {}
    rng = [float(x) for x in stack_range.split(u">")]
    for s in stacks:
        zs = sorted(set([rng[0], rng[1]] + [r["z"][-1] for r in s["joins"]]))
        ps = [b.pipe(s["system"], s["dn"], b.xyz(s["xy"], z1), b.xyz(s["xy"], z2), s["name"]) for z1, z2 in zip(zs, zs[1:])]
        stack_pipes[id(s)] = (zs, ps)
    doc.Regenerate()
    # 3. Y + tê trước (cần nhiều chỗ), co sau
    for r in routes:
        nodes, segs = route_pipes[id(r)]
        last = segs[-1]
        if r["to"][0] == "stack":
            s = r["to"][1]
            zs, ps = stack_pipes[id(s)]
            i = zs.index(r["z"][-1])
            why = b.place3(fits["tee"], nodes[-1], ps[i], ps[i - 1], last)    # trên = +X, dưới = −X
            kind = u"tê vào ống đứng '{}'".format(s["name"])
        else:
            o, i = r["to"][1], r["to"][2]
            onodes, osegs = route_pipes[id(o)]
            k = i + (1 if o.get("has_drop") else 0)    # đoạn sau đỉnh i trong danh sách ống của o
            fit = fits["tee"] if is_vent(r) else fits["wye"]     # thông hơi nhập nhau bằng tê (gấp 90°)
            why = b.place3(fit, onodes[i], osegs[k - 1], osegs[k], last)
            kind = u"{} vào tuyến '{}'".format(u"tê" if is_vent(r) else u"Y", o["name"])
        if why:
            fail.append(u"Tuyến '{}': {} – {}".format(r["name"], kind, why))
    # 3b. tê thông hơi: trên ống xuống bệt (THX) và ở đầu ống rửa (THR)
    for r in routes:
        if not is_vent(r):
            continue
        nodes, segs = route_pipes[id(r)]
        src = r["src"]
        if r["head"][0] == "thx":
            if "thx_upper" not in src:
                fail.append(u"Tuyến '{}': ống xuống bệt chưa dựng, không đặt tê thông hơi".format(r["name"]))
                continue
            _, ssegs = route_pipes[id(src)]
            why = b.place3(fits["tee"], src["thx_pv"], src["thx_upper"], ssegs[0], segs[0])
        else:
            snodes, ssegs = route_pipes[id(src)]
            why = b.place3(fits["tee"], snodes[0], src["thr_stub"], ssegs[0], segs[0])
        if why:
            fail.append(u"Tuyến '{}': tê thông hơi – {}".format(r["name"], why))
    for r in routes:
        nodes, segs = route_pipes[id(r)]
        off = 1 if r.get("has_drop") else 0
        pts = ([None] if off else []) + nodes     # điểm đầu của từng ống trong segs
        for j, (p1, p2) in enumerate(zip(segs, segs[1:])):
            q = pts[j + 1]
            k = j + 1 - off                       # chỉ số đỉnh trên tuyến gốc
            if k >= 1 and turn_deg(r["pts"][k - 1], r["pts"][k], r["pts"][k + 1]) < 1.0:
                continue                          # thẳng hàng theo tuyến gốc (đỉnh có Y) – không co; xét theo ống
                                                  # sau khi Y cắt bị lệch số → từng cố đặt co (Dynamo 2026-10-21)
            if k >= 1 and k == r.get("tt_k"):
                # thông tắc ở chỗ gấp cuối trước trục (mẫu HN Garden City): ống chính chạy thẳng tới nút bịt,
                # nhánh Y rẽ vào trục – Y: chân thẳng phía nút bịt (+X), nhánh nghiêng về phía nút bịt
                a = r["pts"][k - 1]
                L = d2(a, r["pts"][k])
                ahead = (r["pts"][k][0] + (r["pts"][k][0] - a[0]) / L * TT_END_STUB,
                         r["pts"][k][1] + (r["pts"][k][1] - a[1]) / L * TT_END_STUB)
                stub = b.pipe(r["system"], r["dns"][k - 1], q, b.xyz(ahead, r["z"][k]), r["name"])
                r["tt_stub"] = stub
                doc.Regenerate()
                why = b.place3(fits["wye"], q, stub, p1, p2)
                if why:
                    fail.append(u"Tuyến '{}': thông tắc cuối tại {:.0f},{:.0f} – {}".format(r["name"], ft2mm(q.X), ft2mm(q.Y), why))
                continue
            why = b.elbow(p1, p2, q)
            if why:
                fail.append(u"Tuyến '{}': co tại {:.0f},{:.0f} – {}".format(r["name"], ft2mm(q.X), ft2mm(q.Y), why))
    # 4. thông tắc: nút bịt theo rule Caps của pipe type – đặt sau Y / tê / co để chỉ còn đầu thông tắc hở
    fit_cat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_PipeFitting).Id.Value

    def cap_on(p, r, what):
        opened = [c for c in p.ConnectorManager.Connectors if not c.IsConnected]
        if len(opened) != 1:
            fail.append(u"Tuyến '{}': {} – ống có {} đầu hở (cần 1), không đặt nút bịt".format(r["name"], what, len(opened)))
            return
        st = SubTransaction(doc)
        st.Start()
        try:
            PlumbingUtils.PlaceCapOnOpenEnds(doc, p.Id, b.pt.Id)
            doc.Regenerate()
            caps = [x.Owner for x in opened[0].AllRefs
                    if x.Owner.Id != p.Id and x.Owner.Category is not None and x.Owner.Category.Id.Value == fit_cat]
            if not caps:
                raise Exception(u"Revit không đặt nút bịt (kiểm tra rule Caps của pipe type)")
            caps[0].get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | thông tắc".format(COMMENT))
            st.Commit()
            b.made.append((caps[0], r["system"]))
        except Exception as ex:
            st.RollBack()
            fail.append(u"Tuyến '{}': {} – {}".format(r["name"], what, ex))

    for r in routes:
        if r["head"] and r["head"][0] == "cap":
            cap_on(r["thr_stub"] if r.get("vent") is not None else route_pipes[id(r)][1][0], r, u"thông tắc đầu")
        if r.get("tt_stub") is not None:
            cap_on(r["tt_stub"], r, u"thông tắc cuối")
    return b, fail


def main():
    routes, stacks = parse(routes_txt, stacks_txt)
    notes = plan(routes, stacks)
    lines = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"THỰC HIỆN"),
             u"Dốc {:.1f} %, tâm nhánh cao nhất = level − {:.0f}; ống đứng {} so với level".format(slope * 100, h_top_mm, stack_range)]
    lines += describe(routes, stacks) + [u"LƯU Ý: " + n for n in notes]
    if not DYNAMO:
        return lines

    levels = dict((get_name(l), l) for l in FilteredElementCollector(doc).OfClass(Level).ToElements())
    level = levels.get(level_name) if level_name else getattr(doc.ActiveView, "GenLevel", None)
    if level is None:
        return lines + [u"DỪNG: không xác định được level ('{}'). Mở mặt bằng của tầng hoặc nhập IN[6]. Các level: {}".format(
            level_name, u", ".join(sorted(levels)))]
    ptype = [p for p in FilteredElementCollector(doc).OfClass(PipeType).ToElements() if get_name(p) == pipe_type_name]
    if not ptype:
        return lines + [u"DỪNG: không có pipe type '{}' (tool không tạo type).".format(pipe_type_name)]
    ptype = ptype[0]
    systems = dict((get_name(s), s) for s in FilteredElementCollector(doc).OfClass(PipingSystemType).ToElements())
    bad = sorted(set(x["system"] for x in routes + stacks if x["system"] not in systems))
    if bad:
        return lines + [u"DỪNG: không có piping system {}. Các system: {}".format(u", ".join(bad), u", ".join(sorted(systems)))]
    wye, tee = junctions(ptype)
    if wye is None or tee is None:
        return lines + [u"DỪNG: pipe type '{}' thiếu Y / tê trong rule Junctions.".format(pipe_type_name)]
    lines.append(u"Level '{}' ({:+.0f}); pipe type '{}', Y '{}', tê '{}'".format(
        get_name(level), ft2mm(level.Elevation), pipe_type_name, wye.FamilyName, tee.FamilyName))
    old = previous_run()
    if old and not replace:
        return lines + [u"DỪNG: mô hình đã có {} phần tử '{}' của lần chạy trước. Đặt IN[10] = True để xoá và dựng lại, "
                        u"hoặc tự xoá (lọc Comments) rồi chạy lại.".format(len(old), COMMENT)]
    if old:
        lines.append(u"Thay lần chạy trước: xoá {} phần tử (ống / phụ kiện / phễu)".format(len(old)))
    if dry_run:
        return lines + [u"Dry-run: đổi IN[9] = False để dựng."]

    TransactionManager.Instance.ForceCloseTransaction()
    t = Transaction(doc, TRANSACTION_NAME)
    handler = CommitFailures()
    opts = t.GetFailureHandlingOptions()
    opts.SetFailuresPreprocessor(handler)
    opts.SetClearAfterRollback(True)
    t.SetFailureHandlingOptions(opts)
    t.Start()
    try:
        if old:
            ids = List[ElementId]()
            for i in old:
                ids.Add(i)
            doc.Delete(ids)
            doc.Regenerate()
        b, fail = build(routes, stacks, level, ptype, systems, {"wye": wye, "tee": tee}, lines)
        lines.append(apply_colors(b.made))
        status = t.Commit()
    except Exception as ex:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
        import traceback
        return lines + [u"LỖI, mọi thay đổi đã được hoàn tác: {}".format(ex), traceback.format_exc()]
    if status != TransactionStatus.Committed:
        return lines + [u"LỖI: Revit không commit được ({}), đã hoàn tác.".format(status)] + \
            [u"  [{}] {} ×{}".format(s, x, n) for (s, x), n in handler.all.most_common()]
    cnt = collections.Counter(e.Category.Name for e, s in b.made if e is not None and e.IsValidObject)
    lines.append(u"Đã tạo: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(cnt.items())))
    lines.append(u"Không đặt được (nối tay): " + (u"; ".join(fail) if fail else u"0"))
    if handler.resolved:
        lines.append(u"Revit tự xử lý lúc commit (kiểm tra lại): " + u"; ".join(u"{} ×{}".format(k, v) for k, v in handler.resolved.items()))
    lines.append(u"Undo: mục '{}'".format(TRANSACTION_NAME))
    return lines


if DYNAMO:
    try:
        OUT = main()
    except Exception as ex:
        import traceback
        OUT = [u"LỖI: {}".format(ex), traceback.format_exc()]
else:
    print(u"\n".join(main()))
