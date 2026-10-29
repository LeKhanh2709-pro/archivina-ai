;;; K-TOOL.lsp
;;; Thanh công cụ K-TOOL: gom các lệnh LISP Archivina đã làm thành một toolbar.
;;; Nút trên thanh: VK, MDVK, LOMO, NCL, KT-NGANCHAY, CHONGTHAM.
;;; Lệnh gõ tay: KTOOL (hiện lại thanh nếu đã tắt).
;;;
;;; Cách dùng:
;;;   1. Chép cả thư mục chứa các file .lsp (vd. scripts\lisp) sang máy, thêm thư mục đó vào
;;;      Support File Search Path (Options > Files), hoặc đặt biến môi trường ARCHIVINA_LISP = thư mục đó.
;;;   2. APPLOAD chọn K-TOOL.lsp, Add to Startup Suite (lần sau mở AutoCAD thanh tự hiện).
;;;   3. Bấm nút: file LISP tương ứng chỉ được nạp ở lần bấm đầu. Không tìm thấy file thì lệnh hỏi
;;;      chọn đúng file đó một lần, rồi nhớ thư mục qua ARCHIVINA_LISP.
;;;
;;; Thanh được tạo trong bộ nhớ (không sửa file CUIx của bản vẽ / máy). Muốn đổi nút thì sửa kt:bang ở đây
;;; rồi mở lại AutoCAD. Yêu cầu: AutoCAD 2021+, chạy được cả LISPSYS = 0 và 1 (chữ có dấu đã đổi thành \U+XXXX).

(vl-load-com)

;; Bảng nút: (tên lệnh, file LISP, tên c: trong file, nhãn trên nút, chú thích)
(setq kt:bang
  '(("VK" "VK.lsp" "VK"
     "VK - V\U+00E1ch k\U+00EDnh"
     "Chia \U+0111\U+1ED1 v\U+00E0 d\U+1EF1ng v\U+00E1ch k\U+00EDnh m\U+1EB7t b\U+1EB1ng (l\U+1EC7nh VK)")
    ("MDVK" "VKMD.lsp" "MDVK"
     "MDVK - M\U+1EB7t \U+0111\U+1EE9ng VK"
     "D\U+1EF1ng m\U+1EB7t \U+0111\U+1EE9ng v\U+00E1ch k\U+00EDnh t\U+1EEB block VACH KINH (l\U+1EC7nh MDVK)")
    ("LOMO" "Lomo.lsp" "LOMO"
     "LOMO - L\U+1ED7 m\U+1EDF MEP"
     "Ch\U+00E8n block A-MEP cho tr\U+1EE5c / h\U+1ED9p k\U+1EF9 thu\U+1EADt (l\U+1EC7nh LOMO)")
    ("NCL" "fire_stop_shaft.lsp" "NCL"
     "NCL - Ng\U+0103n ch\U+00E1y lan"
     "V\U+1EBD bo + hatch ng\U+0103n ch\U+00E1y lan, kh\U+00F4ng h\U+1ECFi tr\U+01B0\U+1EDBc (l\U+1EC7nh NCL)")
    ("KT-NGANCHAY" "fire_stop_shaft.lsp" "KT-NGANCHAY"
     "KT-NGANCHAY"
     "Ng\U+0103n ch\U+00E1y lan, h\U+1ECFi tr\U+01B0\U+1EDBc khi v\U+1EBD (l\U+1EC7nh KT-NGANCHAY)")
    ("CHONGTHAM" "CHONGTHAM.lsp" "CHONGTHAM"
     "CHONGTHAM - Ch\U+1ED1ng th\U+1EA5m"
     "V\U+1EBD m\U+1EB7t b\U+1EB1ng ch\U+1ED1ng th\U+1EA5m (l\U+1EC7nh CHONGTHAM)")))

;; Tìm file LISP: Support Path > biến ARCHIVINA_LISP > hỏi chọn một lần
(defun kt:tim (ten / f thu)
  (cond
    ((setq f (findfile ten)) f)
    ((and (setq thu (getenv "ARCHIVINA_LISP"))
          (vl-file-systemp (setq f (strcat thu "\\" ten))))
     f)
    (t
     (setq f (getfiled
               (strcat "K-TOOL: ch\U+1ECDn file " ten " (c\U+00F9ng th\U+01B0 m\U+1EE5c v\U+1EDBi c\U+00E1c file LISP)")
               "" "lsp" 8))
     (cond
       ((null f) nil)
       (t
        (setenv "ARCHIVINA_LISP" (vl-filename-directory f))
        f)))))

;; Danh sách file LISP đã nạp trong phiên này (mỗi file chỉ nạp một lần)
(setq kt:da-nap nil)

;; Nạp file LISP, báo lỗi nếu không nạp được (vd. SECURELOAD chặn)
(defun kt:nap (ten / f kq)
  (cond
    ((member ten kt:da-nap) T)
    ((null (setq f (kt:tim ten))) nil)
    (t
     (setq kq (vl-catch-all-apply 'load (list f)))
     (cond
       ((vl-catch-all-error-p kq)
        (princ (strcat "\nK-TOOL: l\U+1ED7i n\U+1EA1p " f ": " (vl-catch-all-error-message kq)))
        nil)
       (t
        (setq kt:da-nap (cons ten kt:da-nap))
        T)))))

;; Chạy một nút: nạp file LISP (nếu chưa nạp) rồi gọi c:<lệnh>
(defun kt:chay (nut / m)
  (setq m (assoc nut kt:bang))
  (cond
    ((null m) (princ (strcat "\nK-TOOL: kh\U+00F4ng c\U+00F3 n\U+00FAt " nut)))
    ((kt:nap (cadr m))
     (eval (read (strcat "(c:" (caddr m) ")"))))
    (t (princ (strcat "\nK-TOOL: ch\U+01B0a n\U+1EA1p \U+0111\U+01B0\U+1EE3c l\U+1EC7nh " (caddr m)))))
  (princ))

;; Tạo thanh K-TOOL trong nhóm menu ACAD (nếu chưa có), gắn nút, hiện thanh
(defun kt:thanh (/ mg tbs tb i m mac)
  (setq mg  (vla-item (vla-get-MenuGroups (vlax-get-acad-object)) "ACAD")
        tbs (vla-get-Toolbars mg)
        tb  nil)
  (vlax-for x tbs
    (if (= (vla-get-Name x) "K-TOOL") (setq tb x)))
  (if (null tb)
    (progn
      (setq tb (vla-Add tbs "K-TOOL")
            i  0)
      (foreach m kt:bang
        (setq mac (strcat "^C^C(kt:chay " (chr 34) (car m) (chr 34) ")"))
        (vla-AddToolbarButton tb i (cadddr m) (last m) (last m) mac)
        (setq i (1+ i)))))
  (vla-put-Visible tb :vlax-true)
  tb)

(defun c:KTOOL ()
  (vl-catch-all-apply 'kt:thanh nil)
  (princ))

;; Chạy khi nạp file: tạo / hiện thanh K-TOOL
(if (vl-catch-all-error-p (vl-catch-all-apply 'kt:thanh nil))
  (princ "\nK-TOOL: kh\U+00F4ng t\U+1EA1o \U+0111\U+01B0\U+1EE3c thanh. Th\U+1EED l\U+1EA1i b\U+1EB1ng l\U+1EC7nh KTOOL sau khi AutoCAD m\U+1EDF xong.")
  (princ "\nK-TOOL \U+0111\U+00E3 s\U+1EB5n s\U+00E0ng. G\U+00F5 KTOOL \U+0111\U+1EC3 hi\U+1EC7n l\U+1EA1i thanh."))
(princ)
