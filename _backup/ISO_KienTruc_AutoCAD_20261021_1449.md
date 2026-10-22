# ISO Kiến trúc ARCHIVINA — Quy chuẩn thể hiện AutoCAD (2023)

Nguồn: `D:\AI\ISO - ARCHIVINA-KIEN TRUC-2023- Nguyen sua.dwg` (bản "Nguyên sửa").
Nội dung dưới đây được trích tự động từ file DWG. Khi có mâu thuẫn, **file DWG gốc là chuẩn**.

Đơn vị bản vẽ: mm (`INSUNITS = 4`). Vẽ model tỷ lệ 1:1, mẫu chuẩn cho tỷ lệ **1/100** (`DIMSCALE = 100`).

## 1. Layer — đặt tên theo cấu kiện

Bảng "ĐẶT TÊN CÁC LỚP THEO CẤU KIỆN VÀ CÁC BẢN VẼ KỸ THUẬT". Cột **Nét in** là bề dày nét khi in khổ A2, A1, A0.

| Layer | Loại nét | Màu | Nét in (mm) | Công dụng |
|---|---|---|---|---|
| A-Column | CONTINUOUS | 1 | 0.35 | Cột |
| A-Text | CONTINUOUS | 2 | 0.09 | Chữ |
| A-Symbol | CONTINUOUS | 3 | 0.13 | Ký hiệu trên model, dùng chung cho các bộ môn |
| A-Symbol@ | CONTINUOUS | 3 | 0.13 | Ký hiệu / text trên model, **tắt đi khi gửi cho bộ môn khác** |
| A-Line1 | CONTINUOUS | 4 | 0.20 | Nét thấy cho các phần nhấn đậm nhất |
| A-Line2 | CONTINUOUS | 5 | 0.13 | Nét thấy thông thường |
| A-Line3 | CONTINUOUS | 251 | 0.05 | Nét thấy mảnh, lớp hoàn thiện tường |
| A-Door | CONTINUOUS | 163 | 0.05 | Cửa đi, cửa sổ |
| A-Wall | CONTINUOUS | 7 | 0.35 | Tường |
| A-Hidden | DASHED | 9 | 0.09 | Nét khuất |
| A-Material | CONTINUOUS | 8 | 0.05 | Vật liệu |
| A-Materials | CONTINUOUS | 8 | 0.05 | Hatch vật liệu riêng của kiến trúc |
| A-Axis | CENTER | 251 | 0.05 | Trục |
| A-Dim | CONTINUOUS | 192 | 0.09 | Kích thước trên model, dùng chung cho các bộ môn |
| A-Dim@ | CONTINUOUS | 192 | 0.09 | Kích thước trên model, **tắt đi khi gửi cho bộ môn khác** |
| A-Interior | CONTINUOUS | 148 | 0.05 | Nội thất |
| A-Interior color | CONTINUOUS | 255,255,255 | 0.05 | Hatch màu solid nội thất |
| A-WC | CONTINUOUS | 109 | 0.05 | Thiết bị vệ sinh |
| A-Do dientich | CONTINUOUS | 7 | **không in** | Đường bo diện tích các không gian |
| A-Color | CONTINUOUS | 250 | **không in** | Hatch màu solid các không gian (hồ sơ concept) |

Quy tắc rút ra:
- Tiền tố `A-` = kiến trúc. Hậu tố `@` = layer chỉ dùng nội bộ kiến trúc, phải tắt khi xuất nền cho các bộ môn (kết cấu, MEP).
- Layer `A-Do dientich`, `A-Color` không in (Plot = No).
- **Lưu ý:** trong file mẫu, lineweight gán trên layer khác với bảng nét in ở trên (vd. A-Wall: layer 0.40 so với bảng 0.35; A-Line3: 0.13 so với 0.05). Nét in có lẽ được điều khiển bằng bảng in CTB theo màu, nhưng điều này **cần xác nhận**. Script chuẩn hoá layer phải lấy **màu + loại nét** theo bảng trên, còn lineweight thì hỏi người dùng trước khi ghi đè.
- Trong file mẫu còn sót một số layer lạ (`A-Windows`, `A-Window`, `A - Text`, `S-Text`, `PAKT-NOTE`, `A-Anno-Scrn`, `A-WALL MATERIAL`, layer có tiền tố `XR Ghi chu$0$…`, `Khung A1 TKCS$0$…`). Đây là layer từ xref/block đã bind, **không phải chuẩn**. Script kiểm tra nên báo cáo chúng là "ngoài chuẩn".

## 2. Text

Font chuẩn: **ARIAL**, viết **CHỮ HOA** cho mọi loại dưới đây. Chiều cao là chiều cao khi in, đơn vị mm; trên model 1/100 thì nhân 100.

| Loại text | Ví dụ | Cao (mm) | Hệ số rộng |
|---|---|---|---|
| Tên bản vẽ, mặt bằng | MẶT BẰNG, DẦM D1-1… | 5.0 | 0.8 – 1.0 |
| Tên trục | 1, 2, 3… A, B, C | 3.5 | 0.8 – 1.0 |
| Tên chi tiết trên mặt bằng | D1-30X60, DP1-22X40, C1, W1… | 2 – 2.2 | 0.8 – 1.0 |
| Text ghi chú, dimension | BÊ TÔNG CẤP BỀN B22,5 (M300), SÀN HẠ CỐT… | 2 – 2.2 | 0.8 – 1.0 |

Text style có sẵn trong mẫu: `Arial` (w 1.0), `Archi- Arial` (w 0.8), `00 Arial 0.7`, `Text 1`, `ghi_chu 2` (đều dùng ARIAL.TTF); `ghi_chu 1` và `00 VnArialNarowH` dùng `VHARIALN.ttf` (font mã TCVN3 cũ); `ROMANS`.

## 3. Kích thước (Dim style)

- Style chuẩn cho model 1/100: **`A 1-100`** — DIMSCALE 100, mũi tên (DIMASZ) 1.0, DIMEXO 0, DIMEXE 1.0, chữ (DIMTXT) 2.0, DIMGAP 0.6, số lẻ 0.
- Style khác có sẵn: `A 1-150` (DIMSCALE 150), `A layout 100` (ghi kích thước trên layout, DIMLFAC 100).
- **Khoảng cách giữa các hàng dim = 2,5 lần chiều cao text của dim** (2.0 × 2.5 = 5 mm khi in, tức 500 trên model 1/100).
- Kích thước đặt trên layer `A-Dim` (dùng chung) hoặc `A-Dim@` (chỉ kiến trúc).

## 4. Ký hiệu — block chuẩn

**Dùng sẵn các block này, không rotate hay mirror.**

| Block | Công dụng | Attribute |
|---|---|---|
| `ky hieu truc` | Ký hiệu / số hiệu trục | `1` = tên trục |
| `kyhieu cat` | Ký hiệu cắt ở mặt cắt | `A` = số hiệu, `KT` = bản vẽ tham chiếu |
| `kyhieucatnho` | Ký hiệu cắt ở chi tiết | `A` |
| `lopvl` | Ghi chú lớp vật liệu trên mặt cắt | `A` (vd. S3), `KT` |
| `A$C715E008F` | Cốt cao độ mặt bằng, mặt cắt | `0.000` (vd. `SFL +/-0.000`, `FFL +0.050`) |
| `A$C44D30E1B` | Chỉ dẫn chi tiết trên mặt bằng / mặt cắt | `A` (vd. CT1), `KT` |
| block động `*U53` (gốc trong file mẫu) | Ký hiệu tên căn hộ – diện tích | `A` |
| `hoagio` | Hoa gió | — |
| — | Độ dốc: mái `i=5%`, nền `i=1%` | — |

Ký hiệu bản vẽ tham chiếu trong attribute `KT` có dạng `A.03.01`.

Block nội thất / thiết bị có sẵn: giường (`g.don1000x2000`, `g.doi1600x2000`), bàn (`ban6c 1100x2000`), tủ (`tu1500`), bếp (`mb-bep610x600`, `mb-bep650x650`), chậu rửa (`mb-sink500x800`), tủ lạnh (`mb-tulanh700x735`, `tulanh`), xí (`Xi4`, `mb-xibet2`), lavabo (`lavabo9`, `lavabo12`, `mb-lavabo6`), bồn tắm (`mb-bontam1500x670`), tivi, cửa sảnh (`cua sanh`).

## 5. Khung tên A1 — `Khung A1 TKCS`

- Khổ giấy A1, minh hoạ ở tỷ lệ 1/100 (chèn block khung theo tỷ lệ bản vẽ).
- Các ô: Tư vấn thiết kế (CÔNG TY CỔ PHẦN TƯ VẤN ARCHIVINA, địa chỉ, website), Chủ đầu tư, Dự án, Công trình, Hạng mục (KIẾN TRÚC), Giai đoạn (vd. TKCS), Tổng giám đốc, Chủ nhiệm dự án, Chủ trì thiết kế, Quản lý kỹ thuật, Thiết kế/vẽ, bảng sửa đổi (STT – Nội dung – Ngày nộp), Tên bản vẽ, Tỷ lệ, Ký hiệu bản vẽ, Khổ giấy.
- Tên bản vẽ và ký hiệu nhập qua block **`Tenbanve`**:
  - `KT-01` = ký hiệu bản vẽ, dạng **`A.01.06`**
  - `TEN` = tên bản vẽ, chữ hoa, hệ số rộng 0.7 (vd. `MẶT BẰNG TẦNG 3`). Block đã đặt sẵn chế độ tự xuống dòng.
- Chữ trong khung: chữ hoa cao 5 mm w 1; chữ hoa cao 3 mm w 1; chữ thường cao 3 mm w 0.8.
- Tên người vẽ và chữ ký: copy vào ô Thiết kế, vẽ.

## 6. Ghi chú trên mặt bằng

- Ghi chú các trục kỹ thuật dùng ký hiệu số (block `so`): trục kỹ thuật điện, điện nhẹ, nước, tăng áp, hút khói hành lang, hút mùi, hút mùi TMDV, bù khí, vị trí tủ PCCC.
- Thống kê đặt góc bản vẽ: Diện tích xây dựng, Diện tích căn hộ, Diện tích TMDV (m²); tỷ lệ ghi dạng `TỶ LỆ: 1/200`.
- Tên phòng kèm số hiệu không gian (layer `PAKT-NOTE`, vd. `9a`, `10b`) và diện tích (vd. `Locker nam - 44m2`).

## 7. Ghi chú thiết kế cửa chống cháy (trong mẫu)

- Cửa thép chống cháy 1 cánh: 1200 + 57 (khung) + 57 (khung) + 10~20 (khe hở kỹ thuật 2 bên) ≈ **1330**. Nếu tính trừ tay đẩy thì không đảm bảo chiều rộng thông thủy thoát nạn 1200.
- Không có tay đẩy: < 400 mm.
