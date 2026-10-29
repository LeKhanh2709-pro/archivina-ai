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
     "VK - Vách kính"
     "Chia đố và dựng vách kính mặt bằng (lệnh VK)")
    ("MDVK" "VKMD.lsp" "MDVK"
     "MDVK - Mặt đứng VK"
     "Dựng mặt đứng vách kính từ block VACH KINH (lệnh MDVK)")
    ("LOMO" "Lomo.lsp" "LOMO"
     "LOMO - Lỗ mở MEP"
     "Chèn block A-MEP cho trục / hộp kỹ thuật (lệnh LOMO)")
    ("NCL" "fire_stop_shaft.lsp" "NCL"
     "NCL - Ngăn cháy lan"
     "Vẽ bo + hatch ngăn cháy lan, không hỏi trước (lệnh NCL)")
    ("KT-NGANCHAY" "fire_stop_shaft.lsp" "KT-NGANCHAY"
     "KT-NGANCHAY"
     "Ngăn cháy lan, hỏi trước khi vẽ (lệnh KT-NGANCHAY)")
    ("CHONGTHAM" "CHONGTHAM.lsp" "CHONGTHAM"
     "CHONGTHAM - Chống thấm"
     "Vẽ mặt bằng chống thấm (lệnh CHONGTHAM)")))

;; Tìm file LISP: Support Path > biến ARCHIVINA_LISP > hỏi chọn một lần
(defun kt:tim (ten / f thu)
  (cond
    ((setq f (findfile ten)) f)
    ((and (setq thu (getenv "ARCHIVINA_LISP"))
          (vl-file-systemp (setq f (strcat thu "\\" ten))))
     f)
    (t
     (setq f (getfiled
               (strcat "K-TOOL: chọn file " ten " (cùng thư mục với các file LISP)")
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
        (princ (strcat "\nK-TOOL: lỗi nạp " f ": " (vl-catch-all-error-message kq)))
        nil)
       (t
        (setq kt:da-nap (cons ten kt:da-nap))
        T)))))

;; Chạy một nút: nạp file LISP (nếu chưa nạp) rồi gọi c:<lệnh>
(defun kt:chay (nut / m)
  (setq m (assoc nut kt:bang))
  (cond
    ((null m) (princ (strcat "\nK-TOOL: không có nút " nut)))
    ((kt:nap (cadr m))
     (eval (read (strcat "(c:" (caddr m) ")"))))
    (t (princ (strcat "\nK-TOOL: chưa nạp được lệnh " (caddr m)))))
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
  (princ "\nK-TOOL: không tạo được thanh. Thử lại bằng lệnh KTOOL sau khi AutoCAD mở xong.")
  (princ "\nK-TOOL đã sẵn sàng. Gõ KTOOL để hiện lại thanh."))
(princ)
