---
name: dung-ket-cau-revit
description: Dựng MÔ HÌNH KẾT CẤU BTCT trong Revit 2027 từ MẶT BẰNG KẾT CẤU AutoCAD (.dwg/.dxf, mm) của Archivina – mặt bằng định vị cột + mặt bằng kết cấu dầm sàn từng tầng (tên "MẶT BẰNG KẾT CẤU SÀN TẦNG n ( CỐT +x.xxx )"): level theo cốt, lưới trục (tên từ bóng trục), cột kết cấu (polyline layer cột, mã C1…, cột dựng), dầm (cặp nét song song thấy / khuất + nhãn "D1-22X40" theo cm), sàn kết cấu (biên ngoài, lỗ mở dấu X, vùng hạ / nâng cốt theo hatch + chú giải), family ARV tự tạo từ .rft, mặt bằng kết cấu mỗi tầng + view 3D. Dùng khi người dùng nhờ dựng / chuyển / mô hình hoá kết cấu, cột dầm sàn sang Revit từ bản vẽ CAD, "dựng mô hình KC", "model kết cấu", "đưa mặt bằng kết cấu vào Revit", kể cả khi không nhắc tên skill. Không dùng cho móng / cọc / vách / cầu thang (chưa thuộc phạm vi), không dùng cho kiến trúc.
---

# /dung-ket-cau-revit – Dựng mô hình kết cấu Revit từ mặt bằng KC AutoCAD

> **Trạng thái: CHƯA DUYỆT, chờ build cho Revit 2027.** Mã gốc (MCP `revit-archivina`) mới chạy trên Revit 2026 và còn tạo tên `Archivina_*`.
> Kế hoạch chuyển đổi: [tools/mcp/revit-archivina/KE-HOACH-REVIT-2027.md](../../../tools/mcp/revit-archivina/KE-HOACH-REVIT-2027.md).
> Trước khi bản 2027 được BIM Manager duyệt, **không chạy bước 5 (ghi)** trên máy dự án; chỉ chạy bước 1–4 để kiểm tra nhận diện.

Quy tắc chi tiết: [references/quy-tac-dung-ket-cau.md](references/quy-tac-dung-ket-cau.md) – **đọc trước khi chạy**.
Đặt tên: [standards/naming-iso19650.md](../../../standards/naming-iso19650.md) mục 7. Quy tắc ghi mô hình: CLAUDE.md mục 4 và 12.

## Áp dụng tại D:\AI (bổ sung 2026-11-03, ưu tiên hơn phần dưới khi mâu thuẫn)
- Nguồn: bộ `AI REVIT` của đồng nghiệp (commit `b7381e6`); bản gốc giữ nguyên ở `D:\AI\AI REVIT\.claude\skills\dung-ket-cau-revit\`.
- Tuân thủ QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`. Bản vẽ đầu vào và thư mục kết quả trên ổ `D:` (thư mục tạm `D:\AI\_tmp\`); DWG → DXF bằng Core Console trên **bản sao** như mục "Đọc file DWG" trong CLAUDE.md.
- Đường dẫn: MCP + kế hoạch 2027 ở `D:\AI\scripts\mcp\revit-archivina\`; `standards/` → `D:\AI\standards\`; `projects/` → `D:\AI\projects\`; `tools/CHANGELOG.md` → ghi vào README của công cụ / CLAUDE.md của D:\AI.
- Chạy nhận diện bằng venv máy này: `D:\AI\_tools\venv\Scripts\python.exe -I D:\AI\.claude\skills\dung-ket-cau-revit\scripts\doc_mb_ket_cau.py <ban_ve.dxf> --ra D:\AI\_tmp\<thư mục> …` (venv có `ezdxf`, `shapely`, `matplotlib`).
- `rv_luu_ban_sao` / `rv_tao_du_an` mặc định lưu vào `D:\AI\_tmp\revit-mcp\03-Cong-Cu\05-Skill-Test\ban-sao-revit\` (chốt `Safety.cs` đã chỉnh cho máy này). Không có `projects/<mã>/CLAUDE.md` thì hỏi mã dự án, không tự đặt.
- Bước 5 (ghi) vẫn theo trạng thái gốc: MCP CHƯA DUYỆT → chỉ chạy trên dự án mới / bản sao thử, hỏi người dùng trước mỗi lệnh.

## Phạm vi
- Đầu vào: **mặt bằng kết cấu KC** (MB định vị cột + MB kết cấu dầm sàn mỗi tầng). Không tự đề xuất hệ kết cấu từ MB kiến trúc.
- Dựng: **trục, level, cột, dầm, sàn** BTCT. Vách / lõi, móng / đài / cọc, cầu thang, dầm cong, cột tròn: **chưa dựng** – gặp thì ghi "chưa dựng" trong báo cáo. Vách / lõi dùng tạm Dynamo `ARV_TaoCotVachTuCAD`.
- Dựng vào **dự án KC MỚI** do Claude tạo (bộ môn S), không dựng vào file gốc, file central hay file của bộ môn khác.

## Quy trình
1. **Xác định dự án:** đọc `projects/<mã>/CLAUDE.md` (mã dự án, khối, template, thư mục bản sao làm việc). Thiếu thì hỏi.
2. **Đọc bản vẽ (chỉ đọc, bản sao):** chuyển DWG → DXF vào thư mục bản sao làm việc của dự án.
3. **Hỏi trước khi đọc** (không tự đặt):
   - Cấp bền bê tông **cột / dầm / sàn** (ví dụ B25 / B22.5). Thiếu → vật liệu `ARV_BT_ChuaXacDinh` và ghi trong báo cáo.
   - Nếu bản vẽ có **cột dựng** (layer `S-Cot dung`) ở tầng trên cùng: đỉnh cột ở cốt nào (level `RF`).
4. **Nhận diện:**
   ```
   python -I .claude/skills/dung-ket-cau-revit/scripts/doc_mb_ket_cau.py <ban_ve.dxf> --ra <thu_muc> --vat-lieu "cot=B25;dam=B22.5;san=B22.5" [--tang-tren "RF=17350"]
   ```
   Layer khác chuẩn: `--layer-cot`, `--layer-cot-dung`, `--layer-dam`, `--layer-truc` (regex). Kết quả: `ket_qua.json` (tóm tắt, `can_hoi`, `canh_bao`), `spec_ket_cau.json`, ảnh `xem_lai_<tầng>.png`.
   **Duyệt với người dùng:** gửi ảnh xem lại, tóm tắt level / số cột, dầm, sàn / loại tiết diện; **hỏi từng mục `can_hoi`** (dầm lệch nhãn, dầm thiếu nhãn, hatch không có chú giải, cột chồng khác tiết diện, cột không có tầng trên, thiếu cốt / chiều dày sàn). Sửa bằng tham số rồi chạy lại; mục không sửa được bằng tham số → sửa tay `spec_ket_cau.json` (ghi rõ đã sửa gì) hoặc báo người vẽ sửa bản vẽ.
5. **Dựng (GHI – theo CLAUDE.md mục 4 "Ghi mô hình có kiểm soát"):**
   - Hỏi người dùng xác nhận: tên file mới, template, số phần tử sẽ tạo.
   - `rv_ket_noi` (Revit 2027 đang mở, tab Archivina MCP, server chạy).
   - `rv_tao_du_an(duong_dan_rvt="<thư mục bản sao>\<PRJ>-ARV-<Vol>-ZZ-M3-S-<Số>.rvt", template=<template S của dự án>)` → file .rvt mới (không ghi đè).
   - Người dùng tự bấm **Archivina MCP > Cho phép ghi**. Claude không được nhắc người dùng bỏ qua bước này.
   - `rv_dung_ket_cau(spec_ket_cau.json)` – lần đầu tạo family `ARV_StrColumn_RC_Rect` / `ARV_StrFraming_RC_Rect` từ `Metric Structural Column.rft` / `Metric Structural Framing - Beams and Braces.rft`. Lỗi → RollBack toàn bộ; thành công → 1 mục Undo `ARV - Dựng kết cấu từ CAD`.
6. **Kiểm tra sau dựng (chỉ đọc):** `rv_thong_tin` (level, cảnh báo), `rv_khoi_luong` cho `OST_StructuralColumns`, `OST_StructuralFraming`, `OST_Floors` theo từng level – so số lượng / tiết diện với `ket_qua.json`; `rv_canh_bao`; `rv_chup_view` view `S_3D_ZZ_Kiem tra KC` và 1–2 mặt bằng `S_MB_<Level>_Ket cau`.
7. **Ghi nhận:** thêm dòng vào `tools/CHANGELOG.md` nếu có sửa công cụ; báo BIM Manager trước khi chuyển mô hình sang `SHARED`.

## Báo cáo
(1) Kết quả: đã dựng / dừng chờ trả lời; số trục, level, cột, dầm, sàn theo tầng; file .rvt. (2) Việc cần quyết định (`can_hoi` còn lại). (3) Chi tiết: loại tiết diện, vùng hạ / nâng cốt, cảnh báo Revit. (4) Chưa kiểm tra được / chưa dựng: móng, vách, cầu thang, xref chưa nạp, hatch lạ, font thiếu.

## Bẫy đã biết
- Bóng trục / nhãn nằm trong block lồng: ATTRIB phải nhân ma trận block cha (đã xử lý).
- Ô lỗ mở: chỉ nhận ô chữ nhật có **đúng 2 đường chéo** nối góc đối; polygonize phải bỏ đường chéo (không thì ô bị chia tam giác).
- Cột cắt (dưới sàn) và cột dựng (trên sàn) cùng vị trí là 2 đoạn cột khác nhau – không gộp.
- Dầm liên tục qua dầm phụ chỉ ghi nhãn 1 lần: nét dầm gộp qua khe ≤ 600 mm, nhịp chỉ chia theo cột; đầu dầm không tựa cột kéo về tim dầm vuông góc.
- Chú giải sàn khác nhau theo từng tờ (ANSI37 = hạ 335 ở T2 nhưng hạ 50 ở T5) – luôn đọc chú giải của đúng tờ.
- Revit: nạp family từ family document phải ở NGOÀI transaction của dự án (add-in làm trước TransactionGroup).
