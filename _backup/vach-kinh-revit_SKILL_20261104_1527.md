---
name: vach-kinh-revit
description: 'Vách kính Revit – Dựng vách kính (curtain wall) trên mặt bằng Revit và chia đố 65 theo đúng quy tắc lệnh VK / MDVK của AutoCAD: mỗi ô kính < 1200 tâm - tâm chia đều, cửa sổ mở CuaSoVK_A_loai2 / cửa đi 2 cánh Door-Curtain-Wall-Double-Glass theo rộng tâm - tâm và chiều cao nhập trong bảng, vách góc vuông có đố góc 150 x 150 + kính góc như mẫu, đổi chiều dài / chiều cao vách thì tự chia lại. Nút pyRevit Archivina > Vách kính. Dùng khi người dùng nhờ "vẽ vách kính trên Revit", "curtain wall chia đố như VK", "vách kính góc vuông Revit", "chia lại đố vách kính Revit", hoặc sửa / thử nút Vách kính.'
---

# Vách kính Revit (Archivina)

Người dùng là kiến trúc sư, dùng nút **Archivina → Vách kính → Vách kính** (pyRevit, Revit 2027). Claude sửa công cụ và
tự thử trên BẢN SAO `.rvt`, không đụng model đang mở trong Revit của người dùng.

## Quy tắc (người dùng chốt 2026-11-01)
- Đố **65 x 150**: kiểu `ARV_Đố 65x150` (Rectangular Mullion, profile hệ thống, đặt GIỮA mặt kính, offset 0, vật liệu lấy
  theo `Đố nổi-65x150mm` nếu có). Không dùng `Đố nổi-65x150mm` vì profile của nó lệch 45,5 mm ra ngoài, không khớp đố góc.
- **L = mép ngoài - mép ngoài**. Đố biên curtain wall Revit nằm TRONG đầu vách (đã đo: chiếm 0..65) nên chiều dài vách =
  L, tâm đố biên cách mép ngoài 32,5 – đúng như VK.
- **Chia y hệt `vk:chia` / `Vk.Chia`**: S = L − đầu − 32,5 (đầu = 32,5; cánh vách góc = 75 = tâm đố góc); cửa chiếm
  đúng rộng tâm - tâm nhập trong bảng (mặc định cửa sổ 1000, cửa đi 1665); phần còn lại chia đều N ô, N nhỏ nhất để
  mỗi ô < 1200 (1200 đúng là không đạt), không làm tròn; cửa không tích ô thì rải đều (cửa đi trước, cửa sổ sau).
  Thử: 4210 + 1 cửa sổ → `1048,33 | 1048,33 | SO 1000 | 1048,33` (khớp VK).
- **Cao độ theo `vkmd:tinh`** (từ chân vách = sàn): cửa đi cao hd → đố ngang suốt vách, mặt dưới = hd; hd + 65 + 65 > cao
  vách thì bỏ đố ngang, cửa lên sát khung trên. Cửa sổ: mép dưới cánh = sàn hoàn thiện + bậu (50 + 1400 = 1450), đố
  dưới cửa sổ chỉ trong ô cửa sổ; có thanh ngang → đố ngang suốt vách ngay trên cửa sổ (cao cửa sổ nhập tay), không →
  cửa sổ lên sát khung trên; thanh ngang chạm khung trên thì báo lỗi như MDVK. Ô cửa đi không có khung dưới. Đố ngang
  không cắt qua ô cửa (bỏ đoạn đó bằng `RemoveSegment`). Vách có cả cửa đi lẫn cửa sổ (MDVK không có): đặt cả 2 đố
  ngang (`Cần xác nhận lại`).
- **Vách góc vuông** (như mẫu `file mau revit\file vach kinh.rvt`, T1-VK.11 / 12): pick 3 điểm đầu cánh 1 → góc NGOÀI →
  đầu cánh 2. Cánh 1 = kiểu `ARV_Vách kính 65 - cánh đố góc` (Border 1 dọc = `ARV_Đố góc 150x150`, chiếm 150 x 150 ở
  góc); cánh 2 = `ARV_Vách kính 65 - cánh kính góc` (không có đố biên ở góc), ô 1 là panel `Kinh_goc_6_trai`. Mặt kính
  2 cánh lùi 75 vào trong so với mép ngoài. Tích có hướng cánh 1 × cánh 2 âm thì lật vách cánh 2 để kính góc luôn ra
  phía ngoài góc. Hai cánh dùng chung đố ngang. Ô 1 cánh 2 không đặt được cửa (`Cần xác nhận lại`). Chỉ nhận góc 90°
  (pick lệch ≤ 1° thì tự vuông lại, hơn thì báo).
- **Bảng nhập** (WPF, bố cục bảng VK đã duyệt + xem trước mặt đứng như MDVK): tên vách (Mark; trống = tự đặt
  `T<số tầng>-VK.<nn>` tiếp số lớn nhất, trùng thì thêm ` (2)`), chiều dài (+ Pick 2 / 3 điểm), chiều cao vách, cửa sổ
  (số lượng, rộng, cao, có thanh ngang, sàn hoàn thiện, bậu), cửa đi (số lượng, rộng, cao), ô Vách góc vuông (Cánh 1 / 2),
  Lật cửa; bảng các ô bấm để tích / bỏ cửa. Sáng / tối nhớ trong bộ nhớ bảng.
- **Tự chia lại**: thông số vách lưu trong Extensible Storage (schema `6f1c2d9a-3b4e-4f5a-9c7d-8e2a1b0c4d53`, trường
  `DuLieu` JSON). `startup.py` đăng ký updater "ARV Vach kinh" (optional): kéo dài / đổi chiều cao vách → chia lại trong
  cùng lần sửa (giữ ô cửa nếu còn hợp, không thì tự đặt); cửa không vừa → trả vách về kích thước cũ. Nhật ký
  `%APPDATA%\pyRevit\ARVTools\VachKinh_updater.log`.
- Không dim, không tạo view mặt đứng, không làm lam nhôm (người dùng chốt).

## File
- Lõi: `<gốc>\scripts\pyrevit\ARVTools.extension\lib\arv_vach_kinh.py` (`chia`, `tinh_cao`, `dam_bao_kieu`, `tao_vach`,
  `dung_luoi`, `cap_nhat_vach`). Chạy cả IronPython 2.7 (pyRevit) và CPython 3 (Dynamo PythonNet3).
- Bảng: `lib\arv_vach_kinh_bang.py` + `lib\vach_kinh\BangVachKinh.xaml` + `ChuDe.xaml` (chép từ K-TOOL).
- Nút: `Archivina.tab\VachKinh.panel\VachKinh.pushbutton\script.py` (IronPython, viết tay, builder không đụng; panel
  có trong `PANEL_VIET_TAY` của `build_from_dynamo.py`). Updater: `ARVTools.extension\startup.py`.
- Family mang theo: `lib\vach_kinh\CuaSoVK_A_loai2.rfa`, `Door-Curtain-Wall-Double-Glass.rfa`, `Kinh_goc_6_trai.rfa` –
  mô hình chưa có thì tự nạp (`.rfa` không đẩy GitHub: chép thư mục sang máy khác). Thiếu kính góc thì ô góc dùng kính
  thường và báo.

## Bẫy curtain grid
- Thêm nhiều đoạn lưới ngang (`AddGridLine(..., oneSegmentOnly=True)`) ở CÙNG cao độ: Revit chỉ nhận đoạn đầu, không báo
  lỗi (người dùng gặp 2026-11-01: 6 cửa sổ chỉ 1 ô có đố dưới, các cửa sổ khác bị kéo từ khung dưới lên). Cách đúng:
  1 đường suốt vách rồi `RemoveSegment` các đoạn không cần (đố dưới cửa sổ, đố ngang qua cửa). Thử lại: 12 ô / 6 cửa
  sổ xen kẽ đủ 6 đố dưới (`_tmp\revit_vachkinh\pyrevit_thu\kq_thu5\`).
- Vách đã dựng bằng bản lỗi: sau khi pyRevit Reload, kéo dài vách rồi trả lại (updater dựng lại) hoặc xoá vẽ lại.

## Bẫy IronPython 2.7 trên Revit 2027 (.NET 10)
- `.Name` của ElementType báo lỗi → `_ten()` đọc thêm qua `DB.Element.Name.GetValue(e)`.
- KHÔNG lồng `try` trong `except`: lỗi biên dịch `InvalidCastException ... TypedParameterExpression`, Revit thoát.
- `ElementId.Value` là `long` → `int()` trước khi `json.dumps`.
- Không dùng `pyrevit.forms`; WPF thuần bằng `XamlReader.Parse`, sự kiện bằng `+=`.

## Thử (máy này)
- Bản sao: `_tmp\revit_vachkinh\thu\ban_sao_goc.rvt` (chép từ `file mau revit\file vach kinh.rvt`).
- Lõi qua Dynamo: `_tmp\revit_vachkinh\thu\chay.sh <tên>` (chép `<tên>.py` → `hien_tai.py`, graph `ThuExec.dyn` exec file
  đó; kết quả `kq_<tên>\`). Mẫu: `thu4.py`.
- Trong pyRevit (IronPython): đặt tạm `_tmp\revit_vachkinh\pyrevit_thu\da_go_khoi_search_path_ARVTestVK.extension` vào
  `<gốc>\scripts\pyrevit\ARVTestVK.extension`, chạy `chay_test.ps1 -Journal journal.txt` (nút ChayThu: bảng chụp PNG ngoài
  màn hình, dựng, updater), `journal_nut.txt` (nút ChayNut: vỏ nút với bảng / pick giả) hoặc `journal_file.txt` (nút
  ChayFile: chạy file `.py` ghi ở `chay_file.txt`, vd. `thu5_ip.py`); xong chuyển extension về `_tmp`. Revit mở thu nhỏ,
  bảng dựng ngoài màn hình (không chiếm bàn phím). Khi người dùng đang mở Revit, Dynamo trong phiên thử báo
  "Run blocked" → thử qua pyRevit (ChayFile).

## Đã thử (2026-11-01, bản sao) và còn mở
- Lõi + updater + vỏ nút chạy đúng (log `_tmp\revit_vachkinh\pyrevit_thu\kq\`, `kq_nut\`; ảnh 3D / bảng sáng tối).
- Người dùng chưa bấm thử trong Revit của mình: hộp thoại thật (ShowDialog), Pick thật, Lật cửa, kéo grip vách thật
  (`Cần xác nhận lại`).
