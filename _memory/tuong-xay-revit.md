---
name: tuong-xay-revit
description: "Nút pyRevit Tường xây (HS TKBVTC) = graph ARV_MBTuongXayTang_v1 của đồng nghiệp (AI REVIT\\TUONG XAY), áp dụng 2026-11-04, chưa duyệt"
metadata:
  node_type: memory
  type: project
  originSessionId: b4172067-bb0a-4d01-8f92-dba06afb7a4b
  modified: 2026-11-09T10:18:07.993Z
---

Người dùng yêu cầu 2026-11-04 "áp dụng cho máy, tạo 1 nút tường xây ở HS TKBVTC" từ `D:\AI\AI REVIT\TUONG XAY\` (graph `ARV_MBTuongXayTang_v1`: view mặt bằng tường xây cả tầng, dim trục, chuỗi định vị tường thô, legend ký hiệu tường, sheet A1).
- Bản dùng: `scripts\dynamo\ARV_MBTuongXayTang_v1.dyn/.py`; khác bản gốc: IN[0] Level trống = tầng của view đang mở, IN[17] đặt lên bản vẽ, sheet trống có sẵn, khung tên "Family : Type".
- Nút MỘT CHẠM (người dùng chốt 2026-11-04: bỏ hộp thoại 17 ô, chỉ hỏi đặt lên bản vẽ như Chống thấm): `MOT_CHAM["TuongXay"]` + `arv_hoi_sheet.hoi_tuong_xay` (chỉ A1); lõi thêm IN[17] + đặt vào sheet trống có sẵn. Icon mdi `wall`.
- Thử bản sao G19_A_L3-32 2026-11-04 OK (sheet A199 khớp A140 đồng nghiệp); một lần Revit tắt đột ngột không rõ lý do.

- 2026-11-09 áp dụng `AI REVIT\TUONG XAY 2` (graph HQV Phía Bắc / Nam mới nhất) bằng gộp 3 chiều: IN[17] vẫn là Đặt lên bản vẽ, 8 ô mới của đồng nghiệp lùi thành IN[18]–IN[25]. Graph đồng nghiệp đánh số IN[17]–IN[24] nên lần gộp sau phải lùi số lại.

**Why:** tool của đồng nghiệp, người dùng muốn dùng ngay trên ribbon như các nút hồ sơ khác.
**How to apply:** sửa logic thì sửa `scripts\dynamo\ARV_MBTuongXayTang_v1.py` (giữ code nhúng .dyn đồng bộ) rồi `build_from_dynamo.py ... --chi TuongXay`; khi đồng nghiệp gửi bản mới, so với bản gốc trong `AI REVIT\TUONG XAY` trước. Liên quan [[ai-revit-dong-nghiep]], [[pyrevit-arvtools-revit2027]].
