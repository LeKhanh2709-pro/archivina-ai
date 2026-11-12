---
name: ai-revit-dong-nghiep
description: "Bộ AI REVIT của đồng nghiệp (D:\\AI\\AI REVIT) đã áp dụng 2026-11-03 — MCP revit-archivina, skill bim-qaqc / dung-ket-cau-revit, 17 Dynamo mới, chuẩn ISO 19650"
metadata:
  node_type: memory
  type: project
  originSessionId: 102dc5a2-4c25-4245-abc5-02ab242d9c1a
  modified: 2026-11-03T03:52:35.676Z
---

`D:\AI\AI REVIT\` = repo `antt-cell/arv-bim-claude` (commit `b7381e6`, máy đồng nghiệp user ANAN, gốc `D:\00. AI REVIT`). Người dùng bảo "áp dụng tất cả" 2026-11-03. Giữ nguyên thư mục gốc (gitignore), chỉ chép sang:
- MCP `revit-archivina` → `D:\AI\scripts\mcp\revit-archivina` (build .NET 10, manifest Addins\2027, `.mcp.json` + quyền trong `.claude\settings.json`; WorkRoot mặc định `D:\AI\_tmp\revit-mcp`). Chưa kết nối thử với Revit.
- Skill `bim-qaqc`, `dung-ket-cau-revit` → `.claude\skills\` (mục "Áp dụng tại D:\AI").
- Dynamo `file mau revit\dynamo`: +17 graph, 9 graph thay bản mới; ARV Tools 44 nút. Xem [[bo-dynamo-arv-file-mau]], [[pyrevit-arvtools-revit2027]].
- `standards\` naming-iso19650 / lod-matrix / required-parameters, `projects\_TEMPLATE`.

**Why:** đồng nghiệp phát triển tiếp cùng bộ công cụ ARV trên máy khác; bản của họ mới hơn và nhiều tool đã được BIM Manager duyệt.
**How to apply:** khi nhận bản AI REVIT mới hơn thì so từng file (mã Python trong .dyn vs .py cục bộ), sao lưu rồi mới thay; input lưu trong .dyn của họ thường là input dự án (HQV, MBKC tầng 30-40) — chỉ khác input thì giữ bản mình. Dùng MCP: tool ghi chỉ khi người dùng bấm "Cho phép ghi" trong Revit + file bản sao, hỏi trước mỗi lệnh.
