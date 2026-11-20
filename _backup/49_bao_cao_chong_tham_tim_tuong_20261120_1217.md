# G19 Side – Chống thấm bo vào tường thô, bản sửa 2 (lượt 1: nút Chống thấm) – 2026-11-20 sáng

Người dùng (ảnh WC góc hộp kỹ thuật, nét đỏ vẽ tay, 2026-11-20): "còn sai rất nhiều, phải bo như nét đỏ. rất nhiều vị trí
chưa bo vào lớp tường thô". Bản 44 – 46 (tối 19/11) vẫn sai – báo cáo 46 ghi "tầng 1 0 cạnh sai" là SAI, xem mục Nguyên nhân.

## File bàn giao
| Số | File | Ghi chú |
|---|---|---|
| 47 | `47_G19_A_Side_chong_tham_tim_tuong.rvt` | = `rvt\60_ct_cua.rvt` + chống thấm vẽ lại 4 tầng bằng nút đã sửa. Chưa có ngăn cháy lan / lan can louver vẽ lại (lượt 2, 4). Mở bằng Detach from Central. Thay cho file 44. |
| 48 | `48_anh_chong_tham_tim_tuong\A_TC-20-01 … 04.png` | ảnh 4 tờ |
| 48 | `48_anh_chong_tham_tim_tuong\so_01 … so_07_*.png` | so TRƯỚC (file 44) / SAU: tường link theo lớp (cam = trát, xám = tường thô) đặt theo MẶT KHỐI THẬT, đường bo (xanh), nét vén (hồng); cạnh sai tô đỏ / cam kèm số mm lệch |
| 49 | file này | |

## Nguyên cái sai
- `Location.Curve` của tường mà API trả về **luôn là tim tường**, không theo tham số Location Line. Kiểm bằng mặt khối thật
  của 454 tường quanh các WC tầng 1 + 3 (`lan\74_soi_tuong_hinh`): mọi tường đối xứng ±W/2 quanh đường này, kể cả tường đặt
  Location Line = Core Face Interior / Exterior / Core Centerline.
- Nút cũ dời dải tường thô theo Location Line → dải lệch tới nửa bề dày tường (WB 15-95 đặt theo mặt lõi: 55 mm; tường
  KC 300 – 400: 150 – 200 mm) → đường bo dừng trước mặt tường thô, có chỗ lấn vào tường.
- Các script soi tối 19/11 dùng CÙNG công thức đó nên báo "đúng" – không phát hiện được. Nay script soi đặt tường theo mặt khối
  thật (`viec\soi_tuong_chong_tham_2.py` đã sửa) và kiểm riêng phía mặt ngoài (`lan\78_soi_mat_ngoai`: 160 / 160 tường mặt ngoài
  thật ở phía +Orientation = đúng giả định lớp trát của lõi).

Soi lại file 44 bằng mặt khối thật (`lan\79_soi_ban_44_theo_hinh_that`): tầng 1 – 0 / 21 cạnh đúng (13 cạnh chưa phủ trát,
8 lấn vào tường); tầng 3 – 182 cạnh đúng, 112 chưa phủ trát, 4 lấn.

## Sửa nút Chống thấm (`scripts\dynamo\ChongTham_VeVenChanTuong.py`, `q_loi_tuong`; nút sinh lại 2026-11-20 08:47)
- Dải tường thô tính từ **tim tường** (Location.Curve), bỏ dời theo Location Line. Giữ các sửa tối 19/11 (dải = lớp thô, bỏ
  trát / ốp; nối tường tới mặt thô xa; cạnh bám từng đoạn mặt thô).
- Thêm biến môi trường thử `ARV_DUMP_VAT_CHAN` (thư mục): ghi mọi vật chặn khi quét + biên phòng ra JSON (chỉ để kiểm,
  `viec\ve_vat_chan.py` vẽ hình).
- Bản trước: `_backup\ChongTham_VeVenChanTuong_20261119_2024_truoc_tuong_tho.py` (trước cả 2 lần sửa).

## Kết quả (phiên 75, 76 từ `rvt\60_ct_cua.rvt`)
| Tờ | Tầng | Phòng ướt | Nét vén | Diện tích | Kiểm tra |
|---|---|---|---|---|---|
| A_TC.20.01 | TẦNG 1 | 5 WC | 30 đoạn | 25,7 m² (file 44: 24,2) | ĐẠT |
| A_TC.20.02 | TẦNG 2 | 0 | 0 | – | ĐẠT |
| A_TC.20.03 | TẦNG 3 | 32 WC + 27 lô gia | 424 đoạn | 212,0 m² (file 44: 210,0) | ĐẠT |
| A_TC.20.04 | TẦNG 4-32 | 32 WC + 27 lô gia | 424 đoạn | 212,0 m² | ĐẠT |

Soi theo mặt khối thật (phiên 77): tầng 1 – 23 / 23 cạnh có tường song song nằm đúng mặt tường thô (2 cạnh giáp cột KC);
tầng 3 – 291 cạnh đúng, 2 cạnh còn lệch: 2 dải 144 × 50 mm ở góc vách bê tông KC (44 155 – 44 300, 21 750 – 21 800) và đối
xứng (18 300 – 18 445) – có từ v6, do ô nối đầu tường hở, `Cần xác nhận lại`. 75 cạnh không có tường song song = mép lô gia
theo lan can / lam thép / vách kính (đúng cách nhận lô gia).

## Còn lại
- Người dùng chưa xem, chưa duyệt (`Cần xác nhận lại`). Duyệt đúng → lượt 2 Ngăn cháy lan.
- **Nút Ngăn cháy lan và Lỗ mở shaft có CÙNG công thức sai** (`NganChay_TrucHKT.py`, `LoMo_ShaftOpening.py`: dời dải lõi theo
  Location Line) → hatch trục / hộp kỹ thuật cũng có thể lệch ở tường đặt Location Line ≠ tim. Chưa sửa (lượt 2).
- Revit đang mở phải Reload pyRevit mới dùng nút mới; view đã có nét vén thì nút không vẽ lại (xoá group
  `ARV_ChongTham_Ven*` / `ARV_ChongTham_Hatch*` cũ trước).
- Hướng nhận phòng theo room (CoreBoundary) không đổi (Revit tự tính biên lõi).
