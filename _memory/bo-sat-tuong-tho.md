---
name: bo-sat-tuong-tho
description: "Hatch / nét bo chống thấm và ngăn cháy lan (Revit, cả CAD) luôn bo sát mép tường thô (mặt lõi tường), không bao giờ bo vào lớp trát / hoàn thiện"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a672e335-b6af-4609-8e94-6faf49c726a9
  modified: 2026-10-28T02:22:19.526Z
---

Bo hatch ngăn cháy lan và chống thấm (vùng hatch, nét vén) sát **mép tường thô = mặt lõi tường** (core face), KHÔNG bo vào mặt hoàn thiện / lớp trát (người dùng chốt 2026-10-28, kèm ảnh khe hộp gen G19).

**Why:** thực tế trong hộp kỹ thuật không có lớp trát; model mẫu vẽ tường có trát 15 mm hai mặt là sai, nên bo theo mặt hoàn thiện thì hụt mất lớp trát.

**How to apply:** Revit: room dùng `SpatialElementBoundaryLocation.CoreBoundary` (không dùng `Finish`); quét dấu chân tường thì lấy dải lõi theo `CompoundStructure` (bỏ lớp hoàn thiện, bỏ tường ốp / trát mỏng không có lõi). Áp cho cả mặt bằng chống thấm và chống cháy lan. Skill CAD chống thấm vốn đã bo "mặt lõi tường". Liên quan [[ngan-chay-lan-revit-dang-do]].
