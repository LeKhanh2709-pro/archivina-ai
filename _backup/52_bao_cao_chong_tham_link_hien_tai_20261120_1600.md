# G19 Side – Chống thấm, bản sửa 3: link kiến trúc hiện tại + gờ lô gia (lượt 1: nút Chống thấm) – 2026-11-20 trưa

Người dùng (2 ảnh WC tầng 1 trên file 47, WC (12 225, 22 774) và WC (40 579, 13 006) có khoanh đỏ cạnh trái): "tầng 1 còn sai
nhiều", rồi "tiếp tục sửa tầng 1". Bản 47 – 49 sáng nay thay bằng bản này.

## File bàn giao
| Số | File | Ghi chú |
|---|---|---|
| 50 | `50_G19_A_Side_chong_tham_link_hien_tai.rvt` | = `rvt\60_ct_cua.rvt` + chống thấm vẽ lại 4 tầng bằng nút đã sửa, link kiến trúc `G19_A_B2-L2` là bản chép từ ổ A: lúc 20/11 11:19 (đặt lại Mark vách kính, `rvt\82_G19_A_B2-L2_20261120_mark_VK.rvt`). Chưa có ngăn cháy lan / lan can louver vẽ lại (lượt 2, 4). Mở bằng Detach from Central. Thay cho file 47. |
| 51 | `51_anh_chong_tham_link_hien_tai\A_TC-20-01 … 04.png` | ảnh 4 tờ |
| 51 | `51_anh_chong_tham_link_hien_tai\so_tang1_*.png` (5), `so_tang3_*.png` (25) | so TRƯỚC (file 47 đo với link hiện tại) / SAU, vẽ từ chính nét Revit xuất DXF: đen = nét tường thô (A-WALL / kết cấu), cam = trát / ốp (A-WALL-FNSH), xanh = đường bo đúng, cam đậm / đỏ = hụt / lấn kèm số mm |
| 52 | file này | |

## Nguyên nhân
1. **Tầng 1 – link kiến trúc đã cũ.** Các phiên chạy nút dùng bản chép `G19_A_B2-L2.rvt` ngày 16/11 (chép để đặt Mark vách kính);
   bản trên ổ A: KTS sửa tiếp tới 20/11 11:19. Trong ảnh người dùng, nét bê tông (link kết cấu nạp thẳng ổ A:) trùng file 47, còn
   nét tường kiến trúc lệch 30 – 45 mm: tường WC (12 225, 22 774) dời / mỏng đi, vách giữa 2 WC (40 579, 13 006) mỏng đi 30 mm.
   Vách kính tầng 1 cũng đổi dài (5 850 → 5 800, 6 150 → 6 300, 1 450 → 1 300 …). Đo file 47 với link hiện tại: tầng 1 sai
   4 / 5 WC (hụt 11,0 m cạnh, lấn 5,5 m). Tầng 3 / 4-32 dùng link ổ A: trực tiếp nên không dính lỗi này.
2. **Tầng 3 / 4-32 – mép lô gia (có từ trước, bộ soi mới mới bắt được).** Dưới lan can / lam thép có gờ bê tông `VBT-120` cao
   150 mm (27 gờ mỗi tầng, không gờ nào trong WC). Nút chỉ lấy tường cắt qua sàn + 1 000 mm nên bỏ gờ, đường bo bám lan can / khung
   lam: lấn 30 – 45 mm vào gờ, hoặc hụt 86 mm trước gờ khi khung bao lam thò vào trong mặt gờ (tầng 3: 25 / 59 phòng có đoạn
   sai, 15 lô gia còn hụt 86 mm sau khi đã thêm gờ).
3. **Góc vách bê tông (2 dải 144 × 50 mm có từ bản v6).** Đầu tường gạch `WB 150_ST` đã chạm kín vách KC, dải gạch cao hơn mặt
   vách 50 mm; phần "nối đầu tường hở" vẫn kéo dải gạch băng qua vách → thò vào lô gia thành dải không hatch.

## Sửa nút Chống thấm (`scripts\dynamo\ChongTham_VeVenChanTuong.py`, `QuetTuong`; nút sinh lại 2026-11-20 12:16, `.dyn` chưa sinh lại)
- Tường đứng trên sàn (đáy ≤ sàn + 200, đỉnh ≥ sàn + 100 mm) thấp hơn mặt cắt quét cũng là tường thô chặn biên
  (`QUET_TUONG_THAP_MIN_MM`).
- Cửa / lam đặt rời có tâm khung bao nằm trên dải thô của tường / gờ thì không lấy khung bao làm vật chặn (`tren_tuong_tho`).
- Đầu tường đã chạm kín vật chặn trên cả bề rộng dải thì không coi là đầu hở, không nối tiếp.
- Bản trước: `_backup\ChongTham_VeVenChanTuong_20261120_1143_truoc_tuong_thap.py` (+ thư mục nút).

## Kết quả (phiên 94, 95 từ `rvt\60_ct_cua.rvt`, link `rvt\82_*`)
| Tờ | Tầng | Phòng ướt | Nét vén | Diện tích | Kiểm tra tờ |
|---|---|---|---|---|---|
| A_TC.20.01 | TẦNG 1 | 5 WC | 30 đoạn | 25,8 m² (file 47: 25,7) | ĐẠT |
| A_TC.20.02 | TẦNG 2 | 0 | 0 | – | ĐẠT |
| A_TC.20.03 | TẦNG 3 | 32 WC + 27 lô gia | 406 đoạn | 212,7 m² (file 47: 212,0) | ĐẠT |
| A_TC.20.04 | TẦNG 4-32 | 32 WC + 27 lô gia | 406 đoạn | 212,7 m² | ĐẠT |

Soi bằng nét Revit vẽ (phiên 96: DXF view chống thấm, `viec\soi_dxf_chong_tham.py`, xét mỗi 25 mm cạnh):
| | Tầng 1 | Tầng 3 | Tầng 4-32 |
|---|---|---|---|
| Cạnh nằm đúng mặt tường thô / gờ / kết cấu | 42,1 m | 417,4 m | 417,4 m |
| Cạnh hụt / lấn | 0 | 0 | 0 |
| Cạnh không có tường (ô cửa đi, cửa trượt lô gia) | 4,7 m | 77,2 m | 77,2 m |
Trước khi sửa (file 47 đo với link hiện tại): tầng 1 hụt 11,0 m + lấn 5,5 m; tầng 3 hụt 25,3 m + lấn 47,9 m (25 / 59 phòng).

## Còn lại
- Người dùng chưa xem, chưa duyệt (`Cần xác nhận lại`). Duyệt đúng → lượt 2 Ngăn cháy lan.
- Link kiến trúc trong file 50 là bản chép 20/11 11:19 trên D:. KTS còn sửa tiếp trên ổ A: thì bấm nút trên model thật (link ổ A:)
  sẽ theo tường mới – vẽ trên bản chép này rồi chép sang thì lại lệch như file 47.
- Số Mark vách kính tầng 1 trên link mới dịch 1 số so với bản 16/11 (vách 3284785 nay dài 7 000 = giống VKT1-01 nên dùng chung tên;
  VKT1-03 cũ → VKT1-02 …): tờ chi tiết vách kính trong file 50 (vẽ từ v6) lệch tên với tag mới → làm lại ở lượt 3 (định vị cửa +
  chi tiết cửa).
- Nút Ngăn cháy lan + Lỗ mở shaft vẫn còn công thức dời theo Location Line (lượt 2), và chưa có 3 sửa ở trên.
- Revit đang mở phải Reload pyRevit mới dùng nút mới; view đã có nét vén thì nút không vẽ lại (xoá group `ARV_ChongTham_Ven*` /
  `ARV_ChongTham_Hatch*` cũ trước).
