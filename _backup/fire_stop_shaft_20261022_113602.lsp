;;; fire_stop_shaft.lsp
;;; Lệnh NCL: tự tìm trục kỹ thuật / hộp kỹ thuật trên mặt bằng tầng và vẽ luôn
;;; đường bo + hatch ngăn cháy lan (bản LISP của skill ngan-chay-truc-hkt).
;;; Lệnh KT-NGANCHAY: như NCL nhưng hỏi trước khi vẽ (xem danh sách vùng).
;;;
;;; Nhận diện (quét cả block lồng nhau, xref đã bind):
;;;   1. Dấu X của trục / hộp: 2 nét chéo nối 4 góc một ô chữ nhật (cạnh 150 - 4000 mm).
;;;      Các ô X chạm nhau được gộp thành một vùng (hộp chữ L).
;;;   2. Ký hiệu ống đứng: vòng tròn trong block tên *PIPE* (piped125-xi, PIPE150).
;;;   3. Block lỗ mở sàn "lo mo": chỉ nhận khi bên trong có ống đứng; X của nó chồng lên ô X
;;;      của hộp thì bỏ (tránh đường bo lồi bậc).
;;;   4. Khung kín trên layer *LO MO* của MEP có ống bên trong: hộp kỹ thuật dù không có X.
;;;   Bỏ qua: cabin thang máy, đồ nội thất, nét khuất tầng hầm, vùng đã có hatch NET.
;;; Vẽ mỗi vùng: polyline kín màu 6 + hatch NET tỉ lệ 1000, góc 315, màu RGB 220,30,30,
;;; liên kết với polyline. Cả hai trên layer A-Material.
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước (lệnh thêm đối tượng vào bản vẽ đang mở).
;;;   2. APPLOAD -> chọn fire_stop_shaft.lsp (hoặc kéo thả file vào cửa sổ AutoCAD).
;;;   3. Gõ NCL. Lệnh quét toàn bộ Model, vẽ luôn bo + hatch cho mọi trục / hộp tìm được, rồi báo
;;;      số vùng và toạ độ lỗ mở bị loại, ống đứng chưa có khung (nếu có) để kiểm tra.
;;;      Muốn xem trước khi vẽ thì gõ KT-NGANCHAY, lệnh hỏi [Ve/Danhsach/Thoat]:
;;;        Ve       : vẽ bo + hatch cho các vùng "sẽ hatch"
;;;        Danhsach : in danh sách vùng (tâm, kích thước, số ống, kiểu) và toạ độ ống chưa có khung
;;;        Thoat    : không vẽ gì
;;;   4. Sau khi vẽ, lệnh chuyển bản vẽ thành mặt bằng ngăn cháy lan: tắt layer nội thất / thiết bị
;;;      vệ sinh, đổi mọi layer khác sang màu xám 150,150,150 (chỉ đường bo + hatch còn nổi màu).
;;;      Trạng thái layer cũ được lưu thành layer state "TRUOC NGAN CHAY LAN" (khôi phục bằng
;;;      Layer States Manager / LAYERSTATE). CHỈ đổi màu / tắt trong bảng layer: không sửa màu từng
;;;      đối tượng, không bind xref / block / link (người dùng chốt 22/10/2026). Đối tượng gán màu
;;;      riêng (không BYLAYER) vì thế vẫn giữ màu.
;;;   5. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ.
;;;   Chạy lại lệnh lần 2: vùng đã có hatch NET (layer A-Material hoặc A-HATCH- Color) không vẽ trùng.
;;;   File lớn (~50 MB) có thể mất vài phút ở bước đọc bản vẽ.
;;;
;;; Yêu cầu: AutoCAD 2025 / 2026 (chạy được cả 2021+), LISPSYS = 1, file lưu UTF-8.
;;; Giới hạn: chỉ đúng với mặt bằng có trục nhà song song X, Y (ô X lấy theo khung bao);
;;;   block có pháp tuyến khác +Z / -Z bị coi như +Z.

(vl-load-com)

;;; ---------- Cấu hình (sửa ở đây nếu dự án đặt tên khác) ----------
;;; Mẫu layer so trên tên đã chuẩn hoá: bỏ tiền tố xref "...$0$", bỏ dấu cách, "_" thành "-", chữ hoa.
(defun nc:cfg (k)
  (cdr
    (assoc
      k
      '((layer-bo "A-INTERIOR*" "*N?ITH?T*" "*NOITHAT*" "*FURN*" "A-DOOR*" "A-C?A*" "A-CUA*"
                  "A-WINDOW*" "A-GLAZ*" "A-DIM*" "A-TEXT*" "A-SYMBOL*" "A-KIHIEU*" "A-K?HI?U*"
                  "A-AXIS" "DEFPOINTS" "*|*")
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
        (layer-state . "TRUOC NGAN CHAY LAN")
       )
    )
  )
)

;;; ---------- Tiện ích chuỗi ----------
(defun nc:khop (s pats)
  (and s (vl-some '(lambda (p) (wcmatch s p)) pats))
)

;;; Chuẩn hoá tên layer: "CH19$0$A_MEP" -> "A-MEP", "A- Truc ME" -> "A-TRUCME"
(defun nc:chuan (lay / l n i j bd c)
  (setq l (vl-string->list lay) n (length l) i 0 bd 0)
  (while (< i n)
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
  )
)

(defun nc:doc-insert (d nz / nm con bp p sx sy r a b c dd e f m fl)
  (setq nm (cdr (assoc 2 d)) fl (nc:co-ten nm))
  ;; block cabin thang máy / đồ nội thất / tầng hầm: bỏ cả block, không đọc bên trong
  (if (and (= 0 (logand fl 3)) (tblsearch "BLOCK" nm))
    (progn
      (setq con (nc:phang nm)
            bp  (cdr (assoc 10 (tblsearch "BLOCK" nm)))
            p   (cdr (assoc 10 d))
            sx  (cond ((cdr (assoc 41 d))) (1.0))
            sy  (cond ((cdr (assoc 42 d))) (1.0))
            r   (cond ((cdr (assoc 50 d))) (0.0)))
      (setq a (* sx (cos r)) b (- (* sy (sin r))) dd (* sx (sin r)) e (* sy (cos r)))
      (setq c (+ (car p) (- (+ (* a (car bp)) (* b (cadr bp)))))
            f (+ (cadr p) (- (+ (* dd (car bp)) (* e (cadr bp))))))
      (setq m (if (minusp nz) (list (- a) (- b) (- c) dd e f) (list a b c dd e f)))
      (mapcar '(lambda (x) (nc:bien x m (cdr (assoc 8 d)) fl)) con)
    )
  )
)

;;; Biến đổi một phần tử con sang hệ của block cha
(defun nc:bien (x m lay-ins fl / lay fin k)
  (setq k (car x)
        lay (if (= (strcase (nth (if (= k "C") 3 (if (= k "S") 3 2)) x)) "0")
              lay-ins
              (nth (if (= k "P") 2 3) x)))
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
    ((= k "P")
     (setq fin (cond ((nth 4 x)) (fl)))
     (list "P" (mapcar '(lambda (p) (nc:ap m p)) (nth 1 x)) lay (logior (nth 3 x) fl) fin)
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
(defun nc:ghep-x (dc / l i n a b k1 ok kq trung)
  (setq l (vl-sort dc '(lambda (a b) (< (car a) (car b)))) kq nil)
  (while l
    (setq a (car l) l (cdr l) b l)
    (while (and b (< (- (car (car b)) (car a)) 40.0))
      (if (and (/= (nth 4 a) (nth 4 (car b)))
               (< (abs (- (nth 1 a) (nth 1 (car b)))) 40.0)
               (< (abs (- (nth 2 a) (nth 2 (car b)))) 40.0)
               (< (abs (- (nth 3 a) (nth 3 (car b)))) 40.0))
        (progn
          (setq k1 (list (nth 0 a) (nth 1 a) (nth 2 a) (nth 3 a)))
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

;;; ---------- Hatch NET đã có (model space) ----------
(defun nc:hatch-co (/ ss i d kq vong pha lay nz)
  (if (setq ss (ssget "X" '((0 . "HATCH") (2 . "NET") (410 . "Model"))))
    (progn
      (setq i 0)
      (repeat (sslength ss)
        (setq d (entget (ssname ss i)) i (1+ i) lay (car (nc:tt-layer (cdr (assoc 8 d)))) nz (nc:nz d))
        (if (member lay '("A-MATERIAL" "A-HATCH-COLOR"))
          (progn
            (setq pha nil vong nil)
            (foreach x d
              (cond
                ((= (car x) 91) (setq pha t))
                ((and pha (= (car x) 92))
                 (if vong (setq kq (cons (nc:khung vong) kq)))
                 (setq vong nil))
                ((and pha (member (car x) '(10 11))) (setq vong (cons (nc:ocs (cdr x) nz) vong)))
                ((and pha (= (car x) 75))
                 (if vong (setq kq (cons (nc:khung vong) kq)))
                 (setq pha nil vong nil))
              )
            )
          )
        )
      )
    )
  )
  kq
)

;;; ---------- Dò toàn bộ bản vẽ ----------
;;; Trả về (vung loai ong-le) ; vung: (kieu dinh khung so-ong trang-thai)
(defun nc:do (/ ss i d tat x lay tt fl fin dx dy dc ong khung ox truc lomo nhom vung loai co
                kk dt g p n ong-le)
  (princ "\nĐang đọc bản vẽ (chỉ đọc, kể cả block lồng nhau)...")
  (setq ss (ssget "X" '((410 . "Model"))) i 0 tat nil)
  (repeat (sslength ss)
    (setq d (entget (ssname ss i)) i (1+ i))
    (if (/= (cdr (assoc 0 d)) "HATCH") (setq tat (append (nc:doc-ent d) tat)))
  )
  (princ (strcat "\n  Phần tử hình học: " (itoa (length tat))))
  (setq dc nil ong nil khung nil)
  (foreach x tat
    (setq lay (nth (if (= (car x) "P") 2 3) x)
          fl  (nth (if (= (car x) "P") 3 4) x)
          fin (nth (if (= (car x) "P") 4 5) x)
          tt  (nc:tt-layer lay))
    (cond
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
    (if p (setq vung (cons (list "Dấu X trục / hộp" p (nc:khung p)) vung)))
  )
  (setq loai nil)
  (foreach k lomo
    (cond
      ((vl-some '(lambda (v) (> (nc:giao k (nth 2 v)) (* 0.05 (min (nc:dt-kh k) (nc:dt-kh (nth 2 v)))))) vung))
      ((> (nc:so-ong k ong) 0)
       (setq vung (cons (list "Lỗ mở có ống đứng" (nc:bao-chu-nhat (list k)) k) vung)))
      ((not (vl-some '(lambda (q) (> (nc:giao k q) (* 0.5 (nc:dt-kh k)))) loai))
       (setq loai (cons k loai)))
    )
  )
  (foreach p (vl-sort khung '(lambda (a b) (< (abs (nc:dt-dg a)) (abs (nc:dt-dg b)))))
    (setq kk (nc:khung p) dt (abs (nc:dt-dg p)))
    (if (and (>= dt 1e4)
             (not (vl-some '(lambda (v) (> (nc:giao kk (nth 2 v)) (* 0.2 (min (nc:dt-kh kk) (nc:dt-kh (nth 2 v)))))) vung))
             (vl-some '(lambda (q) (nc:trong-dg q p)) ong))
      (setq vung (cons (list "Khung lỗ mở MEP có ống (không có X)" p kk) vung))
    )
  )
  (setq co (nc:hatch-co))
  (setq vung
         (mapcar
           '(lambda (v / k)
              (setq k (nth 2 v))
              (list (car v) (cadr v) k (nc:so-ong k ong)
                    (if (vl-some '(lambda (h) (> (nc:giao k h) (* 0.5 (nc:dt-kh k)))) co) "da_co" "se_hatch")))
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
  (and (not (eq h e)) (= (cdr (assoc 0 (entget h))) "HATCH"))
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
(defun nc:lam-mo (lay / l ten an ls)
  (setq ls (nc:cfg 'layer-state))
  (if (and layerstate-save (not (layerstate-has ls)))
    (layerstate-save ls (+ 1 32) nil)
  )
  (setq l (tblnext "LAYER" T) an nil)
  (while l
    (setq ten (cdr (assoc 2 l)))
    (if (and (/= (strcase ten) (strcase lay)) (nc:khop (nc:chuan ten) (nc:cfg 'layer-an)))
      (setq an (cons ten an))
    )
    (setq l (tblnext "LAYER"))
  )
  (command "_.-LAYER" "_C" "_T" (nc:cfg 'mau-mo) "*" "")
  (foreach n an (command "_.-LAYER" "_OFF" n ""))
  (princ (strcat "\nĐã tắt " (itoa (length an)) " layer nội thất / thiết bị vệ sinh, đổi các layer khác sang màu "
                 (nc:cfg 'mau-mo) (if layerstate-save (strcat ". Layer state cũ: \"" ls "\".") ".")))
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
(defun nc:chay (tu-dong / *error* nc-memo nc-co-cache nc-lay-cache bien cu kq vung loai ong-le
                          se n-ve n-h chon lay)
  (defun *error* (msg)
    (if cu (mapcar '(lambda (b v) (if v (setvar b v))) bien cu))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nLỗi: " msg))
    )
    (command-s "_.UNDO" "_E")
    (princ)
  )
  (setq bien '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO")
        cu (mapcar 'getvar bien)
        lay (nc:cfg 'layer-ve))
  (setvar "CMDECHO" 0)
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
      (setq n-ve 0 n-h 0)
      (foreach v se
        (setq n-ve (1+ n-ve))
        (if (nc:ve-vung (cadr v) lay) (setq n-h (1+ n-h)))
      )
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

;;; NCL: vẽ luôn, không hỏi
(defun c:NCL () (nc:chay T))

;;; KT-NGANCHAY: hỏi [Ve/Danhsach/Thoat] trước khi vẽ
(defun c:KT-NGANCHAY () (nc:chay nil))

(princ "\nĐã nạp lệnh NCL: tự vẽ bo + hatch ngăn cháy lan trục / hộp kỹ thuật (KT-NGANCHAY: hỏi trước khi vẽ).")
(princ)
