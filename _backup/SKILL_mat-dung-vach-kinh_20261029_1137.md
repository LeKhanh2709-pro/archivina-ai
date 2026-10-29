---
name: mat-dung-vach-kinh
description: 'Mặt đứng vách kính – Từ block vách kính MẶT BẰNG "VACH KINH <dài>" do lệnh VK (skill chia-do-vach-kinh) tạo, dựng mặt đứng vách: đố đứng 65 theo đúng vị trí trên mặt bằng, khung trên / dưới, đố ngang, cửa sổ hất / cửa đi kính 2 cánh theo block người dùng cấp, ký hiệu kính 3 vạch giữa mỗi ô, gom block MAT DUNG VK <dài>x<cao> trên A-Window, dim "dim cua" ngoài block (A-Dimension), nét cắt 1-1 / 2-2. Lệnh LISP MDVK (file VKMD.lsp). Dùng khi người dùng nhờ "vẽ mặt đứng vách kính", "mặt đứng VK", "dựng mặt đứng từ mặt bằng vách kính", "MDVK".'
---

# Mặt đứng vách kính (Archivina)

Người dùng gõ **`MDVK`** (tên lệnh người dùng chốt 29/10/2026; file vẫn là `VKMD.lsp`, hàm tiền tố `vkmd:`), chọn block vách kính trên mặt bằng (do lệnh `VK` tạo); lệnh **tự nhận loại vách** (cửa đi / cửa sổ / kính không cửa) và hiện bảng hỏi chỉ gồm các ô của loại đó, rồi dựng mặt đứng thẳng hàng phía trên mặt bằng. Không xoá, không sửa đối tượng có sẵn. Người dùng là kiến trúc sư: báo kết quả và đường dẫn bản vẽ trước, ngắn gọn.

## Quy tắc (người dùng chốt 29/10/2026)
- **Đầu vào chỉ là block `VACH KINH <dài>` do `VK` tạo.** Đọc trong block: `VK_DoDung` (tâm đố), `VK_CuaSoMo[_<rộng>]`, `VK_CuaDi[_<rộng>]` (điểm chèn = tâm đố trái, rộng tâm-tâm theo tên block, không hậu tố = 1000 / 1665). Dài vách = tâm đố cuối + 32,5.
- Lệnh riêng, `VK` chỉ vẽ mặt bằng. **Chiều cao vách nhập tay.** Vách không có cả cửa sổ lẫn cửa đi (gặp thì báo lỗi).
- Thứ tự trái / phải **giữ đúng như mặt bằng**. Vách nằm ngang trên mặt bằng: mặt đứng **thẳng hàng theo X phía trên mặt bằng**, người dùng chỉ chọn cao độ chân (vách vẽ từ phải sang trái vẫn đúng thứ tự). Vách xiên: điểm chọn = góc dưới trái mặt đứng.
- Đố đứng, khung trên / dưới, đố ngang rộng **65** (`ACAD-thanh dung va thanh ngang.dxf`). Đố đứng chạy suốt chiều cao; thanh ngang vẽ giữa 2 mặt đố.
- **Vách cửa đi:** khung dưới (không có ở ô cửa đi) + khung trên + **1 đố ngang ở đỉnh cửa, chạy suốt vách** (mặt dưới đố = cao cửa). **Cao cửa nhập tay** (mặc định 2700; block 2699,51).
- **Vách cửa sổ:** khung trên / dưới; **đố dưới cửa sổ chỉ có trong ô cửa sổ**. **Mép dưới cánh (mặt trên đố dưới cửa sổ) LUÔN = sàn hoàn thiện + bậu** (mặc định 50 + 1400, nhập được), kể cả vách ngắn / thấp (người dùng chốt 29/10/2026). Bảng hỏi: chiều cao vách, ô chọn **có thanh ngang trên cửa sổ**:
  - **có** → nhập **chiều cao cửa sổ** (cánh lọt lòng, mặc định 1400 theo block 1399,89); thanh ngang chạy suốt vách ngay trên cửa sổ (mặt dưới thanh = sàn + bậu + cao cửa sổ). Thanh ngang chạm khung trên thì báo lỗi, không vẽ.
  - **không** → cửa sổ lên sát mép dưới khung trên, **chiều cao cửa sổ tự tính** = cao vách − 65 − (sàn + bậu) (ô nhập chiều cao bị khoá). Vách thấp hơn sàn + bậu + 65 thì báo lỗi.
- **Vách kính không cửa:** cùng bảng hỏi với vách cửa sổ; có thanh ngang thì đặt như vách cửa sổ (thẳng hàng vách cửa sổ bên cạnh, như VK06 cạnh VK01).
- Ký hiệu kính 3 vạch **"///"** (thể hiện hatch kính; block `VKMD_KyHieuKinh`, lấy từ ký hiệu kính trong block **cửa đi**, người dùng chốt 29/10/2026) **layer A-Window, giữa MỌI ô kính** (cả cánh cửa sổ); ô nhỏ hơn ký hiệu thì thu nhỏ còn 80 % cạnh ngắn. **Bỏ chữ FIX.** (Bản trước dùng block `VKMD_Kinh` "\\\\\\" của cửa sổ; bản vẽ cũ vẫn giữ block đó.)
- **Giữ nguyên thông tin block cửa đi** (người dùng chốt 29/10/2026): ký hiệu kính 2 cánh, kích thước 1600 (rộng lọt lòng) / 2700 (cao cửa) / 1000 (cao tay nắm) dựng lại bằng DIMLINEAR, ghi chú TAY NẮM INOX / KHÓA ÂM SÀN dựng lại bằng MLEADER (`vla-AddMLeader`, chữ cao 55, kiểu chữ `Archi- Arial` nếu bản vẽ có), đúng layer như block, vị trí kéo giãn theo rộng / cao cửa. **Dim chiều cao cửa nằm trong phạm vi cửa** (người dùng chốt 29/10/2026), cách mép trái cánh 300 (`DIM_TRONG_CUA` trong `tao_du_lieu_md.py`; block gốc để ngoài cửa 161). Mẫu `file mau\05_VachKinh\MDVK_thu4.dwg` + `MDVK_thu4_cuadi.png` (cửa 1665 cao 2700, cửa 2000 cao 2400).
- **Hình + kích thước + nét cắt gom TẤT CẢ vào 1 block `MAT DUNG VK <dài>x<cao>`** (chèn trên layer A-Window; người dùng chốt 29/10/2026, thay cho "dim ngoài block" trước đó). Dựng tạm tại 0,0 rồi `-BLOCK` (như lệnh VK). Kích thước layer `A-Dimension`, kiểu `dim cua`: chuỗi tâm đố + tổng phía dưới (cách chân 200 / 335), chuỗi cao độ tâm thanh ngang + tổng bên phải (cách mép 365 / 485), theo mẫu VK01. **Đường gióng cách đối tượng một khoảng** (người dùng chốt 29/10/2026): bắt đầu dưới chân 80, bên phải mép 240 (theo VK01; thông số `vkmd:dim-ho-ngang` / `vkmd:dim-ho-dung`).
- **Nét cắt** như mẫu CT3: 1-1 dọc qua giữa ô cửa đầu tiên (không có cửa thì ô giữa), 2-2 ngang ở giữa chiều cao cánh cửa sổ / cửa đi (không có cửa thì giữa vách). Ký hiệu `VKMD_Cat11` / `VKMD_Cat22` + số trên `A-Symbol`, đường cắt trên `A-Hidden` (DASHED). Ghi chú, tên vách người dùng tự thêm.
- Vách nhiều tầng (VK33 / VK37 trong CT3): **để sau**.

## Công cụ
- `<skill>` = "Base directory for this skill". `<python>` = Python có ezdxf (máy này `D:\AI\_tools\venv\Scripts\python.exe`).
- `lisp\VKMD.lsp`: **một file**, block mặt đứng nhúng sẵn, chỉ ký tự ASCII (chữ có dấu trong chuỗi là `\U+XXXX`, chạy được LISPSYS 0 và 1). Bản người dùng APPLOAD: `<gốc>\scripts\lisp\VKMD.lsp`.
- Sửa LISP: sửa `lisp\vkmd_nguon.lsp` → `<python> scripts\gop_vkmd.py` → chép `lisp\VKMD.lsp` sang `<gốc>\scripts\lisp\`. Không sửa tay `VKMD.lsp`.
- Đổi block mặt đứng: người dùng cấp lại DXF trong `file mau\block vach kinh\` (tên chứa `md cua di`, `md cua so`, `thanh ngang`) → `<python> scripts\tao_du_lieu_md.py --nguon "<thư mục>"` (sinh `lisp\vkmd_du_lieu.lsp`) → `gop_vkmd.py`.
  - Cửa đi: hình phẳng hoá; ký hiệu kính, kích thước, MULTILEADER tách riêng thành dữ liệu (`vkmd:dl-di-kinh` / `-dim` / `-chu`, chữ tiếng Việt ghi sẵn mã `\U+XXXX`) để dựng lại. Kéo giãn theo rộng / cao: `|x| ≤ 200` (tay nắm, khoá sàn) và `y ≤ 1400` giữ nguyên; `|x| ≥ 580`, `y ≥ 2600` dời; giữa tỉ lệ. **Không giới hạn cao / rộng cửa** (người dùng chốt 29/10/2026: chiều cao cửa đi, cửa sổ do người dùng quy định): cửa cao ≤ 1499,51 hoặc lọt lòng ≤ 840 thì co CẢ hình cửa theo tỉ lệ chiều đó (tay nắm, dim 1000 cũng co). Chỉ báo lỗi khi kích thước thật sự không vừa vách (cửa + đố + khung > cao vách, thanh ngang chạm khung trên, sàn + bậu ≥ mép dưới khung trên). Mẫu `file mau\05_VachKinh\MDVK_thu6.dwg` + `.png` (vách 5900 hai cửa 1700 cao 1000 trong vách 1500; cửa 800 cao 2100).
  - Cửa sổ: vẽ theo thông số đo từ block (cánh màu 5, tam giác nét HIDDEN tỉ lệ 300, đỉnh giữa cạnh trên = cửa hất).

## Chạy thử (không hộp thoại)
`powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\chay_thu_vkmd.ps1 -Dwg <bản vẽ trắng> -OutDwg <kết quả> -LispFile <file biểu thức>`
- Nạp `VK.lsp` (skill `chia-do-vach-kinh`) + `VKMD.lsp` vào `acad.exe /b`; hàm `(vkmd:thu L ns ws nd wd vs vd ptMB gocMB H hd hs co san bau yMD)` dựng mặt bằng bằng VK rồi mặt đứng (`co` = T / nil: có thanh ngang trên cửa sổ). Log ghi chuỗi cao độ.
- `VKMD.lsp` được bọc trong 1 `(progn ...)` khi thử: một dòng lỗi là cả file không nạp, giống APPLOAD. Log dòng đầu phải là `DA_NAP_LISP VKMD DU DU_LIEU CO LENH_MDVK CO`. (29/10/2026: dữ liệu nhúng thiếu dấu `'` trước danh sách → APPLOAD dừng giữa chừng, cửa đi + ký hiệu kính không vẽ; dòng lệnh .scr chạy tiếp sau dòng lỗi nên bản thử cũ không bắt được.)
- Lệnh tự định nghĩa lại block `VKMD_Kinh` nếu bản vẽ đã có block này nhưng rỗng (do bản lỗi trên tạo ra).
- Hộp thoại DCL không chạy được khi tự động: người dùng tự thử.

## Đã kiểm (29/10/2026, bảng hỏi mới: `file mau\05_VachKinh\MDVK_thu.dwg` + `.png` + `_log.txt`)
| Vách | Chuỗi cao độ (dưới lên) | Đối chiếu CT3 |
|---|---|---|
| 4210 cửa sổ ô 3, H 3850, cửa sổ 1185, có thanh ngang, sàn 50 + bậu 1400 | 32,5 / 1385 / 1250 / 1150 / 32,5 | khớp VK01 |
| 4210 cửa đi ô 2, H 3650, cửa 2700 | 32,5 / 2700 / 885 / 32,5 | khớp DVK01 (2699,51 / 885,49) |
| 3000 cửa sổ ô 2, H 2780, cửa sổ 1282,17, không thanh ngang | 32,5 / 1367,83 / 1347,17 / 32,5 | khớp VK101 |
| 1500 không cửa, H 3850, có thanh ngang (1185, 50 + 1400) | 32,5 / 2635 / 1150 / 32,5 | khớp VK06 |
| 4800 2 cửa sổ H 3450; 6385 cửa đi 1500 vẽ ngược chiều | đúng thứ tự mặt bằng | — |
| 3000 H 2780, cửa sổ 1400, có thanh ngang | báo lỗi "thanh ngang chạm khung trên", không vẽ | — |

Bản thử cũ theo quy tắc trước (đố ngang +2700 / ô kính 300): `file mau\05_VachKinh\VKMD_thu.dwg`.

Bản gom 1 block + sửa lỗi nạp (29/10/2026): `file mau\05_VachKinh\MDVK_thu2.dwg` + `_log.txt` + `MDVK_thu2_8085.png` — vách 8085 hai cửa đi ô 1 và 6 (H 3000, cửa 2700: 32,5 / 2700 / 235 / 32,5), VK01, VK101, vách cửa đi vẽ ngược chiều, vách xoay 30°; model chỉ còn block mặt bằng + block mặt đứng (dim 11–14, nét cắt 2, ký hiệu 4 trong mỗi block).

Bản ký hiệu "///" + giữ thông tin cửa đi + dim cách đối tượng (29/10/2026): `file mau\05_VachKinh\MDVK_thu3.dwg` + `_log.txt` + `MDVK_thu3_5535.png` (vách 5535 cửa đi ô 2 như DVK02, 8085 hai cửa đi, VK01, cửa đi vẽ ngược chiều). Bản bậu cố định (29/10/2026): `file mau\05_VachKinh\MDVK_thu5.dwg` + `.png` + `_log.txt` — vách 2218 cao 2800 không thanh ngang (cửa sổ tự tính 1285, chuỗi 32,5 / 1385 / 1350 / 32,5), VK01 có thanh ngang, 3000 cao 2780 và 4210 cao 3850 không thanh ngang (đố dưới cùng cao độ +1417,5), vách cao 1500 báo lỗi. Trước đó (bản thử 2) chế độ không thanh ngang tính ngược bậu từ khung trên → sai với vách ngắn.

Chữ ghi chú trong ảnh thử hiện sai dấu vì bản vẽ trắng không có kiểu chữ `Archi- Arial` (Cần xác nhận lại trên bản vẽ của người dùng).

Người dùng chưa chạy trong AutoCAD của mình, chưa duyệt (`Cần xác nhận lại`).
