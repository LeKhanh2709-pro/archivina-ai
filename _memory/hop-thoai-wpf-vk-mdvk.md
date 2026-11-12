---
name: hop-thoai-wpf-vk-mdvk
description: "VK / MDVK dùng hộp thoại WPF trong K-TOOL.dll (sáng / tối), DCL là dự phòng; bố cục người dùng chốt, sửa quy tắc chia phải sửa cả bản C#"
metadata:
  node_type: memory
  type: project
  originSessionId: a96cfae0-8a6d-40b8-84de-db94615dcf9f
  modified: 2026-10-31T02:45:54.935Z
---

Hộp thoại mới của VK / MDVK (người dùng duyệt mẫu 2026-10-31) viết bằng WPF trong K-TOOL.dll: `scripts\ktool\BangVk.cs`, `BangMdvk.cs`, `ChuDe.cs`, `HopThoaiLisp.cs`, XAML trong `scripts\ktool\xaml\`. LISP gọi `ktool_bang_vk` / `ktool_bang_mdvk`; không có DLL hoặc WPF lỗi thì dùng DCL cũ.

**Why:** DCL không làm được nền tối, nhãn màu, bấm vào sơ đồ. VK.lsp / VKMD.lsp vẫn phải chạy một mình theo quy tắc 8 của CLAUDE.md.

**How to apply:**
- Bố cục VK do người dùng chốt: sơ đồ trên cùng, nhập liệu bên trái, bảng các ô bên phải (không đưa preview sang cạnh). MDVK: danh sách + thông số bên trái, preview lớn bên phải.
- `Vk.Chia` và `Md.Tinh` trong C# chép từ `vk:chia` / `vkmd:tinh`: sửa quy tắc trong LISP thì sửa cả C#, rồi build lại.
- Thử giao diện bằng `_tmp\ktool_wpf\XemBang.csproj` (dựng cửa sổ ngoài màn hình, chụp PNG), thử LISP bằng `thu\chay_ngam.ps1` (hàm giả, không mở hộp thoại). Xem [[khong-lam-phien-may-nguoi-dung]].
- Liên quan: [[k-tool-thanh-cong-cu]], [[vk-mat-dung-dang-do]].
