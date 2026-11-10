---
name: revit-2027-dynamo-tu-dong
description: Cách Claude tự chạy graph Dynamo trên bản sao .rvt ở máy này (Revit 2027 / Dynamo 4.2) và các bẫy đã gặp
metadata:
  node_type: memory
  type: reference
  originSessionId: a672e335-b6af-4609-8e94-6faf49c726a9
  modified: 2026-11-10T09:56:26.865Z
---

Máy này chỉ có Revit 2027.3 (Dynamo 4.2.1, engine Python duy nhất là **PythonNet3**, Python 3.11; graph khai báo CPython3 vẫn chạy nhưng nên sinh `"Engine": "PythonNet3"`). Đã kiểm 2026-10-27.

Cách chạy được (D:\AI\_tmp\revit_g19\chay_dynamo_ui.ps1):
- Revit.exe <journal.txt> trên bản sao trong D:\AI\_tmp. Journal: `Jrn.Directive "DebugMode", "PermissiveJournal", 1` + `"PerformAutomaticActionInErrorDialog", 1`, mở file, `Launch Dynamo , ID_VISUAL_PROGRAMMING_DYNAMO` + `APIStringStringMapJournalData` (dynPath, dynShowUI **true**, dynAutomation, dynPathExecute, dynModelShutDown). KHÔNG thêm dòng trả lời hộp thoại thủ công (lệch journal → dừng), KHÔNG để ID_APP_EXIT (thoát trước khi Dynamo chạy).
- Dynamo 4.2 mở graph nhưng **không tự chạy** (cả dynShowUI false lẫn true) → bấm nút `RunButton` bằng UI Automation, chờ `runNotificationTextBlock` = "Run completed", rồi Stop-Process. Cả vòng ~1 phút.
- Không ai được bấm vào cửa sổ Revit riêng đó (người dùng từng thao tác nhầm).
- Chạy nền (2026-11-10, xem [[khong-lam-phien-may-nguoi-dung]]): luồng C# trong runner quét cửa sổ theo PID mỗi 50 ms, làm trong suốt + click xuyên qua, đẩy ra ngoài màn hình tối đa 5 lần. Bẫy: chỉ đẩy thì cửa sổ WPF không tên cỡ cả màn hình bị Revit kéo về 0,0 hơn 1000 lần; cửa sổ Dynamo bị ẩn theo Revit thì UI Automation vẫn bấm được Run.
- Graph ở thư mục mới → Dynamo hiện "Open external file?" (thư mục chưa tin cậy) và treo; người dùng dặn (2026-10-27) **tự bấm Yes, không hỏi** → runner có hàm `Bam-Yes`. Phải chờ `RunButton.IsEnabled` trước khi Invoke.
- Bồn cầu `AV-Toilet` host trên sàn → LevelId không phải level; khung bao kéo dài ~1,7 m ra sau tường → lấy thiết bị theo view, điểm dò = Location + FacingOrientation·200 mm.

Bẫy PythonNet3: không dùng `isinstance(e, RevitClass)` (không tự ép kiểu) → lọc bằng FilteredElementCollector.OfClass / so Id.Value; `from X import *` chỉ ở cấp module (bọc code trong hàm thì để import ngoài hàm).

Liên quan: [[khong-bind-chi-doi-mau-layer]]
