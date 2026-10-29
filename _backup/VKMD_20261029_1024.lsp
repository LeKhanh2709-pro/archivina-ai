;;; FILE SINH TỰ ĐỘNG từ vkmd_nguon.lsp bằng scripts\gop_vkmd.py — KHÔNG SỬA TAY.
;;; Chữ có dấu trong chuỗi đã đổi thành mã \U+XXXX để hiện đúng với cả LISPSYS = 0 và 1.
;;; VKMD.lsp — Dựng mặt đứng vách kính từ block mặt bằng "VACH KINH <dài>" do lệnh VK tạo (Archivina)
;;; Lệnh: MDVK (người dùng chốt tên 29/10/2026)
;;;   Chọn block vách trên mặt bằng -> lệnh tự nhận loại vách (cửa đi / cửa sổ / kính) -> bảng hỏi theo loại
;;;   -> chọn cao độ đặt mặt đứng (thẳng hàng phía trên mặt bằng).
;;; Quy tắc (người dùng chốt 29/10/2026):
;;;   - Vị trí đố đứng, cửa sổ, cửa đi đọc từ block mặt bằng; thứ tự trái / phải giữ đúng như mặt bằng.
;;;   - Đố đứng, khung trên, khung dưới, đố ngang rộng 65; đố đứng chạy suốt, thanh ngang vẽ giữa 2 mặt đố.
;;;   - Vách cửa đi: khung dưới (trừ ô cửa đi) + khung trên + 1 đố ngang ở đỉnh cửa (mặt dưới đố = cao cửa),
;;;     chạy suốt vách. Cao cửa nhập tay. Vách không có cả cửa sổ lẫn cửa đi.
;;;   - Vách cửa sổ: khung trên / dưới; đố dưới cửa sổ CHỈ trong ô cửa sổ. Bảng hỏi: cao cửa sổ (cánh, lọt lòng),
;;;     có / không thanh ngang trên cửa sổ:
;;;       có    -> mép dưới cánh = sàn hoàn thiện + bậu (vd. 50 + 1400), thanh ngang chạy suốt vách ngay trên cửa sổ
;;;                (mặt dưới thanh = mép dưới cánh + cao cửa sổ);
;;;       không -> cửa sổ lên sát mép dưới khung trên.
;;;     Vách kính không cửa: cùng bảng hỏi, thanh ngang đặt như vách cửa sổ (thẳng hàng với vách cửa sổ bên cạnh).
;;;   - Ký hiệu kính 3 vạch (block VKMD_Kinh, layer A-Window) đặt giữa mỗi ô kính; không ghi chữ FIX.
;;;   - Hình mặt đứng gom block "MAT DUNG VK <dài>x<cao>" (layer A-Window); kích thước "dim cua" NGOÀI block,
;;;     layer A-Dimension; nét cắt 1-1 (qua ô cửa) và 2-2 (giữa chiều cao cửa) như mẫu CT3: ký hiệu layer
;;;     A-Symbol, nét cắt layer A-Hidden. Ghi chú, tên vách người dùng tự thêm.
;;; Hình cửa sổ / cửa đi lấy theo block người dùng cấp (file mau\block vach kinh\ACAD-md *.dxf), nhúng sẵn ở cuối
;;; file (scripts\tao_du_lieu_md.py) -> chép 1 file VKMD.lsp sang máy khác là chạy được.
;;; Tên hàm giữ tiền tố vkmd: (file VKMD.lsp); tên lệnh là MDVK.
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
    ((/= "INSERT" (cdr (assoc 0 ed))) "\\U+0110\\U+1ED1i t\\U+01B0\\U+1EE3ng ch\\U+1ECDn kh\\U+00F4ng ph\\U+1EA3i block")
    ((not (wcmatch (strcase (setq ten (cdr (assoc 2 ed)))) "VACH KINH*"))
     (strcat "Block \"" ten "\" kh\\U+00F4ng ph\\U+1EA3i block v\\U+00E1ch k\\U+00EDnh do l\\U+1EC7nh VK t\\U+1EA1o (VACH KINH ...)"))
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
       ((< (length tam) 2) "Block v\\U+00E1ch kh\\U+00F4ng c\\U+00F3 \\U+0111\\U+1EE7 \\U+0111\\U+1ED1 (VK_DoDung / VK_CuaSoMo / VK_CuaDi)")
       ((not (equal (car tam) (/ vkmd:do 2.0) 0.5)) "\\U+0110\\U+1ED1 \\U+0111\\U+1EA7u v\\U+00E1ch kh\\U+00F4ng \\U+1EDF 32,5 t\\U+1EEB m\\U+00E9p - block kh\\U+00F4ng ph\\U+1EA3i do VK t\\U+1EA1o")
       ((and (assoc "S" mo) (assoc "D" mo)) "V\\U+00E1ch c\\U+00F3 c\\U+1EA3 c\\U+1EEDa s\\U+1ED5 v\\U+00E0 c\\U+1EEDa \\U+0111i: ch\\U+01B0a h\\U+1ED7 tr\\U+1EE3")
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
;;; H cao vách (từ chân vách = mặt sàn kết cấu); hd cao cửa đi; hs cao cửa sổ (cánh, lọt lòng);
;;; co T = có thanh ngang trên cửa sổ; san dày sàn hoàn thiện; bau cao bậu (sàn hoàn thiện -> mép dưới cánh).
;;; Trả về (loai ngang so hd chuoi): ngang = (y1 y2) đố ngang chạy suốt hoặc nil; so = (y-đáy-đố-dưới y-đỉnh-đố-dưới
;;; y-đỉnh-cánh) hoặc nil; chuoi = cao độ các điểm dim đứng từ dưới lên. Lỗi -> chuỗi.
(defun vkmd:tinh (vach H hd hs co san bau / loai d nua y1 yt ngang so)
  (setq loai (vkmd:loai vach) d vkmd:do nua (/ vkmd:do 2.0))
  (cond
    ((or (not H) (<= H (* 3 d))) "Nh\\U+1EADp chi\\U+1EC1u cao v\\U+00E1ch")
    ((= loai "D")
     (cond
       ((or (not hd) (<= hd 0)) "Nh\\U+1EADp chi\\U+1EC1u cao c\\U+1EEDa \\U+0111i")
       ((>= (+ hd d d) H) (strcat "V\\U+00E1ch ph\\U+1EA3i cao h\\U+01A1n c\\U+1EEDa \\U+0111i + \\U+0111\\U+1ED1 ngang + khung tr\\U+00EAn = " (vkmd:so (+ hd d d))))
       ((<= (+ (- hd vkmd:dl-di-cao) 1200.0) 0)
        (strcat "C\\U+1EEDa \\U+0111i th\\U+1EA5p qu\\U+00E1, kh\\U+00F4ng k\\U+00E9o gi\\U+00E3n \\U+0111\\U+01B0\\U+1EE3c h\\U+00ECnh m\\U+1EB7t \\U+0111\\U+1EE9ng (c\\U+1EA7n > " (vkmd:so (- vkmd:dl-di-cao 1200.0)) ")"))
       (T (list loai (list hd (+ hd d)) nil hd (list 0.0 nua (+ hd nua) (- H nua) H)))))
    ((and (or (= loai "S") co) (or (not hs) (<= hs 0))) "Nh\\U+1EADp chi\\U+1EC1u cao c\\U+1EEDa s\\U+1ED5")
    ((and co (or (not san) (< san 0))) "Nh\\U+1EADp chi\\U+1EC1u d\\U+00E0y s\\U+00E0n ho\\U+00E0n thi\\U+1EC7n (0 n\\U+1EBFu kh\\U+00F4ng c\\U+00F3)")
    ((and co (or (not bau) (<= bau 0))) "Nh\\U+1EADp cao b\\U+1EADu c\\U+1EEDa s\\U+1ED5")
    (T
     ;; có thanh ngang: cửa sổ đặt theo bậu, thanh ngang ngay trên; không: cửa sổ sát khung trên
     (if co
       (setq y1 (+ san bau) yt (+ y1 hs) ngang (list yt (+ yt d)))
       (setq yt (- H d) y1 (if hs (- yt hs))))
     (if (= loai "S")
       (setq so (list (- y1 d) y1 yt)))
     (cond
       ((and ngang (> (cadr ngang) (- H d 1e-6)))
        (strcat "Thanh ngang ch\\U+1EA1m khung tr\\U+00EAn: s\\U+00E0n + b\\U+1EADu + c\\U+1EEDa s\\U+1ED5 + 65 = " (vkmd:so (cadr ngang))
                " > " (vkmd:so (- H d)) " (b\\U+1ECF thanh ngang ho\\U+1EB7c gi\\U+1EA3m s\\U+1ED1 \\U+0111o)"))
       ((and so (< (car so) (- d 1e-6)))
        (strcat "\\U+0110\\U+1ED1 d\\U+01B0\\U+1EDBi c\\U+1EEDa s\\U+1ED5 ch\\U+1EA1m khung d\\U+01B0\\U+1EDBi: m\\U+00E9p d\\U+01B0\\U+1EDBi c\\U+00E1nh ph\\U+1EA3i >= " (vkmd:so (* 2 d))
                (if co " (t\\U+0103ng b\\U+1EADu)" (strcat " (c\\U+1EEDa s\\U+1ED5 t\\U+1ED1i \\U+0111a " (vkmd:so (- yt d d)) ")"))))
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
    (princ (strcat "\nKh\\U+00F4ng c\\U+00F3 ki\\U+1EC3u k\\U+00EDch th\\U+01B0\\U+1EDBc \"" vkmd:dimstyle "\": d\\U+00F9ng ki\\U+1EC3u hi\\U+1EC7n h\\U+00E0nh " ds-cu)))
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

;;; Chạy đủ (dùng chung cho lệnh MDVK và chạy thử không hộp thoại).
;;; e: bản chèn block mặt bằng; pt: điểm đặt (nil -> hỏi). Vách nằm ngang trên mặt bằng: mặt đứng thẳng hàng
;;; theo X với mặt bằng, chỉ lấy cao độ Y của điểm chọn; vách xiên: góc dưới trái mặt đứng = điểm chọn.
(defun vkmd:thuc-hien (e H hd hs co san bau pt / *error* bien cu undo ucs vach kq ngang nguoc x0 y0 ten)
  (defun *error* (msg)
    (mapcar 'setvar bien cu)
    (if ucs (command-s "_.UCS" "_P"))
    (if undo (command-s "_.UNDO" "_E"))
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*"))
      (princ (strcat "\nL\\U+1ED7i MDVK: " msg)))
    (princ)
  )
  (setq bien '("CMDECHO" "OSMODE" "CLAYER") cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (if (setq undo (vkmd:undo-ok)) (command "_.UNDO" "_BE"))
  (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
  (setq vach (vkmd:doc-vach e))
  (cond
    ((= 'STR (type vach)) (princ (strcat "\nMDVK: " vach)))
    ((= 'STR (type (setq kq (vkmd:tinh vach H hd hs co san bau)))) (princ (strcat "\nMDVK: " kq)))
    (T
     (setq ngang (< (abs (nth 5 vach)) 1e-6) nguoc (and ngang (< (nth 4 vach) 0)))
     (if nguoc (setq vach (vkmd:lat vach)))
     (if (not pt)
       (setq pt (getpoint (if ngang "\nCh\\U+1ECDn cao \\U+0111\\U+1ED9 ch\\U+00E2n m\\U+1EB7t \\U+0111\\U+1EE9ng (ph\\U+00EDa tr\\U+00EAn m\\U+1EB7t b\\U+1EB1ng): "
                                     "\nCh\\U+1ECDn g\\U+00F3c d\\U+01B0\\U+1EDBi tr\\U+00E1i m\\U+1EB7t \\U+0111\\U+1EE9ng: "))))
     (if (not pt)
       (princ "\n\\U+0110\\U+00E3 hu\\U+1EF7.")
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
           ((not (vkmd:block-phu)) (princ "\nMDVK: kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c block k\\U+00FD hi\\U+1EC7u."))
           ((not (setq ten (vkmd:dung vach kq H x0 y0))) (princ "\nMDVK: kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c block m\\U+1EB7t \\U+0111\\U+1EE9ng."))
           (T
            (vkmd:kich-thuoc vach kq H x0 y0)
            (vkmd:net-cat vach kq H x0 y0)
            (princ (strcat "\nMDVK: m\\U+1EB7t \\U+0111\\U+1EE9ng " (vkmd:so (car vach)) " x " (vkmd:so H)
                           " -> block " ten "\n    Cao \\U+0111\\U+1ED9 (t\\U+1EEB d\\U+01B0\\U+1EDBi l\\U+00EAn): " (vkmd:chuoi kq)))))))))
  (if ucs (command "_.UCS" "_P"))
  (if undo (command "_.UNDO" "_E"))
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- hộp thoại
;;; Loại vách tự nhận từ mặt bằng; chỉ bật ô cần cho loại đó (người dùng chốt 29/10/2026):
;;;   cửa đi: cao vách + cao cửa đi; cửa sổ / kính: cao vách + cao cửa sổ + có thanh ngang? (+ sàn hoàn thiện, bậu)
(defun vkmd:viet-dcl (f / h)
  (setq h (open f "w"))
  (foreach s
    '("vkmd_hop_thoai : dialog {"
      "  label = \"MDVK - M\\U+1EB7t \\U+0111\\U+1EE9ng v\\U+00E1ch k\\U+00EDnh\";"
      "  : text { key = \"mo\"; width = 66; }"
      "  : text { key = \"vach\"; width = 66; }"
      "  : edit_box { key = \"cao\"; label = \"Chi\\U+1EC1u cao v\\U+00E1ch k\\U+00EDnh (mm):\"; edit_width = 10; }"
      "  : boxed_column { key = \"khung_di\"; label = \"V\\U+00E1ch c\\U+1EEDa \\U+0111i\";"
      "    : edit_box { key = \"hd\"; label = \"Chi\\U+1EC1u cao c\\U+1EEDa \\U+0111i (thanh ngang \\U+0111\\U+1EB7t ngay tr\\U+00EAn c\\U+1EEDa, mm):\"; edit_width = 10; }"
      "  }"
      "  : boxed_column { key = \"khung_so\"; label = \"V\\U+00E1ch c\\U+1EEDa s\\U+1ED5\";"
      "    : edit_box { key = \"hs\"; label = \"Chi\\U+1EC1u cao c\\U+1EEDa s\\U+1ED5 (c\\U+00E1nh, l\\U+1ECDt l\\U+00F2ng, mm):\"; edit_width = 10; }"
      "    : toggle { key = \"co\"; label = \"C\\U+00F3 thanh ngang tr\\U+00EAn c\\U+1EEDa s\\U+1ED5 (b\\U+1ECF ch\\U+1ECDn: c\\U+1EEDa s\\U+1ED5 l\\U+00EAn s\\U+00E1t khung tr\\U+00EAn)\"; }"
      "    : edit_box { key = \"san\"; label = \"S\\U+00E0n ho\\U+00E0n thi\\U+1EC7n d\\U+00E0y (mm):\"; edit_width = 10; }"
      "    : edit_box { key = \"bau\"; label = \"Cao b\\U+1EADu c\\U+1EEDa s\\U+1ED5, t\\U+1EEB s\\U+00E0n ho\\U+00E0n thi\\U+1EC7n t\\U+1EDBi m\\U+00E9p d\\U+01B0\\U+1EDBi c\\U+00E1nh (mm):\"; edit_width = 10; }"
      "  }"
      "  : text { key = \"thongtin\"; width = 66; }"
      "  : text { key = \"loi\"; width = 66; }"
      "  ok_cancel;"
      "}")
    (write-line s h))
  (close h)
)

(defun vkmd:cap-nhat (/ kq co)
  (setq co (= "1" (get_tile "co")))
  (mode_tile "san" (if co 0 1))
  (mode_tile "bau" (if co 0 1))
  (setq kq (vkmd:tinh vkmd-vach (vkmd:doc-so (get_tile "cao")) (vkmd:doc-so (get_tile "hd")) (vkmd:doc-so (get_tile "hs"))
                      co (vkmd:doc-so (get_tile "san")) (vkmd:doc-so (get_tile "bau"))))
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "Cao \\U+0111\\U+1ED9 t\\U+00E2m thanh ngang (t\\U+1EEB d\\U+01B0\\U+1EDBi l\\U+00EAn): " (vkmd:chuoi kq)
                                   (if (caddr kq) (strcat "   |   m\\U+00E9p d\\U+01B0\\U+1EDBi c\\U+00E1nh +" (vkmd:so (cadr (caddr kq)))) "")))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "L\\U+1ED7i: " kq))))
  (setq vkmd-kq kq)
)

(defun c:MDVK (/ e f id kq-dlg vkmd-vach vkmd-kq loai s khoa)
  (setq khoa '("cao" "hd" "hs" "co" "san" "bau"))
  (while (and (setq e (entsel "\nCh\\U+1ECDn block v\\U+00E1ch k\\U+00EDnh tr\\U+00EAn m\\U+1EB7t b\\U+1EB1ng (VACH KINH ...): "))
              (= 'STR (type (setq vkmd-vach (vkmd:doc-vach (car e))))))
    (princ (strcat "\n" vkmd-vach)))
  (if e
    (progn
      (setq e (car e) loai (vkmd:loai vkmd-vach)
            f (strcat (getvar "TEMPPREFIX") "MDVK_hop_thoai.dcl"))
      (vkmd:viet-dcl f)
      (if (or (< (setq id (load_dialog f)) 0) (not (new_dialog "vkmd_hop_thoai" id)))
        (princ "\nKh\\U+00F4ng m\\U+1EDF \\U+0111\\U+01B0\\U+1EE3c h\\U+1ED9p tho\\U+1EA1i MDVK.")
        (progn
          (setq s nil)
          (foreach x (cadr vkmd-vach)
            (setq s (strcat (if s (strcat s " | ") "") (cond ((= (car x) "S") "SO ") ((= (car x) "D") "DI ") (T ""))
                            (vkmd:so (cadr x)))))
          (set_tile "mo" (strcat "Lo\\U+1EA1i v\\U+00E1ch (nh\\U+1EADn t\\U+1EEB m\\U+1EB7t b\\U+1EB1ng): "
                                 (cond ((= loai "D") "V\\U+00C1CH K\\U+00CDNH C\\U+1EECA \\U+0110I") ((= loai "S") "V\\U+00C1CH K\\U+00CDNH C\\U+1EECA S\\U+1ED4")
                                       (T "V\\U+00C1CH K\\U+00CDNH KH\\U+00D4NG C\\U+1EECA (thanh ngang \\U+0111\\U+1EB7t nh\\U+01B0 v\\U+00E1ch c\\U+1EEDa s\\U+1ED5)"))))
          (set_tile "vach" (strcat "D\\U+00E0i " (vkmd:so (car vkmd-vach)) " mm, " (itoa (length (caddr vkmd-vach)))
                                   " \\U+0111\\U+1ED1: " s))
          (foreach x (if *vkmd-nho* *vkmd-nho*
                       '(("cao" . "") ("hd" . "2700") ("hs" . "1400") ("co" . "1") ("san" . "50") ("bau" . "1400")))
            (set_tile (car x) (cdr x)))
          (mode_tile "khung_di" (if (= loai "D") 0 1))
          (mode_tile "khung_so" (if (= loai "D") 1 0))
          (foreach k khoa (action_tile k "(vkmd:cap-nhat)"))
          (action_tile "accept"
            "(vkmd:cap-nhat) (if (listp vkmd-kq) (progn (setq *vkmd-nho* (mapcar '(lambda (k) (cons k (get_tile k))) khoa)) (done_dialog 1)))")
          (action_tile "cancel" "(done_dialog 0)")
          (vkmd:cap-nhat)
          (setq kq-dlg (start_dialog))
          (unload_dialog id)
          (if (= kq-dlg 1)
            (vkmd:thuc-hien e (vkmd:doc-so (cdr (assoc "cao" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "hd" *vkmd-nho*)))
                            (vkmd:doc-so (cdr (assoc "hs" *vkmd-nho*))) (= "1" (cdr (assoc "co" *vkmd-nho*)))
                            (vkmd:doc-so (cdr (assoc "san" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "bau" *vkmd-nho*)))
                            nil))))))
  (princ)
)

(princ "\n\\U+0110\\U+00E3 n\\U+1EA1p VKMD.lsp \\U+2014 g\\U+00F5 MDVK, ch\\U+1ECDn block v\\U+00E1ch k\\U+00EDnh tr\\U+00EAn m\\U+1EB7t b\\U+1EB1ng \\U+0111\\U+1EC3 d\\U+1EF1ng m\\U+1EB7t \\U+0111\\U+1EE9ng.")
(princ)

;;; ---------------------------------------------------------------- dữ liệu block nhúng (sinh tự động)
;;; Dữ liệu block mặt đứng — SINH TỰ ĐỘNG bằng scripts\tao_du_lieu_md.py, không sửa tay
;;; nguồn: ACAD-md cua di.dxf, ACAD-md cua so.dxf, ACAD-thanh dung va thanh ngang.dxf
(setq vkmd:dl-do-rong 65.0)
(setq vkmd:dl-di-rong 1600.0 vkmd:dl-di-cao 2699.51)
(setq vkmd:dl-so-rong 935.0 vkmd:dl-so-cao 1399.89 vkmd:dl-so-do 65.0 vkmd:dl-so-mau 5)
(setq vkmd:dl-so-net "HIDDEN" vkmd:dl-so-net-tile 300.0 vkmd:dl-so-net-mau (0.25 -0.125))
(setq vkmd:dl-kinh '(("LINE" 104.828 -104.828 -104.828 104.828) ("LINE" 28.3278 -74.0273 -84.0431 38.3436) ("LINE" 59.1285 -22.4157 -48.3913 85.1041)))
(setq vkmd:dl-cua-di '(
  ("LW" T ((-780.0 -58.0 0.0) (-610.0 -58.0 0.414214) (-590.0 -38.0 0.0) (-590.0 0.0 0.0) (-800.0 0.0 0.0) (-800.0 -38.0 0.414214)))
  ("LW" T ((-730.4425 5.0 0.0) (-705.5575 5.0 0.0) (-705.5575 0.0 0.0) (-730.4425 0.0 0.0)))
  ("LW" T ((-800.0 5.0 0.0) (-636.0 5.0 0.0) (-636.0 56.0 0.0) (-800.0 56.0 0.0)))
  ("LW" T ((-800.0 2699.5121 0.0) (-636.0 2699.5121 0.0) (-636.0 2648.5121 0.0) (-800.0 2648.5121 0.0)))
  ("LW" T ((800.0 2699.5121 0.0) (636.0 2699.5121 0.0) (636.0 2648.5121 0.0) (800.0 2648.5121 0.0)))
  ("LW" nil ((0.0 2699.5121 0.0) (0.0 0.0 0.0)))
  ("LW" T ((780.0 -58.0 0.0) (610.0 -58.0 -0.414214) (590.0 -38.0 0.0) (590.0 0.0 0.0) (800.0 0.0 0.0) (800.0 -38.0 -0.414214)))
  ("LW" T ((730.4425 5.0 0.0) (705.5575 5.0 0.0) (705.5575 0.0 0.0) (730.4425 0.0 0.0)))
  ("LW" T ((800.0 5.0 0.0) (636.0 5.0 0.0) (636.0 56.0 0.0) (800.0 56.0 0.0)))
  ("LW" nil ((0.0 2699.5121 0.0) (-800.0 1200.0 0.0) (0.0 0.0 0.0)))
  ("LW" nil ((0.0 2699.5121 0.0) (800.0 1200.0 0.0) (0.0 0.0 0.0)))
  ("LW" T ((-800.0 2699.5121 0.0) (800.0 2699.5121 0.0) (800.0 0.0 0.0) (-800.0 0.0 0.0)))
  ("LW" nil ((-109.9798 660.0 0.0) (-109.9798 1340.0 0.0)))
  ("LW" nil ((-89.9798 1340.0 0.0) (-89.9798 660.0 0.0)))
  ("ARC" -94.9798 1275.0581 33.9986 2.02772569 4.25545962)
  ("ARC" -104.9798 1275.0581 33.9986 5.16931834 1.11386697)
  ("ARC" -104.9798 724.9419 33.9986 5.16931834 1.11386697)
  ("ARC" -94.9798 724.9419 33.9986 2.02772569 4.25545962)
  ("ARC" -99.9798 1340.0 10.0 0.0 3.14159265)
  ("ARC" -99.9798 660.0 10.0 3.14159265 0.0)
  ("ARC" 90.0202 660.0 10.0 3.14159265 0.0)
  ("ARC" 90.0202 1340.0 10.0 0.0 3.14159265)
  ("ARC" 85.0202 724.9419 33.9986 5.16931834 1.11386697)
  ("ARC" 95.0202 724.9419 33.9986 2.02772569 4.25545962)
  ("ARC" 95.0202 1275.0581 33.9986 2.02772569 4.25545962)
  ("ARC" 85.0202 1275.0581 33.9986 5.16931834 1.11386697)
  ("LW" nil ((80.0202 1340.0 0.0) (80.0202 660.0 0.0)))
  ("LW" nil ((100.0202 660.0 0.0) (100.0202 1340.0 0.0)))
  ("LW" T ((96.8711 19.9527 0.0) (85.5314 19.9527 -3.732051) (85.5314 29.9527 0.0) (96.8711 29.9527 -1.0)))
  ("LW" T ((0.0 52.0 0.0) (165.0 52.0 0.0) (165.0 0.0 0.0) (0.0 0.0 0.0)))
  ("LW" T ((-96.8693 19.9527 -0.0) (-85.5296 19.9527 3.732051) (-85.5296 29.9527 -0.0) (-96.8693 29.9527 1.0)))
  ("LW" T ((0.0018 52.0 -0.0) (-164.9982 52.0 -0.0) (-164.9982 0.0 -0.0) (0.0018 0.0 -0.0)))
))
(princ)
