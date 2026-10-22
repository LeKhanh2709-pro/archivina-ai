;;; amep_bo_truc.lsp
;;; Lệnh AMEP: tự tìm trục kỹ thuật / hộp kỹ thuật trên mặt bằng tầng và chèn block lỗ mở
;;; A-MEP (dynamic block) co giãn khít khung từng trục / hộp (bản LISP của skill truc-lo-mo-mep).
;;; Lệnh KT-AMEP: như AMEP nhưng hỏi trước khi chèn (xem danh sách ô).
;;;
;;; Nhận diện trục / hộp: dùng chung hàm nc:do của lệnh NCL (fire_stop_shaft.lsp), cùng quy tắc
;;; với skill ngan-chay-truc-hkt: ô có dấu X của trục / hộp, lỗ mở "lo mo" có ống đứng, khung lỗ mở
;;; MEP có ống; bỏ thang máy, nội thất, lỗ mở sàn không có ống.
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
;;; Chèn trên layer A_MEP (như mẫu).
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước (lệnh thêm block vào bản vẽ đang mở).
;;;   2. APPLOAD -> chọn fire_stop_shaft.lsp và amep_bo_truc.lsp (cùng thư mục D:\AI\scripts\lisp).
;;;      Chưa nạp fire_stop_shaft.lsp thì lệnh tự tìm và nạp.
;;;   3. Gõ AMEP: quét toàn bộ Model, chèn A-MEP cho mọi trục / hộp chưa có, rồi in các ô cần xem lại.
;;;      Gõ KT-AMEP để xem trước, lệnh hỏi [Chen/Danhsach/Thoat].
;;;   4. Bản vẽ chưa có block A-MEP: lệnh chép định nghĩa block (và layer A_MEP) từ file thư viện
;;;      (xem amep:cfg 'thu-vien). Bản vẽ đã có A-MEP thì dùng block có sẵn, không định nghĩa lại.
;;;   5. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ.
;;;   Chạy lại lệnh: ô đã có A-MEP (chồng > 50%) không chèn trùng.
;;;   Không chèn, chỉ liệt kê (Cần xác nhận lại): vùng có cạnh xiên (không tách được thành chữ nhật),
;;;   khung vượt giới hạn tham số block (cạnh ngắn > 3000 hoặc cạnh dài > 4000).
;;;
;;; Yêu cầu: AutoCAD đầy đủ 2025 / 2026 (chạy được cả 2021+), LISPSYS = 1, file lưu UTF-8.
;;;   KHÔNG chạy được trong AutoCAD Core Console (không có COM để gán tham số dynamic block).
;;; Giới hạn: như NCL, chỉ đúng với mặt bằng có trục nhà song song X, Y.

(vl-load-com)

;;; ---------- Cấu hình (sửa ở đây nếu dự án khác) ----------
(defun amep:cfg (k)
  (cdr
    (assoc
      k
      '((ten-block . "A-MEP")
        (layer . "A_MEP")
        (thu-vien . "D:/AI/.claude/skills/truc-lo-mo-mep/assets/A-MEP_thu_vien.dwg")
        (nc-lsp . "D:/AI/scripts/lisp/fire_stop_shaft.lsp")
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

;;; Nạp fire_stop_shaft.lsp (hàm dò nc:do) nếu chưa có
(defun amep:nap-nc (/ f)
  (if (not nc:do)
    (if (setq f (or (findfile "fire_stop_shaft.lsp") (findfile (amep:cfg 'nc-lsp))))
      (load f)
    )
  )
  nc:do
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

;;; Bảo đảm bản vẽ có block A-MEP và layer A_MEP. Thiếu thì chép từ file thư viện (ObjectDBX, chỉ đọc).
;;; Trả về T nếu đủ.
(defun amep:nap-block (/ acad doc dbx f ten lay)
  (setq ten (amep:cfg 'ten-block) lay (amep:cfg 'layer)
        acad (vlax-get-acad-object) doc (vla-get-ActiveDocument acad))
  (if (not (and (tblsearch "BLOCK" ten) (tblsearch "LAYER" lay)))
    (progn
      (setq f (findfile (amep:cfg 'thu-vien))
            dbx (vl-catch-all-apply 'vla-GetInterfaceObject
                                    (list acad (strcat "ObjectDBX.AxDbDocument." (substr (getvar "ACADVER") 1 2)))))
      (cond
        ((null f) (princ (strcat "\nKhông thấy file thư viện block: " (amep:cfg 'thu-vien))))
        ((vl-catch-all-error-p dbx) (princ "\nKhông mở được ObjectDBX để chép block A-MEP."))
        ((vl-catch-all-error-p (vl-catch-all-apply 'vla-Open (list dbx f)))
         (princ (strcat "\nKhông mở được file thư viện: " f)))
        (t
         (if (not (tblsearch "BLOCK" ten)) (amep:chep dbx (vla-get-Blocks dbx) ten (vla-get-Blocks doc)))
         (if (not (tblsearch "LAYER" lay)) (amep:chep dbx (vla-get-Layers dbx) lay (vla-get-Layers doc)))
         (if (tblsearch "BLOCK" ten) (princ (strcat "\nĐã chép block " ten " từ " f)))
        )
      )
      (if (and dbx (not (vl-catch-all-error-p dbx))) (vlax-release-object dbx))
    )
  )
  (and (tblsearch "BLOCK" ten) (tblsearch "LAYER" lay))
)

;;; ---------- A-MEP có sẵn ----------
;;; Khung bao (x0 y0 x1 y1) của mọi A-MEP trong Model (kể cả bản đã kéo giãn: tên *U..)
(defun amep:co-san (/ ss i o a b kq)
  (setq kq nil)
  (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 (strcat (amep:cfg 'ten-block) ",`*U*")))))
    (repeat (setq i (sslength ss))
      (setq o (vlax-ename->vla-object (ssname ss (setq i (1- i)))))
      (if (and (vlax-property-available-p o 'EffectiveName)
               (= (strcase (vla-get-EffectiveName o)) (strcase (amep:cfg 'ten-block)))
               (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-GetBoundingBox (list o 'a 'b)))))
        (setq a (vlax-safearray->list a) b (vlax-safearray->list b)
              kq (cons (list (car a) (cadr a) (car b) (cadr b)) kq))
      )
    )
  )
  kq
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

;;; Chèn 1 A-MEP theo kết quả amep:tinh; trả về ename hoặc nil
(defun amep:chen (ms r / o g1 g2)
  (setq o (vl-catch-all-apply 'vla-InsertBlock
                              (list ms (vlax-3d-point (nth 8 r)) (amep:cfg 'ten-block) 1.0 1.0 1.0
                                    (* pi (/ (nth 7 r) 180.0)))))
  (if (not (vl-catch-all-error-p o))
    (progn
      (vla-put-Layer o (amep:cfg 'layer))
      (setq g1 (amep:tham-so o "Distance1" (nth 5 r))
            g2 (amep:tham-so o "Distance2" (nth 6 r)))
      (if (not (and g1 g2 (equal g1 (nth 5 r) 0.5) (equal g2 (nth 6 r) 0.5)))
        (princ (strcat "\n  Cảnh báo: block tại " (rtos (nth 1 r) 2 0) ", " (rtos (nth 2 r) 2 0)
                       " không nhận đúng tham số (Distance1/Distance2) - Cần xác nhận lại"))
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

(defun amep:in-ds (ds chi-loi / i)
  (setq i 0)
  (if (and ds (not chi-loi)) (princ "\n STT | Vùng | Trạng thái | Tâm X | Tâm Y | Rộng x Dài | D1 x D2 | Góc | Kiểu"))
  (foreach r ds
    (setq i (1+ i))
    (if (or (not chi-loi) (member (car r) '("xem_lai" "vuot")))
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

(defun amep:hoi (n)
  (initget "Chen Danhsach Thoat")
  (cond ((getkword (strcat "\nChèn A-MEP cho " (itoa n) " ô? [Chen/Danhsach/Thoat] <Chen>: "))) ("Chen"))
)

;;; ---------- Chạy ----------
;;; tu-dong = T: không hỏi, chèn luôn. csv: đường dẫn file CSV kết quả (nil = không ghi)
(defun amep:chay (tu-dong csv / *error* nc-memo nc-co-cache nc-lay-cache bien cu kq co ds se chon ms ss n e dem)
  (defun *error* (msg)
    (if cu (mapcar '(lambda (b v) (if v (setvar b v))) bien cu))
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
  (cond
    ((not (amep:nap-nc))
     (princ "\nChưa nạp được fire_stop_shaft.lsp (hàm dò trục nc:do). APPLOAD file này trước."))
    (t
     (setq kq (nc:do) co (amep:co-san))
     (setq n 0 ds (apply 'append (mapcar '(lambda (v) (amep:tinh v co (setq n (1+ n)))) (car kq))))
     (setq se (vl-remove-if-not '(lambda (r) (= (car r) "se_chen")) ds))
     (princ (strcat "\n  Vùng trục / hộp: " (itoa (length (car kq))) " | khung bo: " (itoa (length ds))
                    " | sẽ chèn: " (itoa (length se))
                    " | đã có A-MEP: " (itoa (length (vl-remove-if-not '(lambda (r) (= (car r) "da_co")) ds)))
                    " | cần xem lại: " (itoa (length (vl-remove-if-not '(lambda (r) (member (car r) '("xem_lai" "vuot"))) ds)))))
     (setq chon (if tu-dong "Chen" (amep:hoi (length se))))
     (while (= chon "Danhsach")
       (amep:in-ds ds nil)
       (setq chon (amep:hoi (length se)))
     )
     (setq dem 0)
     (if (and (= chon "Chen") se)
       (if (amep:nap-block)
         (progn
           (command "_.UNDO" "_BE")
           (setvar "OSMODE" 0)
           (setq ms (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object))) ss (ssadd))
           (setq ds (mapcar '(lambda (r)
                               (if (and (= (car r) "se_chen") (setq e (amep:chen ms r)))
                                 (progn (ssadd e ss) (setq dem (1+ dem)) (cons "da_chen" (cdr r)))
                                 r))
                            ds))
           ;; cập nhật Field diện tích trong các block vừa chèn
           (if (> (sslength ss) 0) (command "_.UPDATEFIELD" ss ""))
           (command "_.UNDO" "_E")
           (princ (strcat "\nĐã chèn " (itoa dem) " block " (amep:cfg 'ten-block) " trên layer " (amep:cfg 'layer)
                          ". Ctrl+Z một lần để hoàn tác."))
         )
         (princ "\nKhông có block A-MEP: không chèn gì.")
       )
       (princ (if se "\nKhông chèn gì." "\nKhông có trục / hộp mới cần chèn A-MEP."))
     )
     (amep:in-ds ds T)
     (if csv (amep:ghi-csv ds csv))
    )
  )
  (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
  (princ)
  dem
)

;;; AMEP: chèn luôn, không hỏi
(defun c:AMEP () (amep:chay T nil) (princ))

;;; KT-AMEP: hỏi [Chen/Danhsach/Thoat] trước khi chèn
(defun c:KT-AMEP () (amep:chay nil nil) (princ))

(princ "\nĐã nạp lệnh AMEP: tự chèn block A-MEP bo trục / hộp kỹ thuật (KT-AMEP: hỏi trước khi chèn).")
(princ)
