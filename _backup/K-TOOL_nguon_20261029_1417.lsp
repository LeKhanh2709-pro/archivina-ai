;;; K-TOOL.lsp
;;; Nạp K-TOOL.dll để hiện tab ribbon K-TOOL (nút VK, MDVK, LOMO, NCL, KT-NGANCHAY, CHONGTHAM).
;;; Các lệnh LISP đã nhúng sẵn trong K-TOOL.dll: bấm nút là DLL tự nạp và chạy, file này chỉ dùng để
;;; tự nạp DLL mỗi lần mở AutoCAD. Lệnh gõ tay: KTOOL (nạp DLL nếu chưa nạp và hiện lại tab K-TOOL).
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

;; Tìm file: Support Path > biến ARCHIVINA_LISP > hỏi chọn một lần
(defun kt:tim (ten / f thu)
  (cond
    ((setq f (findfile ten)) f)
    ((and (setq thu (getenv "ARCHIVINA_LISP"))
          (vl-file-systemp (setq f (strcat thu "\\" ten))))
     f)
    (t
     (setq f (getfiled
               (strcat "K-TOOL: chọn file " ten " (cùng thư mục với K-TOOL.lsp)")
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
     (princ "\nK-TOOL: không tìm thấy K-TOOL.dll, chưa tạo được tab ribbon.")
     nil)
    (t
     (princ (strcat "\nK-TOOL: nạp " f))
     (setq kq (vl-catch-all-apply 'command (list "_.NETLOAD" f)))
     (cond
       ((vl-catch-all-error-p kq)
        (princ (strcat "\nK-TOOL: lỗi nạp " f ": " (vl-catch-all-error-message kq)))
        nil)
       (t
        (vl-bb-set 'kt:dll-da-nap T)
        T)))))

(defun c:KTOOL ()
  (if (kt:nap-dll) (command "_.KTOOLTAB"))
  (princ))

;; Chạy khi nạp file: nạp DLL để thêm tab K-TOOL
(if (kt:nap-dll)
  (princ "\nK-TOOL đã sẵn sàng: tab K-TOOL trên ribbon. Gõ KTOOL nếu chưa thấy tab.")
  (princ "\nK-TOOL: chưa có tab ribbon. Gõ KTOOL để thử lại."))
(princ)
