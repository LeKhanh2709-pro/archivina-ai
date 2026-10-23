---
name: chong-tham-mat-bang
description: 'Mặt bằng chống thấm – Trên mặt bằng tầng / căn hộ AutoCAD (.dwg, kể cả tường cửa AutoCAD Architecture), tự tìm phòng cần chống thấm: WC, lô gia, ban công, phòng kỹ thuật nước, phòng rác (theo thiết bị vệ sinh, máy giặt, cục nóng, cửa trượt + giáp ngoài nhà, lan can, text tên phòng), vẽ vào BẢN SAO: đường bo mặt lõi tường + hatch lưới chéo _U 45°/400 màu 3 + nét vén chân tường đỏ rộng 40 cách bo 50, ngắt tại cửa đi, tất cả trên layer A-Material và gom vào block CHONG THAM, kèm ảnh duyệt (Excel chỉ khi người dùng yêu cầu). Dùng khi người dùng nhờ "vẽ chống thấm", "mặt bằng chống thấm", "hatch chống thấm WC / lô gia / ban công", "vén chân tường", hoặc soát phòng ướt nào chưa hatch chống thấm.'
---

# Mặt bằng chống thấm (Archivina)

Từ mặt bằng: (1) nổ AEC trên bản sao ra DXF, (2) dò phòng ướt + ảnh duyệt, (3) vẽ vào bản sao DWG mới, (4) kiểm tra bản sao. Người dùng là kiến trúc sư: báo kết quả và điểm cần quyết định trước, ngắn gọn.

Quy tắc nhận diện, ranh, đảo, cửa, thông số vẽ và số liệu kiểm chứng: đọc `references/nhan-dien.md` khi gặp bản vẽ khác mẫu hoặc người dùng hỏi vì sao vùng nào được / không được vẽ.

**Bản LISP** để người dùng tự chạy trong AutoCAD: `lisp\CHONGTHAM.lsp` — **MỘT FILE DUY NHẤT** (người dùng chốt 23/10/2026): bộ nhận diện (`chay_cho_lisp.ps1`, `dwg_to_dxf_aec.ps1`, `tim_accoreconsole.ps1`, `moi_truong.ps1`, `cai_dat_python.ps1`, `tim_phong_uot.py` + `tao_polyline_phong.py`, `chinh_hinh.py` của `dien-tich-ch`) được nhúng base64 ở cuối file; lần chạy đầu lệnh giải nén ra `<gốc>\_tools\chongtham_<bản>\` (bản = mã băm nội dung, đổi script là ra bản mới). File này **gộp tự động, không sửa tay**: sửa `lisp\chongtham_nguon.lsp` (phần vẽ, lệnh) hoặc script trong `scripts\` / `dien-tich-ch\scripts\` (nhận diện), rồi **luôn chạy** `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\gop_chongtham.ps1` (ghi `<skill>\lisp\CHONGTHAM.lsp` và `<gốc>\scripts\lisp\CHONGTHAM.lsp`, sao lưu bản cũ vào `<gốc>\_backup`), sau đó chép đồng bộ bản repo `<gốc>\chong-tham-mat-bang\`. Máy thiếu Python / gói Python: lệnh hỏi `[Co/Khong]` rồi chạy `cai_dat_python.ps1` (cửa sổ hiện). Lệnh `CHONGTHAM` gọi ngầm `chay_cho_lisp.ps1` (nổ AEC bản sao file đã lưu → `tim_phong_uot.py --xuat-lsp`), chờ xong rồi đọc `du_lieu.txt` và vẽ thẳng vào bản vẽ đang mở (UNDO một lần), gom block, tắt layer nội thất / TBVS và làm mờ layer (giữ khung tên). Logic nhận diện chỉ nằm trong Python: sửa quy tắc ở `tim_phong_uot.py`, LISP tự dùng bản mới. Chạy thử phần vẽ bằng Core Console: gọi `(ct:ve-tu-file "<du_lieu.txt>")` (lệnh `CHONGTHAM` cần COM nên không chạy trong Core Console).

## Công cụ
- `<python>` = Python có ezdxf, shapely, matplotlib, chạy `-I -X utf8` (đặt `PYTHONUTF8=1`). Máy này: `D:\AI\_tools\venv\Scripts\python.exe`; máy khác script tự tìm (`scripts\moi_truong.ps1` → `Find-Python`). `<skill>` = "Base directory for this skill".
- Core Console tự tìm bằng `scripts\tim_accoreconsole.ps1` (registry Autodesk, `<ổ>\Program Files\Autodesk\AutoCAD *`, `<ổ>\autocad\AutoCAD *`; ưu tiên bản có AutoCAD Architecture → chạy kèm `/product ACA` để giữ tường / cửa ACA khi lưu). Máy này chọn `C:\Program Files\Autodesk\AutoCAD 2027` + ACA.
- Cần skill `dien-tich-ch` (dùng lại hàm dựng lưới nét / khung cửa trong `tao_polyline_phong.py`).
- Không đọc script để hiểu cách dùng: chạy `--help` hoặc theo các bước dưới. Giá trị âm truyền dạng `--vung=-1500,...`.

## Các bước
1. **DWG → DXF có nổ AEC** (bản sao, ~3 phút với file 55 MB):
   `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\dwg_to_dxf_aec.ps1 -Dwg "<file.dwg>" -OutDir "<gốc>\_tmp\<việc>"`
2. **Dò phòng ướt** (~80 giây cả tầng):
   `<python> <skill>\scripts\tim_phong_uot.py "<file.dxf>" --out-dir "<thư mục NN_ChongTham>"`
   Ra `<tên>_chongtham.json / .png` (thêm `--excel` mới ra `.xlsx`, chỉ khi người dùng yêu cầu): vùng `se_ve` (xanh), `da_co` (xám), `can_xem` (cam), dấu X cam = **chỗ cần xem** (có thiết bị nhưng không khép được phòng).
   - Thử một căn: `--vung=x0,y0,x1,y1`.
   - Phòng rác / phòng KT nước nhận theo ký hiệu `R` / `N` (mặc định, đổi bằng `--ky-hieu "R=phong_rac,N=phong_kt_nuoc"`), buồng đệm phòng rác tự nhận theo cửa thông sang phòng rác.
   - Phòng bị lọt: `--them "phong_rac:x,y;lo_gia:x,y"` (điểm nằm trong phòng; loại: `wc`, `lo_gia`, `phong_rac`, `phong_kt_nuoc`, `buong_dem_rac`).
   - Bỏ vùng: sửa `trang_thai` của vùng đó trong JSON thành `bo_qua` trước bước 3.
3. **Ảnh duyệt trên nền thật** (gửi người dùng trước khi vẽ nếu có vùng `can_xem`, lô gia nhận theo cửa trượt, hoặc chỗ cần xem):
   `<python> <skill>\scripts\xem_vung.py "<file.dxf>" "<tên>_chongtham.json" --out-dir "<thư mục>" --luoi 3x4` (hoặc `--id 4,30`, `--khung=x0,y0,x1,y1`).
4. **Vẽ vào bản sao** (chỉ vùng `se_ve`; thêm `-TrangThai se_ve,can_xem` nếu người dùng duyệt cả vùng cam):
   `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\ve_chong_tham_vao_ban_sao.ps1 -Dwg "<file.dwg gốc>" -Json "<tên>_chongtham.json" -OutDwg "<thư mục NN_>\<tên>_chong tham.dwg"`
   Đạt khi log `VUNG_YEU_CAU = BO_DA_TAO = HATCH_DA_TAO`, `NET_VEN_YEU_CAU = NET_VEN_DA_TAO`, có dòng `BLOCK CHONG THAM (n doi tuong)`. Cả tầng ~5 phút: chạy nền.
5. **Kiểm tra bản sao:**
   - `<python> <skill>\scripts\kiem_tra_block.py "<bản sao.dwg>" --goc "<file gốc.dwg>"` → `LOI: 0`, số đối tượng AEC bằng bản gốc.
   - Chạy lại bước 1 + 2 (`--khong-anh`) trên bản sao → **0 vùng `se_ve`**, mọi vùng `da_co`.

## Dùng ở máy khác (chốt 23/10/2026: mọi skill / LISP phải chạy được trên máy khác)
- **Không gắn cứng đường dẫn.** Script PowerShell dùng `scripts\moi_truong.ps1` (bản giống hệt ở 3 skill chong-tham-mat-bang, ngan-chay-truc-hkt, truc-lo-mo-mep — sửa một bản thì chép sang hai bản kia): `Get-GocAI` (thư mục chứa `.claude`, hoặc biến `ARCHIVINA_AI`), `Get-ThuMucTam` (`<gốc>\_tmp`; không có gốc → `%LOCALAPPDATA%\ARCHIVINA\_tmp`), `New-ThuMucLam` (đường dẫn ASCII cho file `.scr`), `Find-AutoCAD`, `Find-Python`.
- **Dùng lệnh LISP trên máy mới:** chỉ chép file `CHONGTHAM.lsp`, APPLOAD từ bất kỳ đâu. Máy cần AutoCAD 2021+ (nên có AutoCAD Architecture) và Python 3.10+ (python.org); gói Python lệnh tự hỏi cài. Không cần chép thư mục skill.
- **Thư mục gốc của lệnh** (`ct:goc`): biến `ARCHIVINA_AI` → `<ổ cứng>:\AI` có thư mục `.claude` (máy này `D:\AI`) → `%LOCALAPPDATA%\ARCHIVINA`. Giải nén ở `<gốc>\_tools\chongtham_<bản>\`, tạm ở `<gốc>\_tmp\`, venv ở `<gốc>\_tools\venv` (hoặc `%LOCALAPPDATA%\ARCHIVINA\venv`). Nhận diện lỗi thì lệnh in đường dẫn `nhat_ky.txt` (mọi thông báo của bước chạy ngầm).
- **Chạy các bước skill (Claude) trên máy mới:** chép thư mục `.claude\skills` (cần `chong-tham-mat-bang` và `dien-tich-ch` cạnh nhau), chạy một lần `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\cai_dat_python.ps1`.
- **Không phụ thuộc thiết lập máy:** lệnh đặt tạm rồi trả lại UCS World (bản vẽ đang ở UCS xoay vẫn gom block đúng 0,0; trước `-WBLOCK *` cũng về World — trước đây `-WBLOCK` lấy UCS xoay làm WCS của bản tạm nên toạ độ phòng bị xoay / dời, chống thấm vẽ lệch chỗ; bước nổ AEC cũng về UCS World), HPANNOTATIVE 0, hatch không nền / trong suốt; UNDO Control None / One thì bỏ nhóm undo thay vì hỏng chuỗi lệnh; tên layer có ký tự đại diện (`@ # .`…) được thoát khi tắt / đổi màu; LISPSYS ≠ 1 thì nhắc.

## Áp dụng tại D:\AI
- Tuân thủ 7 QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`. File đầu vào và kết quả trên ổ `D:`; thư mục kết quả đánh số `NN_` (vd. `D:\AI\file mau\03_ChongTham\`).
- **Không sửa DWG gốc, không đụng tab AutoCAD đang mở**: mọi việc chạy ngầm bằng Core Console trên bản sao. Script **không ghi đè** file đã có, **không xoá** thư mục tạm (`<gốc>\_tmp\chongtham_*`, máy này `D:\AI\_tmp`).
- Người dùng chốt 22/10/2026:
  - Bo, hatch, nét vén **đều trên layer `A-Material`**, gom vào **1 block `CHONG THAM`** chèn 0,0.
  - **Mọi loại phòng cùng một hatch** lưới chéo đôi `_U` 45°/400, màu 3 (WC, lô gia, ban công, phòng rác, buồng đệm phòng rác, phòng KT nước).
  - Ký hiệu phòng (chốt 22/10/2026, bổ sung 23/10/2026): `R` = phòng rác, `N` hoặc `KTN` = phòng kỹ thuật nước; buồng đệm phòng rác = phòng nhỏ có cửa thông vào phòng rác.
  - Lệnh LISP `CHONGTHAM` (23/10/2026): sau khi vẽ thì tắt layer nội thất / thiết bị vệ sinh, đổi mọi layer khác sang xám 150,150,150, **không làm mờ layer khung tên**; lưu layer state "TRUOC CHONG THAM". Chỉ đổi trong bảng layer, không sửa màu từng đối tượng, không bind.
  - Lệnh `CHONGTHAM` **không hỏi gì**, gõ là ra kết quả (chốt 23/10/2026): bản vẽ đã lưu và không đổi → đọc file trên đĩa; có thay đổi chưa lưu / chưa lưu lần nào → `-WBLOCK *` ra bản tạm trong thư mục `chongtham_lisp_*` (giữ AEC, không lưu đè, không đổi tên bản vẽ đang mở).
  - **Xref ngoài: không bind, kể cả trong bản tạm** (chốt 23/10/2026). Căn hộ là xref (vd. CT2: 20 căn ở `A:\1. DU AN\...`) → `dwg_to_dxf_aec.ps1` chép bản sao từng xref có chèn trong Model, nổ AEC, xuất DXF riêng (song song, tới 2 cấp; xref lồng dạng Overlay bỏ; xref chỉ khung tên / lưới / chi giới bỏ), ghi `<tên>_xref.txt`; `tim_phong_uot.py` đặt nội dung xref đúng vị trí **chỉ trong bộ nhớ**, mã căn lấy từ tên xref. Người dùng cho phép đọc xref trên ổ `A:` (chỉ chép bản sao, 23/10/2026). Xref không tìm thấy file → lệnh báo "Xref không tìm thấy file…".
  - Nét vén: màu 1, global width 40, nét liền, cách bo 50, **ngắt tại cửa đi** (không quét vén được ở cửa), kể cả **cửa thang máy** (ô tường không hatch cạnh thang có text tải trọng `…KG`, xác nhận 23/10/2026).
  - Lô gia / ban công: ranh tới **mặt trong lan can / tường lửng**.
  - **Không tạo file Excel** (chốt 23/10/2026): mặc định không xuất `.xlsx`, kể cả lệnh LISP; người dùng cần thì tự yêu cầu → chạy `tim_phong_uot.py` với `--excel`.
  - Không vẽ bảng ghi chú (đã có trong file). Luồng Python vẽ vào bản sao không làm mờ / tắt layer; lệnh LISP thì có (xem trên).
- Không ghi chiều cao vén, vật liệu, số hiệu chi tiết nếu người dùng chưa cung cấp (`[Chờ bổ sung]`); bảng ghi chú trong file mẫu ghi vén cao 300, lưới thủy tinh, chi tiết A.17,01 — chỉ trích khi người dùng hỏi.

## Báo cáo cho người dùng
- Số vùng theo loại (WC / lô gia / phòng rác / KT nước) và trạng thái; số bo, hatch, nét vén đã vẽ; đường dẫn bản sao DWG + PNG (Excel chỉ khi người dùng yêu cầu).
- Danh sách **chỗ cần xem** (tọa độ, nhận theo thiết bị gì) và vùng `can_xem`; lô gia nhận theo cửa trượt / lan can (để người dùng soát).
- Nêu **đã kiểm tra thực tế** (log khớp, `kiem_tra_block` LOI 0, dò lại 0 vùng `se_ve`, ảnh) và **chưa kiểm tra** (chưa mở trong AutoCAD thật, tầng / dự án khác chưa chạy).
