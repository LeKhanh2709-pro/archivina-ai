# CAD → legend 2D Revit (chi tiết cửa)

Làm 2026-11-13 theo yêu cầu người dùng: vẽ các ô chi tiết của `CT Cua khanh.dxf` thành **legend 2D** trong Revit.
Hatch → **Filled Region**, nét trùng chỉ giữ **1 nét**, **mỗi ô chi tiết 1 detail group**. Người dùng chốt thêm:
**1 kiểu chữ** (Arial, rộng 1, chỉ 3 cỡ 2,5 / 3,5 / 5 mm) và **1 kiểu dim** (`CTC_Dim 2.5mm`).

Trạng thái: chạy thử trên bản sao model Site HQV, **người dùng chưa duyệt** (`Cần xác nhận lại`); chưa có nút bấm cho
model thật.

## Các bước

1. `tach_region.py <dxf> <regions.dxf> <regions.json>`: tách mọi REGION / 3DSOLID / SURFACE (kể cả trong block) ra
   DXF riêng, mỗi đối tượng 1 layer `R<n>`, kèm ma trận. Lý do: ezdxf không đọc được ACIS dạng SAB, còn Core Console
   2027 văng khi mở thẳng file DXF gốc (cả `/i` lẫn `DXFIN`).
2. Core Console nổ file đó: `accoreconsole /i regions.dxf /s no_region.scr /product ACAD /l en-US`. Script EXPLODE 4
   lần rồi DXFOUT; đường dẫn ra đang ghi cứng `_tmp\ct_cua_legend\acc\regions2_no.dxf`, đổi trước khi dùng.
3. `trich_xuat.py <dxf> <regions_no.dxf> <regions.json> <ct_cua.json>`: duyệt bản vẽ theo thứ tự vẽ (draworder), nổ
   block (giải ByLayer / ByBlock), tách ô theo khung `A_Symbol`. Gộp các tờ có ô rộng đủ 1 tờ, bỏ ô rỗng.
   - Gộp nét thẳng hàng chồng nhau; nét khác kiểu chồng nhau thì nét đậm thắng. Gộp cung cùng tâm và bán kính.
   - Hatch → vòng biên + định nghĩa mẫu CAD; kèm biên dự phòng (tô chẵn lẻ, nắn tự cắt, mỗi mảnh 1 vùng).
   - Wipeout → vùng che trắng. Chữ neo giữa chiều cao. Dim tuyến tính → điểm đo + chữ / tiền tố / hậu tố CAD.
4. `ve_legend.py` (CPython pyRevit, `locale` "C" ở đầu): nhân bản 1 legend có sẵn thành `CHI TIẾT CỬA (CAD)`, tỉ lệ
   1:20. Không xoá, không sửa kiểu có sẵn; kiểu trùng tên thì dùng lại.
   - Nét → `<Thin / Medium / Wide / Hidden Lines>` / `<Centerline>` theo lineweight + linetype CAD.
   - Hatch → fill pattern **Model** `CTC_<mẫu> [mã]` dựng đúng đường mẫu CAD, kèm kiểu filled region cùng tên; hatch
     đặc giữ màu; viền `<Invisible lines>`.
   - Chữ → `CTC_Arial 2.5 / 3.5 / 5mm`. Chữ CAD < 1 mm giấy bị bỏ và ghi vào log (22 chữ trong block rèm cuốn).
   - Dim → `CTC_Dim 2.5mm`, bám vào nét CAD thật cùng vị trí theo phương đo; không có nét thì bám 1 nét phụ
     `<Invisible lines>`. Chữ khác số Revit đo thì ghi đè.
   - Mỗi ô 1 group `CTC_<mã ô>`. Phần tử Revit không cho vào group thì dò bằng SubTransaction rồi loại riêng.
   - Biến môi trường: `ARV_CTC_JSON`, `ARV_CTC_LOG`, `ARV_CTC_ANH` (xuất PNG), `ARV_CTC_CHI` (tên ô, cách nhau `|`),
     `ARV_CTC_TEN` (tên legend), `ARV_CTC_LUU=1` (lưu file, chỉ dùng cho bản sao).
5. Thử nền: `thu_ve.py` đọc `thu_cfg.txt` rồi chạy `ve_legend.py`, gọi qua
   `_tmp\ho_so_duyet\chay_nen.ps1 -Journal _tmp\ct_cua_legend\journal.txt`. `bo_nap_link.py` đặt link của bản sao về
   không nạp, vì link trên ổ A: lỗi làm Revit không mở được bản sao. `xem_json.py` vẽ lại 1 ô từ json để so với CAD.

## Kết quả thử 2026-11-13 (bản sao Site HQV, `_tmp\ct_cua_legend\duyet_20261113\`)

- 25 ô / 25 group: 66.058 nét (gốc 102.765 trước khi gộp), 9.037 cung, 1.237 / 1.254 hatch, 54 vùng che, 1.002 chữ,
  537 dim.
- Kiểu tạo mới: 118 kiểu filled region + fill pattern, 3 kiểu chữ, 1 kiểu dim.
- Thời gian khoảng 12 phút, phần lớn là Revit commit + tạo group (ô DCA01 7.376 phần tử ~3 phút).
- Còn **17 hatch lỗi biên** (Revit báo vòng không hợp lệ). Số lỗi theo từng bản:
  - Bản ngưỡng đoạn ngắn 0,8 mm: DF02 không lỗi.
  - Nâng ngưỡng lên 1,0 mm: DFX / DF02 mỗi ô mới lỗi 2 hatch; RÈM / SA bớt lỗi.
  - Chưa sửa (`Cần xác nhận lại`).
- Bỏ qua: 2 OLE2FRAME (bảng nhúng, layer `CDC-KT-vat lieu`), 22 chữ quá nhỏ, 3 ô chỉ có khung.
- Ngoài ô: 3 nét + 3 chữ.

## Còn làm

- Sửa 17 hatch lỗi.
- Người dùng duyệt ảnh.
- Làm nút pyRevit (extension riêng) để người dùng bấm trên model thật. Revit API không tạo legend từ đầu, nên model
  phải có sẵn ít nhất 1 legend.
