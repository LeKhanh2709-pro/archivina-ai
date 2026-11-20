# G19 Side – Chống thấm bo vào tường thô (lượt 1: nút Chống thấm) – 2026-11-19 tối

Người dùng (ảnh 1 WC, 2026-11-19 tối): "đường bo chống thấm vẫn còn bo sai nhiều, thực hiện lại ở các tầng (phải bo cả vào
lớp trát của tường, bo vào lớp tường thô). thực hiện lại chống thấm các tầng cho t và fix lỗi".

Đây là **lượt 1** theo quy tắc mới (mỗi lượt 1 nút, duyệt đúng mới sang nút sau): chỉ chạy lại nút **Chống thấm**.

## File bàn giao
| Số | File | Ghi chú |
|---|---|---|
| 44 | `44_G19_A_Side_chong_tham_tuong_tho.rvt` | = `rvt\60_ct_cua.rvt` (chi tiết vách kính / cửa bản v6) + chống thấm vẽ lại 4 tầng. CHƯA có ngăn cháy lan, lan can louver vẽ lại (làm ở lượt 2, 4 sau khi lượt này được duyệt). Mở bằng Detach from Central. |
| 45 | `45_anh_chong_tham_tuong_tho\A_TC-20-01 … 04.png` | ảnh 4 tờ chống thấm |
| 45 | `45_anh_chong_tham_tuong_tho\so_01 … so_05_*.png` | hình so TRƯỚC (v6) / SAU từng WC: tường link theo lớp (cam = trát, xám = tường thô), đường bo hatch (xanh), nét vén (hồng); cạnh sai tô đỏ / cam |
| 46 | file này | |

## Nguyên nhân (soi trên bản v6, `lan\65_soi_tuong_chong_tham`, `lan\66_soi_tuong_toa_do`)
Mỗi cạnh biên hatch được so với các lớp của tường link song song gần nhất. Tầng 3 (tầng 4-32 giống hệt): 428 cạnh, 33 cạnh
còn nằm trên lớp trát (chưa phủ trát), 1 cạnh lấn vào tường; tầng 1: 1 cạnh lồi 70 mm + 1 cạnh lấn.
1. **Chỗ vách ngăn nối chữ T vào tường WC**: dải tường của vách được kéo dài thêm NỬA BỀ DÀY CẢ TƯỜNG kia (gồm lớp trát)
   → xuyên qua lớp trát, đường bo lồi vào WC 7 – 15 mm (tầng 1: tường 230 mm → lồi 70 mm).
2. **2 tường thẳng hàng lệch mặt thô** (một bên có trát, một bên không): đường bo đi 1 đường thẳng theo mặt tường đầu.
3. Dải chặn khi quét lấy theo ranh giới LÕI khai trong kiểu tường – đúng với kiểu tường G19 (lớp trát nằm ngoài lõi) nhưng
   sai với kiểu khai lớp trát trong lõi.

## Sửa nút Chống thấm (`scripts\dynamo\ChongTham_VeVenChanTuong.py`, nút sinh lại 2026-11-19 ~20:45)
1. Dải chặn = các **lớp thô** của tường (bỏ lớp Finish1 / Finish2 / Membrane và lớp vật liệu tên có trát / plaster / ốp
   lát), không theo ranh giới lõi; tường chỉ có lớp trát / ốp (tường trát vẽ riêng) không chặn.
2. Chỗ nối tường: chỉ kéo dải tới **mặt thô xa** của tường kia (không qua lớp trát của nó); nối thẳng hàng kéo nửa ô lưới.
3. Mỗi cạnh bo bám **từng đoạn** mặt thô gần nhất (trong 1 ô lưới 20 mm), đổi mặt thì có bậc.
Bản trước: `_backup\ChongTham_VeVenChanTuong_20261119_2024_truoc_tuong_tho.py` (+ thư mục nút).

## Kết quả (phiên 70, 71 từ `rvt\60_ct_cua.rvt`)
| Tờ | Tầng | Phòng ướt | Nét vén | Diện tích | Kiểm tra |
|---|---|---|---|---|---|
| A_TC.20.01 | TẦNG 1 | 5 WC | 30 đoạn | 24,2 m² | ĐẠT |
| A_TC.20.02 | TẦNG 2 | 0 (không có thiết bị vệ sinh) | 0 | – | ĐẠT |
| A_TC.20.03 | TẦNG 3 | 32 WC + 27 lô gia | 430 đoạn | 210,0 m² | ĐẠT |
| A_TC.20.04 | TẦNG 4-32 | 32 WC + 27 lô gia | 430 đoạn | 210,0 m² | ĐẠT |
(v6: 32 / 476 / 476 đoạn; nét vén ít hơn vì các chỗ lồi đã hết.)

Soi lại từng cạnh (phiên 72):
| | Tầng 1 trước → sau | Tầng 3 trước → sau |
|---|---|---|
| Cạnh đúng mặt tường thô | 24 → 23 | 276 → 292 |
| Cạnh còn trên lớp trát / lồi | 1 → 0 | 33 → 6 |
| Cạnh lấn vào tường | 1 → 0 | 1 → 0 |
| Không có tường song song (mép cột KC, vách kính, lan can, lam) | 6 → 3 | 85 → 76 |

6 cạnh tầng 3 còn lại:
- 4 cạnh dài 900 mm ở đáy / đỉnh 4 WC cùng kiểu (tâm WC (50 483, 8 543), (50 483, 23 007), (12 117, 8 543),
  (12 117, 23 007)): đường bo đã ở đúng mặt thô tường WB 15-95 (vd. y = 7 950); script soi so nhầm với tường kế bên –
  **không phải lỗi**.
- 2 dải 144 × 50 mm ở góc vách bê tông KC tại (44 155 – 44 300, 21 750 – 21 800) và (18 300 – 18 445, 21 750 – 21 800)
  chưa phủ hatch (có từ bản v6, nguyên nhân chưa rõ – có thể do vách kính / đối tượng ở cạnh trái WC) – `Cần xác nhận lại`.

## Chưa làm / cần người dùng
- Người dùng chưa xem, chưa duyệt lượt này (`Cần xác nhận lại`). Duyệt đúng → lượt 2 **Ngăn cháy lan**.
- Ảnh người dùng gửi: Claude chưa tìm được đúng WC đó trong bản v6 (ở góc hộp kỹ thuật, nét vén cách đường bo khoảng
  100 mm, chỗ khác 50 mm) – nếu WC đó vẫn sai thì cần biết tầng / vị trí.
- Revit đang mở phải Reload pyRevit mới dùng nút Chống thấm bản mới. Nút không vẽ lại view đã có nét vén: muốn vẽ lại trên
  model thật thì xoá group `ARV_ChongTham_Ven*` / `ARV_ChongTham_Hatch*` cũ trước (công cụ không tự xoá).
- Hướng nhận phòng theo room (CoreBoundary) chưa đổi – model có room khép kín thì biên vẫn theo lõi khai của kiểu tường.
