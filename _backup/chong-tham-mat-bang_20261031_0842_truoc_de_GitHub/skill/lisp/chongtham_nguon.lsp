;;; CHONGTHAM.lsp
;;; Lệnh CHONGTHAM: vẽ mặt bằng chống thấm vào bản vẽ đang mở (bản LISP của skill chong-tham-mat-bang).
;;;
;;; Lệnh tự tìm và vẽ chống thấm cho: WC, lô gia / ban công, phòng rác (ký hiệu R), buồng đệm phòng rác,
;;; phòng kỹ thuật nước (ký hiệu N hoặc KTN). Mỗi phòng:
;;;   - đường bo kín theo mặt lõi tường / mặt trong lan can (màu 3) + đảo hộp kỹ thuật trong phòng
;;;   - hatch User-defined 45°, khoảng cách 400, lưới chéo đôi, màu 3, liên kết với đường bo
;;;   - nét vén chân tường: polyline màu 1, rộng 40, cách bo 50, ngắt tại cửa đi và cửa thang máy
;;; Tất cả trên layer A-Material, gom vào 1 block "CHONG THAM" (trùng tên thì "CHONG THAM 2"...) chèn tại 0,0.
;;; Sau đó: tắt layer nội thất / thiết bị vệ sinh, đổi mọi layer khác sang màu xám 150,150,150 để nổi
;;; hatch chống thấm; layer của xref khung tên (tên chứa KHUNG / TITLE / TEN BAN VE) giữ nguyên màu, không tắt.
;;; Trạng thái layer cũ lưu thành layer state "TRUOC CHONG THAM" (khôi phục bằng Layer States Manager).
;;; Chỉ đổi trong bảng layer: không sửa màu từng đối tượng, không bind xref / block.
;;;
;;; MỘT FILE DUY NHẤT (người dùng chốt 23/10/2026): chép riêng file này sang máy nào cũng chạy, không cần chép
;;; thư mục skill. Bộ nhận diện (script PowerShell + Python của skill chong-tham-mat-bang và dien-tich-ch) được
;;; NHÚNG SẴN trong file này (base64, cuối file); lần chạy đầu lệnh giải nén ra <gốc>\_tools\chongtham_<bản>\
;;; rồi dùng lại cho các lần sau.
;;; FILE NÀY ĐƯỢC GỘP TỰ ĐỘNG, KHÔNG SỬA TAY: sửa lisp\chongtham_nguon.lsp hoặc script của skill, rồi chạy
;;; scripts\gop_chongtham.ps1 của skill chong-tham-mat-bang để gộp lại.
;;;
;;; Cách hoạt động: phần nhận diện phòng (khép phòng từ tường / cửa ACA, khoét giếng thang, nhận lô gia
;;; theo cửa trượt / lan can...) dùng bộ dò Python nhúng sẵn (đã kiểm chứng trên tầng 4 Tháp B 254HQV
;;; và CT1 tầng 5A-10), chạy ngầm trên BẢN SAO của file đã lưu trên đĩa (File gốc không bị sửa). LISP đọc
;;; kết quả rồi vẽ thẳng vào bản vẽ đang mở.
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước. Lệnh không hỏi lưu: bản vẽ có thay đổi chưa lưu (hoặc chưa lưu lần nào)
;;;      thì lệnh tự ghi trạng thái hiện tại ra bản tạm (-WBLOCK *) để nhận diện, không lưu đè file.
;;;   2. APPLOAD -> chọn CHONGTHAM.lsp (ở thư mục nào cũng được). Gõ CHONGTHAM.
;;;      KHÔNG CẦN CÀI PYTHON (người dùng chốt 23/10/2026): chép kèm thư mục CHONGTHAM_python (gói Python mang
;;;      theo: Python nhúng 3.12 + ezdxf, shapely, matplotlib...) vào <ổ>:\AI\_tools\ (vd. D:\AI\_tools\
;;;      CHONGTHAM_python), lệnh tự tìm. Để chỗ khác thì lần đầu lệnh cho chọn python.exe trong thư mục đó rồi nhớ.
;;;   3. Nhận diện chạy ngầm, không hiện cửa sổ (1 - 6 phút với mặt bằng tầng 50 MB). Trong lúc chờ lệnh in tiến độ ở
;;;      dòng lệnh, Esc để dừng chờ, không bấm nút khác. Xong lệnh vẽ luôn và in:
;;;      số phòng theo loại, các vùng "cần xem" (không vẽ), thư mục chứa ảnh xem lại (không tạo Excel).
;;;   4. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ (cả phần đổi màu layer).
;;;   Chạy lại lần 2: phòng đã có hatch chống thấm (block CHONG THAM*) không vẽ trùng.
;;;
;;; Yêu cầu máy (DÙNG ĐƯỢC Ở MÁY KHÁC, không gắn cứng ổ đĩa / đường dẫn - sửa 23/10/2026):
;;;   - Thư mục gốc: biến môi trường ARCHIVINA_AI, không có thì <ổ cứng>:\AI nếu có thư mục .claude (máy này
;;;     D:\AI), không có nữa thì %LOCALAPPDATA%\ARCHIVINA. Giải nén ở <gốc>\_tools\chongtham_<bản>\, file tạm ở
;;;     <gốc>\_tmp\ (không xoá sau khi chạy).
;;;   - Python: gói mang theo CHONGTHAM_python (trên); không có thì dùng Python có sẵn trên máy nếu đủ gói
;;;     (venv <gốc>\_tools\venv, %LOCALAPPDATA%\ARCHIVINA\venv, py / python trong PATH).
;;;   - AutoCAD 2021+ (có AutoCAD Architecture để giữ tường / cửa ACA). Core Console tự tìm (registry Autodesk,
;;;     <ổ>\Program Files\Autodesk\AutoCAD *, <ổ>\autocad\AutoCAD *; biến ARCHIVINA_ACAD để chỉ định).
;;;     LISPSYS = 1, file lưu UTF-8.
;;;   Lỗi ở máy khác: lệnh in đường dẫn <gốc>\_tmp\chongtham_lisp_<giờ>\nhat_ky.txt (mọi thông báo bước chạy ngầm).
;;; Giới hạn: khu giặt thông thẳng phòng khách / bếp (không tường, không cửa) không tách được -> "cần xem",
;;;   không vẽ. Phòng rác / KT nước nhận theo ký hiệu chữ R / N / KTN đúng nguyên văn.

(vl-load-com)

;;; ---------- Cấu hình ----------
(defun ct:cfg (k)
  (cdr
    (assoc
      k
      '((layer-ve . "A-Material")
        (ten-block . "CHONG THAM")
        ;; layer nội thất / thiết bị vệ sinh: tắt (so trên tên đã chuẩn hoá: bỏ tiền tố xref, dấu cách, chữ hoa)
        (layer-an "A-INTERIOR*" "*N?ITH?T*" "*NOITHAT*" "*FURN*" "A-WC*" "*GATHU*" "*THIETBIVESINH*" "*TBVS*")
        (mau-mo . "150,150,150")
        ;; tên xref khung tên: layer của xref này giữ nguyên màu, không tắt
        (khung-ten "*KHUNG*" "*TITLE*" "*TEN BAN VE*" "*TENBANVE*")
        (layer-state . "TRUOC CHONG THAM")
       )
    )
  )
)

;;; ---------- Tìm đường dẫn trên máy đang chạy ----------
;;; Ổ cứng cố định đang sẵn sàng ("C:" "D:"...), bỏ ổ mạng / ổ rời để không treo khi ổ mạng mất kết nối
(defun ct:o-dia (/ fso kq)
  (setq fso (vl-catch-all-apply 'vlax-create-object '("Scripting.FileSystemObject")))
  (if (and fso (not (vl-catch-all-error-p fso)))
    (progn
      (vlax-for d (vlax-get fso 'Drives)
        (if (and (= (vlax-get d 'DriveType) 2) (member (vlax-get d 'IsReady) '(-1 1 :vlax-true T)))
          (setq kq (cons (strcat (vlax-get d 'DriveLetter) ":") kq))
        )
      )
      (vlax-release-object fso)
    )
  )
  (reverse kq)
)

;;; Thư mục gốc (không có "\\" cuối): biến ARCHIVINA_AI -> <ổ cứng>:\AI có thư mục .claude (máy này D:\AI)
;;; -> %LOCALAPPDATA%\ARCHIVINA. (and / or của AutoLISP trả về T: lấy chuỗi bằng setq trong cond.)
(defun ct:goc (/ g)
  (cond
    (ct:*goc*)
    ((and (setq g (getenv "ARCHIVINA_AI")) (vl-file-directory-p g))
     (setq ct:*goc* (vl-string-right-trim "\\/" g)))
    ((setq g (vl-some '(lambda (o) (if (vl-file-directory-p (strcat o "\\AI\\.claude")) (strcat o "\\AI")))
                      (ct:o-dia)))
     (setq ct:*goc* g))
    (t (setq ct:*goc* (strcat (cond ((getenv "LOCALAPPDATA")) ((getenv "TEMP"))) "\\ARCHIVINA")))
  )
)

;;; Dòng lệnh chạy một script PowerShell. powershell.exe theo đường dẫn đầy đủ: máy có PATH bị sửa vẫn chạy
(defun ct:lenh-ps (ps tham)
  (strcat "\"" (cond ((getenv "SystemRoot")) ("C:\\Windows"))
          "\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\" -NoProfile -ExecutionPolicy Bypass -File \""
          ps "\" " tham)
)

;;; Chạy một script PowerShell, chờ chạy xong; hien = T: hiện cửa sổ (cài Python), nil: chạy ẩn.
;;; Trả về mã thoát, nil nếu máy chặn WScript.Shell (Windows Script Host).
(defun ct:chay-ps (ps tham hien / sh ma)
  (setq sh (vl-catch-all-apply 'vlax-create-object '("WScript.Shell")))
  (if (and sh (not (vl-catch-all-error-p sh)))
    (progn
      ;; :vlax-true = chờ chạy xong
      (setq ma (vl-catch-all-apply 'vlax-invoke-method (list sh 'Run (ct:lenh-ps ps tham) (if hien 1 0) :vlax-true)))
      (vlax-release-object sh)
      (if (vl-catch-all-error-p ma) -1 ma)
    )
  )
)

;;; Chạy ẩn một script PowerShell, KHÔNG chờ. Trả về T nếu khởi động được.
(defun ct:chay-nen (ps tham / sh ma)
  (setq sh (vl-catch-all-apply 'vlax-create-object '("WScript.Shell")))
  (if (and sh (not (vl-catch-all-error-p sh)))
    (progn
      (setq ma (vl-catch-all-apply 'vlax-invoke-method (list sh 'Run (ct:lenh-ps ps tham) 0 :vlax-false)))
      (vlax-release-object sh)
      (not (vl-catch-all-error-p ma))
    )
  )
)

;;; Dòng đầu của file text, nil nếu chưa đọc được
(defun ct:dong-dau (fn / f d)
  (if (and (findfile fn) (setq f (open fn "r")))
    (progn (setq d (read-line f)) (close f) d)
  )
)

;;; Chờ bộ nhận diện chạy ngầm ghi xong.txt, trả về dòng đầu của file đó. Chờ bằng DELAY từng giây chứ không chờ trong
;;; WScript.Shell Run: Run vẫn nhận bấm chuột khi LISP chưa xong (bấm nút, đổi tab bản vẽ giữa chừng), người dùng còn
;;; không biết lệnh đang chạy hay đã treo (bấm liền 4 lần, AutoCAD bị đóng 30/10/2026). DELAY cho bấm Esc để dừng chờ.
;;; Trong 90 giây không thấy tien_do.txt là PowerShell không chạy được: dừng, không chờ mãi.
(defun ct:cho-xong (out / xong td bt giay dong)
  (setq xong (strcat out "\\xong.txt") td (strcat out "\\tien_do.txt") bt "" giay 0)
  (while (and (not (findfile xong)) (< giay 3900) (or (<= giay 90) (findfile td)))
    (command "_.DELAY" 1000)
    (setq giay (1+ giay) dong (ct:dong-dau td))
    (if (and dong (/= dong bt))
      (progn
        (setq bt dong)
        (princ (cond ((= dong "1") "\nBước 1/2: nổ tường / cửa ACA trên bản sao, xuất DXF...")
                     ((= dong "2") "\nBước 2/2: dò phòng ướt...")
                     (""))))
    )
    (if (= 0 (rem giay 30)) (princ (strcat "\n  ... đã chạy " (itoa giay) " giây (Esc để dừng chờ)")))
  )
  ;; xong.txt vừa ghi có thể chưa đọc được ngay
  (setq dong (ct:dong-dau xong))
  (repeat 5 (if (and (null dong) (findfile xong)) (progn (command "_.DELAY" 200) (setq dong (ct:dong-dau xong)))))
  dong
)

;;; Bộ giải mã chép ra đĩa cùng các file base64: đổi base64 về đúng từng byte file gốc (tên file: "#" = "\")
(setq ct:*giai-ma*
  '("param([string]$Dich)"
    "$ErrorActionPreference = 'Stop'"
    "Get-ChildItem -LiteralPath (Join-Path $Dich 'b64') -Filter '*.b64' | ForEach-Object {"
    "    $ra = Join-Path $Dich ($_.BaseName.Replace('#', '\\'))"
    "    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ra) | Out-Null"
    "    $s = ([IO.File]::ReadAllText($_.FullName)) -replace '\\s', ''"
    "    [IO.File]::WriteAllBytes($ra, [Convert]::FromBase64String($s))"
    "}"
    "Set-Content -LiteralPath (Join-Path $Dich 'xong_giai_nen.txt') -Value 'OK' -Encoding ASCII"))

;;; Giải nén bộ nhận diện nhúng trong file này (ct:*ban*, ct:*tep* ở cuối file) ra <gốc>\_tools\chongtham_<bản>\.
;;; Đã giải nén bản này rồi thì dùng lại. Trả về thư mục (kết thúc "\\") hoặc nil.
(defun ct:giai-nen (/ dich b64 f)
  (cond
    ((not (and (boundp 'ct:*tep*) ct:*tep* ct:*ban*))
     (princ "\nFile CHONGTHAM.lsp này thiếu phần nhúng bộ nhận diện (bản nguồn chưa gộp): dùng file đã gộp.")
     nil)
    (t
     (setq dich (strcat (ct:goc) "\\_tools\\chongtham_" ct:*ban* "\\"))
     (if (not (findfile (strcat dich "xong_giai_nen.txt")))
       (progn
         (setq b64 (strcat dich "b64\\"))
         (ct:mkdir b64)
         (foreach tep ct:*tep*
           ;; tep = ("chong-tham-mat-bang/scripts/tim_phong_uot.py" "dòng base64" ...)
           (if (setq f (open (strcat b64 (vl-string-translate "/" "#" (car tep)) ".b64") "w"))
             (progn (foreach dong (cdr tep) (write-line dong f)) (close f))
           )
         )
         (if (setq f (open (strcat dich "giai_nen.ps1") "w"))
           (progn (foreach dong ct:*giai-ma* (write-line dong f)) (close f))
         )
         (ct:chay-ps (strcat dich "giai_nen.ps1") (strcat "-Dich \"" (vl-string-right-trim "\\" dich) "\"") nil)
       )
     )
     (if (findfile (strcat dich "xong_giai_nen.txt"))
       dich
       (progn (princ (strcat "\nKhông giải nén được bộ nhận diện vào " dich)) nil)
     )
    )
  )
)

;;; Thư mục tạm <gốc>\_tmp\ (máy này D:\AI\_tmp\), kết thúc "\\"
(defun ct:thu-muc-tam (/ kq)
  (setq kq (strcat (ct:goc) "\\_tmp\\"))
  (ct:mkdir kq)
  kq
)

;;; Tạo thư mục (kể cả thư mục cha còn thiếu). vl-mkdir chỉ tạo được 1 cấp: máy khác chưa có ..\_tmp thì hỏng.
(defun ct:mkdir (d / cha)
  (setq d (vl-string-right-trim "\\/" d))
  (if (not (vl-file-directory-p d))
    (progn
      (setq cha (vl-filename-directory d))
      (if (and cha (/= (strcase cha) (strcase d)) (> (strlen cha) 2)) (ct:mkdir cha))
      (vl-mkdir d)
    )
  )
  (vl-file-directory-p d)
)

;;; Mở file text, ưu tiên mã UTF-8 (AutoCAD 2021+); bản cũ không có tham số mã thì mở kiểu thường
(defun ct:mo (fn md / f)
  (setq f (vl-catch-all-apply 'open (list fn md "utf8")))
  (if (vl-catch-all-error-p f) (open fn md) f)
)

;;; ---------- Tiện ích ----------
(defun ct:khop (s pats) (and s (vl-some '(lambda (p) (wcmatch s p)) pats)))

;;; UNDO Begin / End: chỉ khi UNDO đang bật đầy đủ. Máy đặt UNDO Control None / One thì "_BE" không phải lựa chọn
;;; hợp lệ, lệnh UNDO hỏi lại và hỏng cả chuỗi lệnh phía sau.
(defun ct:undo-ok () (= 1 (logand 3 (getvar "UNDOCTL"))))

;;; Tên layer đưa vào lệnh -LAYER: thêm ` trước ký tự đại diện (# @ . * ? ~ [ ] , `). Layer ISO hậu tố "@"
;;; (vd. "A-WC@") nếu không thoát sẽ khớp nhầm cả layer khác.
(defun ct:esc (s / kq)
  (setq kq "")
  (foreach c (vl-string->list s)
    (setq kq (strcat kq (if (member c '(35 64 46 42 63 126 91 93 44 96)) "`" "") (chr c)))
  )
  kq
)

;;; setvar không dừng lệnh khi biến không có ở bản AutoCAD này / giá trị không hợp lệ
(defun ct:dat (b v) (if v (vl-catch-all-apply 'setvar (list b v))))

;;; Chuẩn hoá tên layer: bỏ tiền tố xref đã bind "...$0$" / đang attach "XREF|", bỏ dấu cách, "_" -> "-", chữ hoa
(defun ct:chuan (lay / l n i j bd)
  (setq l (vl-string->list lay) n (length l) i 0 bd 0)
  (while (< i n)
    (if (= (nth i l) 124) (setq bd (1+ i)))
    (if (= (nth i l) 36)
      (progn
        (setq j (1+ i))
        (while (and (< j n) (<= 48 (nth j l) 57)) (setq j (1+ j)))
        (if (and (> j (1+ i)) (< j n) (= (nth j l) 36)) (setq bd (1+ j)))
      )
    )
    (setq i (1+ i))
  )
  (repeat bd (setq l (cdr l)))
  (setq l (vl-remove 32 l))
  (setq l (mapcar '(lambda (c) (if (= c 95) 45 c)) l))
  (strcase (vl-list->string l))
)

(defun ct:ten-loai (s)
  (cond ((= s "wc") "WC") ((= s "lo_gia") "Lô gia / ban công") ((= s "phong_rac") "Phòng rác")
        ((= s "buong_dem_rac") "Buồng đệm phòng rác") ((= s "phong_kt_nuoc") "Phòng KT nước") (s))
)

;;; Đọc file dữ liệu do bộ dò Python ghi (mỗi dòng 1 biểu thức: (VUNG ...) hoặc (XEM ...))
(defun ct:doc (path / f dong ds)
  (if (setq f (open path "r"))
    (progn
      (while (setq dong (read-line f))
        (if (wcmatch dong "(*") (setq ds (cons (read dong) ds)))
      )
      (close f)
    )
  )
  (reverse ds)
)

;;; ---------- Vẽ ----------
(defun ct:tao-layer (ten)
  (if (not (tblsearch "LAYER" ten))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 ten) '(70 . 0) '(62 . 251) '(6 . "Continuous")))
  )
)

(defun ct:pl (pts kin mau rong lay)
  (entmake (append (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") (cons 8 lay) (cons 62 mau) '(6 . "Continuous")
                         '(100 . "AcDbPolyline") (cons 90 (length pts)) (cons 70 kin) (cons 43 rong))
                   (mapcar '(lambda (p) (cons 10 p)) pts)))
  (entlast)
)

;;; Vẽ các vùng "se_ve": trả về (số bo, số hatch, số nét vén, danh sách đối tượng mới)
(defun ct:ve (vung lay / moi nbo nhat nven e ss sl)
  (setq moi nil nbo 0 nhat 0 nven 0)
  (foreach v vung
    ;; v = (VUNG id loai trang_thai can bo dao ven)
    (setq ss (ssadd) e (ct:pl (nth 5 v) 1 3 0.0 lay) nbo (1+ nbo) moi (cons e moi))
    (ssadd e ss)
    (foreach d (nth 6 v) (setq e (ct:pl d 1 3 0.0 lay) moi (cons e moi)) (ssadd e ss))
    (setq sl (entlast))
    (command "_.-HATCH" "_P" "_U" "45" "400" "_Y" "_S" ss "" "")
    (if (and (not (equal (entlast) sl)) (= (cdr (assoc 0 (entget (entlast)))) "HATCH"))
      (setq nhat (1+ nhat) moi (cons (entlast) moi))
    )
    (foreach l (nth 7 v)
      (setq e (ct:pl (cadr l) (car l) 1 40.0 lay) nven (1+ nven) moi (cons e moi))
    )
  )
  (list nbo nhat nven moi)
)

;;; Gom đối tượng vừa vẽ vào 1 block, chèn lại tại 0,0 trên layer lay. Không định nghĩa lại block có sẵn.
(defun ct:gom-block (ds lay / ss ten goc i n)
  (setq ss (ssadd) goc (ct:cfg 'ten-block) ten goc i 1)
  (foreach e ds (if (entget e) (ssadd e ss)))
  (while (tblsearch "BLOCK" ten) (setq i (1+ i) ten (strcat goc " " (itoa i))))
  (if (> (sslength ss) 0)
    (progn
      (setq n (sslength ss))
      (command "_.-BLOCK" ten "0,0,0" ss "")
      (if (tblsearch "BLOCK" ten)
        (progn
          ;; tuỳ bản AutoCAD, -BLOCK xoá đối tượng gốc hoặc đổi thành block reference: chỉ chèn khi chưa có
          (if (not (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmake (list '(0 . "INSERT") '(100 . "AcDbEntity") (cons 8 lay) '(100 . "AcDbBlockReference")
                           (cons 2 ten) '(10 0.0 0.0 0.0) '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) '(50 . 0.0)))
          )
          (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmod (subst (cons 8 lay) (assoc 8 (entget (ssname ss 0))) (entget (ssname ss 0))))
          )
          (strcat ten " (" (itoa n) " đối tượng)")
        )
      )
    )
  )
)

;;; ---------- Làm mờ bản vẽ ----------
;;; Layer thuộc xref khung tên (attach "Xref - Khung A1|..." hoặc đã bind "Xref - Khung A1$0$..."): giữ màu, không tắt.
(defun ct:la-khung-ten (ten / i j goc)
  (setq goc nil)
  (if (setq i (vl-string-search "|" ten)) (setq goc (substr ten 1 i)))
  (if (and (null goc) (setq j (vl-string-search "$" ten))) (setq goc (substr ten 1 j)))
  (and goc (ct:khop (strcase goc) (ct:cfg 'khung-ten)))
)

(defun ct:lam-mo (lay / l ten an ls giu c tc)
  (setq ls (ct:cfg 'layer-state))
  (if (and layerstate-save (not (layerstate-has ls)))
    (layerstate-save ls (+ 1 32) nil)
  )
  (setq l (tblnext "LAYER" T) an nil giu nil)
  (while l
    (setq ten (cdr (assoc 2 l)))
    (cond
      ;; khung tên: ghi màu gốc (chỉ số + True Color) để trả lại sau khi đổi xám toàn bộ
      ((ct:la-khung-ten ten)
       (setq giu (cons (list ten (abs (cdr (assoc 62 l))) (cdr (assoc 420 (entget (tblobjname "LAYER" ten))))) giu)))
      ((and (/= (strcase ten) (strcase lay)) (ct:khop (ct:chuan ten) (ct:cfg 'layer-an)))
       (setq an (cons ten an)))
    )
    (setq l (tblnext "LAYER"))
  )
  (command "_.-LAYER" "_C" "_T" (ct:cfg 'mau-mo) "*" "")
  (foreach g giu
    (setq c (cadr g) tc (caddr g))
    (if tc
      (command "_.-LAYER" "_C" "_T"
               (strcat (itoa (/ tc 65536)) "," (itoa (rem (/ tc 256) 256)) "," (itoa (rem tc 256))) (ct:esc (car g)) "")
      (command "_.-LAYER" "_C" (itoa c) (ct:esc (car g)) "")
    )
  )
  ;; layer hiện hành không tắt được: chuyển sang layer vẽ trước
  (setvar "CLAYER" lay)
  (foreach n an (command "_.-LAYER" "_OFF" (ct:esc n) ""))
  (princ (strcat "\nĐã tắt " (itoa (length an)) " layer nội thất / thiết bị vệ sinh, đổi các layer khác sang màu "
                 (ct:cfg 'mau-mo) ", giữ màu " (itoa (length giu)) " layer khung tên"
                 (if layerstate-save (strcat ". Layer state cũ: \"" ls "\".") ".")))
  (length an)
)

;;; ---------- Vẽ từ file dữ liệu (dùng cho lệnh và cho chạy thử bằng Core Console) ----------
(defun ct:ve-tu-file (path / *error* bien cu lay ds vung xem kq tb dem k ucs undo)
  (defun *error* (msg)
    (if ucs (command-s "_.UCS" "_P"))
    (if cu (mapcar 'ct:dat bien cu))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*"))) (princ (strcat "\nLỗi: " msg)))
    (if undo (command-s "_.UNDO" "_E"))
    (princ)
  )
  ;; Biến máy / bản vẽ khác nhau giữa các máy làm sai kết quả, nên đặt tạm rồi trả lại:
  ;;   HPANNOTATIVE 1 -> hatch chú thích, khoảng cách nhân theo tỉ lệ chú thích;
  ;;   HPBACKGROUNDCOLOR / HPTRANSPARENCY đặt sẵn -> hatch có nền / trong suốt;
  ;;   UCS khác World -> -BLOCK "0,0,0" lấy theo UCS, block gom bị lệch vị trí (UCSFOLLOW 0 để không đổi view).
  (setq bien '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO" "TILEMODE" "HPISLANDDETECTION"
               "HPANNOTATIVE" "HPBACKGROUNDCOLOR" "HPTRANSPARENCY" "UCSFOLLOW")
        cu (mapcar 'getvar bien)
        lay (ct:cfg 'layer-ve))
  (setq ds (ct:doc path)
        vung (vl-remove-if-not '(lambda (x) (and (= (car x) 'VUNG) (= (nth 3 x) "se_ve"))) ds)
        xem (vl-remove-if-not '(lambda (x) (or (= (car x) 'XEM) (and (= (car x) 'VUNG) (= (nth 3 x) "can_xem")))) ds))
  ;; thống kê theo loại
  (setq dem nil)
  (foreach v vung
    (if (setq k (assoc (nth 2 v) dem)) (setq dem (subst (cons (car k) (1+ (cdr k))) k dem)) (setq dem (cons (cons (nth 2 v) 1) dem)))
  )
  (princ (strcat "\nSẽ vẽ " (itoa (length vung)) " phòng:"))
  (foreach k (reverse dem) (princ (strcat " " (ct:ten-loai (car k)) " " (itoa (cdr k)) ";")))
  (if vung
    (progn
      (setvar "CMDECHO" 0)
      (if (= (getvar "TILEMODE") 0) (setvar "TILEMODE" 1))
      (if (setq undo (ct:undo-ok)) (command "_.UNDO" "_BE"))
      (ct:dat "UCSFOLLOW" 0)
      (if (= 0 (getvar "WORLDUCS")) (progn (command "_.UCS" "_W") (setq ucs T)))
      (ct:tao-layer lay)
      (setvar "OSMODE" 0)
      (setvar "HPASSOC" 1)
      (ct:dat "HPLAYER" ".")
      (ct:dat "HPCOLOR" ".")
      (ct:dat "HPISLANDDETECTION" 1)
      (ct:dat "HPANNOTATIVE" 0)
      (ct:dat "HPBACKGROUNDCOLOR" ".")
      (ct:dat "HPTRANSPARENCY" ".")
      (setvar "CLAYER" lay)
      (setvar "CECOLOR" "3")
      (setq kq (ct:ve vung lay))
      (setvar "CECOLOR" "BYLAYER")
      (setq tb (ct:gom-block (cadddr kq) lay))
      (ct:lam-mo lay)
      (if ucs (progn (command "_.UCS" "_P") (setq ucs nil)))
      (mapcar 'ct:dat bien cu)
      (if undo (command "_.UNDO" "_E"))
      (princ (strcat "\nĐã vẽ " (itoa (car kq)) " đường bo, " (itoa (cadr kq)) " hatch, " (itoa (caddr kq))
                     " nét vén chân tường trên layer " lay ", block " (if tb tb "(không gom được)")
                     ". Ctrl+Z một lần để hoàn tác."))
    )
    (progn
      (mapcar 'ct:dat bien cu)
      (princ "\nKhông có phòng mới cần vẽ chống thấm.")
    )
  )
  (if xem
    (progn
      (princ (strcat "\nCần xem (không vẽ) " (itoa (length xem)) " chỗ:"))
      (foreach x xem
        (if (= (car x) 'XEM)
          (princ (strcat "\n  - " (ct:ten-loai (cadr x)) " tại " (rtos (caddr x) 2 0) ", " (rtos (cadddr x) 2 0)
                         ": không khép được phòng (" (nth 4 x) ")"))
          (princ (strcat "\n  - " (ct:ten-loai (nth 2 x)) " " (nth 4 x) " #" (itoa (nth 1 x))
                         ": phòng quá lớn, có thể gộp với phòng khác, quanh "
                         (rtos (car (car (nth 5 x))) 2 0) ", " (rtos (cadr (car (nth 5 x))) 2 0)))
        )
      )
    )
  )
  (length vung)
)

;;; Xref không tìm thấy file (dòng "tên|đường dẫn|" trong <tên>_xref.txt): phần đó không được nhận diện -> báo
(defun ct:xref-thieu (fn / f d)
  (if (and (findfile fn) (setq f (ct:mo fn "r")))
    (progn
      (while (setq d (read-line f))
        (if (wcmatch d "*|")
          (princ (strcat "\nXref không tìm thấy file, phần này chưa nhận diện: "
                         (substr d 1 (vl-string-search "|" d))))))
      (close f))))

;;; Python cho bộ nhận diện, KHÔNG CẦN CÀI (người dùng chốt 23/10/2026): gói Python mang theo CHONGTHAM_python
;;; (Python nhúng + thư viện, chỉ việc chép thư mục). Tìm: đã chọn / nhớ lần trước (setenv "ARCHIVINA_PYTHON")
;;; -> <gốc>\_tools\CHONGTHAM_python -> <ổ cứng>:\AI\_tools\CHONGTHAM_python. Trả về đường dẫn python.exe hoặc nil
;;; (nil: để chay_cho_lisp.ps1 tự tìm Python khác trên máy).
(defun ct:tim-python (/ f con)
  (setq con "\\_tools\\CHONGTHAM_python\\python.exe")
  (cond
    ((and (setq f (getenv "ARCHIVINA_PYTHON")) (setq f (findfile f))) f)
    ((findfile (strcat (ct:goc) con)))
    ((vl-some '(lambda (o) (findfile (strcat o "\\AI" con))) (ct:o-dia)))
  )
)

;;; Chạy bộ nhận diện ngầm (chay_cho_lisp.ps1) với python py (nil = tự tìm).
;;; Trả về dòng đầu của xong.txt ("OK" / "LOI ...") hoặc nil.
(defun ct:nhan-dien (sc dwg out py)
  (if (findfile (strcat out "\\xong.txt")) (vl-file-delete (strcat out "\\xong.txt")))
  (if (findfile (strcat out "\\tien_do.txt")) (vl-file-delete (strcat out "\\tien_do.txt")))
  (if (ct:chay-nen (strcat sc "chay_cho_lisp.ps1")
                   (strcat "-Dwg \"" dwg "\" -OutDir \"" out "\""
                           ;; thư mục bản vẽ đang mở: tìm xref đường dẫn tương đối (xref đọc riêng, không bind)
                           " -ThuMucGoc \"" (vl-string-right-trim "\\" (getvar "DWGPREFIX")) "\""
                           (if py (strcat " -Python \"" py "\"") "")))
    (ct:cho-xong out)
  )
)

;;; Ghi trạng thái hiện tại của bản vẽ ra dwg bằng -WBLOCK * (giữ tường / cửa ACA). Không lưu đè file của người dùng,
;;; không đổi tên bản vẽ đang mở. -WBLOCK lấy UCS hiện hành làm WCS của file mới: bản vẽ đang ở UCS xoay / dời gốc thì
;;; toạ độ bản tạm lệch so với bản vẽ, chống thấm vẽ sai chỗ -> chuyển UCS World trước khi ghi, xong trả lại.
;;; Lệnh dừng giữa chừng thì huỷ, không để treo lại lời nhắc. Trả về T nếu có file.
(defun ct:ghi-ban-tam (dwg / uf ucs)
  (if (= 0 (getvar "WORLDUCS"))
    (progn
      (setq uf (getvar "UCSFOLLOW") ucs T)
      (setvar "UCSFOLLOW" 0)
      (command "_.UCS" "_W")
    )
  )
  (vl-cmdf "_.-WBLOCK" dwg "*")
  (if (= 1 (logand 1 (getvar "CMDACTIVE"))) (command))
  (if ucs
    (progn
      (command "_.UCS" "_P")
      (setvar "UCSFOLLOW" uf)
    )
  )
  (if (findfile dwg) T)
)

;;; Không tìm thấy Python: hướng dẫn chép gói mang theo; cho chọn python.exe (nhớ cho lần sau) hoặc cài gói qua mạng.
;;; Trả về đường dẫn python.exe đã chọn, T nếu cài gói xong, nil nếu bỏ qua.
(defun ct:thieu-python (sc out / kq f dong)
  (princ (strcat "\nKhông tìm thấy Python cho bộ nhận diện. KHÔNG CẦN CÀI: chép thư mục CHONGTHAM_python (gói Python"
                 " mang theo) vào <ổ>:\\AI\\_tools\\ (vd. D:\\AI\\_tools\\CHONGTHAM_python) rồi gõ lại CHONGTHAM."
                 "\n  Chon  = chọn python.exe trong thư mục CHONGTHAM_python đang để chỗ khác (lệnh nhớ cho lần sau)"
                 "\n  Cai   = cài gói Python qua mạng (máy đã có Python 3)"))
  (initget "Chon Khong Cai")
  (setq kq (getkword "\n[Chon/Khong/Cai] <Khong>: "))
  (cond
    ((= kq "Chon")
     (if (setq f (getfiled "Chọn python.exe trong thư mục CHONGTHAM_python" "python.exe" "exe" 0))
       (progn (setenv "ARCHIVINA_PYTHON" f) (princ "\nChạy lại nhận diện...") f)
     )
    )
    ((= kq "Cai")
     (ct:chay-ps (strcat sc "cai_dat_python.ps1") (strcat "-Dung -KetQua \"" out "\\cai_dat.txt\"") T)
     (setq f (open (strcat out "\\cai_dat.txt") "r") dong (if f (read-line f)))
     (if f (close f))
     (cond
       ((= dong "OK") (princ "\nĐã cài gói Python, chạy lại nhận diện...") T)
       (t (princ (strcat "\nCài gói Python không xong: " (if dong dong "không có kết quả"))) nil)
     )
    )
  )
)

;;; ---------- Lệnh ----------
(defun c:CHONGTHAM (/ *error* ce dwg tg out goc sc dong n py)
  (defun *error* (msg)
    (if ce (setvar "CMDECHO" ce))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nLỗi: " msg))
      (princ "\nĐã dừng chờ, chưa vẽ gì. Bộ nhận diện chạy ngầm tự kết thúc, không ảnh hưởng bản vẽ.")
    )
    (princ)
  )
  (cond
    ;; -WBLOCK và lệnh vẽ không chạy trong Block Editor / REFEDIT
    ((= 1 (getvar "BLOCKEDITOR"))
     (princ "\nĐang mở Block Editor: đóng lại (BCLOSE) rồi chạy CHONGTHAM."))
    ((/= "" (getvar "REFEDITNAME"))
     (princ "\nĐang sửa block tại chỗ (REFEDIT): đóng lại (REFCLOSE) rồi chạy CHONGTHAM."))
    ((not (setq sc (ct:giai-nen))))
    (t
     (setq sc (strcat sc "chong-tham-mat-bang\\scripts\\")
           goc (ct:thu-muc-tam))
     ;; thư mục kết quả theo giờ; chạy 2 lần trong cùng giây thì thêm số
     (setq tg (vl-string-translate "." "_" (rtos (getvar "CDATE") 2 6))
           out (strcat goc "chongtham_lisp_" tg)
           n 1)
     (while (vl-file-directory-p out)
       (setq n (1+ n) out (strcat goc "chongtham_lisp_" tg "_" (itoa n))))
     (ct:mkdir out)
     ;; Không hỏi lưu (người dùng chốt 23/10/2026): gõ lệnh là ra kết quả.
     (if (and (= (getvar "DWGTITLED") 1) (= (getvar "DBMOD") 0))
       ;; bản vẽ đã lưu, không có thay đổi: đọc thẳng file trên đĩa (script tự chép bản sao, không sửa file)
       (setq dwg (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))
       ;; có thay đổi chưa lưu / chưa lưu lần nào: ghi trạng thái hiện tại ra bản tạm. Không ghi được thì dùng file đã
       ;; lưu trên đĩa và báo rõ (bản đầu dừng ngay, người dùng bấm 4 lần chỉ ra thư mục rỗng, 30/10/2026).
       (progn
         (setq dwg (strcat out "\\" (vl-filename-base (getvar "DWGNAME")) ".dwg"))
         (if (and (vl-file-directory-p out) (not (ct:ghi-ban-tam dwg)) (= (getvar "DWGTITLED") 1))
           (progn
             (setq dwg (strcat (getvar "DWGPREFIX") (getvar "DWGNAME")))
             (princ "\nKhông ghi được bản tạm: nhận diện theo FILE ĐÃ LƯU, các thay đổi chưa lưu không được tính.")
           )
         )
       )
     )
     (cond
       ((not (vl-file-directory-p out))
        (princ (strcat "\nKhông tạo được thư mục tạm: " out)))
       ((not (findfile dwg))
        (princ (strcat "\nKhông ghi được bản tạm của bản vẽ: " dwg ". Lưu bản vẽ (QSAVE) rồi chạy lại.")))
       (t
        (princ "\nĐang nhận diện phòng ướt trên bản sao (chạy ngầm, khoảng 1 - 6 phút). Không bấm gì thêm, Esc để dừng chờ...")
        ;; hiện dòng thông báo trước khi AutoCAD chờ tiến trình ngầm
        (if (vl-cmdf "_.DELAY" 1) nil)
        ;; CMDECHO 0: không in dòng lệnh DELAY mỗi giây
        (setq ce (getvar "CMDECHO"))
        (setvar "CMDECHO" 0)
        (setq py (ct:tim-python) dong (ct:nhan-dien sc dwg out py))
        ;; thiếu Python: hướng dẫn chép gói mang theo / chọn python.exe / cài, rồi chạy lại một lần
        (if (and dong (wcmatch dong "*tim thay Python*") (setq py (ct:thieu-python sc out)))
          (setq dong (ct:nhan-dien sc dwg out (if (= py T) nil py)))
        )
        (setvar "CMDECHO" ce)
        (setq ce nil)
        (if (and dong (= dong "OK") (findfile (strcat out "\\du_lieu.txt")))
          (progn
            (ct:ve-tu-file (strcat out "\\du_lieu.txt"))
            (princ (strcat "\nẢnh xem lại: " out))
            (ct:xref-thieu (strcat out "\\" (vl-filename-base dwg) "_xref.txt")))
          (princ (strcat "\nNhận diện lỗi: " (if dong dong "không có kết quả (máy chặn PowerShell / Windows Script Host?)")
                         ".\nXem nhật ký: " out "\\nhat_ky.txt"))
        )
       )
     )
    )
  )
  (princ)
)

;;; LISPSYS khác 1 (bộ LISP cũ): file UTF-8 đọc sai dấu tiếng Việt -> nhắc đổi (thông báo không dấu để đọc được)
(if (/= 1 (getvar "LISPSYS"))
  (princ "\nCANH BAO: LISPSYS khac 1 - thong bao tieng Viet se loi font. Go LISPSYS, dat 1, khoi dong lai AutoCAD.")
)

(princ "\nĐã nạp lệnh CHONGTHAM: vẽ mặt bằng chống thấm (WC, lô gia, phòng rác, buồng đệm, phòng KT nước).")
(princ)

;;; @@NHUNG_BO_NHAN_DIEN@@
