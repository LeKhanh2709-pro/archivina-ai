# CAD → legend 2D Revit (chi tiết cửa)

Làm 2026-11-13 theo yêu cầu người dùng: vẽ các ô chi tiết của `CT Cua khanh.dxf` thành **legend 2D** trong Revit.
Hatch → **Filled Region**, nét trùng chỉ giữ **1 nét**, **mỗi ô chi tiết 1 detail group**. Người dùng chốt thêm:
**1 kiểu chữ** (Arial, chỉ 3 cỡ 2,5 / 3,5 / 5 mm) và **1 kiểu dim** (`CTC_Dim 2.5mm`). Hệ số rộng chữ do Claude chọn:
bản đầu 1,0; từ tối 2026-11-13 là **0,8** (chữ CAD 73 % rộng 0,8) cho cả kiểu chữ và kiểu dim, đổi bằng `ARV_CTC_RONG_CHU`.

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
   - Hatch → vòng biên + định nghĩa mẫu CAD. Mã mẫu `P<5 số>` tính bằng md5 nên giống nhau giữa các lần chạy (bản đầu
     dùng `hash()` của Python, mỗi lần chạy ra mã khác → chạy lại trên cùng model sinh thêm 118 kiểu hatch trùng hình).
   - Biên dự phòng của hatch (`du_phong`, sửa 2026-11-13 tối), dựng từ vòng biên THÔ (chưa lọc đoạn ngắn), 4 mức thử lần
     lượt trong Revit: (0) nắn biên: tô chẵn lẻ, bỏ tự cắt, mỗi mảnh 1 vùng; (1) nở 0,25 mm; (2) nở 0,5 mm; (3) hình chữ
     nhật bao, chỉ cho vùng nhỏ / mảnh. Lý do: Revit không nhận nét ngắn hơn 0,7804 mm (`ShortCurveTolerance`), vùng
     hatch hẹp hơn mức đó (dải 0,4 mm, ô 1 × 1 mm…) không vẽ nguyên hình được. Nở 0,5 mm = 0,025 mm trên giấy ở 1:20.
     Hatch không có diện tích trong CAD (< 0,01 mm²) thì bỏ, có in ra log.
   - Wipeout → vùng che trắng. Nền che chữ của MULTILEADER (background mask theo màu nền bản vẽ) cũng → vùng che trắng:
     ezdxf dựng nó thành 1 HATCH đặc màu đen, bản đầu vẽ thành ô đen đè lên ghi chú.
   - Mũi tên tô đặc của LEADER / MULTILEADER / dim nổ ra → màu đen (bản đầu giữ màu đối tượng: mũi tên xanh lá cạnh đường
     dẫn đen). Hatch đặc của hình vẽ vẫn giữ màu CAD.
   - Chữ neo giữa chiều cao; MTEXT có khung thì kèm bề rộng khung (`rong`). Dim tuyến tính → điểm đo + chữ / tiền tố /
     hậu tố CAD.
4. `ve_legend.py` (CPython pyRevit, `locale` "C" ở đầu): nhân bản 1 legend có sẵn thành `CHI TIẾT CỬA (CAD)`, tỉ lệ
   1:20. Không xoá, không sửa kiểu có sẵn; kiểu trùng tên thì dùng lại.
   - Nét → `<Thin / Medium / Wide / Hidden Lines>` / `<Centerline>` theo lineweight + linetype CAD.
   - Hatch → fill pattern **Model** `CTC_<mẫu> [mã]` dựng đúng đường mẫu CAD, kèm kiểu filled region cùng tên; hatch
     đặc giữ màu; viền `<Invisible lines>`.
   - Vùng Revit không nhận biên gốc: thử từng mức `du_phong`, lấy mức đầu tiên tạo được ĐỦ mọi mảnh (hỏng 1 mảnh thì
     hoàn tác cả mức bằng SubTransaction); log ghi số vùng theo mức và theo ô.
   - Chữ → `CTC_Arial 2.5 / 3.5 / 5mm`. Chữ CAD < 1 mm giấy bị bỏ và ghi vào log (22 chữ trong block rèm cuốn). Đoạn
     chữ MTEXT có khung mà nhiều dòng hoặc ≥ 40 ký tự thì xuống dòng trong bề rộng khung CAD + 3 % (không bó lại thì đoạn dài
     chạy tràn sang ô bên); nhãn ngắn 1 dòng giữ 1 dòng. Hệ số rộng 0,8: để 1,0 thì chữ dài hơn CAD ~25 %, nhãn đè lên
     đường dẫn, tên ô tràn khỏi khung, ghi chú đầu ô rớt chữ cuối xuống dòng.
   - Dim → `CTC_Dim 2.5mm`. Mỗi điểm đo bám 1 nét VUÔNG GÓC với phương đo: nét CAD thật đúng vị trí (sai ≤ 0,3 mm),
     không có thì 1 nét phụ `<Invisible lines>` dài 2 mm (0,1 mm trên giấy) đặt tại điểm đo. Sửa 2026-11-13 tối: bản đầu
     bám đầu mút nét / 2 đầu 1 nét phụ nối 2 điểm đo → 2 điểm lệch nhau là Revit vẽ dim XIÊN theo đường nối 2 điểm
     (thấy rõ ở ô cửa chống ngập). Chữ dim chỉ ghi đè khi Revit (sau `Regenerate`) hiện khác CAD.
   - Mỗi ô 1 group `CTC_<mã ô>`. Phần tử Revit không cho vào group thì dò bằng SubTransaction rồi loại riêng.
   - Biến môi trường: `ARV_CTC_JSON`, `ARV_CTC_LOG`, `ARV_CTC_ANH` (xuất PNG), `ARV_CTC_CHI` (tên ô, cách nhau `|`),
     `ARV_CTC_TEN` (tên legend), `ARV_CTC_LUU=1` (lưu file, chỉ dùng cho bản sao), `ARV_CTC_RONG_CHU` (mặc định 0.8),
     `ARV_CTC_PX` (bề rộng ảnh xuất, mặc định 12000), `ARV_CTC_KHONG_GROUP=1` (bỏ bước group, chỉ khi vẽ thử lấy ảnh).
5. Thử nền: `thu_ve.py` đọc `thu_cfg.txt` rồi chạy `ve_legend.py`, gọi qua
   `_tmp\ho_so_duyet\chay_nen.ps1 -Journal _tmp\ct_cua_legend\journal.txt`. `bo_nap_link.py` đặt link của bản sao về
   không nạp, vì link trên ổ A: lỗi làm Revit không mở được bản sao. `xem_json.py` vẽ lại 1 ô từ json để so với CAD.
   - `thu_hatch.py`: chỉ thử phần hatch (tạo mọi Filled Region trong 1 transaction rồi RollBack, ~50 giây, không ghi
     gì vào model), ghi vùng Revit từ chối ra `kq\hatch_loi.json`; `xem_hatch_loi.py` in số đo + vẽ ảnh các vùng đó.
   - `thu_anh_o.py`: ảnh TỪNG Ô để duyệt. Mỗi ô vẽ riêng vào 1 legend tạm (không group, 5 – 50 giây / ô) rồi xuất PNG
     6000 px (ô rộng cả tờ: 12000 px), phiên KHÔNG lưu. Legend không crop được; API không ẩn được Group, còn ẩn tạm
     ~77 nghìn phần tử thì quá 9 phút chưa xong (bản `xuat_anh_o.py` đã bỏ, nằm ở `_backup`). `ve_cad_o.py <tên ô>
     <ra.png>`: vẽ lại 1 ô từ CAD gốc bằng ezdxf để đối chiếu (nền che chữ hiện thành ô đen, REGION không hiện).
     `cat_anh.py` / `ghep_anh.py`: cắt, ghép ảnh so sánh.
   - Bản sao để chạy bản cuối phải SẠCH (chưa có kiểu `CTC_*`): kiểu trùng tên được dùng lại nên bản sao đã chạy bản cũ
     vẫn giữ chữ rộng 1 và mã mẫu hatch cũ.
   - Bẫy: script chạy qua nút thử phải là UTF-8 KHÔNG BOM. PowerShell 5.1 `Set-Content -Encoding UTF8` ghi có BOM →
     `compile()` báo lỗi trong cửa sổ pyRevit, phiên chờ tới hết giờ. Ghi bằng `[IO.File]::WriteAllText(...,
     UTF8Encoding($false))`.

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
