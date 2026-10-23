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
- **Layer lỗ mở khi chèn LUÔN là `A-MEP`** (người dùng chốt 22/10/2026), không theo `A_MEP` của bản đặt mẫu; chỉ lấy màu / nét của `A_MEP` mẫu khi phải tạo mới layer `A-MEP`.
- Layer `A-MEP` (và `A_MEP`) khi chuẩn hoá đều thành `A-MEP`, không nằm trong nhóm layer bị bỏ khi dò X của NCL. Vì thế chạy lại lệnh thì X của chính A-MEP được nhận là một ô, rồi khớp với A-MEP có sẵn → "đã có" (không chèn trùng).

## Quy tắc đặt
1. **Khung bo theo hình lỗ mở** (người dùng chốt 22/10/2026, sau khi bản đầu bỏ qua 2 hộp chữ L ở tầng 4 Tháp B). Một vùng của `nc:do` thành một hoặc nhiều khung chữ nhật (trục nhà song song X, Y):
   - Vùng gộp từ ≥ 2 ô X / lỗ mở (phần tử thứ 6 của `nc:do`) mà tổng diện tích các ô ≈ diện tích vùng (lệch < 3%, tức không chồng nhau): mỗi ô một khung.
   - Vùng chữ nhật (diện tích / khung bao ≥ 0.95): 1 khung = khung bao.
   - Còn lại, đa giác chỉ có cạnh song song X, Y (khung MEP chữ L, ô chồng nhau): tách lưới theo toạ độ đỉnh, gộp theo hàng rồi theo cột, lấy cách ra ít khung hơn (L → 2, T → 2, U → 3).
   - Đa giác có cạnh xiên: không chèn, `Cần xác nhận lại`.
2. Cạnh dài → `Distance1`, cạnh ngắn → `Distance2` (giới hạn block cho cạnh Y dài hơn).
3. Ô dọc (cao ≥ rộng): góc 0, điểm chèn góc dưới trái. Ô ngang: góc 90° (như bản đặt mẫu), điểm chèn góc **dưới phải** (trục Y block hướng −X thế giới).
4. Kích thước làm tròn bội 10 mm (bước tham số). Phần lệch chia đều hai đầu (ô 315 × 835 → block 320 × 840, lệch 2.5 mm mỗi bên). Excel ghi cột "Lệch do làm tròn".
5. Đã có A-MEP: khung bao A-MEP có sẵn chồng > 50% diện tích nhỏ hơn → "đã có".
6. Không chèn, đánh dấu `Cần xác nhận lại`:
   - Vùng có cạnh xiên (xem mục 1).
   - Khung vượt giới hạn: cạnh ngắn > 3000 hoặc cạnh dài > 4000 (hoặc < 100).
7. Sau khi chèn: `UPDATEFIELD` các block mới để Field diện tích đúng ngay.
8. Gom mọi A-MEP vừa chèn vào 1 block `LO MO MEP` (số thêm nếu trùng tên) bằng `-BLOCK` gốc 0,0, chèn lại tại 0,0 trên `A-MEP` (người dùng chốt 22/10/2026). A-MEP lồng bên trong giữ định nghĩa `*U..` dynamic. Khi dò "đã có", `amep:co-san` đọc cả A-MEP trong block `LO MO MEP*`, đổi toạ độ theo điểm chèn / tỉ lệ / góc của block gom. Thử trên bản vẽ tự dựng: gom 5, chạy lại thì 6 đã có, 0 chèn.

## Hộp xoay xiên (sửa 23/10/2026, MB Tầng 5 có cánh nhà xoay ~36,87° / 42,6°)
`nc:do` chỉ ghép dấu X có khung song song X, Y, nên ở cánh xoay nó bỏ sót cả ô X lẫn khung MEP. Phần lỗ mở thêm (chỉ trong `lomo_nguon.lsp`, NCL không đổi):
1. **Khung xoay** (vùng `nc:do` có diện tích / khung bao < 0.95): nếu là chữ nhật xoay (4 đỉnh, góc vuông, cos < 0.02) → 1 A-MEP theo góc khung (`amep:chu-nhat-xoay`). Nếu là chữ L / T xoay (mọi cạnh song song / vuông góc với cạnh đầu) → xoay về phương thẳng, tách lưới như hộp thẳng, xoay các khung trả lại (`amep:tach-xoay`).
2. **Ô X xoay** (`amep:do-x-xoay`): đọc lại bản vẽ bằng `nc:doc-ent`, tìm 2 nét chéo dài bằng nhau (≤ 15 mm), chung trung điểm (≤ 15 mm), không song song. Chữ nhật suy ra phải có cạnh lệch trục > 2° và dài 150–4000 mm. Bộ lọc như `nc:do` (thang máy, nội thất, layer bỏ, nét trong ký hiệu ống, A-Material vừa vẽ), bỏ thêm layer `*DIM*`. X của block `lo mo` chỉ nhận khi có ống. Ô nằm trong vùng `nc:do` đã có thì bỏ, ô trùng tâm (≤ 20 mm) chỉ lấy 1.
3. **Góc chèn**: hướng cạnh dài đưa về [90°, 270°), góc = hướng − 90° (với ô thẳng cho đúng 0° / 90° như cũ). Trục X block theo cạnh ngắn, điểm chèn là đỉnh nhỏ nhất theo 2 trục block, phần lệch làm tròn chia đều 2 đầu.
4. **Không bo được**: khung hình thang / tứ giác không đều (một cạnh xiên, các cạnh khác thẳng, ở chỗ giao cánh xiên với phần thẳng) → `xem_lai`.
- Thử trên bản vẽ tự dựng: ô X xoay 500×250 và 300×1200 (36,87°), 850×300 (45°), khung MEP xoay 640×480 có ống → cả 4 bo khít, đỉnh lệch 0,0 mm. Chữ L xoay 36,87° tách thành 500×900 + 1000×600.
- MB Tầng 5 (`file mau\02_LoMo\MB Tang 5_lo mo_v3.dwg`): 162 ô thẳng + 48 ô X xoay + 13 khung MEP xoay = 223 A-MEP. 5 khung hình thang để xem lại. CSV mã kiểu `X_XOAY`, `KHUNG_ONG_XOAY`; cột `rong` / `dai` của khung xoay là cạnh ngắn / cạnh dài.

## Không có block A-MEP: block tĩnh (sửa 23/10/2026)
Lỗi trước đây: sang máy khác không có `A-MEP_thu_vien.dwg` (không đẩy lên GitHub, đường dẫn cố định `D:/AI/...`) thì lệnh báo thiếu thư viện và không chèn gì. Bây giờ `amep:nap-block` không bao giờ dừng vì thiếu block: không có A-MEP dynamic thì dựng block tĩnh `A-MEP <rộng>x<dài>` (`amep:block-tinh`).
- Số đo lấy từ A-MEP gốc: dim đứng cách mép trái 101.5, dim ngang cách đáy 202.6, text diện tích Arial cao 30 tại (20.8, 30.9), X nét `ACAD_ISO03W100`.
- Dim: AutoCAD dựng hình dim theo kiểu dim **hiện hành lúc tạo**. Đổi `StyleName` hay `ScaleFactor` sau đó không vẽ lại hình dim nằm trong block (thử 23/10/2026: vẫn ra chữ 200 mm của `A 1-100`). Vì vậy phải đặt `_1-10_HKT` làm kiểu hiện hành trong lúc tạo dim, rồi trả lại kiểu cũ.
- Dò "đã có": tên `A-MEP <...>` được nhận như A-MEP (`amep:khung-o`, `amep:co-san`, `kiem_tra_amep.py`).
- Thử 23/10/2026 trên bản vẽ không có block / layer A-MEP (nền là bản sao `iso_copy.dwg`): `-KhongThuVien` → `CHE_DO tinh`, chèn 5 khung, gom `LO MO MEP`, đo khung lệch ≤ 2.5 mm (làm tròn), ảnh xem đúng cỡ. Chạy lại thì 5 đã có, 0 chèn. Có thư viện → `CHE_DO dong`, chèn 5 như cũ.

## Vì sao chạy bằng `acad.exe /b`, không dùng Core Console
- Core Console 2027: không có `vla-*` và cũng không có `getpropertyvalue` / `dumpallproperties` (thử 22/10/2026: "no function definition"). Vì vậy không gán được `Distance1` / `Distance2`.
- `acad.exe /nologo <bản sao.dwg> /b <script.scr>` chạy một phiên AutoCAD riêng, có COM. Đã thử: gán 1530 × 640 → khung đúng, Field ra `0.98`.
- Script `.scr` chép thẳng nội dung LISP (SECURELOAD). Lệnh chính bọc trong `vl-catch-all-apply`: lỗi thì ghi `LOI ...` vào log, script vẫn SAVEAS và QUIT, không treo. LISP thiếu hoặc thừa ngoặc thì AutoCAD chờ nhập tiếp và treo tới hết `-TimeoutSec`. Khi đó phát lại `run.scr` bằng Core Console để xem dòng lỗi (phần nạp hàm chạy được ở cả hai).

## Kết quả chạy thử (bản vẽ thử tự tạo trong `_tmp`, đã xoá 22/10/2026; dựng lại bằng LINE trên layer `A-Hidden` nếu cần thử lại)
6 ô X dựng tay trên bản sao file mẫu:
- 600 × 1500 dọc: chèn góc 0, khít.
- 2200 × 450 ngang: chèn góc 90, khít.
- 315 × 835: chèn 320 × 840, lệch 2.5 mm mỗi bên.
- 3500 × 3800: vượt giới hạn, không chèn.
- Chữ L (1000 × 1000 + 1000 × 600): bản đầu xem lại, không chèn. Từ bản tách khung: 2 A-MEP (1000 × 1000 góc 0, 1000 × 600 góc 90), khít 2 ô.
- A-MEP có sẵn trong mẫu: đã có.

Chạy lại trên bản kết quả: 0 chèn, 4 đã có. Chưa chạy trên mặt bằng thật (`Cần xác nhận lại`).
