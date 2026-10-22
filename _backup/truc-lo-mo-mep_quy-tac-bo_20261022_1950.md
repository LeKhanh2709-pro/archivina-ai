# Quy tắc bo A-MEP

## Block A-MEP (đọc từ `FILE MẪU LỖ MỞ.dwg`, 22/10/2026)
- Dynamic block, điểm chèn (0,0) = góc dưới trái khung.
- Thành phần: polyline kín (layer 0 → theo layer INSERT), 2 nét chéo X kiểu `ACAD_ISO03W100` (layer 0), 2 dim style `_1-10_HKT` và 1 TEXT Arial cao 30 chứa Field `Object.Area` của khung (đơn vị m², 2 số lẻ), cả ba trên layer `A_K in` (màu 36, không in).
- Tham số:

| Tên | Hướng (hệ block) | Min | Max | Bước |
|---|---|---|---|---|
| `Distance1` | Y (cao) | 100 | 4000 | 10 |
| `Distance2` | X (rộng) | 100 | 3000 | 10 |

- Định nghĩa gốc 1200 × 2000. Bản đặt sẵn trong mẫu: 700 × 1800, góc 90°, layer `A_MEP` (màu 32, Continuous, nét 0.05).
- Layer `A_MEP` khi chuẩn hoá thành `A-MEP`, nằm trong nhóm layer dò X của NCL. Vì thế chạy lại lệnh thì X của chính A-MEP được nhận là một ô, rồi khớp với A-MEP có sẵn → "đã có" (không chèn trùng).

## Quy tắc đặt
1. Ô = khung bao `(x0 y0 x1 y1)` của vùng `nc:do` trả về (trục nhà song song X, Y).
2. Cạnh dài → `Distance1`, cạnh ngắn → `Distance2` (giới hạn block cho cạnh Y dài hơn).
3. Ô dọc (cao ≥ rộng): góc 0, điểm chèn góc dưới trái. Ô ngang: góc 90° (như bản đặt mẫu), điểm chèn góc **dưới phải** (trục Y block hướng −X thế giới).
4. Kích thước làm tròn bội 10 mm (bước tham số). Phần lệch chia đều hai đầu (ô 315 × 835 → block 320 × 840, lệch 2.5 mm mỗi bên). Excel ghi cột "Lệch do làm tròn".
5. Đã có A-MEP: khung bao A-MEP có sẵn chồng > 50% diện tích nhỏ hơn → "đã có".
6. Không chèn, đánh dấu `Cần xác nhận lại`:
   - Vùng không phải chữ nhật: diện tích vùng / diện tích khung bao < 0.95 (hộp chữ L gộp từ 2 ô X chạm nhau).
   - Vượt giới hạn: cạnh ngắn > 3000 hoặc cạnh dài > 4000 (hoặc < 100).
7. Sau khi chèn: `UPDATEFIELD` các block mới để Field diện tích đúng ngay.

## Vì sao chạy bằng `acad.exe /b`, không dùng Core Console
- Core Console 2027: không có `vla-*` và cũng không có `getpropertyvalue` / `dumpallproperties` (thử 22/10/2026: "no function definition"). Vì vậy không gán được `Distance1` / `Distance2`.
- `acad.exe /nologo <bản sao.dwg> /b <script.scr>` chạy một phiên AutoCAD riêng, có COM. Đã thử: gán 1530 × 640 → khung đúng, Field ra `0.98`.
- Script `.scr` chép thẳng nội dung LISP (SECURELOAD). Lệnh chính bọc trong `vl-catch-all-apply`: lỗi thì ghi `LOI ...` vào log, script vẫn SAVEAS và QUIT, không treo. LISP thiếu hoặc thừa ngoặc thì AutoCAD chờ nhập tiếp và treo tới hết `-TimeoutSec`. Khi đó phát lại `run.scr` bằng Core Console để xem dòng lỗi (phần nạp hàm chạy được ở cả hai).

## Kết quả chạy thử (bản vẽ thử tự tạo, `D:\AI\_tmp\lomo\thu\`)
6 ô X dựng tay trên bản sao file mẫu:
- 600 × 1500 dọc: chèn góc 0, khít.
- 2200 × 450 ngang: chèn góc 90, khít.
- 315 × 835: chèn 320 × 840, lệch 2.5 mm mỗi bên.
- 3500 × 3800: vượt giới hạn, không chèn.
- Chữ L (1000 × 1000 + 1000 × 600): xem lại, không chèn.
- A-MEP có sẵn trong mẫu: đã có.

Chạy lại trên bản kết quả: 0 chèn, 4 đã có. Chưa chạy trên mặt bằng thật (`Cần xác nhận lại`).
