;;; vkmd_nguon.lsp — NGUỒN của VKMD.lsp: sửa file này rồi chạy scripts\gop_vkmd.py để sinh VKMD.lsp (không sửa tay VKMD.lsp)
;;; VKMD.lsp — Dựng mặt đứng vách kính từ block mặt bằng "VACH KINH <dài>" do lệnh VK tạo (Archivina)
;;; Lệnh: VKMD
;;;   Chọn block vách trên mặt bằng -> hộp thoại chiều cao -> chọn cao độ đặt mặt đứng (thẳng hàng phía trên mặt bằng).
;;; Quy tắc (người dùng chốt 29/10/2026):
;;;   - Vị trí đố đứng, cửa sổ, cửa đi đọc từ block mặt bằng; thứ tự trái / phải giữ đúng như mặt bằng.
;;;   - Đố đứng, khung trên, khung dưới, đố ngang rộng 65; đố đứng chạy suốt, thanh ngang vẽ giữa 2 mặt đố.
;;;   - Vách cửa đi: khung dưới (trừ ô cửa đi) + khung trên + 1 đố ngang ở đỉnh cửa (mặt dưới đố = cao cửa),
;;;     chạy suốt vách. Cao cửa nhập tay. Vách không có cả cửa sổ lẫn cửa đi.
;;;   - Vách cửa sổ: khung trên / dưới; cửa sổ treo ngay dưới đố ngang, có đố dưới cửa sổ CHỈ trong ô cửa sổ.
;;;     Đố ngang trên cửa sổ (chạy suốt vách): mặt trên ở cao độ nhập (mặc định 2700); ô kính phía trên đố
;;;     ngang nhỏ hơn mức tối thiểu (mặc định 300) thì bỏ đố, cửa sổ sát khung trên (Cần xác nhận lại).
;;;   - Ký hiệu kính 3 vạch (block VKMD_Kinh, layer A-Window) đặt giữa mỗi ô kính; không ghi chữ FIX.
;;;   - Hình mặt đứng gom block "MAT DUNG VK <dài>x<cao>" (layer A-Window); kích thước "dim cua" NGOÀI block,
;;;     layer A-Dimension; nét cắt 1-1 (qua ô cửa) và 2-2 (giữa chiều cao cửa) như mẫu CT3: ký hiệu layer
;;;     A-Symbol, nét cắt layer A-Hidden. Ghi chú, tên vách người dùng tự thêm.
;;; Hình cửa sổ / cửa đi lấy theo block người dùng cấp (file mau\block vach kinh\ACAD-md *.dxf), nhúng sẵn ở cuối
;;; file (scripts\tao_du_lieu_md.py) -> chép 1 file VKMD.lsp sang máy khác là chạy được.
;;; Yêu cầu: AutoCAD 2021+, bản vẽ có block mặt bằng do VK.lsp tạo. Không xoá, không sửa đối tượng có sẵn.

(vl-load-com)

;;; ---------------------------------------------------------------- thông số
;;;   vkmd:do: bề rộng đố / thanh ngang; vkmd:so-goc / vkmd:di-goc: tâm-tâm mặc định cửa trong block mặt bằng
;;;   vkmd:dim-*: khoảng cách đường dim tới mép mặt đứng (đo theo mẫu VK01 trong CT3)
;;;   vkmd:kinh-min: ô kính nhỏ hơn mức này (cả 2 chiều) thì không đặt ký hiệu kính
(setq vkmd:do 65.0
      vkmd:so-goc 1000.0
      vkmd:di-goc 1665.0
      vkmd:dim-ngang-chuoi 200.0
      vkmd:dim-ngang-tong 335.0
      vkmd:dim-dung-chuoi 365.0
      vkmd:dim-dung-tong 485.0
      vkmd:kinh-min 300.0
      vkmd:layer "A-Window"
      vkmd:layer-dim "A-Dimension"
      vkmd:layer-kh "A-Symbol"
      vkmd:layer-cat "A-Hidden"
      vkmd:dimstyle "dim cua"
      vkmd:kieu-chu "Arial")

;;; ---------------------------------------------------------------- tiện ích
(defun vkmd:undo-ok () (= 1 (logand 3 (getvar "UNDOCTL"))))

;;; Số -> chuỗi gọn, dấu phẩy thập phân: 1058.75 -> "1058,75"
(defun vkmd:so (x / s)
  (setq s (rtos x 2 2))
  (if (vl-string-search "." s)
    (setq s (vl-string-right-trim "." (vl-string-right-trim "0" s))))
  (vl-string-subst "," "." s)
)

(defun vkmd:doc-so (s)
  (if (and s (/= (vl-string-trim " " s) ""))
    (distof (vl-string-subst "." "," (vl-string-trim " " s)) 2))
)

(defun vkmd:lop (ten mau net)
  (if (not (tblsearch "LAYER" ten))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 ten) '(70 . 0) (cons 62 mau)
                   (cons 6 (if (tblsearch "LTYPE" net) net "Continuous")))))
)

;;; Kiểu nét: nạp từ acad.lin / acadiso.lin; không có thì tạo theo mẫu nhúng (HIDDEN của block cửa sổ)
(defun vkmd:net (ten / ds)
  (if (not (tblsearch "LTYPE" ten))
    (vl-catch-all-apply 'vl-cmdf (list "_.-LINETYPE" "_L" ten (if (= 1 (getvar "MEASUREMENT")) "acadiso.lin" "acad.lin") "")))
  (if (and (not (tblsearch "LTYPE" ten)) (= ten vkmd:dl-so-net))
    (progn
      (setq ds (mapcar '(lambda (x) (list (cons 49 x) '(74 . 0))) vkmd:dl-so-net-mau))
      (entmake (append (list '(0 . "LTYPE") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLinetypeTableRecord")
                             (cons 2 ten) '(70 . 0) (cons 3 ten) '(72 . 65) (cons 73 (length ds))
                             (cons 40 (apply '+ (mapcar 'abs vkmd:dl-so-net-mau))))
                       (apply 'append ds)))))
  (tblsearch "LTYPE" ten)
)

(defun vkmd:ten-block (goc / ten i)
  (setq ten goc i 2)
  (while (tblsearch "BLOCK" ten) (setq ten (strcat goc " (" (itoa i) ")") i (1+ i)))
  ten
)

;;; ---------------------------------------------------------------- tạo đối tượng (trong định nghĩa block đang mở)
;;; pts: ((x y [bulge]) ...); them: các cặp DXF thêm (màu, nét...)
(defun vkmd:lw (pts dong lop them / ed)
  (setq ed (append (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") (cons 8 lop)) them
                   (list '(100 . "AcDbPolyline") (cons 90 (length pts)) (cons 70 (if dong 1 0)))))
  (foreach p pts
    (setq ed (append ed (list (list 10 (car p) (cadr p)) (cons 42 (if (caddr p) (caddr p) 0.0))))))
  (entmake ed)
)

(defun vkmd:hcn (x1 y1 x2 y2 lop)
  (vkmd:lw (list (list x1 y1) (list x2 y1) (list x2 y2) (list x1 y2)) T lop nil))

(defun vkmd:line (x1 y1 x2 y2 lop them)
  (entmake (append (list '(0 . "LINE") (cons 8 lop)) them (list (list 10 x1 y1 0.0) (list 11 x2 y2 0.0)))))

(defun vkmd:chen (ten x y sx sy goc lop)
  (entmake (list '(0 . "INSERT") (cons 2 ten) (cons 8 lop) (list 10 x y 0.0)
                 (cons 41 sx) (cons 42 sy) '(43 . 1.0) (cons 50 goc))))

;;; Text căn giữa
(defun vkmd:chu (s x y h lop)
  (entmake (list '(0 . "TEXT") (cons 8 lop) (list 10 x y 0.0) (list 11 x y 0.0) (cons 40 h) (cons 1 s)
                 (cons 7 (if (tblsearch "STYLE" vkmd:kieu-chu) vkmd:kieu-chu (getvar "TEXTSTYLE")))
                 '(72 . 1) '(73 . 2))))

;;; ---------------------------------------------------------------- block phụ (ký hiệu kính, ký hiệu cắt)
;;; Ký hiệu cắt theo mẫu CT3 (block mcccc1 / mat cat ct1, đã nhân tỉ lệ 1 / 0,25): đường ngắn dày + mũi tên đặc
(defun vkmd:block-phu (/ x)
  (if (not (tblsearch "BLOCK" "VKMD_Kinh"))
    (progn
      (entmake '((0 . "BLOCK") (2 . "VKMD_Kinh") (70 . 0) (10 0.0 0.0 0.0)))
      (foreach x vkmd:dl-kinh (vkmd:line (nth 1 x) (nth 2 x) (nth 3 x) (nth 4 x) "0" nil))
      (entmake '((0 . "ENDBLK")))))
  ;; 1-1: nét ngắn dọc theo đường cắt (hướng +Y), mũi tên chỉ hướng nhìn (+X)
  (if (not (tblsearch "BLOCK" "VKMD_Cat11"))
    (progn
      (entmake '((0 . "BLOCK") (2 . "VKMD_Cat11") (70 . 0) (10 0.0 0.0 0.0)))
      (vkmd:lw '((0.0 -39.44) (0.0 150.38)) nil "0" '((43 . 8.64)))
      (vkmd:line -45.11 0.0 90.2 0.0 "0" nil)
      (entmake '((0 . "SOLID") (8 . "0") (10 90.2 16.05 0.0) (11 90.2 -16.05 0.0) (12 148.38 0.0 0.0) (13 148.38 0.0 0.0)))
      (entmake '((0 . "ENDBLK")))))
  ;; 2-2: nét ngắn dọc theo đường cắt (hướng +X), mũi tên chỉ hướng nhìn (+Y)
  (if (not (tblsearch "BLOCK" "VKMD_Cat22"))
    (progn
      (entmake '((0 . "BLOCK") (2 . "VKMD_Cat22") (70 . 0) (10 0.0 0.0 0.0)))
      (vkmd:lw '((-49.3 0.0) (187.98 0.0)) nil "0" '((43 . 10.8)))
      (vkmd:line 0.0 -56.39 0.0 112.75 "0" nil)
      (entmake '((0 . "SOLID") (8 . "0") (10 -20.06 112.75 0.0) (11 20.06 112.75 0.0) (12 0.0 185.48 0.0) (13 0.0 185.48 0.0)))
      (entmake '((0 . "ENDBLK")))))
  (and (tblsearch "BLOCK" "VKMD_Kinh") (tblsearch "BLOCK" "VKMD_Cat11") (tblsearch "BLOCK" "VKMD_Cat22"))
)

;;; ---------------------------------------------------------------- đọc block mặt bằng
;;; Bề rộng tâm-tâm cửa theo tên block: VK_CuaDi -> mặc định, VK_CuaDi_1500 -> 1500, VK_CuaSoMo_1058_75 -> 1058.75
(defun vkmd:rong-ten (n goc mac-dinh)
  (if (= n goc)
    mac-dinh
    (distof (vl-string-translate "_" "." (substr n (+ 2 (strlen goc)))) 2))
)

;;; e: bản chèn block "VACH KINH ..." trên mặt bằng.
;;; Trả về (L o tam pt ux uy): o = ((loai rong) ...) theo thứ tự đi từ đầu vách; tam = tâm đố; pt = điểm chèn;
;;; (ux uy) = hướng trục vách trong WCS. Lỗi -> chuỗi.
(defun vkmd:doc-vach (e / ed ten b n x tam mo w i c loai o kq sx g)
  (setq ed (entget e))
  (cond
    ((/= "INSERT" (cdr (assoc 0 ed))) "Đối tượng chọn không phải block")
    ((not (wcmatch (strcase (setq ten (cdr (assoc 2 ed)))) "VACH KINH*"))
     (strcat "Block \"" ten "\" không phải block vách kính do lệnh VK tạo (VACH KINH ...)"))
    (T
     (setq b (cdr (assoc -2 (tblsearch "BLOCK" ten))))
     (while b
       (setq x (entget b))
       (if (= "INSERT" (cdr (assoc 0 x)))
         (progn
           (setq n (strcase (cdr (assoc 2 x))) c (cadr (assoc 10 x)))
           (cond
             ((= n "VK_DODUNG") (setq tam (cons c tam)))
             ((wcmatch n "VK_CUASOMO*")
              (setq w (vkmd:rong-ten n "VK_CUASOMO" vkmd:so-goc) mo (cons (list "S" c w) mo) tam (cons c (cons (+ c w) tam))))
             ((wcmatch n "VK_CUADI*")
              (setq w (vkmd:rong-ten n "VK_CUADI" vkmd:di-goc) mo (cons (list "D" c w) mo) tam (cons c (cons (+ c w) tam)))))))
       (setq b (entnext b)))
     ;; tâm đố tăng dần, bỏ trùng (cửa liền nhau dùng chung đố)
     (setq tam (vl-sort tam '<) kq nil)
     (foreach c tam (if (not (and kq (equal c (car kq) 0.01))) (setq kq (cons c kq))))
     (setq tam (reverse kq))
     (cond
       ((< (length tam) 2) "Block vách không có đủ đố (VK_DoDung / VK_CuaSoMo / VK_CuaDi)")
       ((not (equal (car tam) (/ vkmd:do 2.0) 0.5)) "Đố đầu vách không ở 32,5 từ mép - block không phải do VK tạo")
       ((and (assoc "S" mo) (assoc "D" mo)) "Vách có cả cửa sổ và cửa đi: chưa hỗ trợ")
       (T
        (setq i 0)
        (repeat (1- (length tam))
          (setq c (nth i tam)
                loai (car (vl-some '(lambda (m) (if (equal (cadr m) c 0.01) (list (car m)))) mo))
                o (cons (list (if loai loai "K") (- (nth (1+ i) tam) c)) o)
                i (1+ i)))
        (setq sx (cdr (assoc 41 ed)) g (cdr (assoc 50 ed)))
        (list (+ (last tam) (/ vkmd:do 2.0)) (reverse o) tam (cdr (assoc 10 ed))
              (* (if (< sx 0) -1.0 1.0) (cos g)) (* (if (< sx 0) -1.0 1.0) (sin g)))))))
)

;;; Lật thứ tự vách (vách đi từ phải sang trái trên mặt bằng)
(defun vkmd:lat (vach / L)
  (setq L (car vach))
  (list L (reverse (cadr vach)) (reverse (mapcar '(lambda (c) (- L c)) (caddr vach)))
        (nth 3 vach) (- (nth 4 vach)) (- (nth 5 vach)))
)

(defun vkmd:loai (vach)
  (cond ((assoc "D" (cadr vach)) "D") ((assoc "S" (cadr vach)) "S") (T "K")))

;;; ---------------------------------------------------------------- tính cao độ
;;; H cao vách; hd cao cửa đi; hs cao cánh cửa sổ (lọt lòng); ht cao độ mặt trên đố ngang; kmin ô kính trên tối thiểu.
;;; Trả về (loai ngang so hd chuoi): ngang = (y1 y2) đố ngang chạy suốt hoặc nil; so = (y-đáy-đố-dưới y-đỉnh-đố-dưới
;;; y-đỉnh-cánh) hoặc nil; chuoi = cao độ các điểm dim đứng từ dưới lên. Lỗi -> chuỗi.
(defun vkmd:tinh (vach H hd hs ht kmin / loai d nua co yt ngang so)
  (setq loai (vkmd:loai vach) d vkmd:do nua (/ vkmd:do 2.0) kmin (if kmin kmin 0.0))
  (cond
    ((or (not H) (<= H (* 3 d))) "Nhập chiều cao vách")
    ((= loai "D")
     (cond
       ((or (not hd) (<= hd 0)) "Nhập chiều cao cửa đi")
       ((>= (+ hd d d) H) (strcat "Vách phải cao hơn cửa đi + đố ngang + khung trên = " (vkmd:so (+ hd d d))))
       ((<= (+ (- hd vkmd:dl-di-cao) 1200.0) 0)
        (strcat "Cửa đi thấp quá, không kéo giãn được hình mặt đứng (cần > " (vkmd:so (- vkmd:dl-di-cao 1200.0)) ")"))
       (T (list loai (list hd (+ hd d)) nil hd (list 0.0 nua (+ hd nua) (- H nua) H)))))
    ((or (not ht) (<= ht (* 2 d))) "Nhập cao độ mặt trên đố ngang")
    ((and (= loai "S") (or (not hs) (<= hs 0))) "Nhập chiều cao cánh cửa sổ")
    (T
     (setq co (and (< ht (- H d)) (>= (- H d ht) kmin))
           ngang (if co (list (- ht d) ht))
           yt (if co (- ht d) (- H d)))
     (if (= loai "S")
       (setq so (list (- yt hs d) (- yt hs) yt)))
     (cond
       ((and so (< (car so) d))
        (strcat "Cửa sổ cao quá: đố dưới cửa sổ chạm khung dưới (cánh tối đa " (vkmd:so (- yt d d)) ")"))
       (T
        (list loai ngang so nil
              (append (list 0.0 nua)
                      (if so (list (+ (car so) nua)))
                      (if ngang (list (+ (car ngang) nua)))
                      (list (- H nua) H)))))))
)

;;; ---------------------------------------------------------------- dựng
;;; Kéo giãn hình cửa đi: |x| <= 200 (tay nắm, khoá sàn) giữ nguyên, |x| >= 580 (mép cánh, kẹp kính, bản lề sàn)
;;; dời theo bề rộng; y <= 1400 (tay nắm) giữ nguyên, y >= 2600 (kẹp kính trên) dời theo chiều cao; giữa: tỉ lệ.
(defun vkmd:fx (x / a)
  (setq a (abs x))
  (* (if (< x 0) -1.0 1.0)
     (cond ((<= a 200.0) a) ((>= a 580.0) (+ a vkmd:dx)) (T (+ 200.0 (* (- a 200.0) (/ (+ 380.0 vkmd:dx) 380.0))))))
)

(defun vkmd:fy (y)
  (cond ((<= y 1400.0) y) ((>= y 2600.0) (+ y vkmd:dy)) (T (+ 1400.0 (* (- y 1400.0) (/ (+ 1200.0 vkmd:dy) 1200.0)))))
)

(defun vkmd:cua-di (xa xb hd / cx x)
  (setq cx (/ (+ xa xb) 2.0) vkmd:dx (/ (- (- xb xa) vkmd:dl-di-rong) 2.0) vkmd:dy (- hd vkmd:dl-di-cao))
  (foreach x vkmd:dl-cua-di
    (cond
      ((= (car x) "LW")
       (vkmd:lw (mapcar '(lambda (p) (list (+ cx (vkmd:fx (car p))) (vkmd:fy (cadr p)) (caddr p))) (caddr x))
                (cadr x) vkmd:layer nil))
      ((= (car x) "LINE")
       (vkmd:line (+ cx (vkmd:fx (nth 1 x))) (vkmd:fy (nth 2 x)) (+ cx (vkmd:fx (nth 3 x))) (vkmd:fy (nth 4 x)) vkmd:layer nil))
      ((= (car x) "ARC")
       (entmake (list '(0 . "ARC") (cons 8 vkmd:layer) (list 10 (+ cx (vkmd:fx (nth 1 x))) (vkmd:fy (nth 2 x)) 0.0)
                      (cons 40 (nth 3 x)) (cons 50 (nth 4 x)) (cons 51 (nth 5 x)))))))
  ;; ký hiệu kính giữa từng cánh
  (vkmd:chen "VKMD_Kinh" (- cx (/ (- xb xa) 4.0)) (/ hd 2.0) 1.0 1.0 0.0 vkmd:layer)
  (vkmd:chen "VKMD_Kinh" (+ cx (/ (- xb xa) 4.0)) (/ hd 2.0) 1.0 1.0 0.0 vkmd:layer)
)

(defun vkmd:cua-so (xa xb y1 y2 / m)
  (setq m (list (cons 62 vkmd:dl-so-mau)))
  (vkmd:lw (list (list xa y1) (list xb y1) (list xb y2) (list xa y2)) T vkmd:layer m)
  ;; tam giác hướng mở: đỉnh giữa cạnh trên (bản lề trên, cửa hất), nét khuất như block người dùng cấp
  (foreach x (list xa xb)
    (vkmd:line (/ (+ xa xb) 2.0) y2 x y1 vkmd:layer
               (append m (if (tblsearch "LTYPE" vkmd:dl-so-net)
                           (list (cons 6 vkmd:dl-so-net) (cons 48 vkmd:dl-so-net-tile))))))
  (vkmd:chen "VKMD_Kinh" (/ (+ xa xb) 2.0) (/ (+ y1 y2) 2.0) 1.0 1.0 0.0 vkmd:layer)
)

;;; Dựng hình mặt đứng thành block, chèn tại (x0 y0) = góc dưới trái. Trả về tên block hoặc nil.
(defun vkmd:dung (vach kq H x0 y0 / L o tam loai ngang so hd d nua ten i xa xb thanh x b k bars)
  (setq L (car vach) o (cadr vach) tam (caddr vach)
        loai (car kq) ngang (cadr kq) so (caddr kq) hd (nth 3 kq) d vkmd:do nua (/ vkmd:do 2.0))
  (setq ten (vkmd:ten-block (strcat "MAT DUNG VK " (vkmd:so L) "x" (vkmd:so H))))
  (entmake (list '(0 . "BLOCK") (cons 2 ten) '(70 . 0) '(10 0.0 0.0 0.0)))
  ;; đố đứng chạy suốt chiều cao
  (foreach x tam (vkmd:hcn (- x nua) 0.0 (+ x nua) H vkmd:layer))
  ;; từng ô: thanh ngang giữa 2 mặt đố, cửa, ký hiệu kính
  (setq i 0)
  (foreach x o
    (setq xa (+ (nth i tam) nua) xb (- (nth (1+ i) tam) nua)
          bars (append (list (list (- H d) H))
                       (if (/= (car x) "D") (list (list 0.0 d)))
                       (if ngang (list ngang))
                       (if (= (car x) "S") (list (list (car so) (cadr so))))))
    (foreach b bars (vkmd:hcn xa (car b) xb (cadr b) vkmd:layer))
    (cond
      ((= (car x) "D") (vkmd:cua-di xa xb hd))
      ((= (car x) "S") (vkmd:cua-so xa xb (cadr so) (caddr so))))
    ;; ô kính cố định = khoảng hở giữa 2 thanh ngang liên tiếp (trừ cánh cửa sổ); ô cửa đi nằm dưới thanh thấp nhất
    (setq bars (vl-sort bars '(lambda (p q) (< (car p) (car q)))) k 0)
    (repeat (1- (length bars))
      (setq b (list (cadr (nth k bars)) (car (nth (1+ k) bars))))
      (if (and (>= (- (cadr b) (car b)) vkmd:kinh-min) (>= (- xb xa) vkmd:kinh-min)
               (not (and so (= (car x) "S") (equal (car b) (cadr so) 0.01))))
        (vkmd:chen "VKMD_Kinh" (/ (+ xa xb) 2.0) (/ (+ (car b) (cadr b)) 2.0) 1.0 1.0 0.0 vkmd:layer))
      (setq k (1+ k)))
    (setq i (1+ i)))
  (entmake '((0 . "ENDBLK")))
  (if (tblsearch "BLOCK" ten)
    (progn (vkmd:chen ten x0 y0 1.0 1.0 0.0 vkmd:layer) ten))
)

(defun vkmd:dim (p q loc huong / e ed)
  (command "_.DIMLINEAR" "_non" p "_non" q huong "_non" loc)
  (if (and (setq e (entlast)) (= "DIMENSION" (cdr (assoc 0 (setq ed (entget e))))))
    (entmod (subst (cons 8 vkmd:layer-dim) (assoc 8 ed) ed)))
)

;;; Kích thước kiểm tra ngoài block: chuỗi đố + tổng ở dưới, chuỗi cao độ + tổng bên phải
(defun vkmd:kich-thuoc (vach kq H x0 y0 / L ds-cu a b)
  (setq L (car vach) ds-cu (getvar "DIMSTYLE"))
  (if (tblsearch "DIMSTYLE" vkmd:dimstyle)
    (command "_.-DIMSTYLE" "_R" vkmd:dimstyle)
    (princ (strcat "\nKhông có kiểu kích thước \"" vkmd:dimstyle "\": dùng kiểu hiện hành " ds-cu)))
  (setq a 0.0)
  (foreach b (append (caddr vach) (list L))
    (vkmd:dim (list (+ x0 a) y0) (list (+ x0 b) y0) (list (+ x0 (/ (+ a b) 2.0)) (- y0 vkmd:dim-ngang-chuoi)) "_H")
    (setq a b))
  (vkmd:dim (list x0 y0) (list (+ x0 L) y0) (list (+ x0 (/ L 2.0)) (- y0 vkmd:dim-ngang-tong)) "_H")
  (setq a nil)
  (foreach b (nth 4 kq)
    (if a (vkmd:dim (list (+ x0 L) (+ y0 a)) (list (+ x0 L) (+ y0 b))
                    (list (+ x0 L vkmd:dim-dung-chuoi) (+ y0 (/ (+ a b) 2.0))) "_V"))
    (setq a b))
  (vkmd:dim (list (+ x0 L) y0) (list (+ x0 L) (+ y0 H)) (list (+ x0 L vkmd:dim-dung-tong) (+ y0 (/ H 2.0))) "_V")
  (if (and (tblsearch "DIMSTYLE" ds-cu) (/= ds-cu (getvar "DIMSTYLE"))) (command "_.-DIMSTYLE" "_R" ds-cu))
)

;;; Nét cắt 1-1 (dọc, qua giữa ô cửa đầu tiên; không có cửa thì ô giữa) và 2-2 (ngang, giữa chiều cao cửa).
;;; Vị trí ký hiệu theo mẫu VK01 (CT3): 1-1 dưới cách chân 536 / trên cách đỉnh 169; 2-2 cách mép trái 206 / phải 230.
(defun vkmd:net-cat (vach kq H x0 y0 / L o tam i k xc yc net)
  (setq L (car vach) o (cadr vach) tam (caddr vach) i 0 k nil)
  (foreach x o (if (and (not k) (member (car x) '("S" "D"))) (setq k i)) (setq i (1+ i)))
  (if (not k) (setq k (fix (/ (length o) 2))))
  (setq xc (+ x0 (/ (+ (nth k tam) (nth (1+ k) tam)) 2.0))
        yc (+ y0 (cond ((caddr kq) (/ (+ (cadr (caddr kq)) (caddr (caddr kq))) 2.0))
                       ((nth 3 kq) (/ (nth 3 kq) 2.0))
                       (T (/ H 2.0))))
        net (if (tblsearch "LTYPE" "DASHED") (list '(48 . 10.0)) nil))
  ;; 1-1
  (vkmd:line xc (- y0 385.0) xc (+ y0 H 66.0) vkmd:layer-cat net)
  (vkmd:chen "VKMD_Cat11" xc (- y0 536.0) 1.0 1.0 0.0 vkmd:layer-kh)
  (vkmd:chen "VKMD_Cat11" xc (+ y0 H 169.0) 1.0 -1.0 0.0 vkmd:layer-kh)
  (vkmd:chu "1" (- xc 66.0) (+ (- y0 536.0) 72.0) 70.0 vkmd:layer-kh)
  (vkmd:chu "1" (- xc 66.0) (- (+ y0 H 169.0) 72.0) 70.0 vkmd:layer-kh)
  ;; 2-2: mũi tên chỉ xuống (nhìn xuống mặt bằng)
  (vkmd:line (- x0 17.6) yc (+ x0 L 42.0) yc vkmd:layer-cat net)
  (vkmd:chen "VKMD_Cat22" (- x0 205.6) yc 1.0 -1.0 0.0 vkmd:layer-kh)
  (vkmd:chen "VKMD_Cat22" (+ x0 L 230.0) yc -1.0 -1.0 0.0 vkmd:layer-kh)
  (vkmd:chu "2" (- x0 205.6 66.0) (- yc 92.0) 87.5 vkmd:layer-kh)
  ;; số bên phải đặt phía trong mũi tên, tránh đè chữ dim đứng
  (vkmd:chu "2" (+ x0 L 230.0 -66.0) (- yc 92.0) 87.5 vkmd:layer-kh)
)

(defun vkmd:chuoi (kq / a s)
  (foreach b (nth 4 kq)
    (if a (setq s (strcat (if s (strcat s " | ") "") (vkmd:so (- b a)))))
    (setq a b))
  s
)

;;; Chạy đủ (dùng chung cho lệnh VKMD và chạy thử không hộp thoại).
;;; e: bản chèn block mặt bằng; pt: điểm đặt (nil -> hỏi). Vách nằm ngang trên mặt bằng: mặt đứng thẳng hàng
;;; theo X với mặt bằng, chỉ lấy cao độ Y của điểm chọn; vách xiên: góc dưới trái mặt đứng = điểm chọn.
(defun vkmd:thuc-hien (e H hd hs ht kmin pt / *error* bien cu undo ucs vach kq ngang nguoc x0 y0 ten)
  (defun *error* (msg)
    (mapcar 'setvar bien cu)
    (if ucs (command-s "_.UCS" "_P"))
    (if undo (command-s "_.UNDO" "_E"))
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*"))
      (princ (strcat "\nLỗi VKMD: " msg)))
    (princ)
  )
  (setq bien '("CMDECHO" "OSMODE" "CLAYER") cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (if (setq undo (vkmd:undo-ok)) (command "_.UNDO" "_BE"))
  (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
  (setq vach (vkmd:doc-vach e))
  (cond
    ((= 'STR (type vach)) (princ (strcat "\nVKMD: " vach)))
    ((= 'STR (type (setq kq (vkmd:tinh vach H hd hs ht kmin)))) (princ (strcat "\nVKMD: " kq)))
    (T
     (setq ngang (< (abs (nth 5 vach)) 1e-6) nguoc (and ngang (< (nth 4 vach) 0)))
     (if nguoc (setq vach (vkmd:lat vach)))
     (if (not pt)
       (setq pt (getpoint (if ngang "\nChọn cao độ chân mặt đứng (phía trên mặt bằng): "
                                     "\nChọn góc dưới trái mặt đứng: "))))
     (if (not pt)
       (princ "\nĐã huỷ.")
       (progn
         (setvar "OSMODE" 0)
         ;; vách ngang: mép trái mặt đứng = mép trái vách trên mặt bằng (vách vẽ từ phải sang trái: điểm chèn
         ;; là mép phải)
         (setq pt (trans pt 1 0)
               x0 (cond (nguoc (- (car (nth 3 vach)) (car vach))) (ngang (car (nth 3 vach))) (T (car pt)))
               y0 (cadr pt))
         (vkmd:lop vkmd:layer 151 "Continuous")
         (vkmd:lop vkmd:layer-dim 192 "Continuous")
         (vkmd:lop vkmd:layer-kh 3 "Continuous")
         (vkmd:net "DASHED")
         (vkmd:lop vkmd:layer-cat 9 "DASHED")
         (vkmd:net vkmd:dl-so-net)
         (if (not (tblsearch "STYLE" vkmd:kieu-chu))
           (entmake (list '(0 . "STYLE") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbTextStyleTableRecord")
                          (cons 2 vkmd:kieu-chu) '(70 . 0) '(40 . 0.0) '(41 . 1.0) '(50 . 0.0) '(71 . 0)
                          '(3 . "arial.ttf") '(4 . ""))))
         (cond
           ((not (vkmd:block-phu)) (princ "\nVKMD: không tạo được block ký hiệu."))
           ((not (setq ten (vkmd:dung vach kq H x0 y0))) (princ "\nVKMD: không tạo được block mặt đứng."))
           (T
            (vkmd:kich-thuoc vach kq H x0 y0)
            (vkmd:net-cat vach kq H x0 y0)
            (princ (strcat "\nVKMD: mặt đứng " (vkmd:so (car vach)) " x " (vkmd:so H)
                           " -> block " ten "\n    Cao độ (từ dưới lên): " (vkmd:chuoi kq)))))))))
  (if ucs (command "_.UCS" "_P"))
  (if undo (command "_.UNDO" "_E"))
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- hộp thoại
(defun vkmd:viet-dcl (f / h)
  (setq h (open f "w"))
  (foreach s
    '("vkmd_hop_thoai : dialog {"
      "  label = \"VKMD - Mặt đứng vách kính\";"
      "  : text { key = \"vach\"; width = 66; }"
      "  : text { key = \"mo\"; width = 66; }"
      "  : edit_box { key = \"cao\"; label = \"Chiều cao vách (mm):\"; edit_width = 10; }"
      "  : boxed_column { key = \"khung_di\"; label = \"Cửa đi\";"
      "    : edit_box { key = \"hd\"; label = \"Chiều cao cửa đi (mặt dưới đố ngang, mm):\"; edit_width = 10; }"
      "  }"
      "  : boxed_column { key = \"khung_so\"; label = \"Vách cửa sổ / vách kính\";"
      "    : edit_box { key = \"hs\"; label = \"Cao cánh cửa sổ (lọt lòng, mm):\"; edit_width = 10; }"
      "    : edit_box { key = \"ht\"; label = \"Cao độ mặt trên đố ngang (mm):\"; edit_width = 10; }"
      "    : edit_box { key = \"kmin\"; label = \"Ô kính trên đố ngang tối thiểu (nhỏ hơn thì bỏ đố, mm):\"; edit_width = 10; }"
      "  }"
      "  : text { key = \"thongtin\"; width = 66; }"
      "  : text { key = \"loi\"; width = 66; }"
      "  ok_cancel;"
      "}")
    (write-line s h))
  (close h)
)

(defun vkmd:cap-nhat (/ kq)
  (setq kq (vkmd:tinh vkmd-vach (vkmd:doc-so (get_tile "cao")) (vkmd:doc-so (get_tile "hd"))
                      (vkmd:doc-so (get_tile "hs")) (vkmd:doc-so (get_tile "ht")) (vkmd:doc-so (get_tile "kmin"))))
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "Cao độ (từ dưới lên): " (vkmd:chuoi kq)
                                   (if (and (/= (car kq) "D") (not (cadr kq))) "   |   không có đố ngang" "")))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "Lỗi: " kq))))
  (setq vkmd-kq kq)
)

(defun c:VKMD (/ e f id kq-dlg vkmd-vach vkmd-kq loai ten s)
  (while (and (setq e (entsel "\nChọn block vách kính trên mặt bằng (VACH KINH ...): "))
              (= 'STR (type (setq vkmd-vach (vkmd:doc-vach (car e))))))
    (princ (strcat "\n" vkmd-vach)))
  (if e
    (progn
      (setq e (car e) loai (vkmd:loai vkmd-vach)
            f (strcat (getvar "TEMPPREFIX") "VKMD_hop_thoai.dcl"))
      (vkmd:viet-dcl f)
      (if (or (< (setq id (load_dialog f)) 0) (not (new_dialog "vkmd_hop_thoai" id)))
        (princ "\nKhông mở được hộp thoại VKMD.")
        (progn
          (setq s nil)
          (foreach x (cadr vkmd-vach)
            (setq s (strcat (if s (strcat s " | ") "") (cond ((= (car x) "S") "SO ") ((= (car x) "D") "DI ") (T ""))
                            (vkmd:so (cadr x)))))
          (set_tile "vach" (strcat "Vách " (vkmd:so (car vkmd-vach)) " mm, "
                                   (itoa (length (caddr vkmd-vach))) " đố: " s))
          (set_tile "mo" (cond ((= loai "D") "Vách cửa đi") ((= loai "S") "Vách cửa sổ") (T "Vách kính không có cửa")))
          (foreach x (if *vkmd-nho* *vkmd-nho*
                       '(("cao" . "") ("hd" . "2700") ("hs" . "1400") ("ht" . "2700") ("kmin" . "300")))
            (set_tile (car x) (cdr x)))
          (mode_tile "khung_di" (if (= loai "D") 0 1))
          (mode_tile "khung_so" (if (= loai "D") 1 0))
          (if (/= loai "S") (mode_tile "hs" 1))
          (foreach k '("cao" "hd" "hs" "ht" "kmin") (action_tile k "(vkmd:cap-nhat)"))
          (action_tile "accept"
            "(vkmd:cap-nhat) (if (listp vkmd-kq) (progn (setq *vkmd-nho* (mapcar '(lambda (k) (cons k (get_tile k))) '(\"cao\" \"hd\" \"hs\" \"ht\" \"kmin\"))) (done_dialog 1)))")
          (action_tile "cancel" "(done_dialog 0)")
          (vkmd:cap-nhat)
          (setq kq-dlg (start_dialog))
          (unload_dialog id)
          (if (= kq-dlg 1)
            (vkmd:thuc-hien e (vkmd:doc-so (cdr (assoc "cao" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "hd" *vkmd-nho*)))
                            (vkmd:doc-so (cdr (assoc "hs" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "ht" *vkmd-nho*)))
                            (vkmd:doc-so (cdr (assoc "kmin" *vkmd-nho*))) nil))))))
  (princ)
)

(princ "\nĐã nạp VKMD.lsp — gõ VKMD, chọn block vách kính trên mặt bằng để dựng mặt đứng.")
(princ)
