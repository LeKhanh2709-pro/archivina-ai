# Quy tắc dựng mô hình kết cấu Revit từ MB KC (chốt 12/10/2026, đổi tên theo ARV 24/10/2026)

## 1. Đầu vào và phạm vi
| Mục | Quy tắc |
|---|---|
| Bản vẽ | MB kết cấu KC: MB định vị cột + MB kết cấu dầm sàn từng tầng. Đơn vị mm (`INSUNITS=4`), khác → hỏi. |
| Cấu kiện | Trục + level + cột; dầm + sàn. Vách, móng, cọc, cầu thang: chưa dựng (báo "chưa dựng"). |
| Dự án Revit | Dự án KC **mới** (bộ môn S) từ template S của dự án; chưa có thì `Structural Analysis-DefaultMetric.rte` của Revit 2027 (mm / m²). Kiến trúc link sau. Tên file theo `standards/naming-iso19650.md` mục 7. |
| Family | Claude tự tạo từ `.rft` khi dự án chưa có: `ARV_StrColumn_RC_Rect`, `ARV_StrFraming_RC_Rect`, tham số kiểu `b`, `h`; type `<b>x<h>` (mm); sàn `ARV_Floor_RC_<dày>`. Family phải được BIM Manager duyệt trước khi dùng trong mô hình phát hành. |
| Vật liệu | Hỏi cấp bền theo dự án cho cột / dầm / sàn → vật liệu `ARV_BT_<cấp>`. Thiếu → `ARV_BT_ChuaXacDinh`. |
| Đầu ra kiểm tra | Mặt bằng `S_MB_<Level>_Ket cau` mỗi level + view 3D `S_3D_ZZ_Kiem tra KC`. Trước khi ghi: ảnh `xem_lai_*.png` để người dùng duyệt. |

## 2. Level và cao độ
- Cốt ghi trên MB (`( CỐT +3.850 )`) = **cốt mặt sàn kết cấu (SSL)** → level `L02` cao độ 3850.
- MB định vị cột tầng 1 không ghi cốt → **chân cột tầng 1 tại ±0.000** (level `L01`).
- MB sàn không ghi cốt → hỏi.
- Tên level theo CLAUDE.md mục 2: `B3…B1`, `L01…`, `RF`, `TR`. Kết cấu làm chủ level / grid; Kiến trúc Copy/Monitor sau.

## 3. Trục và gốc toạ độ
- Trục: nét layer `truc|grid|axis`, tên lấy từ bóng trục (text / attribute trong vòng tròn ở đầu trục).
- Gốc toạ độ Revit = giao **trục chữ đầu tiên × trục số đầu tiên** (A × 1). Các MB quy về gốc này; lưới trục MB nào khác MB đầu → cảnh báo.
- Shared Coordinates / Survey Point của dự án do BIM Manager thiết lập sau khi dựng; công cụ không tự đặt.

## 4. Cột
- Polyline kín layer cột (`cot|column`), chữ nhật (mặt cắt b theo X, h theo Y trước khi xoay, góc chuẩn hoá về (-45°, 45°]).
- Mã cột: text `C1`, `CT2`… gần nhất ≤ 1,5 m, ghi vào `Mark`; MB không ghi mã thì lấy mã cùng vị trí ở tầng khác.
- Đoạn cột tầng k → k+1 = cột trên **MB định vị cột tầng k** ∪ cột cắt trên **MB sàn tầng k+1** ∪ **cột dựng** (layer `cot dung`) trên MB sàn tầng k.
- Cột dựng ở tầng trên cùng → hỏi đỉnh cột (`--tang-tren "RF=<cốt mm>"`).
- Hai polyline cột chồng nhau khác tiết diện ở cùng vị trí → hỏi (đang lấy cột lớn).
- Cùng mã, cùng tầng, khác tiết diện → hỏi. Tiết diện đổi giữa các tầng → cảnh báo, dùng tiết diện MB dưới.

## 5. Dầm
- Dầm = **cặp nét song song** (layer `thay|khuat|dam|beam`), khoảng cách = b; **tim dầm = giữa 2 nét** (dầm biên lệch trục vẫn đúng vị trí).
- Tiết diện lấy **từ nhãn** `[Mã-]bXh` (ví dụ `D1-22X40`, `22X50`, `15X52.5`); số ≤ 200 hiểu là **cm**, lớn hơn là mm. Mã dầm ghi vào `Mark`.
- Nhãn và khoảng cách 2 nét lệch > 15 mm → **dừng, hỏi** (không tự chọn). Nhãn không ghép được cặp nét → hỏi. Cặp nét khuất giống dầm mà không có nhãn → hỏi.
- Nhịp: chia theo cột cắt qua dải dầm; dầm đi qua dầm phụ không bị chia (nhãn ghi 1 lần cho dầm liên tục). Đầu dầm tựa cột → về tim cột; tựa dầm → về tim dầm vuông góc; không tựa gì → giữ đầu nét (công xôn).
- **Đỉnh dầm = mặt sàn kết cấu** của level (offset 0). Vùng sàn hạ cốt chỉ hạ sàn, dầm giữ nguyên trừ khi bản vẽ ghi riêng.

## 6. Sàn
- Biên sàn = bao ngoài các ô khép bởi nét dầm / mép sàn.
- Lỗ mở / ô thông tầng = ô chữ nhật có dấu X (2 đường chéo nối góc đối) → khoét khỏi sàn.
- Chiều dày: chú giải "SÀN BTCT DÀY 150" (ô mẫu không hatch). Không có → hỏi.
- **Tấm theo vùng cốt**: vùng hatch trùng mẫu trong chú giải của **đúng tờ** đó ("HẠ CỐT 50" → offset −50, "NÂNG CỐT 35" → +35) tách thành tấm riêng; phần còn lại là tấm chính offset 0. Hatch trong sàn không có trong chú giải → hỏi.

## 7. An toàn
Theo CLAUDE.md mục 4 "Ghi mô hình có kiểm soát". Tóm tắt: không sửa DWG gốc (đọc qua bản sao DXF); chỉ ghi vào dự án Claude tạo / bản sao làm việc; người dùng tự bấm "Cho phép ghi"; Claude hỏi trước mỗi lần ghi; file workshared bị từ chối.
