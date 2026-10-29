;;; K-TOOL.lsp
;;; Tab ribbon K-TOOL: gom các lệnh LISP Archivina đã làm thành các nút trên ribbon AutoCAD.
;;; Nút: VK, MDVK (Vách kính) | LOMO, NCL, KT-NGANCHAY (Trục kỹ thuật) | CHONGTHAM (Chống thấm).
;;; Tab do K-TOOL.dll tạo (nguồn scripts\ktool\KToolApp.cs); file này nạp DLL và chạy lệnh khi bấm nút.
;;; Lệnh gõ tay: KTOOL (nạp DLL nếu chưa nạp và hiện lại tab K-TOOL).
;;;
;;; Cách dùng:
;;;   1. Để K-TOOL.lsp, K-TOOL.dll và các file LISP (VK.lsp, VKMD.lsp, Lomo.lsp, fire_stop_shaft.lsp,
;;;      CHONGTHAM.lsp) chung một thư mục, vd. scripts\lisp. Thêm thư mục đó vào Trusted Locations
;;;      (Options > Files) để AutoCAD không hỏi khi nạp DLL; nên thêm cả vào Support File Search Path.
;;;   2. APPLOAD chọn K-TOOL.lsp, Add to Startup Suite: lần sau mở AutoCAD tab K-TOOL tự hiện.
;;;   3. Bấm nút: file LISP tương ứng chỉ được nạp ở lần bấm đầu. Không tìm thấy file thì lệnh hỏi
;;;      chọn đúng file đó một lần, rồi nhớ thư mục qua ARCHIVINA_LISP.
;;;
;;; File sinh từ scripts\ktool\K-TOOL_nguon.lsp bằng scripts\ktool\build.ps1 (chữ có dấu trong chuỗi đổi thành
;;; \U+XXXX để chạy được cả LISPSYS = 0 và 1), không sửa tay. Thêm nút: thêm dòng vào kt:bang ở đây và mảng
;;; Panels trong KToolApp.cs, rồi build lại. K-TOOL.dll build cho AutoCAD 2027 (.NET 10).

(vl-load-com)

;; Bảng nút: (tên nút, file LISP, tên c: trong file)
(setq kt:bang
  '(("VK" "VK.lsp" "VK")
    ("MDVK" "VKMD.lsp" "MDVK")
    ("LOMO" "Lomo.lsp" "LOMO")
    ("NCL" "fire_stop_shaft.lsp" "NCL")
    ("KT-NGANCHAY" "fire_stop_shaft.lsp" "KT-NGANCHAY")
    ("CHONGTHAM" "CHONGTHAM.lsp" "CHONGTHAM")))

;; Tìm file: Support Path > biến ARCHIVINA_LISP > hỏi chọn một lần
(defun kt:tim (ten / f thu)
  (cond
    ((setq f (findfile ten)) f)
    ((and (setq thu (getenv "ARCHIVINA_LISP"))
          (vl-file-systemp (setq f (strcat thu "\\" ten))))
     f)
    (t
     (setq f (getfiled
               (strcat "K-TOOL: ch\U+1ECDn file " ten " (c\U+00F9ng th\U+01B0 m\U+1EE5c v\U+1EDBi K-TOOL.lsp)")
               "" (substr (vl-filename-extension ten) 2) 8))
     (cond
       ((null f) nil)
       (t
        (setenv "ARCHIVINA_LISP" (vl-filename-directory f))
        f)))))

;; Danh sách file LISP đã nạp trong bản vẽ này (mỗi file chỉ nạp một lần)
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

;; Nạp K-TOOL.dll một lần cho cả phiên AutoCAD (cờ trên blackboard dùng chung mọi bản vẽ)
(defun kt:nap-dll (/ f kq)
  (cond
    ((vl-bb-ref 'kt:dll-da-nap) T)
    ((null (setq f (kt:tim "K-TOOL.dll")))
     (princ "\nK-TOOL: kh\U+00F4ng t\U+00ECm th\U+1EA5y K-TOOL.dll, ch\U+01B0a t\U+1EA1o \U+0111\U+01B0\U+1EE3c tab ribbon.")
     nil)
    (t
     (setq kq (vl-catch-all-apply 'command (list "_.NETLOAD" f)))
     (cond
       ((vl-catch-all-error-p kq)
        (princ (strcat "\nK-TOOL: l\U+1ED7i n\U+1EA1p " f ": " (vl-catch-all-error-message kq)))
        nil)
       (t
        (vl-bb-set 'kt:dll-da-nap T)
        T)))))

(defun c:KTOOL ()
  (if (kt:nap-dll) (command "_.KTOOLTAB"))
  (princ))

;; Chạy khi nạp file: nạp DLL để thêm tab K-TOOL
(if (kt:nap-dll)
  (princ "\nK-TOOL \U+0111\U+00E3 s\U+1EB5n s\U+00E0ng: tab K-TOOL tr\U+00EAn ribbon. G\U+00F5 KTOOL n\U+1EBFu ch\U+01B0a th\U+1EA5y tab.")
  (princ "\nK-TOOL: ch\U+01B0a c\U+00F3 tab ribbon. G\U+00F5 KTOOL \U+0111\U+1EC3 th\U+1EED l\U+1EA1i."))
(princ)
