---
name: chi-tiet-cua-revit
description: 'Chi tiết cửa Revit – Chọn 1 cửa đi / cửa sổ (family có sẵn) trên Revit, tự tạo MẶT BẰNG (callout), MẶT ĐỨNG (nhìn từ ngoài nhà; cửa trong nhà nhìn từ phía không mở cánh), MẶT CẮT (cắt qua cánh, ngoài nhà bên phải) tỉ lệ 1/25 kèm kích thước tổng, đặt vào ô trống tiếp theo của sheet "CHI TIẾT CỬA" (khung A1 chia 6 ô 2 × 3, dải thông tin dưới mỗi ô: công cụ điền ký hiệu + kích thước, vật liệu / ghi chú để người dùng điền; hết ô thì tạo sheet mới, số sheet tăng tiếp; cửa có Fire Rating, cửa thang máy, louver không làm; thứ tự vách kính → cửa đi → cửa sổ; vách kính đặt bản vẽ riêng "CHI TIẾT VÁCH KÍNH <TẦNG>" mỗi tầng, xếp theo tầng + Mark). View template "CHI TIẾT CỬA - MẶT BẰNG / MẶT ĐỨNG / MẶT CẮT" tạo từ template 1/25 có sẵn. Mỗi type cửa chỉ làm 1 lần. Nút pyRevit Archivina > HS TKBVTC > Chi tiết cửa (một chạm) + graph Dynamo ChiTietCua_TuDong.dyn. Dùng khi người dùng nhờ "triển khai chi tiết cửa", "chi tiết cửa Revit", "mặt đứng / mặt cắt cửa 1/25", "sheet chi tiết cửa", hoặc sửa / thử nút Chi tiết cửa.'
---

# Chi tiết cửa Revit (Archivina)

Người dùng là kiến trúc sư, chọn 1 cửa trên Revit 2027 rồi bấm **Archivina → HS TKBVTC → Chi tiết cửa** (pyRevit). Mẫu cần
đạt: tờ A1 "CHI TIẾT CỬA" (ảnh người dùng gửi 2026-11-03, ký hiệu A.CD.22.13) gồm 6 ô, mỗi ô có mặt đứng, mặt cắt,
mặt bằng + bảng thông tin. Công cụ CHỈ dựng 3 view và chia ô; thông tin cửa người dùng tự điền.
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Quy tắc (người dùng chốt 2026-11-03)
1. **Đầu vào**: 1 hoặc NHIỀU cửa đi / cửa sổ, family có sẵn (người dùng chốt 2026-11-03 tối: chọn nhiều cửa trước rồi
   bấm nút). Các cửa đang chọn (bỏ qua đối tượng khác); chưa chọn thì chọn trên màn hình (PickObjects, Finish). Làm lần
   lượt, xếp tiếp các ô; cửa trong link không chọn được. Nút pyRevit hiện **bảng hỏi** trước khi chạy (`lib\
   arv_hoi_sheet.py` → `hoi_chi_tiet_cua`, dùng chung `_bang` với Tag cửa): dòng "Đã chọn N cửa", giai đoạn, hạng mục
   (gõ mới = thêm), khổ giấy A1 / A0 → khung tên, số hiệu, tên bản vẽ (mặc định `CHI TIẾT CỬA`); nhớ lần trước ở
   `%APPDATA%\pyRevit\ARVTools\ChiTietCua_sheet.json`. Số hiệu gợi ý = sheet chi tiết cửa của công cụ cùng tên + giai
   đoạn + hạng mục số lớn nhất còn ô trống; không có thì số tiếp theo trong hạng mục; trống = công cụ tự đánh số.
2. **3 view, tỉ lệ 1/25**, tên `CT CỬA <Type Mark> - MẶT BẰNG / MẶT ĐỨNG / MẶT CẮT` (Type Mark trống thì dùng tên type),
   Title on Sheet = `MẶT BẰNG` / `MẶT ĐỨNG` / `MẶT CẮT 1-1`. Khung nhìn = hình family + lề 300 mm; mặt đứng / mặt cắt lấy
   xuống tới sàn (cửa sổ thấy cả bậu).
   - **Mặt bằng**: callout trên mặt bằng tầng của cửa (ưu tiên view đang mở nếu đúng tầng, rồi view tên = tên level).
     Khung callout trên mặt bằng gốc ẩn bằng Hide in View; ký hiệu section trong mặt bằng chi tiết cũng ẩn (như mẫu).
     **Mặt bằng XOAY theo mặt đứng** (người dùng chốt 2026-11-03): phía phải mặt bằng = phía phải mặt đứng, ngoài nhà
     ở dưới (cửa trên tường phương Y / tường xiên cũng nằm ngang).
   - **Mặt đứng nhìn từ NGOÀI NHÀ**: một bên không có room → bên đó; cả hai bên có room → bên có tên lô gia / ban công /
     sân; không rõ → cửa có cung mở thì nhìn từ phía KHÔNG mở cánh; còn lại theo Facing của family (G19: Facing của cửa
     sổ / cửa lô gia hướng ra ngoài). Ô IN[11] ép `facing` / `nguoc`.
   - **Mặt cắt**: vuông góc tường, cắt qua cánh (cách tâm cửa 1/4 bề rộng), ngoài nhà bên phải.
   - **Mặt đứng CHỈ CÓ CỬA** (người dùng chốt 2026-11-03): tường, sàn, phần tử model khác Hide in View (giữ cửa +
     family lồng). Level ẩn trên mặt đứng + mặt cắt; mặt phẳng tham chiếu / scope box / lưới trục ẩn ở cả 3 view.
   - **Cốt sàn thay level** (như mẫu người dùng gửi): cao độ = mặt trên sàn trong nhà (không có thì ngoài nhà, cuối
     cùng level). **Nét đứt suốt bề rộng ô** vẽ trên SHEET (line style tên có "khuất" / "đứt", G19 `AV.Nét Khuất.W1`)
     qua cả mặt đứng + mặt cắt (đã gióng cùng cao độ); trong mỗi view có nét sàn kiểu `<Invisible lines>` chỉ để dim bám.
     Chữ đúng `CỐT SÀN HOÀN THIỆN` (KHÔNG thêm tên phòng; kiểu chữ mặc định, mũi tên chỉ xuống nét) bên trái mặt cắt,
     NGOÀI khung cắt (vùng annotation crop trái nới rộng) để không đè tường.
   - **Mặt bằng chỉ hiện cửa + tường** (người dùng chốt 2026-11-03 tối): sàn, cửa khác, đồ đạc Hide in View; khung nhìn
     trùm HẾT hình mặt bằng của cửa (cả cung mở cánh, lấy hình theo view gốc), lề 150.
   - Ký hiệu / khung callout của mọi view `CT CỬA ...` ẩn trong nhau, kể cả view đã làm trước (khung callout cửa làm sau
     hiện trên mặt bằng chi tiết cửa làm trước nếu 2 cửa gần nhau).
   - **Kiểu view riêng** (Project Browser có mục riêng): Floor Plan `CT CỬA`, Section `MẶT CẮT CỬA` (cả mặt đứng + mặt
     cắt); chưa có thì chép từ kiểu của mặt bằng gốc / kiểu Section. **Viewport** kiểu `AV-Title No Line` (không có
     thì giữ mặc định và báo).
3. **Kích thước tổng**: mặt bằng = rộng; mặt đứng = rộng (DƯỚI CHÂN, dưới đuôi ký hiệu mặt cắt 5 mm giấy – người dùng
   chốt 2026-11-04) + cao (bên phải); mặt cắt = cao. Cửa sổ: chuỗi sàn →
   bậu → đỉnh. Reference: family (Left / Right / Top / Bottom) → không có thì mặt lỗ mở của tường (mép, đỉnh, bậu);
   trên MẶT ĐỨNG (tường đã ẩn) lấy mặt trong hình cửa gần mép / đỉnh / bậu lỗ tường nhất (≤ 60 mm); chân = nét cốt sàn
   của từng view.
4. **View template**: `CHI TIẾT CỬA - MẶT BẰNG`, `- MẶT ĐỨNG`, `- MẶT CẮT`. Đã có thì dùng nguyên, KHÔNG sửa. Chưa có thì
   tạo từ template nền theo từ khoá IN[9] (G19: `3.1 Chi Tiết Mặt Bằng`, `3.2 Chi Tiết Mặt Đứng`, `3.3 Mặt Cắt Chi
   tiết`), không có thì template cùng tỉ lệ 1/25; đặt 1/25, Fine, ẩn nội thất + thiết bị vệ sinh + lưới trục; Far Clipping
   và crop để view tự giữ.
5. **Sheet "CHI TIẾT CỬA"**: khung `AV-Khung A1(841x594)-Kien Truc`, vùng vẽ (trong viền, trái dải khung tên) chia 6 ô
   2 hàng × 3 cột bằng Detail Line, mỗi ô có dải 22 % chiều cao phía dưới để điền thông tin. Trong ô: mặt đứng trên trái,
   mặt cắt bên phải (gióng sàn), mặt bằng dưới mặt đứng (gióng tâm cửa).
   - CHỈ đặt view vào sheet do công cụ tạo (có group lưới `ARV_ChiTietCua_Luoi <số sheet>`). Sheet người dùng tự làm dù
     trùng tên (G19: `A.7-101 CHI TIẾT CỬA`) không đụng tới.
   - Giai đoạn / hạng mục (IN[16] / IN[17]) chọn thì chỉ dùng sheet cùng giai đoạn + hạng mục, sheet mới được gán 2 giá
     trị đó (tham số theo cấp nhóm Project Browser, cách tìm như Tag cửa: `cap_thu_muc_sheet` / `ts_giai_doan`).
   - Số hiệu IN[3] có: xếp vào sheet đó (của công cụ, còn ô) rồi các sheet cùng tiền tố số lớn hơn; hết ô thì tạo sheet
     số đó / số tiếp theo chưa dùng. IN[3] trống: số lớn nhất của các sheet tên đó + 1 (G19: A.7-101 → A.7-102), chưa có
     thì `A.CD.01`.
6. **Mỗi type làm 1 lần**: đã có view `CT CỬA <mark> - ...` thì báo sheet chứa nó, không tạo thêm (chọn 2 cửa cùng type
   thì cửa sau báo đã có).
7. Không xoá, không sửa cửa / tường / view gốc / template đã có. Nút pyRevit gom cả lượt nhiều cửa trong 1
   TransactionGroup → Ctrl+Z một lần là hoàn tác hết; lỗi giữa chừng thì hoàn tác toàn bộ lượt.
8. **Ẩn level ở mặt đứng + mặt cắt**: tắt hạng mục Levels của view (bắt cả level file link; template mới cũng ẩn
   Levels) + Hide in View từng level của dự án.
9. **Vết cắt = ký hiệu SECTION của Revit** (người dùng chốt 2026-11-04 "vết cắt thể hiện bằng section"; thay vạch +
   mũi tên + nét đứt vẽ tay của bản 2026-11-03): ký hiệu của mặt cắt KHÔNG ẩn trên mặt đứng. Khung mặt cắt sát chiều cao
   (min(chân cửa, cốt sàn) → đỉnh ± 3 mm giấy) để đường cắt chỉ dài bằng cửa. Kiểu `MẶT CẮT CỬA` (của công cụ) phải dùng
   section tag có đầu: G19 "Wall Section" dùng tag Head / Tail = none (chỉ có đường) → đổi sang tag của kiểu mặt cắt
   "chi tiết" (`AV_Section Detail`: đầu `AV_Section Head` có số chi tiết / số sheet, đuôi `AV_Section Tail_Filled`).
   Tên mặt cắt = `MẶT CẮT n-n`, n = số chi tiết của viewport mặt cắt (khớp số ở đầu ký hiệu). Khung mặt đứng: trên = đầu
   ký hiệu (chừa 12 mm giấy), dưới = đuôi (Height của family đuôi + 1 mm) + dim ngang. **Bẫy**: hộp viewport của mặt đứng
   tính cả hộp bao ký hiệu section (G19 ±603 mm ở 1/25, rộng hơn phần in ra ~8 mm giấy mỗi đầu) → xếp ô theo PHẦN THẤY
   (khung crop + 3 mm, `hop_ht`), dời tên view lên sát phần thấy (`Viewport.LabelOffset`), ô bị lấn > 10 mm mới coi là có
   view. Lần thử 2026-11-03 (ký hiệu section làm vượt ô) là do tính theo hộp viewport.
10. **Vách kính (curtain wall)** (người dùng yêu cầu 2026-11-03 tối: "áp dụng cho cả vách kính"): chọn vách, hoặc tấm
    kính / đố / cửa đi, cửa sổ làm tấm của vách (→ lấy vách chứa nó, trùng thì gộp). Cùng 3 view + sheet + bảng hỏi.
    - Tên `CT VÁCH KÍNH <Mark của vách> - ...` (type vách dùng chung nhiều vách → nhận theo Mark; trống thì
      `VK <dài>x<cao>`); mỗi Mark làm 1 lần. Vách cong: báo, không làm.
    - Khung: trục tường (H = phương đường định vị), ngoài nhà theo luật room như cửa, không rõ → phía không mở cánh của
      cửa trong vách → `Wall.Orientation`.
    - Mặt đứng giữ vách + mọi tấm + đố + lưới (ẩn phần tử khác). Mặt cắt qua giữa ô cửa sổ, không có thì ô cửa đi (lệch
      1/4), rồi ô kính gần giữa vách; nhìn sâu nửa ô + 150 mm.
    - Dim: mép = mặt ngoài đố biên (không có đố thì mặt tấm). Mặt đứng: chuỗi theo lưới đứng + tổng DƯỚI CHÂN (dưới
      đuôi ký hiệu mặt cắt 5 / 12 mm giấy), chuỗi sàn → (chân vách nếu cao hơn sàn) → lưới ngang → đỉnh + tổng bên phải
      (cách 9 / 16 mm giấy). Mặt bằng (người dùng yêu cầu 2026-11-04): chuỗi khoảng cách đố (trục đố = lưới đứng) + tổng
      phía ngoài nhà, cách 6 / 13 mm giấy, bám nét ẩn tại mép + trục đố (reference mặt đố biên theo view mặt bằng không
      ổn định: VK.11 mất đoạn cuối).
      Mặt cắt: sàn → đỉnh. Reference mặt đố lấy theo hình CỦA CHÍNH VIEW (mặt bằng / mặt cắt cắt qua đố: reference hình
      3D làm Revit xoá dim); dim mất (lúc tạo hoặc sau khi ẩn phần tử) thì dựng lại vào nét `<Invisible lines>` tại mép.
    - **Tỉ lệ GIỮ 1:IN[4]** (người dùng chốt 2026-11-04: "để tỉ lệ 1/25 sắp xếp cho phù hợp"; bản lùi 1/50 → 1/100
      đã bỏ). Ước lượng cụm 3 view trước khi tạo (khớp cụm thật ± 1 %); không lọt 1 ô thì chiếm KHỐI ô liền nhau
      2 × 1 → 3 × 1 → 2 × 2 → 3 × 2 (cột × hàng, ít ô trước) trên SHEET MỚI: lưới bỏ nét chia trong khối, 1 dải thông
      tin dưới hàng cuối khối, ô còn lại dùng tiếp cho cửa / vách nhỏ. Vẫn không lọt 3 × 2 → báo "VƯỢT KHỔ" (chia
      đoạn / xếp tay). Lề dưới mặt đứng vách kính chỉ chứa nét cắt + số 1 (40 mm + 1,1 chữ + 2 mm giấy).
    - **Vách kính trong file link** (người dùng báo 2026-11-15 trên Site HQV, ảnh mẫu: "mặt đứng chi tiết cửa cho vách
      kính đang bị sai, muốn hiện đầy đủ cả vách kính"): template `CHI TIẾT CỬA - MẶT ĐỨNG (LINK)` ẩn cả hạng mục Walls,
      mà vách kính THUỘC Walls → đố + kính mất, chỉ còn cửa đi (tấm Doors). Nay mặt đứng vách link dùng template riêng
      `... - MẶT ĐỨNG (LINK VÁCH KÍNH)` (`HAU_TO_LINK_VK`, `AN_LINK_MD_VK` = danh sách cũ bỏ Walls) + view filter
      `ARV_Ẩn tường thường (link)` (Walls, `WALL_ATTR_WIDTH_PARAM` > 1 mm → tường thường ẩn, curtain wall không có
      Width nên còn). Template nền không lấy template tên đuôi `(LINK)` / `(LINK VÁCH KÍNH)` của loại khác. Bấm lại vách
      đã làm bằng bản cũ: view mặt đứng đang dùng template `(LINK)` được ĐỔI sang template mới (không xoá gì, không thêm
      dim). Chuỗi dim đố vách link: vị trí lưới lấy từ `CurtainGrid` của vách trong link (đổi toạ độ), bám nét
      `<Invisible lines>` trên mặt đứng (`net_md_dung` / `net_md_ngang`); bản cũ chỉ có dim tổng.
      Thử nền nút thật (`_tmp\ctcua_vk_link\`, nút thử `ARVTestVL`, `thu.py`, bản sao Site đã tách central): bước A nút
      cũ tái hiện lỗi (DVKT1-01 chỉ còn cửa, `kq_A\`); bước B nút mới: DVKT1-01 đổi template → đủ 6 ô + ô trên cửa,
      DVKT1-02 tạo mới 1011 | 978 | 978 | 1665 | 978 | 1011 = 6620, đứng 3012 | 968, sheet ACD.07.04 (`kq_B\`).
      Mặt đứng vách link còn vài nét xanh (đường bao / lưới của vách link) – chưa xử lý.
    - Ô trống (cả cửa): ô có nét dải thông tin RIÊNG trong group lưới và không viewport nào lấn vào > 2 mm (thay cách
      cũ theo tâm viewport, để ô nằm trong khối ghép không bị dùng lại).

11. **Trình bày sạch như mẫu + bỏ cửa chống cháy** (người dùng 2026-11-18, gửi mẫu A.CD.22.13 FPT P5 + A.19.36 CT1, khoanh
    ảnh G19 Side: mặt đứng / mặt cắt / mặt bằng còn thấy cửa, đồ vật bên cạnh; "trình bày vẫn còn xấu"):
    - **Cửa có Fire Rating** (tham số type `DOOR_FIRE_RATING` / "Fire Rating", rồi instance; vd. EI60, E30) KHÔNG triển
      khai chi tiết: `_chay` bỏ khỏi danh sách và báo "Bỏ qua N cửa có Fire Rating …" (`BO_FIRE_RATING = True`).
    - **Cửa thang máy** cũng KHÔNG triển khai (người dùng chốt 2026-11-18 "cửa thang máy k triển khai", sau khi thấy E32
      trên tờ thử): `cua_thang_may` – tên family / type, Type Comments, Description, Model (không dấu, bỏ ký tự ngăn)
      chứa `thang may` / `thangmay` / `elevator` / `loi thang` / `loithang`, trừ chuỗi có `thang bo`; báo "Bỏ qua N cửa thang
      máy …" (`BO_THANG_MAY = True`). G19 Side: E32, E33, 40 = `Pix_KC_R21_Dr_LoCua : Pix_KC_Cua_LoiThang_<rộng>x2300` (lỗ
      cửa thang máy trong link kết cấu). Không dùng "lift" (trùng cửa nâng trượt lift-slide). Cửa thang máy đặt tên khác
      hẳn (không có các chữ trên) thì vẫn bị làm → `Cần xác nhận lại` với dự án khác.
    - **Louver** cũng KHÔNG triển khai (người dùng chốt 2026-11-18 "louver thì k triển khai"): `cua_louver` – tên family /
      type, Type Comments, Description, Model có từ bắt đầu bằng `louver` / `louvre` hoặc đúng từ `lam` (tách từ theo ký tự
      ngăn và chữ thường → hoa: `LamThep` → lam thep; "Laminated" không tính), hoặc Mark / Type Mark tiền tố `LV` + số (quy
      ước nút Định vị lan can, louver); báo "Bỏ qua N louver …" (`BO_LOUVER = True`). G19 Side: `AV-Lam Thép Logia1` (Type
      Mark 42, lam thép lô gia) tính là louver (`Cần xác nhận lại`).
    - **Khung sát cửa**: mặt đứng ngang = hình cửa ± `LE_SAT_MM` 30 mm (chiều đứng giữ cách cũ: khung chỉnh theo ký hiệu
      mặt cắt – thử khung đứng sát cửa thì đường cắt trên mặt đứng dài vượt cửa ~750 mm, đầu ký hiệu lòi khỏi khung tờ),
      nhìn sâu tới mặt tường phía kia + 30; mặt cắt ngang = 2 mặt tường ± 30; mặt bằng = hình cửa (cả cung mở) ± 30, mỗi
      bên lỗ thấy `LE_MB_TUONG_MM` 80 mm tường. Phần tử link không Hide in View từng cái được nên khung sát là cách duy
      nhất bỏ cửa / đồ vật cạnh bên. Vách kính giữ lề IN[5] như cũ.
    - **Dim cách mép hình `DIM_CACH_MM` 6 mm giấy**, nằm NGOÀI khung model, trong vùng chú thích (annotation crop) nới
      riêng từng phía (phải mặt đứng / mặt cắt, dưới mặt bằng). Nới xong phải ẩn lại ký hiệu view (`an_viewer_thua`):
      lần ẩn đầu, ký hiệu mặt đứng còn ngoài vùng chú thích nên collector theo view không trả về → hiện số "4" thừa.
      `hop_ht` (phần thấy để xếp ô) = khung + offset chú thích từng phía.
    - **Kiểu dim** (`kieu_dim_ct`): ưu tiên kiểu CÓ SẴN thẳng, màu đen, đơn vị mm làm tròn 1 (hoặc theo đơn vị dự án là
      mm), chữ 1,8 – 2,6 mm gần 2,2, tên `AV_` (G19: `AV_Dim 2.2mm_0.6_H _`); không có thì chép kiểu mặc định thành
      `ARV_Dim Chi tiết cửa` (mm, đen). G19 Side trước sửa: kiểu mặc định `AV_Dim 2.0mm_Cut dim 2mm PC` đơn vị m, màu đỏ
      → dim ghi "1.35 m" đỏ.
    - Vết cắt trên mặt đứng ghi đè nét đen (G19 hiện nét đứt xanh xuyên hình cửa).
    - **Dải thông tin điền ký hiệu + kích thước** (người dùng chọn 2026-11-18): `dai_thong_tin` kẻ bảng như mẫu – cột KÝ
      HIỆU (Type Mark / Mark vách, chữ ~5 mm) | KÍCH THƯỚC (mm) (rộng x cao theo tham số Width / Height của cửa, vách =
      dài x cao) | VẬT LIỆU (để trống), hàng dưới GHI CHÚ (để trống); chữ kiểu có sẵn gần 2,2 mm (Arial, đen, không đậm,
      rộng 1, `AV_`), group `ARV_ChiTietCua_TT <sheet> <ký hiệu>`. Kích thước ở dải theo tham số type có thể khác dim trên
      hình khi dim đo theo mép lỗ tường (G19 DW02: 900 x 2200 / dim 910 – 2265) → `Cần xác nhận lại` cách ghi.
    - Ô chật (cụm mặt đứng + mặt bằng + 2 chỗ tên view 14 mm + lề 5 mm > vùng đặt view; G19 Side DW05-G cửa 2220 mở cánh
      vào trong: cụm 215 – 220 / ô 218 mm, tên "MẶT BẰNG" + "TL - 1:25" (~13 mm) chạm dải thông tin – bớt khoảng chừa tên
      vẫn chạm): tên mặt bằng đặt BÊN PHẢI mặt bằng (`GetLabelOutline`, đáy tên ngang đáy phần thấy), dưới mặt bằng chừa
      3 mm, lề trên 3 mm (`ten_mb_phai`). Hộp viewport mặt đứng tính cả hộp bao ký hiệu mặt cắt (±1193 mm model) nên kiểm
      tra của agent báo "tràn trên 3 – 5 mm" dù ảnh không tràn – soát bằng ảnh.
    - Cửa không lọt 1 ô (G19 Side: rèm ngăn cháy 6,2 m tràn sang khung tên – nay bị bỏ vì có Fire Rating) chiếm khối ô
      như vách kính; cửa cao thử khối 1 cột × 2 hàng trước.
    - Thử nền 2026-11-18 (`_tmp\hs_agent\02_G19_Side\`, phiên 38 – 39, bản sao rvt\05): xem nhật ký dự án.
12. **Tách riêng chi tiết cửa và chi tiết vách kính** (người dùng 2026-11-18: "tách riêng chi tiết cửa và chi tiết vách
    kính, chi tiết vách kính sắp xếp theo thứ tự và theo tầng"):
    - Vách kính KHÔNG đặt chung bản vẽ với cửa: bản vẽ riêng tên IN[19] (mặc định `CHI TIẾT VÁCH KÍNH`) + tên tầng viết
      hoa → `CHI TIẾT VÁCH KÍNH TẦNG 1`, mỗi tầng bản vẽ riêng (tên đã kết thúc bằng tên tầng thì không thêm). Tầng =
      level của vách (vách trong link: level model chính cùng cao độ, `lk_level_host`).
    - Số hiệu IN[20]: có thì bắt đầu từ số đó (trùng thì tăng tiếp); trống = tầng đã có bản vẽ vách kính thì tiếp sau
      số lớn nhất của tầng đó, chưa có thì tiếp sau bản vẽ vách kính các tầng khác, chưa có nữa thì bắt đầu từ số hiệu
      chi tiết cửa IN[3] (vách kính xếp trước, cửa đi / cửa sổ đánh tiếp sau), không có IN[3] thì tiếp sau bản vẽ chi
      tiết cửa (cùng giai đoạn / hạng mục). Khung tên / giai đoạn / hạng mục IN[18] / IN[21] / IN[22], trống = như cửa.
    - Thứ tự làm trong 1 lần bấm (`khoa_thu_tu`, người dùng chốt 2026-11-18 "sắp xếp theo thứ tự vách kính, xong đến cửa
      đi, xong cửa sổ"): vách kính theo cao độ tầng rồi Mark so số tự nhiên (VK.2 trước VK.10) → cửa đi → cửa sổ (theo
      Type Mark). Cửa đi, cửa sổ chung bản vẽ CHI TIẾT CỬA. Báo cáo có dòng "Thứ tự: …". Nhiều lần bấm (vd. agent mỗi
      tầng 1 lần) thì số tờ vách kính tầng sau nằm sau tờ cửa của tầng trước → muốn đúng thứ tự cả bộ thì bấm 1 lần cho
      mọi tầng, hoặc cho vách kính dãy số hiệu riêng.
    - Vách kính 1 ô chỉ xếp tiếp vào bản vẽ vách kính CUỐI của tầng (không lấp ô trống tờ trước) → đọc theo thứ tự tờ /
      ô là đúng thứ tự Mark. Cửa vẫn lấp ô trống mọi tờ chi tiết cửa như cũ.
    - **Tờ vách kính XẾP LIỀN** (người dùng 2026-11-19 "XẾP CHẶT VÁCH KÍNH HƠN": G19 Side 13 vách mỗi vách 1 tờ vì khối
      2 × 2 không lọt cột còn lại; `XEP_LIEN_VK = True`, False = khối ô lưới như cũ): tờ vách kính KHÔNG kẻ sẵn lưới 6 ô.
      Mỗi vách = 1 khối rộng đúng 1 ô nếu cụm lọt 1 ô, to hơn thì rộng cụm + 8 mm lề mỗi bên (`LE_KHOI_VK_MM`), cao 1 hoặc
      2 hàng (cùng ngưỡng cũ). `cho_khoi_vk`: khối 2 hàng đặt sau mép phải xa nhất của 2 hàng; khối 1 hàng vào hàng trên
      còn chỗ, không thì hàng dưới; sau khối 2 hàng cuối, hàng dưới đã có khối thì hàng trên khoá (giữ thứ tự đọc trái →
      phải, trên → dưới); vẫn chỉ xếp tiếp vào tờ vách kính cuối của tầng, hết chỗ thì tờ mới. `net_khoi_vk`: mỗi khối kẻ
      nét chia trái (khi chưa có) / phải, nét chia hàng (khối 1 hàng, đoạn chưa có), nét trên dải thông tin, gom group
      `ARV_ChiTietCua_LuoiVK <số tờ> <Mark>`; `khoi_vk_tren_sheet` dò lại khối từ chính các nét đó (nét dải thông tin =
      mép trái / phải + hàng đáy; khối hàng dưới là 1 hàng khi có nét chia hàng hoặc phía trên đã có khối 1 hàng). Tờ vách
      kính cuối kẻ lưới 6 ô kiểu cũ thì báo và sang tờ mới. Báo cáo: "khối n (rộng … mm × h hàng, xếp liền)".
      Thử nền nút thật bản sao file mẫu vách kính (`_tmp\ctcua_tach_vk\`, lượt 08 + ảnh 09, 2 lần bấm): 7 vách → 4 tờ (bản
      cũ 6 tờ), lần 2 xếp tiếp T1-VK.05, .10 vào A.CD.01 cạnh T1-VK.02, T1-VK.11 (525 mm) sang tờ mới; T2-VK.01, .03 cùng
      hàng trên A.CD.02. Giả lập ngoài Revit (`thu_xep_lien.py` trong scratchpad phiên) 4 kịch bản dò lại khối 0 lỗi;
      G19 Side 13 vách ước 9 tờ.
    - Hộp thoại (`arv_hoi_sheet.hoi_chi_tiet_cua`): có chọn vách kính thì hiện thêm bảng "Chi tiết vách kính – đặt lên
      bản vẽ" (nhớ riêng `ChiTietVachKinh_sheet.json`, lần đầu chép giai đoạn / hạng mục của bảng cửa; số hiệu để trống
      = tự đánh); chỉ chọn vách kính thì chỉ hiện bảng vách kính. Agent: khoá `so_vk` / `ten_vk` trong mục ChiTietCua của
      phương án (`chay_hs.py`).
    - Bản vẽ cũ đã có vách kính đặt chung tờ cửa (trước 2026-11-18) giữ nguyên, không dời / xoá.

## File
- Lõi: `<gốc>\scripts\dynamo\ChiTietCua_TuDong.py` (graph `.dyn` sinh bằng `build_dyn.py ChiTietCua_TuDong.json`).
- Nút: sinh bằng `scripts\pyrevit\build_from_dynamo.py "file mau revit\dynamo" --chi ChiTietCua` (MOT_CHAM
  `khong_view`: không cần view, lõi tự lấy cửa; `hoi` = `arv_hoi_sheet.hoi_chi_tiet_cua`, gọi `(doc, view, uidoc)`);
  không sửa tay `ChiTietCua.pushbutton\`. Shift+bấm = hộp thoại đầy đủ, Dry-run (Dry-run nhiều cửa báo cùng ô vì
  không tạo sheet thật).
- `arv_hoi_sheet.py` dùng chung với nút Tag cửa (`hoi(doc, view)` → IN[21] – IN[27] của TagCua): sửa `_bang` thì thử
  cả 2 nút.

## Bẫy đã gặp (Revit 2027.3)
- **Nét `<Invisible lines>`** (soi 2026-11-19 trên bản sao file mẫu vách kính): `Category.GetCategory(doc,
  BuiltInCategory.OST_InvisibleLines)` trả **None** (kiểu nét không nằm trong SubCategories của Lines) → mọi chỗ trong lõi
  lấy kiểu nét ẩn theo cách này (nét sàn trong view, nét bám dim `net_an` / `na`) thực ra đang là nét mặc định
  `<Thin Lines>` / nét đứt dự phòng. Tìm được bằng `FilteredElementCollector(doc).OfClass(GraphicsStyle)` có
  `GraphicsStyleCategory.Id == OST_InvisibleLines` (id 201) và gán được, NHƯNG nét đó vẫn in ra khi xuất ảnh tờ → không
  dùng nét ẩn làm dấu trên sheet. Các chỗ dùng cũ chưa sửa (`Cần xác nhận lại` có hiện thừa nét trên view không).
- **Link lồng chưa được dựng hình trong view vừa tạo** (người dùng báo 2026-11-18, G19 Side cửa sổ 37 trong link
  `G19_A_L3.rvt : G19_A_L3-32.AP1.rvt`): mặt đứng chỉ còn khung chữ nhật, mặt bằng trống, mặt cắt vẫn đủ; ảnh xuất ngay
  khi mở lại file vẫn vậy. Không phải do family (4 khối hình hiện mọi hướng / mức chi tiết, không family con dùng chung),
  không phải View Range (cắt 1200, cửa sổ 450 – 2800). Thử phiên 46 – 48: đổi Detail Level template qua Medium rồi trả Fine
  → mặt đứng hiện đủ; gán lại View Range cùng giá trị → mặt bằng vẫn trống; bỏ template → Regenerate → gán lại → cả 3
  view hiện đủ. Lõi: cửa / vách trong link, sau khi dựng xong 3 view thì gán lại template như vậy (`lk`), báo
  "Dựng lại hình link …", kiểm số kích thước không đổi.
- `ViewSection.CreateSection`: view NHÌN THEO +BasisZ (ViewDirection = -BasisZ), mặt cắt ở Min.Z, cắt xa ở Max.Z,
  RightDirection = -BasisX. Bản đầu tưởng ngược lại nên mặt đứng nhìn từ trong nhà. Lõi kiểm lại ViewDirection /
  RightDirection sau khi tạo và báo CẢNH BÁO nếu lệch.
- Khung tên trên sheet: `get_Geometry` trả None (cả có / không View) → đọc nét trong family bằng `EditFamily` (ngoài
  transaction, đóng không lưu); nét viền có thể chia đoạn → cộng dồn chiều dài theo toạ độ.
- PythonNet3 không đọc được `Element.Name` của ElementType → đọc `SYMBOL_NAME_PARAM` / `ALL_MODEL_TYPE_NAME`.
- Family `D1_WO_OP1` (G19) không có reference Left / Right / Top → dim theo mặt lỗ tường.
- Bật Annotation Crop (lề 3 mm) cho 3 view, không thì ký hiệu section / đầu level ngoài khung làm viewport to ra, xếp
  sai ô. Offset annotation crop tính trên GIẤY (feet giấy), không phải model.
- Xoay mặt bằng = `ElementTransformUtils.RotateElement` phần tử crop của callout quanh trục Z tại tâm cửa, góc
  atan2(X_d) → RightDirection = X_d. Phần tử crop của callout mặt bằng: id = id view - 1, hạng mục **"Views"** (KHÔNG
  phải `OST_CropBoundary`); tìm bằng rule `ID_PARAM` = id view (bỏ chính view).
- Dim tham chiếu phần tử bị Hide in View thì MẤT khi regenerate → mặt đứng dim vào hình cửa (reference symbol đổi sang
  instance bằng chuỗi `<UniqueId>:0:INSTANCE:<ConvertToStableRepresentation>`) và vào nét cốt sàn.
- Detail Line thuộc hạng mục Lines = `CategoryType.Model` → khi ẩn "mọi phần tử model" phải bỏ qua `ViewSpecific`, không
  thì ẩn luôn nét cốt sàn và dim theo nó mất.
- Detail line bị model crop cắt (không hiện trong vùng annotation crop) → nét cốt sàn hiện vẽ trên sheet.
- `FilteredElementCollector(doc, view.Id)` KHÔNG trả Level → ẩn level bằng `OfClass(Level)` toàn dự án +
  `CanBeHidden` / `IsHidden`.
- Khung callout mặt bằng hiện trong view khác là phần tử crop hạng mục "Views" (không phải OST_Viewers).
- Graph `.dyn` ở thư mục mới: Dynamo có thể báo "Run blocked" (không hiện hộp thoại tin cậy) → chạy thử từ thư mục đã
  dùng (`_tmp\revit_ctcua\thu3\`).

## Cách thử
- Dynamo: `_tmp\revit_ctcua\thu2\chay_thu.py` (dry-run, 7 cửa → sang sheet thứ 2, bấm lại không trùng; xuất PNG, lưu
  bản sao), chạy bằng `_tmp\revit_g19\chay_dynamo_ui.ps1`.
- Nút pyRevit: `_tmp\pyrevit_ctcua\ARVTestCT.extension` (chọn sẵn cửa rồi exec `script.py` của nút); thêm vào Extension
  Search Path khi thử, xong `pyrevit extensions paths forget`.
- Kết quả 2026-11-03 trên bản sao G19: 7 cửa (trượt 2 cánh DG26, cửa đi 1 cánh DG16 / 17 / 20 / 21, cửa sổ 32 / 36),
  2 sheet A.7-102 / A.7-103, đủ dim. Bản 2 (xoay mặt bằng, mặt đứng chỉ cửa, cốt sàn): mặt bằng xoay 0 / 180 / -90°,
  mọi dim còn sau khi ẩn, 7 cụm đều nằm trong ô; ảnh `_tmp\revit_ctcua\thu3\`; nút thật (DG26, DG21, bấm lại)
  `_tmp\pyrevit_ctcua\kq\` (bản 1 ở `thu2\`, `kq_v1\`).

- Vách kính 2026-11-03 trên bản sao `file mau revit\file vach kinh.rvt` (`_tmp\revit_ctcua\thu3\VK.rvt`, `chay_vk.py`):
  Bản 1/25 + section + dim chân (2026-11-04): T1-VK.11 9080×5000 có cửa đi + kính góc → khối 3 × 2 (cụm 508 × 345); T2-VK.05 11015×2800 có 2 cửa sổ → khối 3 × 2 (584 × 224; trước khi có ký hiệu section + dim chân vừa 1 hàng 216 / 218); 7 cửa G19 vẫn vừa ô (DG21 218 / 218);
  T1-VK.12 dài 54,5 m → vượt khổ (báo); chọn tấm + đố + vách cùng vách → gộp 1; bấm lại không trùng. Ảnh
  `_tmp\revit_ctcua\thu3\anhvk\`.

## Còn mở (`Cần xác nhận lại`)
- Vách kính 1/25 chiếm khối ô: người dùng chưa xem bố cục; vách rất dài (> ~13 m) vượt khổ A1, chưa có cách chia đoạn.
- Người dùng chưa bấm thử trong Revit của mình, chưa duyệt bố cục ô / template.
- Ẩn level chưa kiểm được trên G19 (template 3.2 / 3.3 đã ẩn level); model thật của người dùng có hiện level.
- Nét cốt sàn trên sheet đứng yên: dời viewport bằng tay thì phải dời nét theo.
- Chưa thử trên model thật `G19_A_L3-32` (có room → luật ngoài nhà theo room chưa được kiểm).
