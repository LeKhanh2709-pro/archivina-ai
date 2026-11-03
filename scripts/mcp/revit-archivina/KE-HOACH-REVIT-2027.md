# Kế hoạch chuyển MCP `revit-archivina` + skill `/dung-ket-cau-revit` sang Revit 2027 / .NET 10

> Lập ngày 2026-10-24. **TRẠNG THÁI: CHƯA DUYỆT.** Người duyệt: BIM Manager.
> Nguồn: `anhnh-archivina/archivina-claude-skills` (bản fork `antt-cell/archivina-claude-skills`, commit giống hệt bản gốc ngày 2026-10-24), thư mục `mcp/revit-archivina` và `skills/dung-ket-cau-revit`.
> Mã trong thư mục này đang là **bản gốc Revit 2026, chưa sửa**, để so sánh khác biệt khi chuyển đổi.

## Mục tiêu
1. Add-in + MCP chạy trên **Revit 2027, `net10.0-windows`**.
2. Mọi phần tử, view, vật liệu, transaction tạo ra theo **chuẩn tên ARV** (`standards/naming-iso19650.md` mục 7).
3. Tuân thủ CLAUDE.md mục 4 (ghi có kiểm soát), 5 (quy tắc code), 8 (bảo mật), 9 (duyệt công cụ).
4. Thay MCP cộng đồng `mcp-servers-for-revit` (chưa có bản 2027) bằng MCP nội bộ này.

## Tiến độ
| Giai đoạn | Trạng thái |
|---|---|
| 0 – Chuẩn bị | **Xong 2026-10-24**: .NET SDK 10.0.402, Python 3.13.15 (`mcp` 2.3.0, `ezdxf`, `shapely`), Revit 2027 tại `C:\Program Files\Autodesk\Revit 2027` (27.3.0.28, runtime `net10.0`). Chưa tạo nhánh `feature/…`, Q1 chưa chốt |
| 1 – Build 2027 | **Xong 2026-10-24** cho 1.1–1.4, 1.7: build sạch 0 cảnh báo; Revit 2027 nạp add-in; `rv_ket_noi` trả về Revit 2027, bridge 1.0.2, core 1.5.1. Còn 1.5 (rà API) – chưa chạy các lệnh dựng trên 2027 |
| 2 – Đổi tên ARV | Chưa làm |
| 3 – Tuân thủ CLAUDE.md | Chưa làm |
| 4 – Kiểm thử | Chưa làm |
| 5 – Duyệt, triển khai | Đã đăng ký `.mcp.json` để thử nghiệm (chưa duyệt); MCP cũ đã gỡ |

## Giai đoạn 0 – Chuẩn bị (≈ 0,5 ngày)
| # | Việc | Ghi chú |
|---|---|---|
| 0.1 | Cài **.NET 10 SDK** trên máy build | `winget install Microsoft.DotNet.SDK.10` |
| 0.2 | Xác định thư mục cài Revit 2027 (chứa `RevitAPI.dll`, `RevitAPIUI.dll`) | Thay mặc định `D:\Revit\Revit 2026` |
| 0.3 | Xác định Python dùng cho MCP + script (`mcp`, `ezdxf`, `shapely`, `matplotlib`) | Không ghi cứng `C:\Users\Admin\...`; khai báo trong `.mcp.json` |
| 0.4 | Chốt **thư mục bản sao làm việc** và **WorkRoot** (biến `REVIT_MCP_WORK_ROOT`) | Xem câu hỏi mở Q1 |
| 0.5 | Tạo nhánh `feature/revit-archivina-2027` | Theo CLAUDE.md mục 9 |

## Giai đoạn 1 – Build lại cho Revit 2027 (≈ 1–2 ngày)
| # | File | Thay đổi |
|---|---|---|
| 1.1 | `bridge/ArchivinaRevitMcp.csproj`, `core/ArchivinaRevitMcp.Core.csproj` | `TargetFramework` `net8.0-windows` → `net10.0-windows`; `RevitDir` mặc định → thư mục Revit 2027 |
| 1.2 | `build.ps1` | `RevitDir` mặc định 2027; `Addins\2026` → `Addins\2027`; dò `dotnet` SDK 10; giữ UTF-8 có BOM |
| 1.3 | `core/Structure.cs` dòng ~345 | Đường dẫn family template `RVT 2026` / `Revit Steel Connections 2026` → 2027 (nên dò theo `Application.FamilyTemplatePath` thay vì ghi cứng) |
| 1.4 | `revit_mcp.py`, `bridge/Bridge.cs`, `core/Commands.cs` | Thông điệp "Revit 2026" → "Revit 2027"; `rv_ket_noi` kiểm tra `VersionNumber == "2027"` |
| 1.5 | Toàn bộ `core/*.cs` | Rà API đổi/bỏ ở Revit 2027 (đọc *What's New* của Revit 2027 SDK); giữ `ElementId.Value` |
| 1.6 | `bridge/Bridge.cs` | Kiểm tra lại cơ chế nạp nóng `AssemblyLoadContext` và `JsonSerializerOptions.TypeInfoResolver` trên .NET 10 |
| 1.7 | `.gitignore` | Bỏ qua thư mục `addin/` và `core/bin/out` (kết quả build) |

Đạt khi: build sạch không cảnh báo mới; Revit 2027 nạp add-in, có tab **Archivina MCP**; `rv_ket_noi` trả về Revit 2027.

## Giai đoạn 2 – Đổi tên theo chuẩn ARV (≈ 1 ngày)
| Vị trí | Hiện tại | Đổi thành |
|---|---|---|
| `core/Structure.cs` 4, 26–27 | `Archivina_Cot BTCT chu nhat`, `Archivina_Dam BTCT chu nhat` | `ARV_StrColumn_RC_Rect`, `ARV_StrFraming_RC_Rect` |
| `core/Structure.cs` (type) | `Cot bxh`, `Dam bxh` | `<b>x<h>` |
| `core/Structure.cs` 234; `doc_mb_ket_cau.py` 845, 848 | `Archivina_San BTCT <dày>` | `ARV_Floor_RC_<dày>` |
| `core/Modeling.cs` 512, 537 | `Archivina_Cot bxh`, `Archivina_Vach BTCT <dày>` | `<b>x<h>`, `ARV_Wall_RC_<dày>` |
| `doc_mb_ket_cau.py` 689; `core/Modeling.cs` 491 | `Archivina_BT <cấp>`, `Archivina_BTCT (chua xac dinh)`, `Archivina_BTCT` | `ARV_BT_<cấp>`, `ARV_BT_ChuaXacDinh` |
| `core/Structure.cs` 160, 415 | Parameter family `Vat lieu KC` | `ARV_VatLieu_KC` (xem Q3) |
| `doc_mb_ket_cau.py` 739, 752 | Level `Tầng n` | `L01…`, `RF`, `Bn`, `TR` theo bảng đổi tầng |
| `core/Structure.cs` 91–98 | View `KC - <level>` | `S_MB_<Level>_Ket cau` |
| `core/Structure.cs` 259; `doc_mb_ket_cau.py` 755; `Modeling.cs` 103 | `Archivina_3D KC`, `Archivina_3D` | `S_3D_ZZ_Kiem tra KC` |
| `core/*.cs`, `revit_mcp.py` (≈ 30 chỗ) | Transaction `Claude MCP - …` | `ARV - …` (tiếng Việt) |
| `core/Structure.cs` 452–455, 513–516 | Reference plane `Archivina_Trai/Phai/Truoc/Sau/Dinh/Day` | `ARV_Trai/…` (nội bộ family) |

Tương thích ngược: khi gặp dự án đã có tên `Archivina_*` (dựng bằng bản 2026), công cụ **không đổi tên** phần tử có sẵn, chỉ báo trong `canh_bao` (đúng quy tắc không sửa family/type có sẵn).

## Giai đoạn 3 – Tuân thủ CLAUDE.md (≈ 1 ngày)
| # | Quy tắc | Việc |
|---|---|---|
| 3.1 | Mục 5: đổi đơn vị bằng `UnitUtils` | Thay `const double FT = 304.8`, `FT2`, `FT3` (`Commands.cs` 81–83, `Modeling.cs` 27) bằng `UnitUtils.ConvertToInternalUnits / ConvertFromInternalUnits` với `UnitTypeId.Millimeters`, `SquareMeters`, `CubicMeters` |
| 3.2 | Mục 5: parameter qua GUID / BuiltIn | Sau khi có shared parameter file: `ARV_VatLieu_KC` lấy theo GUID; tạm thời giữ `LookupParameter` có ghi chú lý do |
| 3.3 | Mục 4: kiểm tra bộ môn | Lệnh ghi đọc mã Role trong tên file: `rv_dung_ket_cau` chỉ chạy khi Role = `S` hoặc dự án do Claude tạo; `rv_dung_can_ho` chỉ khi Role = `A` |
| 3.4 | Mục 4: CDE | Thêm vào `Safety.cs` danh sách thư mục cấm ghi: `\SHARED\`, `\PUBLISHED\`, `\ARCHIVED\` (bên cạnh `\02-Ban-Ve-Goc\`); bản sao hợp lệ: thư mục chốt ở Q1 |
| 3.5 | Mục 5: log | Ghi log mỗi lệnh ghi (thời gian, user, file, số phần tử tạo/sửa/xoá) vào `%APPDATA%\ARV\Logs\` |
| 3.6 | Mục 8: không ghi cứng đường dẫn | Bỏ `H:\@AI Claude Test`, `D:\Revit\...`, `C:\Users\Admin\...`; dùng biến môi trường / tham số |
| 3.7 | Mục 9 | Mỗi file nguồn có dòng `TRẠNG THÁI: CHƯA DUYỆT` cho tới khi BIM Manager duyệt |

## Giai đoạn 4 – Kiểm thử trên Revit 2027 (≈ 1–2 ngày)
1. **Chốt chặn an toàn** – chạy lại bộ 20 ca của bản 2026 (từ chối ghi file gốc, từ chối workshared, không ghi đè, chỉ xoá phần tử Claude tạo, file gốc giữ nguyên SHA-256) + ca mới 3.3 (sai bộ môn) và 3.4 (thư mục `SHARED`/`PUBLISHED`).
2. **Tool đọc** – chạy lại 13 ca đọc (`rv_thong_tin`, `rv_liet_ke`, `rv_khoi_luong`, `rv_phong`, `rv_canh_bao`, `rv_chup_view`, `rv_xuat_dwg`…).
3. **Dựng kết cấu** – 1 bộ MB KC mẫu (≥ 3 tầng, có cột dựng, lỗ mở, sàn hạ cốt): so số trục / level / cột / dầm / sàn với `ket_qua.json`; kiểm tra tên ARV ở mọi phần tử, view, vật liệu, mục Undo.
4. **Đơn vị** – so khối lượng bê tông trước / sau khi đổi sang `UnitUtils` (chênh = 0).
5. Ghi kết quả vào mục "Đã kiểm tra" của `README.md`.

## Giai đoạn 5 – Duyệt và triển khai (≈ 0,5 ngày)
1. Ghi `tools/CHANGELOG.md`; BIM Manager review mã + kết quả kiểm thử; merge `feature/…` → `main`.
2. Đăng ký MCP trong `.mcp.json` (khoá `revit-archivina`), bật trong `.claude/settings.json` (`enabledMcpjsonServers`). Quyền đã khai sẵn: tool đọc **allow**, tool ghi **ask** (Claude Code hỏi người dùng mỗi lần).
3. Gỡ `mcp-servers-for-revit` (MCP cộng đồng) khỏi `.mcp.json` / `settings.json` và add-in Revit 2026.
4. Bỏ dòng "Trạng thái: chưa duyệt" trong `SKILL.md`; cập nhật CLAUDE.md mục 12.

## Câu hỏi mở (cần BIM Manager chốt)
- **Q1.** Thư mục bản sao làm việc: dùng `03-Ban-Sao-Lam-Viec` như bản gốc, hay `WIP\<người dùng>\` trong CDE? WorkRoot cho thử nghiệm đặt ở đâu?
- **Q2.** Cho phép công cụ **tạo** Grid / Level trong dự án KC mới do Claude tạo (đã ghi ngoại lệ trong CLAUDE.md mục 4) – có cần BIM Manager duyệt từng lần không?
- **Q3.** `ARV_VatLieu_KC` là parameter family riêng, hay dùng thẳng `Structural Material` (built-in) để khỏi cần shared parameter?
- **Q4.** Tên tab ribbon giữ `Archivina MCP` hay đổi `ARV MCP`?
- **Q5.** Template S chuẩn của công ty cho Revit 2027 (nếu có) thay cho `Structural Analysis-DefaultMetric.rte`.
- **Q6.** Repo nguồn `anhnh-archivina/archivina-claude-skills` đang **PUBLIC** – đề nghị chuyển Private trước khi tiếp tục phát triển (CLAUDE.md mục 8).
