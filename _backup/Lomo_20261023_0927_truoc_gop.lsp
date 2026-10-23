;;; Lomo.lsp - MỘT FILE DUY NHẤT, chỉ cần APPLOAD file này rồi gõ LOMO.
;;; Lệnh LOMO: tự tìm trục kỹ thuật / hộp kỹ thuật trên mặt bằng tầng và chèn block lỗ mở
;;; A-MEP (dynamic block) co giãn khít khung từng trục / hộp (bản LISP của skill truc-lo-mo-mep).
;;;
;;; FILE NÀY ĐƯỢC GỘP TỰ ĐỘNG, KHÔNG SỬA TAY: phần dò trục lấy từ fire_stop_shaft.lsp (skill
;;; ngan-chay-truc-hkt, bỏ lệnh NCL), phần lỗ mở lấy từ lomo_nguon.lsp (skill truc-lo-mo-mep).
;;; Sửa ở 2 file nguồn rồi chạy scripts\gop_lomo.ps1 của skill truc-lo-mo-mep để gộp lại.
;;;
;;; Nhận diện trục / hộp: hàm nc:do (cùng quy tắc với lệnh NCL của skill ngan-chay-truc-hkt): ô có
;;; dấu X của trục / hộp, lỗ mở "lo mo" có ống đứng, khung lỗ mở MEP có ống; bỏ thang máy, nội thất,
;;; lỗ mở sàn không có ống.
;;;
;;; Block A-MEP (mẫu: FILE MẪU LỖ MỞ.dwg, 22/10/2026): khung chữ nhật + X nét đứt + 2 dim + Field
;;; diện tích m2. Điểm chèn = góc dưới trái. Tham số:
;;;   Distance1 = cạnh theo trục Y của block (100 - 4000, bước 10)
;;;   Distance2 = cạnh theo trục X của block (100 - 3000, bước 10)
;;; Quy tắc bo: bo theo hình lỗ mở. Block chỉ co giãn được thành chữ nhật, nên vùng không chữ nhật
;;; (hộp chữ L, chữ T...) được tách thành nhiều khung chữ nhật, mỗi khung 1 A-MEP:
;;;   - vùng gộp từ nhiều ô X / lỗ mở: mỗi ô một A-MEP (đúng từng lỗ mở trên bản vẽ);
;;;   - khung MEP chữ L, ô chồng nhau: tách lưới đa giác, lấy cách ra ít khung nhất.
;;; Mỗi khung: cạnh dài -> Distance1, cạnh ngắn -> Distance2. Khung dọc (cao >= rộng) chèn góc 0,
;;; khung ngang chèn góc 90 (như block mẫu). Kích thước làm tròn bội 10 mm, sai lệch chia đều 2 đầu.
;;; LAYER LỖ MỞ LUÔN LÀ "A-MEP" (người dùng chốt 22/10/2026, tuân thủ tuyệt đối): mọi block A-MEP và block
;;; gom "LO MO MEP" đều đặt trên layer A-MEP. Bản vẽ chưa có layer này thì tạo mới theo thông số layer
;;; A_MEP của file mẫu (màu 32, Continuous, nét 0.05). Layer A-MEP đang khoá thì mở khoá tạm, xong khoá lại.
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước (lệnh thêm block vào bản vẽ đang mở).
;;;   2. APPLOAD -> chọn Lomo.lsp (D:\AI\scripts\lisp\Lomo.lsp). Chỉ một file, không cần file nào khác.
;;;   3. Gõ LOMO: quét toàn bộ Model, chèn A-MEP cho mọi trục / hộp chưa có, rồi in các ô cần xem lại.
;;;   4. KHÔNG BẮT BUỘC có block A-MEP (sửa 23/10/2026 để chạy được ở máy khác):
;;;      - Bản vẽ đã có A-MEP dynamic: dùng block có sẵn, không định nghĩa lại.
;;;      - Chưa có: chép định nghĩa từ file thư viện A-MEP_thu_vien.dwg nếu tìm thấy (amep:cfg 'thu-vien,
;;;        hoặc trong Support File Search Path).
;;;      - Không có file thư viện / A-MEP không phải dynamic: tự dựng block tĩnh "A-MEP <rộng>x<dài>" cho
;;;        từng kích thước, hình thể như A-MEP (khung, X nét đứt, 2 dim, số diện tích m2), không kéo giãn được.
;;;   5. Các A-MEP vừa chèn được gom vào 1 block "LO MO MEP" (trùng tên thì "LO MO MEP 2"...) chèn tại
;;;      0,0 trên layer A-MEP, giữ nguyên vị trí (người dùng chốt 22/10/2026: dễ kiểm soát). A-MEP bên trong
;;;      vẫn là dynamic block: sửa bằng REFEDIT / BEDIT block gom.
;;;   6. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ.
;;;   Chạy lại lệnh: ô đã có A-MEP (chồng > 50%, kể cả A-MEP nằm trong block "LO MO MEP*") không chèn trùng.
;;;   Không chèn, chỉ liệt kê (Cần xác nhận lại): vùng có cạnh xiên (không tách được thành chữ nhật),
;;;   khung vượt giới hạn tham số block (cạnh ngắn > 3000 hoặc cạnh dài > 4000).
;;;
;;; Yêu cầu: AutoCAD đầy đủ 2025 / 2026 (chạy được cả 2021+), LISPSYS = 1, file lưu UTF-8.
;;;   KHÔNG chạy được trong AutoCAD Core Console (không có COM để gán tham số dynamic block).
;;; Giới hạn: như NCL, chỉ đúng với mặt bằng có trục nhà song song X, Y.

;;; ==================== PHAN DO TRUC / HOP (gop tu fire_stop_shaft.lsp) ====================
(vl-load-com)

;;; ---------- Cấu hình (sửa ở đây nếu dự án đặt tên khác) ----------
;;; Mẫu layer so trên tên đã chuẩn hoá: bỏ tiền tố xref đã bind "...$0$" và xref đang attach "XREF|",
;;; bỏ dấu cách, "_" thành "-", chữ hoa.
(defun nc:cfg (k)
  (cdr
    (assoc
      k
      '((layer-bo "A-INTERIOR*" "*N?ITH?T*" "*NOITHAT*" "*FURN*" "A-DOOR*" "A-C?A*" "A-CUA*"
                  "A-WINDOW*" "A-GLAZ*" "A-DIM*" "A-TEXT*" "A-SYMBOL*" "A-KIHIEU*" "A-K?HI?U*"
                  "A-AXIS" "DEFPOINTS")
        (block-tm "*CABIN*" "*THANG MAY*" "*THANGMAY*" "*ELEVATOR*" "*LIFT*")
        (block-bo "*MAY GIAT*" "*MAYGIAT*" "*MAY RUA*" "*TU LANH*" "*TULANH*" "*MB-BEP*" "*SINK*"
                  "*LAVABO*" "*BON TAM*" "*BONTAM*" "*GIUONG*" "*SOFA*" "*TIVI*" "*LOUVER*"
                  "*TANG HAM*" "*TANGHAM*" "*BASEMENT*")
        (block-ong "*PIPE*")
        (block-lo-mo "*LO MO*" "*LOMO*")
        (layer-khung "*LOMO*")
        (layer-ve . "A-Material")
        ;; layer nội thất / thiết bị vệ sinh: tắt sau khi hatch (so trên tên đã chuẩn hoá)
        (layer-an "A-INTERIOR*" "*N?ITH?T*" "*NOITHAT*" "*FURN*" "A-WC*" "*GATHU*" "*THIETBIVESINH*" "*TBVS*")
        ;; màu làm mờ mọi layer còn lại
        (mau-mo . "150,150,150")
        ;; tên xref khung tên: layer của xref này giữ nguyên màu, không tắt
        (khung-ten "*KHUNG*" "*TITLE*" "*TEN BAN VE*" "*TENBANVE*")
        (layer-state . "TRUOC NGAN CHAY LAN")
        ;; tên block gom đường bo + hatch vừa vẽ (trùng thì thêm số: "NGAN CHAY LAN 2"...)
        (ten-block . "NGAN CHAY LAN")
       )
    )
  )
)

;;; ---------- Tiện ích chuỗi ----------
(defun nc:khop (s pats)
  (and s (vl-some '(lambda (p) (wcmatch s p)) pats))
)

;;; Chuẩn hoá tên layer: "CH19$0$A_MEP" -> "A-MEP", "A- Truc ME" -> "A-TRUCME",
;;; "XREF1|XREF2|A-Truc nuoc" -> "A-TRUCNUOC" (xref đang attach, kể cả lồng nhau)
(defun nc:chuan (lay / l n i j bd c)
  (setq l (vl-string->list lay) n (length l) i 0 bd 0)
  (while (< i n)
    (if (= (nth i l) 124) (setq bd (1+ i)))
    (if (= (nth i l) 36)
      (progn
        (setq j (1+ i))
        (while (and (< j n) (<= 48 (nth j l) 57)) (setq j (1+ j)))
        (if (and (> j (1+ i)) (< j n) (= (nth j l) 36)) (setq bd (1+ j)))
      )
    )
    (setq i (1+ i))
  )
  (repeat bd (setq l (cdr l)))
  (setq l (vl-remove 32 l))
  (setq l (mapcar '(lambda (c) (if (= c 95) 45 c)) l))
  (strcase (vl-list->string l))
)

;;; Cờ của một tên block (có nhớ đệm): 1 thang máy, 2 bỏ qua, 4 ống đứng, 8 lỗ mở
(defun nc:co-ten (nm / s r)
  (cond
    ((cdr (assoc nm nc-co-cache)))
    (t
     (setq s (strcase nm) r 0)
     (if (nc:khop s (nc:cfg 'block-tm)) (setq r (logior r 1)))
     (if (nc:khop s (nc:cfg 'block-bo)) (setq r (logior r 2)))
     (if (nc:khop s (nc:cfg 'block-ong)) (setq r (logior r 4)))
     (if (nc:khop s (nc:cfg 'block-lo-mo)) (setq r (logior r 8)))
     (setq nc-co-cache (cons (cons nm r) nc-co-cache))
     r
    )
  )
)

;;; Thông tin layer (có nhớ đệm): (tên chuẩn bỏ? khung?)
(defun nc:tt-layer (lay / c r)
  (cond
    ((cdr (assoc lay nc-lay-cache)))
    (t
     (setq c (nc:chuan lay))
     (setq r (list c
                   (or (nc:khop c (nc:cfg 'layer-bo)) (nc:khop (strcase lay) (nc:cfg 'block-bo)))
                   (nc:khop c (nc:cfg 'layer-khung))))
     (setq nc-lay-cache (cons (cons lay r) nc-lay-cache))
     r
    )
  )
)

;;; ---------- Ma trận affine 2D (a b c d e f): x' = ax + by + c, y' = dx + ey + f ----------
(defun nc:ap (m p)
  (list (+ (* (nth 0 m) (car p)) (* (nth 1 m) (cadr p)) (nth 2 m))
        (+ (* (nth 3 m) (car p)) (* (nth 4 m) (cadr p)) (nth 5 m)))
)

;;; Toạ độ OCS (pháp tuyến +Z hoặc -Z) sang hệ chứa: -Z thì đảo dấu x
(defun nc:ocs (p nz)
  (if (minusp nz) (list (- (car p)) (cadr p)) (list (car p) (cadr p)))
)

(defun nc:nz (d / v)
  (if (setq v (cdr (assoc 210 d))) (caddr v) 1.0)
)

;;; ---------- Đọc thực thể thành phần tử hình học ----------
;;; Phần tử: ("S" p1 p2 lay fl fin) đoạn thẳng, ("C" tam r lay fl fin) vòng tròn,
;;;          ("P" ds-dinh lay fl fin) polyline kín. fl = OR cờ mọi block chứa nó,
;;;          fin = cờ block trực tiếp chứa nó (nil nếu nằm thẳng trong model).
;;; Chỉ giữ nét chéo dài >= 100 (dấu X chỉ gồm nét chéo). Bỏ nét ngang / dọc ngay khi đọc giúp
;;; giảm khối lượng xử lý nhiều lần: tường, nội thất toàn nét ngang / dọc.
(defun nc:seg (p1 p2 lay / dx dy)
  (setq dx (abs (- (car p2) (car p1))) dy (abs (- (cadr p2) (cadr p1))))
  (if (and (> dx 20.0) (> dy 20.0) (>= (+ (* dx dx) (* dy dy)) 10000.0))
    (list (list "S" p1 p2 lay 0 nil))
  )
)

(defun nc:doc-ent (d / ty lay nz pts kq i n)
  (setq ty (cdr (assoc 0 d)) lay (cdr (assoc 8 d)) nz (nc:nz d))
  (cond
    ((= ty "LINE")
     (nc:seg (nc:ocs (cdr (assoc 10 d)) 1.0) (nc:ocs (cdr (assoc 11 d)) 1.0) lay)
    )
    ((= ty "LWPOLYLINE")
     (setq pts (mapcar '(lambda (x) (nc:ocs (cdr x) nz)) (vl-remove-if-not '(lambda (x) (= (car x) 10)) d)))
     (setq n (length pts) i 0 kq nil)
     (while (< i (1- n))
       (setq kq (append (nc:seg (nth i pts) (nth (1+ i) pts) lay) kq) i (1+ i))
     )
     (if (= 1 (logand 1 (cdr (assoc 70 d))))
       (progn
         (if (> n 2) (setq kq (append (nc:seg (last pts) (car pts) lay) kq)))
         (if (and (>= n 4) (or (= lay "0") (caddr (nc:tt-layer lay))))
           (setq kq (cons (list "P" pts lay 0 nil) kq))
         )
       )
     )
     kq
    )
    ((= ty "CIRCLE")
     (if (<= 8.0 (cdr (assoc 40 d)) 500.0)
       (list (list "C" (nc:ocs (cdr (assoc 10 d)) nz) (cdr (assoc 40 d)) lay 0 nil))
     )
    )
    ((= ty "INSERT") (nc:doc-insert d nz))
    ;; hatch NET có sẵn (ở mọi cấp: model, block, xref): ghi khung từng loop để không vẽ trùng
    ((and (= ty "HATCH") (= (strcase (cdr (assoc 2 d))) "NET"))
     (mapcar '(lambda (k) (list "H" (list (list (nth 0 k) (nth 1 k)) (list (nth 2 k) (nth 1 k))
                                         (list (nth 2 k) (nth 3 k)) (list (nth 0 k) (nth 3 k)))
                               lay 0 nil))
             (nc:vong-hatch d '(1.0 0.0 0.0 0.0 1.0 0.0))))
  )
)

;;; Ma trận đưa toạ độ trong block về hệ chứa INSERT d
(defun nc:ma-tran (d nz / bp p sx sy r a b c dd e f)
  (setq bp (cdr (assoc 10 (tblsearch "BLOCK" (cdr (assoc 2 d)))))
        p  (cdr (assoc 10 d))
        sx (cond ((cdr (assoc 41 d))) (1.0))
        sy (cond ((cdr (assoc 42 d))) (1.0))
        r  (cond ((cdr (assoc 50 d))) (0.0)))
  (setq a (* sx (cos r)) b (- (* sy (sin r))) dd (* sx (sin r)) e (* sy (cos r)))
  (setq c (+ (car p) (- (+ (* a (car bp)) (* b (cadr bp)))))
        f (+ (cadr p) (- (+ (* dd (car bp)) (* e (cadr bp))))))
  (if (minusp nz) (list (- a) (- b) (- c) dd e f) (list a b c dd e f))
)

(defun nc:doc-insert (d nz / nm con m fl)
  (setq nm (cdr (assoc 2 d)) fl (nc:co-ten nm))
  ;; block cabin thang máy / đồ nội thất / tầng hầm: bỏ cả block, không đọc bên trong
  (if (and (= 0 (logand fl 3)) (tblsearch "BLOCK" nm))
    (progn
      (setq con (nc:phang nm) m (nc:ma-tran d nz))
      (mapcar '(lambda (x) (nc:bien x m (cdr (assoc 8 d)) fl)) con)
    )
  )
)

;;; Biến đổi một phần tử con sang hệ của block cha
(defun nc:bien (x m lay-ins fl / lay fin k)
  (setq k (car x)
        lay (nth (if (member k '("P" "H")) 2 3) x)
        lay (if (= (strcase lay) "0") lay-ins lay))
  (cond
    ((= k "S")
     (setq fin (cond ((nth 5 x)) (fl)))
     (list "S" (nc:ap m (nth 1 x)) (nc:ap m (nth 2 x)) lay (logior (nth 4 x) fl) fin)
    )
    ((= k "C")
     (setq fin (cond ((nth 5 x)) (fl)))
     (list "C" (nc:ap m (nth 1 x))
           (* (nth 2 x) (sqrt (abs (- (* (nth 0 m) (nth 4 m)) (* (nth 1 m) (nth 3 m))))))
           lay (logior (nth 4 x) fl) fin)
    )
    ((member k '("P" "H"))
     (setq fin (cond ((nth 4 x)) (fl)))
     (list k (mapcar '(lambda (p) (nc:ap m p)) (nth 1 x)) lay (logior (nth 3 x) fl) fin)
    )
  )
)

;;; Phần tử của một định nghĩa block, trong hệ toạ độ của block (có nhớ đệm)
(defun nc:phang (bn / e d kq)
  (cond
    ((assoc bn nc-memo) (cdr (assoc bn nc-memo)))
    (t
     (setq kq nil e (tblobjname "BLOCK" bn))
     (if e (setq e (entnext e)))
     (while (and e (setq d (entget e)) (/= (cdr (assoc 0 d)) "ENDBLK"))
       (setq kq (append (nc:doc-ent d) kq) e (entnext e))
     )
     (setq nc-memo (cons (cons bn kq) nc-memo))
     kq
    )
  )
)

;;; ---------- Hình học ----------
(defun nc:khung (pts)
  (list (apply 'min (mapcar 'car pts)) (apply 'min (mapcar 'cadr pts))
        (apply 'max (mapcar 'car pts)) (apply 'max (mapcar 'cadr pts)))
)

(defun nc:dt-kh (k) (* (- (nth 2 k) (nth 0 k)) (- (nth 3 k) (nth 1 k))))

;;; Diện tích giao của 2 khung chữ nhật
(defun nc:giao (k1 k2 / w h)
  (setq w (- (min (nth 2 k1) (nth 2 k2)) (max (nth 0 k1) (nth 0 k2)))
        h (- (min (nth 3 k1) (nth 3 k2)) (max (nth 1 k1) (nth 1 k2))))
  (if (and (> w 0) (> h 0)) (* w h) 0.0)
)

(defun nc:no (k d) (list (- (nth 0 k) d) (- (nth 1 k) d) (+ (nth 2 k) d) (+ (nth 3 k) d)))

(defun nc:trong-kh (p k)
  (and (<= (nth 0 k) (car p) (nth 2 k)) (<= (nth 1 k) (cadr p) (nth 3 k)))
)

;;; Điểm trong đa giác (tia ngang)
(defun nc:trong-dg (p pts / x y i j n in xi yi xj yj)
  (setq x (car p) y (cadr p) n (length pts) i 0 j (1- n) in nil)
  (while (< i n)
    (setq xi (car (nth i pts)) yi (cadr (nth i pts)) xj (car (nth j pts)) yj (cadr (nth j pts)))
    (if (and (/= (> yi y) (> yj y))
             (< x (+ xi (/ (* (- xj xi) (- y yi)) (- yj yi)))))
      (setq in (not in))
    )
    (setq j i i (1+ i))
  )
  in
)

(defun nc:so-ong (k ong / kk)
  (setq kk (nc:no k 20.0))
  (length (vl-remove-if-not '(lambda (p) (nc:trong-kh p kk)) ong))
)

(defun nc:tron (v) (* 0.1 (fix (if (minusp v) (- (* v 10.0) 0.5) (+ (* v 10.0) 0.5)))))

(defun nc:duy-nhat (l / kq)
  (foreach v (vl-sort l '<)
    (if (or (null kq) (> (- v (car kq)) 0.5)) (setq kq (cons v kq)))
  )
  (reverse kq)
)

;;; Ô lưới (i, j) có nằm trong nhóm hình chữ nhật không (xét tâm ô, nở 6 mm để lấp khe chạm)
(defun nc:o-phu (i j xs ys ks / cx cy)
  (and (>= i 0) (>= j 0) (< i (1- (length xs))) (< j (1- (length ys)))
       (setq cx (/ (+ (nth i xs) (nth (1+ i) xs)) 2.0) cy (/ (+ (nth j ys) (nth (1+ j) ys)) 2.0))
       (vl-some '(lambda (k) (nc:trong-kh (list cx cy) (nc:no k 6.0))) ks))
)

;;; Đường bao ngoài của nhóm hình chữ nhật trục X, Y chạm nhau (hộp chữ L, chữ T...)
(defun nc:bao-chu-nhat (ks / xs ys nx ny i j c x0 x1 y0 y1 canh vong tot dt p q s0)
  (if (= (length ks) 1)
    (progn
      (setq c (car ks))
      (list (list (nth 0 c) (nth 1 c)) (list (nth 2 c) (nth 1 c))
            (list (nth 2 c) (nth 3 c)) (list (nth 0 c) (nth 3 c)))
    )
    (progn
      (setq xs (nc:duy-nhat (apply 'append (mapcar '(lambda (k) (list (nth 0 k) (nth 2 k))) ks)))
            ys (nc:duy-nhat (apply 'append (mapcar '(lambda (k) (list (nth 1 k) (nth 3 k))) ks)))
            nx (1- (length xs)) ny (1- (length ys)))
      (setq canh nil j 0)
      (while (< j ny)
        (setq i 0)
        (while (< i nx)
          (if (nc:o-phu i j xs ys ks)
            (progn
              (setq x0 (nth i xs) x1 (nth (1+ i) xs) y0 (nth j ys) y1 (nth (1+ j) ys))
              (if (not (nc:o-phu i (1- j) xs ys ks)) (setq canh (cons (list (list x0 y0) (list x1 y0)) canh)))
              (if (not (nc:o-phu (1+ i) j xs ys ks)) (setq canh (cons (list (list x1 y0) (list x1 y1)) canh)))
              (if (not (nc:o-phu i (1+ j) xs ys ks)) (setq canh (cons (list (list x1 y1) (list x0 y1)) canh)))
              (if (not (nc:o-phu (1- i) j xs ys ks)) (setq canh (cons (list (list x0 y1) (list x0 y0)) canh)))
            )
          )
          (setq i (1+ i))
        )
        (setq j (1+ j))
      )
      (setq tot nil dt 0.0)
      (while canh
        (setq p (car canh) canh (cdr canh) s0 (car p) vong (list s0))
        (while (and p (not (equal (cadr p) s0 0.01)))
          (setq vong (cons (cadr p) vong)
                q (vl-some '(lambda (c) (if (equal (car c) (cadr p) 0.01) c)) canh))
          (if q (setq canh (vl-remove q canh)))
          (setq p q)
        )
        (setq c (abs (nc:dt-dg vong)))
        (if (> c dt) (setq dt c tot (reverse vong)))
      )
      (nc:bo-thang-hang tot)
    )
  )
)

(defun nc:dt-dg (pts / s i n a b)
  (setq s 0.0 n (length pts) i 0)
  (while (< i n)
    (setq a (nth i pts) b (nth (rem (1+ i) n) pts)
          s (+ s (- (* (car a) (cadr b)) (* (car b) (cadr a)))) i (1+ i))
  )
  (/ s 2.0)
)

;;; Bỏ đỉnh nằm giữa 2 cạnh thẳng hàng
(defun nc:bo-thang-hang (pts / n i a b c kq)
  (setq n (length pts) i 0)
  (while (< i n)
    (setq a (nth (rem (+ i n -1) n) pts) b (nth i pts) c (nth (rem (1+ i) n) pts))
    (if (> (abs (- (* (- (car b) (car a)) (- (cadr c) (cadr b)))
                   (* (- (cadr b) (cadr a)) (- (car c) (car b))))) 1.0)
      (setq kq (cons b kq))
    )
    (setq i (1+ i))
  )
  (reverse kq)
)

;;; ---------- Ghép dấu X ----------
;;; dc: (x0 y0 x1 y1 dau lomo) - dau = dấu độ dốc (+1 / -1)
;;; Đầu mút của nét chéo dựng lại từ khung + dấu độ dốc
(defun nc:dau-mut (a)
  (if (> (nth 4 a) 0)
    (list (list (nth 0 a) (nth 1 a)) (list (nth 2 a) (nth 3 a)))
    (list (list (nth 0 a) (nth 3 a)) (list (nth 2 a) (nth 1 a))))
)

;;; Điểm p nằm trên cạnh khung k (sai số 40)
(defun nc:tren-canh (p k)
  (and (<= (- (nth 0 k) 40.0) (car p) (+ (nth 2 k) 40.0))
       (<= (- (nth 1 k) 40.0) (cadr p) (+ (nth 3 k) 40.0))
       (or (< (abs (- (car p) (nth 0 k))) 40.0) (< (abs (- (car p) (nth 2 k))) 40.0)
           (< (abs (- (cadr p) (nth 1 k))) 40.0) (< (abs (- (cadr p) (nth 3 k))) 40.0)))
)

;;; Hai nét chéo ngược hướng thành dấu X: trả về khung (x0 y0 x1 y1) hoặc nil.
;;;  - X chuẩn: 2 nét cùng khung (sai số 40);
;;;  - X lệch (vẽ không chuẩn): nét a nối góc-góc làm khung, nét b có 2 đầu nằm trên cạnh khung đó và
;;;    phủ >= 1/2 chiều rộng, chiều cao (vd. 1 nét từ góc tới giữa cạnh) - khung lấy theo nét a.
(defun nc:khop-x (a b / ka kb)
  (setq ka (list (nth 0 a) (nth 1 a) (nth 2 a) (nth 3 a)) kb (list (nth 0 b) (nth 1 b) (nth 2 b) (nth 3 b)))
  (cond
    ((= (nth 4 a) (nth 4 b)) nil)
    ((vl-every '(lambda (u v) (< (abs (- u v)) 40.0)) ka kb) ka)
    ((nc:x-lech kb ka (nc:dau-mut b)) ka)
    ((nc:x-lech ka kb (nc:dau-mut a)) kb)
  )
)

;;; Nét con (khung kc, đầu mút dm) có nằm gọn trong khung k và phủ đủ không
(defun nc:x-lech (kc k dm)
  (and (>= (- (nth 2 kc) (nth 0 kc)) (* 0.5 (- (nth 2 k) (nth 0 k))))
       (>= (- (nth 3 kc) (nth 1 kc)) (* 0.5 (- (nth 3 k) (nth 1 k))))
       (nc:tren-canh (car dm) k) (nc:tren-canh (cadr dm) k))
)

(defun nc:ghep-x (dc / l i n a b k1 ok kq trung)
  (setq l (vl-sort dc '(lambda (a b) (< (car a) (car b)))) kq nil)
  (while l
    (setq a (car l) l (cdr l) b l)
    (while (and b (< (car (car b)) (+ (nth 2 a) 40.0)))
      (if (setq k1 (nc:khop-x a (car b)))
        (progn
          (setq trung (vl-some '(lambda (q) (if (and (< (abs (- (nth 0 q) (nth 0 k1))) 60.0)
                                                     (< (abs (- (nth 1 q) (nth 1 k1))) 60.0)
                                                     (< (abs (- (nth 2 q) (nth 2 k1))) 60.0)
                                                     (< (abs (- (nth 3 q) (nth 3 k1))) 60.0))
                                              q))
                               kq))
          (cond
            ((not trung)
             (setq kq (cons (append k1 (list (or (nth 5 a) (nth 5 (car b))))) kq)))
            ;; trùng với X của lỗ mở mà ô mới là X của hộp: lấy X của hộp (khung tường thật)
            ((and (nth 4 trung) (not (nth 5 a)) (not (nth 5 (car b))))
             (setq kq (subst (append k1 (list nil)) trung kq)))
          )
        )
      )
      (setq b (cdr b))
    )
  )
  kq
)

;;; ---------- Hatch NET đã có ----------
;;; Khung bao từng loop của hatch d, đưa về hệ chứa bằng ma trận m
(defun nc:vong-hatch (d m / pha vong kq nz)
  (setq nz (nc:nz d) pha nil vong nil kq nil)
  (foreach x d
    (cond
      ((= (car x) 91) (setq pha t))
      ((and pha (= (car x) 92))
       (if vong (setq kq (cons (nc:khung vong) kq)))
       (setq vong nil))
      ((and pha (member (car x) '(10 11))) (setq vong (cons (nc:ap m (nc:ocs (cdr x) nz)) vong)))
      ((and pha (= (car x) 75))
       (if vong (setq kq (cons (nc:khung vong) kq)))
       (setq pha nil vong nil))
    )
  )
  kq
)

;;; Xref đang attach mà chưa nạp được (không tìm thấy file / đã unload): lệnh không đọc được bên trong
(defun nc:bao-xref (/ b fl n)
  (setq b (tblnext "BLOCK" T) n 0)
  (while b
    (setq fl (cdr (assoc 70 b)))
    (if (and (/= 0 (logand fl 4)) (= 0 (logand fl 32)))
      (progn
        (setq n (1+ n))
        (princ (strcat "\n  Cảnh báo: xref \"" (cdr (assoc 2 b))
                       "\" chưa nạp (không tìm thấy file hoặc đang Unload) - trục / hộp trong xref này bị bỏ qua."))
      )
    )
    (setq b (tblnext "BLOCK"))
  )
  n
)

;;; ---------- Dò toàn bộ bản vẽ ----------
;;; Trả về (vung loai ong-le) ; vung: (kieu dinh khung so-ong trang-thai cac-o)
;;; cac-o: danh sách khung (x0 y0 x1 y1) các ô X / lỗ mở gốc gộp thành vùng (nil với khung MEP không X),
;;; lệnh A-MEP (amep_bo_truc.lsp) dùng để bo từng ô
;;; Đọc cả xref đang attach đã nạp (chỉ đọc, không bind).
(defun nc:do (/ ss i d tat x lay tt fl fin dx dy dc ong khung ox truc lomo nhom vung loai co
                kk dt g p n ong-le pk)
  (princ "\nĐang đọc bản vẽ (chỉ đọc, kể cả block lồng nhau và xref đang attach)...")
  (nc:bao-xref)
  (setq ss (ssget "X" '((410 . "Model"))) i 0 tat nil)
  (repeat (sslength ss)
    (setq d (entget (ssname ss i)) i (1+ i))
    (setq tat (append (nc:doc-ent d) tat))
  )
  (princ (strcat "\n  Phần tử hình học: " (itoa (length tat))))
  (setq dc nil ong nil khung nil co nil)
  (foreach x tat
    (setq pk  (member (car x) '("P" "H"))
          lay (nth (if pk 2 3) x)
          fl  (nth (if pk 3 4) x)
          fin (nth (if pk 4 5) x)
          tt  (nc:tt-layer lay))
    (cond
      ;; hatch NET ngăn cháy có sẵn ở mọi cấp (model, block NGAN CHAY LAN, xref): vùng đã có
      ((= (car x) "H")
       (if (member (car tt) '("A-MATERIAL" "A-HATCH-COLOR")) (setq co (cons (nc:khung (nth 1 x)) co)))
      )
      ((/= 0 (logand fl 3)))
      ((cadr tt))
      ((= (car x) "C")
       (if (and fin (/= 0 (logand fin 4)) (<= 25.0 (nth 2 x) 160.0))
         (setq ong (cons (nth 1 x) ong))
       )
      )
      ((and fin (/= 0 (logand fin 4))))
      ((= (car x) "P")
       (if (caddr tt) (setq khung (cons (nth 1 x) khung)))
      )
      ((= (car x) "S")
       (if (not (and (= fl 0) (null fin) (= (car tt) "A-MATERIAL")))
         (progn
           (setq dx (- (car (nth 2 x)) (car (nth 1 x))) dy (- (cadr (nth 2 x)) (cadr (nth 1 x))))
           (if (and (>= (+ (* dx dx) (* dy dy)) 22500.0)
                    (< 3.0 (* (/ 180.0 pi) (atan (abs dy) (abs dx))) 87.0))
             (progn
               (setq kk (nc:khung (list (nth 1 x) (nth 2 x))))
               (if (and (<= 150.0 (- (nth 2 kk) (nth 0 kk)) 4000.0)
                        (<= 150.0 (- (nth 3 kk) (nth 1 kk)) 4000.0))
                 (setq dc (cons (append kk (list (if (minusp (* dx dy)) -1 1) (/= 0 (logand fl 8)))) dc))
               )
             )
           )
         )
       )
      )
    )
  )
  (setq tat nil)
  (setq ox (nc:ghep-x dc) dc nil)
  (setq g nil)
  (foreach p ong (if (not (vl-some '(lambda (q) (< (distance p q) 60.0)) g)) (setq g (cons p g))))
  (setq ong g)
  (princ (strcat "\n  Ô dấu X: " (itoa (length ox)) " | ống đứng: " (itoa (length ong))))
  (setq truc (mapcar '(lambda (o) (list (nth 0 o) (nth 1 o) (nth 2 o) (nth 3 o)))
                     (vl-remove-if '(lambda (o) (nth 4 o)) ox))
        lomo (mapcar '(lambda (o) (list (nth 0 o) (nth 1 o) (nth 2 o) (nth 3 o)))
                     (vl-remove-if-not '(lambda (o) (nth 4 o)) ox)))
  (setq vung nil)
  (foreach nh (nc:nhom truc)
    (setq p (nc:bao-chu-nhat nh))
    (if p (setq vung (cons (list "Dấu X trục / hộp" p (nc:khung p) nh) vung)))
  )
  (setq loai nil)
  (foreach k lomo
    (cond
      ((vl-some '(lambda (v) (> (nc:giao k (nth 2 v)) (* 0.05 (min (nc:dt-kh k) (nc:dt-kh (nth 2 v)))))) vung))
      ((> (nc:so-ong k ong) 0)
       (setq vung (cons (list "Lỗ mở có ống đứng" (nc:bao-chu-nhat (list k)) k (list k)) vung)))
      ((not (vl-some '(lambda (q) (> (nc:giao k q) (* 0.5 (nc:dt-kh k)))) loai))
       (setq loai (cons k loai)))
    )
  )
  (foreach p (vl-sort khung '(lambda (a b) (< (abs (nc:dt-dg a)) (abs (nc:dt-dg b)))))
    (setq kk (nc:khung p) dt (abs (nc:dt-dg p)))
    (if (and (>= dt 1e4)
             (not (vl-some '(lambda (v) (> (nc:giao kk (nth 2 v)) (* 0.2 (min (nc:dt-kh kk) (nc:dt-kh (nth 2 v)))))) vung))
             (vl-some '(lambda (q) (nc:trong-dg q p)) ong))
      (setq vung (cons (list "Khung lỗ mở MEP có ống (không có X)" p kk nil) vung))
    )
  )
  (setq vung
         (mapcar
           '(lambda (v / k)
              (setq k (nth 2 v))
              (list (car v) (cadr v) k (nc:so-ong k ong)
                    (if (vl-some '(lambda (h) (> (nc:giao k h) (* 0.5 (nc:dt-kh k)))) co) "da_co" "se_hatch")
                    (nth 3 v)))
           vung))
  (setq vung (vl-sort vung '(lambda (a b) (or (> (nth 3 (nth 2 a)) (+ (nth 3 (nth 2 b)) 250.0))
                                              (and (< (abs (- (nth 3 (nth 2 a)) (nth 3 (nth 2 b)))) 250.0)
                                                   (< (nth 0 (nth 2 a)) (nth 0 (nth 2 b))))))))
  (setq ong-le (vl-remove-if '(lambda (p) (or (vl-some '(lambda (v) (nc:trong-kh p (nc:no (nth 2 v) 20.0))) vung)
                                              (vl-some '(lambda (h) (nc:trong-kh p (nc:no h 20.0))) co)))
                             ong))
  (list vung loai ong-le)
)

;;; Nhóm các ô X chạm nhau (nở 5 mm)
(defun nc:nhom (ks / nhom h moi)
  (setq nhom nil)
  (foreach k ks
    (setq h (vl-remove-if-not '(lambda (g) (vl-some '(lambda (q) (> (nc:giao (nc:no k 5.0) (nc:no q 5.0)) 0)) g)) nhom))
    (setq moi (cons k (apply 'append h)))
    (setq nhom (cons moi (vl-remove-if '(lambda (g) (member g h)) nhom)))
  )
  nhom
)

;;; ---------- Vẽ ----------
(defun nc:tao-layer (ten)
  (if (not (tblsearch "LAYER" ten))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 ten) '(70 . 0) '(62 . 251) '(6 . "Continuous")))
  )
)

(defun nc:ve-vung (pts lay / e h)
  (entmake (append (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") (cons 8 lay) '(62 . 6)
                         '(100 . "AcDbPolyline") (cons 90 (length pts)) '(70 . 1))
                   (mapcar '(lambda (p) (cons 10 p)) pts)))
  (setq e (entlast))
  (command "_.-HATCH" "_P" "NET" "1000" "315" "_S" e "" "")
  (setq h (entlast))
  ;; trả về đối tượng vừa tạo: (polyline hatch) hoặc (polyline) nếu hatch lỗi
  (if (and (not (eq h e)) (= (cdr (assoc 0 (entget h))) "HATCH")) (list e h) (list e))
)

;;; Gom đường bo + hatch vừa vẽ vào 1 block, chèn lại tại 0,0 (giữ nguyên vị trí) trên layer lay.
;;; Không định nghĩa lại block có sẵn: trùng tên thì thêm số.
(defun nc:gom-block (ds lay / ss ten goc i n)
  (setq ss (ssadd) goc (nc:cfg 'ten-block) ten goc i 1)
  (foreach e ds (if (entget e) (ssadd e ss)))
  (while (tblsearch "BLOCK" ten) (setq i (1+ i) ten (strcat goc " " (itoa i))))
  (if (> (sslength ss) 0)
    (progn
      (setq n (sslength ss))
      (command "_.-BLOCK" ten "0,0,0" ss "")
      (if (tblsearch "BLOCK" ten)
        (progn
          ;; tuỳ bản AutoCAD, -BLOCK xoá đối tượng gốc hoặc tự đổi chúng thành block reference:
          ;; chỉ chèn khi chưa có INSERT của block này, tránh 2 block chồng nhau
          (if (not (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmake (list '(0 . "INSERT") '(100 . "AcDbEntity") (cons 8 lay) '(100 . "AcDbBlockReference")
                           (cons 2 ten) '(10 0.0 0.0 0.0) '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) '(50 . 0.0)))
          )
          (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmod (subst (cons 8 lay) (assoc 8 (entget (ssname ss 0))) (entget (ssname ss 0))))
          )
          (princ (strcat "\nĐã gom " (itoa n) " đối tượng vào block \"" ten "\" (layer " lay ")."))
          ten
        )
      )
    )
  )
)

(defun nc:in-ds (vung loai ong-le / i v k)
  (if vung (princ "\n STT | Trạng thái | Tâm X | Tâm Y | Rộng x Dài | Số ống | Kiểu"))
  (setq i 0)
  (foreach v vung
    (setq i (1+ i) k (nth 2 v))
    (princ (strcat "\n " (itoa i) " | " (if (= (nth 4 v) "da_co") "Đã có" "Sẽ hatch")
                   " | " (rtos (/ (+ (nth 0 k) (nth 2 k)) 2.0) 2 0) " | " (rtos (/ (+ (nth 1 k) (nth 3 k)) 2.0) 2 0)
                   " | " (rtos (- (nth 2 k) (nth 0 k)) 2 0) " x " (rtos (- (nth 3 k) (nth 1 k)) 2 0)
                   " | " (itoa (nth 3 v)) " | " (car v)))
  )
  (foreach k loai
    (princ (strcat "\n Loại (lỗ mở sàn không có ống) tại " (rtos (/ (+ (nth 0 k) (nth 2 k)) 2.0) 2 0)
                   ", " (rtos (/ (+ (nth 1 k) (nth 3 k)) 2.0) 2 0)))
  )
  (foreach p ong-le
    (princ (strcat "\n Ống đứng chưa có khung bo tại " (rtos (car p) 2 0) ", " (rtos (cadr p) 2 0)
                   " (Cần xác nhận lại)"))
  )
)

;;; Mặt bằng ngăn cháy lan: tắt layer nội thất / thiết bị vệ sinh, đổi mọi layer sang màu xám
;;; (đường bo màu 6 và hatch RGB 220,30,30 gán màu riêng nên vẫn nổi). Lưu layer state trước
;;; khi đổi (chỉ lưu lần đầu) để khôi phục bằng Layer States Manager.
;;; Layer thuộc xref khung tên (attach "Xref - Khung A1|..." hoặc đã bind "Xref - Khung A1$0$..."):
;;; không làm mờ, không tắt. Nhận theo tên xref (phần trước "|" hoặc "$n$").
(defun nc:la-khung-ten (ten / i j goc)
  (setq goc nil)
  (if (setq i (vl-string-search "|" ten)) (setq goc (substr ten 1 i)))
  (if (and (null goc) (setq j (vl-string-search "$" ten))) (setq goc (substr ten 1 j)))
  (and goc (nc:khop (strcase goc) (nc:cfg 'khung-ten)))
)

(defun nc:lam-mo (lay / l ten an ls giu c tc)
  (setq ls (nc:cfg 'layer-state))
  (if (and layerstate-save (not (layerstate-has ls)))
    (layerstate-save ls (+ 1 32) nil)
  )
  (setq l (tblnext "LAYER" T) an nil giu nil)
  (while l
    (setq ten (cdr (assoc 2 l)))
    (cond
      ;; khung tên: ghi màu gốc (chỉ số + True Color) để trả lại sau khi đổi xám toàn bộ
      ((nc:la-khung-ten ten)
       (setq giu (cons (list ten (abs (cdr (assoc 62 l))) (cdr (assoc 420 (entget (tblobjname "LAYER" ten))))) giu)))
      ((and (/= (strcase ten) (strcase lay)) (nc:khop (nc:chuan ten) (nc:cfg 'layer-an)))
       (setq an (cons ten an)))
    )
    (setq l (tblnext "LAYER"))
  )
  (command "_.-LAYER" "_C" "_T" (nc:cfg 'mau-mo) "*" "")
  (foreach g giu
    (setq c (cadr g) tc (caddr g))
    (if tc
      (command "_.-LAYER" "_C" "_T"
               (strcat (itoa (/ tc 65536)) "," (itoa (rem (/ tc 256) 256)) "," (itoa (rem tc 256))) (car g) "")
      (command "_.-LAYER" "_C" (itoa c) (car g) "")
    )
  )
  (foreach n an (command "_.-LAYER" "_OFF" n ""))
  (princ (strcat "\nĐã tắt " (itoa (length an)) " layer nội thất / thiết bị vệ sinh, đổi các layer khác sang màu "
                 (nc:cfg 'mau-mo) ", giữ màu " (itoa (length giu)) " layer khung tên"
                 (if layerstate-save (strcat ". Layer state cũ: \"" ls "\".") ".")))
  (length an)
)

(defun nc:hoi (se lay)
  (initget "Ve Danhsach Thoat")
  (cond ((getkword (strcat "\nVẽ bo + hatch cho " (itoa (length se))
                           " vùng trên layer " lay "? [Ve/Danhsach/Thoat] <Ve>: ")))
        ("Ve"))
)

;;; ---------- Chạy ----------
;;; tu-dong = T: không hỏi, vẽ luôn (dùng khi chạy thử bằng Core Console)
(defun nc:chay (tu-dong / *error* nc-memo nc-co-cache nc-lay-cache bien cu kq vung loai ong-le moi dt
                          se n-ve n-h chon lay)
  (defun *error* (msg)
    (if cu (mapcar '(lambda (b v) (if v (setvar b v))) bien cu))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nLỗi: " msg))
    )
    (command-s "_.UNDO" "_E")
    (princ)
  )
  ;; TILEMODE: bản vẽ lưu khi đang ở layout thì entmake / -HATCH / -BLOCK rơi vào Paper Space;
  ;; chuyển sang Model để vẽ, xong trả về layout cũ
  (setq bien '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO" "TILEMODE")
        cu (mapcar 'getvar bien)
        lay (nc:cfg 'layer-ve))
  (setvar "CMDECHO" 0)
  (if (= (getvar "TILEMODE") 0) (setvar "TILEMODE" 1))
  (setq kq (nc:do) vung (car kq) loai (cadr kq) ong-le (caddr kq))
  (setq se (vl-remove-if-not '(lambda (v) (= (nth 4 v) "se_hatch")) vung))
  (princ (strcat "\n  Vùng: " (itoa (length vung)) " | sẽ hatch: " (itoa (length se))
                 " | đã có: " (itoa (- (length vung) (length se)))
                 " | lỗ mở không ống (loại): " (itoa (length loai))
                 " | ống chưa có khung: " (itoa (length ong-le))))
  (setq chon (if tu-dong "Ve" (nc:hoi se lay)))
  (while (= chon "Danhsach")
    (nc:in-ds vung loai ong-le)
    (setq chon (nc:hoi se lay))
  )
  (if (and (= chon "Ve") se)
    (progn
      (command "_.UNDO" "_BE")
      (nc:tao-layer lay)
      (setvar "OSMODE" 0)
      (setvar "HPASSOC" 1)
      (if (getvar "HPLAYER") (setvar "HPLAYER" "."))
      (if (getvar "HPCOLOR") (setvar "HPCOLOR" "."))
      (setvar "CLAYER" lay)
      (setvar "CECOLOR" "RGB:220,30,30")
      (setq n-ve 0 n-h 0 moi nil)
      (foreach v se
        (setq n-ve (1+ n-ve) dt (nc:ve-vung (cadr v) lay) moi (append dt moi))
        (if (cadr dt) (setq n-h (1+ n-h)))
      )
      (nc:gom-block moi lay)
      (nc:lam-mo lay)
      (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
      (command "_.UNDO" "_E")
      (princ (strcat "\nĐã vẽ " (itoa n-ve) " đường bo và " (itoa n-h) " hatch NET trên layer " lay
                     ". Ctrl+Z một lần để hoàn tác."))
    )
    (progn
      (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
      (princ (if se "\nKhông vẽ gì." "\nKhông có trục / hộp mới cần hatch."))
    )
  )
  ;; NCL vẽ không hỏi: in luôn các chỗ cần kiểm tra (lỗ mở bị loại, ống chưa có khung)
  (if tu-dong (nc:in-ds nil loai ong-le))
  (princ)
)

;;; ==================== PHAN LO MO A-MEP, LENH LOMO (gop tu lomo_nguon.lsp) ====================

(vl-load-com)

;;; ---------- Cấu hình (sửa ở đây nếu dự án khác) ----------
(defun amep:cfg (k)
  (cdr
    (assoc
      k
      '((ten-block . "A-MEP")
        ;; layer lỗ mở: LUÔN là A-MEP (người dùng chốt 22/10/2026). Không đổi sang tên khác.
        (layer . "A-MEP")
        ;; thông số khi phải tạo mới layer A-MEP: theo layer A_MEP của file mẫu
        (layer-mau . 32) (layer-net . 5)
        ;; tên block gom các A-MEP vừa chèn (trùng thì thêm số: "LO MO MEP 2"...)
        (ten-gom . "LO MO MEP")
        ;; file thư viện chứa block A-MEP dynamic. Không thấy file (máy khác) thì lệnh tự dựng block tĩnh,
        ;; không bắt buộc phải có file này. Cũng tìm "A-MEP_thu_vien.dwg" trong Support File Search Path.
        (thu-vien . "D:/AI/.claude/skills/truc-lo-mo-mep/assets/A-MEP_thu_vien.dwg")
        ;; block tĩnh dựng sẵn khi không có A-MEP dynamic: tên "A-MEP <cạnh ngắn>x<cạnh dài>", hình thể
        ;; như A-MEP gốc (số đo lấy từ block A-MEP trong FILE MẪU LỖ MỞ.dwg, 22/10/2026)
        ;; kiểu dim: dùng kiểu đầu tiên có trong bản vẽ, không có thì kiểu hiện hành
        (dim-style "_1-10_HKT" "A 1-100")
        ;; dim cạnh dài: đường kích thước cách mép trái; dim cạnh ngắn: cách mép dưới
        (dim-x . 101.5) (dim-y . 202.6)
        ;; chữ dim cao thực tế 20 mm như block gốc (DIMTXT 2.0 x DIMSCALE 10 của kiểu _1-10_HKT):
        ;; kiểu dim khác (vd. A 1-100 cho tỷ lệ 1/100) được chỉnh tỷ lệ riêng từng dim cho đúng cỡ này
        (dim-chu-cao . 20.0)
        ;; số diện tích m2
        (text-style . "Arial") (text-cao . 30.0) (text-x . 20.8) (text-y . 30.9)
        ;; nét đứt dấu X
        (net-x . "ACAD_ISO03W100") (lin-file . "acadiso.lin")
        ;; giới hạn và bước tham số, lấy theo block mẫu
        (buoc . 10.0)
        (d1-min . 100.0) (d1-max . 4000.0)
        (d2-min . 100.0) (d2-max . 3000.0)
        ;; diện tích vùng / diện tích khung bao dưới mức này: không phải chữ nhật -> tách khung
        (ti-le-chu-nhat . 0.95)
        ;; ô chồng lên A-MEP có sẵn quá tỉ lệ này: đã có
        (trung . 0.5)
       )
    )
  )
)

;;; ---------- Định nghĩa block ----------
;;; Chép một đối tượng tên ten trong tập coll (của file thư viện) sang tập dich (bản vẽ hiện hành)
(defun amep:chep (dbx coll ten dich / o sa)
  (setq o (vl-catch-all-apply 'vla-Item (list coll ten)))
  (if (not (vl-catch-all-error-p o))
    (progn
      (setq sa (vlax-make-safearray vlax-vbObject '(0 . 0)))
      (vlax-safearray-fill sa (list o))
      (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-CopyObjects (list dbx (vlax-make-variant sa) dich))))
    )
  )
)

;;; Bảo đảm có layer A-MEP: chưa có thì tạo (màu 32, Continuous, nét 0.05 theo mẫu)
(defun amep:tao-layer (lay)
  (if (not (tblsearch "LAYER" lay))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 lay) '(70 . 0) (cons 62 (amep:cfg 'layer-mau)) '(6 . "Continuous")
                   (cons 370 (amep:cfg 'layer-net))))
  )
  (tblsearch "LAYER" lay)
)

;;; Block ten trong bản vẽ có phải dynamic block không
(defun amep:la-dong (ten / b)
  (and (tblsearch "BLOCK" ten)
       (setq b (vl-catch-all-apply 'vla-Item (list (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))) ten)))
       (not (vl-catch-all-error-p b))
       (= (vla-get-IsDynamicBlock b) :vlax-true))
)

;;; File thư viện block A-MEP: biến amep-thu-vien (nếu đặt; "KHONG" = coi như không có thư viện, dùng để
;;; thử chế độ block tĩnh), đường dẫn cấu hình, hoặc tìm trong Support File Search Path. nil nếu không thấy.
(defun amep:file-thu-vien ()
  (cond
    ((= amep-thu-vien "KHONG") nil)
    ((and amep-thu-vien (findfile amep-thu-vien)))
    ((findfile (amep:cfg 'thu-vien)))
    ((findfile "A-MEP_thu_vien.dwg"))
  )
)

;;; Bảo đảm có layer A-MEP và chọn cách chèn, ghi vào biến toàn cục amep-che-do:
;;;   "dong": có block A-MEP dynamic (sẵn trong bản vẽ, hoặc chép từ file thư viện bằng ObjectDBX, chỉ đọc);
;;;   "tinh": không có (máy khác không có file thư viện, hoặc A-MEP trong bản vẽ không phải dynamic)
;;;           -> tự dựng block tĩnh "A-MEP <rộng>x<dài>" cho từng kích thước (amep:block-tinh).
;;; Luôn trả về chế độ (không bao giờ dừng vì thiếu block).
(defun amep:nap-block (/ acad doc dbx f ten lay)
  (setq ten (amep:cfg 'ten-block) lay (amep:cfg 'layer)
        acad (vlax-get-acad-object) doc (vla-get-ActiveDocument acad))
  (amep:tao-layer lay)
  (if (and (not (tblsearch "BLOCK" ten)) (setq f (amep:file-thu-vien)))
    (progn
      (setq dbx (vl-catch-all-apply 'vla-GetInterfaceObject
                                    (list acad (strcat "ObjectDBX.AxDbDocument." (substr (getvar "ACADVER") 1 2)))))
      (cond
        ((vl-catch-all-error-p dbx) (princ "\nKhông mở được ObjectDBX để chép block A-MEP."))
        ((vl-catch-all-error-p (vl-catch-all-apply 'vla-Open (list dbx f)))
         (princ (strcat "\nKhông mở được file thư viện: " f)))
        (t
         (amep:chep dbx (vla-get-Blocks dbx) ten (vla-get-Blocks doc))
         (if (tblsearch "BLOCK" ten) (princ (strcat "\nĐã chép block " ten " từ " f)))
        )
      )
      (if (and dbx (not (vl-catch-all-error-p dbx))) (vlax-release-object dbx))
    )
  )
  (setq amep-che-do (if (amep:la-dong ten) "dong" "tinh"))
  (if (= amep-che-do "tinh")
    (princ (strcat "\nKhông có block " ten " dynamic (không thấy file thư viện hoặc block trong bản vẽ không phải dynamic):"
                   "\n  tự dựng block tĩnh \"" ten " <rộng>x<dài>\" cho từng kích thước, hình thể như " ten
                   " (khung, X, 2 dim, số diện tích m2), không kéo giãn được."))
  )
  amep-che-do
)

;;; Số có đúng 2 chữ số lẻ (như Field %pr2 của block gốc), không phụ thuộc DIMZIN
(defun amep:so2 (v / n)
  (setq n (fix (+ (* v 100.0) 0.5)))
  (strcat (itoa (/ n 100)) "." (if (< (rem n 100) 10) "0" "") (itoa (rem n 100)))
)

;;; Nạp kiểu nét đứt của dấu X (acadiso.lin có sẵn ở mọi máy AutoCAD); trả về tên hoặc nil
(defun amep:nap-net (/ lt)
  (setq lt (amep:cfg 'net-x))
  (if (not (tblsearch "LTYPE" lt))
    (vl-catch-all-apply 'vla-Load (list (vla-get-Linetypes (vla-get-ActiveDocument (vlax-get-acad-object)))
                                        lt (amep:cfg 'lin-file)))
  )
  (if (tblsearch "LTYPE" lt) lt)
)

;;; Block tĩnh cho một kích thước d1 (cạnh dài, theo Y block) x d2 (cạnh ngắn, theo X block), điểm chèn góc dưới
;;; trái như A-MEP gốc. Mọi đối tượng trong block trên layer 0 nên hiện theo layer A-MEP của INSERT.
;;; Đã có block cùng tên thì dùng lại. Trả về tên block.
(defun amep:block-tinh (d1 d2 / ten b sa pl l lt ds dm tx)
  (setq ten (strcat (amep:cfg 'ten-block) " " (itoa (fix (+ d2 0.5))) "x" (itoa (fix (+ d1 0.5)))))
  (if (not (tblsearch "BLOCK" ten))
    (progn
      (setq b (vla-Add (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))) (vlax-3d-point 0 0 0) ten))
      ;; khung chữ nhật
      (setq sa (vlax-make-safearray vlax-vbDouble '(0 . 7)))
      (vlax-safearray-fill sa (list 0.0 0.0 d2 0.0 d2 d1 0.0 d1))
      (setq pl (vla-AddLightWeightPolyline b (vlax-make-variant sa)))
      (vla-put-Closed pl :vlax-true)
      (vla-put-Layer pl "0")
      ;; dấu X nét đứt
      (setq lt (amep:nap-net))
      (foreach c (list (list (list 0.0 0.0 0.0) (list d2 d1 0.0)) (list (list 0.0 d1 0.0) (list d2 0.0 0.0)))
        (setq l (vla-AddLine b (vlax-3d-point (car c)) (vlax-3d-point (cadr c))))
        (vla-put-Layer l "0")
        (if lt (vla-put-Linetype l lt))
      )
      ;; 2 dim: cạnh dài (đứng) và cạnh ngắn (ngang)
      (setq ds (vl-some '(lambda (s) (if (tblsearch "DIMSTYLE" s) s)) (amep:cfg 'dim-style)))
      (foreach dm (list (vla-AddDimRotated b (vlax-3d-point 0 0 0) (vlax-3d-point 0 d1 0)
                                           (vlax-3d-point (amep:cfg 'dim-x) (/ d1 2.0) 0) (/ pi 2.0))
                        (vla-AddDimRotated b (vlax-3d-point 0 0 0) (vlax-3d-point d2 0 0)
                                           (vlax-3d-point (/ d2 2.0) (amep:cfg 'dim-y) 0) 0.0))
        (vla-put-Layer dm "0")
        (if ds (vl-catch-all-apply 'vla-put-StyleName (list dm ds)))
        ;; cỡ chữ = TextHeight (DIMTXT) x ScaleFactor (DIMSCALE): đặt ScaleFactor để chữ cao đúng dim-chu-cao,
        ;; mũi tên / khoảng hở co giãn theo cùng tỉ lệ của kiểu dim
        (if (> (vla-get-TextHeight dm) 0)
          (vl-catch-all-apply 'vla-put-ScaleFactor (list dm (/ (amep:cfg 'dim-chu-cao) (vla-get-TextHeight dm)))))
        ;; dựng lại hình dim theo tỉ lệ mới (không có bước này dim vẫn giữ hình vẽ lúc tạo)
        (vl-catch-all-apply 'vla-Update (list dm))
      )
      ;; số diện tích m2 (giá trị tĩnh, block không kéo giãn nên không cần Field)
      (setq tx (vla-AddText b (amep:so2 (/ (* d1 d2) 1e6))
                            (vlax-3d-point (amep:cfg 'text-x) (amep:cfg 'text-y) 0) (amep:cfg 'text-cao)))
      (vla-put-Layer tx "0")
      (if (tblsearch "STYLE" (amep:cfg 'text-style)) (vla-put-StyleName tx (amep:cfg 'text-style)))
    )
  )
  ten
)

;;; ---------- A-MEP có sẵn ----------
;;; Khung bao (x0 y0 x1 y1) của một đối tượng A-MEP (bản dynamic đã kéo giãn: tên *U..; bản tĩnh: "A-MEP 600x1500"),
;;; nil nếu không phải
(defun amep:khung-o (o / a b ten)
  (setq ten (strcase (amep:cfg 'ten-block)))
  (if (and (= (vla-get-ObjectName o) "AcDbBlockReference")
           (vlax-property-available-p o 'EffectiveName)
           (wcmatch (strcase (vla-get-EffectiveName o)) (strcat ten "," ten " *"))
           (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-GetBoundingBox (list o 'a 'b)))))
    (progn
      (setq a (vlax-safearray->list a) b (vlax-safearray->list b))
      (list (car a) (cadr a) (car b) (cadr b))
    )
  )
)

;;; Đổi khung k trong hệ toạ độ block sang hệ thế giới theo INSERT d (điểm chèn, tỉ lệ, góc)
(defun amep:doi-khung (k d / p sx sy r g)
  (setq p (cdr (assoc 10 d)) sx (cdr (assoc 41 d)) sy (cdr (assoc 42 d)) r (cdr (assoc 50 d)))
  (setq g (mapcar '(lambda (q / x y)
                     (setq x (* sx (car q)) y (* sy (cadr q)))
                     (list (+ (car p) (- (* x (cos r)) (* y (sin r)))) (+ (cadr p) (* x (sin r)) (* y (cos r)))))
                  (list (list (nth 0 k) (nth 1 k)) (list (nth 2 k) (nth 1 k))
                        (list (nth 2 k) (nth 3 k)) (list (nth 0 k) (nth 3 k)))))
  (nc:khung g)
)

;;; Khung bao mọi A-MEP trong Model: chèn thẳng, hoặc nằm trong block gom "LO MO MEP*" của lần chạy trước
(defun amep:co-san (/ ss i e d o k blks trong kq)
  (setq kq nil blks (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))))
  (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model")
                                (cons 2 (strcat (amep:cfg 'ten-block) "," (amep:cfg 'ten-block) " *,`*U*,"
                                                (amep:cfg 'ten-gom) "*")))))
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))) d (entget e) o (vlax-ename->vla-object e))
      (cond
        ((setq k (amep:khung-o o)) (setq kq (cons k kq)))
        ((wcmatch (strcase (cdr (assoc 2 d))) (strcat (strcase (amep:cfg 'ten-gom)) "*"))
         (setq trong nil)
         (vlax-for c (vla-Item blks (cdr (assoc 2 d)))
           (if (setq k (amep:khung-o c)) (setq trong (cons k trong)))
         )
         (setq kq (append (mapcar '(lambda (k) (amep:doi-khung k d)) trong) kq))
        )
      )
    )
  )
  kq
)

;;; Gom các A-MEP vừa chèn vào 1 block "LO MO MEP" (trùng tên thì "LO MO MEP 2"...), chèn lại tại 0,0
;;; trên layer A-MEP, giữ nguyên vị trí. Không định nghĩa lại block có sẵn. Trả về tên block hoặc nil.
(defun amep:gom-block (ds / ss ten goc i n lay)
  (setq ss (ssadd) goc (amep:cfg 'ten-gom) ten goc i 1 lay (amep:cfg 'layer))
  (foreach e ds (if (entget e) (ssadd e ss)))
  (while (tblsearch "BLOCK" ten) (setq i (1+ i) ten (strcat goc " " (itoa i))))
  (if (> (setq n (sslength ss)) 0)
    (progn
      (command "_.-BLOCK" ten "0,0,0" ss "")
      (if (tblsearch "BLOCK" ten)
        (progn
          ;; tuỳ bản AutoCAD, -BLOCK xoá đối tượng gốc hoặc tự đổi chúng thành block reference:
          ;; chỉ chèn khi chưa có INSERT của block này, tránh 2 block chồng nhau
          (if (not (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmake (list '(0 . "INSERT") '(100 . "AcDbEntity") (cons 8 lay) '(100 . "AcDbBlockReference")
                           (cons 2 ten) '(10 0.0 0.0 0.0) '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) '(50 . 0.0)))
          )
          (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmod (subst (cons 8 lay) (assoc 8 (entget (ssname ss 0))) (entget (ssname ss 0))))
          )
          (princ (strcat "\nĐã gom " (itoa n) " block " (amep:cfg 'ten-block) " vào block \"" ten "\" (layer " lay ")."))
          ten
        )
      )
    )
  )
)

;;; ---------- Tính chèn ----------
(defun amep:tron (v / b) (setq b (amep:cfg 'buoc)) (* b (fix (+ (/ v b) 0.5))))

;;; Tách đa giác trực giao thành các hình chữ nhật: lưới theo toạ độ đỉnh, gộp ô liền nhau theo hàng
;;; rồi gộp các dải trùng nhau ở hàng kế tiếp. dao = T: làm theo cột (đổi vai X, Y).
(defun amep:tach-luoi-1 (pts dao / p xs ys nx ny i j i0 chay mo moi kq x0 y0 x1 y1 tim)
  (if dao (setq pts (mapcar '(lambda (p) (list (cadr p) (car p))) pts)))
  (setq xs (nc:duy-nhat (mapcar 'car pts)) ys (nc:duy-nhat (mapcar 'cadr pts))
        nx (1- (length xs)) ny (1- (length ys)) mo nil kq nil j 0)
  (while (< j ny)
    ;; các dải ô liền nhau trong hàng j: (i0 i1)
    (setq chay nil i 0 i0 nil)
    (while (<= i nx)
      (if (and (< i nx)
               (nc:trong-dg (list (/ (+ (nth i xs) (nth (1+ i) xs)) 2.0) (/ (+ (nth j ys) (nth (1+ j) ys)) 2.0)) pts))
        (if (null i0) (setq i0 i))
        (if i0 (setq chay (cons (list i0 (1- i)) chay) i0 nil))
      )
      (setq i (1+ i))
    )
    ;; mo: hình đang mở (i0 i1 j0); dải trùng thì kéo dài, không thì đóng
    (setq moi nil)
    (foreach c chay
      (if (setq tim (vl-some '(lambda (m) (if (and (= (car m) (car c)) (= (cadr m) (cadr c))) m)) mo))
        (setq moi (cons tim moi) mo (vl-remove tim mo))
        (setq moi (cons (list (car c) (cadr c) j) moi))
      )
    )
    (foreach m mo (setq kq (cons (list (car m) (cadr m) (caddr m) (1- j)) kq)))
    (setq mo moi j (1+ j))
  )
  (foreach m mo (setq kq (cons (list (car m) (cadr m) (caddr m) (1- ny)) kq)))
  (mapcar '(lambda (r)
             (setq x0 (nth (nth 0 r) xs) x1 (nth (1+ (nth 1 r)) xs) y0 (nth (nth 2 r) ys) y1 (nth (1+ (nth 3 r)) ys))
             (if dao (list y0 x0 y1 x1) (list x0 y0 x1 y1)))
          kq)
)

;;; Tách theo hàng và theo cột, lấy cách ra ít hình hơn
(defun amep:tach-luoi (pts / a b)
  (setq a (amep:tach-luoi-1 pts nil) b (amep:tach-luoi-1 pts T))
  (if (<= (length a) (length b)) a b)
)

;;; Đa giác chỉ có cạnh song song X, Y
(defun amep:truc-giao (pts / n i a b)
  (setq n (length pts) i 0)
  (while (and (< i n)
              (setq a (nth i pts) b (nth (rem (1+ i) n) pts))
              (or (< (abs (- (car a) (car b))) 0.5) (< (abs (- (cadr a) (cadr b))) 0.5)))
    (setq i (1+ i))
  )
  (= i n)
)

;;; Các khung chữ nhật để bo một vùng, theo hình lỗ mở:
;;;   - vùng gộp từ nhiều ô X / lỗ mở không chồng nhau: mỗi ô một khung (bo theo từng lỗ mở);
;;;   - vùng chữ nhật: 1 khung;
;;;   - vùng không chữ nhật còn lại (ô chồng nhau, khung MEP chữ L): tách lưới đa giác;
;;;   - đa giác có cạnh xiên: nil (xem lại).
(defun amep:khung-bo (v / k o dt tong)
  (setq k (nth 2 v) o (nth 5 v) dt (abs (nc:dt-dg (cadr v))))
  (cond
    ((and (> (length o) 1)
          (setq tong (apply '+ (mapcar 'nc:dt-kh o)))
          (< (abs (- tong dt)) (* 0.03 dt)))
     o)
    ((>= (/ dt (nc:dt-kh k)) (amep:cfg 'ti-le-chu-nhat)) (list k))
    ((amep:truc-giao (cadr v)) (amep:tach-luoi (cadr v)))
  )
)

;;; Từ một vùng của nc:do (số thứ tự iv) -> danh sách bản ghi, mỗi khung bo một bản ghi:
;;; (trang-thai cx cy rong dai d1 d2 goc ins lech ti-le so-ong kieu vung so-khung)
;;; trang-thai: "se_chen" | "da_co" | "xem_lai" (không tách được) | "vuot" (vượt giới hạn block)
(defun amep:tinh (v co iv / ks tl)
  (setq ks (amep:khung-bo v)
        tl (/ (abs (nc:dt-dg (cadr v))) (nc:dt-kh (nth 2 v))))
  (if ks
    (mapcar '(lambda (k) (amep:tinh-kh k co tl (nth 3 v) (car v) iv (length ks))) ks)
    (progn
      (setq ks (amep:tinh-kh (nth 2 v) co tl (nth 3 v) (car v) iv 1))
      (list (if (= (car ks) "da_co") ks (cons "xem_lai" (cdr ks))))
    )
  )
)

;;; Một khung chữ nhật k -> bản ghi
(defun amep:tinh-kh (k co tl so-ong kieu iv sk / w h d1 d2 goc ins tt)
  (setq w (- (nth 2 k) (nth 0 k))
        h (- (nth 3 k) (nth 1 k))
        d1 (amep:tron (max w h))
        d2 (amep:tron (min w h)))
  (if (>= h w)
    ;; ô dọc: góc 0, Distance1 theo Y
    (setq goc 0.0
          ins (list (+ (nth 0 k) (/ (- w d2) 2.0)) (+ (nth 1 k) (/ (- h d1) 2.0)) 0.0))
    ;; ô ngang: góc 90, trục Y của block hướng -X thế giới, điểm chèn ở góc dưới phải
    (setq goc 90.0
          ins (list (- (nth 2 k) (/ (- w d1) 2.0)) (+ (nth 1 k) (/ (- h d2) 2.0)) 0.0))
  )
  (setq tt
         (cond
           ((vl-some '(lambda (q) (> (nc:giao k q) (* (amep:cfg 'trung) (min (nc:dt-kh k) (nc:dt-kh q))))) co) "da_co")
           ((or (< d1 (amep:cfg 'd1-min)) (> d1 (amep:cfg 'd1-max))
                (< d2 (amep:cfg 'd2-min)) (> d2 (amep:cfg 'd2-max))) "vuot")
           ("se_chen")
         ))
  (list tt (/ (+ (nth 0 k) (nth 2 k)) 2.0) (/ (+ (nth 1 k) (nth 3 k)) 2.0) w h d1 d2 goc ins
        (max (abs (- (max w h) d1)) (abs (- (min w h) d2))) tl so-ong kieu iv sk)
)

;;; Gán giá trị tham số dynamic; trả về giá trị đọc lại
(defun amep:tham-so (o ten gt / kq)
  (foreach p (vlax-invoke o 'GetDynamicBlockProperties)
    (if (= (strcase (vla-get-PropertyName p)) (strcase ten))
      (progn
        (vl-catch-all-apply 'vlax-put (list p 'Value gt))
        (setq kq (vlax-get p 'Value))
      )
    )
  )
  kq
)

;;; Chèn 1 A-MEP theo kết quả amep:tinh; trả về ename hoặc nil.
;;; Chế độ "dong": chèn A-MEP dynamic rồi gán Distance1 / Distance2; "tinh": chèn block tĩnh đúng kích thước.
(defun amep:chen (ms r / o g1 g2 ten)
  (setq ten (if (= amep-che-do "tinh") (amep:block-tinh (nth 5 r) (nth 6 r)) (amep:cfg 'ten-block)))
  (setq o (vl-catch-all-apply 'vla-InsertBlock
                              (list ms (vlax-3d-point (nth 8 r)) ten 1.0 1.0 1.0
                                    (* pi (/ (nth 7 r) 180.0)))))
  (if (not (vl-catch-all-error-p o))
    (progn
      (vla-put-Layer o (amep:cfg 'layer))
      (if (/= amep-che-do "tinh")
        (progn
          (setq g1 (amep:tham-so o "Distance1" (nth 5 r))
                g2 (amep:tham-so o "Distance2" (nth 6 r)))
          (if (not (and g1 g2 (equal g1 (nth 5 r) 0.5) (equal g2 (nth 6 r) 0.5)))
            (princ (strcat "\n  Cảnh báo: block tại " (rtos (nth 1 r) 2 0) ", " (rtos (nth 2 r) 2 0)
                           " không nhận đúng tham số (Distance1/Distance2) - Cần xác nhận lại"))
          )
        )
      )
      (vlax-vla-object->ename o)
    )
  )
)

;;; ---------- Báo cáo ----------
(defun amep:nhan (tt)
  (cdr (assoc tt '(("se_chen" . "Sẽ chèn") ("da_co" . "Đã có A-MEP") ("xem_lai" . "Không tách được thành chữ nhật - Cần xác nhận lại")
                   ("vuot" . "Vượt giới hạn block - Cần xác nhận lại") ("da_chen" . "Đã chèn"))))
)

;;; In các khung cần xem lại (không tách được, vượt giới hạn block)
(defun amep:in-ds (ds / i)
  (setq i 0)
  (foreach r ds
    (setq i (1+ i))
    (if (member (car r) '("xem_lai" "vuot"))
      (princ (strcat "\n " (itoa i) " | " (itoa (nth 13 r))
                     (if (> (nth 14 r) 1) (strcat " (tách " (itoa (nth 14 r)) " khung)") "")
                     " | " (amep:nhan (car r)) " | " (rtos (nth 1 r) 2 0) " | " (rtos (nth 2 r) 2 0)
                     " | " (rtos (nth 3 r) 2 0) " x " (rtos (nth 4 r) 2 0)
                     " | " (rtos (nth 5 r) 2 0) " x " (rtos (nth 6 r) 2 0) " | " (rtos (nth 7 r) 2 0) " | " (nth 12 r)))
    )
  )
)

;;; CSV chỉ ghi ký tự ASCII (mã kiểu), Python đổi sang tiếng Việt khi xuất Excel
(defun amep:ma-kieu (s)
  (cond ((= s "Dấu X trục / hộp") "X") ((= s "Lỗ mở có ống đứng") "LOMO_ONG")
        ((= s "Khung lỗ mở MEP có ống (không có X)") "KHUNG_ONG") ("KHAC"))
)

(defun amep:ghi-csv (ds f / fh i)
  (setq fh (open f "w") i 0)
  (write-line "stt,trang_thai,cx,cy,rong,dai,d1,d2,goc,ins_x,ins_y,lech,ti_le,so_ong,kieu,vung,so_khung" fh)
  (foreach r ds
    (setq i (1+ i))
    (write-line (strcat (itoa i) "," (car r) "," (rtos (nth 1 r) 2 1) "," (rtos (nth 2 r) 2 1) ","
                        (rtos (nth 3 r) 2 1) "," (rtos (nth 4 r) 2 1) "," (rtos (nth 5 r) 2 0) "," (rtos (nth 6 r) 2 0) ","
                        (rtos (nth 7 r) 2 0) "," (rtos (car (nth 8 r)) 2 1) "," (rtos (cadr (nth 8 r)) 2 1) ","
                        (rtos (nth 9 r) 2 1) "," (rtos (nth 10 r) 2 3) "," (itoa (nth 11 r)) "," (amep:ma-kieu (nth 12 r))
                        "," (itoa (nth 13 r)) "," (itoa (nth 14 r)))
                fh)
  )
  (close fh)
)

;;; ---------- Chạy ----------
;;; Khoá (khoa = T) / mở khoá (nil) layer lay. Khi mở khoá: trả về T nếu layer đang bị khoá.
(defun amep:khoa-layer (lay khoa / d f)
  (if (setq d (entget (tblobjname "LAYER" lay)))
    (progn
      (setq f (cdr (assoc 70 d)))
      (cond
        (khoa (entmod (subst (cons 70 (logior f 4)) (assoc 70 d) d)) T)
        ((/= 0 (logand f 4)) (entmod (subst (cons 70 (- f 4)) (assoc 70 d) d)) T)
      )
    )
  )
)

;;; Dò, chèn, gom block. csv: đường dẫn file CSV kết quả (nil = không ghi). Trả về số block đã chèn.
(defun amep:chay (csv / *error* nc-memo nc-co-cache nc-lay-cache bien cu kq co ds se ms ss n e dem tb khoa)
  (defun *error* (msg)
    (if cu (mapcar '(lambda (b v) (if v (setvar b v))) bien cu))
    (if khoa (amep:khoa-layer (amep:cfg 'layer) T))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nLỗi: " msg))
    )
    (command-s "_.UNDO" "_E")
    (princ)
  )
  (setq bien '("CLAYER" "OSMODE" "CMDECHO" "TILEMODE")
        cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (if (= (getvar "TILEMODE") 0) (setvar "TILEMODE" 1))
  ;; biến toàn cục: tên block gom lần chạy này, cho script chen_amep_vao_ban_sao.ps1 ghi log
  (setq amep-gom-cuoi nil dem 0)
  (setq kq (nc:do) co (amep:co-san))
  (setq n 0 ds (apply 'append (mapcar '(lambda (v) (amep:tinh v co (setq n (1+ n)))) (car kq))))
  (setq se (vl-remove-if-not '(lambda (r) (= (car r) "se_chen")) ds))
  (princ (strcat "\n  Vùng trục / hộp: " (itoa (length (car kq))) " | khung bo: " (itoa (length ds))
                 " | sẽ chèn: " (itoa (length se))
                 " | đã có A-MEP: " (itoa (length (vl-remove-if-not '(lambda (r) (= (car r) "da_co")) ds)))
                 " | cần xem lại: " (itoa (length (vl-remove-if-not '(lambda (r) (member (car r) '("xem_lai" "vuot"))) ds)))))
  (if se
    (if (amep:nap-block)
      (progn
        (command "_.UNDO" "_BE")
        (setvar "OSMODE" 0)
        ;; layer A-MEP đang khoá: mở khoá tạm để chèn và gom block, xong khoá lại
        (setq khoa (amep:khoa-layer (amep:cfg 'layer) nil))
        (setq ms (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object))) ss (ssadd))
        (setq ds (mapcar '(lambda (r)
                            (if (and (= (car r) "se_chen") (setq e (amep:chen ms r)))
                              (progn (ssadd e ss) (setq dem (1+ dem)) (cons "da_chen" (cdr r)))
                              r))
                         ds))
        ;; cập nhật Field diện tích trong các block vừa chèn
        (if (> (sslength ss) 0) (command "_.UPDATEFIELD" ss ""))
        (princ (strcat "\nĐã chèn " (itoa dem) " block " (amep:cfg 'ten-block) " trên layer " (amep:cfg 'layer) "."))
        ;; gom vào 1 block để dễ kiểm soát (người dùng chốt 22/10/2026)
        (setq tb nil)
        (if (> (sslength ss) 0)
          (setq tb (amep:gom-block (vl-remove-if 'listp (mapcar 'cadr (ssnamex ss))))))
        (setq amep-gom-cuoi tb)
        (if khoa (amep:khoa-layer (amep:cfg 'layer) T))
        (command "_.UNDO" "_E")
        (princ "\nCtrl+Z một lần để hoàn tác.")
      )
    )
    (princ "\nKhông có trục / hộp mới cần chèn A-MEP.")
  )
  (amep:in-ds ds)
  (if csv (amep:ghi-csv ds csv))
  (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
  (princ)
  dem
)

;;; LOMO: chèn luôn, không hỏi
(defun c:LOMO () (amep:chay nil) (princ))

(princ "\nĐã nạp lệnh LOMO: tự chèn block A-MEP bo trục / hộp kỹ thuật, layer A-MEP.")
(princ)
