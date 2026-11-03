# Parameter bắt buộc cho QA/QC

> **PLACEHOLDER: nhóm BIM điền và BIM Manager duyệt.** Skill `/bim-qaqc` đọc các bảng dưới đây để kiểm tra mô hình.
> Cột "Giai đoạn" ghi giai đoạn bắt đầu bắt buộc (TKCS / TKKT / TKBVTC). Cột "Quy tắc" ghi điều kiện hợp lệ: không rỗng, regex, hoặc danh sách giá trị.

## Thông tin dự án (Project Information)

| Parameter | Kiểu | Giai đoạn | Quy tắc |
|---|---|---|---|
| Project Number | Text | TKCS | Không rỗng, khớp mã dự án |
| Project Name | Text | TKCS | Không rỗng |
| ARV_Phase | Text | TKCS | `TKCS` \| `TKKT` \| `TKBVTC` |
| ... | | | |

## Kiến trúc (A)

| Category | Parameter | Kiểu | Giai đoạn | Quy tắc |
|---|---|---|---|---|
| Rooms | Name | Text | TKCS | Không rỗng |
| Rooms | Number | Text | TKCS | Không trùng |
| Doors | Mark | Text | TKKT | Không rỗng, không trùng |
| Walls | ARV_Ma_Cau_Kien *(ví dụ)* | Text | TKKT | ... |
| ... | | | | |

## Kết cấu (S)

| Category | Parameter | Kiểu | Giai đoạn | Quy tắc |
|---|---|---|---|---|
| Structural Columns | Structural Material | Material | TKKT | Không rỗng |
| Structural Columns | Mark | Text | TKKT | Không rỗng |
| Structural Framing | Structural Material | Material | TKKT | Không rỗng |
| Floors (Structural) | ARV_Mac_Be_Tong *(ví dụ)* | Text | TKKT | `B30` \| `B35` \| ... |
| ... | | | | |

## Shared parameter file
- Đường dẫn file shared parameter: *[cần điền]*
- GUID của các parameter `ARV_*`: *[cần điền]*
