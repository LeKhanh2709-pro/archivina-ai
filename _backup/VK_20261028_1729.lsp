;;; VK.lsp — Chia đố thanh đứng và dựng vách kính mặt bằng (Archivina)
;;; Lệnh: VK
;;;   Bảng hỏi: chiều dài vách, cửa sổ mở / cửa đi (số lượng, bề rộng tâm-tâm, ô đặt cửa).
;;;   Bảng tự cập nhật số đố và khoảng cách các đố; OK -> chọn điểm đầu vách (mép ngoài) và hướng vách.
;;; Quy tắc chia (người dùng chốt 28/10/2026):
;;;   - Đố rộng 65: tâm đố đầu / cuối cách mép ngoài 32,5; khoảng chia S = L - 65.
;;;   - Trừ bề rộng tâm-tâm các cửa, phần còn lại chia ĐỀU thành N ô kính, N nhỏ nhất để mỗi ô < 1200.
;;;     Không làm tròn khoảng chia.
;;;   - Cửa đặt vào ô thứ k (đếm từ trái, kể cả ô cửa); bỏ trống thì tự rải đều (1 cửa -> ô giữa).
;;; Kết quả: block "VACH KINH <dài>" trên layer A-Window gồm block đố VK_DoDung, cửa VK_CuaSoMo / VK_CuaDi
;;;   (bề rộng khác mặc định -> block kéo giãn VK_CuaSoMo_<rộng> / VK_CuaDi_<rộng>), kính ô cố định, và
;;;   2 hàng kích thước kiểm tra (chuỗi đố + tổng) kiểu "dim cua", layer Defpoints, nằm trong block.
;;; Block lấy từ file thư viện VK_thu_vien.dwg (skill chia-do-vach-kinh\assets), tự tìm:
;;;   biến môi trường ARCHIVINA_VK -> Support File Search Path -> <ARCHIVINA_AI | %USERPROFILE% | <ổ cứng>:\AI>
;;;   \.claude\skills\chia-do-vach-kinh\assets\ -> hỏi chọn file một lần (nhớ bằng setenv).
;;; Yêu cầu: AutoCAD 2021+, LISPSYS = 1, file lưu UTF-8. Không xoá, không sửa đối tượng có sẵn trong bản vẽ.

(vl-load-com)

;;; ---------------------------------------------------------------- thông số
(setq vk:do-rong 65.0            ; bề rộng đố dùng để chia
      vk:toi-da 1200.0           ; khoảng tâm-tâm phải nhỏ hơn
      vk:nua-do 32.87            ; nửa bề rộng đố trong block (65,74 / 2) — vùng không kéo giãn khi đổi rộng cửa
      vk:so-goc 1000.0           ; tâm-tâm 2 đố của block VK_CuaSoMo
      vk:di-goc 1665.0           ; tâm-tâm 2 đố của block VK_CuaDi
      vk:kinh '((42.04 48.04) (56.86 62.86)) ; 2 tấm kính ô cố định (y so với trục vách), theo kính lá cửa sổ
      vk:dim-chuoi 165.0         ; đường dim chuỗi đố cách trục vách
      vk:dim-tong 260.0          ; đường dim tổng cách trục vách
      vk:layer "A-Window"
      vk:layer-dim "Defpoints"
      vk:dimstyle "dim cua"
      vk:file-tv "VK_thu_vien.dwg"
      vk:thu-muc-tv "\\.claude\\skills\\chia-do-vach-kinh\\assets\\")

;;; ---------------------------------------------------------------- tiện ích
(defun vk:undo-ok () (= 1 (logand 3 (getvar "UNDOCTL"))))

;;; Số -> chuỗi gọn, dấu thập phân là dấu phẩy: 1058.75 -> "1058,75", 1000.0 -> "1000"
(defun vk:so (x / s)
  (setq s (rtos x 2 2))
  (if (vl-string-search "." s)
    (setq s (vl-string-right-trim "." (vl-string-right-trim "0" s))))
  (vl-string-subst "," "." s)
)

;;; Chuỗi -> số thực (nhận cả dấu phẩy thập phân); rỗng / sai -> nil
(defun vk:doc-so (s)
  (if (and s (/= (vl-string-trim " " s) ""))
    (distof (vl-string-subst "." "," (vl-string-trim " " s)) 2))
)

;;; "1, 3;5" -> (1 3 5); rỗng -> nil; sai -> 'LOI
(defun vk:doc-vt (s / ds tu c kq)
  (setq s (vl-string-trim " " (if s s "")))
  (if (= s "")
    nil
    (progn
      (foreach c (vl-string->list s)
        (if (member c '(44 59 32)) ; , ; dấu cách
          (progn (if tu (setq ds (cons tu ds))) (setq tu nil))
          (setq tu (strcat (if tu tu "") (chr c)))))
      (if tu (setq ds (cons tu ds)))
      (setq kq (mapcar '(lambda (x) (if (wcmatch x "#*") (atoi x) 0)) (reverse ds)))
      (if (vl-some '(lambda (x) (< x 1)) kq) 'LOI kq)
    )
  )
)

(defun vk:lap (n x / kq) (repeat n (setq kq (cons x kq))) kq)

;;; ---------------------------------------------------------------- tính chia đố
;;; L: dài vách; ns / nd: số cửa sổ / cửa đi; ws / wd: tâm-tâm cửa; vs / vd: danh sách ô hoặc nil (tự rải)
;;; Trả về (o tam b n): o = ((loai rong) ...) loai "K" kính / "S" cửa sổ / "D" cửa đi; tam = vị trí tâm đố;
;;; b = rộng ô kính; n = số ô kính. Lỗi -> chuỗi thông báo.
(defun vk:chia (L ns ws nd wd vs vd / S R n tong co-dinh tu-do tu-dong o b tam i k x)
  (cond
    ((or (not L) (<= L vk:do-rong)) "Nhập chiều dài vách lớn hơn 65 mm")
    ((or (< ns 0) (< nd 0)) "Số lượng cửa không được âm")
    ((and (> ns 0) (or (not ws) (<= ws 0))) "Nhập bề rộng cửa sổ")
    ((and (> nd 0) (or (not wd) (<= wd 0))) "Nhập bề rộng cửa đi")
    ((or (= vs 'LOI) (= vd 'LOI)) "Ô đặt cửa ghi dạng 1,3 (số nguyên từ 1)")
    ((and vs (/= (length vs) ns)) (strcat "Ô cửa sổ: cần đúng " (itoa ns) " số"))
    ((and vd (/= (length vd) nd)) (strcat "Ô cửa đi: cần đúng " (itoa nd) " số"))
    ((< (setq S (- L vk:do-rong) R (- S (* ns (if ws ws 0)) (* nd (if wd wd 0)))) -1e-6)
     (strcat "Vách quá ngắn: cửa chiếm " (vk:so (- S R)) " > khoảng chia " (vk:so S)))
    (T
     (setq n (if (< R 1e-6) 0 (1+ (fix (/ R vk:toi-da))))
           tong (+ n ns nd)
           b (if (> n 0) (/ R n) 0.0))
     ;; ô cố định do người dùng ghi
     (foreach x (append (mapcar '(lambda (k) (cons k "S")) vs) (mapcar '(lambda (k) (cons k "D")) vd))
       (cond
         ((> (car x) tong) (setq co-dinh 'LOI-NGOAI))
         ((and (listp co-dinh) (assoc (car x) co-dinh)) (setq co-dinh 'LOI-TRUNG))
         ((listp co-dinh) (setq co-dinh (cons x co-dinh)))))
     (cond
       ((= co-dinh 'LOI-NGOAI) (strcat "Ô đặt cửa phải từ 1 đến " (itoa tong)))
       ((= co-dinh 'LOI-TRUNG) "Hai cửa trùng một ô")
       (T
        ;; cửa không ghi ô: rải đều vào các ô còn trống (cửa đi trước, cửa sổ sau)
        (setq i 1)
        (repeat tong (if (not (assoc i co-dinh)) (setq tu-do (cons i tu-do))) (setq i (1+ i)))
        (setq tu-do (reverse tu-do)
              tu-dong (append (if (not vd) (vk:lap nd "D")) (if (not vs) (vk:lap ns "S")))
              i 0)
        (foreach x tu-dong
          (setq k (nth (fix (/ (* (+ i 0.5) (length tu-do)) (length tu-dong))) tu-do)
                co-dinh (cons (cons k x) co-dinh)
                i (1+ i)))
        (setq i 1)
        (repeat tong
          (setq x (cdr (assoc i co-dinh))
                o (cons (cond ((= x "S") (list "S" ws)) ((= x "D") (list "D" wd)) (T (list "K" b))) o)
                i (1+ i)))
        (setq o (reverse o) tam (list (/ vk:do-rong 2.0)))
        (foreach x o (setq tam (cons (+ (car tam) (cadr x)) tam)))
        (list o (reverse tam) b n))
     ))
  )
)

;;; ---------------------------------------------------------------- thư viện block
(defun vk:du-block ()
  (and (tblsearch "BLOCK" "VK_DoDung") (tblsearch "BLOCK" "VK_CuaSoMo") (tblsearch "BLOCK" "VK_CuaDi")))

;;; Ổ cứng cố định đang sẵn sàng ("C:" "D:"...), bỏ ổ mạng / ổ rời để không treo khi ổ mạng mất kết nối
(defun vk:o-dia (/ fso kq)
  (setq fso (vl-catch-all-apply 'vlax-create-object '("Scripting.FileSystemObject")))
  (if (and fso (not (vl-catch-all-error-p fso)))
    (progn
      (vlax-for d (vlax-get fso 'Drives)
        (if (and (= (vlax-get d 'DriveType) 2) (member (vlax-get d 'IsReady) '(-1 1 :vlax-true T)))
          (setq kq (cons (strcat (vlax-get d 'DriveLetter) ":") kq))))
      (vlax-release-object fso)))
  (reverse kq)
)

;;; (and / or trả về T chứ không trả về chuỗi: lấy đường dẫn bằng setq trong cond)
(defun vk:file-thu-vien (/ f)
  (cond
    ((and (getenv "ARCHIVINA_VK") (setq f (findfile (getenv "ARCHIVINA_VK")))) f)
    ((setq f (findfile vk:file-tv)) f)
    ((setq f (vl-some '(lambda (g) (findfile (strcat (vl-string-right-trim "\\/" g) vk:thu-muc-tv vk:file-tv)))
                      (append (if (getenv "ARCHIVINA_AI") (list (getenv "ARCHIVINA_AI")))
                              (if (getenv "USERPROFILE") (list (getenv "USERPROFILE")))
                              (mapcar '(lambda (o) (strcat o "\\AI")) (vk:o-dia)))))
     f)
    ((setq f (getfiled "Chọn file thư viện VK_thu_vien.dwg" "" "dwg" 0))
     (setenv "ARCHIVINA_VK" f)
     f)
  )
)

;;; Chép định nghĩa block VK_* (+ kiểu dim "dim cua") từ file thư viện: -INSERT rồi huỷ ở bước chọn điểm.
;;; Block đã có trong bản vẽ thì giữ nguyên, không định nghĩa lại.
(defun vk:nap-thu-vien (/ f ten i)
  (if (not (vk:du-block))
    (if (setq f (vk:file-thu-vien))
      (progn
        (setq ten "VK_thu_vien" i 2)
        (while (tblsearch "BLOCK" ten) (setq ten (strcat "VK_thu_vien_" (itoa i)) i (1+ i)))
        (command "_.-INSERT" (strcat ten "=" f))
        (command)
        (if (not (vk:du-block)) (princ (strcat "\nFile thư viện thiếu block VK_*: " f))))
      (princ "\nKhông tìm thấy file thư viện VK_thu_vien.dwg")))
  (vk:du-block)
)

;;; ---------------------------------------------------------------- kéo giãn block cửa
;;; Block cửa có 2 đố ở x = 0 và x = W0. Đổi bề rộng tâm-tâm thành W: phần đố trái (x <= a) giữ nguyên,
;;; đố phải (x >= W0 - a) dời W - W0, phần cánh ở giữa giãn theo tỉ lệ k; cung lớn (r > 200, cung mở cánh)
;;; nhân bán kính theo k. Toạ độ LWPOLYLINE / ARC / CIRCLE / HATCH theo OCS: pháp tuyến -Z thì x đảo dấu.
(defun vk:fx (x)
  (cond
    ((<= x vk:nua-do) x)
    ((>= x (- vk:w0 vk:nua-do)) (+ x (- vk:w vk:w0)))
    (T (+ vk:nua-do (* (- x vk:nua-do) vk:k)))
  )
)

(defun vk:keo-dxf (ed / ex gs loai out)
  (setq ex (cdr (assoc 210 ed))
        gs (if (and ex (< (caddr ex) 0)) -1.0 1.0)
        loai (cdr (assoc 0 ed)))
  (foreach p ed
    (cond
      ((member (car p) '(-1 5 330 360 102)) nil)
      ((and (member (car p) '(10 11)) (member loai '("LINE" "LWPOLYLINE" "ARC" "CIRCLE" "HATCH" "POINT")))
       (setq out (cons (cons (car p) (cons (* gs (vk:fx (* gs (cadr p)))) (cddr p))) out)))
      ((and (= (car p) 40) (member loai '("ARC" "CIRCLE")) (> (cdr p) 200.0))
       (setq out (cons (cons 40 (* vk:k (cdr p))) out)))
      (T (setq out (cons p out)))))
  (reverse out)
)

;;; Trả về tên block cửa đúng bề rộng w (tạo block kéo giãn nếu chưa có)
(defun vk:block-cua (goc w0 w / ten e loi)
  (if (equal w w0 1e-6)
    goc
    (progn
      (setq ten (strcat goc "_" (vl-string-subst "_" "," (vk:so w))))
      (if (not (tblsearch "BLOCK" ten))
        (progn
          (setq vk:w0 w0 vk:w w vk:k (/ (- w (* 2 vk:nua-do)) (- w0 (* 2 vk:nua-do))) loi 0)
          (entmake (list '(0 . "BLOCK") (cons 2 ten) '(70 . 0) '(10 0.0 0.0 0.0)))
          (setq e (cdr (assoc -2 (tblsearch "BLOCK" goc))))
          (while e
            (if (not (entmake (vk:keo-dxf (entget e)))) (setq loi (1+ loi)))
            (setq e (entnext e)))
          (entmake '((0 . "ENDBLK")))
          (if (> loi 0) (princ (strcat "\n" ten ": " (itoa loi) " đối tượng không chép được")))))
      ten))
)

;;; ---------------------------------------------------------------- dựng vách
(defun vk:ten-block (goc / ten i)
  (setq ten goc i 2)
  (while (tblsearch "BLOCK" ten) (setq ten (strcat goc " (" (itoa i) ")") i (1+ i)))
  ten
)

(defun vk:chen (ten x sy)
  (entmake (list '(0 . "INSERT") (cons 2 ten) (cons 8 vk:layer) (list 10 x 0.0 0.0)
                 '(41 . 1.0) (cons 42 sy) '(43 . 1.0) '(50 . 0.0)))
)

(defun vk:dim (p q y / e ed)
  (command "_.DIMLINEAR" "_non" (list p 0.0) "_non" (list q 0.0) "_non" (list (/ (+ p q) 2.0) y))
  (if (and (setq e (entlast)) (= "DIMENSION" (cdr (assoc 0 (setq ed (entget e))))))
    (entmod (subst (cons 8 vk:layer-dim) (assoc 8 ed) ed)))
)

;;; kq = kết quả vk:chia; L dài; lat T/nil; pt điểm đầu vách (WCS); goc radian. Trả về tên block vách hoặc nil.
(defun vk:dung (kq L lat pt goc / o tam sy dau ss e i x0 w ten-so ten-di ten ds-cu)
  (setq o (car kq) tam (cadr kq) sy (if lat -1.0 1.0))
  (if (not (tblsearch "LAYER" vk:layer))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 vk:layer) '(70 . 0) '(62 . 151) '(6 . "Continuous"))))
  (setq ten-so (if (assoc "S" o) (vk:block-cua "VK_CuaSoMo" vk:so-goc (cadr (assoc "S" o))))
        ten-di (if (assoc "D" o) (vk:block-cua "VK_CuaDi" vk:di-goc (cadr (assoc "D" o)))))
  ;; dựng tạm tại gốc toạ độ, gom vào block rồi chèn ở điểm người dùng chọn
  (setq dau (entlast) i 0)
  (foreach x o
    (setq x0 (nth i tam) w (cadr x))
    (cond
      ((= (car x) "S") (vk:chen ten-so x0 sy))
      ((= (car x) "D") (vk:chen ten-di x0 sy))
      (T
       (foreach k vk:kinh
         (entmake (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") (cons 8 vk:layer) '(100 . "AcDbPolyline")
                        '(90 . 4) '(70 . 1)
                        (list 10 (+ x0 (/ vk:do-rong 2.0)) (* sy (car k)))
                        (list 10 (- (+ x0 w) (/ vk:do-rong 2.0)) (* sy (car k)))
                        (list 10 (- (+ x0 w) (/ vk:do-rong 2.0)) (* sy (cadr k)))
                        (list 10 (+ x0 (/ vk:do-rong 2.0)) (* sy (cadr k))))))))
    (setq i (1+ i)))
  ;; đố: mọi tâm đố không thuộc block cửa
  (setq i 0)
  (foreach x0 tam
    (if (not (or (and (> i 0) (member (car (nth (1- i) o)) '("S" "D")))
                 (and (< i (length o)) (member (car (nth i o)) '("S" "D")))))
      (vk:chen "VK_DoDung" x0 sy))
    (setq i (1+ i)))
  ;; kích thước kiểm tra: chuỗi đố + tổng, kiểu "dim cua", layer Defpoints
  (setq ds-cu (getvar "DIMSTYLE"))
  (if (tblsearch "DIMSTYLE" vk:dimstyle) (command "_.-DIMSTYLE" "_R" vk:dimstyle))
  (setq x0 0.0)
  (foreach x (append tam (list L))
    (vk:dim x0 x (* sy vk:dim-chuoi))
    (setq x0 x))
  (vk:dim 0.0 L (* sy vk:dim-tong))
  (if (and (tblsearch "DIMSTYLE" ds-cu) (/= ds-cu (getvar "DIMSTYLE"))) (command "_.-DIMSTYLE" "_R" ds-cu))
  ;; gom mọi đối tượng vừa tạo
  (setq ss (ssadd) e (if dau (entnext dau) (entnext)))
  (while e (ssadd e ss) (setq e (entnext e)))
  (setq ten (vk:ten-block (strcat "VACH KINH " (vk:so L))))
  (command "_.-BLOCK" ten "_non" '(0.0 0.0 0.0) ss "")
  (if (tblsearch "BLOCK" ten)
    (progn
      (entmake (list '(0 . "INSERT") (cons 2 ten) (cons 8 vk:layer) (cons 10 pt)
                     '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) (cons 50 goc)))
      ten))
)

;;; Chuỗi tóm tắt: "1058,75 | SO 1000 | ..."
(defun vk:chuoi (o / s)
  (foreach x o
    (setq s (strcat (if s (strcat s " | ") "")
                    (cond ((= (car x) "S") "SO ") ((= (car x) "D") "DI ") (T ""))
                    (vk:so (cadr x)))))
  s
)

;;; Chạy đủ (dùng chung cho lệnh VK và chạy thử không hộp thoại). pt / goc nil -> hỏi người dùng.
(defun vk:thuc-hien (kq L lat pt goc / *error* bien cu undo ucs p2 ten)
  (defun *error* (msg)
    (mapcar 'setvar bien cu)
    (if ucs (command-s "_.UCS" "_P"))
    (if undo (command-s "_.UNDO" "_E"))
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*,*HỦY*"))
      (princ (strcat "\nLỗi VK: " msg)))
    (princ)
  )
  (setq bien '("CMDECHO" "OSMODE" "CLAYER") cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (setvar "OSMODE" 0)
  (if (setq undo (vk:undo-ok)) (command "_.UNDO" "_BE"))
  (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
  (cond
    ((not (vk:nap-thu-vien)) (princ "\nDừng: thiếu block VK_DoDung / VK_CuaSoMo / VK_CuaDi."))
    (T
     (if (not pt)
       (progn
         (setvar "OSMODE" (nth 1 cu))
         (setq pt (getpoint "\nChọn điểm đầu vách (mép ngoài): "))
         (if pt (setq p2 (getpoint pt "\nChọn điểm hướng vách <theo trục X>: ")))
         (setq goc (if p2 (angle pt p2) 0.0))
         (setvar "OSMODE" 0)))
     (if pt
       (progn
         (setq ten (vk:dung kq L lat (trans pt 1 0) goc))
         (princ (strcat "\nVK: vách " (vk:so L) " -> " (itoa (length (cadr kq))) " đố, "
                        (itoa (nth 3 kq)) " ô kính"
                        (if (> (nth 3 kq) 0) (strcat " × " (vk:so (nth 2 kq))) "")
                        "\n    [" (vk:chuoi (car kq)) "]"
                        (if ten (strcat "\n    Block: " ten) "\n    Không tạo được block vách"))))
       (princ "\nĐã huỷ."))))
  (if ucs (command "_.UCS" "_P"))
  (if undo (command "_.UNDO" "_E"))
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- hộp thoại
(defun vk:viet-dcl (f / h)
  (setq h (open f "w" "utf8"))
  (foreach s
    '("vk_hop_thoai : dialog {"
      "  label = \"VK - Chia đố vách kính\";"
      "  : boxed_column { label = \"Vách kính\";"
      "    : edit_box { key = \"dai\"; label = \"Chiều dài vách (mm, mép ngoài - mép ngoài):\"; edit_width = 10; }"
      "    : text { key = \"thongtin\"; width = 62; }"
      "  }"
      "  : row {"
      "    : boxed_column { label = \"Cửa sổ mở\";"
      "      : edit_box { key = \"ns\"; label = \"Số lượng:\"; edit_width = 6; }"
      "      : edit_box { key = \"ws\"; label = \"Rộng tâm - tâm đố (mm):\"; edit_width = 8; }"
      "      : edit_box { key = \"vs\"; label = \"Ở ô thứ (vd. 1,3; trống = tự đặt):\"; edit_width = 8; }"
      "    }"
      "    : boxed_column { label = \"Cửa đi\";"
      "      : edit_box { key = \"nd\"; label = \"Số lượng:\"; edit_width = 6; }"
      "      : edit_box { key = \"wd\"; label = \"Rộng tâm - tâm đố (mm):\"; edit_width = 8; }"
      "      : edit_box { key = \"vd\"; label = \"Ở ô thứ (vd. 2; trống = tự đặt):\"; edit_width = 8; }"
      "    }"
      "  }"
      "  : list_box { key = \"ds\"; label = \"Khoảng cách các đố (tâm - tâm, ô đếm từ trái, kể cả ô cửa):\"; height = 12; width = 62; tabs = \"6 20\"; }"
      "  : row {"
      "    : toggle { key = \"lat\"; label = \"Lật vách (mặt kẹp kính sang phía bên kia)\"; }"
      "    : button { key = \"tinh\"; label = \"Tính lại\"; fixed_width = true; }"
      "  }"
      "  : text { key = \"loi\"; width = 62; }"
      "  ok_cancel;"
      "}")
    (write-line s h))
  (close h)
)

;;; Đọc các ô nhập -> kết quả chia (danh sách) hoặc chuỗi lỗi; cập nhật bảng
(defun vk:cap-nhat (/ L ns nd kq i)
  (setq L (vk:doc-so (get_tile "dai"))
        ns (vk:doc-so (get_tile "ns")) nd (vk:doc-so (get_tile "nd")))
  (setq kq (vk:chia L (if ns (fix ns) 0) (vk:doc-so (get_tile "ws"))
                    (if nd (fix nd) 0) (vk:doc-so (get_tile "wd"))
                    (vk:doc-vt (get_tile "vs")) (vk:doc-vt (get_tile "vd"))))
  (start_list "ds")
  (if (listp kq)
    (progn
      (setq i 1)
      (foreach x (car kq)
        (add_list (strcat "Ô " (itoa i) "\t"
                          (cond ((= (car x) "S") "Cửa sổ mở") ((= (car x) "D") "Cửa đi") (T "Kính"))
                          "\t" (vk:so (cadr x))))
        (setq i (1+ i)))))
  (end_list)
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "Số đố: " (itoa (length (cadr kq))) "   |   Ô kính: " (itoa (nth 3 kq))
                                   (if (> (nth 3 kq) 0) (strcat " × " (vk:so (nth 2 kq)) " mm") "")
                                   "   |   Đố rộng 65, mỗi ô < 1200"))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "Lỗi: " kq))))
  (setq vk-kq kq vk-dai L)
)

(defun vk:luu-nho ()
  (setq *vk-nho* (mapcar '(lambda (k) (cons k (get_tile k))) '("dai" "ns" "ws" "vs" "nd" "wd" "vd" "lat"))))

(defun c:VK (/ f id kq-dlg vk-kq vk-dai lat)
  (setq f (strcat (getvar "TEMPPREFIX") "VK_hop_thoai.dcl"))
  (vk:viet-dcl f)
  (if (< (setq id (load_dialog f)) 0)
    (princ "\nKhông mở được hộp thoại VK.")
    (progn
      (if (not (new_dialog "vk_hop_thoai" id))
        (princ "\nKhông mở được hộp thoại VK.")
        (progn
          (foreach x (if *vk-nho* *vk-nho*
                       '(("dai" . "") ("ns" . "0") ("ws" . "1000") ("vs" . "")
                         ("nd" . "0") ("wd" . "1665") ("vd" . "") ("lat" . "0")))
            (set_tile (car x) (cdr x)))
          (foreach k '("dai" "ns" "ws" "vs" "nd" "wd" "vd" "tinh")
            (action_tile k "(vk:cap-nhat)"))
          (action_tile "accept"
            "(vk:cap-nhat) (if (listp vk-kq) (progn (setq lat (= \"1\" (get_tile \"lat\"))) (vk:luu-nho) (done_dialog 1)))")
          (action_tile "cancel" "(vk:luu-nho) (done_dialog 0)")
          (vk:cap-nhat)
          (setq kq-dlg (start_dialog))))
      (unload_dialog id)
      (if (= kq-dlg 1) (vk:thuc-hien vk-kq vk-dai lat nil nil))))
  (princ)
)

;;; LISPSYS khác 1 (bộ LISP cũ): file UTF-8 đọc sai dấu tiếng Việt -> nhắc đổi (thông báo không dấu để đọc được)
(if (/= 1 (getvar "LISPSYS"))
  (princ "\nCANH BAO: LISPSYS khac 1 - thong bao tieng Viet se loi font. Go LISPSYS, dat 1, khoi dong lai AutoCAD."))
(princ "\nĐã nạp VK.lsp — gõ VK để chia đố vách kính.")
(princ)
