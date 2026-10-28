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
- Chuỗi kích thước (mép ngoài – tâm các đố – mép ngoài), kiểu `dim cua`, layer `A-Dimension`, cách trục vách 400 về phía mặt kẹp kính, nằm ngoài block.

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

## Áp dụng tại D:\AI
- Tuân thủ các QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`. Thư mục kết quả đánh số `NN_` (mẫu: `D:\AI\file mau\05_VachKinh\`). Thư mục tạm `<gốc>\_tmp\vachkinh_*` giữ lại, không xoá.

## Báo cáo cho người dùng
- Chuỗi ô (vd. `1048,33 | 1048,33 | SO 1000 | 1048,33`), số đố, đường dẫn DXF / DWG / PNG.
- Nêu đã kiểm tra gì (PNG, đọc lại DWG) và chưa kiểm tra gì (chưa mở trong AutoCAD thật), kèm các điểm `Cần xác nhận lại` ở trên nếu liên quan.
