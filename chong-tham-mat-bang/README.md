# chong-tham-mat-bang — Mặt bằng chống thấm

Tự động tìm các phòng cần chống thấm trên mặt bằng tầng AutoCAD (kể cả tường / cửa AutoCAD Architecture): **WC, lô gia / ban công, phòng rác, buồng đệm phòng rác, phòng kỹ thuật nước**. Với mỗi phòng, vẽ **đường bo + hatch chống thấm + nét vén chân tường**, gom vào block và làm mờ bản vẽ.

Gồm 2 cách dùng, cùng một bộ nhận diện:

| Cách dùng | File | Khi nào dùng |
|---|---|---|
| Lệnh AutoLISP `CHONGTHAM` | `lisp/CHONGTHAM.lsp` | Người dùng tự chạy trong AutoCAD, vẽ thẳng vào bản vẽ đang mở. |
| Skill Claude Code | `SKILL.md`, `scripts/`, `references/` | Claude chạy ngầm bằng AutoCAD Core Console trên bản sao, xuất ảnh duyệt (Excel chỉ khi yêu cầu, `--excel`). |

## Thể hiện

| Thành phần | Đối tượng | Layer | Thông số |
|---|---|---|---|
| Đường bo | polyline kín, màu 3 | `A-Material` | mặt lõi tường (không tính trát 15) / mặt trong lan can |
| Đảo | polyline kín, màu 3 | `A-Material` | lòng hộp kỹ thuật trong phòng (không chạm biên); cột chạm biên thì khấc vào bo |
| Hatch | hatch liên kết | `A-Material` | User-defined, góc 45°, khoảng cách 400, **double** (lưới chéo), màu 3 |
| Nét vén chân tường | polyline hở, màu 1 | `A-Material` | rộng 40, cách bo 50 vào trong, **ngắt tại cửa đi và cửa thang máy**, chạy liền qua cửa sổ |
| Block | INSERT tại 0,0 | `A-Material` | `CHONG THAM` (trùng tên thì `CHONG THAM 2`…) |

## Nhận diện

- **WC**: thiết bị vệ sinh (block trên `A-Interior WC`, xí, sen, lavabo, bồn tắm); bỏ ống đứng `piped*`, block trục `TA1`.
- **Lô gia / ban công**: máy giặt, cục nóng điều hoà; hoặc ô 1–12 m², rộng ≥ 800, giáp ngoài nhà, có cửa trượt / lan can, không có nội thất.
- **Phòng rác**: ký hiệu `R`. **Phòng KT nước**: ký hiệu `N` hoặc `KTN`. Ô có ký hiệu phải có cửa đi, không thì coi là hộp kỹ thuật.
- **Buồng đệm phòng rác**: ô 1–10 m² nối với phòng rác bằng cửa trong tường chung và có thêm cửa ra hành lang.
- **Cửa thang máy rác**: ô tường không hatch cạnh text tải trọng `…KG`, hoặc giếng thang (khung chữ nhật có dấu X) lấn vào phòng → khoét giếng và ngắt nét vén.
- Thiết bị không rơi vào ô kín nào: dựng lại lưới quanh đó, thêm nét mặt ngoài (layer `0`, `A-line*`) để khép lô gia.

Chi tiết quy tắc, số liệu kiểm chứng: `references/nhan-dien.md`.

## Lệnh LISP `CHONGTHAM`

1. **Sao lưu bản vẽ** (lệnh vẽ thêm vào bản vẽ đang mở). Bản vẽ phải được lưu.
2. `APPLOAD` → chọn `lisp/CHONGTHAM.lsp`. Gõ **`CHONGTHAM`**.
3. Nhận diện chạy ngầm trên bản sao file đã lưu (3–6 phút với mặt bằng tầng ~50 MB, AutoCAD tạm dừng chờ). Xong lệnh vẽ luôn và in số phòng theo loại, các chỗ "cần xem", thư mục chứa ảnh xem lại (không tạo Excel).
4. Lệnh tắt layer nội thất / thiết bị vệ sinh, đổi các layer khác sang xám 150,150,150, **giữ nguyên màu layer xref khung tên**; trạng thái layer cũ lưu thành layer state `TRUOC CHONG THAM`.
5. Sai thì **Ctrl+Z một lần** để hoàn tác toàn bộ. Chạy lại: phòng đã có trong block `CHONG THAM*` không vẽ trùng.

Lệnh LISP gọi bộ nhận diện Python (`scripts/chay_cho_lisp.ps1` → `scripts/tim_phong_uot.py`), nên máy cần:
- Python 3.12 + gói `ezdxf`, `shapely`, `openpyxl`, `matplotlib` (mặc định `D:\AI\_tools\venv`);
- AutoCAD Core Console (tự tìm trong `C:\Program Files\Autodesk\AutoCAD *` và `D:\autocad\AutoCAD *`; có AutoCAD Architecture thì chạy kèm `/product ACA`);
- skill **`dien-tich-ch`** cài cạnh skill này (`.claude/skills/dien-tich-ch/`) — dùng lại hàm dựng lưới nét / khung cửa trong `tao_polyline_phong.py`.

Đường dẫn khác máy: sửa `ct:cfg` ở đầu file LISP và tham số `-Python` của `chay_cho_lisp.ps1`.

## Skill Claude Code

Chép cả thư mục vào `.claude/skills/chong-tham-mat-bang/` của dự án. Quy trình: `SKILL.md`.

- `scripts/tim_accoreconsole.ps1` — tìm AutoCAD Core Console.
- `scripts/dwg_to_dxf_aec.ps1` — DWG → DXF trên bản sao, nổ tường / cửa ACA.
- `scripts/tim_phong_uot.py` — dò phòng ướt, xuất JSON + PNG (+ Excel khi có `--excel`, + file dữ liệu cho LISP `--xuat-lsp`).
- `scripts/xem_vung.py` — ảnh duyệt trên nền bản vẽ thật.
- `scripts/ve_chong_tham_vao_ban_sao.ps1` — vẽ vào bản sao DWG, gom block.
- `scripts/kiem_tra_block.py` — kiểm tra bản sao (layer, màu, hatch, số đối tượng ACA).
- `scripts/chay_cho_lisp.ps1` — chạy nền cho lệnh LISP.

## Đã kiểm chứng (23/10/2026)

- 254HQV Tháp B tầng 4: 82 vùng (47 WC, 31 lô gia, phòng rác, buồng đệm, 2 phòng KT nước); căn CH15 khớp bản vẽ tay.
- CT1 tầng 5A-10: 83 vùng (46 WC, 31 lô gia, 2 phòng rác, 2 buồng đệm, 2 phòng KT nước `KTN`); 4 khu giặt thông phòng khách không tách được → "cần xem".
- Phần vẽ của LISP chạy thử bằng Core Console trên CT1. Lệnh đầy đủ trong AutoCAD thật: người dùng đang chạy thử.

Giới hạn: bo theo mặt lõi tường chỉ khi bản vẽ có nét trát song song; khu giặt không có tường / cửa tách khỏi phòng khách không tự nhận; ký hiệu phòng so nguyên văn.
