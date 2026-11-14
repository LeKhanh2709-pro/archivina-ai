# CAD → legend 2D Revit (chi tiết cửa)

Làm 2026-11-13 theo yêu cầu người dùng: vẽ các ô chi tiết của `CT Cua khanh.dxf` thành **legend 2D** trong Revit.
Hatch → **Filled Region**, nét trùng chỉ giữ **1 nét**, **mỗi ô chi tiết 1 detail group**. Người dùng chốt thêm:
**1 kiểu chữ** (Arial, chỉ 3 cỡ 2,5 / 3,5 / 5 mm) và **1 kiểu dim** (`CTC_Dim 2.5mm`). Hệ số rộng chữ do Claude chọn:
bản đầu 1,0; từ tối 2026-11-13 là **0,8** (chữ CAD 73 % rộng 0,8) cho cả kiểu chữ và kiểu dim, đổi bằng `ARV_CTC_RONG_CHU`.

Trạng thái (2026-11-14): bản sửa chạy trên bản sao sạch model Site HQV đủ 25 ô, 0 lỗi; **người dùng chưa duyệt**
(`Cần xác nhận lại`); chưa có nút bấm cho model thật.

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
   - Chữ của MULTILEADER lấy nguyên 1 MTEXT (`ezdxf.render.mleader.make_mtext`), không lấy các TEXT ezdxf nổ ra: ezdxf
     tách chữ theo từng đoạn định dạng (đổi font giữa các chữ có dấu), vị trí tính theo font CAD → sang Revit các mảnh hở /
     đè nhau ("Tay ch ống"). Bề rộng khung của multileader bỏ qua (không bó dòng).
   - Mã Unicode kiểu AutoCAD còn nằm nguyên trong chuỗi (`\U+1EEC` = Ử) được giải thành ký tự thật (ezdxf không giải mã
     này với DXF lưu UTF-8; bản đầu vẽ ra "TAY CO ÂM C\U+1EECA" ở 16 nhãn của 4 ô cửa gỗ / CCN).
   - MTEXT có căn lề riêng của đoạn (`\pxql;` / `\pxqc;`…) khác điểm neo: căn theo đoạn, điểm neo dời tới mép / tâm khung
     (6 đoạn: khối GHI CHÚ ô CCN neo giữa nhưng căn trái, tiêu đề CHI TIẾT A / B neo trái nhưng căn giữa).
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

## Kết quả bản sửa 2026-11-13 tối / 14 sáng (bản sao SẠCH Site HQV `_tmp\ct_cua_legend\rvt_sach4\Site.rvt`)

- 25 ô / 25 group, **0 lỗi** ở mọi loại: 66.058 nét (gốc 102.765 trước khi gộp), 9.037 cung, 1.225 hatch, 91 vùng che
  (54 wipeout + 37 nền che chữ của multileader), 954 chữ, 537 dim. Log `kq\thu16_log.txt`.
- Hatch vẽ bằng biên dự phòng: 63 / 1.225 (mức 0 nắn biên 37, mức 1 nở 0,25 mm 25, mức 2 nở 0,5 mm 1; không vùng nào
  phải dùng hình bao). 8 hatch 1 × 1 mm trước đây bị bỏ hẳn nay được vẽ.
- Dim: 456 / 537 bám ít nhất 1 nét CAD thật, 305 nét phụ 2 mm; 94 dim ghi đè chữ theo CAD (chữ CAD không phải số đo
  thuần); 1 dim Revit đo lệch CAD > 0,6 mm (chữ hiện vẫn theo CAD, chưa tra là dim nào, `Cần xác nhận lại`).
- Chữ: 35 đoạn xuống dòng theo khung CAD; 160 multileader mỗi cái 1 khối chữ. Đã soi ảnh từng ô 11 / 25 ô, trong đó đối
  chiếu với ảnh CAD dựng bằng ezdxf ở 4 ô (DF02, rèm ngăn cháy, CCN 6400, cửa chống ngập hầm); 14 ô cửa còn lại cùng
  khuôn với DF02 / DW04, chưa soi từng ô.
- Kiểu tạo mới: 116 kiểu filled region + fill pattern, 3 kiểu chữ, 1 kiểu dim (đều hệ số rộng 0,8).
- Thời gian 12 – 20 phút tuỳ máy đang bận gì, phần lớn là Revit commit + tạo group (ô DCA01 ~3 phút).
- Bỏ qua: 2 OLE2FRAME (bảng nhúng, layer `CDC-KT-vat lieu`), 22 chữ quá nhỏ, 3 ô chỉ có khung, nền che của 2 MTEXT
  thường (chưa vẽ). Ngoài ô: 3 nét + 3 chữ.
- Chưa xử lý: hatch đặc của hình vẽ giữ màu CAD (thép xanh dương, mũi tên ký hiệu mặt cắt xanh lá) – chờ người dùng
  quyết có đổi hết sang đen / xám không; 1 kiểu dim 2,5 mm nên dim CAD chữ to (ô rèm ngăn cháy) thành chữ nhỏ.
- Ảnh gửi duyệt: `_tmp\ct_cua_legend\duyet_20261114\` (bản cuối). Thư mục `duyet_20261113\` là các bản trước: 01 – 06
  bản thử chiều 13/11 (17 hatch lỗi, dim xiên, ô đen), 07 – 10 bản tối 13/11 (còn lỗi chữ multileader tách mảnh).

### Các bản trước (để đối chiếu)

- Bản thử chiều 13/11 (`rvt\Site.rvt`, `duyet_20261113\06_*.rvt`): 1.237 / 1.254 hatch, 17 hatch lỗi biên, chữ rộng 1,
  dim bám đầu mút (xiên), nền che multileader thành ô đen, 118 kiểu hatch mã ngẫu nhiên.
- `rvt_sach\Site.rvt`: bản 21:09 (hết lỗi hatch + dim thẳng + nền che trắng, chữ còn rộng 1).
  `rvt_sach2\Site.rvt`: bản 21:53 (thêm chữ rộng 0,8 + mũi tên đen, chữ multileader còn tách mảnh).
  `rvt_sach3\Site.rvt`: bản 14/11 08:33 (chữ multileader đã liền khối, còn mã `\U+` và căn lề đoạn sai).

## Còn làm

- Người dùng chốt 2026-11-14: **không cần làm nút pyRevit**, chỉ lấy file `.rvt` đã làm
  (`duyet_20261114\05_Site_legend_CT_cua.rvt`). File cửa không còn việc dở.
- **File thứ 2 `ctchung.dxf` (chi tiết chống thấm, chống mối): XONG 2026-11-14 15:00**, bàn giao
  `_tmp\ct_chung_legend\duyet_20261114\` (`01_*.rvt` có 7 legend chi tiết chung + legend cửa vẽ lại, ảnh, so sánh với bản
  in AutoCAD từng ô, `05_DOC_TRUOC.txt`). 8 legend 0 lỗi; người dùng chưa duyệt (`Cần xác nhận lại`).
- Bản nhiều tờ (từ 2026-11-14, bộ script này đã có):
  - `tao_o_cfg.py` → `o_cfg.json` (`to`: mã / tỉ lệ / tên legend, `o`: tờ / tên / khung ô). Mẫu: `vd_o_cfg_ctchung.json`.
    `trich_xuat.py <dxf> <regions_no.dxf> <regions.json> <ra.json> [o_cfg.json]`: có cấu hình thì mỗi ô mang tỉ lệ tờ,
    toạ độ tính từ góc trái trên của tờ, nét trên ranh chung bên phải / trên chỉ thuộc 1 ô. Không có cấu hình = cách cũ.
  - `ve_chung.py` (chạy qua nút thử, đọc `ve_cfg.txt`, mẫu `vd_ve_cfg.txt`): mỗi tờ 1 legend đúng tỉ lệ, `KHAC=` vẽ thêm
    1 legend từ json khác, `LUU=1` lưu file. Ghi nhịp từng ô vào `tong.txt` (bộ chạy nền dừng phiên khi 10 phút không
    có dòng `=== ` mới; legend cửa 25 ô mất ~13 phút).
  - `ma_chu.py`: đổi TCVN3 / VNI theo font từng đoạn (cả `\f` giữa MTEXT), font chữ HOA thì viết hoa, chữ TCVN3 gán font
    Unicode nhận theo nội dung.
  - `tao_plot_o.py` (Core Console in từng ô ra PNG đơn sắc) + `so_o.py <KQ>` (ghép ảnh AutoCAD – Revit từng ô).
  - Sửa chung (ảnh hưởng cả file cửa): cung / elip biên hatch chiều kim đồng hồ (ezdxf đã lưu góc ngược chiều, code cũ
    lật lần nữa); polyline có bề rộng ≥ 0,2 mm giấy → vùng đặc; nét đứt chu kỳ < 0,05 mm giấy → nét liền; mẫu hatch
    trong block xoay / co theo block; mẫu quá dày (< 0,12 mm giấy) → đặc; chấm mẫu = 0,2 mm giấy; MTEXT thụt lề đoạn
    (`\pxi` bội chiều cao chữ, `\pi` không `x` = đơn vị bản vẽ, đã kiểm bằng bản in AutoCAD); bỏ layer không in;
    hatch kiểu Outer / Ignore. Cỡ chữ đổi bằng `ARV_CTC_CO_CHU` (ctchung: thêm cỡ 2,0 mm).
- Gói mang đi: `_dist\CAD_Legend_20261114\` + `.zip` (làm TRƯỚC các sửa ở trên: kết quả file cửa cũ, bộ script cũ).
- Nếu sau này cần chạy cho file CAD khác hoặc làm nút: Revit API không tạo legend từ đầu, nên model phải có sẵn ít
  nhất 1 legend; máy khác cần Python có ezdxf + shapely (gói `_tools\CHONGTHAM_python` có đủ) và AutoCAD Core Console
  cho bước nổ REGION.