---
name: revit-vang-locale-cpython
description: Revit 2027 văng Unmarshaller.cpp 357 / corruptData ExportPatternKey sau khi chạy script CPython của pyRevit – do locale; chữa bằng setlocale C
metadata:
  node_type: memory
  type: project
  originSessionId: f17cdaa7-edbb-48e3-aaad-1b9eb2580468
  modified: 2026-11-13T14:06:19.927Z
---

Revit 2027 thoát "An unrecoverable error has occurred" (journal: `ArchiveException 105 corruptData ... ExportPatternKey`,
`Assertion failed: line 357 ... Unmarshaller.cpp`) khi nạp phần tử ExportDWGSettings (model HQV Site: `AV-Export Cad`, bảng
mẫu hatch tên có dấu) SAU KHI engine CPython của pyRevit đã khởi động. CPython đặt `LC_CTYPE = English_United States.1252`
cho cả tiến trình → thứ tự so sánh chuỗi của Revit đổi → báo hỏng dữ liệu.

**Why:** tìm ra 2026-11-12 tối khi chạy 4 nút HS TKBVTC trên bản sao Site (văng 6/6 phiên ở lần chuyển view đầu; trước đó
ghi nhận "văng ngẫu nhiên ~1/2 phiên"). `_tmp\site_duyet\diag.py` chứng minh: đặt lại locale C thì nạp + chuyển view được.

**How to apply:** script thử CPython chạy trong Revit (nút ARVTest*, chay.py) đặt ở dòng đầu, trước khi đụng model:
`import locale; locale.setlocale(locale.LC_ALL, "C")`. Nút riêng [[nut-ho-so-duyet]] có dòng này ở đầu script. Các nút
thật của ARVTools (Archivina) đã được chữa 2026-11-13 21:01 sau khi người dùng đồng ý ("Có, thêm vào"):
`lib\arv_dynamo_host.py` có `dat_locale_c()` gọi lúc import (mọi script.py / config.py CPython của Archivina import module
này đầu tiên) và ở đầu `run_button` / `run_core`. Thử nền bấm thẳng nút Archivina trên bản sao HQV Site
(`_tmp\tag_archivina\thu_locale.py`): `LC_CTYPE` 1252 → `C` sau import, đặt lại locale xấu thì `run_button` tự trả về `C`,
nạp `AV-Export Cad` + chuyển 3 view không văng; chưa chạy phép đối chứng không có dòng chữa, người dùng chưa bấm.
Extension mới có script CPython riêng (không import `arv_dynamo_host`) thì tự đặt dòng này ở đầu. Gặp Revit nền văng ở lần
chuyển view đầu thì kiểm locale trước, đừng chỉ chạy lại. Liên quan: [[pyrevit-arvtools-revit2027]],
[[nut-hs-tkbvtc-nhan-link]], [[nut-moi-extension-rieng]].
