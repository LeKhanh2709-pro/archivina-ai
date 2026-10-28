---
name: chia-do-vach-kinh
description: 'Chia đố vách kính – Từ CHIỀU DÀI vách (mm) và các cửa trong vách (cửa sổ mở, cửa đi), tự chia đố thanh đứng 65 đều nhau, mỗi ô < 1200 mm tâm-tâm, rồi dựng vách kính mặt bằng bằng các block người dùng cấp (VK_DoDung, VK_CuaSoMo, VK_CuaDi) trên layer A-Window, gom vào block VACH KINH <dài>, kèm chuỗi kích thước "dim cua" và ảnh PNG, xuất DXF + DWG. Dùng khi người dùng nhờ "chia đố", "chia thanh đứng vách kính", "dựng vách kính dài …", "vách kính có cửa sổ / cửa đi", hoặc hỏi khoảng chia đố cho một chiều dài vách.'
---

# Chia đố vách kính (Archivina)

Người dùng chỉ cấp **chiều dài vách** (mép ngoài – mép ngoài) và cửa nằm ở ô nào; skill tính vị trí đố và dựng vách kính mặt bằng mới (không sửa bản vẽ nào có sẵn). Người dùng là kiến trúc sư: báo chuỗi ô và đường dẫn kết quả trước, ngắn gọn.

## Quy tắc chia (người dùng chốt 28/10/2026)
- Đố thanh đứng rộng **65 mm** (block vẽ 65,7, chỉ là nét chi tiết; số chia dùng 65). Đố đầu và đố cuối chính là khung vách: tâm cách mép ngoài **32,5**.
- Khoảng cần chia `S = L − 65` (tâm đố đầu → tâm đố cuối).
- Cửa trong vách chiếm đúng khoảng **tâm-tâm 2 đố của cửa**: cửa sổ mở **1000**, cửa đi **1665** (đo từ block người dùng cấp; người dùng chốt dùng 1665 cho mọi cửa đi đến khi báo đổi). Đố hai bên cửa là đố của block cửa, không chèn thêm đố trùng.
- Phần còn lại `R = S − Σ cửa` chia **đều** thành `N` ô kính, `N` nhỏ nhất để mỗi ô **< 1200** (1200 đúng là không đạt) → `N = floor(R / 1200) + 1`. **Không làm tròn** khoảng chia (vd. 1048,33). Kích thước ghi trên bản vẽ làm tròn theo kiểu dim `dim cua` (0 số lẻ, làm tròn nửa lên: 32,5 → 33).
- Cửa đặt vào ô thứ `k` (đếm từ trái, kể cả ô cửa). Một cửa không ghi `k` thì đặt ô giữa (`tổng ô // 2 + 1`); nhiều cửa phải ghi `k` cho từng cửa.
- Ví dụ đối chiếu (ảnh người dùng gửi, vách 4210 + cửa sổ): 4210 − 65 − 1000 = 3145 → 3 ô × 1048,33 → `[1048 | 1048 | SO 1000 | 1048]`, bản vẽ gốc ghi 33 / 1048 / 1048 / 1000 / 1048 / 33.

## Công cụ
- `<python>` = Python có ezdxf + matplotlib (máy này `D:\AI\_tools\venv\Scripts\python.exe`; máy khác dùng `Find-Python` trong `scripts\moi_truong.ps1`). `<skill>` = "Base directory for this skill".
- Thư viện block: `<skill>\assets\VK_thu_vien.dxf` + `VK_thu_vien.json` (khoảng tâm-tâm, vị trí kính). Mọi block có điểm chèn = **tâm đố trái**, vách chạy theo trục X, Y = chiều sâu đố (mặt kẹp kính phía +Y); mọi nét trên layer `A-Window`, giữ màu / kiểu nét như bản gốc (đã đổi BYLAYER thành màu cụ thể).
- Không đọc script để hiểu cách dùng: chạy `--help` hoặc theo các bước dưới.

## Các bước
1. **Dựng vách:**
   `<python> <skill>\scripts\chia_do.py --dai <L> [--mo so@3] [--mo di@5] --out "<thư mục NN_>\VK_<L>.dxf"`
   - `--mo`: `so` = cửa sổ mở, `di` = cửa đi, `@k` = ô thứ k; nhiều cửa ghi `--mo so@1,di@4`.
   - Tuỳ chọn: `--goc <độ>` `--x` `--y` (vị trí mép ngoài đầu vách), `--lat` (mặt kẹp kính sang −Y), `--khong-kinh`, `--khong-dim`, `--khong-anh`.
   - In chuỗi ô + JSON toạ độ tâm đố; tạo `.dxf`, `.json`, `.png` (không ghi đè: trùng tên thì thêm `_2`, `_3`…). **Không tạo Excel.**
2. **Sang DWG:** `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\dxf_to_dwg.ps1 -Dxf "<file>.dxf"` (Core Console, DWG 2018, không ghi đè).
3. **Xem PNG** trước khi báo. Muốn ảnh do AutoCAD in thì `-PLOT` theo mẫu `<gốc>\_tools\plot_png.scr` trên file DWG.

## Kết quả
- Block `VACH KINH <L>` (trùng tên thì `… 2`) chèn tại `(x, y)` xoay `--goc`, layer `A-Window`, gồm: `VK_DoDung` ở mọi tâm đố không thuộc cửa, `VK_CuaSoMo` / `VK_CuaDi` tại tâm đố trái của cửa, kính ô cố định.
- Kích thước kiểm tra, kiểu `dim cua`, **nằm trong block `VACH KINH`, layer `Defpoints`** (không in; người dùng chốt 28/10/2026), **sát vách** về phía mặt kẹp kính: hàng chuỗi đố (mép ngoài – tâm các đố – mép ngoài) cách trục vách 165, hàng tổng chiều dài cách 260 (mặt đố ở +93,6).

## Lệnh LISP `VK` (người dùng tự chạy trong AutoCAD, chốt 28/10/2026)
- File: `<skill>\lisp\VK.lsp` (bản người dùng APPLOAD: `<gốc>\scripts\lisp\VK.lsp`). **VK.lsp là file sinh tự động**: sửa `lisp\vk_nguon.lsp` rồi chạy `<python> <skill>\scripts\gop_vk.py` (đổi mọi chữ có dấu trong chuỗi thành `\U+XXXX`, chỉ còn ASCII → hộp thoại / thông báo đúng dấu với cả `LISPSYS = 0` và `1`; người dùng báo lỗi font khi `LISPSYS = 0`, 28/10/2026), rồi chép `VK.lsp` sang `<gốc>\scripts\lisp\`. **Một file duy nhất, mang sang máy khác là chạy** (người dùng chốt 28/10/2026): block `VK_DoDung` / `VK_CuaSoMo` / `VK_CuaDi`, kiểu nét CENTER / HIDDEN / CENTER2, layer `A-Window`, kiểu chữ `Arch-Dim` (romans.shx) và kiểu dim `dim cua` **nhúng sẵn** ở cuối `VK.lsp` (~1 MB, dữ liệu entmake), không cần file thư viện hay Python. Bản vẽ đã có block / kiểu cùng tên thì dùng luôn, không định nghĩa lại.
- Dữ liệu nhúng `lisp\vk_du_lieu.lsp` sinh bằng `scripts\nhung_block.ps1` (AutoCAD `/b` mở `assets\VK_thu_vien.dwg`, chạy `scripts\xuat_du_lieu_block.lsp`: entget từng đối tượng, bỏ handle / tham chiếu, số thực 10 chữ số lẻ) rồi `gop_vk.py` gộp vào `VK.lsp`. Đổi block: tạo lại `VK_thu_vien.dxf` → `xuat_thu_vien_lisp.py` + `dxf_to_dwg.ps1` ra `VK_thu_vien.dwg` → `nhung_block.ps1` → `gop_vk.py`.
- Khi tạo block từ dữ liệu, HATCH phải sửa trước khi entmake (`vk:sua-hatch`): `(97 . n)` → `(97 . 0)` (tham chiếu biên liên kết không mang theo được) và góc cung biên đưa về [0, 2π). Một đối tượng entmake lỗi làm hỏng cả định nghĩa block đang tạo (ENDBLK trả nil).
- Gõ `VK` → hộp thoại: chiều dài vách; cửa sổ mở (số lượng, rộng tâm-tâm mặc định 1000, ở ô thứ); cửa đi (số lượng, rộng mặc định 1665, ở ô thứ). Bảng tự tính lại số đố, số ô kính × khoảng chia và danh sách từng ô khi rời ô nhập hoặc bấm **Tính lại**; lỗi hiện ngay dưới bảng. Có ô **Lật vách**. OK → chọn điểm đầu vách (mép ngoài) và điểm hướng vách (Enter = trục X).
- Ô đặt cửa bỏ trống thì tự rải đều vào các ô còn trống (cửa đi trước, cửa sổ sau; 1 cửa → ô giữa `tổng // 2 + 1`, khớp script Python).
- **Rộng cửa khác mặc định** → tạo block `VK_CuaSoMo_<rộng>` / `VK_CuaDi_<rộng>` bằng cách kéo giãn block gốc: đố trái giữ nguyên, đố phải dời, phần cánh giữa giãn theo tỉ lệ, cung mở cánh (r > 200) nhân bán kính theo tỉ lệ; bản lề / tay nắm nằm trong vùng giãn nên cũng bị giãn nhẹ (`Cần xác nhận lại`).
- Kết quả giống script Python: block `VACH KINH <dài>` (trùng tên thì `… (2)`) trên `A-Window`, kích thước kiểm tra trong block. AutoCAD 2027 `-BLOCK` tự đổi đối tượng thành 1 bản chèn tại 0,0 → lệnh dời bản chèn đó tới điểm chọn (bản cũ xoá đối tượng → chèn mới).
- **Chạy thử không giao diện** (hộp thoại DCL không chạy được khi tự động): `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\chay_thu_vk.ps1 -Dwg "<bản vẽ trắng>.dwg" -OutDwg "<kết quả>.dwg" -Lisp "(vk:thu 5300.0 1 1000.0 0 1665.0 nil nil nil '(0.0 0.0 0.0) 0.0)"` — `vk:thu L số-sổ rộng-sổ số-đi rộng-đi ô-sổ ô-đi lật điểm góc(rad)`; log từng vách ở `<kết quả>.dwg_log.txt`.
- Lưu ý khi viết LISP chạy bằng script: **không huỷ lệnh bằng `(command)`** (Esc trong script dừng cả script, AutoCAD treo); `open` có tham số mã hoá `"utf8"` lỗi khi `LISPSYS = 0` (AutoCAD 2027 chạy `/b` trên máy này đang `LISPSYS = 0`) → bọc `vl-catch-all-apply`, lỗi thì ghi thường.
- `VK_thu_vien.dwg` (nguồn để nhúng) sinh từ `VK_thu_vien.dxf` bằng `scripts\xuat_thu_vien_lisp.py` (đặt sẵn 1 bản chèn mỗi block + 1 dim `dim cua` trong model) rồi `dxf_to_dwg.ps1`. Chạy thử: `-LispFile <file.lsp>` thay cho `-Lisp` khi biểu thức có dấu ngoặc kép.

## Đổi block (khi người dùng cấp block mới)
Người dùng xuất DXF 3 file vào một thư mục (tên chứa `thanh dung`, `cua so`, `cua di`; mỗi file cửa có đúng 2 đố là block cùng tên), rồi:
`<python> <skill>\scripts\tao_thu_vien.py --nguon "<thư mục>" --out "<skill>\assets\VK_thu_vien.dxf"`
Script không ghi đè: chép thư viện cũ vào `_backup\` trước (quy tắc 2), tạo bản mới ở tên khác rồi người dùng đồng ý mới thay. Script tự đo khoảng tâm-tâm 2 đố của cửa (ghi vào JSON) và tấm kính lá cửa sổ. Nguồn hiện tại: `<gốc>\file mau\block vach kinh\ACAD-block *.dxf` (28/10/2026).

## Giới hạn đã biết (`Cần xác nhận lại`)
- **Kính ô cố định** chưa có block riêng: đang vẽ theo 2 tấm kính của lá cửa sổ mở (y 42,0–48,0 và 56,9–62,9 so với tâm đố), chạy giữa 2 mặt đố (tâm ± 32,5). Người dùng đồng ý giữ tạm cách này (28/10/2026); khi người dùng cấp block / cấu tạo kính cố định thì thay.
- Kính cửa đi nằm trên trục tâm đố (y −6 … 6,3), đúng như block người dùng cấp.
- Layer `A-Window` theo người dùng chốt; file ISO công ty ghi cửa đi / cửa sổ là `A-Door` (`standards\ISO_KienTruc_AutoCAD.md`).
- Chưa đặt vách vào bản vẽ mặt bằng có sẵn: kết quả là bản vẽ mới, người dùng tự chèn / chép vào mặt bằng.
- Ô kính quá hẹp (cửa gần lấp hết vách) không cảnh báo; vách ngắn hơn tổng cửa thì báo lỗi.
- Mới kiểm tra bằng ảnh PNG (ezdxf và AutoCAD in) và đọc lại DWG; chưa mở trong AutoCAD thật.
- Lệnh `VK`: phần dựng vách đã chạy thử bằng `acad.exe /b` (5 vách, gồm cửa kéo giãn 1200 / 1400, lật + xoay 30°); **hộp thoại chưa thử** (cần người dùng bấm thử). Hộp thoại ghi file DCL (ASCII, mã `\U+XXXX`) vào `TEMPPREFIX`; bản đầu ghi UTF-8 bị lỗi font khi `LISPSYS = 0`, bản mã hoá chưa được người dùng xác nhận hiển thị đúng.

## Áp dụng tại D:\AI
- Tuân thủ các QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`. Thư mục kết quả đánh số `NN_` (mẫu: `D:\AI\file mau\05_VachKinh\`). Thư mục tạm `<gốc>\_tmp\vachkinh_*` giữ lại, không xoá.

## Báo cáo cho người dùng
- Chuỗi ô (vd. `1048,33 | 1048,33 | SO 1000 | 1048,33`), số đố, đường dẫn DXF / DWG / PNG.
- Nêu đã kiểm tra gì (PNG, đọc lại DWG) và chưa kiểm tra gì (chưa mở trong AutoCAD thật), kèm các điểm `Cần xác nhận lại` ở trên nếu liên quan.
