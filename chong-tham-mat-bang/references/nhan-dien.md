# Quy tắc nhận diện và thể hiện chống thấm (Archivina)

Nguồn: bản vẽ tay căn CH15 trong `D:\AI\file mau\254HQV-Thap B-Mat bang tang 4 ch15.dwg` (so với bản gốc `...tang 4 .dwg`), bảng ghi chú ký hiệu trong cùng file, và các quyết định người dùng chốt ngày 22/10/2026.

## Mục lục
1. Thể hiện (layer, hatch, nét vén)
2. Nhận phòng ướt
3. Đường bo
4. Đảo (hộp kỹ thuật, cột)
5. Nét vén chân tường và cửa
6. Chỗ chưa tự động được
7. Số liệu kiểm chứng

## 1. Thể hiện
| Thành phần | Đối tượng | Layer | Màu | Thông số |
|---|---|---|---|---|
| Đường bo | LWPOLYLINE kín | `A-Material` | 3 | mặt lõi tường / mặt trong lan can |
| Đảo | LWPOLYLINE kín | `A-Material` | 3 | lòng hộp kỹ thuật, cột trong phòng |
| Hatch | HATCH liên kết đường bo + đảo | `A-Material` | 3 | User-defined (`_U`), góc 45°, khoảng cách 400, **double** (lưới chéo) |
| Nét vén chân tường | LWPOLYLINE hở | `A-Material` | 1 | global width 40, nét liền, cách bo 50 vào trong |
| Block | INSERT tại 0,0 | `A-Material` | | tên `CHONG THAM` (trùng thì `CHONG THAM 2`…) |

- Mọi loại phòng (WC, lô gia, ban công, phòng kỹ thuật nước, phòng rác) dùng **chung một kiểu hatch** (chốt 22/10/2026).
- Bản mẫu vẽ nét vén trên layer `xr bang thong ke$0$!00 mach co gian` (đỏ theo layer); người dùng chốt chuyển sang `A-Material`, màu 1 gán riêng.
- Bản mẫu dùng một HATCH chung cho cả căn; skill vẽ **mỗi phòng một HATCH** để sửa từng phòng dễ hơn (thể hiện giống hệt).
- Bảng ghi chú ký hiệu và "Lưu ý" (vén cao 300, lưới thủy tinh, chi tiết A.17,01, A-1601) **người dùng tự đặt**, skill không vẽ.
- File mẫu: layer `A-Material` màu 251, Continuous. Thành phần tường ACA sau khi nổ cũng nằm trên `A-Material` (lớp lõi + trát) → không dùng layer này để nhận "đã có"; chỉ HATCH `_USER` ở Model hoặc block `CHONG THAM*`.

## 2. Nhận phòng ướt
Mặt bằng tầng là các block căn `CHxx (T4)` chèn tại 0,0; tường / cửa trong block là **đối tượng AEC** → luôn nổ AEC trên bản sao trước (`dwg_to_dxf_aec.ps1`). Một số căn có tường ACA đã nổ sẵn nhưng nằm trên **layer 0** (block ẩn danh `*U..` chỉ gồm LINE + HATCH, cạnh ngắn ≤ 450): script nhận theo cấu trúc này (tầng 4 Tháp B: 5.700 nét).

| Loại | Hạt giống | Ghi chú |
|---|---|---|
| WC | block trên layer `A-Interior WC`; tên khớp xí (`马桶`), sen, lavabo (`台盆`), bồn tắm, tiểu | bỏ ống đứng `piped*` (vd. `piped125-xi` không phải xí) và block trục tăng áp `TA1` (CT1 đặt trên `A-Interior WC`) |
| Lô gia / ban công | máy giặt, cục nóng điều hoà (`May giat`, `VRF`…) | |
| Lô gia / ban công không thiết bị | ô kín 1–12 m², rộng ≥ 800, **giáp ngoài nhà**, có **cửa trượt** (cửa đi không cung quay) hoặc **lan can** sát biên, **không có nội thất** (giường, tủ, sofa trên `A-Interior*`) | lô gia dài CH15 nhận theo cửa trượt; phòng ngủ có cửa sổ trượt bị loại nhờ điều kiện nội thất |
| Phòng rác, phòng KT nước | **ký hiệu so nguyên văn**: `R` = phòng rác, `N` hoặc `KTN` = phòng KT nước (`KTN` dùng ở CT1, bổ sung 23/10/2026) (chốt 22/10/2026; tầng 4 Tháp B nằm trên layer `Defpoints`), đổi bằng `--ky-hieu`; hoặc text tên phòng (so không dấu): `phong rac`, `ky thuat nuoc`, `phong bom`… | ô chứa ký hiệu / tên **phải có cửa đi**, không có thì là hộp kỹ thuật → bỏ, ghi vào "Chỗ cần xem". Bỏ text bắt đầu bằng `Trục`, `Hộp`, `Ống`. Các ký hiệu trục `BK`, `TA`, `HM` không dùng |
| Buồng đệm phòng rác | ô 1–10 m² nối với phòng rác bằng **cửa đi nằm trong tường chung** (khung cửa chạm biên cả hai ô ≤ 150) và có **thêm ≥ 1 cửa đi** (ra hành lang); nhiều ô đạt thì lấy ô nhỏ nhất | thang máy rác nối với phòng rác bằng tường mảnh / ô mở, không cửa → không nhận. Phòng đệm thang bộ "Đ" sát phòng rác bị loại vì cửa phòng rác không nằm trong tường chung |

Nhiều hạt cùng một ô: ưu tiên phòng rác > buồng đệm > phòng KT nước > WC > lô gia. Mã căn lấy từ tên block `CHxx (T4)$0$...` (thiết bị hoặc nội thất gần nhất ≤ 3 m); phòng rác, buồng đệm, phòng KT nước ghi "Khu chung".

**Thiết bị không rơi vào ô kín nào** (lô gia giặt có mặt ngoài chỉ là lan can ngắn + nét LINE / polyline layer `0`, `A-line*` ở cấp Model): dựng lại lưới nét bán kính 6 m quanh thiết bị, **thêm các nét mặt ngoài đó** (dài ≥ 300), lấy ô nhỏ nhất 1–20 m² chứa thiết bị; ghi nguồn "khép bằng nét mặt ngoài". Tầng 4 Tháp B: 7/7 lô gia giặt khép được (vd. lô gia CH27 ~ 39725, −51544).

## 3. Đường bo
- Ô kín = polygonize lưới nét tường (`A-Wall`, `A-Material`, `A-Column`, `A-Line`, `S-Wall`, `A-Lancan`, `A_Wall BT`, `A-Vua trat`) + tường đã nổ ở layer 0 + khung bao block lan can mỏng (≤ 200) + khung cửa (hàm của `dien-tich-ch`), đóng ô mở ≤ 1.200.
- **Mặt lõi tường, không tính trát**: cạnh nào có nét song song cách 8–22 mm phía tường (phủ ≥ 40% cạnh) thì đẩy ra nét đó. Mẫu: lõi x=150, trát x=165 → bo ở 150. Không lùi ốp WC (khác skill diện tích).
- **Lô gia / ban công dừng ở mặt trong lan can / tường lửng** (chốt 22/10/2026). Bản mẫu CH15 phủ qua tường lửng 150 của lô gia dài — không theo.
- Đầu nét tường hở hụt ≤ 40 mm so với tường vuông góc (tường lửng lô gia giặt CH15 hụt 15 mm) được nối dài cho khép.

## 4. Đảo
- Nét trên layer trục / hộp kỹ thuật (`A- Truc ME`, `*HKT*`, `A-MEP`, `A-Column`, `S-Wall`) → polygonize. Ô có lỗ lớn (vỏ hộp) bỏ, lấy **lòng hộp**; tam giác dấu X gộp lại; ô hẹp < 100 mm (vỏ hộp 80) bỏ — **vỏ hộp vẫn hatch** như mẫu.
- Đảo nằm trong phòng, **không chạm biên** → lỗ trong hatch, nét vén **không** đi vòng quanh (mẫu: hộp chữ L trong lô gia giặt CH15).
- Đảo **chạm biên** (cột sát tường) → khấc vào đường bo, nét vén đi theo; dải vụn < 60 mm còn lại giữa cột và tường bị bỏ (mẫu: cột góc lô gia dài CH15).
- Sửa 23/10/2026 (người dùng báo lỗi trục trên CT2):
  - Khe giữa đảo và biên **nhỏ hơn khoảng lùi nét vén (50)** cũng tính là chạm biên (CT2: hộp trục cách bo 25 mm, nét vén từng cắt ngang hộp).
  - Bỏ nét **ống / cùm ống** (layer có chữ `ong`, `cum ong`, `pipe`, vd. `AV-ME-Ống trục đứng`) khi dựng hộp: vòng tròn ống cắt hộp thành mảnh vụn → mất cả hộp.
  - Dự phòng: polyline kín 0,02–6 m² trên layer trục / `A-MEP` mà polygonize bỏ sót thì lấy nguyên làm đảo.
- Ô hẹp < 500 mm hoặc < 0,5 m² (khe tường, dải mép sàn) không phải phòng, kể cả khi có thiết bị → "chỗ cần xem" (CT2: cục nóng rơi vào dải 1400 × 150).

## 5. Nét vén chân tường và cửa
- Offset đường bo vào trong 50 (`--cach-ven`), góc vuông (mitre).
- **Ngắt tại cửa đi**: cửa (INSERT trên layer cửa) có cung quay, hoặc chỉ gồm polyline (cửa trượt); dải cắt rộng đúng bề rộng ô cửa đo dọc theo cạnh phòng gần cửa nhất. Mẫu: WC1 CH15 hở y −4690…−3910 = khung cửa.
- Cửa sổ (có ≥ 3 LINE kính, không cung quay): nét vén **chạy liền** qua.
- Ô mở không vẽ cửa (đoạn đóng ≥ 300 mm trên biên, không trùng khung cửa sổ): cũng ngắt; ghi chú "ô mở không vẽ cửa" (vd. WC2 CH15).
- **Giếng thang máy lấn vào phòng ướt** (CT1 tầng 5A-10: giếng thang máy rác chỉ có viền + dấu X nét khuất `...Loi TDH$0$A-Hidden`, không có nét tường ngăn với phòng rác nên ô phòng rác nuốt cả giếng): giếng = polyline kín chữ nhật 0,8–12 m² có 2 đường chéo nối góc đối diện. Khoét giếng + dải ô cửa trong chiều dày tường (tăng độ khoét 10 mm/bước, dừng khi diện tích khoét tăng đột biến = chạm mặt tường phòng chính), ngắt nét vén đúng bề rộng ô cửa thang.
- Phòng rác / buồng đệm: phần biên giáp thẳng một ô kín khác rộng ≥ 500 (không có bề dày tường) là ô mở → ngắt. Không áp cho WC / lô gia (tầng 4 cắt nhầm 4 chỗ đáy phòng chỉ là 1 nét).
- **Cửa thang máy** (người dùng xác nhận 23/10/2026): polyline kín ở cấp Model trên layer `A-Wall`, cạnh ngắn ≤ 300, dài ≥ 600, không hatch, cách text tải trọng `…KG` ≤ 2,5 m, nằm sát biên phòng (≤ 50) → ngắt nét vén đúng bề rộng ô đó; ghi chú "cửa thang máy". Tầng 4 Tháp B: cửa thang máy rác 150 × 1000 giữa phòng rác và thang `300KG`, nét vén hở y −52480…−51480.
- Không có cửa nào: nét vén kín, ghi chú để người dùng xem.
- Sửa 23/10/2026 (người dùng báo nét vén chạy qua cửa trên CT2):
  - **Thứ tự nổ AEC**: cửa đi / cửa sổ / ô mở trước, tường sau cùng. Nổ tường trước thì cửa gắn trong tường bị xoá theo (CT2 CH.02: mất cả 10 cửa).
  - Cửa vẽ bằng **nét rời** trên layer cửa (không phải block) cũng nhận: gom các nét cách nhau ≤ 30 mm thành một cửa.
  - Cửa có cung quay: lấy **đường mở** (bản lề → mép cánh khi đóng, nằm trong tường); chỉ cắt nét vén ở cạnh phòng song song đường mở (lệch ≤ 20°), rộng đúng đường mở. Cánh cửa phòng bên vẽ ở tư thế mở nằm sát tường WC không cắt nhầm.
  - Vùng cắt chỉ rộng 120 mm tính từ cạnh phòng (trước là 400): bản lề sát góc không cắt lan sang nét vén cạnh vuông góc.

## 6. Chỗ chưa tự động được → sheet "Chỗ cần xem"
- Thiết bị / ký hiệu vẫn không khép được phòng sau bước dựng lại có nét mặt ngoài → không vẽ, liệt kê tọa độ để vẽ tay hoặc `--them`.
- Ký hiệu R / N nằm trong ô không có cửa đi.
- Ô mở không có khung cửa, chỉ có nét tường mảnh, mà không cạnh text tải trọng thang máy: vẫn coi là **tường**, nét vén chạy liền qua. Gặp thì hỏi người dùng.
- Phòng > 15 m² → `can_xem` (có thể gộp nhầm với phòng khác), không vẽ trừ khi chạy với `-TrangThai se_ve,can_xem`.

## 7. Số liệu kiểm chứng (22/10/2026)
- CH15 (tầng 4 Tháp B, so với bản vẽ tay): WC1 bo `150..2950 × −5350..−3800` trùng tuyệt đối, nét vén trùng (hở y −4690…−3910). WC2 bo trùng; nét vén hở −5250…−4450 (mẫu −5240…−4480, ô mở không có cửa). Lô gia giặt bo `150..1700 × −10980..−9150`, đảo chữ L trùng mẫu, nét vén hở −10160…−9260 (mẫu −10167…−9250). Lô gia dài: nét vén 1200,−6025 … 1200,−8225 trùng mẫu; bo dừng ở mặt trong tường lửng x=150 và dầm y=−8700 (mẫu 0 và −8750) theo chốt 1.
- Cả tầng 4 Tháp B lần 1 (22/10/2026): 47 WC + 24 lô gia; 7 chỗ cần xem (lô gia giặt không khép).
- Lần 2 (23/10/2026, sau khi người dùng báo thiếu lô gia CH27 và bổ sung R / N / buồng đệm): 47 WC + 31 lô gia + 1 phòng rác (2,13 m²) + 1 buồng đệm (1,31 m²) + 2 phòng KT nước (2,25 và 3,30 m²) = 82 vùng, 112 nét vén, 0 chỗ cần xem; `kiem_tra_block` LOI 0; dò lại 82/82 `da_co`. Bản v3 (23/10/2026): thêm ngắt nét vén ở cửa thang máy rác → 113 nét vén, LOI 0.
- CT1 tầng 5A-10 (23/10/2026, `file mau\03_ChongTham\CT1- MB TANG 5A-10_chong tham.dwg`): 46 WC + 31 lô gia + 2 phòng rác + 2 buồng đệm = 81 vùng, 139 nét vén, LOI 0, AEC 972 = 972, dò lại 81/81 `da_co`. Không có ký hiệu `N`. 4 vùng `can_xem` 46–76 m² (#80–83, căn CH16 / CH19 dãy dưới): máy giặt / cục nóng rơi vào ô gộp với phòng khách – bếp (khu giặt thông, không tách được) → không vẽ. 1 điểm `sen vuong` ở (361134, 52962) nằm ngoài mặt bằng. Kiểm tra hồi quy: chạy lại tầng 4 Tháp B với quy tắc mới → 0 vùng đổi. Dò ~80 giây sau khi nổ AEC (~3 phút).
