;;; K-TOOL.lsp
;;; Nạp K-TOOL.dll để hiện tab ribbon K-TOOL (nút VK, MDVK, LOMO, NCL, CHONGTHAM; bỏ nút KT-NGANCHAY theo
;;; yêu cầu người dùng 2026-10-29, lệnh gõ tay KT-NGANCHAY vẫn có vì chung file với NCL).
;;; Các lệnh LISP đã nhúng sẵn trong K-TOOL.dll: nạp DLL là nạp luôn mọi lệnh vào từng bản vẽ (nút và lệnh
;;; gõ tay dùng được ngay); file này chỉ dùng để tự nạp DLL mỗi lần mở AutoCAD.
;;; Lệnh gõ tay: KTOOL (nạp DLL nếu chưa nạp và hiện lại tab K-TOOL).
;;;
;;; Cách dùng:
;;;   1. Để K-TOOL.lsp và K-TOOL.dll chung một thư mục, thêm thư mục đó vào Trusted Locations
;;;      (Options > Files) để AutoCAD không hỏi khi nạp; nên thêm cả vào Support File Search Path.
;;;   2. APPLOAD chọn K-TOOL.lsp, Add to Startup Suite: lần sau mở AutoCAD tab K-TOOL tự hiện.
;;;      Không tìm thấy K-TOOL.dll thì lệnh hỏi chọn file một lần, rồi nhớ thư mục qua ARCHIVINA_LISP.
;;;
;;; File sinh từ scripts\ktool\K-TOOL_nguon.lsp bằng scripts\ktool\build.ps1 (chữ có dấu trong chuỗi đổi thành
;;; \U+XXXX để chạy được cả LISPSYS = 0 và 1), không sửa tay. K-TOOL.dll build cho AutoCAD 2027 (.NET 10).

(vl-load-com)

;; Các ổ cứng trên máy (C:, D:...), không gồm ổ mạng / USB
(defun kt:o-dia (/ fso kq)
  (setq fso (vl-catch-all-apply 'vlax-create-object '("Scripting.FileSystemObject")))
  (if (and fso (not (vl-catch-all-error-p fso)))
    (progn
      (vlax-for d (vlax-get fso 'Drives)
        (if (and (= (vlax-get d 'DriveType) 2) (member (vlax-get d 'IsReady) '(-1 1 :vlax-true T)))
          (setq kq (cons (strcat (vlax-get d 'DriveLetter) ":") kq))))
      (vlax-release-object fso)))
  (reverse kq))

;; Tìm file: Support Path > biến ARCHIVINA_LISP > <ổ cứng>:\AI\scripts\lisp (gói K-TOOL giải nén ra ổ bất kỳ)
;; > hỏi chọn một lần
(defun kt:tim (ten / f thu)
  (cond
    ((setq f (findfile ten)) f)
    ((and (setq thu (getenv "ARCHIVINA_LISP"))
          (vl-file-systemp (setq f (strcat thu "\\" ten))))
     f)
    ((setq f (vl-some '(lambda (o / g)
                         (if (vl-file-systemp (setq g (strcat o "\\AI\\scripts\\lisp\\" ten))) g))
                      (kt:o-dia)))
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

;; Nạp K-TOOL.dll một lần cho cả phiên AutoCAD (cờ trên blackboard dùng chung mọi bản vẽ)
(defun kt:nap-dll (/ f kq)
  (cond
    ((vl-bb-ref 'kt:dll-da-nap) T)
    ((null (setq f (kt:tim "K-TOOL.dll")))
     (princ "\nK-TOOL: kh\U+00F4ng t\U+00ECm th\U+1EA5y K-TOOL.dll, ch\U+01B0a t\U+1EA1o \U+0111\U+01B0\U+1EE3c tab ribbon.")
     nil)
    (t
     (princ (strcat "\nK-TOOL: n\U+1EA1p " f))
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
