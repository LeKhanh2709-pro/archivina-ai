---
name: ngan-chay-lan-revit-dang-do
description: "Công cụ Revit ngăn cháy lan trục / HKT (nút một chạm) — bản v4 bo lõi tường được người dùng duyệt 2026-10-28, chưa áp lên G19 thật"
metadata:
  node_type: memory
  type: project
  originSessionId: a672e335-b6af-4609-8e94-6faf49c726a9
  modified: 2026-10-28T04:14:16.295Z
---

Người dùng yêu cầu 2026-10-27: làm nút pyRevit một chạm Ngăn cháy lan giống nút Chống thấm (người dùng tự tạo view + đặt sheet). `scripts\dynamo\NganChay_TrucHKT.py/.json/.dyn`, nút `ARV Tools` → `Hồ sơ` → `Ngăn cháy lan` (BUTTONS + MOT_CHAM "chay lan" trong builder). Chi tiết ghi trong CLAUDE.md và `scripts\pyrevit\README.md`.

**Trạng thái 2026-10-28:** người dùng duyệt bản v4 ("ngăn cháy lan cũng OK rồi"): quét lưới dấu chân tường theo dải lõi, nối đầu tường hở ≤ 400 mm, đóng miệng hốc U, ≤ 3 m2, lòng ≥ 80 mm, bo mép lõi tường thô ([[bo-sat-tuong-tho]]); 38 ô trên bản sao `_tmp\pyrevit_nganchay\G19_ngan_chay_thu_v4.rvt`. Chưa áp lên G19 thật (chỉ làm khi người dùng bảo).

**2026-11-04:** model thật G19_A_L3-32 sót hộp ống 150×150 lõi–lõi (0,0225 m2 < ngưỡng khe 0,03) → `DT_NHO_NHAT_M2` = 0,01; thử bản sao `_tmp\revit_nganchay_L3\` 49 → 59 ô. Người dùng chưa bấm lại.

**Why:** G19 không có ống / dấu X → nhận ô theo hình học; góp ý bản 1: ô 1770×2520 hành lang SAI, thiếu khe hộp gen ~120 mm, "nhận diện lỗ mở mà không cần ống".

**How to apply:**
- Sửa quy tắc nhận trục trong khối PHẦN CHUNG của NganChay_TrucHKT.py → sinh lại nút (`build_from_dynamo.py ... --chi NganChay`) VÀ gộp lại Lỗ mở shaft (`gop_lomo_shaft.py`, `--chi LoMoShaft`) vì dùng chung `tim_truc`.
- Chỉ vẽ lại bản đang bàn ([[chi-lam-1-ban-ve]]); cách thử nút xem [[pyrevit-arvtools-revit2027]].
