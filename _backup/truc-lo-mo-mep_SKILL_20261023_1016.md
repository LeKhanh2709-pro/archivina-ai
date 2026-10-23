---
name: truc-lo-mo-mep
description: 'Trục lỗ mở MEP – Trên mặt bằng tầng AutoCAD (.dwg), tìm mọi trục kỹ thuật / hộp kỹ thuật (cùng quy tắc với skill ngan-chay-truc-hkt: ô dấu X, lỗ mở có ống đứng, khung lỗ mở MEP có ống; bỏ thang máy, nội thất, lỗ mở sàn không ống) rồi chèn dynamic block A-MEP (khung + X + dim + Field diện tích m2) co giãn khít từng trục / hộp, LUÔN trên layer A-MEP, gom vào block LO MO MEP, vào BẢN SAO, kèm Excel. Dùng khi người dùng nhờ "bo lỗ mở", "trục lỗ mở", "mặt bằng lỗ mở MEP", "chèn block A-MEP", "bo A-MEP theo trục / hộp kỹ thuật", hoặc soát xem trục nào chưa có A-MEP. Lệnh LISP: LOMO (file Lomo.lsp).'
---

# Trục lỗ mở MEP – bo trục / hộp kỹ thuật bằng block A-MEP (Archivina)

Từ mặt bằng tầng: dò trục / hộp kỹ thuật, chèn block **A-MEP** kéo giãn khít khung từng ô vào **bản sao** DWG, xuất Excel. Người dùng là kiến trúc sư: báo kết quả và điểm cần quyết định trước, ngắn gọn.

Quy tắc bo, thông số block, lý do chọn cách chạy: `references/quy-tac-bo.md`.

**Nguyên tắc cốt lõi:**
- **Nhận diện trục / hộp** dùng hàm `nc:do` của lệnh NCL (`fire_stop_shaft.lsp`, skill `ngan-chay-truc-hkt`), nên hai skill nhận cùng một bộ ô. Sửa quy tắc nhận diện thì sửa bên skill ngăn cháy.
- **A-MEP là dynamic block** (`Distance1` = cạnh dài theo Y block 100–4000, `Distance2` = cạnh ngắn theo X block 100–3000, bước 10). Gán tham số dynamic cần COM → **không chạy được bằng Core Console**. Script dùng **AutoCAD đầy đủ** (`acad.exe /b`) chạy thành một tiến trình riêng trên bản sao. Việc này nặng máy (mở thêm một cửa sổ AutoCAD thu nhỏ, mất 1–3 phút), nên báo người dùng trước khi chạy.
- **`Lomo.lsp` là MỘT FILE gộp sẵn** (người dùng chốt 22/10/2026: thao tác đơn giản nhất, chỉ APPLOAD 1 file rồi gõ `LOMO`). File này do `scripts\gop_lomo.ps1` tạo ra, **không sửa tay**. Nó ghép phần dò trục của `fire_stop_shaft.lsp` (skill ngăn cháy, bỏ lệnh NCL) với `lisp\lomo_nguon.lsp` (phần lỗ mở + lệnh `LOMO`), rồi ghi ra `<skill>\lisp\Lomo.lsp` và `D:\AI\scripts\lisp\Lomo.lsp` (bản cũ tự sao lưu vào `_backup`). Sửa quy tắc dò → sửa `fire_stop_shaft.lsp`; sửa phần lỗ mở → sửa `lomo_nguon.lsp`; sau đó **luôn chạy lại** `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\gop_lomo.ps1`. Script `chen_amep_vao_ban_sao.ps1` cũng chỉ nạp `Lomo.lsp`. Tên file `Lomo.lsp` và tên lệnh `LOMO` do người dùng đặt (22/10/2026), không đổi.
- **Layer lỗ mở LUÔN là `A-MEP`** (người dùng chốt 22/10/2026, tuân thủ tuyệt đối): mọi block A-MEP và block gom `LO MO MEP` đều trên `A-MEP`, không dùng `A_MEP` hay tên khác. Chưa có layer thì tạo mới theo thông số layer `A_MEP` của file mẫu (màu 32, Continuous, nét 0.05). Layer đang khoá thì mở tạm, xong khoá lại.

## Công cụ
- `<skill>` = "Base directory for this skill". `<python>` = `D:\AI\_tools\venv\Scripts\python.exe`.
- Thư viện block: `<skill>\assets\A-MEP_thu_vien.dwg` (bản chép của `D:\AI\file mau\FILE MẪU LỖ MỞ.dwg`). Bản vẽ chưa có A-MEP thì lệnh chép định nghĩa block từ file này (ObjectDBX, chỉ đọc). Đã có A-MEP thì dùng block có sẵn, không định nghĩa lại.
  **File này KHÔNG có trên GitHub** (người dùng chốt 22/10/2026: giữ quy ước `.gitignore` không đẩy `.dwg`), và **không bắt buộc phải có** (người dùng chốt 23/10/2026: máy khác không có block A-MEP vẫn phải tạo được). Lệnh chọn cách chèn (log `CHE_DO`):
  - `dong`: bản vẽ đã có A-MEP dynamic, hoặc tìm thấy file thư viện (đường dẫn `amep:cfg 'thu-vien`, hoặc `A-MEP_thu_vien.dwg` trong Support File Search Path) → chèn A-MEP dynamic, gán `Distance1` / `Distance2`.
  - `tinh`: không có các thứ trên (hoặc A-MEP trong bản vẽ không phải dynamic) → **tự dựng block tĩnh `A-MEP <rộng>x<dài>`** (vd. `A-MEP 600x1500`) cho từng kích thước, dùng lại nếu đã có. Hình thể như A-MEP gốc: khung, X nét `ACAD_ISO03W100` (tự nạp từ `acadiso.lin`), 2 dim, số diện tích m² (2 số lẻ, giá trị tĩnh thay Field), text Arial cao 30. Mọi đối tượng trong block trên layer `0` nên hiện theo layer `A-MEP`. Dim dùng kiểu `_1-10_HKT`; bản vẽ chưa có thì tạo kiểu cùng tên từ `A 1-100` (hoặc kiểu hiện hành), chỉ đổi DIMSCALE 10 / DIMTXT 2.0 như block gốc, xong trả lại kiểu hiện hành. Khác bản dynamic: không kéo giãn được; dim và số diện tích nằm trên `A-MEP` nên **có in** (bản gốc để trên layer `A_K in` không in).
  - Thử chế độ máy khác ngay trên máy này: thêm `-KhongThuVien` khi chạy `chen_amep_vao_ban_sao.ps1` (đặt biến `amep-thu-vien` = `"KHONG"`).
- Kiểm tra: `scripts\kiem_tra_amep.py <bản sao.dxf> [<..._amep.csv>]` đếm A-MEP (trong Model / trong block gom), in layer và độ lệch khung. `scripts\kiem_ngoac_lisp.py <file.lsp>` kiểm tra cân ngoặc sau mỗi lần sửa / gộp LISP.

## Các bước
1. **Chèn vào bản sao** (báo người dùng trước vì sẽ mở thêm một AutoCAD):
   `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\chen_amep_vao_ban_sao.ps1 -Dwg "<file.dwg gốc>" -OutDwg "<thư mục NN_>\<tên>_lo mo.dwg"`
   Kết quả: bản sao DWG, `<tên>_lo mo_amep.csv`, `<tên>_lo mo_amep.xlsx`, `<tên>_lo mo.dwg_log.txt`.
   Log có `DA_NAP_LISP`, `CHE_DO dong|tinh`, `BLOCK_DA_CHEN n` = `DA_CHEN n` và `BLOCK_GOM LO MO MEP` là đạt. Log có `LOI ...` thì báo nguyên văn. File lớn (~50 MB) thì chạy nền, `-TimeoutSec 3600`.
2. **Kiểm tra:**
   - Chạy lại bước 1 trên bản sao kết quả (ra file `_lan2`) → phải còn `DA_CHEN 0`, các ô đã chèn chuyển sang `DA_CO`.
   - Đổi bản sao sang DXF (`..\ngan-chay-truc-hkt\scripts\dwg_to_dxf.ps1`), chạy `<python> -I <skill>\scripts\kiem_tra_amep.py <file.dxf> <..._amep.csv>`: khung từng A-MEP so với ô trục (sai lệch ≤ 5 mm do làm tròn bước 10), layer phải là `A-MEP`.
   - Xuất PNG vài vùng bằng `-PLOT` vùng `W` (mẫu `D:\AI\_tools\plot_png.scr`). Dim và Field của A-MEP nằm trên layer `A_K in` không in nên không hiện trên ảnh.
3. Người dùng muốn tự chạy trong AutoCAD: APPLOAD **một file** `D:\AI\scripts\lisp\Lomo.lsp`, gõ `LOMO`.
   - Kiểm tra thêm: mọi A-MEP và block gom nằm trên layer `A-MEP` (kiểm tra bằng `scripts\kiem_tra_amep.py`, in ra tập layer).

## Áp dụng tại D:\AI
- Tuân thủ 7 QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`.
- File đầu vào và kết quả trên ổ `D:`. Thư mục kết quả đánh số `NN_` (thư mục thử: `D:\AI\file mau\02_LoMo\`).
- **Không sửa DWG gốc, không đụng phiên AutoCAD người dùng đang mở**: script tự mở một `acad.exe` riêng trên bản sao trong `D:\AI\_tmp\amep_*`, xong thì thoát. Chỉ dừng (kill) đúng tiến trình script tự khởi động khi quá thời gian.
- Script **không ghi đè** file đã có, **không xoá** thư mục tạm.
- Layer chèn: **`A-MEP`** (xem trên). Không đổi màu / tắt layer khác (khác skill ngăn cháy).
- **Gom vào block** (người dùng chốt 22/10/2026, để dễ kiểm soát): mọi A-MEP vừa chèn được gom vào 1 block `LO MO MEP` (trùng tên thì `LO MO MEP 2`…, không định nghĩa lại block cũ), chèn tại 0,0 trên `A-MEP`. A-MEP bên trong vẫn là dynamic block (sửa bằng REFEDIT). Chạy lại thì A-MEP nằm trong block `LO MO MEP*` được nhận là "đã có". Log có dòng `BLOCK_GOM <tên>`.
- **Bo theo hình lỗ mở** (người dùng chốt 22/10/2026): A-MEP chỉ co giãn thành chữ nhật, nên vùng không chữ nhật (hộp chữ L, chữ T…) được tách thành nhiều khung chữ nhật, mỗi khung 1 A-MEP. Vùng gộp từ nhiều ô X / lỗ mở thì **mỗi ô một A-MEP** (đúng từng lỗ mở trên bản vẽ). Khung MEP chữ L hoặc ô chồng nhau thì tách lưới đa giác, lấy cách ra ít khung nhất. Excel ghi cột "Vùng trục / hộp" và "Số khung bo của vùng" để biết khung nào tách từ cùng một hộp.
- **Hộp xoay xiên** (người dùng yêu cầu 23/10/2026, cánh nhà xoay ở MB Tầng 5): bo cả ô dấu X xoay, khung MEP chữ nhật xoay và chữ L / T xoay; A-MEP chèn theo góc của ô. Cách dò: `references/quy-tac-bo.md` mục "Hộp xoay xiên".
- Không chèn, chỉ liệt kê (`Cần xác nhận lại`): khung hình thang / tứ giác không đều (cạnh xiên lẫn cạnh thẳng, không tách được thành chữ nhật), khung vượt giới hạn tham số block. Không tự kéo dài giới hạn block.
- `nc:do` (fire_stop_shaft.lsp) trả thêm phần tử thứ 6 = danh sách ô gốc của vùng, cho lệnh LOMO dùng. Lệnh NCL không dùng phần tử này.

## Báo cáo cho người dùng
- Số vùng trục / hộp, số khung bo (vùng nào tách nhiều khung); số khung đã chèn / đã có / cần xem lại (cạnh xiên, vượt giới hạn) kèm tọa độ tâm và kích thước; khung bị làm tròn lệch > 0 mm.
- Đường dẫn bản sao DWG + Excel.
- Nêu **đã kiểm tra** (chạy lại còn 0 ô chưa chèn, đo khung qua DXF) và **chưa kiểm tra** (chưa mở xem trong AutoCAD thật, tầng khác chưa chạy).
