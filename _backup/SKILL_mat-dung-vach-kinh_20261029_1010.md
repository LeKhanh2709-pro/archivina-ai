---
name: mat-dung-vach-kinh
description: 'Mặt đứng vách kính – Từ block vách kính MẶT BẰNG "VACH KINH <dài>" do lệnh VK (skill chia-do-vach-kinh) tạo, dựng mặt đứng vách: đố đứng 65 theo đúng vị trí trên mặt bằng, khung trên / dưới, đố ngang, cửa sổ hất / cửa đi kính 2 cánh theo block người dùng cấp, ký hiệu kính 3 vạch giữa mỗi ô, gom block MAT DUNG VK <dài>x<cao> trên A-Window, dim "dim cua" ngoài block (A-Dimension), nét cắt 1-1 / 2-2. Lệnh LISP VKMD (file VKMD.lsp). Dùng khi người dùng nhờ "vẽ mặt đứng vách kính", "mặt đứng VK", "dựng mặt đứng từ mặt bằng vách kính", "VKMD".'
---

# Mặt đứng vách kính (Archivina)

Người dùng chọn block vách kính trên mặt bằng (do lệnh `VK` tạo), nhập chiều cao; lệnh `VKMD` dựng mặt đứng thẳng hàng phía trên mặt bằng. Không xoá, không sửa đối tượng có sẵn. Người dùng là kiến trúc sư: báo kết quả và đường dẫn bản vẽ trước, ngắn gọn.

## Quy tắc (người dùng chốt 29/10/2026)
- **Đầu vào chỉ là block `VACH KINH <dài>` do `VK` tạo.** Đọc trong block: `VK_DoDung` (tâm đố), `VK_CuaSoMo[_<rộng>]`, `VK_CuaDi[_<rộng>]` (điểm chèn = tâm đố trái, rộng tâm-tâm theo tên block, không hậu tố = 1000 / 1665). Dài vách = tâm đố cuối + 32,5.
- Lệnh riêng, `VK` chỉ vẽ mặt bằng. **Chiều cao vách nhập tay.** Vách không có cả cửa sổ lẫn cửa đi (gặp thì báo lỗi).
- Thứ tự trái / phải **giữ đúng như mặt bằng**. Vách nằm ngang trên mặt bằng: mặt đứng **thẳng hàng theo X phía trên mặt bằng**, người dùng chỉ chọn cao độ chân (vách vẽ từ phải sang trái vẫn đúng thứ tự). Vách xiên: điểm chọn = góc dưới trái mặt đứng.
- Đố đứng, khung trên / dưới, đố ngang rộng **65** (`ACAD-thanh dung va thanh ngang.dxf`). Đố đứng chạy suốt chiều cao; thanh ngang vẽ giữa 2 mặt đố.
- **Vách cửa đi:** khung dưới (không có ở ô cửa đi) + khung trên + **1 đố ngang ở đỉnh cửa, chạy suốt vách** (mặt dưới đố = cao cửa). **Cao cửa nhập tay** (mặc định 2700; block 2699,51).
- **Vách cửa sổ / vách kính không cửa:** khung trên / dưới; **đố dưới cửa sổ chỉ có trong ô cửa sổ**; cửa sổ treo ngay dưới đố ngang, cao cánh lọt lòng mặc định 1400 (block 1399,89), sửa được.
  - Đố ngang trên cửa sổ (chạy suốt vách): mặt trên ở cao độ nhập (mặc định **2700**); ô kính phía trên đố nhỏ hơn mức tối thiểu (mặc định **300**) thì **bỏ đố**, cửa sổ sát khung trên. Người dùng nói quy tắc này "phụ thuộc kích thước vách và cửa sổ" nhưng chưa chốt số → 2700 / 300 là đề xuất, `Cần xác nhận lại`.
- Ký hiệu kính 3 vạch (block `VKMD_Kinh`, lấy từ ký hiệu kính trong block cửa sổ) **layer A-Window, giữa mỗi ô kính** (ô < 300 thì bỏ); cửa đi: giữa mỗi cánh. **Bỏ chữ FIX.**
- Hình gom block **`MAT DUNG VK <dài>x<cao>`** (layer A-Window). **Kích thước ngoài block, layer `A-Dimension`**, kiểu `dim cua`: chuỗi tâm đố + tổng phía dưới (cách chân 200 / 335), chuỗi cao độ tâm thanh ngang + tổng bên phải (cách mép 365 / 485), theo mẫu VK01.
- **Nét cắt** như mẫu CT3: 1-1 dọc qua giữa ô cửa đầu tiên (không có cửa thì ô giữa), 2-2 ngang ở giữa chiều cao cánh cửa sổ / cửa đi (không có cửa thì giữa vách). Ký hiệu `VKMD_Cat11` / `VKMD_Cat22` + số trên `A-Symbol`, đường cắt trên `A-Hidden` (DASHED). Ghi chú, tên vách người dùng tự thêm.
- Vách nhiều tầng (VK33 / VK37 trong CT3): **để sau**.

## Công cụ
- `<skill>` = "Base directory for this skill". `<python>` = Python có ezdxf (máy này `D:\AI\_tools\venv\Scripts\python.exe`).
- `lisp\VKMD.lsp`: **một file**, block mặt đứng nhúng sẵn, chỉ ký tự ASCII (chữ có dấu trong chuỗi là `\U+XXXX`, chạy được LISPSYS 0 và 1). Bản người dùng APPLOAD: `<gốc>\scripts\lisp\VKMD.lsp`.
- Sửa LISP: sửa `lisp\vkmd_nguon.lsp` → `<python> scripts\gop_vkmd.py` → chép `lisp\VKMD.lsp` sang `<gốc>\scripts\lisp\`. Không sửa tay `VKMD.lsp`.
- Đổi block mặt đứng: người dùng cấp lại DXF trong `file mau\block vach kinh\` (tên chứa `md cua di`, `md cua so`, `thanh ngang`) → `<python> scripts\tao_du_lieu_md.py --nguon "<thư mục>"` (sinh `lisp\vkmd_du_lieu.lsp`) → `gop_vkmd.py`.
  - Cửa đi: phẳng hoá, bỏ MULTILEADER (ghi chú tay nắm / khoá sàn), dim, ký hiệu kính. Kéo giãn theo rộng / cao: `|x| ≤ 200` (tay nắm, khoá sàn) và `y ≤ 1400` giữ nguyên; `|x| ≥ 580`, `y ≥ 2600` dời; giữa tỉ lệ. Cao cửa phải > 1499,5.
  - Cửa sổ: vẽ theo thông số đo từ block (cánh màu 5, tam giác nét HIDDEN tỉ lệ 300, đỉnh giữa cạnh trên = cửa hất).

## Chạy thử (không hộp thoại)
`powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\chay_thu_vkmd.ps1 -Dwg <bản vẽ trắng> -OutDwg <kết quả> -LispFile <file biểu thức>`
- Nạp `VK.lsp` (skill `chia-do-vach-kinh`) + `VKMD.lsp` vào `acad.exe /b`; hàm `(vkmd:thu L ns ws nd wd vs vd ptMB gocMB H hd hs ht kmin yMD)` dựng mặt bằng bằng VK rồi mặt đứng. Log ghi chuỗi cao độ.
- Hộp thoại DCL không chạy được khi tự động: người dùng tự thử.

## Đã kiểm (29/10/2026, `file mau\05_VachKinh\VKMD_thu.dwg` + `.png`)
| Vách | Chuỗi cao độ (dưới lên) | Đối chiếu CT3 |
|---|---|---|
| 4210 cửa sổ ô 3, H 3850, cánh 1185 | 32,5 / 1385 / 1250 / 1150 / 32,5 | khớp VK01 |
| 4210 cửa đi ô 2, H 3650, cửa 2700 | 32,5 / 2700 / 885 / 32,5 | khớp DVK01 (2699,51 / 885,49) |
| 3000 cửa sổ ô 2, H 2780, cánh 1282,17 (không đố ngang) | 32,5 / 1367,83 / 1347,17 / 32,5 | khớp VK101 |
| 1500 không cửa, H 3850 | 32,5 / 2635 / 1150 / 32,5 | khớp VK06 |
| 4800 2 cửa sổ, 6385 cửa đi 1500 vẽ ngược chiều, 4210 xoay 30°, 4210 H 2000 | đúng thứ tự mặt bằng, không lỗi | — |

Người dùng chưa chạy trong AutoCAD của mình, chưa duyệt (`Cần xác nhận lại`).
