;;; FILE SINH TỰ ĐỘNG từ vk_nguon.lsp bằng scripts\gop_vk.py — KHÔNG SỬA TAY.
;;; Chữ có dấu trong chuỗi đã đổi thành mã \U+XXXX để hiện đúng với cả LISPSYS = 0 và 1.
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
;;; Yêu cầu: AutoCAD 2021+. Chữ có dấu trong chuỗi đã đổi sang \U+XXXX nên chạy được cả LISPSYS = 0 và 1. Không xoá, không sửa đối tượng có sẵn trong bản vẽ.

(vl-load-com)

;;; ---------------------------------------------------------------- thông số
;;;   vk:do-rong: bề rộng đố dùng để chia; vk:toi-da: khoảng tâm-tâm phải nhỏ hơn
;;;   vk:nua-do: nửa bề rộng đố trong block (65,74 / 2), vùng không kéo giãn khi đổi rộng cửa
;;;   vk:so-goc / vk:di-goc: tâm-tâm 2 đố của block VK_CuaSoMo / VK_CuaDi
;;;   vk:kinh: 2 tấm kính ô cố định (y so với trục vách), theo kính lá cửa sổ
;;;   vk:dim-chuoi / vk:dim-tong: đường dim chuỗi đố / dim tổng cách trục vách
(setq vk:do-rong 65.0
      vk:toi-da 1200.0
      vk:nua-do 32.87
      vk:so-goc 1000.0
      vk:di-goc 1665.0
      vk:kinh '((42.04 48.04) (56.86 62.86))
      vk:dim-chuoi 165.0
      vk:dim-tong 260.0
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
        ;; 44 = dấu phẩy, 59 = chấm phẩy, 32 = dấu cách
        (if (member c '(44 59 32))
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
    ((or (not L) (<= L vk:do-rong)) "Nh\\U+1EADp chi\\U+1EC1u d\\U+00E0i v\\U+00E1ch l\\U+1EDBn h\\U+01A1n 65 mm")
    ((or (< ns 0) (< nd 0)) "S\\U+1ED1 l\\U+01B0\\U+1EE3ng c\\U+1EEDa kh\\U+00F4ng \\U+0111\\U+01B0\\U+1EE3c \\U+00E2m")
    ((and (> ns 0) (or (not ws) (<= ws 0))) "Nh\\U+1EADp b\\U+1EC1 r\\U+1ED9ng c\\U+1EEDa s\\U+1ED5")
    ((and (> nd 0) (or (not wd) (<= wd 0))) "Nh\\U+1EADp b\\U+1EC1 r\\U+1ED9ng c\\U+1EEDa \\U+0111i")
    ((or (= vs 'LOI) (= vd 'LOI)) "\\U+00D4 \\U+0111\\U+1EB7t c\\U+1EEDa ghi d\\U+1EA1ng 1,3 (s\\U+1ED1 nguy\\U+00EAn t\\U+1EEB 1)")
    ((and vs (/= (length vs) ns)) (strcat "\\U+00D4 c\\U+1EEDa s\\U+1ED5: c\\U+1EA7n \\U+0111\\U+00FAng " (itoa ns) " s\\U+1ED1"))
    ((and vd (/= (length vd) nd)) (strcat "\\U+00D4 c\\U+1EEDa \\U+0111i: c\\U+1EA7n \\U+0111\\U+00FAng " (itoa nd) " s\\U+1ED1"))
    ((< (setq S (- L vk:do-rong) R (- S (* ns (if ws ws 0)) (* nd (if wd wd 0)))) -1e-6)
     (strcat "V\\U+00E1ch qu\\U+00E1 ng\\U+1EAFn: c\\U+1EEDa chi\\U+1EBFm " (vk:so (- S R)) " > kho\\U+1EA3ng chia " (vk:so S)))
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
       ((= co-dinh 'LOI-NGOAI) (strcat "\\U+00D4 \\U+0111\\U+1EB7t c\\U+1EEDa ph\\U+1EA3i t\\U+1EEB 1 \\U+0111\\U+1EBFn " (itoa tong)))
       ((= co-dinh 'LOI-TRUNG) "Hai c\\U+1EEDa tr\\U+00F9ng m\\U+1ED9t \\U+00F4")
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
    ((setq f (getfiled "Ch\\U+1ECDn file th\\U+01B0 vi\\U+1EC7n VK_thu_vien.dwg" "" "dwg" 0))
     (setenv "ARCHIVINA_VK" f)
     f)
  )
)

;;; Chép định nghĩa block VK_* (+ kiểu dim "dim cua") từ file thư viện: -INSERT tại 0,0 rồi bỏ ngay bản chèn
;;; tạm vừa tạo (chỉ cần định nghĩa block). Không huỷ lệnh giữa chừng: Esc trong script dừng cả script.
;;; Block đã có trong bản vẽ thì giữ nguyên, không định nghĩa lại.
(defun vk:nap-thu-vien (/ f ten i e)
  (if (not (vk:du-block))
    (if (setq f (vk:file-thu-vien))
      (progn
        (setq ten "VK_thu_vien" i 2)
        (while (tblsearch "BLOCK" ten) (setq ten (strcat "VK_thu_vien_" (itoa i)) i (1+ i)))
        (setq e (entlast))
        (command "_.-INSERT" (strcat ten "=" f) "_non" '(0.0 0.0 0.0) 1.0 1.0 0.0)
        (if (and (not (equal e (entlast))) (= ten (cdr (assoc 2 (entget (entlast))))))
          (entdel (entlast)))
        (if (not (vk:du-block)) (princ (strcat "\nFile th\\U+01B0 vi\\U+1EC7n thi\\U+1EBFu block VK_*: " f))))
      (princ "\nKh\\U+00F4ng t\\U+00ECm th\\U+1EA5y file th\\U+01B0 vi\\U+1EC7n VK_thu_vien.dwg")))
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
          (if (> loi 0) (princ (strcat "\n" ten ": " (itoa loi) " \\U+0111\\U+1ED1i t\\U+01B0\\U+1EE3ng kh\\U+00F4ng ch\\U+00E9p \\U+0111\\U+01B0\\U+1EE3c")))))
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
(defun vk:dung (kq L lat pt goc / o tam sy dau ss e ed i x0 w ten-so ten-di ten ds-cu)
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
  (setq e (entlast))
  (command "_.-BLOCK" ten "_non" '(0.0 0.0 0.0) ss "")
  (if (tblsearch "BLOCK" ten)
    (progn
      ;; AutoCAD 2027 -BLOCK đổi luôn đối tượng thành 1 bản chèn tại 0,0 (layer hiện hành); bản cũ thì xoá
      ;; đối tượng -> dời bản chèn có sẵn tới điểm chọn, không có thì chèn mới
      (setq ed (entget (entlast)))
      (if (and (not (equal e (entlast))) (= "INSERT" (cdr (assoc 0 ed))) (= ten (cdr (assoc 2 ed))))
        (entmod (subst (cons 50 goc) (assoc 50 ed)
                       (subst (cons 10 pt) (assoc 10 ed) (subst (cons 8 vk:layer) (assoc 8 ed) ed))))
        (entmake (list '(0 . "INSERT") (cons 2 ten) (cons 8 vk:layer) (cons 10 pt)
                       '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) (cons 50 goc))))
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
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*"))
      (princ (strcat "\nL\\U+1ED7i VK: " msg)))
    (princ)
  )
  (setq bien '("CMDECHO" "OSMODE" "CLAYER") cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (setvar "OSMODE" 0)
  (if (setq undo (vk:undo-ok)) (command "_.UNDO" "_BE"))
  (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
  (cond
    ((not (vk:nap-thu-vien)) (princ "\nD\\U+1EEBng: thi\\U+1EBFu block VK_DoDung / VK_CuaSoMo / VK_CuaDi."))
    (T
     (if (not pt)
       (progn
         (setvar "OSMODE" (nth 1 cu))
         (setq pt (getpoint "\nCh\\U+1ECDn \\U+0111i\\U+1EC3m \\U+0111\\U+1EA7u v\\U+00E1ch (m\\U+00E9p ngo\\U+00E0i): "))
         (if pt (setq p2 (getpoint pt "\nCh\\U+1ECDn \\U+0111i\\U+1EC3m h\\U+01B0\\U+1EDBng v\\U+00E1ch <theo tr\\U+1EE5c X>: ")))
         (setq goc (if p2 (angle pt p2) 0.0))
         (setvar "OSMODE" 0)))
     (if pt
       (progn
         (setq ten (vk:dung kq L lat (trans pt 1 0) goc))
         (princ (strcat "\nVK: v\\U+00E1ch " (vk:so L) " -> " (itoa (length (cadr kq))) " \\U+0111\\U+1ED1, "
                        (itoa (nth 3 kq)) " \\U+00F4 k\\U+00EDnh"
                        (if (> (nth 3 kq) 0) (strcat " \\U+00D7 " (vk:so (nth 2 kq))) "")
                        "\n    [" (vk:chuoi (car kq)) "]"
                        (if ten (strcat "\n    Block: " ten) "\n    Kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c block v\\U+00E1ch"))))
       (princ "\n\\U+0110\\U+00E3 hu\\U+1EF7."))))
  (if ucs (command "_.UCS" "_P"))
  (if undo (command "_.UNDO" "_E"))
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- hộp thoại
(defun vk:viet-dcl (f / h)
  ;; VK.lsp sinh từ file này đã đổi chữ có dấu thành mã \U+XXXX (chỉ còn ký tự ASCII) -> ghi DCL thường,
  ;; hộp thoại hiện đúng dấu với cả LISPSYS = 0 và 1
  (setq h (open f "w"))
  (foreach s
    '("vk_hop_thoai : dialog {"
      "  label = \"VK - Chia \\U+0111\\U+1ED1 v\\U+00E1ch k\\U+00EDnh\";"
      "  : boxed_column { label = \"V\\U+00E1ch k\\U+00EDnh\";"
      "    : edit_box { key = \"dai\"; label = \"Chi\\U+1EC1u d\\U+00E0i v\\U+00E1ch (mm, m\\U+00E9p ngo\\U+00E0i - m\\U+00E9p ngo\\U+00E0i):\"; edit_width = 10; }"
      "    : text { key = \"thongtin\"; width = 62; }"
      "  }"
      "  : row {"
      "    : boxed_column { label = \"C\\U+1EEDa s\\U+1ED5 m\\U+1EDF\";"
      "      : edit_box { key = \"ns\"; label = \"S\\U+1ED1 l\\U+01B0\\U+1EE3ng:\"; edit_width = 6; }"
      "      : edit_box { key = \"ws\"; label = \"R\\U+1ED9ng t\\U+00E2m - t\\U+00E2m \\U+0111\\U+1ED1 (mm):\"; edit_width = 8; }"
      "      : edit_box { key = \"vs\"; label = \"\\U+1EDE \\U+00F4 th\\U+1EE9 (vd. 1,3; tr\\U+1ED1ng = t\\U+1EF1 \\U+0111\\U+1EB7t):\"; edit_width = 8; }"
      "    }"
      "    : boxed_column { label = \"C\\U+1EEDa \\U+0111i\";"
      "      : edit_box { key = \"nd\"; label = \"S\\U+1ED1 l\\U+01B0\\U+1EE3ng:\"; edit_width = 6; }"
      "      : edit_box { key = \"wd\"; label = \"R\\U+1ED9ng t\\U+00E2m - t\\U+00E2m \\U+0111\\U+1ED1 (mm):\"; edit_width = 8; }"
      "      : edit_box { key = \"vd\"; label = \"\\U+1EDE \\U+00F4 th\\U+1EE9 (vd. 2; tr\\U+1ED1ng = t\\U+1EF1 \\U+0111\\U+1EB7t):\"; edit_width = 8; }"
      "    }"
      "  }"
      "  : list_box { key = \"ds\"; label = \"Kho\\U+1EA3ng c\\U+00E1ch c\\U+00E1c \\U+0111\\U+1ED1 (t\\U+00E2m - t\\U+00E2m, \\U+00F4 \\U+0111\\U+1EBFm t\\U+1EEB tr\\U+00E1i, k\\U+1EC3 c\\U+1EA3 \\U+00F4 c\\U+1EEDa):\"; height = 12; width = 62; tabs = \"6 20\"; }"
      "  : row {"
      "    : toggle { key = \"lat\"; label = \"L\\U+1EADt v\\U+00E1ch (m\\U+1EB7t k\\U+1EB9p k\\U+00EDnh sang ph\\U+00EDa b\\U+00EAn kia)\"; }"
      "    : button { key = \"tinh\"; label = \"T\\U+00EDnh l\\U+1EA1i\"; fixed_width = true; }"
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
        (add_list (strcat "\\U+00D4 " (itoa i) "\t"
                          (cond ((= (car x) "S") "C\\U+1EEDa s\\U+1ED5 m\\U+1EDF") ((= (car x) "D") "C\\U+1EEDa \\U+0111i") (T "K\\U+00EDnh"))
                          "\t" (vk:so (cadr x))))
        (setq i (1+ i)))))
  (end_list)
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "S\\U+1ED1 \\U+0111\\U+1ED1: " (itoa (length (cadr kq))) "   |   \\U+00D4 k\\U+00EDnh: " (itoa (nth 3 kq))
                                   (if (> (nth 3 kq) 0) (strcat " \\U+00D7 " (vk:so (nth 2 kq)) " mm") "")
                                   "   |   \\U+0110\\U+1ED1 r\\U+1ED9ng 65, m\\U+1ED7i \\U+00F4 < 1200"))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "L\\U+1ED7i: " kq))))
  (setq vk-kq kq vk-dai L)
)

(defun vk:luu-nho ()
  (setq *vk-nho* (mapcar '(lambda (k) (cons k (get_tile k))) '("dai" "ns" "ws" "vs" "nd" "wd" "vd" "lat"))))

(defun c:VK (/ f id kq-dlg vk-kq vk-dai lat)
  (setq f (strcat (getvar "TEMPPREFIX") "VK_hop_thoai.dcl"))
  (vk:viet-dcl f)
  (if (< (setq id (load_dialog f)) 0)
    (princ "\nKh\\U+00F4ng m\\U+1EDF \\U+0111\\U+01B0\\U+1EE3c h\\U+1ED9p tho\\U+1EA1i VK.")
    (progn
      (if (not (new_dialog "vk_hop_thoai" id))
        (princ "\nKh\\U+00F4ng m\\U+1EDF \\U+0111\\U+01B0\\U+1EE3c h\\U+1ED9p tho\\U+1EA1i VK.")
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

(princ "\n\\U+0110\\U+00E3 n\\U+1EA1p VK.lsp \\U+2014 g\\U+00F5 VK \\U+0111\\U+1EC3 chia \\U+0111\\U+1ED1 v\\U+00E1ch k\\U+00EDnh.")
(princ)
