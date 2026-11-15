---
name: cad-sang-legend-revit
description: "Chuyển chi tiết CAD (DXF) sang legend 2D Revit: hatch → Filled Region, nét trùng còn 1, mỗi ô 1 detail group; 1 kiểu chữ, 1 kiểu dim, ít cỡ chữ; soi ảnh từng ô so với CAD trước khi báo xong"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3d257101-e997-402b-a090-1e16997bbbcb
  modified: 2026-11-14T08:09:39.254Z
---

Người dùng yêu cầu 2026-11-13 (file `CT Cua khanh.dxf`, 25 ô chi tiết cửa): vẽ chi tiết CAD bằng **legend 2D** trong Revit; chỗ hatch dùng **Filled Region**; nét trùng chỉ giữ **1 nét**; **mỗi ô chi tiết 1 group**. Giữa chừng người dùng chốt thêm: **chung 1 kiểu chữ, 1 kiểu dim, chiều cao chữ gom về ít loại nhất** (Arial, cỡ 2,5 / 3,5 / 5 mm; dim 2,5 mm; chữ CAD < 1 mm giấy bỏ, có báo).

Hệ số rộng chữ KHÔNG phải lời người dùng: bản đầu Claude đặt 1,0; tối 2026-11-13 Claude đổi sang 0,8 (chữ CAD 73 % rộng 0,8, rộng 1 thì nhãn đè đường dẫn) và đã báo người dùng, chưa có phản hồi. Hatch đặc giữ màu CAD (xanh dương / xanh lá) cũng chưa được người dùng quyết.

**Why:** hồ sơ Revit gọn, dễ quản lý kiểu; người dùng không muốn nhiều kiểu chữ / dim lặt vặt từ CAD.

**How to apply:** khi chuyển bản vẽ CAD sang Revit (legend / drafting), không sinh kiểu chữ / dim theo từng cỡ CAD; gom về bộ cỡ chuẩn. Công cụ + bẫy ở `D:\AI\scripts\cad_legend\README.md` (bản làm việc `D:\AI\_tmp\ct_cua_legend\`). Bài học 13 – 14/11 (diễn giải của Claude): log "0 lỗi" không đủ – bản đầu 0 lỗi nét / chữ / dim mà dim vẫn xiên, nền che chữ thành ô đen, chữ còn mã `\U+XXXX`; phải xuất ảnh TỪNG Ô (`thu_anh_o.py`) và so với ảnh CAD (`ve_cad_o.py`) rồi mới gửi duyệt, và chạy bản cuối trên bản sao SẠCH. File thứ 2 `ctchung.dxf` (14/11, xong 15:00, bàn giao `D:\AI\_tmp\ct_chung_legend\duyet_20261114\`, chưa duyệt; so sánh từng ô với bản IN THẬT của AutoCAD bằng `tao_plot_o.py` + `so_o.py` – nhờ đó tìm ra lỗi lật cung hatch có cả trong bản cửa đã giao): trước khi chạy bộ script cho file CAD mới phải kiểm 3 thứ mà file cửa không có – (1) nhiều tỉ lệ trong 1 file (mỗi tỉ lệ 1 legend riêng), (2) chữ lẫn bảng mã TCVN3 / VNI / Unicode (`ma_chu.py`, đổi theo font từng đoạn), (3) MTEXT đặt chữ bằng thụt lề đoạn `\pi`. Người dùng cắt ngang lúc đang khảo sát dài và bảo "đóng gói những gì đã làm được rồi gửi link" (diễn giải của Claude: với việc dài, báo sớm phạm vi + thời gian và đưa kết quả trung gian, đừng im lặng khảo sát lâu). Liên quan [[anh-duyet-truoc-khi-build]], [[nut-moi-extension-rieng]], [[revit-vang-locale-cpython]], [[gui-link-ban-ve-sau-test]].
