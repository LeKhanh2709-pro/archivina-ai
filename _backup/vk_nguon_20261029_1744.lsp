;;; vk_nguon.lsp — NGUỒN của VK.lsp: sửa file này rồi chạy scripts\gop_vk.py để sinh VK.lsp (không sửa tay VK.lsp)
;;; VK.lsp — Chia đố thanh đứng và dựng vách kính mặt bằng (Archivina)
;;; Lệnh: VK
;;;   Bảng hỏi: chiều dài vách, cửa sổ mở / cửa đi (số lượng, bề rộng tâm-tâm, ô đặt cửa).
;;;   Bảng tự cập nhật số đố và khoảng cách các đố; OK -> chọn điểm đầu vách (mép ngoài) và hướng vách.
;;;   Bảng hiện trước; chưa có chiều dài thì bấm "Pick 2 điểm <": chọn điểm đầu + điểm cuối vách trên mặt bằng,
;;;   bảng mở lại với chiều dài đã điền -> chọn cửa sổ / cửa đi -> OK dựng vách đúng 2 điểm đó (người dùng chốt
;;;   29/10/2026). Sửa tay chiều dài sau khi pick thì OK hỏi điểm như cũ.
;;; Quy tắc chia (người dùng chốt 28/10/2026):
;;;   - Đố rộng 65: tâm đố đầu / cuối cách mép ngoài 32,5; khoảng chia S = L - 65.
;;;   - Trừ bề rộng tâm-tâm các cửa, phần còn lại chia ĐỀU thành N ô kính, N nhỏ nhất để mỗi ô < 1200.
;;;     Không làm tròn khoảng chia.
;;;   - Cửa đặt vào ô thứ k (đếm từ trái, kể cả ô cửa); bỏ trống thì tự rải đều (1 cửa -> ô giữa).
;;; Kết quả: block "VACH KINH <dài>" trên layer A-Window gồm block đố VK_DoDung, cửa VK_CuaSoMo / VK_CuaDi
;;;   (bề rộng khác mặc định -> block kéo giãn VK_CuaSoMo_<rộng> / VK_CuaDi_<rộng>), kính ô cố định, và
;;;   2 hàng kích thước kiểm tra (chuỗi đố + tổng) kiểu "dim cua", layer Defpoints, nằm trong block.
;;; Block VK_*, kiểu dim "dim cua" nhúng sẵn trong file (cuối file): chép 1 file VK.lsp sang máy khác là dùng được.
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
      ;; dim sau khi MDVK chuyển xuống dưới mặt bằng (giống dim mặt đứng của VKMD.lsp)
      vk:layer-dim-mb "A-Dimension"
      vk:dim-ho 80.0
      vk:dim-duoi-chuoi 200.0
      vk:dim-duoi-tong 335.0
      vk:dimstyle "dim cua")

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

;;; "1, 3;5" -> (1 3 5); rỗng hoặc chỉ toàn 0 -> nil (tự đặt); số 0 bị bỏ qua (người dùng nhập 0 = tự đặt,
;;; báo 28/10/2026); chữ / số âm -> 'LOI
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
      (setq kq (mapcar '(lambda (x) (if (wcmatch x "#,##,###") (atoi x) -1)) (reverse ds)))
      (cond
        ((vl-some '(lambda (x) (< x 0)) kq) 'LOI)
        (T (vl-remove 0 kq)))
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
    ((or (= vs 'LOI) (= vd 'LOI)) "Ô đặt cửa ghi dạng 1,3 (số nguyên; 0 hoặc trống = tự đặt)")
    ;; ghi ít ô hơn số cửa: các cửa còn lại tự đặt
    ((> (length vs) ns) (strcat "Ô cửa sổ: ghi " (itoa (length vs)) " ô nhưng chỉ có " (itoa ns) " cửa sổ"))
    ((> (length vd) nd) (strcat "Ô cửa đi: ghi " (itoa (length vd)) " ô nhưng chỉ có " (itoa nd) " cửa đi"))
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
              tu-dong (append (vk:lap (- nd (length vd)) "D") (vk:lap (- ns (length vs)) "S"))
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

;;; ---------------------------------------------------------------- block nhúng sẵn
;;; Định nghĩa block VK_*, kiểu nét, layer A-Window, kiểu chữ + kiểu dim "dim cua" NHÚNG trong file này
;;; (biến vk:dl-* ở cuối file, sinh bằng scripts\nhung_block.ps1) -> chép VK.lsp sang máy khác là chạy được,
;;; không cần file thư viện ngoài (người dùng chốt 28/10/2026).
(defun vk:du-block ()
  (and (tblsearch "BLOCK" "VK_DoDung") (tblsearch "BLOCK" "VK_CuaSoMo") (tblsearch "BLOCK" "VK_CuaDi")))

;;; HATCH trước khi entmake (một đối tượng lỗi làm hỏng cả định nghĩa block đang tạo):
;;;   - (97 . n): số đối tượng biên liên kết; tham chiếu (330) không mang theo được -> đặt 0
;;;   - góc cung biên (50 / 51) đưa về [0, 2π), giữ nguyên hiệu số -> cùng hình (entget có thể trả góc > 2π)
(defun vk:sua-hatch (ed / a out)
  (foreach p ed
    (cond
      ((= (car p) 97) (setq out (cons '(97 . 0) out)))
      ((= (car p) 50)
       (setq a (cdr p))
       (while (>= a (* 2 pi)) (setq a (- a (* 2 pi))))
       (while (< a 0.0) (setq a (+ a (* 2 pi))))
       (setq out (cons (cons 50 a) out) a (- a (cdr p))))
      ((and (= (car p) 51) a) (setq out (cons (cons 51 (+ (cdr p) a)) out) a nil))
      (T (setq out (cons p out)))))
  (reverse out)
)

;;; Tạo những gì bản vẽ còn thiếu; cái đã có (cùng tên) giữ nguyên, không định nghĩa lại. Trả về T nếu đủ block.
(defun vk:nap-thu-vien (/ ten loi ds-cu blk)
  ;; kiểu nét dùng trong block (CENTER, HIDDEN...)
  (foreach ed vk:dl-ltype
    (if (not (tblsearch "LTYPE" (cdr (assoc 2 ed)))) (entmake ed)))
  (if (not (tblsearch "LAYER" vk:layer)) (entmake vk:dl-layer))
  ;; block VK_*
  (foreach blk vk:dl-block
    (setq ten (car blk) loi 0)
    (if (not (tblsearch "BLOCK" ten))
      (progn
        (entmake (list '(0 . "BLOCK") (cons 2 ten) '(70 . 0) '(10 0.0 0.0 0.0)))
        (foreach ed (cdr blk)
          (if (= "HATCH" (cdr (assoc 0 ed))) (setq ed (vk:sua-hatch ed)))
          (if (not (entmake ed)) (setq loi (1+ loi))))
        (entmake '((0 . "ENDBLK")))
        (if (> loi 0) (princ (strcat "\n" ten ": " (itoa loi) " đối tượng không tạo được"))))))
  ;; kiểu chữ + kiểu dim "dim cua": đặt các biến DIM* theo dữ liệu, lưu kiểu, rồi trả lại kiểu đang dùng
  (if (not (tblsearch "STYLE" (cdr (assoc 2 vk:dl-style)))) (entmake vk:dl-style))
  (if (not (tblsearch "DIMSTYLE" vk:dimstyle))
    (progn
      (setq ds-cu (getvar "DIMSTYLE"))
      (foreach p vk:dl-dimvar (vl-catch-all-apply 'setvar (list (car p) (cdr p))))
      (command "_.-DIMSTYLE" "_S" vk:dimstyle)
      (if (tblsearch "DIMSTYLE" ds-cu) (command "_.-DIMSTYLE" "_R" ds-cu))))
  (if (not (vk:du-block)) (princ "\nKhông tạo được block VK_DoDung / VK_CuaSoMo / VK_CuaDi."))
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

;;; Nội dung vách dựng bằng ActiveX (vla-*) thẳng vào một block (định nghĩa mới, hoặc bản *U của block động khi
;;; kéo grip): không gọi lệnh qua dòng lệnh nên chạy được cả trong reactor.
(defun vk:doc () (vla-get-ActiveDocument (vlax-get-acad-object)))

(defun vk:mang (ds)
  (vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbDouble (cons 0 (1- (length ds)))) ds)))

(defun vk:chen (blk ten x sy / e)
  (setq e (vla-InsertBlock blk (vlax-3d-point x 0.0 0.0) ten 1.0 sy 1.0 0.0))
  (vla-put-Layer e vk:layer)
)

;;; Dim ngang p..q, đường gióng bắt đầu ở cao độ yg, đường dim ở y, layer lop
(defun vk:dim (blk p q yg y lop / e)
  (setq e (vla-AddDimRotated blk (vlax-3d-point p yg 0.0) (vlax-3d-point q yg 0.0)
                             (vlax-3d-point (/ (+ p q) 2.0) y 0.0) 0.0))
  (if (tblsearch "DIMSTYLE" vk:dimstyle) (vla-put-StyleName e vk:dimstyle))
  (vla-put-Layer e lop)
)

;;; Mép ngoài cùng của nội dung block (bỏ qua dim) về phía ben (+1: y lớn nhất, -1: y nhỏ nhất), tính cả trục vách
(defun vk:mep (blk ben / y mn mx)
  (setq y 0.0)
  (vlax-for x blk
    (if (and (not (wcmatch (vla-get-ObjectName x) "*Dimension"))
             (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-GetBoundingBox (list x 'mn 'mx)))))
      (setq y (if (> ben 0)
                (max y (cadr (vlax-safearray->list mx)))
                (min y (cadr (vlax-safearray->list mn)))))))
  y
)

;;; Vẽ vách (kết quả vk:chia kq, dài L, lật lat) vào block blk, mép ngoài đầu vách tại x = dx (0 khi tạo mới;
;;; khác 0 khi đã kéo grip đầu vách: bản *U giữ điểm chèn cũ, đầu vách dời đi dx).
;;; ben: 0 = dim kiểm tra sát vách trên Defpoints (mặc định khi tạo); +1 / -1 = MDVK đã chuyển dim xuống dưới mặt
;;; bằng (phía ben trong toạ độ block), layer A-Dimension, cách đối tượng như dim mặt đứng (gióng 80, chuỗi 200,
;;; tổng 335) - kéo grip vẽ lại vẫn giữ kiểu đó (người dùng yêu cầu 29/10/2026).
(defun vk:ve-vao (blk kq L lat dx ben / o tam sy i x0 w ten-so ten-di e m yg y1 y2 lop)
  (setq o (car kq) tam (mapcar '(lambda (x) (+ x dx)) (cadr kq)) sy (if lat -1.0 1.0))
  (setq ten-so (if (assoc "S" o) (vk:block-cua "VK_CuaSoMo" vk:so-goc (cadr (assoc "S" o))))
        ten-di (if (assoc "D" o) (vk:block-cua "VK_CuaDi" vk:di-goc (cadr (assoc "D" o)))))
  (setq i 0)
  (foreach x o
    (setq x0 (nth i tam) w (cadr x))
    (cond
      ((= (car x) "S") (vk:chen blk ten-so x0 sy))
      ((= (car x) "D") (vk:chen blk ten-di x0 sy))
      (T
       (foreach k vk:kinh
         (setq e (vla-AddLightWeightPolyline blk
                   (vk:mang (list (+ x0 (/ vk:do-rong 2.0)) (* sy (car k))
                                  (- (+ x0 w) (/ vk:do-rong 2.0)) (* sy (car k))
                                  (- (+ x0 w) (/ vk:do-rong 2.0)) (* sy (cadr k))
                                  (+ x0 (/ vk:do-rong 2.0)) (* sy (cadr k))))))
         (vla-put-Closed e :vlax-true)
         (vla-put-Layer e vk:layer))))
    (setq i (1+ i)))
  ;; đố: mọi tâm đố không thuộc block cửa
  (setq i 0)
  (foreach x0 tam
    (if (not (or (and (> i 0) (member (car (nth (1- i) o)) '("S" "D")))
                 (and (< i (length o)) (member (car (nth i o)) '("S" "D")))))
      (vk:chen blk "VK_DoDung" x0 sy))
    (setq i (1+ i)))
  ;; kích thước kiểm tra: chuỗi đố + tổng, kiểu "dim cua"
  (if (and ben (/= ben 0))
    (progn
      (setq m (vk:mep blk ben) yg (+ m (* ben vk:dim-ho)) y1 (+ m (* ben vk:dim-duoi-chuoi))
            y2 (+ m (* ben vk:dim-duoi-tong)) lop vk:layer-dim-mb)
      (if (not (tblsearch "LAYER" lop))
        (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                       (cons 2 lop) '(70 . 0) '(62 . 192) '(6 . "Continuous")))))
    (setq yg 0.0 y1 (* sy vk:dim-chuoi) y2 (* sy vk:dim-tong) lop vk:layer-dim))
  (setq x0 dx)
  (foreach x (append tam (list (+ dx L)))
    (vk:dim blk x0 x yg y1 lop)
    (setq x0 x))
  (vk:dim blk dx (+ dx L) yg y2 lop)
)

;;; Vị trí mép ngoài đầu vách trong block blk = tâm đố / cửa đầu tiên (x nhỏ nhất của bản chèn VK_*) - 32,5
(defun vk:dau-vach (blk / x)
  (vlax-for e blk
    (if (and (= "AcDbBlockReference" (vla-get-ObjectName e)) (wcmatch (strcase (vla-get-Name e)) "VK_*"))
      (if (or (not x) (< (car (vlax-get e 'InsertionPoint)) x)) (setq x (car (vlax-get e 'InsertionPoint))))))
  (if x (- x (/ vk:do-rong 2.0)) 0.0)
)

;;; ---------------------------------------------------------------- block động (kéo grip chiều dài)
;;; Người dùng chốt 29/10/2026: block vách có grip ở điểm cuối; kéo grip -> đố chia lại đúng quy tắc (ô < 1200,
;;; chia đều), cửa sổ / cửa đi giữ đúng ô thứ k (ô không còn thì tự đặt lại).
;;;   - Tham số Linear "ChieuDai" (0,0)-(L,0), CHỈ 1 grip ở điểm cuối, điểm đầu khoá (người dùng chốt 29/10/2026
;;;     sau khi thử bản kéo 2 đầu), 1 Stretch action quanh đầu cuối: tạo bằng -BEDIT / BPARAMETER / BACTION (LISP
;;;     không có hàm tạo tham số động). Không có VK.lsp thì kéo grip chỉ giãn ô cuối. Vách tạo bằng bản 2 grip
;;;     vẫn chia lại đúng khi kéo đầu: đầu vách trong *U dời dx (vk:dau-vach đo theo đố đầu) -> vẽ lại từ dx;
;;;     MDVK cũng trừ dx này.
;;;   - Thông số cửa lưu ở XData "ARCHIVINA_VK" của bản chèn. Reactor ghi lại bản chèn vách bị sửa; hết lệnh
;;;     (kéo grip, Properties...) thì so ChieuDai với chiều dài đã lưu, khác thì chia lại và vẽ lại nội dung
;;;     bản *U của bản chèn đó (block gốc giữ nguyên). Cửa không còn vừa -> trả ChieuDai về chiều dài cũ.
(setq vk:app "ARCHIVINA_VK" vk:tham-so "ChieuDai")

;;; Gắn tham số + Stretch action vào định nghĩa block ten (đang có nội dung vách dài L). Trả về T nếu xong.
(defun vk:lam-dong (ten L lat wmax / sy off big)
  (setq sy (if lat -1.0 1.0)
        ;; nhãn tham số phía không có dim, ra ngoài cung mở cánh cửa (bán kính tới bề rộng cửa)
        off (* -1.0 sy (+ 900.0 wmax))
        big (+ 1500.0 wmax))
  (cond
    ((/= 0 (getvar "BLOCKEDITLOCK")) nil)
    (T
     (command "_.-BEDIT" ten)
     (if (/= 1 (getvar "BLOCKEDITOR"))
       nil
       (progn
         (command "_.ZOOM" "_E")
         ;; 1 grip ở điểm cuối, điểm đầu khoá (người dùng chốt 29/10/2026, sau khi thử bản kéo 2 đầu)
         (command "_.BPARAMETER" "_L" "_L" vk:tham-so "_non" '(0.0 0.0) "_non" (list L 0.0)
                  "_non" (list (/ L 2.0) off) "1")
         (if (> (logand 1 (getvar "CMDACTIVE")) 0) (command))
         (command "_.ZOOM" "_E")
         ;; chọn tham số bằng một điểm trên đường kích thước của nó, LỆCH khỏi chữ nhãn ở giữa (bấm đúng
         ;; tâm nhãn thì không chọn được, thử 29/10/2026); khung kéo giãn + đối tượng kéo: quanh đầu cuối vách
         (command "_.BACTION" "_non" (list (* L 0.12) off) "_T" "_S"
                  "_non" (list (- L 80.0) (- big)) "_non" (list (+ L 300.0) big)
                  "_C" "_non" (list (- L 80.0) (- big)) "_non" (list (+ L 300.0) big) "")
         (if (> (logand 1 (getvar "CMDACTIVE")) 0) (command))
         (command "_.BSAVE")
         (if (> (logand 1 (getvar "CMDACTIVE")) 0) (command))
         (command "_.BCLOSE")
         (if (> (logand 1 (getvar "CMDACTIVE")) 0) (command))
         (and (= 0 (getvar "BLOCKEDITOR")) (vk:du-grip ten))))))
)

;;; Đếm nút trong đồ thị block động (BLOCK_RECORD -> từ điển mở rộng -> ACAD_ENHANCEDBLOCK):
;;; trả về (số Stretch action . số grip). Thiếu = BACTION / BPARAMETER không chọn được (bản đầu bấm đúng tâm
;;; chữ nhãn -> vách có grip đầu nhưng không có Stretch đầu, kéo đầu thì vách dài ra phía cuối; 29/10/2026).
(defun vk:dem-dong (ten / br xd g so-a so-g)
  (setq so-a 0 so-g 0)
  (if (and (setq br (tblobjname "BLOCK" ten)) (setq br (cdr (assoc 330 (entget br))))
           (setq xd (cdr (assoc 360 (entget br)))) (setq g (dictsearch xd "ACAD_ENHANCEDBLOCK")))
    (foreach p g
      (if (and (= 360 (car p)) (= 'ENAME (type (cdr p))))
        (cond
          ((= "BLOCKSTRETCHACTION" (cdr (assoc 0 (entget (cdr p))))) (setq so-a (1+ so-a)))
          ((= "BLOCKLINEARGRIP" (cdr (assoc 0 (entget (cdr p))))) (setq so-g (1+ so-g)))))))
  (cons so-a so-g)
)

(defun vk:du-grip (ten / d)
  (setq d (vk:dem-dong ten))
  (if (and (= 1 (car d)) (= 1 (cdr d)))
    T
    (progn
      (princ (strcat "\nVK: block " ten " có " (itoa (cdr d)) "/1 grip, " (itoa (car d))
                     "/1 Stretch action - kéo grip có thể không đúng, báo lại để sửa."))
      nil))
)

(defun vk:prop (o / p)
  (if (= :vlax-true (vla-get-IsDynamicBlock o))
    (vl-some '(lambda (x) (if (= (strcase (vla-get-PropertyName x)) (strcase vk:tham-so)) x))
             (vlax-invoke o 'GetDynamicBlockProperties)))
)

;;; XData bản chèn: (L lat ns ws "ô sổ" nd wd "ô đi" ben), ô = vị trí thực tế sau khi chia (vd. "3" / "2,5");
;;; ben = phía đặt dim (0 sát vách Defpoints; ±1 dưới mặt bằng A-Dimension, do MDVK ghi). Vách cũ chỉ có 8 phần tử.
(defun vk:o-cua (o loai / i s)
  (setq i 1)
  (foreach x o
    (if (= (car x) loai) (setq s (strcat (if s (strcat s ",") "") (itoa i))))
    (setq i (1+ i)))
  (if s s "")
)

(defun vk:dat-xd (obj kq L lat ben / o ds ma gt)
  (if (not (tblsearch "APPID" vk:app)) (regapp vk:app))
  (setq o (car kq)
        ds (list (cons 1001 vk:app) (cons 1040 L) (cons 1070 (if lat 1 0))
                 (cons 1070 (length (vl-remove-if-not '(lambda (x) (= (car x) "S")) o)))
                 (cons 1040 (if (assoc "S" o) (cadr (assoc "S" o)) 0.0)) (cons 1000 (vk:o-cua o "S"))
                 (cons 1070 (length (vl-remove-if-not '(lambda (x) (= (car x) "D")) o)))
                 (cons 1040 (if (assoc "D" o) (cadr (assoc "D" o)) 0.0)) (cons 1000 (vk:o-cua o "D"))
                 (cons 1070 (if ben (fix ben) 0))))
  (setq ma (vlax-make-safearray vlax-vbInteger (cons 0 (1- (length ds))))
        gt (vlax-make-safearray vlax-vbVariant (cons 0 (1- (length ds)))))
  (vlax-safearray-fill ma (mapcar 'car ds))
  (vlax-safearray-fill gt (mapcar '(lambda (x) (vlax-make-variant (cdr x))) ds))
  (vla-SetXData obj ma gt)
)

;;; -> (L lat ns ws vs nd wd vd ben) hoặc nil
(defun vk:doc-xd (e / xd)
  (if (setq xd (cdr (assoc vk:app (cdr (assoc -3 (entget e (list vk:app)))))))
    (if (>= (length xd) 8)
      (list (cdr (nth 0 xd)) (= 1 (cdr (nth 1 xd))) (cdr (nth 2 xd)) (cdr (nth 3 xd))
            (vk:doc-vt (cdr (nth 4 xd))) (cdr (nth 5 xd)) (cdr (nth 6 xd)) (vk:doc-vt (cdr (nth 7 xd)))
            (if (nth 8 xd) (cdr (nth 8 xd)) 0))))
)

;;; Chia lại vách e theo ChieuDai hiện tại. Trả về chuỗi báo hoặc nil (không cần làm gì).
(defun vk:keo-lai (e / obj p L1 d kq ten blk ds ds2 dx)
  (setq obj (vlax-ename->vla-object e) p (vk:prop obj) d (vk:doc-xd e))
  (if (and p d (setq L1 (vlax-variant-value (vla-get-Value p))) (not (equal L1 (car d) 0.005)))
    (progn
      (setq kq (vk:chia L1 (nth 2 d) (nth 3 d) (nth 5 d) (nth 6 d) (nth 4 d) (nth 7 d)))
      ;; ô cửa cũ không còn hợp (vách ngắn đi) -> tự đặt lại
      (if (not (listp kq)) (setq kq (vk:chia L1 (nth 2 d) (nth 3 d) (nth 5 d) (nth 6 d) nil nil)))
      (if (not (listp kq))
        (progn
          ;; cửa không vừa: trả về chiều dài cũ rồi vẽ lại đúng như trước
          (vla-put-Value p (vlax-make-variant (car d) vlax-vbDouble))
          (setq ds (strcat "Vách " (vk:so L1) ": " kq " -> giữ chiều dài " (vk:so (car d)))
                L1 (car d)
                kq (vk:chia L1 (nth 2 d) (nth 3 d) (nth 5 d) (nth 6 d) (nth 4 d) (nth 7 d)))))
      ;; chỉ ghi vào bản *U riêng của bản chèn; trả về đúng chiều dài gốc thì AutoCAD dùng lại block gốc
      (setq ten (vla-get-Name obj))
      (if (and (listp kq) (= "*" (substr ten 1 1)))
        (progn
          ;; đầu vách đọc từ hình AutoCAD vừa kéo giãn (kéo grip đầu thì đố đầu dời theo), đo TRƯỚC khi xoá
          (setq blk (vla-Item (vla-get-Blocks (vk:doc)) ten)
                dx (vk:dau-vach blk))
          (vlax-for x blk (setq ds2 (cons x ds2)))
          (foreach x ds2 (vla-Delete x))
          (vk:ve-vao blk kq L1 (nth 1 d) dx (nth 8 d))
          (vla-Update obj)))
      (if (listp kq) (vk:dat-xd obj kq L1 (nth 1 d) (nth 8 d)))
      (cond
        (ds (strcat "VK: " ds))
        ((listp kq)
         (strcat "VK: vách kéo thành " (vk:so L1) " -> " (itoa (length (cadr kq))) " đố, "
                 (itoa (nth 3 kq)) " ô kính" (if (> (nth 3 kq) 0) (strcat " × " (vk:so (nth 2 kq))) "")
                 " [" (vk:chuoi (car kq)) "]")))))
)

;;; Reactor: ghi handle bản chèn bị sửa; hết lệnh thì xử lý (bỏ qua khi UNDO / REDO: Undo tự trả nội dung)
;;; reactor database gọi (r (list database đối-tượng)), đối tượng là ename. KHÔNG đọc đối tượng ở đây
;;; (entget trong lúc SAVEAS làm AutoCAD lỗi 0xC0000005, thử 29/10/2026): chỉ ghi ename, lọc khi hết lệnh;
;;; bỏ qua cả khi đang lưu bản vẽ.
(defun vk:r-sua (r ds / obj)
  (if (not (or *vk-dang-sua* *vk-dang-luu*))
    (if (= 'ENAME (type (setq obj (cadr ds))))
      (setq *vk-cho* (cons obj *vk-cho*))))
)

(defun vk:r-luu (r ds) (setq *vk-dang-luu* T))
(defun vk:r-luu-xong (r ds) (setq *vk-dang-luu* nil *vk-cho* nil))

(defun vk:xu-ly-cho (/ ds kq undo)
  (setq ds *vk-cho* *vk-cho* nil *vk-dang-sua* T)
  ;; một nhóm undo: U lần 1 bỏ phần chia lại, U lần 2 bỏ thao tác kéo grip
  (if (setq undo (vk:undo-ok)) (vla-StartUndoMark (vk:doc)))
  (foreach e ds
    ;; vách nhận theo XData (tên block do người dùng đặt, không còn luôn là VACH KINH ...)
    (if (and (= 'ENAME (type e)) (entget e) (vk:doc-xd e))
      (progn
        (setq kq (vl-catch-all-apply 'vk:keo-lai (list e)))
        (cond
          ((vl-catch-all-error-p kq) (princ (strcat "\nVK: lỗi chia lại vách: " (vl-catch-all-error-message kq))))
          (kq (princ (strcat "\n" kq)))))))
  (if undo (vla-EndUndoMark (vk:doc)))
  (setq *vk-dang-sua* nil)
  (princ)
)

;;; Bản chèn vách (có XData) mà ChieuDai khác chiều dài đã lưu -> cần chia lại. Chỉ ĐỌC, gọi được trong reactor.
(defun vk:can-chia (e / d p)
  (and (= 'ENAME (type e)) (entget e) (= "INSERT" (cdr (assoc 0 (entget e)))) (setq d (vk:doc-xd e))
       (setq p (vk:prop (vlax-ename->vla-object e)))
       (not (equal (vlax-variant-value (vla-get-Value p)) (car d) 0.005)))
)

;;; Hết lệnh: KHÔNG sửa bản vẽ ngay trong reactor (sửa nội dung *U trong commandEnded làm hỏng CSDL: AUDIT
;;; dừng giữa chừng, không lưu được - thử 29/10/2026) -> lọc vách cần chia rồi gửi (vk:xu-ly-cho) ra dòng
;;; lệnh, AutoCAD chạy ngay sau khi lệnh hiện tại xong hẳn.
(defun vk:r-xong (r cmd / ds)
  (if *vk-cho*
    (if (or *vk-dang-sua* (member (strcase (car cmd)) '("U" "UNDO" "REDO" "MREDO" "VK")))
      (setq *vk-cho* nil)
      (progn
        (setq ds *vk-cho* *vk-cho* nil)
        (foreach e ds
          (if (and (not (member e *vk-cho*)) (= T (vl-catch-all-apply 'vk:can-chia (list e))))
            (setq *vk-cho* (cons e *vk-cho*))))
        (if *vk-cho* (vla-SendCommand (vk:doc) "(vk:xu-ly-cho)\n")))))
)

(defun vk:r-huy (r cmd) (setq *vk-cho* nil))

(defun vk:bat-reactor ()
  (if (not (and *vk-r-db* (vlr-added-p *vk-r-db*)))
    (setq *vk-r-db* (vlr-acdb-reactor nil '((:vlr-objectModified . vk:r-sua)))))
  (if (not (and *vk-r-luu* (vlr-added-p *vk-r-luu*)))
    (setq *vk-r-luu* (vlr-editor-reactor nil '((:vlr-beginSave . vk:r-luu) (:vlr-saveComplete . vk:r-luu-xong)))))
  (if (not (and *vk-r-lenh* (vlr-added-p *vk-r-lenh*)))
    (setq *vk-r-lenh* (vlr-command-reactor nil '((:vlr-commandEnded . vk:r-xong)
                                                 (:vlr-commandCancelled . vk:r-huy)
                                                 (:vlr-commandFailed . vk:r-huy)))))
)

;;; kq = kết quả vk:chia; L dài; lat T/nil; pt điểm đầu vách (WCS); goc radian. Trả về tên block vách hoặc nil.
;;; Định nghĩa block "VACH KINH <dài>" dựng bằng vla (vk:ve-vao), gắn tham số động (vk:lam-dong), chèn tại pt
;;; góc goc, ghi XData thông số cửa. Không còn dùng -BLOCK.
(defun vk:dung (kq L lat pt goc / o ten blk e wmax)
  (setq o (car kq))
  (if (not (tblsearch "LAYER" vk:layer))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 vk:layer) '(70 . 0) '(62 . 151) '(6 . "Continuous"))))
  ;; tên block không được có dấu phẩy: chiều dài lẻ 4210,53 -> "VACH KINH 4210_53"
  ;; (người dùng gặp "Invalid block name" 29/10/2026), cùng cách đặt tên block cửa kéo giãn
  ;; vk-ten: tên người dùng ghi trong bảng (biến của c:VK); trống / nil -> tự đặt
  (setq ten (if (and vk-ten (/= vk-ten "") (snvalid vk-ten)) (vk:ten-block vk-ten) (vk:ten-tu-dat L))
        blk (vla-Add (vla-get-Blocks (vk:doc)) (vlax-3d-point 0.0 0.0 0.0) ten)
        wmax (apply 'max (cons 0.0 (mapcar '(lambda (x) (if (/= (car x) "K") (cadr x) 0.0)) o))))
  (vk:ve-vao blk kq L lat 0.0 0)
  (if (not (vk:lam-dong ten L lat wmax))
    (princ "\nVK: grip kéo chiều dài chưa gắn đủ (Block Editor bị khoá, hoặc xem dòng báo phía trên)."))
  (entmake (list '(0 . "INSERT") (cons 2 ten) (cons 8 vk:layer) (cons 10 pt)
                 '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) (cons 50 goc)))
  (setq e (entlast))
  (if (and e (= ten (cdr (assoc 2 (entget e)))))
    (progn (vk:dat-xd (vlax-ename->vla-object e) kq L lat 0) ten))
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
;;; Nhóm undo bằng vla-StartUndoMark, không gọi lệnh UNDO qua dòng lệnh: lệnh UNDO có lúc dừng ở dòng hỏi
;;; "Enter the number of operations to undo" (người dùng báo 29/10/2026, sau khi pick 2 điểm).
(defun vk:thuc-hien (kq L lat pt goc / *error* bien cu undo ucs p2 ten doc)
  (defun *error* (msg)
    (mapcar 'setvar bien cu)
    (if ucs (command-s "_.UCS" "_P"))
    (if undo (vla-EndUndoMark doc))
    (setq *vk-dang-sua* nil *vk-cho* nil)
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*"))
      (princ (strcat "\nLỗi VK: " msg)))
    (princ)
  )
  (setq bien '("CMDECHO" "OSMODE" "CLAYER") cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (setvar "OSMODE" 0)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  ;; reactor bỏ qua mọi thay đổi trong lúc đang dựng vách
  (setq *vk-dang-sua* T)
  (if (setq undo (vk:undo-ok)) (vla-StartUndoMark doc))
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
  (if undo (vla-EndUndoMark doc))
  (setq *vk-dang-sua* nil *vk-cho* nil)
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- pick 2 điểm
;;; Chọn điểm đầu / cuối vách (mép ngoài, theo OSNAP người dùng đang đặt). Trả về (p1 p2 dài): p1 p2 toạ độ
;;; WCS (vk:thuc-hien chuyển UCS về World trước khi dựng), dài đo trên mặt phẳng XY; huỷ / trùng điểm -> nil.
;;; Enter ở điểm đầu = thôi, quay lại bảng.
(defun vk:pick-dai (/ p1 p2 a b)
  (if (and (setq p1 (getpoint "\nChọn điểm đầu vách (mép ngoài) <Enter = quay lại bảng>: "))
           (setq p2 (getpoint p1 "\nChọn điểm cuối vách (mép ngoài): ")))
    (progn
      (setq a (trans p1 1 0) b (trans p2 1 0)
            a (list (car a) (cadr a) (caddr a)) b (list (car b) (cadr b) (caddr a)))
      (if (> (distance a b) 1e-6) (list a b (distance a b)))))
)

;;; ---------------------------------------------------------------- hộp thoại
;;; Lưới ô (người dùng chốt 29/10/2026, thay cho 2 ô "Ở ô thứ"): mỗi ô của vách một dòng có 2 ô tích Sổ / Đi;
;;; tích = đặt cửa sổ / cửa đi vào đúng ô đó, số lượng cửa tự cập nhật. DCL không có ô tích trong list_box nên
;;; dựng sẵn vk:o-max dòng (vk:o-cot dòng mỗi cột), dòng thừa để trống và khoá.
(setq vk:o-max 36 vk:o-cot 12)

(defun vk:dcl-luoi (/ ds c r i)
  (setq ds (list "  : boxed_column { label = \"Các ô của vách (đếm từ trái) - tích Sổ / Đi để đặt cửa sổ / cửa đi vào ô đó\";"
                 "    : row {")
        c 0)
  (repeat (/ vk:o-max vk:o-cot)
    (setq ds (append ds
                     (list "      : column {"
                           "        : row { : text { label = \"Sổ\"; width = 4; fixed_width = true; } : text { label = \"Đi\"; width = 4; fixed_width = true; } : text { label = \"Ô  -  loại  -  rộng\"; width = 24; } }"))
          r 1)
    (repeat vk:o-cot
      (setq i (itoa (+ (* c vk:o-cot) r))
            ds (append ds
                       (list (strcat "        : row { : toggle { key = \"s" i "\"; label = \"\"; width = 4; fixed_width = true; }"
                                     " : toggle { key = \"d" i "\"; label = \"\"; width = 4; fixed_width = true; }"
                                     " : text { key = \"t" i "\"; width = 24; } }")))
            r (1+ r)))
    (setq ds (append ds (list "      }")) c (1+ c)))
  (append ds (list "    }" "    : text { key = \"oluu\"; width = 90; }" "  }"))
)

(defun vk:viet-dcl (f / h)
  ;; VK.lsp sinh từ file này đã đổi chữ có dấu thành mã \U+XXXX (chỉ còn ký tự ASCII) -> ghi DCL thường,
  ;; hộp thoại hiện đúng dấu với cả LISPSYS = 0 và 1
  (setq h (open f "w"))
  (foreach s
    (append
      '("vk_hop_thoai : dialog {"
        "  label = \"VK - Chia đố vách kính\";"
        "  : boxed_column { label = \"Vách kính\";"
        "    : row {"
        "      : edit_box { key = \"dai\"; label = \"Chiều dài vách (mm, mép ngoài - mép ngoài):\"; edit_width = 10; }"
        "      : button { key = \"pick\"; label = \"Pick 2 điểm <\"; fixed_width = true; }"
        "    }"
        "    : text { key = \"diem\"; width = 62; }"
        "    : edit_box { key = \"ten\"; label = \"Tên vách (= tên block; trống = tự đặt):\"; edit_width = 28; }"
        "    : text { key = \"tenbao\"; width = 62; }"
        "    : text { key = \"thongtin\"; width = 62; }"
        "  }"
        "  : row {"
        "    : boxed_column { label = \"Cửa sổ mở\";"
        "      : edit_box { key = \"ns\"; label = \"Số lượng:\"; edit_width = 6; }"
        "      : edit_box { key = \"ws\"; label = \"Rộng tâm - tâm đố (mm):\"; edit_width = 8; }"
        "    }"
        "    : boxed_column { label = \"Cửa đi\";"
        "      : edit_box { key = \"nd\"; label = \"Số lượng:\"; edit_width = 6; }"
        "      : edit_box { key = \"wd\"; label = \"Rộng tâm - tâm đố (mm):\"; edit_width = 8; }"
        "    }"
        "    : boxed_column { label = \"Xem trước (mặt bằng, trái -> phải): xanh = cửa sổ, đỏ = cửa đi\";"
        "      : image { key = \"xem\"; width = 58; height = 5; color = 250; fixed_width = true; fixed_height = true; }"
        "    }"
        "  }")
      (vk:dcl-luoi)
      '("  : row {"
        "    : toggle { key = \"lat\"; label = \"Lật vách (mặt kẹp kính sang phía bên kia)\"; }"
        "    : button { key = \"tinh\"; label = \"Tính lại\"; fixed_width = true; }"
        "  }"
        "  : text { key = \"loi\"; width = 62; }"
        "  ok_cancel;"
        "}"))
    (write-line s h))
  (close h)
)

;;; Ô xem trước (người dùng yêu cầu 29/10/2026): sơ đồ mặt bằng vách theo kết quả chia kq, vẽ lại mỗi lần bảng đổi.
;;; Ô kính: nét xanh nhạt; cửa sổ: dải xanh dương; cửa đi: dải đỏ + 2 nét chéo (cánh mở); đố: vạch trắng.
(defun vk:ve-xem (kq / w h L le x0 y0 tl o tam i xa xb)
  (setq w (dimx_tile "xem") h (dimy_tile "xem") le 6 y0 (/ h 2))
  (start_image "xem")
  (fill_image 0 0 w h 250)
  (if (and (listp kq) (setq o (car kq) tam (cadr kq)) o)
    (progn
      (setq L (+ (last tam) (/ vk:do-rong 2.0))
            tl (/ (- w (* 2 le)) L)
            i 0)
      (foreach x o
        (setq xa (+ le (fix (* tl (nth i tam)))) xb (+ le (fix (* tl (nth (1+ i) tam)))))
        (cond
          ((= (car x) "S") (fill_image xa (- y0 3) (max 1 (- xb xa)) 7 5))
          ((= (car x) "D")
           (fill_image xa (- y0 3) (max 1 (- xb xa)) 7 1)
           ;; cánh mở 2 bên
           (vector_image xa y0 (/ (+ xa xb) 2) (- y0 (fix (* 0.4 h))) 1)
           (vector_image xb y0 (/ (+ xa xb) 2) (- y0 (fix (* 0.4 h))) 1))
          (T (vector_image xa y0 xb y0 4)))
        (setq i (1+ i)))
      ;; đố
      (foreach c tam
        (setq x0 (+ le (fix (* tl c))))
        (fill_image (max 0 (1- x0)) (- y0 6) 3 13 7))))
  (end_image)
)

;;; Vị trí (ô thứ, đếm từ 1) các ô loại loai ("S" / "D") trong danh sách ô o
(defun vk:vi-tri (o loai / i kq)
  (setq i 1)
  (foreach x o (if (= (car x) loai) (setq kq (cons i kq))) (setq i (1+ i)))
  (reverse kq)
)

(defun vk:vt->chuoi (ds / s)
  (foreach i ds (setq s (strcat (if s (strcat s ",") "") (itoa i))))
  (if s s "")
)

(defun vk:dau (ds n / kq) (repeat (min n (length ds)) (setq kq (cons (car ds) kq) ds (cdr ds))) (reverse kq))

;;; Đọc các ô nhập + vị trí cửa đang tích (vk-vs / vk-vd, biến của c:VK) -> kết quả chia; cập nhật bảng
(defun vk:cap-nhat (/ L ns nd ws wd kq i x tn tu-dat)
  (setq L (vk:doc-so (get_tile "dai"))
        ns (vk:doc-so (get_tile "ns")) ns (if ns (max 0 (fix ns)) 0)
        nd (vk:doc-so (get_tile "nd")) nd (if nd (max 0 (fix nd)) 0)
        ws (vk:doc-so (get_tile "ws")) wd (vk:doc-so (get_tile "wd"))
        kq (vk:chia L ns ws nd wd vk-vs vk-vd))
  ;; vị trí đã tích không còn hợp (vd. vách ngắn đi, ít ô hơn) -> đặt lại tự động
  (if (and (not (listp kq)) (or vk-vs vk-vd) (listp (vk:chia L ns ws nd wd nil nil)))
    (setq kq (vk:chia L ns ws nd wd nil nil) vk-vs nil vk-vd nil tu-dat T))
  (vk:ve-xem kq)
  ;; lưới ô
  (setq i 1)
  (repeat vk:o-max
    (setq x (if (listp kq) (nth (1- i) (car kq))))
    (if x
      (progn
        (set_tile (strcat "t" (itoa i))
                  (strcat "Ô " (itoa i) "  -  "
                          (cond ((= (car x) "S") "Cửa sổ") ((= (car x) "D") "Cửa đi") (T "Kính"))
                          "  -  " (vk:so (cadr x))))
        (set_tile (strcat "s" (itoa i)) (if (= (car x) "S") "1" "0"))
        (set_tile (strcat "d" (itoa i)) (if (= (car x) "D") "1" "0"))
        (mode_tile (strcat "s" (itoa i)) 0)
        (mode_tile (strcat "d" (itoa i)) 0))
      (progn
        (set_tile (strcat "t" (itoa i)) "")
        (set_tile (strcat "s" (itoa i)) "0")
        (set_tile (strcat "d" (itoa i)) "0")
        (mode_tile (strcat "s" (itoa i)) 1)
        (mode_tile (strcat "d" (itoa i)) 1)))
    (setq i (1+ i)))
  (set_tile "oluu"
    (cond
      (tu-dat "Vị trí cửa đã tích không còn hợp với số ô mới - đã đặt lại tự động")
      ((and (listp kq) (> (length (car kq)) vk:o-max))
       (strcat "Vách có " (itoa (length (car kq))) " ô: bảng chỉ hiện " (itoa vk:o-max) " ô đầu"))
      (T "")))
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "Số đố: " (itoa (length (cadr kq))) "   |   Ô kính: " (itoa (nth 3 kq))
                                   (if (> (nth 3 kq) 0) (strcat " × " (vk:so (nth 2 kq)) " mm") "")
                                   "   |   Đố rộng 65, mỗi ô < 1200"))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "Lỗi: " kq))))
  (set_tile "diem"
    (cond
      ((not vk-diem) "Chưa có chiều dài thì bấm Pick 2 điểm (đầu / cuối vách); nhập tay thì OK sẽ hỏi điểm đặt")
      ((vk:dung-diem L) "Đã pick 2 điểm: OK là dựng vách đúng vị trí đã chọn")
      (T "Chiều dài đã sửa tay: OK sẽ hỏi lại điểm đặt vách")))
  ;; tên vách = tên block (người dùng yêu cầu 29/10/2026); trống = tự đặt "VACH KINH <dài>"
  (setq tn (vl-string-trim " " (get_tile "ten")) vk-ten-loi nil)
  (set_tile "tenbao"
    (cond
      ((= tn "") (if L (strcat "Tên tự đặt: " (vk:ten-tu-dat L)) "Để trống: tự đặt VACH KINH <dài>"))
      ((not (snvalid tn))
       (setq vk-ten-loi T)
       "Lỗi: tên có ký tự không dùng được trong tên block (< > / \\ \" : ; ? * | , = `)")
      ((tblsearch "BLOCK" tn) (strcat "Tên đã có trong bản vẽ -> block sẽ đặt \"" (vk:ten-block tn) "\""))
      (T (strcat "Block: " tn))))
  (setq vk-kq kq vk-dai L)
)

;;; Tích / bỏ tích ô i ở cột loai ("S" / "D"): vị trí cửa = các ô đang là cửa trong bảng (+ / - ô i), số lượng
;;; cửa = số ô tích; một ô chỉ là một loại cửa
(defun vk:tich (loai i v / so di)
  (if (listp vk-kq)
    (progn
      (setq so (vk:vi-tri (car vk-kq) "S") di (vk:vi-tri (car vk-kq) "D"))
      (if (= v "1")
        (if (= loai "S")
          (setq so (vl-sort (cons i (vl-remove i so)) '<) di (vl-remove i di))
          (setq di (vl-sort (cons i (vl-remove i di)) '<) so (vl-remove i so)))
        (if (= loai "S") (setq so (vl-remove i so)) (setq di (vl-remove i di))))
      (setq vk-vs so vk-vd di)
      (set_tile "ns" (itoa (length so)))
      (set_tile "nd" (itoa (length di)))))
  (vk:cap-nhat)
)

;;; Sửa ô Số lượng: giữ các cửa đang có (bớt thì bỏ từ cuối), cửa thêm thì tự đặt
(defun vk:sua-sl (/ ns nd)
  (setq ns (vk:doc-so (get_tile "ns")) ns (if ns (max 0 (fix ns)) 0)
        nd (vk:doc-so (get_tile "nd")) nd (if nd (max 0 (fix nd)) 0))
  (if (listp vk-kq)
    (setq vk-vs (vk:dau (vk:vi-tri (car vk-kq) "S") ns)
          vk-vd (vk:dau (vk:vi-tri (car vk-kq) "D") nd))
    (setq vk-vs (vk:dau vk-vs ns) vk-vd (vk:dau vk-vd nd)))
  (vk:cap-nhat)
)

;;; Tên tự đặt: "VACH KINH <dài>", dấu phẩy -> "_" (tên block không được có dấu phẩy), trùng thì thêm " (2)"...
(defun vk:ten-tu-dat (L) (vk:ten-block (strcat "VACH KINH " (vl-string-translate "," "_" (vk:so L)))))

;;; Chiều dài L còn khớp 2 điểm đã pick (ô nhập làm tròn 2 chữ số lẻ)
(defun vk:dung-diem (L) (and vk-diem L (equal L (caddr vk-diem) 0.006)))

(defun vk:luu-nho ()
  ;; vị trí cửa không còn ô nhập: lấy từ các ô đang tích (vk-vs / vk-vd)
  (setq *vk-nho* (append (mapcar '(lambda (k) (cons k (get_tile k))) '("dai" "ns" "ws" "nd" "wd" "lat" "ten"))
                         (list (cons "vs" (vk:vt->chuoi vk-vs)) (cons "vd" (vk:vt->chuoi vk-vd))))))

;;; Ghi chiều dài 2 điểm vừa pick vào ô "dai" của bộ nhớ hộp thoại
(defun vk:nho-dai (d)
  (if (not *vk-nho*)
    (setq *vk-nho* '(("dai" . "") ("ns" . "0") ("ws" . "1000") ("vs" . "")
                     ("nd" . "0") ("wd" . "1665") ("vd" . "") ("lat" . "0"))))
  (setq *vk-nho* (subst (cons "dai" (vk:so (caddr d))) (assoc "dai" *vk-nho*) *vk-nho*))
)

;;; Gõ VK -> bảng hiện ra trước: có chiều dài thì nhập, chưa có thì bấm "Pick 2 điểm <" (bảng ẩn, chọn điểm đầu
;;; + điểm cuối vách, bảng mở lại với chiều dài đã điền) -> chọn cửa sổ / cửa đi -> OK dựng vách đúng 2 điểm đã
;;; pick (người dùng chốt 29/10/2026). Hộp thoại đóng với mã 2 khi bấm nút pick.
(defun c:VK (/ f id kq-dlg vk-kq vk-dai vk-diem lat d vk-ten vk-ten-loi vk-vs vk-vd i)
  ;; tên vách không nhớ sang vách sau (mỗi vách một tên); chỉ giữ trong lúc bảng đóng / mở lại khi pick
  (if (assoc "ten" *vk-nho*) (setq *vk-nho* (subst '("ten" . "") (assoc "ten" *vk-nho*) *vk-nho*)))
  ;; vị trí cửa lần trước (chuỗi "2,4" trong bộ nhớ bảng)
  (setq vk-vs (vk:doc-vt (cdr (assoc "vs" *vk-nho*))) vk-vd (vk:doc-vt (cdr (assoc "vd" *vk-nho*))))
  (if (not (listp vk-vs)) (setq vk-vs nil))
  (if (not (listp vk-vd)) (setq vk-vd nil))
  (setq f (strcat (getvar "TEMPPREFIX") "VK_hop_thoai.dcl"))
  (vk:viet-dcl f)
  (if (< (setq id (load_dialog f)) 0)
    (princ "\nKhông mở được hộp thoại VK.")
    (progn
      (setq kq-dlg 2)
      (while (= kq-dlg 2)
        (setq kq-dlg nil)
        (if (not (new_dialog "vk_hop_thoai" id))
          (princ "\nKhông mở được hộp thoại VK.")
          (progn
            (foreach x (if *vk-nho* *vk-nho*
                         '(("dai" . "") ("ns" . "0") ("ws" . "1000") ("vs" . "")
                           ("nd" . "0") ("wd" . "1665") ("vd" . "") ("lat" . "0")))
              (if (not (member (car x) '("vs" "vd"))) (set_tile (car x) (cdr x))))
            (foreach k '("dai" "ws" "wd" "ten" "tinh")
              (action_tile k "(vk:cap-nhat)"))
            (action_tile "ns" "(vk:sua-sl)")
            (action_tile "nd" "(vk:sua-sl)")
            ;; ô tích Sổ / Đi của từng ô
            (setq i 1)
            (repeat vk:o-max
              (action_tile (strcat "s" (itoa i)) (strcat "(vk:tich \"S\" " (itoa i) " $value)"))
              (action_tile (strcat "d" (itoa i)) (strcat "(vk:tich \"D\" " (itoa i) " $value)"))
              (setq i (1+ i)))
            (action_tile "pick" "(vk:luu-nho) (done_dialog 2)")
            (action_tile "accept"
              (strcat "(vk:cap-nhat) (if (and (listp vk-kq) (not vk-ten-loi)) (progn (setq lat (= \"1\" (get_tile \"lat\"))"
                      " vk-ten (vl-string-trim \" \" (get_tile \"ten\"))) (vk:luu-nho) (done_dialog 1)))"))
            (action_tile "cancel" "(vk:luu-nho) (done_dialog 0)")
            (vk:cap-nhat)
            (setq kq-dlg (start_dialog))
            ;; bấm Pick 2 điểm: pick lại rồi mở lại bảng với chiều dài mới
            (if (and (= kq-dlg 2) (setq d (vk:pick-dai)))
              (progn (setq vk-diem d) (vk:nho-dai d))))))
      (unload_dialog id)
      (if (= kq-dlg 1)
        (if (vk:dung-diem vk-dai)
          (vk:thuc-hien vk-kq vk-dai lat (car vk-diem) (angle (car vk-diem) (cadr vk-diem)))
          (vk:thuc-hien vk-kq vk-dai lat nil nil)))))
  (princ)
)

(vk:bat-reactor)
(princ "\nĐã nạp VK.lsp — gõ VK để chia đố vách kính (kéo grip cuối vách để đổi chiều dài, đố tự chia lại).")
(princ)
