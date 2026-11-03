# Ma trận LOD – Kiến trúc & Kết cấu nhà cao tầng

> Đây là mức tham chiếu nội bộ. BEP dự án được ưu tiên áp dụng. Ô ghi *[cần xác nhận]* phải được BIM Manager chốt.

| Giai đoạn | LOD |
|---|---|
| Lập dự án / Concept | 100 |
| TKCS | 200 |
| TKKT | 300 |
| TKBVTC | 350 |

> LOD 100 (Concept): mô hình khối, diện tích và chiều cao tổng. Áp dụng chung cho mọi cấu kiện, không tách yêu cầu riêng.

## Kiến trúc (A)

| Cấu kiện | LOD 200 (TKCS) | LOD 300 (TKKT) | LOD 350 (TKBVTC) |
|---|---|---|---|
| Tường | Chiều dày tổng gần đúng | Chiều dày lớp đúng, loại tường đúng | Lớp hoàn thiện, liên kết với kết cấu, lỗ mở chính xác |
| Sàn hoàn thiện | Khối sàn tổng | Lớp hoàn thiện theo phòng | Độ dốc, giật cấp, khe |
| Cửa đi / cửa sổ | Kích thước gần đúng | Kích thước, loại, hướng mở đúng | Khuôn, phụ kiện, mã cửa đầy đủ |
| Vách kính / mặt dựng | Mặt phẳng tổng | Lưới đố, panel đúng | Như LOD 300; không mô hình liên kết neo và chi tiết đố |
| Thang bộ, lan can | Khối thang | Kích thước bậc, chiếu nghỉ đúng | Lan can, tay vịn chi tiết |
| Phòng (Room) | Ranh giới, tên | Diện tích, mã phòng, hoàn thiện | Đầy đủ parameter hoàn thiện |
| Trần | Không bắt buộc | Cao độ, loại trần | Lỗ thăm, giật cấp |

## Kết cấu (S)

| Cấu kiện | LOD 200 (TKCS) | LOD 300 (TKKT) | LOD 350 (TKBVTC) |
|---|---|---|---|
| Cột, vách | Tiết diện sơ bộ | Tiết diện, vị trí, mác bê tông đúng | Thay đổi tiết diện theo tầng, lỗ mở, liên kết |
| Dầm | Tiết diện sơ bộ | Tiết diện, cao độ đúng | Lỗ chờ xuyên dầm, nách dầm |
| Sàn | Chiều dày sơ bộ | Chiều dày, cao độ, lỗ mở đúng | Giật cấp, dốc, lỗ kỹ thuật phối hợp |
| Móng, cọc, đài | Khối sơ bộ | Kích thước, cao độ đúng | Cọc đầy đủ, giằng, hố pit |
| Lõi thang | Khối lõi | Vách, lỗ cửa đúng | Lỗ kỹ thuật, dầm lanh tô |
| Cốt thép | Không | Không | Không |

## Ghi chú cao tầng
- Tầng chuyển và tầng kỹ thuật thường cần LOD cao hơn tầng điển hình. Kiểm tra BEP.
- Cao độ SSL (kết cấu) và FFL (hoàn thiện) phải nhất quán với chiều dày lớp hoàn thiện.
