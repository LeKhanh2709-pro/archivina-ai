;;; FILE SINH TỰ ĐỘNG từ vkmd_nguon.lsp bằng scripts\gop_vkmd.py — KHÔNG SỬA TAY.
;;; Chữ có dấu trong chuỗi đã đổi thành mã \U+XXXX để hiện đúng với cả LISPSYS = 0 và 1.
;;; VKMD.lsp — Dựng mặt đứng vách kính từ block mặt bằng "VACH KINH <dài>" do lệnh VK tạo (Archivina)
;;; Lệnh: MDVK (người dùng chốt tên 29/10/2026)
;;;   Quét chọn vùng mặt bằng (Enter = cả bản vẽ) -> lệnh TỰ NHẬN mọi vách kính: block do VK tạo và cả vách vẽ tay
;;;   (block tên tuỳ ý, đố có thể nằm rời; người dùng yêu cầu 30/10/2026, mẫu file mau\ACAD-CT VACH KINH.dxf)
;;;   -> nhận loại vách (cửa đi / cửa sổ / kính) -> bảng hỏi chung -> mặt đứng đặt NGAY TRÊN mỗi vách.
;;; Quy tắc (người dùng chốt 29/10/2026):
;;;   - Vị trí đố đứng, cửa sổ, cửa đi đọc từ block mặt bằng; thứ tự trái / phải giữ đúng như mặt bằng.
;;;   - Đố đứng, khung trên, khung dưới, đố ngang rộng 65; đố đứng chạy suốt, thanh ngang vẽ giữa 2 mặt đố.
;;;   - Vách cửa đi: khung dưới (trừ ô cửa đi) + khung trên + 1 đố ngang ở đỉnh cửa (mặt dưới đố = cao cửa),
;;;     chạy suốt vách. Cao cửa nhập tay. Vách không có cả cửa sổ lẫn cửa đi.
;;;   - Vách cửa sổ: khung trên / dưới; đố dưới cửa sổ CHỈ trong ô cửa sổ. Mép dưới cánh LUÔN = sàn hoàn thiện +
;;;     bậu (vd. 50 + 1400) (người dùng chốt 29/10/2026, kể cả vách ngắn / thấp). Có / không thanh ngang trên cửa sổ:
;;;       có    -> cao cửa sổ nhập tay; thanh ngang chạy suốt vách ngay trên cửa sổ (mặt dưới thanh = mép dưới
;;;                cánh + cao cửa sổ);
;;;       không -> cửa sổ lên sát mép dưới khung trên, cao cửa sổ TỰ TÍNH = cao vách - 65 - (sàn + bậu).
;;;     Vách kính không cửa: cùng bảng hỏi, thanh ngang đặt như vách cửa sổ (thẳng hàng với vách cửa sổ bên cạnh).
;;;   - Ký hiệu kính 3 vạch (block VKMD_KyHieuKinh, layer A-Window) đặt giữa mỗi ô kính; không ghi chữ FIX.
;;;   - Hình mặt đứng + kích thước "dim cua" (layer A-Dimension) + nét cắt 1-1 (qua ô cửa) và 2-2 (giữa chiều cao
;;;     cửa) như mẫu CT3 (ký hiệu layer A-Symbol, đường cắt layer A-Hidden) gom TẤT CẢ vào 1 block
;;;     "MAT DUNG VK <dài>x<cao>", chèn trên layer A-Window (người dùng chốt 29/10/2026, thay cho dim ngoài block).
;;;     Ghi chú, tên vách người dùng tự thêm.
;;; Hình cửa sổ / cửa đi lấy theo block người dùng cấp (file mau\block vach kinh\ACAD-md *.dxf), nhúng sẵn ở cuối
;;; file (scripts\tao_du_lieu_md.py) -> chép 1 file VKMD.lsp sang máy khác là chạy được.
;;; Tên hàm giữ tiền tố vkmd: (file VKMD.lsp); tên lệnh là MDVK.
;;; Yêu cầu: AutoCAD 2021+, bản vẽ có block mặt bằng do VK.lsp tạo. Không xoá, không sửa đối tượng có sẵn.

(vl-load-com)

;;; ---------------------------------------------------------------- thông số
;;;   vkmd:do: bề rộng đố / thanh ngang; vkmd:so-goc / vkmd:di-goc: tâm-tâm mặc định cửa trong block mặt bằng
;;;   vkmd:dim-*: khoảng cách đường dim tới mép mặt đứng; vkmd:dim-ho-*: khoảng hở từ mép mặt đứng tới đầu
;;;   đường gióng (đo theo mẫu VK01 trong CT3)
(setq vkmd:do 65.0
      vkmd:so-goc 1000.0
      vkmd:di-goc 1665.0
      vkmd:dim-ngang-chuoi 200.0
      vkmd:dim-ngang-tong 335.0
      vkmd:dim-dung-chuoi 365.0
      vkmd:dim-dung-tong 485.0
      vkmd:dim-ho-ngang 80.0
      vkmd:dim-ho-dung 240.0
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
  ;; cỡ ký hiệu kính (cạnh khung bao) để thu nhỏ khi ô kính nhỏ
  (setq vkmd:kinh-co (* 2.0 (apply 'max (mapcar 'abs (apply 'append (mapcar 'cdr vkmd:dl-kinh))))))
  ;; ký hiệu "///" lấy từ block cửa đi, tên block mới VKMD_KyHieuKinh (bản cũ VKMD_Kinh là "\\\" hoặc rỗng);
  ;; có mà RỖNG thì định nghĩa lại
  (if (or (not (tblsearch "BLOCK" "VKMD_KyHieuKinh")) (not (cdr (assoc -2 (tblsearch "BLOCK" "VKMD_KyHieuKinh")))))
    (progn
      (entmake '((0 . "BLOCK") (2 . "VKMD_KyHieuKinh") (70 . 0) (10 0.0 0.0 0.0)))
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
  (and (tblsearch "BLOCK" "VKMD_KyHieuKinh") (tblsearch "BLOCK" "VKMD_Cat11") (tblsearch "BLOCK" "VKMD_Cat22"))
)

;;; ---------------------------------------------------------------- đọc block mặt bằng
;;; Bề rộng tâm-tâm cửa theo tên block: VK_CuaDi -> mặc định, VK_CuaDi_1500 -> 1500, VK_CuaSoMo_1058_75 -> 1058.75
(defun vkmd:rong-ten (n goc mac-dinh)
  (if (= n goc)
    mac-dinh
    (distof (vl-string-translate "_" "." (substr n (+ 2 (strlen goc)))) 2))
)

;;; e: bản chèn block "VACH KINH ..." trên mặt bằng.
;;; Trả về (L o tam pt ux uy): o = ((loai rong) ...) theo thứ tự đi từ đầu vách; tam = tâm đố; pt = mép ngoài đầu
;;; vách trong WCS (= điểm chèn, trừ khi đã kéo grip đầu vách);
;;; (ux uy) = hướng trục vách trong WCS. Lỗi -> chuỗi.
(defun vkmd:doc-vach (e / ed ten b n x tam mo w i c loai o kq sx g pt dx)
  (setq ed (entget e))
  (cond
    ((/= "INSERT" (cdr (assoc 0 ed))) "\\U+0110\\U+1ED1i t\\U+01B0\\U+1EE3ng ch\\U+1ECDn kh\\U+00F4ng ph\\U+1EA3i block")
    ;; vách do VK tạo: có XData "ARCHIVINA_VK" (tên block người dùng tự đặt được từ 29/10/2026), hoặc vách
    ;; bản cũ tên gốc "VACH KINH ..."; vách đã kéo grip (*Uxx) xét tên gốc (EffectiveName), đọc nội dung *Uxx
    ((not (or (assoc -3 (entget e '("ARCHIVINA_VK")))
              (wcmatch (strcase (vla-get-EffectiveName (vlax-ename->vla-object e))) "VACH KINH*")))
     (strcat "Block \"" (vla-get-EffectiveName (vlax-ename->vla-object e))
             "\" kh\\U+00F4ng ph\\U+1EA3i block v\\U+00E1ch k\\U+00EDnh do l\\U+1EC7nh VK t\\U+1EA1o"))
    (T
     (setq ten (cdr (assoc 2 ed))
           b (cdr (assoc -2 (tblsearch "BLOCK" ten))))
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
     (setq tam (reverse kq)
           sx (cdr (assoc 41 ed)) g (cdr (assoc 50 ed))
           pt (cdr (assoc 10 ed)))
     ;; vách đã kéo grip ĐẦU (bản *Uxx): điểm chèn giữ nguyên, đầu vách dời dx -> đưa đố / cửa về gốc 0 và
     ;; dời điểm đầu vách theo trục vách (người dùng cho kéo 2 đầu 29/10/2026)
     (if (and tam (= "*" (substr ten 1 1)))
       (progn
         (setq dx (- (car tam) (/ vkmd:do 2.0))
               tam (mapcar '(lambda (c) (- c dx)) tam)
               mo (mapcar '(lambda (m) (list (car m) (- (cadr m) dx) (caddr m))) mo)
               pt (list (+ (car pt) (* dx (if (< sx 0) -1.0 1.0) (cos g)))
                        (+ (cadr pt) (* dx (if (< sx 0) -1.0 1.0) (sin g)))
                        (caddr pt)))))
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
        (list (+ (last tam) (/ vkmd:do 2.0)) (reverse o) tam pt
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
;;; H cao vách (từ chân vách = mặt sàn kết cấu); hd cao cửa đi; hs cao cửa sổ (cánh, lọt lòng; chỉ dùng khi có
;;; thanh ngang, không thì tự tính); co T = có thanh ngang trên cửa sổ; san dày sàn hoàn thiện; bau cao bậu
;;; (sàn hoàn thiện -> mép dưới cánh).
;;; Trả về (loai ngang so hd chuoi): ngang = (y1 y2) đố ngang chạy suốt hoặc nil; so = (y-đáy-đố-dưới y-đỉnh-đố-dưới
;;; y-đỉnh-cánh) hoặc nil; chuoi = cao độ các điểm dim đứng từ dưới lên. Lỗi -> chuỗi.
(defun vkmd:tinh (vach H hd hs co san bau / loai d nua y1 yt ngang so)
  (setq loai (vkmd:loai vach) d vkmd:do nua (/ vkmd:do 2.0))
  (cond
    ((or (not H) (<= H (* 3 d))) "Nh\\U+1EADp chi\\U+1EC1u cao v\\U+00E1ch")
    ((= loai "D")
     (cond
       ((or (not hd) (<= hd 0)) "Nh\\U+1EADp chi\\U+1EC1u cao c\\U+1EEDa \\U+0111i")
       ((> hd (+ H 1e-6)) (strcat "C\\U+1EEDa \\U+0111i cao " (vkmd:so hd) " > v\\U+00E1ch " (vkmd:so H)))
       ;; không đủ chỗ thanh ngang (cửa + 65 + khung trên 65 > vách, vd. cửa = vách): bỏ thanh ngang, đỉnh cửa sát
       ;; dưới khung trên, cửa cao = vách - 65 (người dùng chốt 29/10/2026)
       ((> (+ hd d d) (+ H 1e-6)) (list loai nil nil (- H d) (list 0.0 nua (- H nua) H)))
       ;; không giới hạn cao cửa: người dùng tự quy định (chốt 29/10/2026); cửa thấp thì hình cửa co theo tỉ lệ
       (T (list loai (list hd (+ hd d)) nil hd (list 0.0 nua (+ hd nua) (- H nua) H)))))
    ((and co (or (not hs) (<= hs 0))) "Nh\\U+1EADp chi\\U+1EC1u cao c\\U+1EEDa s\\U+1ED5")
    ((and (or (= loai "S") co) (or (not san) (< san 0))) "Nh\\U+1EADp chi\\U+1EC1u d\\U+00E0y s\\U+00E0n ho\\U+00E0n thi\\U+1EC7n (0 n\\U+1EBFu kh\\U+00F4ng c\\U+00F3)")
    ((and (or (= loai "S") co) (or (not bau) (<= bau 0))) "Nh\\U+1EADp cao b\\U+1EADu c\\U+1EEDa s\\U+1ED5")
    (T
     ;; mép dưới cánh luôn = sàn + bậu; có thanh ngang: đỉnh cửa = bậu + cao cửa sổ, thanh ngang ngay trên;
     ;; không: cửa sổ lên sát khung trên (cao cửa sổ tự tính)
     (if (or (= loai "S") co) (setq y1 (+ san bau)))
     (if co
       (setq yt (+ y1 hs) ngang (list yt (+ yt d)))
       (setq yt (- H d)))
     (if (= loai "S")
       (setq so (list (- y1 d) y1 yt)))
     (cond
       ((and ngang (> (cadr ngang) (- H d 1e-6)))
        (strcat "Thanh ngang ch\\U+1EA1m khung tr\\U+00EAn: s\\U+00E0n + b\\U+1EADu + c\\U+1EEDa s\\U+1ED5 + 65 = " (vkmd:so (cadr ngang))
                " > " (vkmd:so (- H d)) " (b\\U+1ECF thanh ngang ho\\U+1EB7c gi\\U+1EA3m s\\U+1ED1 \\U+0111o)"))
       ((and so (<= (- yt y1) 0))
        (strcat "V\\U+00E1ch th\\U+1EA5p qu\\U+00E1: s\\U+00E0n + b\\U+1EADu = " (vkmd:so y1) " >= m\\U+00E9p d\\U+01B0\\U+1EDBi khung tr\\U+00EAn " (vkmd:so (- H d))))
       ((and so (< (car so) (- d 1e-6)))
        (strcat "\\U+0110\\U+1ED1 d\\U+01B0\\U+1EDBi c\\U+1EEDa s\\U+1ED5 ch\\U+1EA1m khung d\\U+01B0\\U+1EDBi: s\\U+00E0n + b\\U+1EADu ph\\U+1EA3i >= " (vkmd:so (* 2 d))))
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
;;; Cửa thấp (cao <= 1499,51) / hẹp (lọt lòng <= 840) không đủ chỗ giữ nguyên tay nắm -> co CẢ hình theo tỉ lệ
;;; chiều đó (vkmd:kx / vkmd:ky), không báo lỗi (người dùng chốt 29/10/2026: cao cửa do người dùng quy định).
(defun vkmd:fx (x / a)
  (if vkmd:kx
    (* x vkmd:kx)
    (progn
      (setq a (abs x))
      (* (if (< x 0) -1.0 1.0)
         (cond ((<= a 200.0) a) ((>= a 580.0) (+ a vkmd:dx)) (T (+ 200.0 (* (- a 200.0) (/ (+ 380.0 vkmd:dx) 380.0)))))))))

(defun vkmd:fy (y)
  (cond (vkmd:ky (* y vkmd:ky))
        ((<= y 1400.0) y) ((>= y 2600.0) (+ y vkmd:dy)) (T (+ 1400.0 (* (- y 1400.0) (/ (+ 1200.0 vkmd:dy) 1200.0)))))
)

(defun vkmd:cua-di (xa xb hd / cx x)
  (setq cx (/ (+ xa xb) 2.0) vkmd:dx (/ (- (- xb xa) vkmd:dl-di-rong) 2.0) vkmd:dy (- hd vkmd:dl-di-cao)
        vkmd:kx (if (<= (+ 380.0 vkmd:dx) 0.0) (/ (- xb xa) vkmd:dl-di-rong))
        vkmd:ky (if (<= (+ 1200.0 vkmd:dy) 0.0) (/ hd vkmd:dl-di-cao)))
  (foreach x vkmd:dl-cua-di
    (cond
      ((= (car x) "LW")
       (vkmd:lw (mapcar '(lambda (p) (list (+ cx (vkmd:fx (car p))) (vkmd:fy (cadr p)) (caddr p))) (caddr x))
                (cadr x) vkmd:layer nil))
      ((= (car x) "LINE")
       (vkmd:line (+ cx (vkmd:fx (nth 1 x))) (vkmd:fy (nth 2 x)) (+ cx (vkmd:fx (nth 3 x))) (vkmd:fy (nth 4 x)) vkmd:layer nil))
      ((= (car x) "ARC")
       (entmake (list '(0 . "ARC") (cons 8 vkmd:layer) (list 10 (+ cx (vkmd:fx (nth 1 x))) (vkmd:fy (nth 2 x)) 0.0)
                      (cons 40 (* (nth 3 x) (min (if vkmd:kx vkmd:kx 1.0) (if vkmd:ky vkmd:ky 1.0))))
                      (cons 50 (nth 4 x)) (cons 51 (nth 5 x)))))))
  ;; giữ nguyên thông tin block cửa đi (người dùng chốt 29/10/2026): ký hiệu kính, kích thước, ghi chú
  ;; đặt theo vị trí trong block, kéo giãn theo rộng / cao cửa
  (foreach x vkmd:dl-di-kinh
    (vkmd:chen "VKMD_KyHieuKinh" (+ cx (vkmd:fx (car x))) (vkmd:fy (cadr x)) 1.0 1.0 0.0 vkmd:layer))
  (foreach x vkmd:dl-di-dim
    (vkmd:dim (list (+ cx (vkmd:fx (nth 2 x))) (vkmd:fy (nth 3 x))) (list (+ cx (vkmd:fx (nth 4 x))) (vkmd:fy (nth 5 x)))
              (list (+ cx (vkmd:fx (nth 6 x))) (vkmd:fy (nth 7 x))) (nth 1 x) (car x)))
  (foreach x vkmd:dl-di-chu
    (vkmd:ghi-chu (car x) (+ cx (vkmd:fx (nth 1 x))) (vkmd:fy (nth 2 x)) (+ cx (vkmd:fx (nth 3 x))) (vkmd:fy (nth 4 x))
                  (nth 5 x) (nth 6 x) (nth 7 x)))
)

;;; Ghi chú MLEADER (kiểu MLEADER hiện hành), mũi tên tại (x1 y1), chữ tại (x2 y2). Lỗi -> báo, không dừng lệnh.
(defun vkmd:ghi-chu (s x1 y1 x2 y2 h kieu lop / r)
  (setq r (vl-catch-all-apply
            '(lambda (/ pts ml)
               (setq pts (vlax-make-safearray vlax-vbDouble '(0 . 5)))
               (vlax-safearray-fill pts (list x1 y1 0.0 x2 y2 0.0))
               (setq ml (vla-AddMLeader (vla-get-Block (vla-get-ActiveLayout (vla-get-ActiveDocument (vlax-get-acad-object))))
                                        (vlax-make-variant pts) 0))
               (vla-put-TextString ml s)
               (vla-put-TextHeight ml h)
               (vla-put-ArrowheadSize ml 25.0)
               (if (tblsearch "STYLE" kieu) (vla-put-TextStyleName ml kieu))
               (vla-put-Layer ml lop))))
  (if (vl-catch-all-error-p r)
    (princ (strcat "\nMDVK: kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c ghi ch\\U+00FA \"" s "\": " (vl-catch-all-error-message r))))
)

;;; Ký hiệu kính giữa ô kính rộng w, cao h: thu nhỏ nếu ô nhỏ hơn ký hiệu (chiếm tối đa 80 % cạnh ngắn)
(defun vkmd:kinh (x y w h / k)
  (setq k (min 1.0 (/ (* 0.8 (min w h)) vkmd:kinh-co)))
  (if (> k 0.1) (vkmd:chen "VKMD_KyHieuKinh" x y k k 0.0 vkmd:layer))
)

(defun vkmd:cua-so (xa xb y1 y2 / m)
  (setq m (list (cons 62 vkmd:dl-so-mau)))
  (vkmd:lw (list (list xa y1) (list xb y1) (list xb y2) (list xa y2)) T vkmd:layer m)
  ;; tam giác hướng mở: đỉnh giữa cạnh trên (bản lề trên, cửa hất), nét khuất như block người dùng cấp
  (foreach x (list xa xb)
    (vkmd:line (/ (+ xa xb) 2.0) y2 x y1 vkmd:layer
               (append m (if (tblsearch "LTYPE" vkmd:dl-so-net)
                           (list (cons 6 vkmd:dl-so-net) (cons 48 vkmd:dl-so-net-tile))))))
  (vkmd:kinh (/ (+ xa xb) 2.0) (/ (+ y1 y2) 2.0) (- xb xa) (- y2 y1))
)

;;; Dựng hình mặt đứng tạm tại gốc toạ độ (góc dưới trái = 0,0) trong không gian hiện hành; vkmd:gom gom lại sau.
(defun vkmd:dung (vach kq H / L o tam loai ngang so hd d nua i xa xb x b k bars)
  (setq L (car vach) o (cadr vach) tam (caddr vach)
        loai (car kq) ngang (cadr kq) so (caddr kq) hd (nth 3 kq) d vkmd:do nua (/ vkmd:do 2.0))
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
      (if (and (> (- (cadr b) (car b)) 0.0)
               (not (and so (= (car x) "S") (equal (car b) (cadr so) 0.01))))
        (vkmd:kinh (/ (+ xa xb) 2.0) (/ (+ (car b) (cadr b)) 2.0) (- xb xa) (- (cadr b) (car b))))
      (setq k (1+ k)))
    (setq i (1+ i)))
)

;;; Gom mọi đối tượng tạo sau `dau` (hình + dim + nét cắt) thành block `ten` gốc 0,0, chèn tại pt (layer A-Window).
;;; Trả về tên block hoặc nil. Cách gom giống lệnh VK: AutoCAD 2027 -BLOCK đổi luôn đối tượng thành 1 bản chèn tại
;;; 0,0 -> dời bản chèn đó tới pt; bản cũ thì xoá đối tượng -> chèn mới.
(defun vkmd:gom (dau ten pt / ss e ed cuoi)
  (setq ss (ssadd) e (if dau (entnext dau) (entnext)))
  (while e (ssadd e ss) (setq e (entnext e)))
  (setq cuoi (entlast))
  (command "_.-BLOCK" ten "_non" '(0.0 0.0 0.0) ss "")
  (if (tblsearch "BLOCK" ten)
    (progn
      (setq ed (entget (entlast)))
      (if (and (not (equal cuoi (entlast))) (= "INSERT" (cdr (assoc 0 ed))) (= ten (cdr (assoc 2 ed))))
        (entmod (subst (cons 10 pt) (assoc 10 ed) (subst (cons 8 vkmd:layer) (assoc 8 ed) ed)))
        (vkmd:chen ten (car pt) (cadr pt) 1.0 1.0 0.0 vkmd:layer))
      ten))
)

(defun vkmd:dim (p q loc huong lop / e ed)
  (command "_.DIMLINEAR" "_non" p "_non" q huong "_non" loc)
  (if (and (setq e (entlast)) (= "DIMENSION" (cdr (assoc 0 (setq ed (entget e))))))
    (entmod (subst (cons 8 lop) (assoc 8 ed) ed)))
)

;;; Kích thước kiểm tra: chuỗi đố + tổng ở dưới, chuỗi cao độ + tổng bên phải. Đường gióng bắt đầu cách đối tượng
;;; một khoảng (người dùng chốt 29/10/2026, theo mẫu VK01: dưới 80, phải 240).
(defun vkmd:kich-thuoc (vach kq H x0 y0 / L a b yg xg)
  (setq L (car vach) yg (- y0 vkmd:dim-ho-ngang) xg (+ x0 L vkmd:dim-ho-dung) a 0.0)
  (foreach b (append (caddr vach) (list L))
    (vkmd:dim (list (+ x0 a) yg) (list (+ x0 b) yg) (list (+ x0 (/ (+ a b) 2.0)) (- y0 vkmd:dim-ngang-chuoi))
              "_H" vkmd:layer-dim)
    (setq a b))
  (vkmd:dim (list x0 yg) (list (+ x0 L) yg) (list (+ x0 (/ L 2.0)) (- y0 vkmd:dim-ngang-tong)) "_H" vkmd:layer-dim)
  (setq a nil)
  (foreach b (nth 4 kq)
    (if a (vkmd:dim (list xg (+ y0 a)) (list xg (+ y0 b))
                    (list (+ x0 L vkmd:dim-dung-chuoi) (+ y0 (/ (+ a b) 2.0))) "_V" vkmd:layer-dim))
    (setq a b))
  (vkmd:dim (list xg y0) (list xg (+ y0 H)) (list (+ x0 L vkmd:dim-dung-tong) (+ y0 (/ H 2.0))) "_V" vkmd:layer-dim)
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

;;; Sau khi dựng mặt đứng (người dùng yêu cầu 29/10/2026, theo ảnh mẫu): dim kiểm tra trong block MẶT BẰNG ->
;;; layer A-Dimension, DƯỚI mặt bằng, cách đối tượng như dim mặt đứng (gióng 80, chuỗi 200, tổng 335 từ mép ngoài
;;; cùng của vách phía đó, tính cả cung mở cánh cửa đi).
;;;   - Chuỗi dim DỰNG LẠI theo đố thật đang có trong block (người dùng sửa tay block - thêm / dời đố - thì dim
;;;     theo đúng; báo lỗi 29/10/2026: dim cũ không cập nhật). Dim cũ bỏ hết, vẽ lại bằng vla (sửa tại chỗ bằng
;;;     entmod không ăn trong AutoCAD của người dùng). Dim mới không nằm trong Stretch action: kéo grip thì VK.lsp
;;;     vẽ lại dim theo phía đã ghi trong XData.
;;;   - "Dưới" theo hướng thật trên bản vẽ: phía trục y block có thành phần Y thế giới âm (vách đứng: phía -X).
;;;   - Sửa định nghĩa block mà bản chèn đang dùng (block gốc hoặc bản *U đã kéo grip).
;;;   - Ghi phía đặt dim vào phần tử thứ 9 XData "ARCHIVINA_VK" -> VK.lsp vẽ lại dim đúng kiểu này khi kéo grip.
;;; Trả về chuỗi báo.
(defun vkmd:dim-mat-bang (e / ed g s42 ben blk dims lo hi mn mx m tam n c w kq diem doan kieu
                             yg i xd moi ma gt bo)
  (setq ed (entget e) g (cdr (assoc 50 ed))
        s42 (if (and (assoc 42 ed) (< (cdr (assoc 42 ed)) 0)) -1.0 1.0)
        ben (cond ((> (* (cos g) s42) 1e-6) -1)
                  ((< (* (cos g) s42) -1e-6) 1)
                  ((> (* (sin g) s42) 0) 1)
                  (T -1))
        blk (vla-Item (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))) (cdr (assoc 2 ed)))
        lo 0.0 hi 0.0)
  ;; dim có sẵn, mép ngoài cùng (không tính dim) và tâm đố thật (toạ độ trong block)
  (vlax-for x blk
    (cond
      ((wcmatch (vla-get-ObjectName x) "*Dimension") (setq dims (cons x dims)))
      (T
       (if (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-GetBoundingBox (list x 'mn 'mx))))
         (setq lo (min lo (cadr (vlax-safearray->list mn))) hi (max hi (cadr (vlax-safearray->list mx)))))
       (if (= "AcDbBlockReference" (vla-get-ObjectName x))
         (progn
           (setq n (strcase (vla-get-Name x)) c (car (vlax-get x 'InsertionPoint)))
           (cond
             ((= n "VK_DODUNG") (setq tam (cons c tam)))
             ((wcmatch n "VK_CUASOMO*")
              (setq w (vkmd:rong-ten n "VK_CUASOMO" vkmd:so-goc) tam (cons c (cons (+ c w) tam))))
             ((wcmatch n "VK_CUADI*")
              (setq w (vkmd:rong-ten n "VK_CUADI" vkmd:di-goc) tam (cons c (cons (+ c w) tam))))))))))
  (setq tam (vl-sort tam '<) kq nil)
  (foreach c tam (if (not (and kq (equal c (car kq) 0.01))) (setq kq (cons c kq))))
  (setq tam (reverse kq))
  (if (< (length tam) 2)
    "kh\\U+00F4ng th\\U+1EA5y \\U+0111\\U+1ED1 trong block m\\U+1EB7t b\\U+1EB1ng, gi\\U+1EEF nguy\\U+00EAn dim"
    (progn
      ;; điểm chuỗi: mép đầu vách, các tâm đố, mép cuối vách
      (setq diem (append (list (- (car tam) (/ vkmd:do 2.0))) tam (list (+ (last tam) (/ vkmd:do 2.0))))
            i 0)
      (repeat (1- (length diem)) (setq doan (cons (list (nth i diem) (nth (1+ i) diem)) doan) i (1+ i)))
      (setq doan (reverse doan)
            m (if (> ben 0) hi lo)
            yg (+ m (* ben vkmd:dim-ho-ngang))
            kieu (cond ((tblsearch "DIMSTYLE" vkmd:dimstyle) vkmd:dimstyle) (dims (vla-get-StyleName (car dims)))))
      ;; bỏ hết dim kiểm tra cũ rồi vẽ lại bằng vla: bản sửa tại chỗ (entmod) trong AutoCAD của người dùng không
      ;; đổi được dim (dim cũ đứng yên chỗ cũ, chỉ dim thêm mới hiện đúng; báo 29/10/2026)
      (setq bo 0)
      (foreach x dims
        (if (vl-catch-all-error-p (vl-catch-all-apply 'vla-Delete (list x))) (setq bo (1+ bo))))
      (foreach s doan (vkmd:them-dim blk (car s) (cadr s) yg (+ m (* ben vkmd:dim-ngang-chuoi)) kieu))
      (vkmd:them-dim blk (car diem) (last diem) yg (+ m (* ben vkmd:dim-ngang-tong)) kieu)
      ;; phía đặt dim -> phần tử thứ 9 của XData (vách bản cũ không có XData thì thôi)
      (if (setq xd (cdr (assoc "ARCHIVINA_VK" (cdr (assoc -3 (entget e '("ARCHIVINA_VK")))))))
        (progn
          (setq moi (append (list (cons 1001 "ARCHIVINA_VK"))
                            (if (> (length xd) 8) (reverse (cdr (reverse xd))) xd)
                            (list (cons 1070 ben)))
                ma (vlax-make-safearray vlax-vbInteger (cons 0 (1- (length moi))))
                gt (vlax-make-safearray vlax-vbVariant (cons 0 (1- (length moi)))))
          (vlax-safearray-fill ma (mapcar 'car moi))
          (vlax-safearray-fill gt (mapcar '(lambda (p) (vlax-make-variant (cdr p))) moi))
          (vla-SetXData (vlax-ename->vla-object e) ma gt)))
      (vla-Update (vlax-ename->vla-object e))
      (strcat "dim m\\U+1EB7t b\\U+1EB1ng v\\U+1EBD l\\U+1EA1i " (itoa (length doan)) " \\U+0111o\\U+1EA1n + t\\U+1ED5ng " (vkmd:so (- (last diem) (car diem)))
              " (A-Dimension, d\\U+01B0\\U+1EDBi m\\U+1EB7t b\\U+1EB1ng)"
              (if (> bo 0) (strcat " - " (itoa bo) " dim c\\U+0169 kh\\U+00F4ng xo\\U+00E1 \\U+0111\\U+01B0\\U+1EE3c (layer b\\U+1ECB kho\\U+00E1?)") ""))))
)

;;; Thêm 1 dim ngang p..q vào block blk: gióng bắt đầu ở yg, đường dim ở y, kiểu kieu, layer A-Dimension
(defun vkmd:them-dim (blk p q yg y kieu / x)
  (setq x (vla-AddDimRotated blk (vlax-3d-point p yg 0.0) (vlax-3d-point q yg 0.0)
                             (vlax-3d-point (/ (+ p q) 2.0) y 0.0) 0.0))
  (if kieu (vla-put-StyleName x kieu))
  (vla-put-Layer x vkmd:layer-dim)
)

;;; Chạy đủ (dùng chung cho lệnh MDVK và chạy thử không hộp thoại).
;;; e: bản chèn block mặt bằng; pt: điểm đặt (nil -> hỏi). Vách nằm ngang trên mặt bằng: mặt đứng thẳng hàng
;;; theo X với mặt bằng, chỉ lấy cao độ Y của điểm chọn; vách xiên: góc dưới trái mặt đứng = điểm chọn.
(defun vkmd:thuc-hien (e H hd hs co san bau pt / *error* bien cu undo ucs vach kq ngang nguoc x0 y0 ten dau ds-cu r)
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
  ;; nhiều vách một lần: vkmd:chay-het đã mở một nhóm undo chung
  (if (and (not *vkmd-mot-nhom*) (setq undo (vkmd:undo-ok))) (command "_.UNDO" "_BE"))
  (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
  ;; e: bản chèn vách do VK tạo, hoặc danh sách vách đã nhận từ hình vẽ tay (vkmd:tao-vach)
  (setq vach (if (= 'ENAME (type e)) (vkmd:doc-vach e) e))
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
           ((not (and vkmd:dl-kinh vkmd:dl-cua-di))
            (princ "\nMDVK: thi\\U+1EBFu d\\U+1EEF li\\U+1EC7u block nh\\U+00FAng (VKMD.lsp n\\U+1EA1p kh\\U+00F4ng h\\U+1EBFt) - APPLOAD l\\U+1EA1i b\\U+1EA3n m\\U+1EDBi."))
           ((not (vkmd:block-phu)) (princ "\nMDVK: kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c block k\\U+00FD hi\\U+1EC7u."))
           (T
            ;; dựng hình + dim + nét cắt tại gốc toạ độ rồi gom thành 1 block, chèn tại (x0 y0)
            (setq dau (entlast) ds-cu (getvar "DIMSTYLE"))
            ;; kiểu dim "dim cua" cho cả kích thước của cửa đi lẫn kích thước kiểm tra
            (if (tblsearch "DIMSTYLE" vkmd:dimstyle)
              (command "_.-DIMSTYLE" "_R" vkmd:dimstyle)
              (princ (strcat "\nKh\\U+00F4ng c\\U+00F3 ki\\U+1EC3u k\\U+00EDch th\\U+01B0\\U+1EDBc \"" vkmd:dimstyle "\": d\\U+00F9ng ki\\U+1EC3u hi\\U+1EC7n h\\U+00E0nh " ds-cu)))
            (vkmd:dung vach kq H)
            (vkmd:kich-thuoc vach kq H 0.0 0.0)
            (vkmd:net-cat vach kq H 0.0 0.0)
            (if (and (tblsearch "DIMSTYLE" ds-cu) (/= ds-cu (getvar "DIMSTYLE"))) (command "_.-DIMSTYLE" "_R" ds-cu))
            (setq ten (vkmd:gom dau (vkmd:ten-block (vl-string-translate "," "_" (strcat "MAT DUNG VK " (vkmd:so (car vach))
                                                                                          "x" (vkmd:so H))))
                                (list x0 y0 0.0)))
            ;; dim kiểm tra của mặt bằng -> A-Dimension, xuống dưới mặt bằng (chỉ vách do VK tạo; vách vẽ tay
            ;; không sửa)
            (if (and ten (= 'ENAME (type e)))
              (progn
                (setq r (vl-catch-all-apply 'vkmd:dim-mat-bang (list e)))
                (princ (strcat "
MDVK: " (if (vl-catch-all-error-p r)
                                               (strcat "l\\U+1ED7i khi s\\U+1EEDa dim m\\U+1EB7t b\\U+1EB1ng: " (vl-catch-all-error-message r))
                                               r)))))
            (princ (if ten
                     (strcat "\nMDVK: m\\U+1EB7t \\U+0111\\U+1EE9ng " (vkmd:so (car vach)) " x " (vkmd:so H)
                             " -> block " ten "\n    Cao \\U+0111\\U+1ED9 (t\\U+1EEB d\\U+01B0\\U+1EDBi l\\U+00EAn): " (vkmd:chuoi kq))
                     "\nMDVK: kh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c block m\\U+1EB7t \\U+0111\\U+1EE9ng."))))))))
  (if ucs (command "_.UCS" "_P"))
  (if undo (command "_.UNDO" "_E"))
  (mapcar 'setvar bien cu)
  (princ)
)

;;; ---------------------------------------------------------------- tự nhận vách kính vẽ tay
;;; Người dùng yêu cầu 30/10/2026 (mẫu file mau\ACAD-CT VACH KINH.dxf): MDVK nhận cả vách mặt bằng KHÔNG do VK tạo
;;; (block tên tuỳ ý, đố có thể nằm rời ngoài block, lồng nhiều cấp) rồi dựng mặt đứng ngay trên mỗi vách.
;;;   - Đố = bản chèn block có khung bao 55..80 x 120..300 mm (mẫu: 65,7 x 187,2, block "5345" / "6456"), ở mọi cấp
;;;     lồng; phương vách = cạnh ngắn của đố.
;;;   - Đố cùng phương, lệch trục <= 30, cách nhau <= 3000 tâm-tâm = một vách; đố trùng (cách < 10) bỏ bớt.
;;;   - Ô giữa 2 đố: có cung bán kính > 200 (cánh mở, mẫu r = 378; cung rời hoặc trong block có đố) hoặc block chứa cung đó nằm
;;;     trong ô -> cửa đi; có block khác (không phải đố) nằm trong ô, dài từ 1/2 ô tới ô + 2 đố (profile cánh / block
;;;     cửa sổ) -> cửa sổ; còn lại -> kính.
;;;   - Dài vách = mép ngoài đố đầu -> mép ngoài đố cuối (đo bề rộng đố thật).
;;; Toạ độ phẳng hoá bằng ma trận afin 2D m = (a b c d e f): x' = a x + b y + e, y' = c x + d y + f.
(setq vkmd:do-min 55.0 vkmd:do-max 80.0 vkmd:sau-min 120.0 vkmd:sau-max 300.0
      vkmd:khoang-max 3000.0 vkmd:lech-max 30.0 vkmd:cung-cua 200.0
      ;; mặt đứng (chân) cao hơn mép trên mặt bằng vách (trục + nửa cửa đi lớn nhất, tối thiểu 300) một khoảng này;
      ;; dim chuỗi + ký hiệu cắt 1-1 nằm dưới chân mặt đứng ~700
      vkmd:cach-mb 1000.0
      vkmd:m0 '(1.0 0.0 0.0 1.0 0.0 0.0))

(defun vkmd:m* (m n)
  (list (+ (* (nth 0 m) (nth 0 n)) (* (nth 1 m) (nth 2 n)))
        (+ (* (nth 0 m) (nth 1 n)) (* (nth 1 m) (nth 3 n)))
        (+ (* (nth 2 m) (nth 0 n)) (* (nth 3 m) (nth 2 n)))
        (+ (* (nth 2 m) (nth 1 n)) (* (nth 3 m) (nth 3 n)))
        (+ (* (nth 0 m) (nth 4 n)) (* (nth 1 m) (nth 5 n)) (nth 4 m))
        (+ (* (nth 2 m) (nth 4 n)) (* (nth 3 m) (nth 5 n)) (nth 5 m)))
)

(defun vkmd:mp (m p)
  (list (+ (* (nth 0 m) (car p)) (* (nth 1 m) (cadr p)) (nth 4 m))
        (+ (* (nth 2 m) (car p)) (* (nth 3 m) (cadr p)) (nth 5 m)))
)

;;; Đối tượng vẽ ngược mặt (pháp tuyến -Z): toạ độ OCS x đảo dấu
(defun vkmd:ocs (ed)
  (if (and (assoc 210 ed) (< (caddr (cdr (assoc 210 ed))) 0)) '(-1.0 0.0 0.0 1.0 0.0 0.0) vkmd:m0)
)

;;; Ma trận bản chèn: OCS . dời điểm chèn . xoay . tỉ lệ . trừ điểm gốc block
(defun vkmd:m-ins (ed / p r sx sy b)
  (setq p (cdr (assoc 10 ed)) r (cdr (assoc 50 ed)) sx (cdr (assoc 41 ed)) sy (cdr (assoc 42 ed))
        b (cdr (assoc 10 (tblsearch "BLOCK" (cdr (assoc 2 ed))))))
  (if (not r) (setq r 0.0))
  (if (not sx) (setq sx 1.0))
  (if (not sy) (setq sy 1.0))
  (if (not b) (setq b '(0.0 0.0 0.0)))
  (vkmd:m* (vkmd:ocs ed)
           (vkmd:m* (list (* (cos r) sx) (- (* (sin r) sy)) (* (sin r) sx) (* (cos r) sy) (car p) (cadr p))
                    (list 1.0 0.0 0.0 1.0 (- (car b)) (- (cadr b)))))
)

(defun vkmd:goc4 (k)
  (list (list (nth 0 k) (nth 1 k)) (list (nth 2 k) (nth 1 k)) (list (nth 2 k) (nth 3 k)) (list (nth 0 k) (nth 3 k))))

;;; Khung bao (xmin ymin xmax ymax) của danh sách điểm, rỗng -> nil
(defun vkmd:bao (pts)
  (if pts
    (list (apply 'min (mapcar 'car pts)) (apply 'min (mapcar 'cadr pts))
          (apply 'max (mapcar 'car pts)) (apply 'max (mapcar 'cadr pts))))
)

;;; Các góc cần lấy điểm để bao một cung / đường tròn ed
(defun vkmd:goc-cung (ed / a1 a2 kq g)
  (if (= "CIRCLE" (cdr (assoc 0 ed)))
    (list 0.0 (/ pi 2.0) pi (* 1.5 pi))
    (progn
      (setq a1 (cdr (assoc 50 ed)) a2 (cdr (assoc 51 ed)))
      (if (< a2 a1) (setq a2 (+ a2 (* 2 pi))))
      (setq kq (list a1 a2) g 0.0)
      (while (< g (* 4 pi))
        (if (< a1 g a2) (setq kq (cons g kq)))
        (setq g (+ g (/ pi 2.0))))
      kq))
)

(defun vkmd:xref-p (ten / b)
  (and (setq b (tblsearch "BLOCK" ten)) (= 4 (logand 4 (cdr (assoc 70 b))))))

;;; Thông tin block (nhớ theo tên trong một lần chạy, *vkmd-kt*): (khung-bao có-đố có-cung)
;;;   có-đố: block là đố hoặc chứa đố (ở cấp lồng bất kỳ); có-cung: chứa cung cánh cửa (bán kính > 200)
(defun vkmd:tt-block (ten / c e ed loai pts k co-do co-cung con r m)
  (cond
    ((setq c (assoc ten *vkmd-kt*)) (cdr c))
    ((or (vkmd:xref-p ten) (not (tblsearch "BLOCK" ten))) nil)
    (T
     ;; chặn đệ quy vòng
     (setq *vkmd-kt* (cons (list ten nil nil nil) *vkmd-kt*)
           e (cdr (assoc -2 (tblsearch "BLOCK" ten))))
     (while e
       (setq ed (entget e) loai (cdr (assoc 0 ed)) m (vkmd:ocs ed))
       (cond
         ((= loai "LINE") (setq pts (cons (cdr (assoc 10 ed)) (cons (cdr (assoc 11 ed)) pts))))
         ((= loai "LWPOLYLINE")
          (foreach p ed (if (= 10 (car p)) (setq pts (cons (vkmd:mp m (cdr p)) pts)))))
         ((member loai '("ARC" "CIRCLE"))
          ;; cung: đúng phần cung (2 đầu + điểm 0/90/180/270 độ nằm trong cung); tính cả đường tròn thì khung bao
          ;; đố mẫu thành 86 thay vì 65,7 (đố có cung nhỏ ở góc)
          (setq c (cdr (assoc 10 ed)) r (cdr (assoc 40 ed)))
          (foreach g (vkmd:goc-cung ed)
            (setq pts (cons (vkmd:mp m (list (+ (car c) (* r (cos g))) (+ (cadr c) (* r (sin g))))) pts)))
          (if (and (= loai "ARC") (> r vkmd:cung-cua)) (setq co-cung T)))
         ((and (= loai "INSERT") (setq con (vkmd:tt-block (cdr (assoc 2 ed)))) (car con))
          (setq m (vkmd:m-ins ed))
          (foreach p (vkmd:goc4 (car con)) (setq pts (cons (vkmd:mp m p) pts)))
          (if (or (vkmd:la-do (car con)) (cadr con)) (setq co-do T))
          (if (caddr con) (setq co-cung T))))
       (setq e (entnext e)))
     (setq k (list (vkmd:bao pts) co-do co-cung)
           *vkmd-kt* (cons (cons ten k) (vl-remove (assoc ten *vkmd-kt*) *vkmd-kt*)))
     k))
)

;;; Khung bao cỡ đố: cạnh ngắn 55..80, cạnh dài 120..300
(defun vkmd:la-do (k / a b)
  (if k
    (progn
      (setq a (- (nth 2 k) (nth 0 k)) b (- (nth 3 k) (nth 1 k)))
      (and (<= vkmd:do-min (min a b) vkmd:do-max) (<= vkmd:sau-min (max a b) vkmd:sau-max))))
)

;;; Duyệt đối tượng ed (ma trận m tới toạ độ thế giới, cấp lồng sau), ghi:
;;;   *vkmd-do*: 4 góc thế giới mỗi đố; *vkmd-khoi*: (4 góc . có-cung) mỗi block khác; *vkmd-cung*: điểm giữa cung cánh
;;; Chỉ đi vào block có chứa đố (block khác không liên quan vách kính).
(defun vkmd:quet (ed m sau / loai tt mi e c r a1 a2 am)
  (setq loai (cdr (assoc 0 ed)))
  (cond
    ((and (= loai "INSERT") (setq tt (vkmd:tt-block (cdr (assoc 2 ed)))) (car tt))
     (setq mi (vkmd:m* m (vkmd:m-ins ed)))
     (cond
       ((vkmd:la-do (car tt))
        (setq *vkmd-do* (cons (mapcar '(lambda (p) (vkmd:mp mi p)) (vkmd:goc4 (car tt))) *vkmd-do*)))
       (T
        (setq *vkmd-khoi* (cons (cons (mapcar '(lambda (p) (vkmd:mp mi p)) (vkmd:goc4 (car tt))) (caddr tt))
                                *vkmd-khoi*))
        (if (and (cadr tt) (< sau 8))
          (progn
            (setq e (cdr (assoc -2 (tblsearch "BLOCK" (cdr (assoc 2 ed))))))
            (while e (vkmd:quet (entget e) mi (1+ sau)) (setq e (entnext e))))))))
    ((and (= loai "ARC") (> (cdr (assoc 40 ed)) vkmd:cung-cua))
     (setq c (cdr (assoc 10 ed)) r (cdr (assoc 40 ed)) a1 (cdr (assoc 50 ed)) a2 (cdr (assoc 51 ed)))
     (if (< a2 a1) (setq a2 (+ a2 (* 2 pi))))
     (setq am (/ (+ a1 a2) 2.0)
           *vkmd-cung* (cons (vkmd:mp m (vkmd:mp (vkmd:ocs ed) (list (+ (car c) (* r (cos am))) (+ (cadr c) (* r (sin am))))))
                             *vkmd-cung*))))
)

;;; Góc phương vách đưa về [0, pi); gần 0 / 90 độ thì làm tròn hẳn
(defun vkmd:goc-pi (a)
  (while (>= a pi) (setq a (- a pi)))
  (while (< a 0.0) (setq a (+ a pi)))
  (cond ((or (< a 1e-4) (> a (- pi 1e-4))) 0.0) ((equal a (/ pi 2.0) 1e-4) (/ pi 2.0)) (T a))
)

;;; Toạ độ dọc trục t / lệch trục q của điểm p theo phương a
(defun vkmd:tq (a p)
  (list (+ (* (cos a) (car p)) (* (sin a) (cadr p))) (- (* (cos a) (cadr p)) (* (sin a) (car p)))))

;;; Đố (4 góc thế giới) -> (t q a w): t / q của tâm đố, a phương vách, w bề rộng đố
(defun vkmd:do-tt (g / d1 d3 a c)
  (setq d1 (distance (nth 0 g) (nth 1 g)) d3 (distance (nth 0 g) (nth 3 g))
        a (vkmd:goc-pi (if (< d1 d3) (angle (nth 0 g) (nth 1 g)) (angle (nth 0 g) (nth 3 g))))
        c (list (/ (+ (car (nth 0 g)) (car (nth 2 g))) 2.0) (/ (+ (cadr (nth 0 g)) (cadr (nth 2 g))) 2.0)))
  (append (vkmd:tq a c) (list a (min d1 d3)))
)

;;; Gom đố thành vách: danh sách các vách, mỗi vách = danh sách (t q a w) tăng dần theo t
(defun vkmd:gom-vach (/ ds x nhom con vach kq)
  (setq ds (mapcar 'vkmd:do-tt *vkmd-do*))
  (while ds
    (setq x (car ds) nhom nil con nil)
    (foreach y ds
      (if (and (equal (caddr y) (caddr x) 0.01) (< (abs (- (cadr y) (cadr x))) vkmd:lech-max))
        (setq nhom (cons y nhom))
        (setq con (cons y con))))
    (setq ds (reverse con) vach nil
          nhom (vl-sort nhom '(lambda (p q) (< (car p) (car q)))))
    (foreach y nhom
      (cond
        ((and vach (< (- (car y) (car (car vach))) 10.0)) nil)
        ((and vach (> (- (car y) (car (car vach))) vkmd:khoang-max))
         (if (cdr vach) (setq kq (cons (reverse vach) kq)))
         (setq vach (list y)))
        (T (setq vach (cons y vach)))))
    (if (cdr vach) (setq kq (cons (reverse vach) kq))))
  kq
)

;;; Loại ô giữa 2 đố (dọc trục ta..tb, trục ở lệch q, phương a, bề rộng đố w): "D" / "S" / "K"
(defun vkmd:loai-o (a q ta tb w / g)
  (setq g (- tb ta))
  (cond
    ((or (vl-some '(lambda (p / v) (setq v (vkmd:tq a p))
                     (and (< ta (car v) tb) (< (abs (- (cadr v) q)) g)))
                  *vkmd-cung*)
         (vkmd:co-khoi a q ta tb w T))
     "D")
    ((vkmd:co-khoi a q ta tb w nil) "S")
    (T "K"))
)

;;; Có block (không phải đố) nằm trong ô: tâm trong ô, dài từ 1/2 ô tới ô + 2 đố, gần trục; cung = T: block có cung cánh
(defun vkmd:co-khoi (a q ta tb w cung / g)
  (setq g (- tb ta))
  (vl-some '(lambda (k / v t1 t2 q1 q2)
              (if (or (and cung (cdr k)) (and (not cung) (not (cdr k))))
                (progn
                  (setq v (mapcar '(lambda (p) (vkmd:tq a p)) (car k))
                        t1 (apply 'min (mapcar 'car v)) t2 (apply 'max (mapcar 'car v))
                        q1 (apply 'min (mapcar 'cadr v)) q2 (apply 'max (mapcar 'cadr v)))
                  (and (< ta (/ (+ t1 t2) 2.0) tb) (>= (- t2 t1) (* 0.5 g)) (<= (- t2 t1) (+ g w w 20.0))
                       (< (abs (- (/ (+ q1 q2) 2.0) q)) (if cung g 300.0))))))
           *vkmd-khoi*)
)

;;; Danh sách đố một vách -> vách dạng vkmd:doc-vach: (L o tam pt ux uy)
(defun vkmd:tao-vach (ds / a q w nua t0 tn tam o i ux uy)
  (setq a (caddr (car ds))
        q (/ (apply '+ (mapcar 'cadr ds)) (length ds))
        w (/ (apply '+ (mapcar 'cadddr ds)) (length ds)) nua (/ w 2.0)
        t0 (car (car ds)) tn (car (last ds))
        tam (mapcar '(lambda (y) (+ (- (car y) t0) nua)) ds)
        i 0)
  (repeat (1- (length ds))
    (setq o (cons (list (vkmd:loai-o a q (car (nth i ds)) (car (nth (1+ i) ds)) w)
                        (- (car (nth (1+ i) ds)) (car (nth i ds))))
                  o)
          i (1+ i)))
  (setq ux (cos a) uy (sin a))
  (cond ((= a 0.0) (setq ux 1.0 uy 0.0)) ((= a (/ pi 2.0)) (setq ux 0.0 uy 1.0)))
  ;; dài vách sát số nguyên (đố đo được 65,7353: 4210,02) -> làm tròn mm, lệch dồn vào nửa đố cuối (< 0,1)
  (list (if (equal (+ (- tn t0) w) (fix (+ (- tn t0) w 0.5)) 0.1) (float (fix (+ (- tn t0) w 0.5))) (+ (- tn t0) w))
        (reverse o) tam
        (list (- (* ux (- t0 nua)) (* uy q)) (+ (* uy (- t0 nua)) (* ux q)) 0.0)
        ux uy)
)

;;; Vách do VK tạo (XData "ARCHIVINA_VK" hoặc tên gốc VACH KINH*)
(defun vkmd:la-vk (e)
  (and (= "INSERT" (cdr (assoc 0 (entget e))))
       (or (assoc -3 (entget e '("ARCHIVINA_VK")))
           (wcmatch (strcase (vla-get-EffectiveName (vlax-ename->vla-object e))) "VACH KINH*")))
)

;;; Tập chọn -> danh sách (e . vach), e = bản chèn vách VK hoặc nil (vách nhận từ hình vẽ tay); từ trên xuống, trái
;;; sang phải. Vách bỏ qua thì báo ra dòng lệnh.
(defun vkmd:tim-vach (ss / i e ed v kq)
  (setq *vkmd-kt* nil *vkmd-do* nil *vkmd-cung* nil *vkmd-khoi* nil i 0)
  (repeat (sslength ss)
    (setq e (ssname ss i) ed (entget e) i (1+ i))
    (cond
      ((vkmd:la-vk e)
       (if (= 'STR (type (setq v (vkmd:doc-vach e))))
         (princ (strcat "\nMDVK: b\\U+1ECF qua 1 v\\U+00E1ch VK: " v))
         (setq kq (cons (cons e v) kq))))
      (T (vkmd:quet ed vkmd:m0 0))))
  (foreach ds (vkmd:gom-vach)
    (setq v (vkmd:tao-vach ds))
    (if (and (assoc "S" (cadr v)) (assoc "D" (cadr v)))
      (princ (strcat "\nMDVK: b\\U+1ECF qua v\\U+00E1ch " (vkmd:so (car v)) " mm (c\\U+00F3 c\\U+1EA3 c\\U+1EEDa s\\U+1ED5 v\\U+00E0 c\\U+1EEDa \\U+0111i: ch\\U+01B0a h\\U+1ED7 tr\\U+1EE3)."))
      (setq kq (cons (cons nil v) kq))))
  (setq *vkmd-kt* nil *vkmd-do* nil *vkmd-cung* nil *vkmd-khoi* nil)
  (vl-sort kq '(lambda (p q / a b)
                 (setq a (nth 3 (cdr p)) b (nth 3 (cdr q)))
                 (if (equal (cadr a) (cadr b) 100.0) (< (car a) (car b)) (> (cadr a) (cadr b)))))
)

;;; Điểm đặt mặt đứng ngay trên vách (truyền cho vkmd:thuc-hien): vách ngang chỉ dùng Y = trục vách + nửa cửa đi lớn
;;; nhất (cánh mở; tối thiểu 300) + vkmd:cach-mb; vách xiên / đứng: góc dưới trái = (x nhỏ nhất, y lớn nhất + như trên)
(defun vkmd:diem-dat (vach / L p x2 y2 cao)
  (setq L (car vach) p (nth 3 vach)
        x2 (+ (car p) (* L (nth 4 vach))) y2 (+ (cadr p) (* L (nth 5 vach)))
        cao (apply 'max (cons 300.0 (mapcar '(lambda (x) (if (= (car x) "D") (/ (cadr x) 2.0) 0.0)) (cadr vach)))))
  (list (min (car p) x2) (+ (max (cadr p) y2) cao vkmd:cach-mb) 0.0)
)

;;; Dựng mặt đứng cho mọi vách ds ((e . vach) ...), mỗi cái ngay trên vách của nó; một nhóm undo (Ctrl+Z một lần).
(defun vkmd:chay-het (ds H hd hs co san bau / *error* undo cm)
  (defun *error* (msg)
    (setq *vkmd-mot-nhom* nil)
    (if undo (command-s "_.UNDO" "_E"))
    (if cm (setvar "CMDECHO" cm))
    (if (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*BREAK*")) (princ (strcat "\nL\\U+1ED7i MDVK: " msg)))
    (princ)
  )
  (setq cm (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  (if (setq undo (vkmd:undo-ok)) (command "_.UNDO" "_BE"))
  (setq *vkmd-mot-nhom* T)
  (foreach x ds
    (vkmd:thuc-hien (if (car x) (car x) (cdr x)) H hd hs co san bau (vkmd:diem-dat (cdr x))))
  (setq *vkmd-mot-nhom* nil)
  (if undo (command "_.UNDO" "_E"))
  (setvar "CMDECHO" cm)
  (princ (strcat "\nMDVK: xong " (itoa (length ds)) " v\\U+00E1ch."))
  (princ)
)

;;; Tóm tắt vách: "Dài 4210 mm, 4 đố: 1240 | DI 1665 | 1240"
(defun vkmd:mo-ta (vach / s)
  (foreach x (cadr vach)
    (setq s (strcat (if s (strcat s " | ") "") (cond ((= (car x) "S") "SO ") ((= (car x) "D") "DI ") (T ""))
                    (vkmd:so (cadr x)))))
  (strcat "D\\U+00E0i " (vkmd:so (car vach)) " mm, " (itoa (length (caddr vach))) " \\U+0111\\U+1ED1: " s)
)

(defun vkmd:ten-loai (v)
  (cond ((= v "D") "c\\U+1EEDa \\U+0111i") ((= v "S") "c\\U+1EEDa s\\U+1ED5") (T "k\\U+00EDnh kh\\U+00F4ng c\\U+1EEDa")))

;;; ---------------------------------------------------------------- hộp thoại
;;; Loại vách tự nhận từ mặt bằng; chỉ bật ô cần cho loại đó (người dùng chốt 29/10/2026):
;;;   cửa đi: cao vách + cao cửa đi; cửa sổ / kính: cao vách + cao cửa sổ + có thanh ngang? (+ sàn hoàn thiện, bậu)
(defun vkmd:viet-dcl (f / h)
  (setq h (open f "w"))
  (foreach s
    '("vkmd_hop_thoai : dialog {"
      "  label = \"MDVK - M\\U+1EB7t \\U+0111\\U+1EE9ng v\\U+00E1ch k\\U+00EDnh\";"
      "  : text { key = \"mo\"; width = 66; }"
      "  : popup_list { key = \"chon\"; label = \"Xem tr\\U+01B0\\U+1EDBc v\\U+00E1ch:\"; width = 66; }"
      "  : text { key = \"vach\"; width = 66; }"
      "  : row {"
      "  : column {"
      "  : edit_box { key = \"cao\"; label = \"Chi\\U+1EC1u cao v\\U+00E1ch k\\U+00EDnh (mm):\"; edit_width = 10; }"
      "  : boxed_column { key = \"khung_di\"; label = \"V\\U+00E1ch c\\U+1EEDa \\U+0111i\";"
      "    : edit_box { key = \"hd\"; label = \"Chi\\U+1EC1u cao c\\U+1EEDa \\U+0111i (thanh ngang \\U+0111\\U+1EB7t ngay tr\\U+00EAn c\\U+1EEDa, mm):\"; edit_width = 10; }"
      "  }"
      "  : boxed_column { key = \"khung_so\"; label = \"V\\U+00E1ch c\\U+1EEDa s\\U+1ED5\";"
      "    : toggle { key = \"co\"; label = \"C\\U+00F3 thanh ngang tr\\U+00EAn c\\U+1EEDa s\\U+1ED5 (b\\U+1ECF ch\\U+1ECDn: c\\U+1EEDa s\\U+1ED5 l\\U+00EAn s\\U+00E1t khung tr\\U+00EAn, cao t\\U+1EF1 t\\U+00EDnh)\"; }"
      "    : edit_box { key = \"hs\"; label = \"Chi\\U+1EC1u cao c\\U+1EEDa s\\U+1ED5 khi c\\U+00F3 thanh ngang (c\\U+00E1nh, l\\U+1ECDt l\\U+00F2ng, mm):\"; edit_width = 10; }"
      "    : edit_box { key = \"san\"; label = \"S\\U+00E0n ho\\U+00E0n thi\\U+1EC7n d\\U+00E0y (mm):\"; edit_width = 10; }"
      "    : edit_box { key = \"bau\"; label = \"Cao b\\U+1EADu c\\U+1EEDa s\\U+1ED5, t\\U+1EEB s\\U+00E0n ho\\U+00E0n thi\\U+1EC7n t\\U+1EDBi m\\U+00E9p d\\U+01B0\\U+1EDBi c\\U+00E1nh (mm):\"; edit_width = 10; }"
      "  }"
      "  }"
      "  : boxed_column { label = \"Xem tr\\U+01B0\\U+1EDBc m\\U+1EB7t \\U+0111\\U+1EE9ng: xanh = c\\U+00E1nh c\\U+1EEDa s\\U+1ED5, \\U+0111\\U+1ECF = c\\U+1EEDa \\U+0111i\";"
      "    : image { key = \"xem\"; width = 44; height = 15; color = 250; fixed_width = true; fixed_height = true; }"
      "  }"
      "  }"
      "  : text { key = \"thongtin\"; width = 66; }"
      "  : text { key = \"loi\"; width = 66; }"
      "  ok_cancel;"
      "}")
    (write-line s h))
  (close h)
)

;;; Ô xem trước mặt đứng (người dùng yêu cầu 29/10/2026, như ô xem trước của lệnh VK): sơ đồ đúng tỉ lệ theo kết
;;; quả vkmd:tinh - khung / đố / thanh ngang trắng, cánh cửa sổ dải xanh, cửa đi khung đỏ + hình thoi; vẽ lại mỗi
;;; lần bảng đổi. Thanh ngang lấy y như vkmd:dung (khung trên, khung dưới trừ ô cửa đi, thanh ngang, đố dưới cửa sổ).
(defun vkmd:ve-xem (vach kq H / rx ry le L sc x0 yb o tam d nua i xa xb bars so hd px py)
  (setq rx (dimx_tile "xem") ry (dimy_tile "xem") le 6)
  (start_image "xem")
  (fill_image 0 0 rx ry 250)
  (if (and (listp kq) H (> H 0) vach)
    (progn
      (setq L (car vach) o (cadr vach) tam (caddr vach) d vkmd:do nua (/ vkmd:do 2.0)
            so (caddr kq) hd (nth 3 kq)
            sc (min (/ (- rx (* 2 le)) L) (/ (- ry (* 2 le)) H))
            x0 (/ (- rx (* L sc)) 2.0) yb (- ry (/ (- ry (* H sc)) 2.0)))
      (defun px (x) (fix (+ x0 (* x sc))))
      (defun py (y) (fix (- yb (* y sc))))
      (setq i 0)
      (foreach x o
        (setq xa (+ (nth i tam) nua) xb (- (nth (1+ i) tam) nua)
              bars (append (list (list (- H d) H))
                           (if (/= (car x) "D") (list (list 0.0 d)))
                           (if (cadr kq) (list (cadr kq)))
                           (if (= (car x) "S") (list (list (car so) (cadr so))))))
        ;; cánh cửa sổ / cửa đi
        (cond
          ((= (car x) "S")
           (fill_image (px xa) (py (caddr so)) (max 1 (- (px xb) (px xa))) (max 1 (- (py (cadr so)) (py (caddr so)))) 5))
          ((= (car x) "D")
           (vector_image (px xa) (py 0.0) (px xb) (py 0.0) 1)
           (vector_image (px xa) (py hd) (px xb) (py hd) 1)
           (vector_image (px xa) (py 0.0) (px xa) (py hd) 1)
           (vector_image (px xb) (py 0.0) (px xb) (py hd) 1)
           (vector_image (px (/ (+ xa xb) 2.0)) (py hd) (px xa) (py (/ hd 2.0)) 1)
           (vector_image (px xa) (py (/ hd 2.0)) (px (/ (+ xa xb) 2.0)) (py 0.0) 1)
           (vector_image (px (/ (+ xa xb) 2.0)) (py 0.0) (px xb) (py (/ hd 2.0)) 1)
           (vector_image (px xb) (py (/ hd 2.0)) (px (/ (+ xa xb) 2.0)) (py hd) 1)))
        (foreach b bars
          (fill_image (px xa) (py (cadr b)) (max 1 (- (px xb) (px xa))) (max 1 (- (py (car b)) (py (cadr b)))) 7))
        (setq i (1+ i)))
      ;; đố đứng chạy suốt
      (foreach c tam
        (fill_image (px (- c nua)) (py H) (max 1 (- (px (+ c nua)) (px (- c nua)))) (max 1 (- (py 0.0) (py H))) 7))))
  (end_image)
)

;;; vkmd-vach: vách đang xem trước; vkmd-ds: mọi vách sẽ dựng ((e . vach) ...) - thông số bảng áp cho tất cả,
;;; vách nào tính lỗi thì báo và không cho OK
(defun vkmd:cap-nhat (/ kq kq-xem co ts loi)
  (setq co (= "1" (get_tile "co")))
  ;; cao cửa sổ chỉ nhập khi có thanh ngang (không thì tự tính); sàn + bậu luôn cần cho vách cửa sổ
  (mode_tile "hs" (if co 0 1))
  (mode_tile "san" (if (or co (vl-some '(lambda (x) (= "S" (vkmd:loai (cdr x)))) vkmd-ds)) 0 1))
  (mode_tile "bau" (if (or co (vl-some '(lambda (x) (= "S" (vkmd:loai (cdr x)))) vkmd-ds)) 0 1))
  (setq ts (list (vkmd:doc-so (get_tile "cao")) (vkmd:doc-so (get_tile "hd")) (vkmd:doc-so (get_tile "hs"))
                 co (vkmd:doc-so (get_tile "san")) (vkmd:doc-so (get_tile "bau")))
        kq (apply 'vkmd:tinh (cons vkmd-vach ts))
        loi (vl-some '(lambda (x / r)
                        (if (= 'STR (type (setq r (apply 'vkmd:tinh (cons (cdr x) ts)))))
                          (strcat "v\\U+00E1ch " (vkmd:so (car (cdr x))) " mm (" (vkmd:ten-loai (vkmd:loai (cdr x))) "): " r)))
                     vkmd-ds))
  ;; hình xem trước theo vách đang chọn; lỗi của vách bất kỳ chặn OK
  (setq kq-xem kq)
  (if (and loi (listp kq)) (setq kq loi))
  (if (listp kq)
    (progn
      (set_tile "thongtin" (strcat "Cao \\U+0111\\U+1ED9 t\\U+00E2m thanh ngang (t\\U+1EEB d\\U+01B0\\U+1EDBi l\\U+00EAn): " (vkmd:chuoi kq)
                                   (cond
                                     ((caddr kq)
                                      (strcat "   |   m\\U+00E9p d\\U+01B0\\U+1EDBi c\\U+00E1nh +" (vkmd:so (cadr (caddr kq)))
                                              ", cao c\\U+1EEDa s\\U+1ED5 " (vkmd:so (- (caddr (caddr kq)) (cadr (caddr kq))))))
                                     ((and (= "D" (car kq)) (not (cadr kq)))
                                      (strcat "   |   kh\\U+00F4ng \\U+0111\\U+1EE7 ch\\U+1ED7 thanh ngang: b\\U+1ECF thanh ngang, c\\U+1EEDa cao "
                                              (vkmd:so (nth 3 kq)) " s\\U+00E1t d\\U+01B0\\U+1EDBi khung tr\\U+00EAn"))
                                     (T ""))))
      (set_tile "loi" ""))
    (progn (set_tile "thongtin" "") (set_tile "loi" (strcat "L\\U+1ED7i: " kq))))
  (vkmd:ve-xem vkmd-vach kq-xem (vkmd:doc-so (get_tile "cao")))
  (setq vkmd-kq kq)
)

;;; Chọn vách để xem trước (popup "chon", vị trí i trong vkmd-ds)
(defun vkmd:chon (i / x)
  (setq x (nth i vkmd-ds) vkmd-vach (cdr x))
  (set_tile "vach" (strcat (if (car x) "V\\U+00E1ch VK - " "V\\U+00E1ch v\\U+1EBD tay - ") (vkmd:ten-loai (vkmd:loai vkmd-vach)) " - "
                           (vkmd:mo-ta vkmd-vach)))
  (vkmd:cap-nhat)
)

;;; Gõ MDVK -> quét chọn vùng mặt bằng (Enter = cả bản vẽ) -> tự nhận mọi vách kính (block VK + vách vẽ tay)
;;; -> một bảng hỏi chung (thông số áp cho mọi vách) -> mặt đứng đặt ngay trên mỗi vách (người dùng chốt 30/10/2026).
(defun c:MDVK (/ ss f id kq-dlg vkmd-vach vkmd-kq vkmd-ds khoa n i)
  (setq khoa '("cao" "hd" "hs" "co" "san" "bau"))
  (princ "\nQu\\U+00E9t ch\\U+1ECDn v\\U+00F9ng m\\U+1EB7t b\\U+1EB1ng c\\U+00F3 v\\U+00E1ch k\\U+00EDnh (block VK ho\\U+1EB7c v\\U+00E1ch v\\U+1EBD tay) <Enter = c\\U+1EA3 b\\U+1EA3n v\\U+1EBD>: ")
  (setq ss (ssget '((0 . "INSERT,ARC"))))
  (if (not ss) (setq ss (ssget "_X" (list '(0 . "INSERT,ARC") (cons 410 (getvar "CTAB"))))))
  (if ss (setq vkmd-ds (vkmd:tim-vach ss)))
  (if (not vkmd-ds)
    (princ "\nMDVK: kh\\U+00F4ng t\\U+00ECm th\\U+1EA5y v\\U+00E1ch k\\U+00EDnh (block VK, ho\\U+1EB7c \\U+0111\\U+1ED1 55..80 x 120..300 mm th\\U+1EB3ng h\\U+00E0ng).")
    (progn
      (setq vkmd-vach (cdar vkmd-ds)
            f (strcat (getvar "TEMPPREFIX") "MDVK_hop_thoai.dcl"))
      (vkmd:viet-dcl f)
      (if (or (< (setq id (load_dialog f)) 0) (not (new_dialog "vkmd_hop_thoai" id)))
        (princ "\nKh\\U+00F4ng m\\U+1EDF \\U+0111\\U+01B0\\U+1EE3c h\\U+1ED9p tho\\U+1EA1i MDVK.")
        (progn
          (set_tile "mo" (strcat "T\\U+00ECm th\\U+1EA5y " (itoa (length vkmd-ds)) " v\\U+00E1ch: "
                                 (itoa (length (vl-remove-if-not '(lambda (x) (= "D" (vkmd:loai (cdr x)))) vkmd-ds))) " c\\U+1EEDa \\U+0111i, "
                                 (itoa (length (vl-remove-if-not '(lambda (x) (= "S" (vkmd:loai (cdr x)))) vkmd-ds))) " c\\U+1EEDa s\\U+1ED5, "
                                 (itoa (length (vl-remove-if-not '(lambda (x) (= "K" (vkmd:loai (cdr x)))) vkmd-ds)))
                                 " k\\U+00EDnh - m\\U+1EB7t \\U+0111\\U+1EE9ng \\U+0111\\U+1EB7t ngay tr\\U+00EAn m\\U+1ED7i v\\U+00E1ch"))
          (start_list "chon")
          (setq i 0)
          (foreach x vkmd-ds
            (add_list (strcat (itoa (setq i (1+ i))) ". " (vkmd:ten-loai (vkmd:loai (cdr x))) " - d\\U+00E0i "
                              (vkmd:so (car (cdr x))) (if (car x) " (VK)" ""))))
          (end_list)
          (set_tile "chon" "0")
          (foreach x (if *vkmd-nho* *vkmd-nho*
                       '(("cao" . "") ("hd" . "2700") ("hs" . "1400") ("co" . "1") ("san" . "50") ("bau" . "1400")))
            (set_tile (car x) (cdr x)))
          ;; bật ô của loại vách có trong danh sách
          (mode_tile "khung_di" (if (vl-some '(lambda (x) (= "D" (vkmd:loai (cdr x)))) vkmd-ds) 0 1))
          (mode_tile "khung_so" (if (vl-some '(lambda (x) (/= "D" (vkmd:loai (cdr x)))) vkmd-ds) 0 1))
          (foreach k khoa (action_tile k "(vkmd:cap-nhat)"))
          (action_tile "chon" "(vkmd:chon (atoi $value))")
          (action_tile "accept"
            "(vkmd:cap-nhat) (if (listp vkmd-kq) (progn (setq *vkmd-nho* (mapcar '(lambda (k) (cons k (get_tile k))) khoa)) (done_dialog 1)))")
          (action_tile "cancel" "(done_dialog 0)")
          (vkmd:chon 0)
          (setq kq-dlg (start_dialog))
          (unload_dialog id)
          (if (= kq-dlg 1)
            (vkmd:chay-het vkmd-ds (vkmd:doc-so (cdr (assoc "cao" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "hd" *vkmd-nho*)))
                           (vkmd:doc-so (cdr (assoc "hs" *vkmd-nho*))) (= "1" (cdr (assoc "co" *vkmd-nho*)))
                           (vkmd:doc-so (cdr (assoc "san" *vkmd-nho*))) (vkmd:doc-so (cdr (assoc "bau" *vkmd-nho*)))))))))
  (princ)
)

(princ "\n\\U+0110\\U+00E3 n\\U+1EA1p VKMD.lsp \\U+2014 g\\U+00F5 MDVK, qu\\U+00E9t ch\\U+1ECDn v\\U+00F9ng m\\U+1EB7t b\\U+1EB1ng (Enter = c\\U+1EA3 b\\U+1EA3n v\\U+1EBD) \\U+0111\\U+1EC3 d\\U+1EF1ng m\\U+1EB7t \\U+0111\\U+1EE9ng m\\U+1ECDi v\\U+00E1ch k\\U+00EDnh.")
(princ)

;;; ---------------------------------------------------------------- dữ liệu block nhúng (sinh tự động)
;;; Dữ liệu block mặt đứng — SINH TỰ ĐỘNG bằng scripts\tao_du_lieu_md.py, không sửa tay
;;; Mọi danh sách phải có dấu ' (thiếu thì APPLOAD dừng giữa file, lỗi 29/10/2026)
;;; nguồn: ACAD-md cua di.dxf, ACAD-md cua so.dxf, ACAD-thanh dung va thanh ngang.dxf
(setq vkmd:dl-do-rong 65.0)
(setq vkmd:dl-di-rong 1600.0 vkmd:dl-di-cao 2699.51)
(setq vkmd:dl-so-rong 935.0 vkmd:dl-so-cao 1399.89 vkmd:dl-so-do 65.0 vkmd:dl-so-mau 5)
(setq vkmd:dl-so-net "HIDDEN" vkmd:dl-so-net-tile 300.0 vkmd:dl-so-net-mau '(0.25 -0.125))
(setq vkmd:dl-kinh '(("LINE" 95.0551 106.1246 -95.0551 -106.1246) ("LINE" -2.2394 63.9543 -69.4983 -14.4298) ("LINE" 67.2597 -0.9928 -2.2394 -72.658)))
(setq vkmd:dl-di-kinh '((528.9787 1201.3887) (-506.8289 1151.3887)))
(setq vkmd:dl-di-dim '(("A-Dimension" "_V" 130.0202 999.998 130.0202 -0.002 237.2552 -0.002) ("A-Dimension" "_V" -718.0 2699.5121 -714.582 0.0 -500.0 0.0) ("A-Window" "_H" 800.0 2516.0888 -800.0 2516.0888 -800.0 2275.8197)))
(setq vkmd:dl-di-chu '(("TAY N\\U+1EAEM INOX" 93.8375 1118.341 286.5581 1367.155 55.0 "Archi- Arial" "A-Window") ("KH\\U+00D3A \\U+00C2M S\\U+00C0N" 105.4107 32.7167 294.964 505.889 55.0 "Archi- Arial" "A-Window")))
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
