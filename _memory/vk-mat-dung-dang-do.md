---
name: vk-mat-dung-dang-do
description: "Vách kính: MDVK (VKMD.lsp) duyệt OK; VK có pick 2 điểm + block động CHỈ kéo điểm cuối (người dùng chốt 2026-10-29, sau khi thử bản kéo 2 đầu); K-TOOL.dll phải build lại khi sửa LISP"
metadata:
  node_type: memory
  type: project
  originSessionId: 76f2a5b5-b8aa-4917-aa80-c955d362948c
  modified: 2026-10-30T04:13:53.117Z
---

Skill `mat-dung-vach-kinh`, lệnh **MDVK** (người dùng chốt tên 2026-10-29, chỉ MDVK; file vẫn `scripts\lisp\VKMD.lsp`). Liên quan [[chia-do-vach-kinh]]. Quy tắc đầy đủ trong SKILL.md của skill.

Chốt 2026-10-29: lệnh tự nhận loại vách từ mặt bằng; vách cửa đi hỏi cao vách + cao cửa đi; vách cửa sổ hỏi cao vách + cao cửa sổ + có thanh ngang trên cửa sổ không. Mép dưới cánh LUÔN = sàn hoàn thiện + bậu (50 + 1400, khớp VK01), kể cả vách ngắn. Có thanh ngang: nhập cao cửa sổ, thanh ngang ngay trên. Không: cửa sổ sát mép dưới khung trên, cao cửa sổ tự tính.

Chốt thêm 2026-10-29 (sau khi thử): hình + dim + nét cắt gom 1 block; ký hiệu kính "///" (block cửa đi) giữa mọi ô; cửa đi giữ nguyên ghi chú + dim của block; đường gióng dim cách đối tượng 80 / 240.

Người dùng duyệt "OK" 2026-10-29 và cho đẩy GitHub. Còn để sau: vách nhiều tầng.

Lệnh VK (chiều 2026-10-29, người dùng chốt): bảng hiện trước, nút "Pick 2 điểm <" lấy chiều dài rồi OK dựng đúng 2 điểm; block VACH KINH là **block động, chỉ 1 grip ở điểm cuối, điểm đầu khoá** (người dùng đổi từ kéo 2 đầu; grip + Stretch, reactor chia lại đố, XData `ARCHIVINA_VK`); MDVK đọc theo EffectiveName và trừ độ lệch đầu vách. MDVK: dim mặt bằng vẽ lại theo đố thật (entmod không ăn trong AutoCAD người dùng); cửa đi bằng vách thì bỏ thanh ngang. Máy khác dùng K-TOOL.dll (LISP nhúng) → sửa LISP xong phải build lại DLL và đẩy GitHub, không thì máy kia vẫn chạy bản cũ. Xem [[lisp-reactor-an-toan]].

2026-10-30: MDVK tự nhận vách (quét vùng / Enter cả bản vẽ), gồm cả vách VẼ TAY không do VK tạo (mẫu `file mau\ACAD-CT VACH KINH.dxf`, đố block 65,7×187,2 tên tuỳ ý); mặt đứng đặt ngay trên mỗi vách (người dùng chọn). Người dùng muốn Claude "học nhận diện từ file mẫu" họ cấp thay vì chọn cách nhận trừu tượng. Chưa duyệt.

**Why:** người dùng sửa quy tắc đố ngang sau lần thử đầu.
**How to apply:** khi người dùng phản hồi về MDVK, sửa vkmd_nguon.lsp → gop_vkmd.py → chép VKMD.lsp sang scripts\lisp; sửa SKILL.md + dòng CLAUDE.md.
