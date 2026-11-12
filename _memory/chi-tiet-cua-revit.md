---
name: chi-tiet-cua-revit
description: "Nút pyRevit Chi tiết cửa (2026-11-03) – chọn 1 cửa → MB/MĐ/MC 1/25 vào sheet 6 ô; người dùng chỉ cần 3 view + ô trống, tự điền thông tin"
metadata:
  node_type: memory
  type: project
  originSessionId: 16ea747d-4408-4a26-9ac5-ab62de22ad70
  modified: 2026-11-04T01:56:56.951Z
---

Nút `ARV Tools → Hồ sơ → Chi tiết cửa` (lõi `scripts\dynamo\ChiTietCua_TuDong.py`, skill `chi-tiet-cua-revit`), làm 2026-11-03 theo ảnh mẫu A.CD.22.13 người dùng gửi.

**Why:** người dùng chốt: làm trên Revit, chọn 1 cửa có sẵn family, CHỈ tạo mặt bằng / mặt đứng / mặt cắt 1/25 và chia ô; ký hiệu, vật liệu, phụ kiện, bảng thông tin họ tự điền. Đã chọn: sheet 6 ô như mẫu, mặt đứng nhìn từ ngoài nhà, template mới, dim tổng rộng / cao.

Bản 2 (người dùng chốt 2026-11-03 tối): mặt bằng xoay theo mặt đứng (ngoài nhà ở dưới), mặt đứng CHỈ CÓ CỬA, level ẩn → nét đứt cốt sàn + chữ "CỐT SÀN HOÀN THIỆN ..." có mũi tên (như mẫu của họ). Lần đầu người dùng báo "lỗi chưa fix" vì Revit còn chạy nút cũ → sau khi sinh lại nút luôn nhắc Reload pyRevit, và nhắc xoá view / sheet bản cũ (mỗi type chỉ làm 1 lần, công cụ không xoá). Bản 3 (19:00): viewport "AV-Title No Line", kiểu view riêng Floor Plan "CT CỬA" / Section "MẶT CẮT CỬA", chữ đúng "CỐT SÀN HOÀN THIỆN" (không tên phòng), nét đứt cốt sàn suốt ô như mẫu CAD của họ, mặt bằng chỉ cửa + tường, trùm hết cung mở. Bản 4 (20:00): chọn nhiều cửa trước rồi bấm → bảng hỏi giai đoạn / hạng mục / khổ giấy / số hiệu / tên bản vẽ (lib\arv_hoi_sheet.py dùng chung với nút Tag cửa, phiên Tag cửa cũng sửa file này → giữ nguyên hàm hoi(doc, view)).

Bản 5 (2026-11-03 tối → 11-04): áp dụng cho cả vách kính (curtain wall) — tên `CT VÁCH KÍNH <Mark>`, dim chuỗi theo lưới đố, người dùng chốt 2026-11-04 GIỮ 1/25 ("sắp xếp cho phù hợp") → vách dài chiếm khối 2/3/4/6 ô trên sheet mới, lưới bỏ nét trong khối (bản lùi 1/50 → 1/100 đã bỏ; đừng đề xuất lùi tỉ lệ lại). Thử trên bản sao `file mau revit\file vach kinh.rvt`, không phải G19 (G19 không có curtain wall).

**How to apply:** không tự thêm bảng phụ kiện / vật liệu / ghi chú vào ô trừ khi được yêu cầu. Thử trên bản sao G19 đã OK (7 cửa, nút thật); người dùng chưa bấm thử, chưa duyệt. Bẫy lớn: `ViewSection.CreateSection` nhìn theo +BasisZ (xem skill). Liên quan [[tag-cua-revit]], [[pyrevit-arvtools-revit2027]].
