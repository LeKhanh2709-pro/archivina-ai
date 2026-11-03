# Quy ước đặt tên theo ISO 19650 – Archivina (ARV)

> Nếu BEP của dự án quy định khác thì làm theo BEP. Ô ghi *[cần xác nhận]* phải được BIM Manager chốt.

## 1. Tên file (container)

```
<Project>-<Originator>-<Volume>-<Level>-<Type>-<Role>-<Number>
PRJ      -ARV         -T1      -TY     -M3    -A     -0001
```

| Trường | Ý nghĩa | Giá trị |
|---|---|---|
| Project | Mã dự án (2–6 ký tự) | Theo `projects/<mã>/CLAUDE.md` |
| Originator | Đơn vị lập | `ARV` (Archivina) |
| Volume | Khối/tháp | `ZZ` toàn bộ, `XX` không áp dụng, `T1`, `T2`… tháp |
| Level | **Mô hình (`M3`)**: nhóm tầng | `BS` hầm, `PD` khối đế, `TY` tầng điển hình, `RF` mái/tum/kỹ thuật mái, `ZZ` nhiều nhóm |
| | **Bản vẽ, bảng biểu (`DR`, `SH`)**: tầng cụ thể | `B3`, `B2`, `B1`, `01`…`99`, `RF`; `ZZ` nhiều tầng, `XX` không áp dụng |
| Type | Loại thông tin | `M3` mô hình 3D, `DR` bản vẽ, `SH` bảng biểu, `RP` báo cáo, `MI` biên bản, `SP` chỉ dẫn kỹ thuật |
| Role | Bộ môn | `A` Kiến trúc, `S` Kết cấu, `C` Điều phối/federated (quy ước nội bộ) |
| Number | Số thứ tự | 4 chữ số `0001` |

Ví dụ:
- `PRJ-ARV-T1-BS-M3-A-0001.rvt`: mô hình kiến trúc tầng hầm tháp T1
- `PRJ-ARV-T1-TY-M3-S-0001.rvt`: mô hình kết cấu tầng điển hình tháp T1
- `PRJ-ARV-ZZ-ZZ-M3-C-0001.rvt`: mô hình tổng hợp (federated)
- `PRJ-ARV-T1-05-DR-A-1005.pdf`: bản vẽ mặt bằng tầng 5 tháp T1

Regex kiểm tra tên file mô hình:
```
^[A-Z0-9]{2,6}-ARV-(ZZ|XX|T\d)-(BS|PD|TY|RF|ZZ)-M3-[ASC]-\d{4}$
```

## 2. Trạng thái và phiên bản

| Mã | Ý nghĩa |
|---|---|
| S0 | WIP |
| S1–S4 | Shared (phối hợp / thông tin / duyệt / phê duyệt) |
| A1… | Published (phát hành) |
| P01.01 | Phiên bản sơ bộ (Preliminary) |
| C01 | Phiên bản hợp đồng (Contractual) |

## 3. Level

`B3, B2, B1, L01, L02, …, RF`; tầng kỹ thuật/chuyển dùng `TR`. Thêm hậu tố bộ môn nếu cần tách cao độ, ví dụ `L05_FFL` (hoàn thiện, A) và `L05_SSL` (kết cấu, S) *[cần xác nhận]*.

## 4. View *[cần xác nhận]*

```
<Bộ môn>_<Loại view>_<Tầng/Vị trí>_<Mô tả>
A_MB_L05_Mat bang kien truc
S_MB_L05_Mat bang dam san
A_MC_1-1_Mat cat ngang
WIP_<tên người>_<mô tả>      ← view làm việc cá nhân, không đưa lên sheet
```
Loại view: `MB` mặt bằng, `MD` mặt đứng, `MC` mặt cắt, `CT` chi tiết, `3D`, `TK` thống kê.

## 5. Sheet *[cần xác nhận]*

```
<Bộ môn>-<Nhóm><Số>      ví dụ A-101, S-201
```
Nhóm: `0` chung, `1` mặt bằng, `2` mặt đứng, `3` mặt cắt, `5` chi tiết, `9` thống kê.

## 6. Family

```
ARV_<Category>_<Mô tả>_<Biến thể>
ARV_Door_Swing1_900x2200
ARV_StrColumn_RC_Rect
```
Không đặt tên family có dấu tiếng Việt. Không dùng family mặc định của Autodesk trong mô hình phát hành.

## 7. Mô hình kết cấu BTCT dựng tự động (MCP `revit-archivina`, skill `/dung-ket-cau-revit`)

Áp dụng cho mọi phần tử, view, transaction do công cụ tạo ra. Bảng dưới thay cho tên `Archivina_*` trong mã gốc Revit 2026.

| Đối tượng | Tên ARV | Ví dụ | Tên cũ (2026) |
|---|---|---|---|
| File dự án | `<PRJ>-ARV-<Vol>-ZZ-M3-S-<Số>.rvt` | `PRJ-ARV-T1-ZZ-M3-S-0001.rvt` | tự đặt |
| Family cột | `ARV_StrColumn_RC_Rect` | | `Archivina_Cot BTCT chu nhat` |
| Type cột | `<b>x<h>` (mm) | `400x600` | `Cot bxh`, `Archivina_Cot bxh` |
| Family dầm | `ARV_StrFraming_RC_Rect` | | `Archivina_Dam BTCT chu nhat` |
| Type dầm | `<b>x<h>` (mm) | `220x400` | `Dam bxh` |
| Type sàn | `ARV_Floor_RC_<dày>` | `ARV_Floor_RC_150` | `Archivina_San BTCT 150` |
| Type vách (khi dựng) | `ARV_Wall_RC_<dày>` | `ARV_Wall_RC_250` | `Archivina_Vach BTCT 250` |
| Vật liệu | `ARV_BT_<cấp bền>`; chưa có: `ARV_BT_ChuaXacDinh` | `ARV_BT_B25` | `Archivina_BT B25`, `Archivina_BTCT (chua xac dinh)` |
| Parameter vật liệu trong family | `ARV_VatLieu_KC` | | `Vat lieu KC` |
| Level | Theo mục 3: `B3…B1`, `L01…L99`, `RF`, `TR`. Level của mô hình S = cốt mặt sàn kết cấu (SSL), không thêm hậu tố | `Tầng 2 (+3.850)` → `L02` | `Tầng n` |
| Mặt bằng kết cấu | `S_MB_<Level>_Ket cau` | `S_MB_L02_Ket cau` | `KC - Tầng n` |
| View 3D kiểm tra | `S_3D_ZZ_Kiem tra KC` | | `Archivina_3D KC` |
| Transaction / TransactionGroup | `ARV - <việc, tiếng Việt>` | `ARV - Dựng kết cấu từ CAD` | `Claude MCP - …` |

Đổi tầng bản vẽ sang level: "TẦNG 1" → `L01` (chân cột ±0.000), "TẦNG n" → `L0n`/`Lnn`, "MÁI" → `RF`, "TẦNG HẦM n" → `Bn`, tầng chuyển/kỹ thuật → `TR` *[cần xác nhận khi có nhiều tầng TR]*.
