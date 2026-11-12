---
name: cua-kinh-ban-le-san
description: "Chi tiết cửa kính cường lực bản lề sàn + vách kính kẹp — người dùng chỉ cần bản vẽ CAD, không cần LISP (2026-11-02)"
metadata:
  node_type: memory
  type: project
  originSessionId: aeed6e97-4e0f-4aac-9b2f-3901431795e9
  modified: 2026-11-02T09:11:10.098Z
---

Người dùng nhờ chi tiết cửa kính cường lực bản lề sàn (kẹp kính, vách kính cường lực kẹp hai bên + ô fix trên). Sau khi xem ảnh mẫu thì chốt **"không cần lisp, tạo bản vẽ cad"** (2026-11-02).

- Bố cục theo ảnh mẫu người dùng gửi: MẶT ĐỨNG trên, CẮT 2-2 (mặt bằng, cánh mở 2 chiều vẽ nét đứt hình thoi) ngay dưới + dim dưới mặt bằng, CẮT 1-1 bên phải; ghi chú nằm trong ô kính / cạnh phụ kiện; 2 cánh: KẸP TRÊN cánh trái, KẸP L cánh phải, 1 khoá sàn.
- Kết quả: `file mau\06_CuaKinh\01_CuaKinh_BanLeSan.dwg` (1 cánh + 2 cánh, TL 1/50), sinh bằng ezdxf `_tmp\cua_kinh\ve_dwg_cua_kinh.py` từ ISO DXF (layer ISO, dim `A 1-100` ghi đè DIMSCALE 50, block `kyhieu cat` + cốt cao độ).
- Kích thước phụ kiện là số tạm (Cần xác nhận lại); dim 60 hai đầu trong ảnh mẫu chưa rõ nghĩa.

**Why:** người dùng muốn bản vẽ dùng ngay, không cần công cụ.
**How to apply:** sửa theo góp ý thì chạy lại script trên rồi DXF → DWG; chỉ làm thành lệnh K-TOOL khi người dùng yêu cầu lại. Liên quan [[vk-mat-dung-dang-do]], [[gui-link-ban-ve-sau-test]].
