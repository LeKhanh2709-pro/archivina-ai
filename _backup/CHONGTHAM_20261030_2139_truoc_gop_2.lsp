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
        (princ (cond ((= dong "1") "\nB\\U+01B0\\U+1EDBc 1/2: n\\U+1ED5 t\\U+01B0\\U+1EDDng / c\\U+1EEDa ACA tr\\U+00EAn b\\U+1EA3n sao, xu\\U+1EA5t DXF...")
                     ((= dong "2") "\nB\\U+01B0\\U+1EDBc 2/2: d\\U+00F2 ph\\U+00F2ng \\U+01B0\\U+1EDBt...")
                     (""))))
    )
    (if (= 0 (rem giay 30)) (princ (strcat "\n  ... \\U+0111\\U+00E3 ch\\U+1EA1y " (itoa giay) " gi\\U+00E2y (Esc \\U+0111\\U+1EC3 d\\U+1EEBng ch\\U+1EDD)")))
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
     (princ "\nFile CHONGTHAM.lsp n\\U+00E0y thi\\U+1EBFu ph\\U+1EA7n nh\\U+00FAng b\\U+1ED9 nh\\U+1EADn di\\U+1EC7n (b\\U+1EA3n ngu\\U+1ED3n ch\\U+01B0a g\\U+1ED9p): d\\U+00F9ng file \\U+0111\\U+00E3 g\\U+1ED9p.")
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
       (progn (princ (strcat "\nKh\\U+00F4ng gi\\U+1EA3i n\\U+00E9n \\U+0111\\U+01B0\\U+1EE3c b\\U+1ED9 nh\\U+1EADn di\\U+1EC7n v\\U+00E0o " dich)) nil)
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
  (cond ((= s "wc") "WC") ((= s "lo_gia") "L\\U+00F4 gia / ban c\\U+00F4ng") ((= s "phong_rac") "Ph\\U+00F2ng r\\U+00E1c")
        ((= s "buong_dem_rac") "Bu\\U+1ED3ng \\U+0111\\U+1EC7m ph\\U+00F2ng r\\U+00E1c") ((= s "phong_kt_nuoc") "Ph\\U+00F2ng KT n\\U+01B0\\U+1EDBc") (s))
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
          (strcat ten " (" (itoa n) " \\U+0111\\U+1ED1i t\\U+01B0\\U+1EE3ng)")
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
  (princ (strcat "\n\\U+0110\\U+00E3 t\\U+1EAFt " (itoa (length an)) " layer n\\U+1ED9i th\\U+1EA5t / thi\\U+1EBFt b\\U+1ECB v\\U+1EC7 sinh, \\U+0111\\U+1ED5i c\\U+00E1c layer kh\\U+00E1c sang m\\U+00E0u "
                 (ct:cfg 'mau-mo) ", gi\\U+1EEF m\\U+00E0u " (itoa (length giu)) " layer khung t\\U+00EAn"
                 (if layerstate-save (strcat ". Layer state c\\U+0169: \"" ls "\".") ".")))
  (length an)
)

;;; ---------- Vẽ từ file dữ liệu (dùng cho lệnh và cho chạy thử bằng Core Console) ----------
(defun ct:ve-tu-file (path / *error* bien cu lay ds vung xem kq tb dem k ucs undo)
  (defun *error* (msg)
    (if ucs (command-s "_.UCS" "_P"))
    (if cu (mapcar 'ct:dat bien cu))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*"))) (princ (strcat "\nL\\U+1ED7i: " msg)))
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
  (princ (strcat "\nS\\U+1EBD v\\U+1EBD " (itoa (length vung)) " ph\\U+00F2ng:"))
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
      (princ (strcat "\n\\U+0110\\U+00E3 v\\U+1EBD " (itoa (car kq)) " \\U+0111\\U+01B0\\U+1EDDng bo, " (itoa (cadr kq)) " hatch, " (itoa (caddr kq))
                     " n\\U+00E9t v\\U+00E9n ch\\U+00E2n t\\U+01B0\\U+1EDDng tr\\U+00EAn layer " lay ", block " (if tb tb "(kh\\U+00F4ng gom \\U+0111\\U+01B0\\U+1EE3c)")
                     ". Ctrl+Z m\\U+1ED9t l\\U+1EA7n \\U+0111\\U+1EC3 ho\\U+00E0n t\\U+00E1c."))
    )
    (progn
      (mapcar 'ct:dat bien cu)
      (princ "\nKh\\U+00F4ng c\\U+00F3 ph\\U+00F2ng m\\U+1EDBi c\\U+1EA7n v\\U+1EBD ch\\U+1ED1ng th\\U+1EA5m.")
    )
  )
  (if xem
    (progn
      (princ (strcat "\nC\\U+1EA7n xem (kh\\U+00F4ng v\\U+1EBD) " (itoa (length xem)) " ch\\U+1ED7:"))
      (foreach x xem
        (if (= (car x) 'XEM)
          (princ (strcat "\n  - " (ct:ten-loai (cadr x)) " t\\U+1EA1i " (rtos (caddr x) 2 0) ", " (rtos (cadddr x) 2 0)
                         ": kh\\U+00F4ng kh\\U+00E9p \\U+0111\\U+01B0\\U+1EE3c ph\\U+00F2ng (" (nth 4 x) ")"))
          (princ (strcat "\n  - " (ct:ten-loai (nth 2 x)) " " (nth 4 x) " #" (itoa (nth 1 x))
                         ": ph\\U+00F2ng qu\\U+00E1 l\\U+1EDBn, c\\U+00F3 th\\U+1EC3 g\\U+1ED9p v\\U+1EDBi ph\\U+00F2ng kh\\U+00E1c, quanh "
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
          (princ (strcat "\nXref kh\\U+00F4ng t\\U+00ECm th\\U+1EA5y file, ph\\U+1EA7n n\\U+00E0y ch\\U+01B0a nh\\U+1EADn di\\U+1EC7n: "
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
  (vl-catch-all-apply 'command (list "_.-WBLOCK" dwg "*"))
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
  (princ (strcat "\nKh\\U+00F4ng t\\U+00ECm th\\U+1EA5y Python cho b\\U+1ED9 nh\\U+1EADn di\\U+1EC7n. KH\\U+00D4NG C\\U+1EA6N C\\U+00C0I: ch\\U+00E9p th\\U+01B0 m\\U+1EE5c CHONGTHAM_python (g\\U+00F3i Python"
                 " mang theo) v\\U+00E0o <\\U+1ED5>:\\AI\\_tools\\ (vd. D:\\AI\\_tools\\CHONGTHAM_python) r\\U+1ED3i g\\U+00F5 l\\U+1EA1i CHONGTHAM."
                 "\n  Chon  = ch\\U+1ECDn python.exe trong th\\U+01B0 m\\U+1EE5c CHONGTHAM_python \\U+0111ang \\U+0111\\U+1EC3 ch\\U+1ED7 kh\\U+00E1c (l\\U+1EC7nh nh\\U+1EDB cho l\\U+1EA7n sau)"
                 "\n  Cai   = c\\U+00E0i g\\U+00F3i Python qua m\\U+1EA1ng (m\\U+00E1y \\U+0111\\U+00E3 c\\U+00F3 Python 3)"))
  (initget "Chon Khong Cai")
  (setq kq (getkword "\n[Chon/Khong/Cai] <Khong>: "))
  (cond
    ((= kq "Chon")
     (if (setq f (getfiled "Ch\\U+1ECDn python.exe trong th\\U+01B0 m\\U+1EE5c CHONGTHAM_python" "python.exe" "exe" 0))
       (progn (setenv "ARCHIVINA_PYTHON" f) (princ "\nCh\\U+1EA1y l\\U+1EA1i nh\\U+1EADn di\\U+1EC7n...") f)
     )
    )
    ((= kq "Cai")
     (ct:chay-ps (strcat sc "cai_dat_python.ps1") (strcat "-Dung -KetQua \"" out "\\cai_dat.txt\"") T)
     (setq f (open (strcat out "\\cai_dat.txt") "r") dong (if f (read-line f)))
     (if f (close f))
     (cond
       ((= dong "OK") (princ "\n\\U+0110\\U+00E3 c\\U+00E0i g\\U+00F3i Python, ch\\U+1EA1y l\\U+1EA1i nh\\U+1EADn di\\U+1EC7n...") T)
       (t (princ (strcat "\nC\\U+00E0i g\\U+00F3i Python kh\\U+00F4ng xong: " (if dong dong "kh\\U+00F4ng c\\U+00F3 k\\U+1EBFt qu\\U+1EA3"))) nil)
     )
    )
  )
)

;;; ---------- Lệnh ----------
(defun c:CHONGTHAM (/ *error* ce dwg tg out goc sc dong n py)
  (defun *error* (msg)
    (if ce (setvar "CMDECHO" ce))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nL\\U+1ED7i: " msg))
      (princ "\n\\U+0110\\U+00E3 d\\U+1EEBng ch\\U+1EDD, ch\\U+01B0a v\\U+1EBD g\\U+00EC. B\\U+1ED9 nh\\U+1EADn di\\U+1EC7n ch\\U+1EA1y ng\\U+1EA7m t\\U+1EF1 k\\U+1EBFt th\\U+00FAc, kh\\U+00F4ng \\U+1EA3nh h\\U+01B0\\U+1EDFng b\\U+1EA3n v\\U+1EBD.")
    )
    (princ)
  )
  (cond
    ;; -WBLOCK và lệnh vẽ không chạy trong Block Editor / REFEDIT
    ((= 1 (getvar "BLOCKEDITOR"))
     (princ "\n\\U+0110ang m\\U+1EDF Block Editor: \\U+0111\\U+00F3ng l\\U+1EA1i (BCLOSE) r\\U+1ED3i ch\\U+1EA1y CHONGTHAM."))
    ((/= "" (getvar "REFEDITNAME"))
     (princ "\n\\U+0110ang s\\U+1EEDa block t\\U+1EA1i ch\\U+1ED7 (REFEDIT): \\U+0111\\U+00F3ng l\\U+1EA1i (REFCLOSE) r\\U+1ED3i ch\\U+1EA1y CHONGTHAM."))
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
             (princ "\nKh\\U+00F4ng ghi \\U+0111\\U+01B0\\U+1EE3c b\\U+1EA3n t\\U+1EA1m: nh\\U+1EADn di\\U+1EC7n theo FILE \\U+0110\\U+00C3 L\\U+01AFU, c\\U+00E1c thay \\U+0111\\U+1ED5i ch\\U+01B0a l\\U+01B0u kh\\U+00F4ng \\U+0111\\U+01B0\\U+1EE3c t\\U+00EDnh.")
           )
         )
       )
     )
     (cond
       ((not (vl-file-directory-p out))
        (princ (strcat "\nKh\\U+00F4ng t\\U+1EA1o \\U+0111\\U+01B0\\U+1EE3c th\\U+01B0 m\\U+1EE5c t\\U+1EA1m: " out)))
       ((not (findfile dwg))
        (princ (strcat "\nKh\\U+00F4ng ghi \\U+0111\\U+01B0\\U+1EE3c b\\U+1EA3n t\\U+1EA1m c\\U+1EE7a b\\U+1EA3n v\\U+1EBD: " dwg ". L\\U+01B0u b\\U+1EA3n v\\U+1EBD (QSAVE) r\\U+1ED3i ch\\U+1EA1y l\\U+1EA1i.")))
       (t
        (princ "\n\\U+0110ang nh\\U+1EADn di\\U+1EC7n ph\\U+00F2ng \\U+01B0\\U+1EDBt tr\\U+00EAn b\\U+1EA3n sao (ch\\U+1EA1y ng\\U+1EA7m, kho\\U+1EA3ng 1 - 6 ph\\U+00FAt). Kh\\U+00F4ng b\\U+1EA5m g\\U+00EC th\\U+00EAm, Esc \\U+0111\\U+1EC3 d\\U+1EEBng ch\\U+1EDD...")
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
            (princ (strcat "\n\\U+1EA2nh xem l\\U+1EA1i: " out))
            (ct:xref-thieu (strcat out "\\" (vl-filename-base dwg) "_xref.txt")))
          (princ (strcat "\nNh\\U+1EADn di\\U+1EC7n l\\U+1ED7i: " (if dong dong "kh\\U+00F4ng c\\U+00F3 k\\U+1EBFt qu\\U+1EA3 (m\\U+00E1y ch\\U+1EB7n PowerShell / Windows Script Host?)")
                         ".\nXem nh\\U+1EADt k\\U+00FD: " out "\\nhat_ky.txt"))
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

(princ "\n\\U+0110\\U+00E3 n\\U+1EA1p l\\U+1EC7nh CHONGTHAM: v\\U+1EBD m\\U+1EB7t b\\U+1EB1ng ch\\U+1ED1ng th\\U+1EA5m (WC, l\\U+00F4 gia, ph\\U+00F2ng r\\U+00E1c, bu\\U+1ED3ng \\U+0111\\U+1EC7m, ph\\U+00F2ng KT n\\U+01B0\\U+1EDBc).")
(princ)

;;; ==================== BO NHAN DIEN NHUNG SAN (gop tu dong boi gop_chongtham.ps1, KHONG SUA TAY) ====================
;;; Ban 0bf2d7a7d2, gop 2026-10-30 21:38: chong-tham-mat-bang/scripts/chay_cho_lisp.ps1, chong-tham-mat-bang/scripts/dwg_to_dxf_aec.ps1, chong-tham-mat-bang/scripts/tim_accoreconsole.ps1, chong-tham-mat-bang/scripts/moi_truong.ps1, chong-tham-mat-bang/scripts/cai_dat_python.ps1, chong-tham-mat-bang/scripts/tim_phong_uot.py, dien-tich-ch/scripts/tao_polyline_phong.py, dien-tich-ch/scripts/chinh_hinh.py
(setq ct:*ban* "0bf2d7a7d2")
(setq ct:*tep* '(
("chong-tham-mat-bang/scripts/chay_cho_lisp.ps1"
"PCMKLlNZTk9QU0lTCiAgICBDaGF5IG5lbiBjaG8gbGVuaCBMSVNQIENIT05HVEhBTTogbm8gQUVDIHRyZW4gYmFuIHNhbyBEV0cgLT4gRFhGLCBkbyBwaG9uZyB1b3QgLT4gZmlsZSBkdSBsaWV1IGNobyBMSVNQLgoKLkRFU0NSSVBUSU9OCiAgICBMZW5oIENIT05H"
"VEhBTSAoQ0hPTkdUSEFNLmxzcCkgZ29pIHNjcmlwdCBuYXkgdmEgY2hvIG5vIGNoYXkgeG9uZywgcm9pIGRvYyA8T3V0RGlyPlxkdV9saWV1LnR4dAogICAgZGUgdmUgdmFvIGJhbiB2ZSBkYW5nIG1vLiBLaG9uZyBkb25nIHZhbyBmaWxlIERXRyBnb2MgKGR3Z190"
"b19keGZfYWVjLnBzMSBjaGVwIGJhbiBzYW8gdmFvIHRodSBtdWMgdGFtKS4KICAgIEtldCBxdWE6IDxPdXREaXI+XGR1X2xpZXUudHh0LCA8dGVuPl9jaG9uZ3RoYW0uanNvbiAvIC5wbmcgKGtob25nIHRhbyBFeGNlbCksIDxPdXREaXI+XHhvbmcudHh0ICgiT0si"
"IGhvYWMgIkxPSSAuLi4iKSwKICAgIDxPdXREaXI+XG5oYXRfa3kudHh0ICh0b2FuIGJvIHRob25nIGJhbywgZGUgeGVtIGtoaSBsb2kgbyBtYXkga2hhYykuCiAgICBQeXRob24gLyBBdXRvQ0FEIHR1IHRpbSB0cmVuIG1heSAobW9pX3RydW9uZy5wczEpLCBraG9u"
"ZyBnYW4gY3VuZyBkdW9uZyBkYW4uCgouRVhBTVBMRQogICAgcG93ZXJzaGVsbCAtTm9Qcm9maWxlIC1FeGVjdXRpb25Qb2xpY3kgQnlwYXNzIC1GaWxlIGNoYXlfY2hvX2xpc3AucHMxIC1Ed2cgIkQ6XC4uLlxNQiB0YW5nIDQuZHdnIiAtT3V0RGlyICJEOlxBSVxf"
"dG1wXGNob25ndGhhbV9saXNwX3giCiM+CnBhcmFtKAogICAgW1BhcmFtZXRlcihNYW5kYXRvcnkgPSAkdHJ1ZSldW3N0cmluZ10kRHdnLAogICAgW1BhcmFtZXRlcihNYW5kYXRvcnkgPSAkdHJ1ZSldW3N0cmluZ10kT3V0RGlyLAogICAgIyBkZSB0cm9uZzogdHUg"
"dGltIChtb2lfdHJ1b25nLnBzMSAvIEZpbmQtUHl0aG9uKQogICAgW3N0cmluZ10kUHl0aG9uID0gJycsCiAgICAjIHRodSBtdWMgYmFuIHZlIGRhbmcgbW8gKGRlIHRpbSB4cmVmIGR1b25nIGRhbiB0dW9uZyBkb2kga2hpIC1Ed2cgbGEgYmFuIHRhbSAtV0JMT0NL"
"KQogICAgW3N0cmluZ10kVGh1TXVjR29jID0gJycKKQokRXJyb3JBY3Rpb25QcmVmZXJlbmNlID0gJ1N0b3AnCk5ldy1JdGVtIC1JdGVtVHlwZSBEaXJlY3RvcnkgLUZvcmNlIC1QYXRoICRPdXREaXIgfCBPdXQtTnVsbAokeG9uZyA9IEpvaW4tUGF0aCAkT3V0RGly"
"ICd4b25nLnR4dCcKIyB0aWVuX2RvLnR4dDogYnVvYyBkYW5nIGNoYXkgKDEgLyAyKSwgbGVuaCBMSVNQIGRvYyBkZSBiYW8gbyBkb25nIGxlbmggdmEgYmlldCBQb3dlclNoZWxsIGRhIGNoYXkgZHVvYwokdGllbkRvID0gSm9pbi1QYXRoICRPdXREaXIgJ3RpZW5f"
"ZG8udHh0JwpTZXQtQ29udGVudCAtTGl0ZXJhbFBhdGggJHRpZW5EbyAtVmFsdWUgJzEnIC1FbmNvZGluZyBBU0NJSQp0cnkgeyBTdGFydC1UcmFuc2NyaXB0IC1MaXRlcmFsUGF0aCAoSm9pbi1QYXRoICRPdXREaXIgJ25oYXRfa3kudHh0JykgLUZvcmNlIHwgT3V0"
"LU51bGwgfSBjYXRjaCB7fQp0cnkgewogICAgLiAoSm9pbi1QYXRoICRQU1NjcmlwdFJvb3QgJ21vaV90cnVvbmcucHMxJykKICAgICRweSA9IEZpbmQtUHl0aG9uIC1QeXRob24gJFB5dGhvbiAtR29pIEAoJ2V6ZHhmJywgJ3NoYXBlbHknLCAnbWF0cGxvdGxpYicp"
"CiAgICBXcml0ZS1Ib3N0ICJQeXRob246ICRweSIKICAgIFdyaXRlLUhvc3QgJ0NIT05HVEhBTSAtIGJ1b2MgMS8yOiBubyB0dW9uZyAvIGN1YSBBQ0EgdHJlbiBiYW4gc2FvLCB4dWF0IERYRiAodmFpIHBodXQpLi4uJwogICAgJGtxID0gJiAoSm9pbi1QYXRoICRQ"
"U1NjcmlwdFJvb3QgJ2R3Z190b19keGZfYWVjLnBzMScpIC1Ed2cgJER3ZyAtT3V0RGlyICRPdXREaXIgLVRodU11Y0dvYyAkVGh1TXVjR29jCiAgICAka3EgfCBGb3JFYWNoLU9iamVjdCB7IFdyaXRlLUhvc3QgJF8gfQogICAgJGR4ZiA9IEpvaW4tUGF0aCAkT3V0"
"RGlyIChbSU8uUGF0aF06OkdldEZpbGVOYW1lV2l0aG91dEV4dGVuc2lvbigkRHdnKSArICcuZHhmJykKICAgIGlmICgtbm90IChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRkeGYpKSB7IHRocm93ICJLaG9uZyB0YW8gZHVvYyBEWEY6ICRrcSIgfQogICAgV3JpdGUt"
"SG9zdCAnQ0hPTkdUSEFNIC0gYnVvYyAyLzI6IGRvIHBob25nIHVvdCAoV0MsIGxvIGdpYSwgcGhvbmcgcmFjLCBwaG9uZyBLVCBudW9jKS4uLicKICAgIFNldC1Db250ZW50IC1MaXRlcmFsUGF0aCAkdGllbkRvIC1WYWx1ZSAnMicgLUVuY29kaW5nIEFTQ0lJCiAg"
"ICAkZW52OlBZVEhPTlVURjggPSAnMScKICAgICYgJHB5IC1JIC1YIHV0ZjggKEpvaW4tUGF0aCAkUFNTY3JpcHRSb290ICd0aW1fcGhvbmdfdW90LnB5JykgJGR4ZiAtLW91dC1kaXIgJE91dERpciAtLXh1YXQtbHNwIChKb2luLVBhdGggJE91dERpciAnZHVfbGll"
"dS50eHQnKQogICAgaWYgKCRMQVNURVhJVENPREUgLW5lIDApIHsgdGhyb3cgInRpbV9waG9uZ191b3QucHkgbG9pIChtYSAkTEFTVEVYSVRDT0RFKSIgfQogICAgU2V0LUNvbnRlbnQgLUxpdGVyYWxQYXRoICR4b25nIC1WYWx1ZSAnT0snIC1FbmNvZGluZyBBU0NJ"
"SQp9CmNhdGNoIHsKICAgICMgeG9uZy50eHQgY2hpIEFTQ0lJOiBMSVNQIGRvYyBiYW5nIHJlYWQtbGluZSwgdGhvbmcgYmFvIGxvaSBraG9uZyBkYXUKICAgIFNldC1Db250ZW50IC1MaXRlcmFsUGF0aCAkeG9uZyAtVmFsdWUgKCdMT0kgJyArICRfLkV4Y2VwdGlv"
"bi5NZXNzYWdlKSAtRW5jb2RpbmcgQVNDSUkKICAgIFdyaXRlLUhvc3QgKCdMT0k6ICcgKyAkXy5FeGNlcHRpb24uTWVzc2FnZSkKICAgIHRyeSB7IFN0b3AtVHJhbnNjcmlwdCB8IE91dC1OdWxsIH0gY2F0Y2gge30KICAgIGV4aXQgMQp9CnRyeSB7IFN0b3AtVHJh"
"bnNjcmlwdCB8IE91dC1OdWxsIH0gY2F0Y2gge30K"
)
("chong-tham-mat-bang/scripts/dwg_to_dxf_aec.ps1"
"PCMKLlNZTk9QU0lTCiAgICBDaHV5ZW4gRFdHIHNhbmcgRFhGLCBLRU0gbm8gZG9pIHR1b25nIEF1dG9DQUQgQXJjaGl0ZWN0dXJlICh0dW9uZywgY3VhLCBjdWEgc28gQUNBKSB0aGFuaCBoaW5oIGhvYyB0aHVvbmcsCiAgICB0cmVuIEJBTiBTQU8uIEtob25nIGRv"
"bmcgdmFvIGZpbGUgZ29jLgoKLkRFU0NSSVBUSU9OCiAgICBEdWEgdHJlbiBkaWVuLXRpY2gtY2hcc2NyaXB0c1xkd2dfdG9fZHhmX2FlYy5wczEuIE1hdCBiYW5nIHRhbmcgQVJDSElWSU5BOiBjYW4gaG8gbGEgYmxvY2sgIkNIeHggKFQ0KSIgY2hlbiB0YWkgMCww"
"LAogICAgdHVvbmcgLyBjdWEgdHJvbmcgYmxvY2sgbGEgQUVDIC0+IERYRk9VVCB0aHVvbmcgbGFtIG1hdCB0dW9uZy4gQ2FjaCBsYW06IG5vIGNhYyBJTlNFUlQgY28gY2h1YSBBRUMgKHRvaSAzIGNhcCksCiAgICByb2kgbm8gdHVuZyBkb2kgdHVvbmcgQUVDLCBy"
"b2kgRFhGT1VUIDIwMTguIFNhdSBraGkgbm8sIGJsb2NrIHRoaWV0IGJpIGxvbmcgYmVuIHRyb25nIGdpdSB0ZW4KICAgICJDSHh4IChUNCkkMCQ8dGVuPiIgbmVuIHZhbiBiaWV0IHRoaWV0IGJpIHRodW9jIGNhbiBuYW8uCiAgICBDb3JlIENvbnNvbGUgdGltIGJh"
"bmcgdGltX2FjY29yZWNvbnNvbGUucHMxIChrZW0gL3Byb2R1Y3QgQUNBIG5ldSBtYXkgY28gQXV0b0NBRCBBcmNoaXRlY3R1cmUpLiBUaHUgbXVjIHRhbSB0aW0gYmFuZwogICAgbW9pX3RydW9uZy5wczEgKG1heSBEOlxBSTogRDpcQUlcX3RtcDsgbWF5IGtoYWM6"
"IDxnb2M+XF90bXAgaG9hYyAlTE9DQUxBUFBEQVRBJVxBUkNISVZJTkFcX3RtcCkuCiAgICBHaGkgPHRlbj5fYWVjLnR4dCAoZGVtIEFFQyB0cnVvYyAvIHNhdSBraGkgbm8pIGNhbmggZmlsZSBEWEYuCiAgICBCYW4gdmUgbHV1IGtoaSBkYW5nIG8gVUNTIHhvYXkg"
"KGNhbmggbmhhIHhvYXkpOiBjaHV5ZW4gVUNTIFdvcmxkIHRydW9jIGtoaSBubywgZGUga2V0IHF1YSBubyBBRUMga2hvbmcgcGh1IHRodW9jIFVDUy4KICAgIFhyZWYgbmdvYWkgKHZkLiBDVDI6IG1vaSBjYW4gaG8gbGEgeHJlZiBvIEE6XC4uLik6IEtIT05HIGJp"
"bmQsIGtlIGNhIHRyZW4gYmFuIHNhbyAobmd1b2kgZHVuZyBjaG90IDIzLzEwLzIwMjYpLgogICAgRFhGT1VUIGtob25nIGNodWEgbm9pIGR1bmcgeHJlZiwgbmVuIG1vaSB4cmVmIGR1b2MgY2hlcCBiYW4gc2FvICsgbm8gQUVDICsgRFhGIHJpZW5nIChnb2kgbGFp"
"IGNoaW5oIHNjcmlwdCBuYXksCiAgICBjaGF5IHNvbmcgc29uZywgdG9pIDIgY2FwIHhyZWYgbG9uZyBuaGF1KSB2YW8gPE91dERpcj5ceHJlZlxOTlwuIEdoaSA8dGVuPl94cmVmLnR4dDogInRlbiB4cmVmfGR1b25nIGRhbnxkeGYiCiAgICBkZSB0aW1fcGhvbmdf"
"dW90LnB5IGRhdCBub2kgZHVuZyB4cmVmIHZhbyBkdW5nIHZpIHRyaSAoY2hpIHRyb25nIGJvIG5obykuIC1UaHVNdWNHb2M6IHRodSBtdWMgYmFuIHZlIGdvYyBkZSB0aW0geHJlZgogICAgZHVvbmcgZGFuIHR1b25nIGRvaSAoa2hpIC1Ed2cgbGEgYmFuIHRhbSku"
"CgouRVhBTVBMRQogICAgcG93ZXJzaGVsbCAtTm9Qcm9maWxlIC1FeGVjdXRpb25Qb2xpY3kgQnlwYXNzIC1GaWxlIGR3Z190b19keGZfYWVjLnBzMSAtRHdnICJEOlwuLi5cTUIgdGFuZyA0LmR3ZyIgLU91dERpciAiRDpcQUlcX3RtcFxjaG9uZ3RoYW0iCiM+CnBh"
"cmFtKAogICAgW1BhcmFtZXRlcihNYW5kYXRvcnkgPSAkdHJ1ZSldW3N0cmluZ10kRHdnLAogICAgW1BhcmFtZXRlcihNYW5kYXRvcnkgPSAkdHJ1ZSldW3N0cmluZ10kT3V0RGlyLAogICAgIyBUSFUgVFUgTk86IGN1YSAvIGN1YSBzbyAvIG8gbW8gdHJ1b2MsIHR1"
"b25nIHNhdSBjdW5nLiBObyB0dW9uZyB0cnVvYyB0aGkgY3VhIGdhbiB0cm9uZyB0dW9uZyBiaSB4b2EgdGhlbwogICAgIyAoQ1QyIENILjAyOiAxMCBjdWEgbWF0IGhldCAtPiBuZXQgdmVuIGNoYXkgcXVhIGN1YSwgbmd1b2kgZHVuZyBiYW8gbG9pIDIzLzEwLzIw"
"MjYpCiAgICAjIENVQSBBRUMgTkFNIFNBSSBMQVlFUjogY3VhIC8gY3VhIHNvIEFFQyB0cmVuIGxheWVyIGtob25nIHBoYWkgbGF5ZXIgY3VhICh2ZC4gIjAiKSAtPiBjaHV5ZW4gc2FuZyBBLURvb3IgLyBBLVdpbmRvdwogICAgIyBUUkVOIEJBTiBTQU8gdHJ1b2Mg"
"a2hpIG5vLCB2aSB0aW1fcGhvbmdfdW90LnB5IG5oYW4gY3VhIHRoZW8gbGF5ZXIgY3VhIGN1YSBJTlNFUlQgc2F1IGtoaSBuby4gVGFuZyA0IFRoYXAgQiBjYW4gQ0gyNToKICAgICMgMiBjdWEgdHJ1b3QgcmEgbG8gZ2lhIHRyZW4gbGF5ZXIgIjAiIC0+IG5ldCB2"
"ZW4gY2hheSBraW4gcXVhIGN1YSAobmd1b2kgZHVuZyBiYW8gbG9pIDI5LzEwLzIwMjYpLiBMYXllciBraG9hOiBibyBxdWEuCiAgICBbc3RyaW5nXSRMb2FpID0gJ0FFQ19ET09SLEFFQ19XSU5ET1csQUVDX09QRU5JTkcsQUVDXypBU1NFTUJMWSxBRUNfQ1VSVEFJ"
"TiosQUVDX1dBTEwnLAogICAgW2ludF0kVGltZW91dFNlYyA9IDM2MDAsCiAgICBbc3RyaW5nXSRUaHVNdWNHb2MgPSAnJywKICAgIFtpbnRdJENhcFhyZWYgPSAwCikKJEVycm9yQWN0aW9uUHJlZmVyZW5jZSA9ICdTdG9wJwoKLiAoSm9pbi1QYXRoICRQU1Njcmlw"
"dFJvb3QgJ21vaV90cnVvbmcucHMxJykKJGFjYyA9ICYgKEpvaW4tUGF0aCAkUFNTY3JpcHRSb290ICd0aW1fYWNjb3JlY29uc29sZS5wczEnKQppZiAoLW5vdCAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAkRHdnKSkgeyB0aHJvdyAiS2hvbmcgdGhheSBmaWxlOiAk"
"RHdnIiB9Ck5ldy1JdGVtIC1JdGVtVHlwZSBEaXJlY3RvcnkgLUZvcmNlIC1QYXRoICRPdXREaXIgfCBPdXQtTnVsbAokYmFzZSA9IFtJTy5QYXRoXTo6R2V0RmlsZU5hbWVXaXRob3V0RXh0ZW5zaW9uKCREd2cpCiRkZXN0ID0gSm9pbi1QYXRoICRPdXREaXIgKCRi"
"YXNlICsgJy5keGYnKQojIGtob25nIGdoaSBkZSBmaWxlIGRhIGNvIChxdXkgdGFjIDIpCmlmIChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRkZXN0KSB7IHRocm93ICJEYSB0b24gdGFpLCBraG9uZyBnaGkgZGU6ICRkZXN0IChjaHV5ZW4gYmFuIGN1IHZhbyBfYmFj"
"a3VwIHRydW9jKSIgfQoKIyB0aHUgbXVjIHRhbSAocXV5IHRhYyA3KSwga2hvbmcgeG9hIHNhdSBraGkgY2hheSAocXV5IHRhYyAxKTsgZHVvbmcgZGFuIEFTQ0lJIGRlIGR1YSB2YW8gLnNjcgokd29yayA9IE5ldy1UaHVNdWNMYW0gJ2Nob25ndGhhbV9hZWNfJwpD"
"b3B5LUl0ZW0gLUxpdGVyYWxQYXRoICREd2cgLURlc3RpbmF0aW9uIChKb2luLVBhdGggJHdvcmsgJ3NyYy5kd2cnKQokZncgPSAkd29yay5SZXBsYWNlKCdcJywgJy8nKQokZHNMb2FpID0gKCRMb2FpIC1zcGxpdCAnLCcgfCBGb3JFYWNoLU9iamVjdCB7ICciJyAr"
"ICRfLlRyaW0oKSArICciJyB9KSAtam9pbiAnICcKJGxpc3AgPSBAIgooZGVmdW4gYWVjLXR5cGVzICggLyBzcyBpIGQgbHN0IGMpCiAgKHNldHEgc3MgKHNzZ2V0ICJYIiAnKCgwIC4gIkFFQ18qIikpKSBsc3QgbmlsIGkgMCkKICAoaWYgc3MgKHJlcGVhdCAoc3Ns"
"ZW5ndGggc3MpIChzZXRxIGQgKGNkciAoYXNzb2MgMCAoZW50Z2V0IChzc25hbWUgc3MgaSkpKSkpIChpZiAoc2V0cSBjIChhc3NvYyBkIGxzdCkpIChzZXRxIGxzdCAoc3Vic3QgKGNvbnMgZCAoMSsgKGNkciBjKSkpIGMgbHN0KSkgKHNldHEgbHN0IChjb25zIChj"
"b25zIGQgMSkgbHN0KSkpIChzZXRxIGkgKDErIGkpKSkpCiAgbHN0KQooZGVmdW4gd3JpdGUtdHlwZXMgKGZuIHRhZyBsc3QgLyBmKSAoc2V0cSBmIChvcGVuIGZuICJhIikpIChmb3JlYWNoIGMgbHN0ICh3cml0ZS1saW5lIChzdHJjYXQgdGFnICIgIiAoY2FyIGMp"
"ICIgIiAoaXRvYSAoY2RyIGMpKSkgZikpIChjbG9zZSBmKSkKKGRlZnVuIHhwbCAoZSkgKGNvbW1hbmQgIl8uRVhQTE9ERSIgZSkgKHdoaWxlICg9IDEgKGxvZ2FuZCAxIChnZXR2YXIgIkNNREFDVElWRSIpKSkgKGNvbW1hbmQgIiIpKSkKKHNldHEgbnRhZyAwKQoo"
"ZGVmdW4gdGFnLWN1YSAoZSBrIC8gZCBsIGxheSBiKQogIChzZXRxIGQgKGVudGdldCBlKSBsIChzdHJjYXNlIChjZHIgKGFzc29jIDggZCkpKSBiICh0YmxzZWFyY2ggIkxBWUVSIiAoY2RyIChhc3NvYyA4IGQpKSkpCiAgKHNldHEgbGF5IChjb25kICgoPSBrICJB"
"RUNfRE9PUiIpICJBLURvb3IiKSAoKD0gayAiQUVDX1dJTkRPVyIpICJBLVdpbmRvdyIpKSkKICAoaWYgKGFuZCBsYXkgYiAoLz0gNCAobG9nYW5kIDQgKGNkciAoYXNzb2MgNzAgYikpKSkgKG5vdCAod2NtYXRjaCBsICJBLURPT1IsQS1XSU5ET1csQS1HTEFaLEEt"
"Q1VBLEEtT1BFTklORyxBLVdJTkRPVy1HIikpKQogICAgKHByb2duIChpZiAobm90ICh0YmxzZWFyY2ggIkxBWUVSIiBsYXkpKSAoY29tbWFuZCAiXy4tTEFZRVIiICJfTiIgbGF5ICIiKSkKICAgICAgKGNvbW1hbmQgIl8uQ0hQUk9QIiBlICIiICJfTEEiIGxheSAi"
"IikgKHNldHEgbnRhZyAoMSsgbnRhZykpKSkpCihkZWZ1biBleHBsLWFsbCAoIC8gc3MgaSBuIGUpIChzZXRxIG4gMCkKICAoZm9yZWFjaCBrICcoJGRzTG9haSkgKHNldHEgc3MgKHNzZ2V0ICJYIiAobGlzdCAoY29ucyAwIGspKSkgaSAwKQogICAgKGlmIHNzIChy"
"ZXBlYXQgKHNzbGVuZ3RoIHNzKSAoc2V0cSBlIChzc25hbWUgc3MgaSkpIChpZiAoZW50Z2V0IGUpIChwcm9nbiAodGFnLWN1YSBlIGspICh4cGwgZSkgKHNldHEgbiAoMSsgbikpKSkgKHNldHEgaSAoMSsgaSkpKSkpCiAgbikKKGRlZnVuIGJsay1hZWMgKG5tIGRl"
"cCAvIGUgZCByIGIpIChzZXRxIGIgKHRibHNlYXJjaCAiQkxPQ0siIG5tKSkgKGlmIChhbmQgYiAoLz0gNCAobG9nYW5kIDQgKGNkciAoYXNzb2MgNzAgYikpKSkpIChzZXRxIGUgKHRibG9iam5hbWUgIkJMT0NLIiBubSkpKQogIChpZiBlIChzZXRxIGUgKGVudG5l"
"eHQgZSkpKQogICh3aGlsZSAoYW5kIGUgKG5vdCByKSkgKHNldHEgZCAoZW50Z2V0IGUpKQogICAgKGNvbmQgKCh3Y21hdGNoIChjZHIgKGFzc29jIDAgZCkpICJBRUNfKiIpIChzZXRxIHIgVCkpCiAgICAgICAgICAoKGFuZCAoPSAoY2RyIChhc3NvYyAwIGQpKSAi"
"SU5TRVJUIikgKDwgZGVwIDMpKSAoc2V0cSByIChibGstYWVjIChjZHIgKGFzc29jIDIgZCkpICgxKyBkZXApKSkpKQogICAgKHNldHEgZSAoZW50bmV4dCBlKSkpCiAgcikKKGRlZnVuIGV4cGwtYmxrLWFlYyAoIC8gc3MgaSBlIG4pIChzZXRxIHNzIChzc2dldCAi"
"WCIgJygoMCAuICJJTlNFUlQiKSAoNDEwIC4gIk1vZGVsIikpKSBpIDAgbiAwKQogIChpZiBzcyAocmVwZWF0IChzc2xlbmd0aCBzcykgKHNldHEgZSAoc3NuYW1lIHNzIGkpKSAoaWYgKGFuZCAoZW50Z2V0IGUpIChibGstYWVjIChjZHIgKGFzc29jIDIgKGVudGdl"
"dCBlKSkpIDApKSAocHJvZ24gKHhwbCBlKSAoc2V0cSBuICgxKyBuKSkpKSAoc2V0cSBpICgxKyBpKSkpKQogIG4pCihkZWZ1biBsb2ctbiAoZm4gdGFnIG4gLyBmKSAoc2V0cSBmIChvcGVuIGZuICJhIikpICh3cml0ZS1saW5lIChzdHJjYXQgdGFnICIgIiAoaXRv"
"YSBuKSkgZikgKGNsb3NlIGYpKQooZGVmdW4geHJlZi1saXN0ICggLyBzcyBpIG4gYiBsc3QgZikgKHNldHEgZiAob3BlbiAiJGZ3L3hyZWYudHh0IiAidyIgInV0ZjgiKSBzcyAoc3NnZXQgIlgiICcoKDAgLiAiSU5TRVJUIikgKDQxMCAuICJNb2RlbCIpKSkgaSAw"
"KSAoaWYgc3MgKHJlcGVhdCAoc3NsZW5ndGggc3MpIChzZXRxIG4gKGNkciAoYXNzb2MgMiAoZW50Z2V0IChzc25hbWUgc3MgaSkpKSkgYiAodGJsc2VhcmNoICJCTE9DSyIgbikpIChpZiAoYW5kIGIgKD0gNCAobG9nYW5kIDQgKGNkciAoYXNzb2MgNzAgYikpKSkg"
"KG5vdCAobWVtYmVyIG4gbHN0KSkpIChwcm9nbiAoc2V0cSBsc3QgKGNvbnMgbiBsc3QpKSAod3JpdGUtbGluZSAoc3RyY2F0IG4gInwiIChpdG9hIChjZHIgKGFzc29jIDcwIGIpKSkgInwiIChjZHIgKGFzc29jIDEgYikpKSBmKSkpIChzZXRxIGkgKDErIGkpKSkp"
"IChjbG9zZSBmKSkKKHhyZWYtbGlzdCkKKHNldHZhciAiQ01ERUNITyIgMCkKKGlmICg9IDAgKGdldHZhciAiV09STERVQ1MiKSkgKGNvbW1hbmQgIl8uVUNTIiAiX1ciKSkKKGxvZy1uICIkZncvYWVjLnR4dCIgIkJMT0NLX0NPX0FFQ19EQV9OTyIgKCsgKGV4cGwt"
"YmxrLWFlYykgKGV4cGwtYmxrLWFlYykgKGV4cGwtYmxrLWFlYykpKQood3JpdGUtdHlwZXMgIiRmdy9hZWMudHh0IiAiVFJVT0MiIChhZWMtdHlwZXMpKQooc2V0cSBubiAodmwtY2F0Y2gtYWxsLWFwcGx5ICdleHBsLWFsbCkpCih3cml0ZS10eXBlcyAiJGZ3L2Fl"
"Yy50eHQiICJTQVUiIChhZWMtdHlwZXMpKQoobG9nLW4gIiRmdy9hZWMudHh0IiAiQ1VBX0FFQ19ET0lfTEFZRVJfQ1VBIiBudGFnKQoiQAokbGluZXMgPSAkbGlzcCAtc3BsaXQgImByP2BuIiB8IFdoZXJlLU9iamVjdCB7ICRfLlRyaW0oKSAtbmUgJycgfQokc2Ny"
"ID0gKCRsaW5lcyAtam9pbiAiYHJgbiIpICsgImByYG5GSUxFRElBYHJgbjBgcmBuXy5EWEZPVVRgcmBuJGZ3L291dC5keGZgcmBuVmByYG4yMDE4YHJgbjE2YHJgbl8uUVVJVGByYG5fWWByYG4iClNldC1Db250ZW50IC1QYXRoIChKb2luLVBhdGggJHdvcmsgJ3J1"
"bi5zY3InKSAtVmFsdWUgJHNjciAtRW5jb2RpbmcgQVNDSUkKJHAgPSBTdGFydC1Qcm9jZXNzIC1GaWxlUGF0aCAkYWNjLkV4ZSAtV29ya2luZ0RpcmVjdG9yeSAkd29yayAtV2luZG93U3R5bGUgSGlkZGVuIC1QYXNzVGhydSBgCiAgICAtUmVkaXJlY3RTdGFuZGFy"
"ZE91dHB1dCAoSm9pbi1QYXRoICR3b3JrICdjb25zb2xlLnR4dCcpIGAKICAgIC1Bcmd1bWVudExpc3QgIi9pIGAiJHdvcmtcc3JjLmR3Z2AiIC9zIGAiJHdvcmtccnVuLnNjcmAiICQoJGFjYy5Qcm9kdWN0KSAvbCBlbi1VUyIKaWYgKC1ub3QgJHAuV2FpdEZvckV4"
"aXQoJFRpbWVvdXRTZWMgKiAxMDAwKSkgeyAkcC5LaWxsKCk7IHRocm93ICJRdWEgJFRpbWVvdXRTZWMgZ2lheSwgZGEgZHVuZyBDb3JlIENvbnNvbGUuIFRodSBtdWMgdGFtOiAkd29yayIgfQokb3V0ID0gSm9pbi1QYXRoICR3b3JrICdvdXQuZHhmJwppZiAoLW5v"
"dCAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAkb3V0KSkgeyB0aHJvdyAiS2hvbmcgdGFvIGR1b2MgRFhGLiBYZW0gJHdvcmtcY29uc29sZS50eHQiIH0KTW92ZS1JdGVtIC1MaXRlcmFsUGF0aCAkb3V0IC1EZXN0aW5hdGlvbiAkZGVzdAokcmVwID0gSm9pbi1QYXRo"
"ICR3b3JrICdhZWMudHh0JwppZiAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAkcmVwKSB7IENvcHktSXRlbSAtTGl0ZXJhbFBhdGggJHJlcCAtRGVzdGluYXRpb24gKEpvaW4tUGF0aCAkT3V0RGlyICgkYmFzZSArICdfYWVjLnR4dCcpKTsgR2V0LUNvbnRlbnQgLUxp"
"dGVyYWxQYXRoICRyZXAgfQoKIyBYcmVmIG5nb2FpOiBraG9uZyBiaW5kLiBNb2kgeHJlZiAtPiBiYW4gc2FvICsgbm8gQUVDICsgRFhGIHJpZW5nIChjaGF5IHNvbmcgc29uZywgdG9pIGRhIDYgdGllbiB0cmluaCkKJHhyZWZUeHQgPSBKb2luLVBhdGggJHdvcmsg"
"J3hyZWYudHh0JwokYmFuZyA9IEAoKQppZiAoKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJHhyZWZUeHQpIC1hbmQgJENhcFhyZWYgLWx0IDIpIHsKICAgICRnb2MgPSBpZiAoJFRodU11Y0dvYykgeyAkVGh1TXVjR29jLlRyaW1FbmQoJ1wnKSB9IGVsc2UgeyAoU3Bs"
"aXQtUGF0aCAtUGFyZW50ICREd2cpLlRyaW1FbmQoJ1wnKSB9CiAgICAjIHhyZWYgY2hpIGNodWEgY2h1IHRoaWNoIC8ga2h1bmcgdGVuIC8gbHVvaSB0cnVjIC8gY2hpIGdpb2k6IGtob25nIGNvIHJhbmggcGhvbmcsIGJvIHF1YSBjaG8gbmhhbmgKICAgICRib1F1"
"YSA9ICcoP2kpa2h1bmd8Z2hpID9jaHxub3RlfGxlZ2VuZHxjaHUgZ2lhaXxsdW9pfGNoaSA/Z2lvaXxjYWxsb3V0JwogICAgJGNoYXkgPSBAKCk7ICRpID0gMAogICAgZm9yZWFjaCAoJGRvbmcgaW4gR2V0LUNvbnRlbnQgLUxpdGVyYWxQYXRoICR4cmVmVHh0IC1F"
"bmNvZGluZyBVVEY4KSB7CiAgICAgICAgIyBkb25nOiB0ZW58Y28gNzB8ZHVvbmcgZGFuLiBYcmVmIGxvbmcgZGFuZyBPdmVybGF5IChjbyA4KSBraG9uZyBoaWVuIG8gYmFuIHZlIGNodSAtPiBibwogICAgICAgICRwID0gJGRvbmcgLXNwbGl0ICdcfCcsIDMKICAg"
"ICAgICBpZiAoJHAuQ291bnQgLWx0IDMgLW9yICRwWzBdIC1tYXRjaCAkYm9RdWEpIHsgY29udGludWUgfQogICAgICAgIGlmICgkQ2FwWHJlZiAtZ2UgMSAtYW5kIChbaW50XSRwWzFdIC1iYW5kIDgpKSB7IGNvbnRpbnVlIH0KICAgICAgICAkdGVuID0gJHBbMF07"
"ICRkdW9uZyA9ICRwWzJdCiAgICAgICAgJHRpbSA9ICRudWxsCiAgICAgICAgZm9yZWFjaCAoJGMgaW4gQCgkZHVvbmcsICIkZ29jXCRkdW9uZyIsICIkZ29jXCQoW0lPLlBhdGhdOjpHZXRGaWxlTmFtZSgkZHVvbmcpKSIpKSB7CiAgICAgICAgICAgIHRyeSB7IGlm"
"IChbSU8uUGF0aF06OklzUGF0aFJvb3RlZCgkYykgLWFuZCAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAkYyAtUGF0aFR5cGUgTGVhZikpIHsgJHRpbSA9ICRjOyBicmVhayB9IH0gY2F0Y2gge30KICAgICAgICB9CiAgICAgICAgaWYgKC1ub3QgJHRpbSkgeyAkYmFu"
"ZyArPSAiJHRlbnwkZHVvbmd8IjsgV3JpdGUtT3V0cHV0ICJYUkVGIEtIT05HIFRJTSBUSEFZOiAkdGVuICgkZHVvbmcpIjsgY29udGludWUgfQogICAgICAgICRpKysKICAgICAgICAkb2QgPSBKb2luLVBhdGggJE91dERpciAoJ3hyZWZcJyArICRpLlRvU3RyaW5n"
"KCcwMCcpKQogICAgICAgICRiYW5nICs9ICIkdGVufCR0aW18IiArIChKb2luLVBhdGggJG9kIChbSU8uUGF0aF06OkdldEZpbGVOYW1lV2l0aG91dEV4dGVuc2lvbigkdGltKSArICcuZHhmJykpCiAgICAgICAgd2hpbGUgKEAoJGNoYXkgfCBXaGVyZS1PYmplY3Qg"
"eyAtbm90ICRfLkhhc0V4aXRlZCB9KS5Db3VudCAtZ2UgNikgeyBTdGFydC1TbGVlcCAtTWlsbGlzZWNvbmRzIDUwMCB9CiAgICAgICAgJGNoYXkgKz0gU3RhcnQtUHJvY2VzcyAtRmlsZVBhdGggJ3Bvd2Vyc2hlbGwuZXhlJyAtV2luZG93U3R5bGUgSGlkZGVuIC1Q"
"YXNzVGhydSAtQXJndW1lbnRMaXN0ICgKICAgICAgICAgICAgIi1Ob1Byb2ZpbGUgLUV4ZWN1dGlvblBvbGljeSBCeXBhc3MgLUZpbGUgYCIkUFNDb21tYW5kUGF0aGAiIC1Ed2cgYCIkdGltYCIgLU91dERpciBgIiRvZGAiICIgKwogICAgICAgICAgICAiLUNhcFhy"
"ZWYgJCgkQ2FwWHJlZiArIDEpIC1UaHVNdWNHb2MgYCIkKChTcGxpdC1QYXRoIC1QYXJlbnQgJHRpbSkuVHJpbUVuZCgnXCcpKWAiIC1UaW1lb3V0U2VjICRUaW1lb3V0U2VjIikKICAgIH0KICAgIGZvcmVhY2ggKCRjIGluICRjaGF5KSB7IGlmICgtbm90ICRjLldh"
"aXRGb3JFeGl0KCRUaW1lb3V0U2VjICogMTAwMCkpIHsgJGMuS2lsbCgpIH0gfQp9CiMgVVRGLTgga2hvbmcgQk9NOiBsZW5oIExJU1AgQ0hPTkdUSEFNIGRvYyBmaWxlIG5heSBkZSBiYW8geHJlZiBraG9uZyB0aW0gdGhheQpbSU8uRmlsZV06OldyaXRlQWxsTGlu"
"ZXMoKEpvaW4tUGF0aCAkT3V0RGlyICgkYmFzZSArICdfeHJlZi50eHQnKSksIFtzdHJpbmdbXV0kYmFuZywgKE5ldy1PYmplY3QgVGV4dC5VVEY4RW5jb2RpbmcgJGZhbHNlKSkKaWYgKCRiYW5nLkNvdW50KSB7IFdyaXRlLU91dHB1dCAiWFJFRjogJCgkYmFuZy5D"
"b3VudCkgZmlsZSAoZG9jIHJpZW5nLCBraG9uZyBiaW5kKSIgfQpXcml0ZS1PdXRwdXQgJGRlc3QKV3JpdGUtT3V0cHV0ICJUaHUgbXVjIHRhbSBnaXUgbGFpOiAkd29yayIK"
)
("chong-tham-mat-bang/scripts/tim_accoreconsole.ps1"
"PCMKLlNZTk9QU0lTCiAgICBUaW0gQXV0b0NBRCBDb3JlIENvbnNvbGUgKGFjY29yZWNvbnNvbGUuZXhlKSB0cmVuIG1heSwgdHJhIHZlIGRvaSB0dW9uZyB7IEV4ZTsgUHJvZHVjdCB9LgoKLkRFU0NSSVBUSU9OCiAgICBEdW5nIEZpbmQtQXV0b0NBRCB0cm9uZyBt"
"b2lfdHJ1b25nLnBzMSAoY2hheSBkdW9jIHRyZW4gbWF5IGJhdCBreSk6IGJpZW4gQVJDSElWSU5BX0FDQUQsIHJlZ2lzdHJ5IEF1dG9kZXNrLAogICAgcm9pIDxvIGRpYT5cUHJvZ3JhbSBGaWxlc1xBdXRvZGVza1xBdXRvQ0FEICosIDxvIGRpYT5cYXV0b2NhZFxB"
"dXRvQ0FEICogKHZkLiBtYXkgY2FpIEFDQSAyMDIxIG8gRDpcYXV0b2NhZCkuCiAgICBVdSB0aWVuIGJhbiBjbyBBdXRvQ0FEIEFyY2hpdGVjdHVyZSwgcm9pIGJhbiBtb2kgbmhhdC4KICAgIFByb2R1Y3QgPSAnL3Byb2R1Y3QgQUNBJyBuZXUgdGh1IG11YyBjbyBB"
"dXRvQ0FEIEFyY2hpdGVjdHVyZSAodGh1IG11YyBjb24gJ0FDQScgaG9hYyBBZWNCYXNlKi5kYngpIC0+IGNoYXkga2VtCiAgICAiL3Byb2R1Y3QgQUNBIiBkZSBDb3JlIENvbnNvbGUgbmFwIG9iamVjdCBlbmFibGVyIEFFQyAodHVvbmcsIGN1YSBBQ0EpLCBraG9u"
"ZyB0aGkgZGUgdHJvbmcuCgouRVhBTVBMRQogICAgJGFjYyA9ICYgIiRQU1NjcmlwdFJvb3RcdGltX2FjY29yZWNvbnNvbGUucHMxIjsgJiAkYWNjLkV4ZSAvaSBhLmR3ZyAvcyBiLnNjciAkYWNjLlByb2R1Y3QKIz4KJEVycm9yQWN0aW9uUHJlZmVyZW5jZSA9ICdT"
"dG9wJwouIChKb2luLVBhdGggJFBTU2NyaXB0Um9vdCAnbW9pX3RydW9uZy5wczEnKQpGaW5kLUF1dG9DQUQgLUV4ZSAnYWNjb3JlY29uc29sZS5leGUnIC1VdVRpZW5BQ0EK"
)
("chong-tham-mat-bang/scripts/moi_truong.ps1"
"PCMKLlNZTk9QU0lTCiAgICBUaW0gbW9pIHRydW9uZyB0cmVuIE1BWSBCQVQgS1kgKGtob25nIGdhbiBjdW5nIEQ6XEFJLCBDOlxQcm9ncmFtIEZpbGVzLi4uKTogdGh1IG11YyBnb2MsIHRodSBtdWMgdGFtLAogICAgQXV0b0NBRCAvIENvcmUgQ29uc29sZSwgUHl0"
"aG9uIGNvIGdvaSBjYW4gZHVuZy4gRHVuZyBjaHVuZyBjaG8gY2FjIHNraWxsIEFSQ0hJVklOQSAoYmFuIHNhbyBnaW9uZyBuaGF1IG8KICAgIGNob25nLXRoYW0tbWF0LWJhbmcsIG5nYW4tY2hheS10cnVjLWhrdCwgdHJ1Yy1sby1tby1tZXAgLSBzdWEgMSBmaWxl"
"IHRoaSBjaGVwIHNhbmcgMiBmaWxlIGtpYSkuCgouREVTQ1JJUFRJT04KICAgIERvdC1zb3VyY2U6ICAuIChKb2luLVBhdGggJFBTU2NyaXB0Um9vdCAnbW9pX3RydW9uZy5wczEnKQogICAgVGh1IHR1IHRpbSAoYmllbiBtb2kgdHJ1b25nIGRhdCBkdW9jIHRyZW4g"
"dHVuZyBtYXkgZGUgZXAgZHVvbmcgZGFuKToKICAgICAgR29jIEFJICAgOiAkZW52OkFSQ0hJVklOQV9BSSAtPiB0aHUgbXVjIGNoYSBjdWEgIi5jbGF1ZGUiIGNodWEgc2tpbGwgLT4gdGh1IG11YyBjaGEgY28gQ0xBVURFLm1kLgogICAgICAgICAgICAgICAgIE1h"
"eSBEOlxBSTogZ29jID0gRDpcQUkgKHRhbSBEOlxBSVxfdG1wLCBzYW8gbHV1IEQ6XEFJXF9iYWNrdXAgbmh1IENMQVVERS5tZCkuCiAgICAgICAgICAgICAgICAgS2hvbmcgY28gZ29jIChza2lsbCBkYXQgbyAlVVNFUlBST0ZJTEUlXC5jbGF1ZGUpOiB0YW0gLyBz"
"YW8gbHV1IG8gJUxPQ0FMQVBQREFUQSVcQVJDSElWSU5BLgogICAgICBBdXRvQ0FEICA6ICRlbnY6QVJDSElWSU5BX0FDQUQgKHRodSBtdWMgY2FpKSAtPiByZWdpc3RyeSBIS0xNXFNPRlRXQVJFXEF1dG9kZXNrXEF1dG9DQUQgKEFjYWRMb2NhdGlvbikKICAgICAg"
"ICAgICAgICAgICAtPiA8byBkaWE+XFByb2dyYW0gRmlsZXNcQXV0b2Rlc2tcQXV0b0NBRCAqLCA8byBkaWE+XGF1dG9jYWRcQXV0b0NBRCAqLCA8byBkaWE+XEF1dG9kZXNrXEF1dG9DQUQgKi4KICAgICAgUHl0aG9uICAgOiAtUHl0aG9uIC0+ICRlbnY6QVJDSElW"
"SU5BX1BZVEhPTiAtPiBnb2kgbWFuZyB0aGVvIDxnb2MgfCBvIGN1bmc6XEFJPlxfdG9vbHNcQ0hPTkdUSEFNX3B5dGhvbgogICAgICAgICAgICAgICAgIC0+IDxnb2M+XF90b29sc1x2ZW52IC0+ICVMT0NBTEFQUERBVEElXEFSQ0hJVklOQVx2ZW52CiAgICAgICAg"
"ICAgICAgICAgLT4gcHkgLTMgLT4gcHl0aG9uIHRyb25nIFBBVEguIENoaSBuaGFuIGJhbiBpbXBvcnQgZHVvYyBjYWMgZ29pIGNhbiBkdW5nLgogICAgICAgICAgICAgICAgIENodWEgY286IGNoYXkgMSBsYW4gY2FpX2RhdF9weXRob24ucHMxIChjdW5nIHRodSBt"
"dWMpLgojPgoKZnVuY3Rpb24gR2V0LUdvY0FJIHsKICAgIGlmICgkZW52OkFSQ0hJVklOQV9BSSAtYW5kIChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRlbnY6QVJDSElWSU5BX0FJIC1QYXRoVHlwZSBDb250YWluZXIpKSB7CiAgICAgICAgcmV0dXJuIChSZXNvbHZl"
"LVBhdGggLUxpdGVyYWxQYXRoICRlbnY6QVJDSElWSU5BX0FJKS5QYXRoLlRyaW1FbmQoJ1wnKQogICAgfQogICAgJG5oYSA9IGlmICgkZW52OlVTRVJQUk9GSUxFKSB7ICRlbnY6VVNFUlBST0ZJTEUuVHJpbUVuZCgnXCcpIH0gZWxzZSB7ICcnIH0KICAgICRkID0g"
"JFBTU2NyaXB0Um9vdAogICAgd2hpbGUgKCRkKSB7CiAgICAgICAgJGRkID0gJGQuVHJpbUVuZCgnXCcpCiAgICAgICAgaWYgKChTcGxpdC1QYXRoIC1MZWFmICRkKSAtZXEgJy5jbGF1ZGUnKSB7CiAgICAgICAgICAgICRnID0gU3BsaXQtUGF0aCAtUGFyZW50ICRk"
"CiAgICAgICAgICAgICMgLmNsYXVkZSBjdWEgdGFpIGtob2FuICglVVNFUlBST0ZJTEUlXC5jbGF1ZGUpOiBraG9uZyBsYXkgdGh1IG11YyBuZ3VvaSBkdW5nIGxhbSBnb2MKICAgICAgICAgICAgaWYgKCRnIC1hbmQgJGcuVHJpbUVuZCgnXCcpIC1uZSAkbmhhKSB7"
"IHJldHVybiAkZy5UcmltRW5kKCdcJykgfQogICAgICAgICAgICByZXR1cm4gJG51bGwKICAgICAgICB9CiAgICAgICAgIyB0aHUgbXVjIGNvIENMQVVERS5tZCBob2FjIC5jbGF1ZGVcc2tpbGxzICh2ZC4gRDpcQUkpLiBTY3JpcHQgZ2lhaSBuZW4gdHUgQ0hPTkdU"
"SEFNLmxzcCBuYW0gbwogICAgICAgICMgPGdvYz5cX3Rvb2xzXGNob25ndGhhbV88YmFuPlwuLi4gbmVuIGN1bmcgdGltIHJhIDxnb2M+LiBCbyBxdWEgdGh1IG11YyBuZ3VvaSBkdW5nLgogICAgICAgIGlmICgkZGQgLW5lICRuaGEgLWFuZCAoKFRlc3QtUGF0aCAt"
"TGl0ZXJhbFBhdGggKEpvaW4tUGF0aCAkZCAnQ0xBVURFLm1kJykpIC1vcgogICAgICAgICAgICAgICAgKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggKEpvaW4tUGF0aCAkZCAnLmNsYXVkZVxza2lsbHMnKSkpKSB7IHJldHVybiAkZGQgfQogICAgICAgICRkID0gU3Bs"
"aXQtUGF0aCAtUGFyZW50ICRkCiAgICB9CiAgICByZXR1cm4gJG51bGwKfQoKZnVuY3Rpb24gR2V0LVRodU11Y0Nvbihbc3RyaW5nXSRUZW4pIHsKICAgICRnID0gR2V0LUdvY0FJCiAgICAkdCA9IGlmICgkZykgeyBKb2luLVBhdGggJGcgJFRlbiB9IGVsc2UgeyBK"
"b2luLVBhdGggJGVudjpMT0NBTEFQUERBVEEgKCdBUkNISVZJTkFcJyArICRUZW4pIH0KICAgIE5ldy1JdGVtIC1JdGVtVHlwZSBEaXJlY3RvcnkgLUZvcmNlIC1QYXRoICR0IHwgT3V0LU51bGwKICAgICR0Cn0KCiMgVGh1IG11YyB0YW0gKGtob25nIHhvYSBzYXUg"
"a2hpIGNoYXkgLSBxdXkgdGFjIDEpCmZ1bmN0aW9uIEdldC1UaHVNdWNUYW0geyBHZXQtVGh1TXVjQ29uICdfdG1wJyB9CiMgVGh1IG11YyBzYW8gbHV1IGJhbiBjdSB0cnVvYyBraGkgc3VhIChxdXkgdGFjIDIpCmZ1bmN0aW9uIEdldC1UaHVNdWNCYWNrdXAgeyBH"
"ZXQtVGh1TXVjQ29uICdfYmFja3VwJyB9CgojIFRodSBtdWMgbGFtIHZpZWMgbW9pIGNobyBDb3JlIENvbnNvbGUuIER1b25nIGRhbiBuYW0gdHJvbmcgZmlsZSAuc2NyOyBDb3JlIENvbnNvbGUgZG9jIC5zY3IgdGhlbyBtYSBBTlNJCiMgbmVuIGR1b25nIGRhbiBj"
"byBkYXUgdGllbmcgVmlldCAodmQuIHRlbiBuZ3VvaSBkdW5nIGNvIGRhdSkgc2UgaG9uZyAtPiBjaHV5ZW4gc2FuZyBDOlxVc2Vyc1xQdWJsaWNcQVJDSElWSU5BX3RtcC4KZnVuY3Rpb24gTmV3LVRodU11Y0xhbShbc3RyaW5nXSRUaWVuKSB7CiAgICAkdG1wID0g"
"R2V0LVRodU11Y1RhbQogICAgaWYgKCR0bXAgLW1hdGNoICdbXlx4MjAtXHg3RV0nKSB7CiAgICAgICAgJHRtcCA9IEpvaW4tUGF0aCAkZW52OlBVQkxJQyAnQVJDSElWSU5BX3RtcCcKICAgICAgICBOZXctSXRlbSAtSXRlbVR5cGUgRGlyZWN0b3J5IC1Gb3JjZSAt"
"UGF0aCAkdG1wIHwgT3V0LU51bGwKICAgIH0KICAgICR3ID0gSm9pbi1QYXRoICR0bXAgKCRUaWVuICsgW2d1aWRdOjpOZXdHdWlkKCkuVG9TdHJpbmcoJ04nKSkKICAgIE5ldy1JdGVtIC1JdGVtVHlwZSBEaXJlY3RvcnkgLUZvcmNlIC1QYXRoICR3IHwgT3V0LU51"
"bGwKICAgICR3Cn0KCmZ1bmN0aW9uIEdldC1PRGlhQ29EaW5oIHsKICAgIFtJTy5Ecml2ZUluZm9dOjpHZXREcml2ZXMoKSB8IFdoZXJlLU9iamVjdCB7ICRfLkRyaXZlVHlwZSAtZXEgJ0ZpeGVkJyAtYW5kICRfLklzUmVhZHkgfSB8CiAgICAgICAgRm9yRWFjaC1P"
"YmplY3QgeyAkXy5Sb290RGlyZWN0b3J5LkZ1bGxOYW1lLlRyaW1FbmQoJ1wnKSB9Cn0KCjwjCiAgVGltIEF1dG9DQUQuIC1FeGUgYWNjb3JlY29uc29sZS5leGUgKENvcmUgQ29uc29sZSkgaG9hYyBhY2FkLmV4ZSAoQXV0b0NBRCBkYXkgZHUpLgogIC1VdVRpZW5B"
"Q0E6IHV1IHRpZW4gYmFuIGNvIEF1dG9DQUQgQXJjaGl0ZWN0dXJlIChnaXUgdHVvbmcgLyBjdWEgQUNBIGtoaSBubyBBRUMpLgogIFRyYSB2ZSB7IEV4ZTsgRGlyOyBQcm9kdWN0IH0gLSBQcm9kdWN0ID0gJy9wcm9kdWN0IEFDQScgbmV1IHRodSBtdWMgY28gQUNB"
"LCBraG9uZyB0aGkgJycuCiM+CmZ1bmN0aW9uIEZpbmQtQXV0b0NBRChbc3RyaW5nXSRFeGUgPSAnYWNjb3JlY29uc29sZS5leGUnLCBbc3dpdGNoXSRVdVRpZW5BQ0EpIHsKICAgICRkaXJzID0gTmV3LU9iamVjdCBTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5M"
"aXN0W3N0cmluZ10KICAgIGlmICgkZW52OkFSQ0hJVklOQV9BQ0FEKSB7ICRkaXJzLkFkZCgkZW52OkFSQ0hJVklOQV9BQ0FEKSB9CiAgICBmb3JlYWNoICgkciBpbiBAKCdIS0xNOlxTT0ZUV0FSRVxBdXRvZGVza1xBdXRvQ0FEJykpIHsKICAgICAgICBmb3JlYWNo"
"ICgkdmVyIGluIEAoR2V0LUNoaWxkSXRlbSAtTGl0ZXJhbFBhdGggJHIgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUpKSB7CiAgICAgICAgICAgIGZvcmVhY2ggKCRzcCBpbiBAKEdldC1DaGlsZEl0ZW0gLUxpdGVyYWxQYXRoICR2ZXIuUFNQYXRoIC1FcnJv"
"ckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlKSkgewogICAgICAgICAgICAgICAgJGxvYyA9IChHZXQtSXRlbVByb3BlcnR5IC1MaXRlcmFsUGF0aCAkc3AuUFNQYXRoIC1FcnJvckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlKS5BY2FkTG9jYXRpb24KICAgICAgICAgICAg"
"ICAgIGlmICgkbG9jKSB7ICRkaXJzLkFkZCgkbG9jKSB9CiAgICAgICAgICAgIH0KICAgICAgICB9CiAgICB9CiAgICBmb3JlYWNoICgkbyBpbiBAKEdldC1PRGlhQ29EaW5oKSkgewogICAgICAgIGZvcmVhY2ggKCRtIGluIEAoJ1Byb2dyYW0gRmlsZXNcQXV0b2Rl"
"c2tcQXV0b0NBRCAqJywgJ2F1dG9jYWRcQXV0b0NBRCAqJywgJ0F1dG9kZXNrXEF1dG9DQUQgKicpKSB7CiAgICAgICAgICAgIEdldC1DaGlsZEl0ZW0gLVBhdGggKEpvaW4tUGF0aCAkbyAkbSkgLURpcmVjdG9yeSAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51"
"ZSB8IEZvckVhY2gtT2JqZWN0IHsgJGRpcnMuQWRkKCRfLkZ1bGxOYW1lKSB9CiAgICAgICAgfQogICAgfQogICAgJGRzID0gZm9yZWFjaCAoJGQgaW4gKCRkaXJzIHwgRm9yRWFjaC1PYmplY3QgeyAkXy5UcmltRW5kKCdcJykgfSB8IFNvcnQtT2JqZWN0IC1Vbmlx"
"dWUpKSB7CiAgICAgICAgJGYgPSBKb2luLVBhdGggJGQgJEV4ZQogICAgICAgIGlmIChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRmIC1QYXRoVHlwZSBMZWFmKSB7CiAgICAgICAgICAgICRhY2EgPSAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAoSm9pbi1QYXRoICRk"
"ICdBQ0EnKSkgLW9yIFtib29sXShHZXQtQ2hpbGRJdGVtIChKb2luLVBhdGggJGQgJ0FlY0Jhc2UqLmRieCcpIC1FcnJvckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlKQogICAgICAgICAgICAkbmFtID0gaWYgKCRkIC1tYXRjaCAnKDIwXGRcZCknKSB7IFtpbnRdJE1h"
"dGNoZXNbMV0gfSBlbHNlIHsgMCB9CiAgICAgICAgICAgIFtwc2N1c3RvbW9iamVjdF1AeyBFeGUgPSAkZjsgRGlyID0gJGQ7IE5hbSA9ICRuYW07IEFDQSA9ICRhY2E7IFByb2R1Y3QgPSAkKGlmICgkYWNhKSB7ICcvcHJvZHVjdCBBQ0EnIH0gZWxzZSB7ICcnIH0p"
"IH0KICAgICAgICB9CiAgICB9CiAgICBpZiAoLW5vdCAkZHMpIHsKICAgICAgICB0aHJvdyAiS2hvbmcgdGltIHRoYXkgJEV4ZSB0cmVuIG1heS4gQ2FpIEF1dG9DQUQsIGhvYWMgZGF0IGJpZW4gbW9pIHRydW9uZyBBUkNISVZJTkFfQUNBRCA9IHRodSBtdWMgY2Fp"
"IEF1dG9DQUQgKHZkLiBEOlxhdXRvY2FkXEF1dG9DQUQgMjAyMSkuIgogICAgfQogICAgaWYgKCRVdVRpZW5BQ0EpIHsgJGRzID0gJGRzIHwgU29ydC1PYmplY3QgQHsgZSA9IHsgJF8uQUNBIH07IERlc2NlbmRpbmcgPSAkdHJ1ZSB9LCBAeyBlID0geyAkXy5OYW0g"
"fTsgRGVzY2VuZGluZyA9ICR0cnVlIH0gfQogICAgZWxzZSB7ICRkcyA9ICRkcyB8IFNvcnQtT2JqZWN0IEB7IGUgPSB7ICRfLk5hbSB9OyBEZXNjZW5kaW5nID0gJHRydWUgfSB9CiAgICAkZHMgfCBTZWxlY3QtT2JqZWN0IC1GaXJzdCAxCn0KCjwjCiAgVGltIFB5"
"dGhvbiBpbXBvcnQgZHVvYyBjYWMgZ29pIC1Hb2kuIFRyYSB2ZSBkdW9uZyBkYW4gcHl0aG9uLmV4ZTsga2hvbmcgY28gdGhpIGJhbyBsb2kga2VtIGNhY2ggY2FpLgojPgpmdW5jdGlvbiBGaW5kLVB5dGhvbihbc3RyaW5nXSRQeXRob24gPSAnJywgW3N0cmluZ1td"
"XSRHb2kgPSBAKCdlemR4ZicsICdzaGFwZWx5JykpIHsKICAgICRFcnJvckFjdGlvblByZWZlcmVuY2UgPSAnQ29udGludWUnCiAgICAkdW5nID0gTmV3LU9iamVjdCBTeXN0ZW0uQ29sbGVjdGlvbnMuR2VuZXJpYy5MaXN0W3N0cmluZ10KICAgIGlmICgkUHl0aG9u"
"KSB7ICR1bmcuQWRkKCRQeXRob24pIH0KICAgIGlmICgkZW52OkFSQ0hJVklOQV9QWVRIT04pIHsgJHVuZy5BZGQoJGVudjpBUkNISVZJTkFfUFlUSE9OKSB9CiAgICAjIGdvaSBQeXRob24gbWFuZyB0aGVvIChraG9uZyBjYWkpOiB0aHUgbXVjIENIT05HVEhBTV9w"
"eXRob24gY2hlcCB2YW8gPGdvYz5cX3Rvb2xzIGhvYWMgPG8gY3VuZz46XEFJXF90b29scwogICAgJGcgPSBHZXQtR29jQUkKICAgIGlmICgkZykgeyAkdW5nLkFkZCgoSm9pbi1QYXRoICRnICdfdG9vbHNcQ0hPTkdUSEFNX3B5dGhvblxweXRob24uZXhlJykpIH0K"
"ICAgIGZvcmVhY2ggKCRvIGluIEAoR2V0LU9EaWFDb0RpbmgpKSB7ICR1bmcuQWRkKChKb2luLVBhdGggJG8gJ0FJXF90b29sc1xDSE9OR1RIQU1fcHl0aG9uXHB5dGhvbi5leGUnKSkgfQogICAgaWYgKCRnKSB7ICR1bmcuQWRkKChKb2luLVBhdGggJGcgJ190b29s"
"c1x2ZW52XFNjcmlwdHNccHl0aG9uLmV4ZScpKSB9CiAgICBpZiAoJGVudjpMT0NBTEFQUERBVEEpIHsgJHVuZy5BZGQoKEpvaW4tUGF0aCAkZW52OkxPQ0FMQVBQREFUQSAnQVJDSElWSU5BXHZlbnZcU2NyaXB0c1xweXRob24uZXhlJykpIH0KICAgICRweSA9IEdl"
"dC1Db21tYW5kIHB5LmV4ZSAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZQogICAgaWYgKCRweSkgewogICAgICAgIHRyeSB7ICRwID0gJiAkcHkuU291cmNlIC0zIC1jICdpbXBvcnQgc3lzOyBwcmludChzeXMuZXhlY3V0YWJsZSknIDI+JG51bGw7IGlmICgk"
"cCkgeyAkdW5nLkFkZCgoW3N0cmluZ10kcCkuVHJpbSgpKSB9IH0gY2F0Y2gge30KICAgIH0KICAgICMgYm8gInB5dGhvbi5leGUiIGdpYSBjdWEgTWljcm9zb2Z0IFN0b3JlIChXaW5kb3dzQXBwcyk6IGdvIGxhIG1vIFN0b3JlLCBraG9uZyBjaGF5CiAgICBHZXQt"
"Q29tbWFuZCBweXRob24uZXhlIC1BbGwgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29udGludWUgfCBXaGVyZS1PYmplY3QgeyAkXy5Tb3VyY2UgLW5vdG1hdGNoICdXaW5kb3dzQXBwcycgfSB8CiAgICAgICAgRm9yRWFjaC1PYmplY3QgeyAkdW5nLkFkZCgkXy5Tb3Vy"
"Y2UpIH0KICAgICRraWVtID0gJ2ltcG9ydCAnICsgKCRHb2kgLWpvaW4gJywgJykKICAgIGZvcmVhY2ggKCRjIGluICgkdW5nIHwgU2VsZWN0LU9iamVjdCAtVW5pcXVlKSkgewogICAgICAgIGlmICgtbm90IChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRjIC1QYXRo"
"VHlwZSBMZWFmKSkgeyBjb250aW51ZSB9CiAgICAgICAgdHJ5IHsgJiAkYyAtSSAtYyAka2llbSAyPiRudWxsIHwgT3V0LU51bGw7IGlmICgkTEFTVEVYSVRDT0RFIC1lcSAwKSB7IHJldHVybiAkYyB9IH0gY2F0Y2gge30KICAgIH0KICAgIHRocm93ICgiS2hvbmcg"
"dGltIHRoYXkgUHl0aG9uIGNvIGdvaSAiICsgKCRHb2kgLWpvaW4gJywgJykgKyAiLiBDaGVwIHRodSBtdWMgQ0hPTkdUSEFNX3B5dGhvbiAoZ29pIFB5dGhvbiBtYW5nIHRoZW8sIGtob25nIGNhaSkgdmFvICIgKwogICAgICAgICI8bz46XEFJXF90b29sc1wsIGhv"
"YWMgY2hheSAxIGxhbjogcG93ZXJzaGVsbCAtTm9Qcm9maWxlIC1FeGVjdXRpb25Qb2xpY3kgQnlwYXNzIC1GaWxlIGAiIiArCiAgICAgICAgKEpvaW4tUGF0aCAkUFNTY3JpcHRSb290ICdjYWlfZGF0X3B5dGhvbi5wczEnKSArICJgIiAoaG9hYyBkYXQgYmllbiBt"
"b2kgdHJ1b25nIEFSQ0hJVklOQV9QWVRIT04gPSBkdW9uZyBkYW4gcHl0aG9uLmV4ZSkuIikKfQo="
)
("chong-tham-mat-bang/scripts/cai_dat_python.ps1"
"PCMKLlNZTk9QU0lTCiAgICBDYWkgbW9pIHRydW9uZyBQeXRob24gY2hvIGNhYyBza2lsbCBBUkNISVZJTkEgdHJlbiBNQVkgTU9JIChjaGF5IDEgbGFuLCBuZ3VvaSBkdW5nIHR1IGNoYXkpLgoKLkRFU0NSSVBUSU9OCiAgICBUYW8gdmVudiByaWVuZywgY2FpIGV6"
"ZHhmLCBzaGFwZWx5LCBvcGVucHl4bCwgbWF0cGxvdGxpYiAoa2hvbmcgY2FpIHZhbyBQeXRob24gaGUgdGhvbmcpOgogICAgICAtIGNvIHRodSBtdWMgZ29jIEFJICh2ZC4gRDpcQUksIHhlbSBtb2lfdHJ1b25nLnBzMSk6IDxnb2M+XF90b29sc1x2ZW52CiAgICAg"
"IC0ga2hvbmcgY286ICVMT0NBTEFQUERBVEElXEFSQ0hJVklOQVx2ZW52CiAgICBDYW4gUHl0aG9uIDMuMTArIGRhIGNhaSBzYW4gKHB5dGhvbi5vcmcsIGhvYWM6IHdpbmdldCBpbnN0YWxsIFB5dGhvbi5QeXRob24uMy4xMikuIFNjcmlwdCBraG9uZyB0dSBjYWkg"
"UHl0aG9uLgogICAgdmVudiBkYSBjbyB0aGkgY2hpIGNhaSBibyBzdW5nIGdvaSBjb24gdGhpZXUsIGtob25nIHhvYSBnaS4KCi5FWEFNUExFCiAgICBwb3dlcnNoZWxsIC1Ob1Byb2ZpbGUgLUV4ZWN1dGlvblBvbGljeSBCeXBhc3MgLUZpbGUgY2FpX2RhdF9weXRo"
"b24ucHMxCiM+CnBhcmFtKAogICAgW3N0cmluZ10kUHl0aG9uID0gJycsCiAgICAjIGxlbmggQ0hPTkdUSEFNIGdvaSBzY3JpcHQgbmF5IHRyb25nIGN1YSBzbyBoaWVuOiBkdW5nIGxhaSBjaG8gbmd1b2kgZHVuZyBkb2MgdHJ1b2Mga2hpIGRvbmcKICAgIFtzd2l0"
"Y2hdJER1bmcsCiAgICAjIGdoaSBrZXQgcXVhICJPSyIgLyAiTE9JIC4uLiIgcmEgZmlsZSBuYXkgKGxlbmggQ0hPTkdUSEFNIGRvYyBsYWkpCiAgICBbc3RyaW5nXSRLZXRRdWEgPSAnJwopCiRFcnJvckFjdGlvblByZWZlcmVuY2UgPSAnU3RvcCcKdHJ5IHsKLiAo"
"Sm9pbi1QYXRoICRQU1NjcmlwdFJvb3QgJ21vaV90cnVvbmcucHMxJykKCiRnb2MgPSBHZXQtR29jQUkKJHZlbnYgPSBpZiAoJGdvYykgeyBKb2luLVBhdGggJGdvYyAnX3Rvb2xzXHZlbnYnIH0gZWxzZSB7IEpvaW4tUGF0aCAkZW52OkxPQ0FMQVBQREFUQSAnQVJD"
"SElWSU5BXHZlbnYnIH0KJHB5VmVudiA9IEpvaW4tUGF0aCAkdmVudiAnU2NyaXB0c1xweXRob24uZXhlJwoKaWYgKC1ub3QgKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJHB5VmVudikpIHsKICAgICRuZW4gPSAkUHl0aG9uCiAgICBpZiAoLW5vdCAkbmVuKSB7CiAg"
"ICAgICAgJHB5ID0gR2V0LUNvbW1hbmQgcHkuZXhlIC1FcnJvckFjdGlvbiBTaWxlbnRseUNvbnRpbnVlCiAgICAgICAgaWYgKCRweSkgeyAkbmVuID0gKCYgJHB5LlNvdXJjZSAtMyAtYyAnaW1wb3J0IHN5czsgcHJpbnQoc3lzLmV4ZWN1dGFibGUpJykuVHJpbSgp"
"IH0KICAgIH0KICAgIGlmICgtbm90ICRuZW4pIHsKICAgICAgICAkYyA9IEdldC1Db21tYW5kIHB5dGhvbi5leGUgLUFsbCAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51ZSB8IFdoZXJlLU9iamVjdCB7ICRfLlNvdXJjZSAtbm90bWF0Y2ggJ1dpbmRvd3NBcHBz"
"JyB9IHwgU2VsZWN0LU9iamVjdCAtRmlyc3QgMQogICAgICAgIGlmICgkYykgeyAkbmVuID0gJGMuU291cmNlIH0KICAgIH0KICAgIGlmICgtbm90ICRuZW4pIHsgdGhyb3cgJ01heSBjaHVhIGNvIFB5dGhvbiAzLiBDYWkgUHl0aG9uIDMuMTIgKHB5dGhvbi5vcmcg"
"aG9hYzogd2luZ2V0IGluc3RhbGwgUHl0aG9uLlB5dGhvbi4zLjEyKSByb2kgY2hheSBsYWkuJyB9CiAgICBXcml0ZS1Ib3N0ICJUYW8gdmVudjogJHZlbnYgKHR1ICRuZW4pIgogICAgJiAkbmVuIC1tIHZlbnYgJHZlbnYKICAgIGlmICgkTEFTVEVYSVRDT0RFIC1u"
"ZSAwKSB7IHRocm93ICdUYW8gdmVudiBsb2kuJyB9Cn0KV3JpdGUtSG9zdCAnQ2FpIGdvaTogZXpkeGYgc2hhcGVseSBvcGVucHl4bCBtYXRwbG90bGliJwomICRweVZlbnYgLW0gcGlwIGluc3RhbGwgLS1kaXNhYmxlLXBpcC12ZXJzaW9uLWNoZWNrIGV6ZHhmIHNo"
"YXBlbHkgb3BlbnB5eGwgbWF0cGxvdGxpYgppZiAoJExBU1RFWElUQ09ERSAtbmUgMCkgeyB0aHJvdyAncGlwIGluc3RhbGwgbG9pIChraWVtIHRyYSBtYW5nKS4nIH0KJiAkcHlWZW52IC1JIC1jICdpbXBvcnQgZXpkeGYsIHNoYXBlbHksIG9wZW5weXhsLCBtYXRw"
"bG90bGliOyBwcmludCgiT0siLCBlemR4Zi5fX3ZlcnNpb25fXywgc2hhcGVseS5fX3ZlcnNpb25fXyknCmlmICgkTEFTVEVYSVRDT0RFIC1uZSAwKSB7IHRocm93ICdDYWkgeG9uZyBuaHVuZyBraG9uZyBpbXBvcnQgZHVvYyBnb2kuJyB9CldyaXRlLUhvc3QgIlhv"
"bmcuIFB5dGhvbjogJHB5VmVudiIKaWYgKCRLZXRRdWEpIHsgU2V0LUNvbnRlbnQgLUxpdGVyYWxQYXRoICRLZXRRdWEgLVZhbHVlICdPSycgLUVuY29kaW5nIEFTQ0lJIH0KfQpjYXRjaCB7CiAgICBXcml0ZS1Ib3N0ICgnTE9JOiAnICsgJF8uRXhjZXB0aW9uLk1l"
"c3NhZ2UpIC1Gb3JlZ3JvdW5kQ29sb3IgUmVkCiAgICBpZiAoJEtldFF1YSkgeyBTZXQtQ29udGVudCAtTGl0ZXJhbFBhdGggJEtldFF1YSAtVmFsdWUgKCdMT0kgJyArICRfLkV4Y2VwdGlvbi5NZXNzYWdlKSAtRW5jb2RpbmcgQVNDSUkgfQogICAgaWYgKCREdW5n"
"KSB7IFJlYWQtSG9zdCAnTmhhbiBFbnRlciBkZSBkb25nIGN1YSBzbycgfCBPdXQtTnVsbCB9CiAgICBleGl0IDEKfQppZiAoJER1bmcpIHsgUmVhZC1Ib3N0ICdOaGFuIEVudGVyIGRlIGRvbmcgY3VhIHNvJyB8IE91dC1OdWxsIH0K"
)
("chong-tham-mat-bang/scripts/tim_phong_uot.py"
"IyEvdXNyL2Jpbi9lbnYgcHl0aG9uCiMgLSotIGNvZGluZzogdXRmLTggLSotCiIiIkRvIHBob25nIHVvdCBjYW4gY2hvbmcgdGhhbSAoV0MsIGxvIGdpYSwgYmFuIGNvbmcsIHBob25nIGt5IHRodWF0IG51b2MsIHBob25nIHJhYykgdHJlbiBtYXQgYmFuZyB0YW5n"
"IChBcmNoaXZpbmEpLgoKRGF1IHZhbzogRFhGIGRhIE5PIEFFQyAoZHdnX3RvX2R4Zl9hZWMucHMxKS4gQ2FjaCBsYW06CiAgMS4gRHVuZyBsdW9pIG5ldCB0dW9uZyAvIGNvdCAvIGxhbiBjYW4gKyBraHVuZyBjdWEgKGhhbSBjdWEgZGllbi10aWNoLWNoXFxzY3Jp"
"cHRzXFx0YW9fcG9seWxpbmVfcGhvbmcucHkpLCBwb2x5Z29uaXplIHJhCiAgICAgY2FjIG8ga2luLgogIDIuIEhhdCBnaW9uZyBwaG9uZyB1b3Q6IHRoaWV0IGJpIHZlIHNpbmggKGJsb2NrIHRyZW4gbGF5ZXIgQS1JbnRlcmlvciBXQywgeGksIHNlbiwgbGF2YWJv"
"KSwgbWF5IGdpYXQgLyBjdWMgbm9uZyBkaWV1IGhvYSwKICAgICB0ZXh0IHRlbiBwaG9uZyAoV0MsIGxvIGdpYSwgYmFuIGNvbmcsIHBob25nIHJhYywgcGhvbmcga3kgdGh1YXQgbnVvYzsgYm8gdGV4dCAiVHJ1YyAuLi4iKS4KICAzLiBNb2kgaGF0IC0+IG8ga2lu"
"IG5obyBuaGF0IGNodWEgbm8gPSBwaG9uZy4gRGF5IGNhbmggcmEgTUFUIExPSSB0dW9uZyAoYm8gbG9wIHRyYXQgOC0yMiBtbSBuZXUgY28gbmV0IHNvbmcgc29uZykuCiAgNC4gRGFvOiB0cnVjIC8gaG9wIGt5IHRodWF0LCBjb3QsIHZhY2ggUy1XYWxsIG5hbSB0"
"cm9uZyBwaG9uZyAtPiBsbyB0cm9uZyBoYXRjaCAobmV0IHZlbiBraG9uZyBkaSB2b25nKS4KICA1LiBOZXQgdmVuIGNoYW4gdHVvbmc6IG9mZnNldCBiaWVuIHBob25nIHZhbyB0cm9uZyAtLWNhY2gtdmVuICg1MCksIG5nYXQgdGFpIGN1YSBkaSAoY3VhIGNvIGN1"
"bmcgcXVheSwgY3VhIHRydW90KQogICAgIHZhIG8gbW8ga2hvbmcgY28gdHVvbmcuClh1YXQ6IDx0ZW4+X2Nob25ndGhhbS5qc29uIChkdW5nIGNobyB2ZV9jaG9uZ190aGFtX3Zhb19iYW5fc2FvLnBzMSksIC5wbmc7IC54bHN4IGNoaSBraGkgY28gLS1leGNlbCAo"
"bmd1b2kgZHVuZyBjaG90IDIzLzEwLzIwMjY6IG1hYyBkaW5oIGtob25nIHRhbyBFeGNlbCkuIEtob25nIHN1YSBmaWxlIGRhdSB2YW8uCgogICAgcHl0aG9uIHRpbV9waG9uZ191b3QucHkgPGZpbGVfYWVjLmR4Zj4gLS1vdXQtZGlyIDx0aHUgbXVjPiBbLS12dW5n"
"IHgwLHkwLHgxLHkxXSBbLS1raG9uZy1hbmhdIFstLWV4Y2VsXQoiIiIKaW1wb3J0IGFyZ3BhcnNlCmltcG9ydCBpbXBvcnRsaWIudXRpbAppbXBvcnQganNvbgppbXBvcnQgbWF0aAppbXBvcnQgb3MKaW1wb3J0IHJlCmltcG9ydCBzeXMKZnJvbSBjb2xsZWN0aW9u"
"cyBpbXBvcnQgZGVmYXVsdGRpY3QKCmltcG9ydCBlemR4ZgppbXBvcnQgc2hhcGVseQpmcm9tIGV6ZHhmIGltcG9ydCBiYm94IGFzIGV6YmJveApmcm9tIHNoYXBlbHkuZ2VvbWV0cnkgaW1wb3J0IExpbmVTdHJpbmcsIE11bHRpTGluZVN0cmluZywgUG9pbnQsIFBv"
"bHlnb24sIGJveApmcm9tIHNoYXBlbHkub3BzIGltcG9ydCBsaW5lbWVyZ2UsIHBvbHlnb25pemUsIHVuYXJ5X3VuaW9uCgojIER1bmcgbGFpIGhhbSBkdW5nIGx1b2kgbmV0IC8ga2h1bmcgY3VhIC8gcG9seWdvbml6ZSBjdWEgc2tpbGwgZGllbi10aWNoLWNoLiBU"
"aW0gbzogYmllbiBBUkNISVZJTkFfRFRDSCwKIyBjYW5oIHNraWxsIG5heSAoLmNsYXVkZVxza2lsbHNcZGllbi10aWNoLWNoKSwgPGdvYz5cLmNsYXVkZVxza2lsbHMgKGdvYyA9IEFSQ0hJVklOQV9BSSBob2FjIGNoYSBjdWEgdGh1IG11YwojIHJlcG8pLCAlVVNF"
"UlBST0ZJTEUlXC5jbGF1ZGVcc2tpbGxzIC0+IGNoYXkgZHVvYyBvIG1heSBraGFjIC8gcmVwbyBHaXRIdWIgZGF0IHNraWxsIG8gZ29jIHJlcG8uCmRlZiBfdGltX2R0Y2goKToKICAgIHRlbiA9IG9zLnBhdGguam9pbigiZGllbi10aWNoLWNoIiwgInNjcmlwdHMi"
"LCAidGFvX3BvbHlsaW5lX3Bob25nLnB5IikKICAgIHNraWxsID0gb3MucGF0aC5kaXJuYW1lKG9zLnBhdGguZGlybmFtZShvcy5wYXRoLmFic3BhdGgoX19maWxlX18pKSkKICAgIHVuZyA9IFtvcy5lbnZpcm9uLmdldCgiQVJDSElWSU5BX0RUQ0giLCAiIiksCiAg"
"ICAgICAgICAgb3MucGF0aC5qb2luKG9zLnBhdGguZGlybmFtZShza2lsbCksIHRlbiksCiAgICAgICAgICAgb3MucGF0aC5qb2luKG9zLnBhdGguZGlybmFtZShza2lsbCksICIuY2xhdWRlIiwgInNraWxscyIsIHRlbiksCiAgICAgICAgICAgb3MucGF0aC5qb2lu"
"KG9zLmVudmlyb24uZ2V0KCJBUkNISVZJTkFfQUkiLCAiIiksICIuY2xhdWRlIiwgInNraWxscyIsIHRlbikgaWYgb3MuZW52aXJvbi5nZXQoIkFSQ0hJVklOQV9BSSIpIGVsc2UgIiIsCiAgICAgICAgICAgb3MucGF0aC5qb2luKG9zLnBhdGguZXhwYW5kdXNlcigi"
"fiIpLCAiLmNsYXVkZSIsICJza2lsbHMiLCB0ZW4pXQogICAgZm9yIGMgaW4gdW5nOgogICAgICAgIGlmIGMgYW5kIG9zLnBhdGguaXNmaWxlKGMpOgogICAgICAgICAgICByZXR1cm4gYwogICAgc3lzLmV4aXQoIktob25nIHRoYXkgc2tpbGwgZGllbi10aWNoLWNo"
"ICh0YW9fcG9seWxpbmVfcGhvbmcucHkpIC0gY2FuIHNraWxsIG5heSBkZSBkdW5nIGx1b2kgbmV0IHR1b25nLiAiCiAgICAgICAgICAgICAiQ2hlcCB0aHUgbXVjIGRpZW4tdGljaC1jaCBjYW5oIHRodSBtdWMgY2hvbmctdGhhbS1tYXQtYmFuZywgaG9hYyBkYXQg"
"YmllbiBBUkNISVZJTkFfRFRDSC4gRGEgdGltOiAiCiAgICAgICAgICAgICArICI7ICIuam9pbihjIGZvciBjIGluIHVuZyBpZiBjKSkKCgpfRFRDSCA9IF90aW1fZHRjaCgpCl9zcGVjID0gaW1wb3J0bGliLnV0aWwuc3BlY19mcm9tX2ZpbGVfbG9jYXRpb24oInRh"
"b19wb2x5bGluZV9waG9uZyIsIF9EVENIKQp0cHAgPSBpbXBvcnRsaWIudXRpbC5tb2R1bGVfZnJvbV9zcGVjKF9zcGVjKQpfc3BlYy5sb2FkZXIuZXhlY19tb2R1bGUodHBwKQpib19kYXUsIGxheWVyX2dvYyA9IHRwcC5ib19kYXUsIHRwcC5sYXllcl9nb2MKCkxB"
"WUVSX1ZFID0gIkEtTWF0ZXJpYWwiCiMgTGF5ZXIgbGFtIHJhbmggcGhvbmcuIEEtTWF0ZXJpYWw6IHRoYW5oIHBoYW4gdHVvbmcgQUNBIHNhdSBraGkgbm8gKGxvaSArIHRyYXQpIG5hbSB0cmVuIGxheWVyIG5heSBvIGR1IGFuIDI1NEhRVi4KTEFZRVJfUkFOSCA9"
"IFsiQS1XYWxsIiwgIkEtTWF0ZXJpYWwiLCAiQS1Db2x1bW4iLCAiQS1MaW5lIiwgIlMtV2FsbCIsICJBLUxhbmNhbiIsICJBX1dhbGwgQlQiLCAiQS1WdWEgdHJhdCJdCkxBWUVSX0NVQSA9IHRwcC5MQVlFUl9DVUEKTEFZRVJfV0MgPSAiQS1JbnRlcmlvciBXQyIK"
"IyBUZW4gYmxvY2sgKGtob25nIGRhdSwgY2h1IHRodW9uZykgdGhpZXQgYmkgdmUgc2luaCAvIGxvIGdpYQpSRV9UQl9XQyA9IHIi6ams5qG2fOWPsOebhnx0b2lsZXR8XGJiZXRcYnxib24gY2F1fHNlblxifHZvaSBzZW58bGF2YWJvfGNoYXUgcnVhIG1hdHx0aWV1"
"IG5hbXx1cmluYWx8Ym9uIHRhbSIKUkVfVEJfTEcgPSByIm1heSBnaWF0fHdhc2hpbmd8dnJmfGN1YyBub25nfGRhbiBub25nfGRpZXUgaG9hfG91dGRvb3J8bWF5IHNheXxnaWF0IHNheSIKIyBvbmcgZHVuZyAodmQuICdwaXBlZDEyNS14aScpLCBibG9jayB0cnVj"
"IHRhbmcgYXAgJ1RBMScgKENUMSB0YW5nIDVBLTEwLCBuYW0gdHJlbiBsYXllciBBLUludGVyaW9yIFdDKSBraG9uZyBwaGFpIHRoaWV0IGJpClJFX1RCX0JPID0gciJecGlwZXxeb25nXGJ8b25nIGR1bmd8cGlwZWR8XnRhXGQqJCIKUkVfTEFOX0NBTiA9IHIibGFu"
"ID9jYW58cmFpbGluZ3xiYWx1c3RyYWRlfGxvdXZlciIgICMgYmxvY2sgbGFuIGNhbiAvIGxhbTogcGhvbmcgc2F0IGxhbiBjYW4gbGEgbG8gZ2lhIC8gYmFuIGNvbmcKTk9JX0RBSSA9IDQwLjAgICAgICAgIyBtbTogbm9pIGRhaSBkYXUgbmV0IGhvIHRvaSBuZXQg"
"Z2FuIG5oYXQgKG5ldCB0dW9uZyBsdW5nIG5nYW4gaHV0IDE1IG1tIHNvIHZvaSB0dW9uZyB2dW9uZyBnb2MpCkxHX0RUID0gKDEuMCwgMTIuMCkgICMgbTI6IGxvIGdpYSBuaGFuIHRoZW8gY3VhIHRydW90IC8gbGFuIGNhbgojIFRleHQgdGVuIHBob25nIChraG9u"
"ZyBkYXUsIGNodSB0aHVvbmcpClJFX1RFTiA9IFsoInBob25nX3JhYyIsIHIicGhvbmcgcmFjfHBcLj8gP3JhY1xifGtobyByYWMiKSwKICAgICAgICAgICgicGhvbmdfa3RfbnVvYyIsIHIiKHBob25nfHBcLik/ID8oa3kgdGh1YXR8a1wuP3RcLj8pID8oY2FwIHx0"
"aG9hdCApP251b2N8Ym9tIG51b2N8cGhvbmcgYm9tIiksCiAgICAgICAgICAoIndjIiwgciJcYndjXGJ8dmUgc2luaHxcYnZzXGJ8cGhvbmcgdGFtIiksCiAgICAgICAgICAoImxvX2dpYSIsIHIibG8gP2dpYXxsb2dpYXxsb2dnaWF8YmFuIGNvbmciKV0KUkVfVEVO"
"X0JPID0gciJeXHMqKHRydWN8aG9wfG9uZ3xvIHRob2FuZ3xnaWVuZykiICAgICAjICJUcnVjIGt5IHRodWF0IG51b2MiLCAiVHJ1YyBodXQgbXVpIHJhYyIgbGEgdHJ1Yywga2hvbmcgcGhhaSBwaG9uZwojIEt5IGhpZXUgcGhvbmcgMSBjaHUgKHNvIGtob3Agbmd1"
"eWVuIHZhbiwgY2h1IGhvYSk6IHRhbmcgNCBUaGFwIEIgZ2hpICJSIiA9IHBob25nIHJhYywgIk4iID0gcGhvbmcga3kgdGh1YXQgbnVvYywKIyB0cmVuIGxheWVyIERlZnBvaW50cyAobmd1b2kgZHVuZyBjaG90IDIyLzEwLzIwMjYpLiBLeSBoaWV1IG5hbSB0cm9u"
"ZyBvIEtIT05HIGNvIGN1YSAoaG9wIGt5IHRodWF0KSB0aGkgYm8gcXVhLgojIENUMSB0YW5nIDVBLTEwIGdoaSBwaG9uZyBreSB0aHVhdCBudW9jIGxhICJLVE4iIChuZ3VvaSBkdW5nIGJvIHN1bmcgMjMvMTAvMjAyNikKS1lfSElFVSA9ICJSPXBob25nX3JhYyxO"
"PXBob25nX2t0X251b2MsS1ROPXBob25nX2t0X251b2MiCkRUX0JVT05HX0RFTSA9IDEwLjAgICMgbTI6IGJ1b25nIGRlbSBwaG9uZyByYWMgbG9uIG5oYXQKIyBMYXllciBuZXQgbWF0IG5nb2FpIChsYW4gY2FuLCBtZXAgc2FuKSBkdW5nIGRlIGtoZXAgbG8gZ2lh"
"IGtoaSB0aGlldCBiaSBraG9uZyBuYW0gdHJvbmcgbyBraW4gbmFvCkxBWUVSX01BVF9OR09BSSA9IHIiXigwfGEtbGluZVxkKikkIgojIExheWVyIG5ldCBkYW8gdHJvbmcgcGhvbmc6IHRydWMgLyBob3Aga3kgdGh1YXQsIGNvdCwgdmFjaApSRV9MQVlFUl9EQU8g"
"PSByInRydWN8aGt0fGhvcCBreSB0aHVhdHxhLW1lcHxhLWNvbHVtbnxzLXdhbGx8c2hhZnQiCiMgTmh1bmcgYm8gbmV0IG9uZyAvIGN1bSBvbmcgKHZkLiBDVDIgJ0FWLU1FLeG7kG5nIHRy4bulYyDEkeG7qW5nJywgJ0FWLU1FLUPDuW0g4buRbmcnKTogdm9uZyB0"
"cm9uIG9uZyBjYXQgaG9wIHRoYW5oIG1hbmggdnVuCiMgLT4gbWF0IGNhIGhvcCAobmd1b2kgZHVuZyBiYW8gbG9pIDIzLzEwLzIwMjYpClJFX0xBWUVSX0RBT19CTyA9IHIiXGJvbmdcYnxjdW0gb25nfHBpcGUiCkRBT19LSU5fRFQgPSAoMC4wMmU2LCA2ZTYpICAg"
"IyBtbTI6IHBvbHlsaW5lIGtpbiB0cmVuIGxheWVyIHRydWMgLyBBLU1FUCBsYXkgbmd1eWVuIGxhbSBkYW8gbmV1IHBvbHlnb25pemUgYm8gc290ClRFTl9MT0FJID0geyJ3YyI6ICJXQyIsICJsb19naWEiOiAiTMO0IGdpYSAvIGJhbiBjw7RuZyIsICJwaG9uZ19y"
"YWMiOiAiUGjDsm5nIHLDoWMiLCAicGhvbmdfa3RfbnVvYyI6ICJQaMOybmcgS1Qgbsaw4bubYyIsCiAgICAgICAgICAgICJidW9uZ19kZW1fcmFjIjogIkJ14buTbmcgxJHhu4dtIHBow7JuZyByw6FjIn0KVVVfVElFTiA9IHsicGhvbmdfcmFjIjogMCwgImJ1b25n"
"X2RlbV9yYWMiOiAxLCAicGhvbmdfa3RfbnVvYyI6IDIsICJ3YyI6IDMsICJsb19naWEiOiA0fQpDQU5fQ1VBID0geyJwaG9uZ19yYWMiLCAicGhvbmdfa3RfbnVvYyJ9ICAgIyBuaGFuIHRoZW8ga3kgaGlldSAvIHRlbjogbyBwaGFpIGNvIGN1YSBkaSBtb2kgbGEg"
"cGhvbmcKCgpkZWYgcjEodik6CiAgICByZXR1cm4gcm91bmQoZmxvYXQodiksIDEpCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIGRvYyBiYW4gdmUKZGVmIGxvY19tc3AobXNwKToKICAg"
"ICIiIkJvIGNob25nIHRoYW0gZGEgdmUgKGhhdGNoIC8gcG9seWxpbmUgQS1NYXRlcmlhbCBvIE1vZGVsLCBibG9jayBDSE9ORyBUSEFNKikga2hvaSBuZXQgbmVuLiIiIgogICAgb3V0ID0gW10KICAgIGZvciBlIGluIG1zcDoKICAgICAgICB0ID0gZS5keGZ0eXBl"
"KCkKICAgICAgICBpZiB0ID09ICJJTlNFUlQiIGFuZCBib19kYXUoZS5keGYubmFtZSkuc3RhcnRzd2l0aCgiY2hvbmcgdGhhbSIpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIHQgaW4gKCJIQVRDSCIsICJMV1BPTFlMSU5FIikgYW5kIGxheWVyX2dv"
"YyhlLmR4Zi5sYXllcikgPT0gbGF5ZXJfZ29jKExBWUVSX1ZFKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBvdXQuYXBwZW5kKGUpCiAgICByZXR1cm4gb3V0CgoKX1hSRUYgPSB7fSAgICMgZHVvbmcgZGFuIERYRiB4cmVmIC0+IChkb2MsIGRvaSB0dW9u"
"ZyBkYSBnb20geHJlZiBjb24pCgoKZGVmIG1hX2Nhbl94cmVmKG5hbWUpOgogICAgIiIiJ0NUMiAtIENILjA1QScgLT4gJ0NIMDVBJyAobWEgY2FuIHR1IHRlbiB4cmVmIGNhbiBobykuIiIiCiAgICBtID0gcmUuc2VhcmNoKHIiXGJDSFtccy5cLV0qKFxkK1tBLVpd"
"PylcYiIsIG5hbWUgb3IgIiIsIHJlLkkpCiAgICByZXR1cm4gKCJDSCIgKyBtLmdyb3VwKDEpKS51cHBlcigpIGlmIG0gZWxzZSAiIgoKCmRlZiBkb2NfeHJlZihlbnRzLCBkeGZfcGF0aCwgZGVwdGg9MCk6CiAgICAiIiJOb2kgZHVuZyB4cmVmIG5nb2FpLCBLSE9O"
"RyBiaW5kIChuZ3VvaSBkdW5nIGNob3QgMjMvMTAvMjAyNiwga2UgY2EgYmFuIHRhbSk6IGR3Z190b19keGZfYWVjLnBzMSBjaHV5ZW4gcmllbmcgbW9pCiAgICB4cmVmIHRoYW5oIERYRiAobm8gQUVDIHRyZW4gYmFuIHNhbykgdmEgZ2hpIDx0ZW4+X3hyZWYudHh0"
"ICJ0ZW58ZHVvbmcgZGFufGR4ZiIuIExheSBkb2kgdHVvbmcgTW9kZWwgY3VhIERYRiB4cmVmLAogICAgc2FvIGFvICsgYmllbiBkb2kgdGhlbyBJTlNFUlQgeHJlZiB0cm9uZyBiYW4gdmUgY2h1LCBjaGkgdHJvbmcgYm8gbmhvLCBraG9uZyBnaGkgZmlsZSBuYW8u"
"CiAgICBUcmEgdmUgKGRvaSB0dW9uZyB0b2EgZG8gTW9kZWwsIFsoa2h1bmcgYmFvLCBtYSBjYW4pXSkuIiIiCiAgICBmID0gb3MucGF0aC5zcGxpdGV4dChkeGZfcGF0aClbMF0gKyAiX3hyZWYudHh0IgogICAgaWYgZGVwdGggPiAyIG9yIG5vdCBvcy5wYXRoLmV4"
"aXN0cyhmKToKICAgICAgICByZXR1cm4gW10sIFtdCiAgICBiYW5nID0ge30KICAgIHdpdGggb3BlbihmLCBlbmNvZGluZz0idXRmLTgtc2lnIikgYXMgZmk6CiAgICAgICAgZm9yIGRvbmcgaW4gZmk6CiAgICAgICAgICAgIHAgPSBkb25nLnJzdHJpcCgiXHJcbiIp"
"LnNwbGl0KCJ8IikKICAgICAgICAgICAgaWYgbGVuKHApID49IDMgYW5kIHBbMl0gYW5kIG9zLnBhdGguZXhpc3RzKHBbMl0pOgogICAgICAgICAgICAgICAgYmFuZ1twWzBdLmxvd2VyKCldID0gcFsyXQogICAgb3V0LCBraHVuZyA9IFtdLCBbXQogICAgZm9yIGUg"
"aW4gZW50czoKICAgICAgICBpZiBlLmR4ZnR5cGUoKSAhPSAiSU5TRVJUIiBvciBlLmR4Zi5uYW1lLmxvd2VyKCkgbm90IGluIGJhbmc6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgeCA9IGJhbmdbZS5keGYubmFtZS5sb3dlcigpXQogICAgICAgIGlmIHgg"
"bm90IGluIF9YUkVGOgogICAgICAgICAgICB4ZCA9IGV6ZHhmLnJlYWRmaWxlKHgpCiAgICAgICAgICAgIHhlID0gbG9jX21zcCh4ZC5tb2RlbHNwYWNlKCkpCiAgICAgICAgICAgIGNvbiwgXyA9IGRvY194cmVmKHhlLCB4LCBkZXB0aCArIDEpICAgICAgICAgICAj"
"IHhyZWYgbG9uZyBuaGF1OiBkYSBvIHRvYSBkbyBjdWEgeHJlZiBuYXkKICAgICAgICAgICAgX1hSRUZbeF0gPSAoeGQsIHhlICsgY29uKQogICAgICAgIG0gPSBlLm1hdHJpeDQ0KCkKICAgICAgICBtb2kgPSBbXQogICAgICAgIGZvciB2IGluIF9YUkVGW3hdWzFd"
"OgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBjID0gdi5jb3B5KCkKICAgICAgICAgICAgICAgIGMudHJhbnNmb3JtKG0pCiAgICAgICAgICAgICAgICBtb2kuYXBwZW5kKGMpCiAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAg"
"ICAgICBwYXNzCiAgICAgICAgb3V0ICs9IG1vaQogICAgICAgIGNhbiA9IG1hX2Nhbl94cmVmKGUuZHhmLm5hbWUpCiAgICAgICAgaWYgY2FuIGFuZCBtb2k6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIGIgPSBlemJib3guZXh0ZW50cyhtb2ksIGZh"
"c3Q9VHJ1ZSkKICAgICAgICAgICAgICAgIGlmIGIuaGFzX2RhdGE6CiAgICAgICAgICAgICAgICAgICAga2h1bmcuYXBwZW5kKChib3goYi5leHRtaW4ueCwgYi5leHRtaW4ueSwgYi5leHRtYXgueCwgYi5leHRtYXgueSksIGNhbikpCiAgICAgICAgICAgIGV4Y2Vw"
"dCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICBwYXNzCiAgICByZXR1cm4gb3V0LCBraHVuZwoKCmRlZiBkdXlldF9pbnNlcnQoZW50aXRpZXMsIGRlcHRoPTAsIG1heF9kZXB0aD00LCBwYXJfbGF5ZXI9Tm9uZSk6CiAgICAiIiJTaW5oIChpbnNlcnQgYW8sIHRl"
"biBibG9jaywgbGF5ZXIgaGlldSBkdW5nKSBjaG8gbW9pIElOU0VSVCwga2UgY2EgbG9uZyBuaGF1ICh0b2EgZG8gTW9kZWwpLiIiIgogICAgZm9yIGUgaW4gZW50aXRpZXM6CiAgICAgICAgaWYgZS5keGZ0eXBlKCkgIT0gIklOU0VSVCI6CiAgICAgICAgICAgIGNv"
"bnRpbnVlCiAgICAgICAgbGF5ID0gcGFyX2xheWVyIGlmIChwYXJfbGF5ZXIgYW5kIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgPT0gIjAiKSBlbHNlIGUuZHhmLmxheWVyCiAgICAgICAgeWllbGQgZSwgZS5keGYubmFtZSwgbGF5CiAgICAgICAgaWYgZGVwdGggPCBt"
"YXhfZGVwdGg6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHN1YnMgPSBsaXN0KGUudmlydHVhbF9lbnRpdGllcygpKQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgeWllbGQg"
"ZnJvbSBkdXlldF9pbnNlcnQoc3VicywgZGVwdGggKyAxLCBtYXhfZGVwdGgsIGxheSkKCgpkZWYgZHV5ZXRfdGV4dChlbnRpdGllcywgZGVwdGg9MCwgbWF4X2RlcHRoPTQpOgogICAgZm9yIGUgaW4gZW50aXRpZXM6CiAgICAgICAgdCA9IGUuZHhmdHlwZSgpCiAg"
"ICAgICAgaWYgdCBpbiAoIlRFWFQiLCAiTVRFWFQiKToKICAgICAgICAgICAgeWllbGQgZQogICAgICAgIGVsaWYgdCA9PSAiSU5TRVJUIiBhbmQgZGVwdGggPCBtYXhfZGVwdGg6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHlpZWxkIGZyb20gZHV5"
"ZXRfdGV4dChsaXN0KGUudmlydHVhbF9lbnRpdGllcygpKSwgZGVwdGggKyAxLCBtYXhfZGVwdGgpCiAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICBwYXNzCgoKZGVmIHRhbV9iYm94KGUpOgogICAgdHJ5OgogICAgICAgIGIgPSBl"
"emJib3guZXh0ZW50cyhbZV0sIGZhc3Q9VHJ1ZSkKICAgICAgICBpZiBiLmhhc19kYXRhOgogICAgICAgICAgICByZXR1cm4gKChiLmV4dG1pbi54ICsgYi5leHRtYXgueCkgLyAyLCAoYi5leHRtaW4ueSArIGIuZXh0bWF4LnkpIC8gMiksIChiLnNpemUueCwgYi5z"
"aXplLnkpCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHBhc3MKICAgIHJldHVybiAoZS5keGYuaW5zZXJ0LngsIGUuZHhmLmluc2VydC55KSwgKDAsIDApCgoKZGVmIG1hX2NhbihuYW1lKToKICAgIG0gPSByZS5tYXRjaChyIlxzKihDSFxzP1xkK1tBLVpd"
"PykiLCBuYW1lIG9yICIiLCByZS5JKQogICAgcmV0dXJuIG0uZ3JvdXAoMSkudXBwZXIoKS5yZXBsYWNlKCIgIiwgIiIpIGlmIG0gZWxzZSAiIgoKCmRlZiBkb2NfaGF0X2dpb25nKGVudHMsIGEpOgogICAgIiIiSGF0IGdpb25nOiAobG9haSwgZGllbSwgbmd1b24s"
"IGNhbikuIiIiCiAgICByZV93YywgcmVfbGcsIHJlX2JvID0gcmUuY29tcGlsZShhLnRiX3djLCByZS5JKSwgcmUuY29tcGlsZShhLnRiX2xnLCByZS5JKSwgcmUuY29tcGlsZShSRV9UQl9CTykKICAgIHNlZWRzID0gW10KICAgIGZvciBlLCBuYW1lLCBsYXkgaW4g"
"ZHV5ZXRfaW5zZXJ0KGVudHMpOgogICAgICAgIG4gPSBib19kYXUobmFtZSkKICAgICAgICB0ZW5fbmdhbiA9IG4uc3BsaXQoIiQiKVstMV0KICAgICAgICBpZiByZV9iby5zZWFyY2godGVuX25nYW4pOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGxvYWkg"
"PSBOb25lCiAgICAgICAgaWYgcmVfd2Muc2VhcmNoKHRlbl9uZ2FuKSBvciBsYXllcl9nb2MobGF5KSA9PSBsYXllcl9nb2MoTEFZRVJfV0MpOgogICAgICAgICAgICBsb2FpID0gIndjIgogICAgICAgIGVsaWYgcmVfbGcuc2VhcmNoKHRlbl9uZ2FuKToKICAgICAg"
"ICAgICAgbG9haSA9ICJsb19naWEiCiAgICAgICAgaWYgbm90IGxvYWk6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgcCwgc3ogPSB0YW1fYmJveChlKQogICAgICAgIGlmIG1heChzeikgPiAzMDAwOiAgICAgICAgICAgICMgYmxvY2sgbG9uIChjYSBjdW0g"
"bm9pIHRoYXQgLyBjYSBjYW4pIGtob25nIGxhbSBoYXQgZ2lvbmcKICAgICAgICAgICAgY29udGludWUKICAgICAgICBzZWVkcy5hcHBlbmQoKGxvYWksIHAsIG5hbWUuc3BsaXQoIiQiKVstMV0sIG1hX2NhbihuYW1lKSkpCiAgICByZV9ibyA9IHJlLmNvbXBpbGUo"
"UkVfVEVOX0JPKQogICAga3kgPSBkaWN0KGt2LnNwbGl0KCI9IikgZm9yIGt2IGluIGEua3lfaGlldS5zcGxpdCgiLCIpIGlmICI9IiBpbiBrdikKICAgIGZvciBlIGluIGR1eWV0X3RleHQoZW50cyk6CiAgICAgICAgZ29jID0gKGUucGxhaW5fdGV4dCgpIGlmIGUu"
"ZHhmdHlwZSgpID09ICJNVEVYVCIgZWxzZSBlLmR4Zi50ZXh0KS5zdHJpcCgpCiAgICAgICAgaWYgZ29jIGluIGt5OiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIGt5IGhpZXUgMSBjaHUgIlIiLCAiTiIgKHNvIG5ndXllbiB2YW4sIHBoYW4gYmll"
"dCBob2EgdGh1b25nKQogICAgICAgICAgICBwLCBfID0gdGFtX2Jib3goZSkKICAgICAgICAgICAgc2VlZHMuYXBwZW5kKChreVtnb2NdLCBwLCAia8O9IGhp4buHdTogIiArIGdvYywgIiIpKQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHMgPSBib19kYXUo"
"Z29jKQogICAgICAgIGlmIG5vdCBzIG9yIGxlbihzKSA+IDQwIG9yIHJlX2JvLnNlYXJjaChzKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBmb3IgbG9haSwgcnggaW4gUkVfVEVOOgogICAgICAgICAgICBpZiByZS5zZWFyY2gocngsIHMpOgogICAgICAg"
"ICAgICAgICAgcCA9IGUuZHhmLmluc2VydAogICAgICAgICAgICAgICAgc2VlZHMuYXBwZW5kKChsb2FpLCAocC54LCBwLnkpLCAidGV4dDogIiArIHMsICIiKSkKICAgICAgICAgICAgICAgIGJyZWFrCiAgICByZXR1cm4gc2VlZHMKCgpkZWYgZG9jX2RhbyhlbnRz"
"KToKICAgICIiIk5ldCB0cmVuIGxheWVyIHRydWMgLyBob3Aga3kgdGh1YXQgLyBjb3QgLyB2YWNoIChrZSBjYSB0cm9uZyBibG9jaykgLT4gcG9seWdvbiBkYW8uIiIiCiAgICByeCwgcnhfYm8gPSByZS5jb21waWxlKFJFX0xBWUVSX0RBTyksIHJlLmNvbXBpbGUo"
"UkVfTEFZRVJfREFPX0JPKQogICAgc2Vncywga2luID0gW10sIFtdCiAgICBmb3IgZSBpbiB0cHAud2FsayhlbnRzLCBtYXhfZGVwdGg9NCk6CiAgICAgICAgaWYgZS5keGZ0eXBlKCkgbm90IGluICgiTElORSIsICJMV1BPTFlMSU5FIik6CiAgICAgICAgICAgIGNv"
"bnRpbnVlCiAgICAgICAgbGF5ID0gYm9fZGF1KGxheWVyX2dvYyhlLmR4Zi5sYXllcikpCiAgICAgICAgaWYgbm90IHJ4LnNlYXJjaChsYXkpIG9yIHJ4X2JvLnNlYXJjaChsYXkpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIGUuZHhmdHlwZSgpID09"
"ICJMSU5FIjoKICAgICAgICAgICAgc2Vncy5hcHBlbmQoTGluZVN0cmluZyhbKGUuZHhmLnN0YXJ0LngsIGUuZHhmLnN0YXJ0LnkpLCAoZS5keGYuZW5kLngsIGUuZHhmLmVuZC55KV0pKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHB0cyA9IFsodlswXSwgdlsx"
"XSkgZm9yIHYgaW4gZS5nZXRfcG9pbnRzKCldCiAgICAgICAgICAgIGlmIGUuY2xvc2VkIGFuZCBsZW4ocHRzKSA+IDI6CiAgICAgICAgICAgICAgICBpZiBsZW4ocHRzKSA+PSAzOgogICAgICAgICAgICAgICAgICAgIHEgPSBQb2x5Z29uKHB0cykKICAgICAgICAg"
"ICAgICAgICAgICBpZiBxLmlzX3ZhbGlkIGFuZCBEQU9fS0lOX0RUWzBdIDw9IHEuYXJlYSA8PSBEQU9fS0lOX0RUWzFdOgogICAgICAgICAgICAgICAgICAgICAgICBraW4uYXBwZW5kKHEpCiAgICAgICAgICAgICAgICBwdHMuYXBwZW5kKHB0c1swXSkKICAgICAg"
"ICAgICAgaWYgbGVuKHB0cykgPj0gMjoKICAgICAgICAgICAgICAgIHNlZ3MuYXBwZW5kKExpbmVTdHJpbmcocHRzKSkKICAgIGlmIG5vdCBzZWdzOgogICAgICAgIHJldHVybiBbXQogICAgcG9seXMgPSBsaXN0KHBvbHlnb25pemUoc2hhcGVseS51bmlvbl9hbGwo"
"c2VncywgZ3JpZF9zaXplPTAuMDEpKSkKICAgIGxvbmcsIHRhbWdpYWMgPSBbXSwgW10KICAgIGZvciBwIGluIHBvbHlzOgogICAgICAgIGxvID0gc3VtKFBvbHlnb24ocikuYXJlYSBmb3IgciBpbiBwLmludGVyaW9ycykKICAgICAgICBpZiBwLmludGVyaW9ycyBh"
"bmQgbG8gPj0gMC41ICogUG9seWdvbihwLmV4dGVyaW9yKS5hcmVhOgogICAgICAgICAgICBjb250aW51ZSAgICAgICAgIyB2byBob3AgKHZhY2ggbW9uZyBiYW8gcXVhbmggbG9uZyBob3ApOiBibywgbG9uZyBob3AgbGEgbyByaWVuZyAobWF1IENIMTU6IHZvIGhv"
"cCB2YW4gaGF0Y2gpCiAgICAgICAgcSA9IFBvbHlnb24ocC5leHRlcmlvcikgICAgICAgICAgICAgICAgICAgICAgICMgbG8gbmhvIGJlbiB0cm9uZyAob25nIHRyb24pIGtob25nIHRpbmgKICAgICAgICBpZiBsZW4oc2hhcGVseS5zaW1wbGlmeShxLCAxKS5leHRl"
"cmlvci5jb29yZHMpID09IDQ6CiAgICAgICAgICAgIHRhbWdpYWMuYXBwZW5kKHEpICAgICAgICAgICAgICAgICAgICAgICAgICMgdGFtIGdpYWMgY3VhIGRhdSBYOiBnb3AgbGFpIHRoYW5oIG8gaG9wCiAgICAgICAgZWxzZToKICAgICAgICAgICAgbG9uZy5hcHBl"
"bmQocSkKICAgIGlmIHRhbWdpYWM6CiAgICAgICAgZ29wID0gdW5hcnlfdW5pb24oW3QuYnVmZmVyKDAuNSwgam9pbl9zdHlsZT0ibWl0cmUiKSBmb3IgdCBpbiB0YW1naWFjXSkKICAgICAgICBsb25nICs9IFtQb2x5Z29uKGcuZXh0ZXJpb3IpLmJ1ZmZlcigtMC41"
"LCBqb2luX3N0eWxlPSJtaXRyZSIpIGZvciBnIGluIChnb3AuZ2VvbXMgaWYgaGFzYXR0cihnb3AsICJnZW9tcyIpIGVsc2UgW2dvcF0pXQogICAgIyBvIGhlcCA8IDEwMCBtbSBsYSB2YWNoIHZvIGhvcCAvIGJhdSwga2hvbmcgcGhhaSBsb25nIGhvcCAobWF1IENI"
"MTU6IHZvIGhvcCA4MCBtbSB2YW4gaGF0Y2gpCiAgICBsb25nID0gW2cuc2ltcGxpZnkoNSkgZm9yIGcgaW4gbG9uZyBpZiBnLmFyZWEgPj0gMC4wMmU2IGFuZCBub3QgZy5idWZmZXIoLTUwKS5pc19lbXB0eV0KICAgIGxvbmcuc29ydChrZXk9bGFtYmRhIGc6IC1n"
"LmFyZWEpCiAgICBvdXQgPSBbXQogICAgZm9yIGcgaW4gbG9uZzogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIG8gbmFtIHRyb25nIG8gZGEgZ2l1IChvIGNoaWEgYm9pIG9uZywgbmV0IHRyb25nIGhvcCkgLT4gYm8KICAgICAgICBpZiBub3Qg"
"YW55KG8uYnVmZmVyKDIpLmNvbnRhaW5zKGcpIGZvciBvIGluIG91dCk6CiAgICAgICAgICAgIG91dC5hcHBlbmQoZykKICAgICMgRHUgcGhvbmc6IGhvcCB2ZSBiYW5nIHBvbHlsaW5lIGtpbiAodmQuICdBLU1lcCcgQ1QyKSBtYSBwb2x5Z29uaXplIGJvIHNvdCAo"
"YmkgbmV0IHRyb25nIGhvcCBjYXQgdnVuKSAtPiBsYXkgbmd1eWVuCiAgICBmb3IgayBpbiBzb3J0ZWQoa2luLCBrZXk9bGFtYmRhIGc6IGcuYXJlYSk6CiAgICAgICAgaWYgbm90IGFueShvLmludGVyc2VjdGlvbihrKS5hcmVhID49IDAuMyAqIGsuYXJlYSBmb3Ig"
"byBpbiBvdXQpOgogICAgICAgICAgICBvdXQuYXBwZW5kKGsuc2ltcGxpZnkoNSkpCiAgICByZXR1cm4gb3V0CgoKZGVmIHRpbV9jYW4oZW50cyk6CiAgICAiIiJUYW0gY2FjIElOU0VSVCB0ZW4gJ0NIeHggKFQ0KSQwJC4uLicgKHRoaWV0IGJpLCBub2kgdGhhdCBj"
"dWEgY2FuKSAtPiAoY2F5LCBtYSBjYW4pIGRlIGdhbiBtYSBjYW4gY2hvIHBob25nLiIiIgogICAgcHRzLCBtYSA9IFtdLCBbXQogICAgZm9yIGUsIG5hbWUsIGxheSBpbiBkdXlldF9pbnNlcnQoZW50cyk6CiAgICAgICAgbSA9IG1hX2NhbihuYW1lKQogICAgICAg"
"IGlmIG0gYW5kICIkIiBpbiBuYW1lOgogICAgICAgICAgICBwLCBzeiA9IHRhbV9iYm94KGUpCiAgICAgICAgICAgIGlmIG1heChzeikgPCA1MDAwOgogICAgICAgICAgICAgICAgcHRzLmFwcGVuZChQb2ludChwKSkKICAgICAgICAgICAgICAgIG1hLmFwcGVuZCht"
"KQogICAgcmV0dXJuIChzaGFwZWx5LlNUUnRyZWUocHRzKSwgcHRzLCBtYSkgaWYgcHRzIGVsc2UgTm9uZQoKCmRlZiBjdWFfbmV0X3JvaShlbnRzLCB3YW50LCBnYW49MzAuMCk6CiAgICAiIiJDdWEgLyBjdWEgc28gdmUgYmFuZyBORVQgUk9JIHRyZW4gbGF5ZXIg"
"Y3VhIChraG9uZyBwaGFpIGJsb2NrKTogQ1QyIHhyZWYgY2FuIGhvIHNhdSBraGkgbm8gQUVDX0RPT1IgY2hpIGNvbgogICAgTElORSAvIExXUE9MWUxJTkUgLyBBUkMgdHJlbiBBLURvb3IgKG5ndW9pIGR1bmcgYmFvIGxvaSBuZXQgdmVuIGNoYXkgcXVhIGN1YSAy"
"My8xMC8yMDI2KS4gR29tIGNhYyBuZXQgY2FjaCBuaGF1CiAgICA8PSBnYW4gKG1tKSB0aGFuaCBtb3QgY3VhLiIiIgogICAgaXRlbXMgPSBbXQoKICAgIGRlZiBkaShlcywgZCk6CiAgICAgICAgZm9yIGUgaW4gZXM6CiAgICAgICAgICAgIHQgPSBlLmR4ZnR5cGUo"
"KQogICAgICAgICAgICBpZiB0ID09ICJJTlNFUlQiOiAgICAgICAgICAgIyBJTlNFUlQgdHJlbiBsYXllciBjdWEgZGEgdGluaCBvIHRwcC5fbmhvbV9jdWEKICAgICAgICAgICAgICAgIGlmIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgaW4gd2FudCBvciBkID49IDMg"
"b3IgKAogICAgICAgICAgICAgICAgICAgICAgICB0cHAuX0JPX1FVQVswXSBpcyBub3QgTm9uZSBhbmQgdHBwLl9CT19RVUFbMF0uc2VhcmNoKGUuZHhmLm5hbWUgb3IgIiIpKToKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgdHJ5"
"OgogICAgICAgICAgICAgICAgICAgIGRpKGxpc3QoZS52aXJ0dWFsX2VudGl0aWVzKCkpLCBkICsgMSkKICAgICAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICAgICAgcGFzcwogICAgICAgICAgICBlbGlmIHQgaW4gKCJMSU5FIiwg"
"IkxXUE9MWUxJTkUiLCAiQVJDIikgYW5kIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgaW4gd2FudDoKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICBiID0gZXpiYm94LmV4dGVudHMoW2VdLCBmYXN0PVRydWUpCiAgICAgICAgICAgICAgICBl"
"eGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICBpZiBiLmhhc19kYXRhOgogICAgICAgICAgICAgICAgICAgIGl0ZW1zLmFwcGVuZCgoZSwgYm94KGIuZXh0bWluLngsIGIuZXh0bWluLnksIGIuZXh0bWF4"
"LngsIGIuZXh0bWF4LnkpLmJ1ZmZlcihnYW4gLyAyKSkpCgogICAgZGkoZW50cywgMCkKICAgIGlmIG5vdCBpdGVtczoKICAgICAgICByZXR1cm4gW10KICAgIGNheSA9IHNoYXBlbHkuU1RSdHJlZShbZyBmb3IgXywgZyBpbiBpdGVtc10pCiAgICBjaGEgPSBsaXN0"
"KHJhbmdlKGxlbihpdGVtcykpKQoKICAgIGRlZiBnb2MoaSk6CiAgICAgICAgd2hpbGUgY2hhW2ldICE9IGk6CiAgICAgICAgICAgIGNoYVtpXSA9IGNoYVtjaGFbaV1dCiAgICAgICAgICAgIGkgPSBjaGFbaV0KICAgICAgICByZXR1cm4gaQogICAgZm9yIGksIChf"
"LCBnKSBpbiBlbnVtZXJhdGUoaXRlbXMpOgogICAgICAgIGZvciBqIGluIGNheS5xdWVyeShnLCBwcmVkaWNhdGU9ImludGVyc2VjdHMiKToKICAgICAgICAgICAgYSwgYiA9IGdvYyhpKSwgZ29jKGludChqKSkKICAgICAgICAgICAgaWYgYSAhPSBiOgogICAgICAg"
"ICAgICAgICAgY2hhW2FdID0gYgogICAgbmhvbSA9IGRlZmF1bHRkaWN0KGxpc3QpCiAgICBmb3IgaSwgKGUsIF8pIGluIGVudW1lcmF0ZShpdGVtcyk6CiAgICAgICAgbmhvbVtnb2MoaSldLmFwcGVuZChlKQogICAgcmV0dXJuIGxpc3QobmhvbS52YWx1ZXMoKSkK"
"CgpkZWYgZG9jX2N1YShlbnRzLCBjaGFpbnMpOgogICAgIiIiTW9pIGN1YSAoSU5TRVJUIHRyZW4gbGF5ZXIgY3VhKSAtPiBkaWN0KGRvYW4sIGNvX2N1bmcsIGxvYWkpLiBsb2FpOiAnY3VhX2RpJyAoY28gY3VuZyBxdWF5LCBob2FjIGNoaSBnb20gcG9seWxpbmUK"
"ICAgIG5odSBjdWEgdHJ1b3QpIC8gJ2N1YV9zbycgKGNvID49IDMgTElORSBraW5oLCBraG9uZyBjdW5nIHF1YXkpLiIiIgogICAgd2FudCA9IHtsYXllcl9nb2MoeCkgZm9yIHggaW4gTEFZRVJfQ1VBfQogICAgb3V0ID0gW10KICAgIGZvciBmbGF0IGluIGxpc3Qo"
"dHBwLl9uaG9tX2N1YShlbnRzLCB3YW50KSkgKyBjdWFfbmV0X3JvaShlbnRzLCB3YW50KToKICAgICAgICBkb2FuLCBuX2FyYyA9IHRwcC5fZG9hbl9jdWEoZmxhdCkKICAgICAgICBpZiBub3QgZG9hbjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBuX2xp"
"bmUgPSBzdW0oMSBmb3IgcyBpbiBmbGF0IGlmIHMuZHhmdHlwZSgpID09ICJMSU5FIikKICAgICAgICBsb2FpID0gImN1YV9kaSIgaWYgKG5fYXJjID4gMCBvciBuX2xpbmUgPCAzKSBlbHNlICJjdWFfc28iCiAgICAgICAgYyA9IGRpY3QoZG9hbj1kb2FuLCBsb2Fp"
"PWxvYWksIHRydW90PShsb2FpID09ICJjdWFfZGkiIGFuZCBuX2FyYyA9PSAwKSkKICAgICAgICBtbyA9IGR1b25nX21vX2N1YShmbGF0LCBkb2FuKQogICAgICAgIGlmIG1vOgogICAgICAgICAgICBjWyJtbyJdID0gbW8KICAgICAgICBvdXQuYXBwZW5kKGMpCiAg"
"ICByZXR1cm4gb3V0CgoKZGVmIGR1b25nX21vX2N1YShmbGF0LCBkb2FuKToKICAgICIiIkR1b25nIG1vIGN1YSAobmFtIHRyb25nIHR1b25nKTogYmFuIGxlIC0+IG1lcCBjYW5oIGtoaSBkb25nLCB0dSBjdW5nIHF1YXkgbG9uIG5oYXQuIEJhbiBraW5oIG5hbyBj"
"byBjYW5oIGN1YQogICAgKGRvYW4gc29uZyBzb25nLCBzYXQgYmFuIGtpbmgpIGxhIGNhbmggZGFuZyBtbzsgYmFuIGtpbmggY29uIGxhaSBsYSBkdW9uZyBtby4gRHVuZyBkZSBjaGkgY2F0IG5ldCB2ZW4gbyBwaG9uZyBjbwogICAgY2FuaCBzb25nIHNvbmcgZHVv"
"bmcgbW86IGNhbmggY3VhIHBob25nIGJlbiBjYW5oIHZlIG8gdHUgdGhlIG1vIG5hbSBzYXQgdHVvbmcgV0Mga2hvbmcgY2F0IG5oYW0gKENUMiwgMjMvMTAvMjAyNikuIiIiCiAgICBhcmNzID0gW3MgZm9yIHMgaW4gZmxhdCBpZiBzLmR4ZnR5cGUoKSA9PSAiQVJD"
"IiBhbmQgMzAwIDw9IHMuZHhmLnJhZGl1cyA8PSAxNTAwXQogICAgaWYgbm90IGFyY3M6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIGEgPSBtYXgoYXJjcywga2V5PWxhbWJkYSBzOiBzLmR4Zi5yYWRpdXMpCiAgICB0cnk6CiAgICAgICAgYyA9IGEub2NzKCkudG9f"
"d2NzKGEuZHhmLmNlbnRlcikKICAgICAgICBwMSwgcDIgPSBhLnN0YXJ0X3BvaW50LCBhLmVuZF9wb2ludAogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gTm9uZQogICAgYywgciA9IChjLngsIGMueSksIGEuZHhmLnJhZGl1cwoKICAgIGRlZiBk"
"b19jYW5oKHApOiAgICAgICAgICAgICAgICAgIyB0b25nIGNoaWV1IGRhaSBkb2FuIGN1YSBzb25nIHNvbmcgdmEgc2F0IGJhbiBraW5oIGMgLT4gcAogICAgICAgIHV4LCB1eSA9IChwWzBdIC0gY1swXSkgLyByLCAocFsxXSAtIGNbMV0pIC8gcgogICAgICAgIHRv"
"bmcgPSAwLjAKICAgICAgICBmb3IgcywgZSBpbiBkb2FuOgogICAgICAgICAgICBMID0gbWF0aC5kaXN0KHMsIGUpCiAgICAgICAgICAgIGlmIEwgPCAxOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgaWYgYWJzKCgoZVswXSAtIHNbMF0pICog"
"dXggKyAoZVsxXSAtIHNbMV0pICogdXkpIC8gTCkgPCAwLjk1OgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgbmdhbmcgPSBtYXgoYWJzKChxWzBdIC0gY1swXSkgKiAtdXkgKyAocVsxXSAtIGNbMV0pICogdXgpIGZvciBxIGluIChzLCBlKSkK"
"ICAgICAgICAgICAgaWYgbmdhbmcgPD0gMTIwOgogICAgICAgICAgICAgICAgdG9uZyArPSBMCiAgICAgICAgcmV0dXJuIHRvbmcKICAgIHAxLCBwMiA9IChwMS54LCBwMS55KSwgKHAyLngsIHAyLnkpCiAgICBtbyA9IHAyIGlmIGRvX2NhbmgocDEpID49IGRvX2Nh"
"bmgocDIpIGVsc2UgcDEKICAgIHJldHVybiAoYywgbW8pCgoKZGVmIGRvY190dW9uZ19ubyhlbnRzLCBtYXhfZGVwdGg9NCk6CiAgICAiIiJOZXQgY3VhIHR1b25nIEFDQSBkYSBubyBuaHVuZyBuYW0gdHJlbiBsYXllciAwIChibG9jayBhbiBkYW5oICcqVS4uJyBj"
"aGkgZ29tIExJTkUvTFdQT0xZTElORSArIEhBVENILCBjYW5oIG5nYW4KICAgIDw9IDQ1MCBtbSkuIFRhbmcgNCBUaGFwIEI6IG5oaWV1IGNhbiBjbyB0dW9uZyBraWV1IG5heSwga2hvbmcgY28gbmV0IEEtV2FsbCBuYW8uIiIiCiAgICBjaGFpbnMgPSBbXQoKICAg"
"IGRlZiBkaShlbnRpdGllcywgZGVwdGgpOgogICAgICAgIGZvciBlIGluIGVudGl0aWVzOgogICAgICAgICAgICBpZiBlLmR4ZnR5cGUoKSAhPSAiSU5TRVJUIjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAg"
"IHN1YnMgPSBsaXN0KGUudmlydHVhbF9lbnRpdGllcygpKQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAga2lldSA9IHtzLmR4ZnR5cGUoKSBmb3IgcyBpbiBzdWJzfQogICAgICAgICAgICBp"
"ZiBlLmR4Zi5uYW1lLnN0YXJ0c3dpdGgoIioiKSBhbmQgIkhBVENIIiBpbiBraWV1IGFuZCBraWV1IDw9IHsiTElORSIsICJMV1BPTFlMSU5FIiwgIkhBVENIIn06CiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgYiA9IGV6YmJveC5leHRl"
"bnRzKFtlXSwgZmFzdD1UcnVlKQogICAgICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgaWYgYi5oYXNfZGF0YSBhbmQgbWluKGIuc2l6ZS54LCBiLnNpemUueSkgPD0gNDUwOgog"
"ICAgICAgICAgICAgICAgICAgIGZvciBzIGluIHN1YnM6CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIHMuZHhmdHlwZSgpID09ICJMSU5FIjoKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNoYWlucy5hcHBlbmQoKEZhbHNlLCBbKHMuZHhmLnN0YXJ0Lngs"
"IHMuZHhmLnN0YXJ0LnkpLCAocy5keGYuZW5kLngsIHMuZHhmLmVuZC55KV0pKQogICAgICAgICAgICAgICAgICAgICAgICBlbGlmIHMuZHhmdHlwZSgpID09ICJMV1BPTFlMSU5FIjoKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHB0cyA9IFsodlswXSwgdlsx"
"XSkgZm9yIHYgaW4gcy5nZXRfcG9pbnRzKCldCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiBsZW4ocHRzKSA+PSAyOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNoYWlucy5hcHBlbmQoKGJvb2wocy5jbG9zZWQpLCBwdHMpKQogICAgICAg"
"ICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGRlcHRoIDwgbWF4X2RlcHRoOgogICAgICAgICAgICAgICAgZGkoc3VicywgZGVwdGggKyAxKQoKICAgIGRpKGVudHMsIDApCiAgICByZXR1cm4gY2hhaW5zCgoKZGVmIGRvY19tYXRfbmdvYWkoZW50"
"cywgZG1pbj0zMDAuMCk6CiAgICAiIiJOZXQgTElORSAvIExXUE9MWUxJTkUgbyBjYXAgTW9kZWwgdHJlbiBsYXllciAwIC8gQS1saW5lKiAobWVwIHNhbiwgbWF0IG5nb2FpIGxhbiBjYW4pIGRhaSA+PSBkbWluLiBDaGkgZHVuZyBkZQogICAga2hlcCBsYWkgbG8g"
"Z2lhIG1hIHRoaWV0IGJpIGtob25nIG5hbSB0cm9uZyBvIGtpbiBuYW8gKHZkLiBsbyBnaWEgQ0gyNyB0YW5nIDQgVGhhcCBCOiBtYXQgbmdvYWkgY2hpIGNvIGxhbiBjYW4KICAgIGRhaSAxMDM5IHZhIDIgTElORSBsYXllciAwKS4iIiIKICAgIHJ4ID0gcmUuY29t"
"cGlsZShMQVlFUl9NQVRfTkdPQUkpCiAgICBvdXQgPSBbXQogICAgZm9yIGUgaW4gZW50czoKICAgICAgICB0ID0gZS5keGZ0eXBlKCkKICAgICAgICBpZiB0IG5vdCBpbiAoIkxJTkUiLCAiTFdQT0xZTElORSIpIG9yIG5vdCByeC5tYXRjaChsYXllcl9nb2MoZS5k"
"eGYubGF5ZXIpKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiB0ID09ICJMSU5FIjoKICAgICAgICAgICAgcHRzID0gWyhlLmR4Zi5zdGFydC54LCBlLmR4Zi5zdGFydC55KSwgKGUuZHhmLmVuZC54LCBlLmR4Zi5lbmQueSldCiAgICAgICAgICAgIGNs"
"b3NlZCA9IEZhbHNlCiAgICAgICAgZWxzZToKICAgICAgICAgICAgcHRzID0gWyh2WzBdLCB2WzFdKSBmb3IgdiBpbiBlLmdldF9wb2ludHMoKV0KICAgICAgICAgICAgY2xvc2VkID0gYm9vbChlLmNsb3NlZCkKICAgICAgICBpZiBsZW4ocHRzKSA+PSAyIGFuZCBM"
"aW5lU3RyaW5nKHB0cykubGVuZ3RoID49IGRtaW46CiAgICAgICAgICAgIG91dC5hcHBlbmQoKGNsb3NlZCwgcHRzKSkKICAgIHJldHVybiBvdXQKCgpkZWYga2hlcF9sYWkoZGllbSwgY2hhaW5zLCBraHVuZywgbWF0X25nb2FpLCBnYXBfbWF4LCByPTYwMDAuMCk6"
"CiAgICAiIiJEdW5nIGxhaSBsdW9pIG5ldCBxdWFuaCBjYWMgZGllbSAodGhlbSBuZXQgbWF0IG5nb2FpKSwgdHJhIHZlIChvIGtpbiBuaG8gbmhhdCAxLTIwIG0yIGNodWEgbW90IGRpZW0sIGNhYyBkb2FuCiAgICBkb25nIG8gbW8pIGhvYWMgKE5vbmUsIFtdKS4i"
"IiIKICAgIHZ1bmcgPSB1bmFyeV91bmlvbihbUG9pbnQocCkuYnVmZmVyKHIpIGZvciBwIGluIGRpZW1dKQoKICAgIGRlZiBnYW4oYyk6CiAgICAgICAgcmV0dXJuIExpbmVTdHJpbmcoY1sxXSBpZiBsZW4oY1sxXSkgPiAxIGVsc2UgY1sxXSAqIDIpLmludGVyc2Vj"
"dHModnVuZykKCiAgICBjaCA9IFtjIGZvciBjIGluIGNoYWlucyBpZiBnYW4oYyldICsgW2MgZm9yIGMgaW4gbWF0X25nb2FpIGlmIGdhbihjKV0KICAgIGtoID0gW2sgZm9yIGsgaW4ga2h1bmcgaWYgay5pbnRlcnNlY3RzKHZ1bmcpXQogICAgZnMsIF8sIGJyID0g"
"dHBwLmJ1aWxkX2ZhY2VzKGNoLCBnYXBfbWF4LCBraCArIG5vaV9kYWlfZGF1X2hvKGNoKSkKICAgIGJlc3QgPSBOb25lCiAgICBmb3IgZiBpbiBmczoKICAgICAgICBpZiBub3QgKDEuMGU2IDw9IGYuYXJlYSA8PSAyMC4wZTYpOgogICAgICAgICAgICBjb250aW51"
"ZQogICAgICAgIGlmIGFueShmLmNvbnRhaW5zKFBvaW50KHApKSBmb3IgcCBpbiBkaWVtKSBhbmQgKGJlc3QgaXMgTm9uZSBvciBmLmFyZWEgPCBiZXN0LmFyZWEpOgogICAgICAgICAgICBiZXN0ID0gZgogICAgcmV0dXJuIGJlc3QsIGJyCgoKZGVmIGRvY19jdWFf"
"dGhhbmcoZW50cyk6CiAgICAiIiJPIGN1YSB0aGFuZyBtYXk6IHBvbHlsaW5lIGtpbiBvIGNhcCBNb2RlbCB0cmVuIGxheWVyIHR1b25nIChBLVdhbGwpLCBjYW5oIG5nYW4gPD0gMzAwLCBraG9uZyBoYXRjaCwgbmFtIGNhbmgKICAgIHRleHQgdGFpIHRyb25nIHRo"
"YW5nICczMDBLRycgKDw9IDIsNSBtKS4gVGFuZyA0IFRoYXAgQjogY3VhIHRoYW5nIG1heSByYWMgZ2l1YSBwaG9uZyByYWMgdmEgdGhhbmcgbWF5IGxhCiAgICBwb2x5bGluZSAxNTAgeCAxMDAwIHRyZW4gQS1XYWxsIChuZ3VvaSBkdW5nIHhhYyBuaGFuIDIzLzEw"
"LzIwMjYgbGEgY3VhIC0+IG5nYXQgbmV0IHZlbikuCiAgICBUcmEgdmUgKGNhYyBvIGN1YSwgY2FjIGRpZW0gdGV4dCB0YWkgdHJvbmcpLiIiIgogICAgcnhfa2cgPSByZS5jb21waWxlKHIiXlxzKlxkK1xzKmtnXHMqJCIpCiAgICBrZyA9IFtdCiAgICBmb3IgZSBp"
"biBkdXlldF90ZXh0KGVudHMpOgogICAgICAgIHMgPSBib19kYXUoZS5wbGFpbl90ZXh0KCkgaWYgZS5keGZ0eXBlKCkgPT0gIk1URVhUIiBlbHNlIGUuZHhmLnRleHQpCiAgICAgICAgaWYgcnhfa2cubWF0Y2gocyk6CiAgICAgICAgICAgIHAsIF8gPSB0YW1fYmJv"
"eChlKQogICAgICAgICAgICBrZy5hcHBlbmQoUG9pbnQocCkpCiAgICBpZiBub3Qga2c6CiAgICAgICAgcmV0dXJuIFtdLCBbXQogICAgb3V0ID0gW10KICAgIGZvciBlIGluIGVudHM6CiAgICAgICAgaWYgZS5keGZ0eXBlKCkgIT0gIkxXUE9MWUxJTkUiIG9yIG5v"
"dCBlLmNsb3NlZCBvciBsYXllcl9nb2MoZS5keGYubGF5ZXIpICE9ICJhLXdhbGwiOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHB0cyA9IFsodlswXSwgdlsxXSkgZm9yIHYgaW4gZS5nZXRfcG9pbnRzKCldCiAgICAgICAgaWYgbGVuKHB0cykgPCAzOgog"
"ICAgICAgICAgICBjb250aW51ZQogICAgICAgIGcgPSBQb2x5Z29uKHB0cykKICAgICAgICB4MCwgeTAsIHgxLCB5MSA9IGcuYm91bmRzCiAgICAgICAgaWYgbWluKHgxIC0geDAsIHkxIC0geTApID4gMzAwIG9yIG1heCh4MSAtIHgwLCB5MSAtIHkwKSA8IDYwMDoK"
"ICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBhbnkoZy5kaXN0YW5jZShrKSA8PSAyNTAwIGZvciBrIGluIGtnKToKICAgICAgICAgICAgb3V0LmFwcGVuZChnKQogICAgcmV0dXJuIG91dCwga2cKCgpkZWYgZG9jX2dpZW5nX3RoYW5nKGVudHMpOgogICAg"
"IiIiR2llbmcgdGhhbmcgbWF5OiBwb2x5bGluZSBraW4gNCBkaW5oICgwLDgtMTIgbTIpLCBiZW4gdHJvbmcgY28gMiBkdW9uZyBjaGVvIG5vaSBjYWMgZ29jIGRvaSBkaWVuIChkYXUgWCksIG1vaQogICAgbGF5ZXIga2UgY2EgbmV0IGtodWF0LiBDVDEgdGFuZyA1"
"QS0xMDogZ2llbmcgdGhhbmcgbWF5IHJhYyBjaGkgY28gdmllbiArIGRhdSBYIHRyZW4gJy4uLkxvaSBUREgkMCRBLUhpZGRlbicsCiAgICBraG9uZyBjbyBuZXQgdHVvbmcgbmdhbiB2b2kgcGhvbmcgcmFjLiIiIgogICAgaGNuLCBjaGVvID0gW10sIFtdCiAgICBm"
"b3IgZSBpbiB0cHAud2FsayhlbnRzLCBtYXhfZGVwdGg9NCk6CiAgICAgICAgdCA9IGUuZHhmdHlwZSgpCiAgICAgICAgaWYgdCA9PSAiTElORSI6CiAgICAgICAgICAgIGNoZW8uYXBwZW5kKCgoZS5keGYuc3RhcnQueCwgZS5keGYuc3RhcnQueSksIChlLmR4Zi5l"
"bmQueCwgZS5keGYuZW5kLnkpKSkKICAgICAgICBlbGlmIHQgPT0gIkxXUE9MWUxJTkUiOgogICAgICAgICAgICBwdHMgPSBbKHZbMF0sIHZbMV0pIGZvciB2IGluIGUuZ2V0X3BvaW50cygpXQogICAgICAgICAgICBpZiBsZW4ocHRzKSA9PSAyOgogICAgICAgICAg"
"ICAgICAgY2hlby5hcHBlbmQoKHB0c1swXSwgcHRzWzFdKSkKICAgICAgICAgICAgZWxpZiBlLmNsb3NlZCBhbmQgbGVuKHB0cykgaW4gKDQsIDUpOgogICAgICAgICAgICAgICAgZyA9IFBvbHlnb24ocHRzWzo0XSkKICAgICAgICAgICAgICAgIGlmIGcuaXNfdmFs"
"aWQgYW5kIDAuOGU2IDw9IGcuYXJlYSA8PSAxMmU2IGFuZCBhYnMoZy5hcmVhIC0gZy5taW5pbXVtX3JvdGF0ZWRfcmVjdGFuZ2xlLmFyZWEpIDwgMC4wMiAqIGcuYXJlYToKICAgICAgICAgICAgICAgICAgICBoY24uYXBwZW5kKGcpCiAgICBpZiBub3QgaGNuIG9y"
"IG5vdCBjaGVvOgogICAgICAgIHJldHVybiBbXQogICAgY2F5ID0gc2hhcGVseS5TVFJ0cmVlKFtMaW5lU3RyaW5nKHMpIGZvciBzIGluIGNoZW9dKQogICAgb3V0ID0gW10KICAgIGZvciBnIGluIGhjbjoKICAgICAgICBnb2MgPSBsaXN0KGcuZXh0ZXJpb3IuY29v"
"cmRzKVs6NF0KICAgICAgICBjYXAgPSBbKGdvY1swXSwgZ29jWzJdKSwgKGdvY1sxXSwgZ29jWzNdKV0KICAgICAgICBuID0gMAogICAgICAgIGZvciBhLCBiIGluIGNhcDoKICAgICAgICAgICAgZm9yIGsgaW4gY2F5LnF1ZXJ5KExpbmVTdHJpbmcoW2EsIGJdKS5i"
"dWZmZXIoMTAwKSk6CiAgICAgICAgICAgICAgICBwLCBxID0gY2hlb1tpbnQoayldCiAgICAgICAgICAgICAgICBpZiAobWF0aC5kaXN0KHAsIGEpIDwgMTUwIGFuZCBtYXRoLmRpc3QocSwgYikgPCAxNTApIG9yIChtYXRoLmRpc3QocCwgYikgPCAxNTAgYW5kIG1h"
"dGguZGlzdChxLCBhKSA8IDE1MCk6CiAgICAgICAgICAgICAgICAgICAgbiArPSAxCiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICBpZiBuID09IDIgYW5kIG5vdCBhbnkoby5idWZmZXIoNSkuY29udGFpbnMoZykgZm9yIG8gaW4gb3V0KToKICAgICAg"
"ICAgICAgb3V0LmFwcGVuZChnKQogICAgcmV0dXJuIG91dAoKCmRlZiBjdWFfcXVhbmgoZmFjZSwgY3VhcywgZD0yNTAuMCk6CiAgICAiIiJDaGkgc28gY2FjIGN1YSBkaSBuYW0gc2F0IGJpZW4gbyAoa2h1bmcgY3VhIGNhY2ggYmllbiA8PSBkKS4iIiIKICAgIGV4"
"dCA9IFBvbHlnb24oZmFjZS5leHRlcmlvcikuZXh0ZXJpb3IKICAgIG91dCA9IFtdCiAgICBmb3IgaSwgYyBpbiBlbnVtZXJhdGUoY3Vhcyk6CiAgICAgICAgaWYgY1sibG9haSJdICE9ICJjdWFfZGkiOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHB0cyA9"
"IGxpc3QoY1sibW8iXSkgaWYgYy5nZXQoIm1vIikgZWxzZSBbcCBmb3IgcyBpbiBjWyJkb2FuIl0gZm9yIHAgaW4gc10KICAgICAgICBnID0gTGluZVN0cmluZyhwdHMpIGlmIGxlbihwdHMpID4gMSBlbHNlIFBvaW50KHB0c1swXSkKICAgICAgICBpZiBnLmRpc3Rh"
"bmNlKGV4dCkgPD0gZDoKICAgICAgICAgICAgb3V0LmFwcGVuZChpKQogICAgcmV0dXJuIG91dAoKCmRlZiBkb2Nfbm9pX3RoYXQoZW50cyk6CiAgICAiIiJUYW0gY2FjIGJsb2NrIG5vaSB0aGF0IChnaXVvbmcsIHR1LCBzb2ZhLCBiYW4gLi4uKSAtIG8ga2luIGNv"
"IG5vaSB0aGF0IGtob25nIHBoYWkgbG8gZ2lhLiIiIgogICAgcnhfYm8gPSByZS5jb21waWxlKCJ8Ii5qb2luKFtSRV9UQl9XQywgUkVfVEJfTEcsIFJFX1RCX0JPLCBSRV9MQU5fQ0FOXSkpCiAgICBwdHMgPSBbXQogICAgZm9yIGUsIG5hbWUsIGxheSBpbiBkdXll"
"dF9pbnNlcnQoZW50cywgbWF4X2RlcHRoPTIpOgogICAgICAgIEwgPSBib19kYXUobGF5ZXJfZ29jKGxheSkpCiAgICAgICAgaWYgbm90IChMLnN0YXJ0c3dpdGgoImEtaW50ZXJpb3IiKSBvciBMLnN0YXJ0c3dpdGgoImEtbm9pIHRoYXQiKSBvciAiZnVybiIgaW4g"
"TCkgb3IgIndjIiBpbiBMOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIHJ4X2JvLnNlYXJjaChib19kYXUobmFtZSkuc3BsaXQoIiQiKVstMV0pOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHAsIHN6ID0gdGFtX2Jib3goZSkKICAgICAgICBp"
"ZiA0MDAgPD0gbWF4KHN6KSA8PSA0MDAwOgogICAgICAgICAgICBwdHMuYXBwZW5kKFBvaW50KHApKQogICAgcmV0dXJuIHB0cwoKCmRlZiBkb2NfbGFuX2NhbihlbnRzKToKICAgICIiIktodW5nIGJhbyBjYWMgYmxvY2sgbGFuIGNhbiAvIGxhbSAoTW9kZWwpOiB0"
"ZW4ga2hvcCBSRV9MQU5fQ0FOLCBob2FjIGJsb2NrIGFuIGRhbmggbW9uZyAoY2FuaCBuZ2FuIDw9IDIwMCwKICAgIGRhaSA+PSA4MDApIGNodWEgPj0gNSBkb2kgdHVvbmcgdmEgY28gYmxvY2sgY29uIChzb25nIGxhbiBjYW4pIC0gdmQuICcqVTEwOTUnIHRhbmcg"
"NCBUaGFwIEIuIiIiCiAgICByeCA9IHJlLmNvbXBpbGUoUkVfTEFOX0NBTikKICAgIGN1YSA9IHtsYXllcl9nb2MoeCkgZm9yIHggaW4gTEFZRVJfQ1VBfSB8IHtsYXllcl9nb2MoTEFZRVJfV0MpfQogICAgb3V0ID0gW10KICAgIGZvciBlLCBuYW1lLCBsYXkgaW4g"
"ZHV5ZXRfaW5zZXJ0KGVudHMsIG1heF9kZXB0aD0zKToKICAgICAgICB0ZW4gPSBib19kYXUobmFtZSkuc3BsaXQoIiQiKVstMV0KICAgICAgICB0aGVvX3RlbiA9IHJ4LnNlYXJjaCh0ZW4pIG9yIHJ4LnNlYXJjaChib19kYXUobGF5ZXJfZ29jKGxheSkpKQogICAg"
"ICAgIGlmIG5vdCB0aGVvX3RlbiBhbmQgKG5vdCBuYW1lLnN0YXJ0c3dpdGgoIioiKSBvciBsYXllcl9nb2MobGF5KSBpbiBjdWEpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHRyeToKICAgICAgICAgICAgYiA9IGV6YmJveC5leHRlbnRzKFtlXSwgZmFz"
"dD1UcnVlKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgaWYgbm90IGIuaGFzX2RhdGEgb3IgbWF4KGIuc2l6ZS54LCBiLnNpemUueSkgPj0gMjAwMDA6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgIyBj"
"aGkgbGF5IGJsb2NrIG1vbmcgKGNhbmggbmdhbiA8PSAyMDApOiBsYW0gZ29jIGNodSBMIGNvIGtodW5nIGJhbyB0cnVtIHZhbyBsb25nIGxvIGdpYSwgbGFtIGNoaWEgZG9pIHBob25nCiAgICAgICAgaWYgbWluKGIuc2l6ZS54LCBiLnNpemUueSkgPiAyMDAgb3Ig"
"bWF4KGIuc2l6ZS54LCBiLnNpemUueSkgPCA4MDA6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgaWYgbm90IHRoZW9fdGVuOgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBzdWJzID0gbGlzdChlLnZpcnR1YWxfZW50aXRpZXMoKSkKICAgICAg"
"ICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGxlbihzdWJzKSA8IDUgb3Igbm90IGFueShzLmR4ZnR5cGUoKSA9PSAiSU5TRVJUIiBmb3IgcyBpbiBzdWJzKToKICAgICAgICAgICAgICAgIGNvbnRp"
"bnVlCiAgICAgICAgb3V0LmFwcGVuZChib3goYi5leHRtaW4ueCwgYi5leHRtaW4ueSwgYi5leHRtYXgueCwgYi5leHRtYXgueSkpCiAgICByZXR1cm4gb3V0CgoKZGVmIG5vaV9kYWlfZGF1X2hvKGNoYWlucywgZG1heD1OT0lfREFJKToKICAgICIiIkRvYW4gbm9p"
"IGRhaSBkYXUgbXV0IG5ldCBobyB0aGVvIGh1b25nIGN1YSBubyB0b2kgbmV0IGdhbiBuaGF0ICg8PSBkbWF4KS4gVHJhIHZlIGxpc3QgTGluZVN0cmluZy4iIiIKICAgIHNlZ3MgPSBbXQogICAgZm9yIGNsb3NlZCwgcHRzIGluIGNoYWluczoKICAgICAgICBxID0g"
"cHRzICsgKFtwdHNbMF1dIGlmIGNsb3NlZCBlbHNlIFtdKQogICAgICAgIHNlZ3MgKz0gW0xpbmVTdHJpbmcoW3FbaV0sIHFbaSArIDFdXSkgZm9yIGkgaW4gcmFuZ2UobGVuKHEpIC0gMSkgaWYgbWF0aC5kaXN0KHFbaV0sIHFbaSArIDFdKSA+IDAuNV0KICAgIGlm"
"IG5vdCBzZWdzOgogICAgICAgIHJldHVybiBbXQogICAgY2F5ID0gc2hhcGVseS5TVFJ0cmVlKHNlZ3MpCiAgICBvdXQgPSBbXQogICAgZm9yIGNsb3NlZCwgcHRzIGluIGNoYWluczoKICAgICAgICBpZiBjbG9zZWQgb3IgbGVuKHB0cykgPCAyOgogICAgICAgICAg"
"ICBjb250aW51ZQogICAgICAgIGZvciBwLCBxIGluICgocHRzWzBdLCBwdHNbMV0pLCAocHRzWy0xXSwgcHRzWy0yXSkpOgogICAgICAgICAgICBMID0gbWF0aC5kaXN0KHAsIHEpCiAgICAgICAgICAgIGlmIEwgPCAxOgogICAgICAgICAgICAgICAgY29udGludWUK"
"ICAgICAgICAgICAgdXgsIHV5ID0gKHBbMF0gLSBxWzBdKSAvIEwsIChwWzFdIC0gcVsxXSkgLyBMCiAgICAgICAgICAgIHRpYSA9IExpbmVTdHJpbmcoWyhwWzBdICsgdXggKiAwLjUsIHBbMV0gKyB1eSAqIDAuNSksIChwWzBdICsgdXggKiBkbWF4LCBwWzFdICsg"
"dXkgKiBkbWF4KV0pCiAgICAgICAgICAgIGJlc3QgPSBOb25lCiAgICAgICAgICAgIGZvciBrIGluIGNheS5xdWVyeSh0aWEsIHByZWRpY2F0ZT0iaW50ZXJzZWN0cyIpOgogICAgICAgICAgICAgICAgeCA9IHRpYS5pbnRlcnNlY3Rpb24oc2Vnc1tpbnQoayldKQog"
"ICAgICAgICAgICAgICAgaWYgeC5pc19lbXB0eToKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgZCA9IFBvaW50KHApLmRpc3RhbmNlKHgpCiAgICAgICAgICAgICAgICBpZiAxLjAgPCBkIDw9IGRtYXggYW5kIChiZXN0IGlzIE5v"
"bmUgb3IgZCA8IGJlc3QpOgogICAgICAgICAgICAgICAgICAgIGJlc3QgPSBkCiAgICAgICAgICAgIGlmIGJlc3Q6CiAgICAgICAgICAgICAgICBvdXQuYXBwZW5kKExpbmVTdHJpbmcoW3AsIChwWzBdICsgdXggKiBiZXN0LCBwWzFdICsgdXkgKiBiZXN0KV0pKQog"
"ICAgcmV0dXJuIG91dAoKCmRlZiBnaWFwX25nb2FpX25oYShwb2x5LCBmYWNlc190cmVlLCBmYWNlcywgY2F5X25ldCwgbmV0LCBkbWluPTgwMC4wLCB4YT0zMDAwLjApOgogICAgIiIiQ28gY2FuaCBkYWkgPj0gZG1pbiBtYSBwaGlhIG5nb2FpICgzMDAgdmEgNjAw"
"IG1tKSBraG9uZyB0aHVvYyBvIGtpbiBuYW8gdmEgS0hPTkcgZ2FwIHR1b25nIHRyb25nIDcwMCAtIHhhIG1tCiAgICAtPiBnaWFwIG5nb2FpIG5oYS4gR2llbmcgdGhhbmcgbWF5IGtob25nIHBoYWkgbyBraW4gbmh1bmcgY28gdHVvbmcgcGhpYSBzYXU6IHNhbmgg"
"dGhhbmcgdHVuZyBiaSBjb2kgbGEgZ2lhcCBuZ29haQogICAgbmhhIHJvaSBuaGFuIHRoYW5oIGxvIGdpYSB2aSBjdWEgdGhhbmcgbWF5IGdpb25nIGN1YSB0cnVvdCAodGFuZyA0IFRoYXAgQiwgMzAvMTAvMjAyNikuIiIiCiAgICBwdHMgPSBsaXN0KHNoYXBlbHku"
"Z2VvbWV0cnkucG9seWdvbi5vcmllbnQocG9seSwgMS4wKS5leHRlcmlvci5jb29yZHMpCiAgICBmb3IgYSwgYiBpbiB6aXAocHRzLCBwdHNbMTpdKToKICAgICAgICBMID0gbWF0aC5kaXN0KGEsIGIpCiAgICAgICAgaWYgTCA8IGRtaW46CiAgICAgICAgICAgIGNv"
"bnRpbnVlCiAgICAgICAgdXgsIHV5ID0gKGJbMF0gLSBhWzBdKSAvIEwsIChiWzFdIC0gYVsxXSkgLyBMCiAgICAgICAgbngsIG55ID0gdXksIC11eAogICAgICAgIG5nb2FpID0gVHJ1ZQogICAgICAgIGZvciB0IGluICgwLjI1LCAwLjUsIDAuNzUpOgogICAgICAg"
"ICAgICBmb3IgZCBpbiAoMzAwLjAsIDYwMC4wKToKICAgICAgICAgICAgICAgIFAgPSBQb2ludChhWzBdICsgdXggKiBMICogdCArIG54ICogZCwgYVsxXSArIHV5ICogTCAqIHQgKyBueSAqIGQpCiAgICAgICAgICAgICAgICBpZiBhbnkoZmFjZXNbaW50KGspXS5j"
"b250YWlucyhQKSBmb3IgayBpbiBmYWNlc190cmVlLnF1ZXJ5KFApKToKICAgICAgICAgICAgICAgICAgICBuZ29haSA9IEZhbHNlCiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgaWYgbm90IG5nb2FpOgogICAgICAgICAgICAgICAgYnJlYWsK"
"ICAgICAgICBpZiBuZ29haToKICAgICAgICAgICAgY2hhbiA9IDAKICAgICAgICAgICAgZm9yIHQgaW4gKDAuMjUsIDAuNSwgMC43NSk6CiAgICAgICAgICAgICAgICB4LCB5ID0gYVswXSArIHV4ICogTCAqIHQsIGFbMV0gKyB1eSAqIEwgKiB0CiAgICAgICAgICAg"
"ICAgICB0aWEgPSBMaW5lU3RyaW5nKFsoeCArIG54ICogNzAwLCB5ICsgbnkgKiA3MDApLCAoeCArIG54ICogeGEsIHkgKyBueSAqIHhhKV0pCiAgICAgICAgICAgICAgICBjaGFuICs9IGFueShuZXRbaW50KGspXS5pbnRlcnNlY3RzKHRpYSkgZm9yIGsgaW4gY2F5"
"X25ldC5xdWVyeSh0aWEpKQogICAgICAgICAgICBpZiBjaGFuIDwgMjoKICAgICAgICAgICAgICAgIHJldHVybiBUcnVlCiAgICByZXR1cm4gRmFsc2UKCgpkZWYgcGh1X3R1b25nKGJyLCBjYXlfbmV0LCBuZXQsIHRvbD0xMC4wKToKICAgICIiIlR5IGxlIGNoaWV1"
"IGRhaSBkb2FuIGRvbmcgbyBtbyBkYSBjbyBuZXQgdHVvbmcgVEhBVCBzb25nIHNvbmcsIHRydW5nIHZpIHRyaSAoPD0gdG9sKSBwaHUuCiAgICBidWlsZF9mYWNlcyBjbyB0aGUgc2luaCBkb2FuIGRvbmcgbmFtIGRlIGxlbiB0dW9uZyB0aGF0ICgyIGRhdSB0dW9u"
"ZyBjdW5nIG5hbSB0cmVuIDEgbmV0IGRhaSk6IGRvIGtob25nIHBoYWkgbyBtby4iIiIKICAgIEwgPSBici5sZW5ndGgKICAgICh4MCwgeTApLCAoeDEsIHkxKSA9IGJyLmNvb3Jkc1swXSwgYnIuY29vcmRzWy0xXQogICAgdXgsIHV5ID0gKHgxIC0geDApIC8gTCwg"
"KHkxIC0geTApIC8gTAogICAgZGF5ID0gYnIuYnVmZmVyKHRvbCwgY2FwX3N0eWxlPSJmbGF0IikKICAgIGtob2FuZyA9IFtdCiAgICBmb3IgayBpbiBjYXlfbmV0LnF1ZXJ5KGRheSk6CiAgICAgICAgbiA9IG5ldFtpbnQoayldCiAgICAgICAgKGEsIGIpLCAoYywg"
"ZCkgPSBuLmNvb3Jkc1swXSwgbi5jb29yZHNbLTFdCiAgICAgICAgaWYgbi5sZW5ndGggPCAxIG9yIGFicygoYyAtIGEpICogdXggKyAoZCAtIGIpICogdXkpIC8gbi5sZW5ndGggPCAwLjk4NToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBvID0gbi5pbnRl"
"cnNlY3Rpb24oZGF5KQogICAgICAgIGlmIG8uaXNfZW1wdHk6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgdHMgPSBbKHBbMF0gLSB4MCkgKiB1eCArIChwWzFdIC0geTApICogdXkgZm9yIGcgaW4gZ2V0YXR0cihvLCAiZ2VvbXMiLCBbb10pIGZvciBwIGlu"
"IGcuY29vcmRzXQogICAgICAgIGtob2FuZy5hcHBlbmQoKG1heCgwLjAsIG1pbih0cykpLCBtaW4oTCwgbWF4KHRzKSkpKQogICAgdG9uZyA9IGN1b2kgPSAwLjAKICAgIGZvciBhLCBiIGluIHNvcnRlZChraG9hbmcpOgogICAgICAgIGlmIGIgPiBjdW9pOgogICAg"
"ICAgICAgICB0b25nICs9IGIgLSBtYXgoYSwgY3VvaSkKICAgICAgICAgICAgY3VvaSA9IGIKICAgIHJldHVybiB0b25nIC8gTAoKCmRlZiBoYXRjaF9kYV9jbyhtc3ApOgogICAgIiIiUG9seWdvbiBjYWMgaGF0Y2ggY2hvbmcgdGhhbSBkYSBjbzogSEFUQ0ggX1VT"
"RVIgdHJlbiBBLU1hdGVyaWFsIG8gTW9kZWwgaG9hYyB0cm9uZyBibG9jayBDSE9ORyBUSEFNKi4iIiIKICAgIHBvbHlzID0gW10KCiAgICBkZWYgdHVfaGF0Y2goaCk6CiAgICAgICAgZm9yIHAgaW4gaC5wYXRoczoKICAgICAgICAgICAgdHJ5OgogICAgICAgICAg"
"ICAgICAgaWYgaGFzYXR0cihwLCAidmVydGljZXMiKToKICAgICAgICAgICAgICAgICAgICBwdHMgPSBbKHZbMF0sIHZbMV0pIGZvciB2IGluIHAudmVydGljZXNdCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIHB0cyA9IFsoZWQuc3Rh"
"cnRbMF0sIGVkLnN0YXJ0WzFdKSBmb3IgZWQgaW4gcC5lZGdlcyBpZiBoYXNhdHRyKGVkLCAic3RhcnQiKV0KICAgICAgICAgICAgICAgIGlmIGxlbihwdHMpID49IDM6CiAgICAgICAgICAgICAgICAgICAgcG9seXMuYXBwZW5kKFBvbHlnb24ocHRzKS5idWZmZXIo"
"MCkpCiAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgICAgICBwYXNzCgogICAgZm9yIGUgaW4gbXNwOgogICAgICAgIGlmIGUuZHhmdHlwZSgpID09ICJIQVRDSCIgYW5kIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgPT0gbGF5ZXJfZ29jKExB"
"WUVSX1ZFKSBhbmQgZS5keGYucGF0dGVybl9uYW1lLnVwcGVyKCkgaW4gKCJfVVNFUiIsICJfVSIpOgogICAgICAgICAgICB0dV9oYXRjaChlKQogICAgICAgIGVsaWYgZS5keGZ0eXBlKCkgPT0gIklOU0VSVCIgYW5kIGJvX2RhdShlLmR4Zi5uYW1lKS5zdGFydHN3"
"aXRoKCJjaG9uZyB0aGFtIik6CiAgICAgICAgICAgIGZvciB2IGluIGUudmlydHVhbF9lbnRpdGllcygpOgogICAgICAgICAgICAgICAgaWYgdi5keGZ0eXBlKCkgPT0gIkhBVENIIjoKICAgICAgICAgICAgICAgICAgICB0dV9oYXRjaCh2KQogICAgcmV0dXJuIHVu"
"YXJ5X3VuaW9uKHBvbHlzKSBpZiBwb2x5cyBlbHNlIE5vbmUKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gaGluaCBob2MKZGVmIGRvbl9naWFuKHBvbHkpOgogICAgIiIiQm8gZGluaCB0"
"aGFuZyBoYW5nIC8gdHJ1bmcgbmhhdSwgaHVvbmcgQ0NXLiIiIgogICAgcG9seSA9IHNoYXBlbHkuZ2VvbWV0cnkucG9seWdvbi5vcmllbnQocG9seS5idWZmZXIoMCksIDEuMCkKICAgIHB0cyA9IGxpc3QocG9seS5leHRlcmlvci5jb29yZHMpWzotMV0KICAgIGNo"
"YW5nZWQgPSBUcnVlCiAgICB3aGlsZSBjaGFuZ2VkIGFuZCBsZW4ocHRzKSA+IDM6CiAgICAgICAgY2hhbmdlZCA9IEZhbHNlCiAgICAgICAgZm9yIGkgaW4gcmFuZ2UobGVuKHB0cykpOgogICAgICAgICAgICBhLCBiLCBjID0gcHRzW2kgLSAxXSwgcHRzW2ldLCBw"
"dHNbKGkgKyAxKSAlIGxlbihwdHMpXQogICAgICAgICAgICBjcm9zcyA9IChiWzBdIC0gYVswXSkgKiAoY1sxXSAtIGJbMV0pIC0gKGJbMV0gLSBhWzFdKSAqIChjWzBdIC0gYlswXSkKICAgICAgICAgICAgaWYgbWF0aC5kaXN0KGEsIGIpIDwgMC41IG9yIGFicyhj"
"cm9zcykgLyBtYXgobWF0aC5kaXN0KGEsIGMpLCAxZS05KSA8IDAuNToKICAgICAgICAgICAgICAgIHB0cy5wb3AoaSkKICAgICAgICAgICAgICAgIGNoYW5nZWQgPSBUcnVlCiAgICAgICAgICAgICAgICBicmVhawogICAgcmV0dXJuIFBvbHlnb24ocHRzLCBbbGlz"
"dChyLmNvb3JkcykgZm9yIHIgaW4gcG9seS5pbnRlcmlvcnNdKQoKCmRlZiB2ZV9tYXRfbG9pKHBvbHksIGNheV9uZXQsIG5ldCwgdG1pbj04LjAsIHRtYXg9MjIuMCk6CiAgICAiIiJEYXkgdHVuZyBjYW5oIHJhIG5nb2FpIHRvaSBuZXQgc29uZyBzb25nIGNhY2gg"
"dG1pbi10bWF4IG1tIChtYXQgbG9pIHR1b25nIHBoaWEgc2F1IGxvcCB0cmF0KS4KICAgIFRyYSB2ZSAocG9seWdvbiBtb2ksIHNvIGNhbmggZGEgZGF5KS4iIiIKICAgIHB0cyA9IGxpc3QocG9seS5leHRlcmlvci5jb29yZHMpWzotMV0gICAgICAgICAgIyBDQ1c6"
"IHBoaWEgbmdvYWkgbGEgYmVuIHBoYWkgaHVvbmcgY2FuaAogICAgbiA9IGxlbihwdHMpCiAgICBkaWNoID0gW10KICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgIGEsIGIgPSBwdHNbaV0sIHB0c1soaSArIDEpICUgbl0KICAgICAgICBMID0gbWF0aC5kaXN0"
"KGEsIGIpCiAgICAgICAgdXgsIHV5ID0gKGJbMF0gLSBhWzBdKSAvIEwsIChiWzFdIC0gYVsxXSkgLyBMCiAgICAgICAgbngsIG55ID0gdXksIC11eCAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIHBoYXAgdHV5ZW4gcmEgbmdvYWkKICAgICAgICB2dW5nID0g"
"TGluZVN0cmluZyhbYSwgYl0pLmJ1ZmZlcih0bWF4ICsgMSwgY2FwX3N0eWxlPSJmbGF0IikKICAgICAgICBiZXN0ID0gMC4wCiAgICAgICAgdG90ID0gZGVmYXVsdGRpY3QoZmxvYXQpCiAgICAgICAgZm9yIGsgaW4gY2F5X25ldC5xdWVyeSh2dW5nKToKICAgICAg"
"ICAgICAgcyA9IG5ldFtrXQogICAgICAgICAgICAoeDEsIHkxKSwgKHgyLCB5MikgPSBzLmNvb3Jkc1swXSwgcy5jb29yZHNbLTFdCiAgICAgICAgICAgIGxzID0gbWF0aC5kaXN0KCh4MSwgeTEpLCAoeDIsIHkyKSkKICAgICAgICAgICAgaWYgbHMgPCAxIG9yIGFi"
"cygoeDIgLSB4MSkgKiB1eSAtICh5MiAtIHkxKSAqIHV4KSAvIGxzID4gMC4wMjogICAjIGtob25nIHNvbmcgc29uZwogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgZCA9ICh4MSAtIGFbMF0pICogbnggKyAoeTEgLSBhWzFdKSAqIG55CiAgICAg"
"ICAgICAgIGlmIG5vdCAodG1pbiA8PSBkIDw9IHRtYXgpOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgdDEgPSAoeDEgLSBhWzBdKSAqIHV4ICsgKHkxIC0gYVsxXSkgKiB1eQogICAgICAgICAgICB0MiA9ICh4MiAtIGFbMF0pICogdXggKyAo"
"eTIgLSBhWzFdKSAqIHV5CiAgICAgICAgICAgIG92ID0gbWF4KDAuMCwgbWluKG1heCh0MSwgdDIpLCBMKSAtIG1heChtaW4odDEsIHQyKSwgMC4wKSkKICAgICAgICAgICAgdG90W3JvdW5kKGQsIDEpXSArPSBvdgogICAgICAgIGlmIHRvdDoKICAgICAgICAgICAg"
"ZCwgb3YgPSBtYXgodG90Lml0ZW1zKCksIGtleT1sYW1iZGEga3Y6IGt2WzFdKQogICAgICAgICAgICBpZiBvdiA+PSAwLjQgKiBMOgogICAgICAgICAgICAgICAgYmVzdCA9IGQKICAgICAgICBkaWNoLmFwcGVuZChiZXN0KQogICAgaWYgbm90IGFueShkaWNoKToK"
"ICAgICAgICByZXR1cm4gcG9seSwgMAoKICAgIGRlZiBnaWFvKHAxLCBkMSwgcDIsIGQyKToKICAgICAgICBkZW4gPSBkMVswXSAqIGQyWzFdIC0gZDFbMV0gKiBkMlswXQogICAgICAgIGlmIGFicyhkZW4pIDwgMWUtOToKICAgICAgICAgICAgcmV0dXJuIE5vbmUK"
"ICAgICAgICB0ID0gKChwMlswXSAtIHAxWzBdKSAqIGQyWzFdIC0gKHAyWzFdIC0gcDFbMV0pICogZDJbMF0pIC8gZGVuCiAgICAgICAgcmV0dXJuIChwMVswXSArIHQgKiBkMVswXSwgcDFbMV0gKyB0ICogZDFbMV0pCgogICAgbGluZXMgPSBbXQogICAgZm9yIGkg"
"aW4gcmFuZ2Uobik6CiAgICAgICAgYSwgYiA9IHB0c1tpXSwgcHRzWyhpICsgMSkgJSBuXQogICAgICAgIEwgPSBtYXRoLmRpc3QoYSwgYikKICAgICAgICB1eCwgdXkgPSAoYlswXSAtIGFbMF0pIC8gTCwgKGJbMV0gLSBhWzFdKSAvIEwKICAgICAgICBueCwgbnkg"
"PSB1eSwgLXV4CiAgICAgICAgbGluZXMuYXBwZW5kKCgoYVswXSArIG54ICogZGljaFtpXSwgYVsxXSArIG55ICogZGljaFtpXSksICh1eCwgdXkpLCAoYlswXSArIG54ICogZGljaFtpXSwgYlsxXSArIG55ICogZGljaFtpXSkpKQogICAgbW9pID0gW10KICAgIGZv"
"ciBpIGluIHJhbmdlKG4pOgogICAgICAgIHAwLCBkMCwgZTAgPSBsaW5lc1tpIC0gMV0KICAgICAgICBwMSwgZDEsIF8gPSBsaW5lc1tpXQogICAgICAgIHEgPSBnaWFvKHAwLCBkMCwgcDEsIGQxKQogICAgICAgIGlmIHEgaXMgTm9uZTogICAgICAgICAgICAgICAg"
"ICAgICAgICAgICAgICAgIyBoYWkgY2FuaCB0aGFuZyBoYW5nLCBkbyBkYXkga2hhYyBuaGF1IC0+IGJhYwogICAgICAgICAgICBtb2kgKz0gW2UwLCBwMV0KICAgICAgICBlbHNlOgogICAgICAgICAgICBtb2kuYXBwZW5kKHEpCiAgICBnID0gUG9seWdvbihtb2ks"
"IFtsaXN0KHIuY29vcmRzKSBmb3IgciBpbiBwb2x5LmludGVyaW9yc10pLmJ1ZmZlcigwKQogICAgaWYgZy5nZW9tX3R5cGUgIT0gIlBvbHlnb24iIG9yIGFicyhnLmFyZWEgLSBwb2x5LmFyZWEpID4gMC4yICogcG9seS5hcmVhOgogICAgICAgIHJldHVybiBwb2x5"
"LCAwCiAgICByZXR1cm4gZywgc3VtKDEgZm9yIGQgaW4gZGljaCBpZiBkKQoKCmRlZiBkYWlfY2F0X2N1YShyaW5nX3BvbHksIGN1YSk6CiAgICAiIiJWdW5nIGNhdCBuZXQgdmVuIHRhaSBtb3QgY3VhIGRpOiBkYWkgZG9jIHRoZW8gY2FuaCBwaG9uZyBnYW4gY3Vh"
"IG5oYXQsIHJvbmcgYmFuZyBiZSByb25nIG8gY3VhLgogICAgQ3VhIGNvIGR1b25nIG1vIChjdW5nIHF1YXkpOiBjaGkgY2F0IGNhbmggc29uZyBzb25nIGR1b25nIG1vIChsZWNoIDw9IDIwIGRvKSwgcm9uZyBiYW5nIGR1b25nIG1vLiIiIgogICAgbW8gPSBjdWEu"
"Z2V0KCJtbyIpCiAgICBwdHMgPSBsaXN0KG1vKSBpZiBtbyBlbHNlIFtwIGZvciBzIGluIGN1YVsiZG9hbiJdIGZvciBwIGluIHNdCiAgICBjeCA9IHN1bShwWzBdIGZvciBwIGluIHB0cykgLyBsZW4ocHRzKQogICAgY3kgPSBzdW0ocFsxXSBmb3IgcCBpbiBwdHMp"
"IC8gbGVuKHB0cykKICAgIGV4dCA9IHJpbmdfcG9seS5leHRlcmlvcgogICAgYmVzdCA9IE5vbmUKICAgIGNvb3JkcyA9IGxpc3QoZXh0LmNvb3JkcykKICAgIGZvciBhLCBiIGluIHppcChjb29yZHMsIGNvb3Jkc1sxOl0pOgogICAgICAgIGlmIG1vOgogICAgICAg"
"ICAgICBMYSwgTG0gPSBtYXRoLmRpc3QoYSwgYiksIG1hdGguZGlzdCgqbW8pCiAgICAgICAgICAgIGlmIExhIDwgMSBvciBMbSA8IDEgb3IgYWJzKCgoYlswXSAtIGFbMF0pICogKG1vWzFdWzBdIC0gbW9bMF1bMF0pICsgKGJbMV0gLSBhWzFdKSAqIChtb1sxXVsx"
"XSAtIG1vWzBdWzFdKSkKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgLyAoTGEgKiBMbSkpIDwgbWF0aC5jb3MobWF0aC5yYWRpYW5zKDIwKSk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgIHNlZyA9IExpbmVTdHJpbmcoW2Es"
"IGJdKQogICAgICAgIGQgPSBzZWcuZGlzdGFuY2UoTGluZVN0cmluZyhwdHMpIGlmIGxlbihwdHMpID4gMSBlbHNlIFBvaW50KHB0c1swXSkpCiAgICAgICAgaWYgYmVzdCBpcyBOb25lIG9yIGQgPCBiZXN0WzBdOgogICAgICAgICAgICBiZXN0ID0gKGQsIGEsIGIp"
"CiAgICBpZiBiZXN0IGlzIE5vbmU6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIGQsIGEsIGIgPSBiZXN0CiAgICBpZiBkID4gNDAwOgogICAgICAgIHJldHVybiBOb25lCiAgICBMID0gbWF0aC5kaXN0KGEsIGIpCiAgICB1eCwgdXkgPSAoYlswXSAtIGFbMF0pIC8g"
"TCwgKGJbMV0gLSBhWzFdKSAvIEwKICAgIHRzID0gWyhwWzBdIC0gYVswXSkgKiB1eCArIChwWzFdIC0gYVsxXSkgKiB1eSBmb3IgcCBpbiBwdHNdCiAgICB0MCwgdDEgPSBtaW4odHMpLCBtYXgodHMpCiAgICBueCwgbnkgPSAtdXksIHV4CiAgICAjIGJlIG5nYW5n"
"IHZ1bmcgY2F0IHRpbmggdHUgY2FuaCBwaG9uZzogZHUgcGh1IG5ldCB2ZW4gKGNhY2ggYm8gNTApIGNodSBraG9uZyBsYW4gc2FuZyBuZXQgdmVuIGNhbmggdnVvbmcgZ29jIGtoaQogICAgIyBiYW4gbGUgY3VhIHNhdCBnb2MgcGhvbmcgKHRydW9jIGxhIDQwMCwg"
"Y2F0IG1hdCB+MzYwIG1tIG5ldCB2ZW4gY2FuaCBiZW4sIENUMiAyMy8xMC8yMDI2KQogICAgdyA9IDEyMC4wCiAgICBxID0gWyhhWzBdICsgdXggKiB0MCArIG54ICogdywgYVsxXSArIHV5ICogdDAgKyBueSAqIHcpLCAoYVswXSArIHV4ICogdDEgKyBueCAqIHcs"
"IGFbMV0gKyB1eSAqIHQxICsgbnkgKiB3KSwKICAgICAgICAgKGFbMF0gKyB1eCAqIHQxIC0gbnggKiB3LCBhWzFdICsgdXkgKiB0MSAtIG55ICogdyksIChhWzBdICsgdXggKiB0MCAtIG54ICogdywgYVsxXSArIHV5ICogdDAgLSBueSAqIHcpXQogICAgcmV0dXJu"
"IFBvbHlnb24ocSkKCgpkZWYgbmV0X3Zlbihwb2x5LCBjdXQsIGNhY2gpOgogICAgIiIiT2Zmc2V0IGJpZW4gbmdvYWkgdmFvIHRyb25nICdjYWNoJywgYm8gcGhhbiBuYW0gdHJvbmcgdnVuZyBjYXQgKGN1YSkuIFRyYSB2ZSBsaXN0IChkb25nPywgW2RpZW1dKS4i"
"IiIKICAgIGlubmVyID0gcG9seS5idWZmZXIoLWNhY2gsIGpvaW5fc3R5bGU9Im1pdHJlIikKICAgIGlmIGlubmVyLmlzX2VtcHR5OgogICAgICAgIHJldHVybiBbXQogICAgaWYgaW5uZXIuZ2VvbV90eXBlID09ICJNdWx0aVBvbHlnb24iOgogICAgICAgIGlubmVy"
"ID0gbWF4KGlubmVyLmdlb21zLCBrZXk9bGFtYmRhIGc6IGcuYXJlYSkKICAgIGlubmVyID0gc2hhcGVseS5nZW9tZXRyeS5wb2x5Z29uLm9yaWVudChQb2x5Z29uKGlubmVyLmV4dGVyaW9yKSwgMS4wKQogICAgcmluZyA9IExpbmVTdHJpbmcoaW5uZXIuZXh0ZXJp"
"b3IuY29vcmRzKQogICAgaWYgY3V0IGlzIE5vbmUgb3IgY3V0LmlzX2VtcHR5OgogICAgICAgIHJldHVybiBbKFRydWUsIFsocjEoeCksIHIxKHkpKSBmb3IgeCwgeSBpbiBsaXN0KHJpbmcuY29vcmRzKVs6LTFdXSldCiAgICByZXN0ID0gcmluZy5kaWZmZXJlbmNl"
"KGN1dCkKICAgIGlmIHJlc3QuaXNfZW1wdHk6CiAgICAgICAgcmV0dXJuIFtdCiAgICBwYXJ0cyA9IGxpc3QocmVzdC5nZW9tcykgaWYgaGFzYXR0cihyZXN0LCAiZ2VvbXMiKSBlbHNlIFtyZXN0XQogICAgIyB2b25nIGJpIGNhdCB0YWkgZGllbSBkYXUgKGdvYyBk"
"YXUgdGllbikgLT4gbm9pIGxhaSBoYWkgZG9hbiBjaGFtIG5oYXUKICAgIG1lcmdlZCA9IGxpbmVtZXJnZShNdWx0aUxpbmVTdHJpbmcocGFydHMpKSBpZiBsZW4ocGFydHMpID4gMSBlbHNlIHBhcnRzWzBdCiAgICBwYXJ0cyA9IGxpc3QobWVyZ2VkLmdlb21zKSBp"
"ZiBoYXNhdHRyKG1lcmdlZCwgImdlb21zIikgZWxzZSBbbWVyZ2VkXQogICAgb3V0ID0gW10KICAgIGZvciBwIGluIHBhcnRzOgogICAgICAgIGNzID0gbGlzdChzaGFwZWx5LnNpbXBsaWZ5KHAsIDAuNSkuY29vcmRzKQogICAgICAgIGlmIHAubGVuZ3RoID49IDIw"
"OgogICAgICAgICAgICBvdXQuYXBwZW5kKChGYWxzZSwgWyhyMSh4KSwgcjEoeSkpIGZvciB4LCB5IGluIGNzXSkpCiAgICByZXR1cm4gb3V0CgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
"IGNoaW5oCmRlZiBtYWluKCk6CiAgICBhcCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKGRlc2NyaXB0aW9uPV9fZG9jX18sIGZvcm1hdHRlcl9jbGFzcz1hcmdwYXJzZS5SYXdEZXNjcmlwdGlvbkhlbHBGb3JtYXR0ZXIpCiAgICBhcC5hZGRfYXJndW1lbnQoImR4"
"ZiIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tb3V0LWRpciIsIGRlZmF1bHQ9Ii4iKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXZ1bmciLCBkZWZhdWx0PSIiLCBoZWxwPSJjaGkgeGV0IHZ1bmcgeDAseTAseDEseTEgKHRvYSBkbyBNb2RlbCkiKQogICAgYXAuYWRk"
"X2FyZ3VtZW50KCItLWNhY2gtdmVuIiwgdHlwZT1mbG9hdCwgZGVmYXVsdD01MC4wLCBoZWxwPSJuZXQgdmVuIGNhY2ggZHVvbmcgYm8gdmFvIHRyb25nIChtbSkiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWdhcC1tYXgiLCB0eXBlPWZsb2F0LCBkZWZhdWx0PTEy"
"MDAuMCwgaGVscD0iZG9uZyBvIG1vIHR1b25nIDw9IGdhcCAobW0pIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1kaWVuLXRpY2gtbWF4IiwgdHlwZT1mbG9hdCwgZGVmYXVsdD0xNS4wLCBoZWxwPSJwaG9uZyBsb24gaG9uIChtMikgLT4gY2FuX3hlbSIpCiAgICBh"
"cC5hZGRfYXJndW1lbnQoIi0tbGF5ZXItcmFuaCIsIGRlZmF1bHQ9IiwiLmpvaW4oTEFZRVJfUkFOSCkpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tdGItd2MiLCBkZWZhdWx0PVJFX1RCX1dDLCBoZWxwPSJyZWdleCB0ZW4gYmxvY2sgdGhpZXQgYmkgdmUgc2luaCAo"
"a2hvbmcgZGF1KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tdGItbGciLCBkZWZhdWx0PVJFX1RCX0xHLCBoZWxwPSJyZWdleCB0ZW4gYmxvY2sgbWF5IGdpYXQgLyBjdWMgbm9uZyAoa2hvbmcgZGF1KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tdGhlbSIsIGRl"
"ZmF1bHQ9IiIsCiAgICAgICAgICAgICAgICAgICAgaGVscD0idGhlbSBwaG9uZyBjaGkgZGluaCB0YXkgJ2xvYWk6eCx5O2xvYWk6eCx5JyAobG9haTogd2MsIGxvX2dpYSwgcGhvbmdfcmFjLCBwaG9uZ19rdF9udW9jLCAiCiAgICAgICAgICAgICAgICAgICAgICAg"
"ICAiYnVvbmdfZGVtX3JhYyksIHZkLiBwaG9uZyByYWMga2hvbmcgY28gdGV4dCB0ZW4iKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWt5LWhpZXUiLCBkZWZhdWx0PUtZX0hJRVUsCiAgICAgICAgICAgICAgICAgICAgaGVscD0idGV4dCBreSBoaWV1IHBob25nIHNv"
"IGtob3Agbmd1eWVuIHZhbjogJ1I9cGhvbmdfcmFjLE49cGhvbmdfa3RfbnVvYyciKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWtob25nLWFuaCIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tZXhjZWwiLCBhY3Rpb249InN0b3Jl"
"X3RydWUiLCBoZWxwPSJ4dWF0IHRoZW0gZmlsZSBFeGNlbCAobWFjIGRpbmgga2hvbmcgeHVhdCkiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXh1YXQtbHNwIiwgZGVmYXVsdD0iIiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJnaGkgdGhlbSBmaWxlIGR1IGxp"
"ZXUgY2hvIGxlbmggTElTUCBDSE9OR1RIQU0gKEFTQ0lJLCBtb2kgZG9uZyAxIGJpZXUgdGh1YyBMSVNQKSIpCiAgICBhID0gYXAucGFyc2VfYXJncygpCgogICAgb3MubWFrZWRpcnMoYS5vdXRfZGlyLCBleGlzdF9vaz1UcnVlKQogICAgdGVuID0gb3MucGF0aC5z"
"cGxpdGV4dChvcy5wYXRoLmJhc2VuYW1lKGEuZHhmKSlbMF0KICAgIHByaW50KCJEb2MgRFhGLi4uIiwgZmx1c2g9VHJ1ZSkKICAgIGRvYyA9IGV6ZHhmLnJlYWRmaWxlKGEuZHhmKQogICAgbXNwID0gZG9jLm1vZGVsc3BhY2UoKQogICAgZW50cyA9IGxvY19tc3Ao"
"bXNwKQogICAgeGVudHMsIHhraHVuZyA9IGRvY194cmVmKGVudHMsIGEuZHhmKQogICAgaWYgeGVudHM6CiAgICAgICAgcHJpbnQoZiIgIHRoZW0ge2xlbih4ZW50cyl9IGRvaSB0dW9uZyB0dSB7bGVuKF9YUkVGKX0geHJlZiAoZG9jIHJpZW5nLCBraG9uZyBiaW5k"
"KSIsIGZsdXNoPVRydWUpCiAgICAgICAgZW50cyA9IGVudHMgKyB4ZW50cwogICAgaWYgYS52dW5nOgogICAgICAgIHgwLCB5MCwgeDEsIHkxID0gKGZsb2F0KHYpIGZvciB2IGluIGEudnVuZy5zcGxpdCgiLCIpKQogICAgICAgIGtodW5nX3hldCA9IGJveCh4MCwg"
"eTAsIHgxLCB5MSkKICAgIGVsc2U6CiAgICAgICAga2h1bmdfeGV0ID0gTm9uZQoKICAgIHByaW50KCJEdW5nIGx1b2kgbmV0Li4uIiwgZmx1c2g9VHJ1ZSkKICAgIGNoYWlucyA9IHRwcC5kb2NfY2hhaW5zKGVudHMsIFt4LnN0cmlwKCkgZm9yIHggaW4gYS5sYXll"
"cl9yYW5oLnNwbGl0KCIsIikgaWYgeC5zdHJpcCgpXSkKICAgIHRoZW0gPSBkb2NfdHVvbmdfbm8oZW50cykKICAgIGNoYWlucyArPSB0aGVtCiAgICAjIGtodW5nIGJhbyBibG9jayBsYW4gY2FuIGxhbSByYW5oOiBsbyBnaWEgLyBiYW4gY29uZyBkdW5nIG8gTUFU"
"IFRST05HIGxhbiBjYW4gKGNob3QgMjIvMTAvMjAyNikKICAgIGxhbl9jYW4gPSBkb2NfbGFuX2NhbihlbnRzKQogICAgY2hhaW5zICs9IFsoVHJ1ZSwgbGlzdChiLmV4dGVyaW9yLmNvb3JkcylbOi0xXSkgZm9yIGIgaW4gbGFuX2Nhbl0KICAgIGlmIGtodW5nX3hl"
"dCBpcyBub3QgTm9uZToKICAgICAgICBreCA9IGtodW5nX3hldC5idWZmZXIoMzAwMCkKICAgICAgICBjaGFpbnMgPSBbYyBmb3IgYyBpbiBjaGFpbnMgaWYgTGluZVN0cmluZyhjWzFdIGlmIGxlbihjWzFdKSA+IDEgZWxzZSBjWzFdICogMikuaW50ZXJzZWN0cyhr"
"eCldCiAgICBraHVuZywgdGsgPSB0cHAuZG9jX2todW5nX2N1YShlbnRzLCBjaGFpbnMsIExBWUVSX0NVQSkKICAgIG5vaSA9IG5vaV9kYWlfZGF1X2hvKGNoYWlucykKICAgIGZhY2VzLCBwYWlycywgYnJpZGdlcyA9IHRwcC5idWlsZF9mYWNlcyhjaGFpbnMsIGEu"
"Z2FwX21heCwgbGlzdChraHVuZykgKyBub2kpCiAgICBmYWNlcyA9IFtmIGZvciBmIGluIGZhY2VzIGlmIGYuYXJlYSA+IDAuM2U2XQogICAgY2F5X2ZhY2UgPSBzaGFwZWx5LlNUUnRyZWUoZmFjZXMpCiAgICBuZXQgPSBbXQogICAgZm9yIGNsb3NlZCwgcHRzIGlu"
"IGNoYWluczoKICAgICAgICBxID0gcHRzICsgKFtwdHNbMF1dIGlmIGNsb3NlZCBlbHNlIFtdKQogICAgICAgIG5ldCArPSBbTGluZVN0cmluZyhbcVtpXSwgcVtpICsgMV1dKSBmb3IgaSBpbiByYW5nZShsZW4ocSkgLSAxKSBpZiBtYXRoLmRpc3QocVtpXSwgcVtp"
"ICsgMV0pID4gMC41XQogICAgY2F5X25ldCA9IHNoYXBlbHkuU1RSdHJlZShuZXQpCiAgICBjdWFzID0gZG9jX2N1YShlbnRzLCBjaGFpbnMpCiAgICBjdWFfdGhhbmcsIGRpZW1fa2cgPSBkb2NfY3VhX3RoYW5nKGVudHMpCiAgICBnaWVuZyA9IGRvY19naWVuZ190"
"aGFuZyhlbnRzKQogICAgZGFvX2FsbCA9IGRvY19kYW8oZW50cykKICAgIGNheV9kYW8gPSBzaGFwZWx5LlNUUnRyZWUoZGFvX2FsbCkgaWYgZGFvX2FsbCBlbHNlIE5vbmUKICAgIGRhX2NvID0gaGF0Y2hfZGFfY28obXNwKQogICAgcHJpbnQoZiIgIHtsZW4oY2hh"
"aW5zKX0gY2h1b2kgbmV0ICh0aGVtIHtsZW4odGhlbSl9IG5ldCB0dW9uZyBkYSBubyBvIGxheWVyIDApLCB7bGVuKGZhY2VzKX0gbyBraW4sIHtsZW4oY3Vhcyl9IGN1YSwgIgogICAgICAgICAgZiJ7bGVuKGRhb19hbGwpfSBvIGRhbyIsIGZsdXNoPVRydWUpCgog"
"ICAgc2VlZHMgPSBkb2NfaGF0X2dpb25nKGVudHMsIGEpCiAgICBmb3IgcyBpbiBbeCBmb3IgeCBpbiBhLnRoZW0uc3BsaXQoIjsiKSBpZiB4LnN0cmlwKCldOgogICAgICAgIGxvYWksIHh5ID0gcy5zcGxpdCgiOiIpCiAgICAgICAgaWYgbG9haS5zdHJpcCgpIG5v"
"dCBpbiBURU5fTE9BSToKICAgICAgICAgICAgc3lzLmV4aXQoZiItLXRoZW06IGxvYWkgJ3tsb2FpfScga2hvbmcgaG9wIGxlLCBjaG9uIHRyb25nIHtsaXN0KFRFTl9MT0FJKX0iKQogICAgICAgIHgsIHkgPSAoZmxvYXQodikgZm9yIHYgaW4geHkuc3BsaXQoIiwi"
"KSkKICAgICAgICBzZWVkcy5hcHBlbmQoKGxvYWkuc3RyaXAoKSwgKHgsIHkpLCAiY2jhu4kgxJHhu4tuaCB0YXkiLCAiIikpCiAgICBpZiB4a2h1bmc6ICAgIyBoYXQgdHJvbmcgeHJlZiBjYW4gaG86IG1hIGNhbiBsYXkgdHUgdGVuIHhyZWYgKGtodW5nIGJhbyBu"
"aG8gbmhhdCBjaHVhIGhhdCkKICAgICAgICBkZWYgY2FuX3hyZWYocCk6CiAgICAgICAgICAgIGMgPSBbKGsuYXJlYSwgbWEpIGZvciBrLCBtYSBpbiB4a2h1bmcgaWYgay5jb250YWlucyhQb2ludChwKSldCiAgICAgICAgICAgIHJldHVybiBtaW4oYylbMV0gaWYg"
"YyBlbHNlICIiCiAgICAgICAgc2VlZHMgPSBbKGwsIHAsIG4sIGMgb3IgY2FuX3hyZWYocCkpIGZvciBsLCBwLCBuLCBjIGluIHNlZWRzXQogICAgaWYga2h1bmdfeGV0IGlzIG5vdCBOb25lOgogICAgICAgIHNlZWRzID0gW3MgZm9yIHMgaW4gc2VlZHMgaWYga2h1"
"bmdfeGV0LmNvbnRhaW5zKFBvaW50KHNbMV0pKV0KICAgICMgZ29tIGhhdCB0aGVvIG8ga2luCiAgICBwaG9uZyA9IHt9CiAgICBraG9uZ192YW8gPSBbXQogICAgZm9yIGxvYWksIHAsIG5ndW9uLCBjYW4gaW4gc2VlZHM6CiAgICAgICAgUCA9IFBvaW50KHApCiAg"
"ICAgICAgY2FuZHMgPSBbZmFjZXNbaW50KGspXSBmb3IgayBpbiBjYXlfZmFjZS5xdWVyeShQLCBwcmVkaWNhdGU9ImludGVyc2VjdHMiKV0KICAgICAgICBjYW5kcyA9IFtmIGZvciBmIGluIGNhbmRzIGlmIGYuY29udGFpbnMoUCkgb3IgZi5kaXN0YW5jZShQKSA8"
"IDFdCiAgICAgICAgIyBvIGhlcCA8IDUwMCBtbSAvIDwgMCw1IG0yIChraGUgdHVvbmcsIGRhaSBtZXAgc2FuKSBraG9uZyBwaGFpIHBob25nOiBDVDIgY3VjIG5vbmcgcm9pIHZhbyBkYWkgMTQwMCB4IDE1MAogICAgICAgICMgdGhhbmggImxvIGdpYSIgMCwyMSBt"
"MiAoMjMvMTAvMjAyNikKICAgICAgICBjYW5kcyA9IFtmIGZvciBmIGluIGNhbmRzIGlmIGYuYXJlYSA+PSAwLjVlNiBhbmQgbm90IFBvbHlnb24oZi5leHRlcmlvcikuYnVmZmVyKC0yNTAsIGpvaW5fc3R5bGU9Im1pdHJlIikuaXNfZW1wdHldCiAgICAgICAgaWYg"
"bm90IGNhbmRzOgogICAgICAgICAgICBraG9uZ192YW8uYXBwZW5kKChsb2FpLCBwLCBuZ3VvbikpCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZiA9IG1pbihjYW5kcywga2V5PWxhbWJkYSBnOiBnLmFyZWEpCiAgICAgICAgayA9IGlkKGYpCiAgICAgICAg"
"eiA9IHBob25nLnNldGRlZmF1bHQoaywgZGljdChmYWNlPWYsIGxvYWk9c2V0KCksIG5ndW9uPVtdLCBjYW49c2V0KCkpKQogICAgICAgIHpbImxvYWkiXS5hZGQobG9haSkKICAgICAgICB6WyJuZ3VvbiJdLmFwcGVuZChuZ3VvbikKICAgICAgICBpZiBjYW46CiAg"
"ICAgICAgICAgIHpbImNhbiJdLmFkZChjYW4pCiAgICAjIExvIGdpYSAvIGJhbiBjb25nIGtob25nIGNvIHRoaWV0IGJpLCBraG9uZyBjbyB0ZW46IG8ga2luIDEtMTIgbTIsIGdpYXAgbmdvYWkgbmhhLCBjbyBjdWEgdHJ1b3QgaG9hYyBsYW4gY2FuIHNhdCBiaWVu"
"CiAgICBub2lfdGhhdCA9IGRvY19ub2lfdGhhdChlbnRzKQogICAgY2F5X250ID0gc2hhcGVseS5TVFJ0cmVlKG5vaV90aGF0KSBpZiBub2lfdGhhdCBlbHNlIE5vbmUKICAgIHRydW90ID0gW0xpbmVTdHJpbmcoW3AgZm9yIHMgaW4gY1siZG9hbiJdIGZvciBwIGlu"
"IHNdKSBmb3IgYyBpbiBjdWFzIGlmIGMuZ2V0KCJ0cnVvdCIpXQogICAgZm9yIGYgaW4gZmFjZXM6CiAgICAgICAgaWYgaWQoZikgaW4gcGhvbmcgb3Igbm90IChMR19EVFswXSA8PSBmLmFyZWEgLyAxZTYgPD0gTEdfRFRbMV0pOgogICAgICAgICAgICBjb250aW51"
"ZQogICAgICAgIGlmIGtodW5nX3hldCBpcyBub3QgTm9uZSBhbmQgbm90IGtodW5nX3hldC5jb250YWlucyhmLnJlcHJlc2VudGF0aXZlX3BvaW50KCkpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIGNheV9udCBpcyBub3QgTm9uZSBhbmQgbGVuKGNh"
"eV9udC5xdWVyeShmLCBwcmVkaWNhdGU9ImNvbnRhaW5zIikpID4gMDoKICAgICAgICAgICAgY29udGludWUgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIGNvIGdpdW9uZyAvIHR1IC8gc29mYS4uLiAtPiBwaG9uZyBvLCBraG9uZyBwaGFpIGxv"
"IGdpYQogICAgICAgIGlmIFBvbHlnb24oZi5leHRlcmlvcikuYnVmZmVyKC00MDAsIGpvaW5fc3R5bGU9Im1pdHJlIikuaXNfZW1wdHk6CiAgICAgICAgICAgIGNvbnRpbnVlICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyByb25nIDwgODAwIG1t"
"OiBkYWkgYmF1IC8ga2hlIHR1b25nLCBraG9uZyBwaGFpIGxvIGdpYQogICAgICAgIHZpZW4gPSBQb2x5Z29uKGYuZXh0ZXJpb3IpLmJ1ZmZlcigyNTApCiAgICAgICAgbHlfZG8gPSBbXQogICAgICAgIGlmIGFueSh2aWVuLmludGVyc2VjdHModCkgYW5kIFBvbHln"
"b24oZi5leHRlcmlvcikuYnVmZmVyKC01MCkuZGlzam9pbnQodCkgZm9yIHQgaW4gdHJ1b3QpOgogICAgICAgICAgICBseV9kby5hcHBlbmQoImPhu61hIHRyxrDhu6N0IikKICAgICAgICBpZiBhbnkodmllbi5pbnRlcnNlY3RzKGwpIGZvciBsIGluIGxhbl9jYW4p"
"OgogICAgICAgICAgICBseV9kby5hcHBlbmQoImxhbiBjYW4iKQogICAgICAgIGlmIGx5X2RvIGFuZCBnaWFwX25nb2FpX25oYShQb2x5Z29uKGYuZXh0ZXJpb3IpLCBjYXlfZmFjZSwgZmFjZXMsIGNheV9uZXQsIG5ldCk6CiAgICAgICAgICAgIHBob25nW2lkKGYp"
"XSA9IGRpY3QoZmFjZT1mLCBsb2FpPXsibG9fZ2lhIn0sIG5ndW9uPVsiZ2nDoXAgbmdvw6BpIG5ow6AgKyAiICsgIiArICIuam9pbihseV9kbyldLCBjYW49c2V0KCkpCgogICAgIyBUaGlldCBiaSAvIHRlbiBwaG9uZyBraG9uZyBuYW0gdHJvbmcgbyBraW4gbmFv"
"OiBkdW5nIGxhaSBsdW9pIG5ldCBxdWFuaCBkbywgdGhlbSBuZXQgbWF0IG5nb2FpIChsYXllciAwLCBBLWxpbmUqKQogICAgbmhvbSA9IFtdCiAgICBmb3IgbCwgcCwgbiBpbiBraG9uZ192YW86CiAgICAgICAgZyA9IG5leHQoKGcgZm9yIGcgaW4gbmhvbSBpZiBt"
"YXRoLmRpc3QoZ1siZGllbSJdWzBdLCBwKSA8PSAyMDAwKSwgTm9uZSkKICAgICAgICBpZiBnIGlzIE5vbmU6CiAgICAgICAgICAgIG5ob20uYXBwZW5kKGRpY3QobG9haT1bbF0sIGRpZW09W3BdLCBuZ3Vvbj1bbl0pKQogICAgICAgIGVsc2U6CiAgICAgICAgICAg"
"IGdbImxvYWkiXS5hcHBlbmQobCkKICAgICAgICAgICAgZ1siZGllbSJdLmFwcGVuZChwKQogICAgICAgICAgICBnWyJuZ3VvbiJdLmFwcGVuZChuKQogICAgbWF0X25nb2FpID0gZG9jX21hdF9uZ29haShlbnRzKSBpZiBuaG9tIGVsc2UgW10KICAgIGtob25nX3Zh"
"byA9IFtdCiAgICBmb3IgZyBpbiBuaG9tOgogICAgICAgIGYsIGJyID0ga2hlcF9sYWkoZ1siZGllbSJdLCBjaGFpbnMsIGtodW5nLCBtYXRfbmdvYWksIGEuZ2FwX21heCkKICAgICAgICBpZiBmIGlzIG5vdCBOb25lIGFuZCAoZi5hcmVhIDwgMC41ZTYgb3IgUG9s"
"eWdvbihmLmV4dGVyaW9yKS5idWZmZXIoLTI1MCwgam9pbl9zdHlsZT0ibWl0cmUiKS5pc19lbXB0eSk6CiAgICAgICAgICAgIGYgPSBOb25lICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyBvIGhlcCAoa2hlIHR1b25nIC8gZGFpIG1lcCBzYW4p"
"IGtob25nIHBoYWkgcGhvbmcKICAgICAgICBpZiBmIGlzIE5vbmU6CiAgICAgICAgICAgIGtob25nX3ZhbyArPSBsaXN0KHppcChnWyJsb2FpIl0sIGdbImRpZW0iXSwgZ1sibmd1b24iXSkpCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgdHJ1bmcgPSBuZXh0"
"KCh6IGZvciB6IGluIHBob25nLnZhbHVlcygpIGlmIHpbImZhY2UiXS5pbnRlcnNlY3Rpb24oZikuYXJlYSA+IDAuNSAqIGYuYXJlYSksIE5vbmUpCiAgICAgICAgeiA9IHRydW5nIG9yIHBob25nLnNldGRlZmF1bHQoaWQoZiksIGRpY3QoZmFjZT1mLCBsb2FpPXNl"
"dCgpLCBuZ3Vvbj1bXSwgY2FuPXNldCgpKSkKICAgICAgICB6WyJsb2FpIl0udXBkYXRlKGdbImxvYWkiXSkKICAgICAgICB6WyJuZ3VvbiJdICs9IGdbIm5ndW9uIl0gKyBbImtow6lwIGLhurFuZyBuw6l0IG3hurd0IG5nb8OgaSAobGF5ZXIgMCAvIEEtbGluZSki"
"XQogICAgICAgIGJyaWRnZXMgPSBsaXN0KGJyaWRnZXMpICsgbGlzdChicikKCiAgICAjIFBob25nIHJhYyBraG9uZyBjbyBreSBoaWV1IFI6IG8gbmhvIGNvIGN1YSBkaSB2YSBtbyByYSBjdWEgdGhhbmcgdGFpIHRyb25nICh0aGFuZyByYWMpLiBUYW5nIDQgVGhh"
"cCBCOiBvIGNhbmggdGhhbmcKICAgICMgMzAwS0cgY28gMyB0aHVuZyByYWMgNDcweDUzMHg5NDAsIGtob25nIGNvIGNodSBSICgzMC8xMC8yMDI2KS4gQ2hpbmggZ2llbmcgdGhhbmcgY2h1YSB0ZXh0IHRhaSB0cm9uZyAtPiBibyBxdWEuCiAgICBmb3IgZ19jdCBp"
"biBjdWFfdGhhbmc6CiAgICAgICAgZm9yIGsgaW4gY2F5X2ZhY2UucXVlcnkoZ19jdC5idWZmZXIoNTApKToKICAgICAgICAgICAgZiA9IGZhY2VzW2ludChrKV0KICAgICAgICAgICAgaWYgaWQoZikgaW4gcGhvbmcgb3Igbm90IChMR19EVFswXSA8PSBmLmFyZWEg"
"LyAxZTYgPD0gTEdfRFRbMV0pIG9yIGYuZGlzdGFuY2UoZ19jdCkgPiA1MDoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIFBvbHlnb24oZi5leHRlcmlvcikuYnVmZmVyKC00MDAsIGpvaW5fc3R5bGU9Im1pdHJlIikuaXNfZW1wdHkgb3Ig"
"YW55KGYuY29udGFpbnMocSkgZm9yIHEgaW4gZGllbV9rZyk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBpZiBjdWFfcXVhbmgoZiwgY3Vhcyk6CiAgICAgICAgICAgICAgICBwaG9uZ1tpZChmKV0gPSBkaWN0KGZhY2U9ZiwgbG9haT17InBo"
"b25nX3JhYyJ9LCBuZ3Vvbj1bImPhu61hIHRoYW5nIHThuqNpIHRy4buNbmcgKyBj4butYSDEkWkiXSwgY2FuPXNldCgpKQoKICAgICMgUGhvbmcgcmFjIC8gcGhvbmcgS1QgbnVvYyBuaGFuIHRoZW8ga3kgaGlldSwgdGVuOiBvIHBoYWkgY28gY3VhIGRpLCBraG9u"
"ZyB0aGkgbGEgaG9wIGt5IHRodWF0IC0+IGJvCiAgICBmb3IgayBpbiBsaXN0KHBob25nKToKICAgICAgICB6ID0gcGhvbmdba10KICAgICAgICBpZiB6WyJsb2FpIl0gPD0gQ0FOX0NVQSBhbmQgImNo4buJIMSR4buLbmggdGF5IiBub3QgaW4gelsibmd1b24iXSBh"
"bmQgbm90IGN1YV9xdWFuaCh6WyJmYWNlIl0sIGN1YXMpOgogICAgICAgICAgICBkZWwgcGhvbmdba10KICAgICAgICAgICAga2hvbmdfdmFvLmFwcGVuZCgobWluKHpbImxvYWkiXSksICh6WyJmYWNlIl0uY2VudHJvaWQueCwgelsiZmFjZSJdLmNlbnRyb2lkLnkp"
"LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAia8O9IGhp4buHdSAvIHTDqm4gcGjDsm5nIHRyb25nIMO0IGtow7RuZyBjw7MgY+G7rWEgxJFpICho4buZcCBr4bu5IHRodeG6rXQ/KSIpKQoKICAgICMgQnVvbmcgZGVtIHBob25nIHJhYzogbyAxLTEwIG0y"
"IG5vaSB2b2kgcGhvbmcgcmFjIGJhbmcgY3VhIGRpIE5BTSBUUk9ORyBUVU9ORyBHSVVBIEhBSSBPIChraHVuZyBjdWEgY2hhbSBiaWVuIGNhCiAgICAjIGhhaSBvIDw9IDE1MCkgdmEgY28gdGhlbSBpdCBuaGF0IDEgY3VhIGRpIGtoYWMgKHJhIGhhbmggbGFuZyk7"
"IG5oaWV1IG8gZGF0IHRoaSBsYXkgbyBuaG8gbmhhdC4gVGhhbmcgbWF5IHJhYyBub2kKICAgICMgdm9pIHBob25nIHJhYyBiYW5nIHR1b25nIC8gbyBtbyAoa2hvbmcgY3VhKSBuZW4ga2hvbmcgYmkgbmhhbjsgcGhvbmcgZGVtIHRoYW5nIGJvICLEkCIgbyBzYXQg"
"cGhvbmcgcmFjIG5odW5nIGN1YQogICAgIyBwaG9uZyByYWMga2hvbmcgbmFtIHRyb25nIHR1b25nIGNodW5nIG5lbiBjdW5nIGJpIGxvYWkgKHRhbmcgNCBUaGFwIEIpLgogICAgZm9yIHogaW4gW3ogZm9yIHogaW4gbGlzdChwaG9uZy52YWx1ZXMoKSkgaWYgInBo"
"b25nX3JhYyIgaW4gelsibG9haSJdXToKICAgICAgICBjdWFfciA9IGN1YV9xdWFuaCh6WyJmYWNlIl0sIGN1YXMpCiAgICAgICAgdW5nID0gW10KICAgICAgICBmb3IgZiBpbiBmYWNlczoKICAgICAgICAgICAgaWYgaWQoZikgaW4gcGhvbmcgb3IgZiBpcyB6WyJm"
"YWNlIl0gb3Igbm90ICgxLjBlNiA8PSBmLmFyZWEgPD0gRFRfQlVPTkdfREVNICogMWU2KToKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGYuZGlzdGFuY2UoelsiZmFjZSJdKSA+IDQwMDoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAg"
"ICAgICAgICAgIGN1YV9mID0gY3VhX3F1YW5oKGYsIGN1YXMpCiAgICAgICAgICAgIGNodW5nID0gW2kgZm9yIGkgaW4gY3VhX3IgaWYgaSBpbiBjdWFfZiBhbmQKICAgICAgICAgICAgICAgICAgICAgTGluZVN0cmluZyhbcCBmb3IgcyBpbiBjdWFzW2ldWyJkb2Fu"
"Il0gZm9yIHAgaW4gc10pLmRpc3RhbmNlKFBvbHlnb24oZi5leHRlcmlvcikuZXh0ZXJpb3IpIDw9IDE1MCBhbmQKICAgICAgICAgICAgICAgICAgICAgTGluZVN0cmluZyhbcCBmb3IgcyBpbiBjdWFzW2ldWyJkb2FuIl0gZm9yIHAgaW4gc10pLmRpc3RhbmNlKFBv"
"bHlnb24oelsiZmFjZSJdLmV4dGVyaW9yKS5leHRlcmlvcikgPD0gMTUwXQogICAgICAgICAgICBpZiBjaHVuZyBhbmQgbGVuKGN1YV9mKSA+PSAyOgogICAgICAgICAgICAgICAgdW5nLmFwcGVuZChmKQogICAgICAgIGlmIHVuZzoKICAgICAgICAgICAgZiA9IG1p"
"bih1bmcsIGtleT1sYW1iZGEgZzogZy5hcmVhKQogICAgICAgICAgICBwaG9uZ1tpZChmKV0gPSBkaWN0KGZhY2U9ZiwgbG9haT17ImJ1b25nX2RlbV9yYWMifSwgbmd1b249WyJj4butYSDEkWkgc2FuZyBwaMOybmcgcsOhYyArIGPhu61hIHJhIGjDoG5oIGxhbmci"
"XSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBjYW49c2V0KCkpCgogICAgY2FuX2lkeCA9IHRpbV9jYW4oZW50cykKICAgIHZ1bmcgPSBbXQogICAgZm9yIHogaW4gc29ydGVkKHBob25nLnZhbHVlcygpLCBrZXk9bGFtYmRhIHo6ICgtelsiZmFjZSJd"
"LmNlbnRyb2lkLnksIHpbImZhY2UiXS5jZW50cm9pZC54KSk6CiAgICAgICAgZiA9IHpbImZhY2UiXQogICAgICAgIGxvYWkgPSBtaW4oelsibG9haSJdLCBrZXk9bGFtYmRhIGw6IFVVX1RJRU5bbF0pCiAgICAgICAgZ2hpID0gW10KICAgICAgICBnID0gZG9uX2dp"
"YW4oZikKICAgICAgICBnLCBuX2RheSA9IHZlX21hdF9sb2koZywgY2F5X25ldCwgbmV0KQogICAgICAgIGcgPSBkb25fZ2lhbihnKQogICAgICAgIGlmIGcuYXJlYSA8IDAuNWU2IG9yIFBvbHlnb24oZy5leHRlcmlvcikuYnVmZmVyKC0yNTAsIGpvaW5fc3R5bGU9"
"Im1pdHJlIikuaXNfZW1wdHk6CiAgICAgICAgICAgICMgbyBoZXAgKGtoZSB0dW9uZyAvIGRhaSBtZXAgc2FuKSBraG9uZyBwaGFpIHBob25nIC0+IGNobyBjYW4geGVtIChDVDI6IGRhaSAxNDAwIHggMTUwLCAyMy8xMC8yMDI2KQogICAgICAgICAgICBraG9uZ192"
"YW8uYXBwZW5kKChsb2FpLCAoZi5jZW50cm9pZC54LCBmLmNlbnRyb2lkLnkpLCAiw7QgaOG6uXAgPCA1MDAgbW0sIGtow7RuZyBwaOG6o2kgcGjDsm5nIikpCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgIyBkYW86IHRydWMgLyBob3Aga3kgdGh1YXQgbmFt"
"IHRyb25nIHBob25nICg+PSA4MCUgZGllbiB0aWNoIGRhbykKICAgICAgICBkYW8gPSBbXQogICAgICAgIGlmIGNheV9kYW8gaXMgbm90IE5vbmU6CiAgICAgICAgICAgIGZvciBrIGluIGNheV9kYW8ucXVlcnkoZyk6CiAgICAgICAgICAgICAgICBxID0gZGFvX2Fs"
"bFtpbnQoayldCiAgICAgICAgICAgICAgICBpZiBxLmludGVyc2VjdGlvbihnKS5hcmVhID49IDAuOCAqIHEuYXJlYSBhbmQgcS5hcmVhIDwgMC42ICogZy5hcmVhOgogICAgICAgICAgICAgICAgICAgIGRhby5hcHBlbmQocSkKICAgICAgICBsbyA9IFtQb2x5Z29u"
"KHIpIGZvciByIGluIGcuaW50ZXJpb3JzIGlmIFBvbHlnb24ocikuYXJlYSA+PSAwLjAyZTZdCiAgICAgICAgYm8gPSBQb2x5Z29uKGcuZXh0ZXJpb3IpCiAgICAgICAgIyBkYW8gY2hhbSBiaWVuIHBob25nIChjb3QsIGhvcCBzYXQgdHVvbmcpIC0+IGtoYWMgdmFv"
"IGR1b25nIGJvLCBuZXQgdmVuIGRpIHRoZW8KICAgICAgICAjIGtoZSBnaXVhIGRhbyB2YSBiaWVuIDwga2hvYW5nIGx1aSBuZXQgdmVuICg1MCkgdGhpIG5ldCB2ZW4gc2UgY2F0IHF1YSBkYW8gLT4gY29pIGxhIGNoYW0gKENUMjogaG9wIHRydWMgY2FjaAogICAg"
"ICAgICMgYm8gMjUgbW0sIG5ndW9pIGR1bmcgYmFvIGxvaSAyMy8xMC8yMDI2KQogICAgICAgIGNoYW0gPSBbcSBmb3IgcSBpbiBkYW8gaWYgcS5kaXN0YW5jZShiby5leHRlcmlvcikgPCBhLmNhY2hfdmVuXQogICAgICAgIGlmIGNoYW06CiAgICAgICAgICAgIGcy"
"ID0gYm8uZGlmZmVyZW5jZSh1bmFyeV91bmlvbihjaGFtKSkKICAgICAgICAgICAgIyBibyBkYWkgdnVuIDwgNjAgbW0gY29uIGxhaSBnaXVhIGRhbyB2YSB0dW9uZyAobWF1IENIMTU6IGNvdCBjYWNoIHR1b25nIDUwIC0+IGtoYWMgbGllbiB0b2kgdHVvbmcpCiAg"
"ICAgICAgICAgIGcyID0gZzIuYnVmZmVyKC0zMCwgam9pbl9zdHlsZT0ibWl0cmUiKS5idWZmZXIoMzAsIGpvaW5fc3R5bGU9Im1pdHJlIikKICAgICAgICAgICAgaWYgZzIuZ2VvbV90eXBlID09ICJNdWx0aVBvbHlnb24iOgogICAgICAgICAgICAgICAgZzIgPSBt"
"YXgoZzIuZ2VvbXMsIGtleT1sYW1iZGEgeDogeC5hcmVhKQogICAgICAgICAgICBpZiBnMi5nZW9tX3R5cGUgPT0gIlBvbHlnb24iIGFuZCBub3QgZzIuaXNfZW1wdHk6CiAgICAgICAgICAgICAgICBibyA9IGRvbl9naWFuKFBvbHlnb24oZzIuZXh0ZXJpb3IpKQog"
"ICAgICAgICAgICBkYW8gPSBbcSBmb3IgcSBpbiBkYW8gaWYgbm90IGFueShxIGlzIGMgZm9yIGMgaW4gY2hhbSldCiAgICAgICAgIyBnaWVuZyB0aGFuZyBtYXkgbGFuIHZhbyBwaG9uZyAoa2hvbmcgY28gbmV0IHR1b25nIG5nYW4pOiBraG9ldCBnaWVuZyArIGRh"
"aSBvIGN1YSA8PSAzMDAgdHJvbmcgY2hpZXUgZGF5IHR1b25nLAogICAgICAgICMgY2FuaCBjb24gbGFpIGdpYXAgbyBjdWEgbGEgY3VhIHRoYW5nIG1heSAtPiBuZ2F0IG5ldCB2ZW4KICAgICAgICBjdWFfdG0gPSBbXQogICAgICAgIGZvciBzaCBpbiBnaWVuZzoK"
"ICAgICAgICAgICAgaWYgc2guaW50ZXJzZWN0aW9uKGJvKS5hcmVhIDwgMC4wNWU2OgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgIyBkbyBraG9ldCBkOiB0YW5nIDEwIG1tL2J1b2M7IHRyb25nIGRhaSBvIGN1YSBkaWVuIHRpY2gga2hvZXQg"
"dGFuZyBkZXUgKD0gYmUgcm9uZyBvIGN1YSB4IDEwKSwgY2hhbSBtYXQgdHVvbmcKICAgICAgICAgICAgIyBwaG9uZyBjaGluaCB0aGkgdGFuZyBkb3QgYmllbiAtPiBkdW5nIG8gYnVvYyB0cnVvYyBkbwogICAgICAgICAgICBuZ29haSA9IGJvLmRpZmZlcmVuY2Uo"
"c2gpCiAgICAgICAgICAgIGR0ID0gW25nb2FpLmludGVyc2VjdGlvbihzaC5idWZmZXIoZCwgam9pbl9zdHlsZT0ibWl0cmUiKSkuYXJlYSBmb3IgZCBpbiByYW5nZSgwLCA0MTAsIDEwKV0KICAgICAgICAgICAgYnVvYyA9IFtkdFtpICsgMV0gLSBkdFtpXSBmb3Ig"
"aSBpbiByYW5nZShsZW4oZHQpIC0gMSldCiAgICAgICAgICAgIGRfb2sgPSAwCiAgICAgICAgICAgIGlmIGJ1b2MgYW5kIGJ1b2NbMF0gPiAwOgogICAgICAgICAgICAgICAgZm9yIGksIGJfIGluIGVudW1lcmF0ZShidW9jKToKICAgICAgICAgICAgICAgICAgICBp"
"ZiBiXyA+IDEuMyAqIGJ1b2NbMF0gKyAxMDAwOgogICAgICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgICAgIGRfb2sgPSAoaSArIDEpICogMTAKICAgICAgICAgICAgYm8yID0gbmdvYWkuZGlmZmVyZW5jZShzaC5idWZmZXIoZF9vaywg"
"am9pbl9zdHlsZT0ibWl0cmUiKSkgaWYgZF9vayBlbHNlIG5nb2FpCiAgICAgICAgICAgIGJvMiA9IGJvMi5idWZmZXIoLTMwLCBqb2luX3N0eWxlPSJtaXRyZSIpLmJ1ZmZlcigzMCwgam9pbl9zdHlsZT0ibWl0cmUiKQogICAgICAgICAgICBpZiBibzIuZ2VvbV90"
"eXBlID09ICJNdWx0aVBvbHlnb24iOgogICAgICAgICAgICAgICAgYm8yID0gbWF4KGJvMi5nZW9tcywga2V5PWxhbWJkYSB4OiB4LmFyZWEpCiAgICAgICAgICAgIGlmIGJvMi5pc19lbXB0eSBvciBibzIuZ2VvbV90eXBlICE9ICJQb2x5Z29uIiBvciBibzIuYXJl"
"YSA8IDAuNSAqIGJvLmFyZWE6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBib19tb2kgPSBkb25fZ2lhbihQb2x5Z29uKGJvMi5leHRlcmlvcikpCiAgICAgICAgICAgICMgY2hpIGRhaSBvIGN1YSAocGhhbiBraG9ldCBuZ29haSBnaWVuZyk7"
"IGtob25nIGR1bmcgYm8gLSBib19tb2kgdmkgcGhlcCB0cnUgZGUgbGFpIG1lcCB2dW4gZG9jIG1vaSBjYW5oCiAgICAgICAgICAgICMgZHVuZyB0cnVvYyBtYXQgdHVvbmcgNSBtbTogbyBkX29rIGRhaSBraG9ldCBjaGFtIG1hdCBwaG9uZyBjaGluaCBkb2MgY2Eg"
"Y2FuaCAoZGllbiB0aWNoIDApCiAgICAgICAgICAgIGRhaSA9IG5nb2FpLmludGVyc2VjdGlvbihzaC5idWZmZXIobWF4KGRfb2sgLSA1LCAxKSwgam9pbl9zdHlsZT0ibWl0cmUiKSkgaWYgZF9vayBlbHNlIHNoCiAgICAgICAgICAgIGNodW5nID0gYm9fbW9pLmV4"
"dGVyaW9yLmludGVyc2VjdGlvbihkYWkuYnVmZmVyKDEwKSkKICAgICAgICAgICAgYm8gPSBib19tb2kKICAgICAgICAgICAgaWYgbm90IGNodW5nLmlzX2VtcHR5IGFuZCBjaHVuZy5sZW5ndGggPj0gMzAwOgogICAgICAgICAgICAgICAgY3VhX3RtLmFwcGVuZChj"
"aHVuZy5idWZmZXIoMzAwLCBjYXBfc3R5bGU9ImZsYXQiKSkKICAgICAgICAgICAgZGFvID0gW3EgZm9yIHEgaW4gZGFvIGlmIHEuaW50ZXJzZWN0aW9uKGJvKS5hcmVhID4gMC41ICogcS5hcmVhXQogICAgICAgICAgICBsbyA9IFtxIGZvciBxIGluIGxvIGlmIHEu"
"aW50ZXJzZWN0aW9uKGJvKS5hcmVhID4gMC41ICogcS5hcmVhXQogICAgICAgICAgICBnaGkuYXBwZW5kKCJraG/DqXQgZ2nhur9uZyB0aGFuZyBtw6F5LCBuZ+G6r3QgbsOpdCB2w6luIOG7nyBj4butYSB0aGFuZyIpCiAgICAgICAgdnVuZ19oYXRjaCA9IGJvLmRp"
"ZmZlcmVuY2UodW5hcnlfdW5pb24oZGFvICsgbG8pKSBpZiAoZGFvIG9yIGxvKSBlbHNlIGJvCiAgICAgICAgIyBjYXQgbmV0IHZlbiB0YWkgY3VhIGRpCiAgICAgICAgY3V0ID0gbGlzdChjdWFfdG0pCiAgICAgICAgbl9jdWEgPSBsZW4oY3VhX3RtKQogICAgICAg"
"IGZvciBjIGluIGN1YXM6CiAgICAgICAgICAgIGlmIGNbImxvYWkiXSAhPSAiY3VhX2RpIjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIHB0cyA9IFtwIGZvciBzIGluIGNbImRvYW4iXSBmb3IgcCBpbiBzXQogICAgICAgICAgICBpZiBQb2x5"
"Z29uKGJvLmV4dGVyaW9yKS5idWZmZXIoMzAwKS5pbnRlcnNlY3RzKExpbmVTdHJpbmcocHRzKSBpZiBsZW4ocHRzKSA+IDEgZWxzZSBQb2ludChwdHNbMF0pKToKICAgICAgICAgICAgICAgIGQgPSBkYWlfY2F0X2N1YShibywgYykKICAgICAgICAgICAgICAgIGlm"
"IGQgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgY3V0LmFwcGVuZChkKQogICAgICAgICAgICAgICAgICAgIG5fY3VhICs9IDEKICAgICAgICAjIGN1YSB0aGFuZyBtYXkgKG8gdHVvbmcga2hvbmcgaGF0Y2ggY2FuaCB0aGFuZyBtYXkgY28gdGV4dCB0"
"YWkgdHJvbmcpIHNhdCBiaWVuIHBob25nCiAgICAgICAgZm9yIGdfY3QgaW4gY3VhX3RoYW5nOgogICAgICAgICAgICBpZiBnX2N0LmRpc3RhbmNlKGJvLmV4dGVyaW9yKSA8PSA1MCBhbmQgbm90IGJvLmJ1ZmZlcigtMjApLmNvbnRhaW5zKGdfY3QuY2VudHJvaWQp"
"OgogICAgICAgICAgICAgICAgZCA9IGRhaV9jYXRfY3VhKGJvLCBkaWN0KGRvYW49WyhwLCBxKSBmb3IgcCwgcSBpbiB6aXAoZ19jdC5leHRlcmlvci5jb29yZHMsIGxpc3QoZ19jdC5leHRlcmlvci5jb29yZHMpWzE6XSldKSkKICAgICAgICAgICAgICAgIGlmIGQg"
"aXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgY3V0LmFwcGVuZChkKQogICAgICAgICAgICAgICAgICAgIG5fY3VhICs9IDEKICAgICAgICAgICAgICAgICAgICBpZiAiY+G7rWEgdGhhbmcgbcOheSIgbm90IGluIGdoaToKICAgICAgICAgICAgICAgICAg"
"ICAgICAgZ2hpLmFwcGVuZCgiY+G7rWEgdGhhbmcgbcOheSIpCiAgICAgICAgIyBvIGtpbiBraGFjIGNoYW0gdGhhbmcgdmFvIGJpZW4gcGhvbmcgKGNoaSBjYWNoIDEgbmV0LCBraG9uZyBjbyBiZSBkYXkgdHVvbmcpID0gbyBtbywgdmQuIHRoYW5nIG1heSByYWMg"
"dGhvbmcKICAgICAgICAjIHRoYW5nIHZhbyBwaG9uZyByYWMgKENUMSB0YW5nIDVBLTEwKS4gQ3VhIGNvIGtodW5nIC8gdHVvbmcgY28gYmUgZGF5IHRoaSBoYWkgbyBjYWNoIG5oYXUgPj0gMTAwIG5lbiBraG9uZyBiaSBjYXQuCiAgICAgICAgIyBDaGkgYXAgY2hv"
"IHBob25nIHJhYyAvIGJ1b25nIGRlbTogbyBXQywgbG8gZ2lhIHRhbmcgNCBUaGFwIEIgcXV5IHRhYyBuYXkgY2F0IG5oYW0gNCBjaG8gKGRheSBwaG9uZyBjaGkgbGEgMSBuZXQpLgogICAgICAgIGZvciBrIGluIChjYXlfZmFjZS5xdWVyeShmLmJ1ZmZlcigzMCkp"
"IGlmIGxvYWkgaW4gKCJwaG9uZ19yYWMiLCAiYnVvbmdfZGVtX3JhYyIpIGVsc2UgW10pOgogICAgICAgICAgICBuYiA9IGZhY2VzW2ludChrKV0KICAgICAgICAgICAgaWYgbmIgaXMgZiBvciBuYi5hcmVhID4gMC42ICogZi5hcmVhIGFuZCBuYi5hcmVhID4gMjBl"
"NjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIG5iLmJ1ZmZlcigtMjUwLCBqb2luX3N0eWxlPSJtaXRyZSIpLmlzX2VtcHR5OgogICAgICAgICAgICAgICAgY29udGludWUgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICMgZGFp"
"IGhlcCA8IDUwMCBtbTogbG9uZyB0dW9uZyAvIGJhdSwga2hvbmcgcGhhaSBvIG1vCiAgICAgICAgICAgIGNodW5nID0gZi5leHRlcmlvci5pbnRlcnNlY3Rpb24obmIuYnVmZmVyKDMwKSkKICAgICAgICAgICAgaWYgY2h1bmcuaXNfZW1wdHkgb3IgY2h1bmcubGVu"
"Z3RoIDwgMzAwOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgY3V0LmFwcGVuZChjaHVuZy5idWZmZXIoMzAwLCBjYXBfc3R5bGU9ImZsYXQiKSkKICAgICAgICAgICAgcyA9IGYiw7QgbeG7nyBnacOhcCDDtCBrw61uIGLDqm4gY+G6oW5oIHtj"
"aHVuZy5sZW5ndGg6LjBmfSBtbSIKICAgICAgICAgICAgaWYgcyBub3QgaW4gZ2hpOgogICAgICAgICAgICAgICAgZ2hpLmFwcGVuZChzKQogICAgICAgICMgbyBtbyBraG9uZyBjbyBjdWEgKGRvYW4gZG9uZyBvIG1vIG5hbSB0cmVuIGJpZW4gcGhvbmcsIGtob25n"
"IHRydW5nIGtodW5nIGN1YSBzbykKICAgICAgICBmb3IgYnIgaW4gYnJpZGdlczoKICAgICAgICAgICAgaWYgYnIubGVuZ3RoIDwgMzAwOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgaWYgYm8uZXh0ZXJpb3IuYnVmZmVyKDUpLmNvbnRhaW5z"
"KGJyKSBhbmQgbm90IGFueSgKICAgICAgICAgICAgICAgICAgICBMaW5lU3RyaW5nKFtwIGZvciBzIGluIGNbImRvYW4iXSBmb3IgcCBpbiBzXVs6Ml0pLmJ1ZmZlcigzMDApLmludGVyc2VjdHMoYnIpIGZvciBjIGluIGN1YXMpOgogICAgICAgICAgICAgICAgIyBk"
"b2FuIGRvbmcgbmFtIGRlIGxlbiB0dW9uZyB0aGF0IGtob25nIHBoYWkgbyBtbzogdHVuZyBuZ2F0IG5oYXQgbmV0IHZlbiBvIHR1b25nIChUaGFwIEIgIzM5LCBDVDEgIzEsCiAgICAgICAgICAgICAgICAjICM2NjsgMzAvMTAvMjAyNikuIEJlIG5nYW5nIDEyMCBu"
"aHUgZGFpX2NhdF9jdWE6IDMwMCBjYXQgbGFuIHNhbmcgbmV0IHZlbiBjYW5oIHZ1b25nIGdvYwogICAgICAgICAgICAgICAgaWYgcGh1X3R1b25nKGJyLCBjYXlfbmV0LCBuZXQpID49IDAuNToKICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAg"
"ICAgICAgY3V0LmFwcGVuZChici5idWZmZXIoMTIwLCBjYXBfc3R5bGU9ImZsYXQiKSkKICAgICAgICAgICAgICAgIHMgPSBmIsO0IG3hu58ga2jDtG5nIHbhur0gY+G7rWEge2JyLmxlbmd0aDouMGZ9IG1tIgogICAgICAgICAgICAgICAgaWYgcyBub3QgaW4gZ2hp"
"OgogICAgICAgICAgICAgICAgICAgIGdoaS5hcHBlbmQocykKICAgICAgICBpZiBvcy5lbnZpcm9uLmdldCgiQ1RfREVCVUciKToKICAgICAgICAgICAgcHJpbnQoIiAgW2RlYnVnXSIsIGxvYWksIFtyMSh2KSBmb3IgdiBpbiBiby5ib3VuZHNdLCAiY2F0OiIsIFtb"
"cjEodikgZm9yIHYgaW4gYy5ib3VuZHNdIGZvciBjIGluIGN1dF0pCiAgICAgICAgaWYgYm8uYXJlYSA8IDAuNWU2IG9yIFBvbHlnb24oYm8uZXh0ZXJpb3IpLmJ1ZmZlcigtMjUwLCBqb2luX3N0eWxlPSJtaXRyZSIpLmlzX2VtcHR5OgogICAgICAgICAgICBraG9u"
"Z192YW8uYXBwZW5kKChsb2FpLCAoYm8uY2VudHJvaWQueCwgYm8uY2VudHJvaWQueSksICLDtCBo4bq5cCA8IDUwMCBtbSBzYXUga2hpIGtob8OpdCwga2jDtG5nIHBo4bqjaSBwaMOybmciKSkKICAgICAgICAgICAgY29udGludWUKICAgICAgICB2ZW4gPSBuZXRf"
"dmVuKGJvLCB1bmFyeV91bmlvbihjdXQpIGlmIGN1dCBlbHNlIE5vbmUsIGEuY2FjaF92ZW4pCiAgICAgICAgZHQgPSBiby5hcmVhIC8gMWU2CiAgICAgICAgdHJhbmcgPSAic2VfdmUiCiAgICAgICAgaWYgZGFfY28gaXMgbm90IE5vbmUgYW5kIHZ1bmdfaGF0Y2gu"
"aW50ZXJzZWN0aW9uKGRhX2NvKS5hcmVhID49IDAuOSAqIHZ1bmdfaGF0Y2guYXJlYToKICAgICAgICAgICAgdHJhbmcgPSAiZGFfY28iCiAgICAgICAgZWxpZiBkdCA+IGEuZGllbl90aWNoX21heDoKICAgICAgICAgICAgdHJhbmcgPSAiY2FuX3hlbSIKICAgICAg"
"ICAgICAgZ2hpLmFwcGVuZChmInBow7JuZyBs4bubbiB7ZHQ6LjFmfSBtwrIgKGPDsyB0aOG7gyBn4buZcCBuaOG6p20gduG7m2kgcGjDsm5nIGtow6FjKSIpCiAgICAgICAgZWxpZiBuX2N1YSA9PSAwIGFuZCBub3QgYW55KCLDtCBt4bufIiBpbiBzIGZvciBzIGlu"
"IGdoaSk6CiAgICAgICAgICAgIGdoaS5hcHBlbmQoImtow7RuZyB0w6xtIHRo4bqleSBj4butYSDEkWkgLSBuw6l0IHbDqW4gY2jhuqF5IGvDrW4iKQogICAgICAgIGN4LCBjeSA9IGJvLmNlbnRyb2lkLngsIGJvLmNlbnRyb2lkLnkKICAgICAgICBpZiBsb2FpIGlu"
"IENBTl9DVUEgfCB7ImJ1b25nX2RlbV9yYWMifToKICAgICAgICAgICAgelsiY2FuIl0gPSB7IktodSBjaHVuZyJ9ICAgICAgICAgICAgICAgICAgICAjIHBob25nIHJhYywgYnVvbmcgZGVtLCBwaG9uZyBLVCBudW9jIHRodW9jIGxvaSBjaHVuZwogICAgICAgIGVs"
"aWYgbm90IHpbImNhbiJdIGFuZCBjYW5faWR4IGlzIG5vdCBOb25lOgogICAgICAgICAgICBjYXlfYywgcHRzX2MsIG1hX2MgPSBjYW5faWR4CiAgICAgICAgICAgIGsgPSBjYXlfYy5uZWFyZXN0KFBvaW50KGN4LCBjeSkpCiAgICAgICAgICAgIGlmIGsgaXMgbm90"
"IE5vbmUgYW5kIHB0c19jW2ludChrKV0uZGlzdGFuY2UoYm8pIDw9IDMwMDA6CiAgICAgICAgICAgICAgICB6WyJjYW4iXS5hZGQobWFfY1tpbnQoayldKQogICAgICAgIHZ1bmcuYXBwZW5kKGRpY3QoCiAgICAgICAgICAgIGlkPWxlbih2dW5nKSArIDEsIGxvYWk9"
"bG9haSwgdGVuX2xvYWk9VEVOX0xPQUlbbG9haV0sIGNhbj0iLCIuam9pbihzb3J0ZWQoelsiY2FuIl0pKSwKICAgICAgICAgICAgbmd1b249c29ydGVkKHNldCh6WyJuZ3VvbiJdKSlbOjhdLCBkaWVuX3RpY2g9cm91bmQoZHQsIDIpLCB0YW09W3IxKGN4KSwgcjEo"
"Y3kpXSwKICAgICAgICAgICAgYm89W1tyMSh4KSwgcjEoeSldIGZvciB4LCB5IGluIGxpc3QoYm8uZXh0ZXJpb3IuY29vcmRzKVs6LTFdXSwKICAgICAgICAgICAgZGFvPVtbW3IxKHgpLCByMSh5KV0gZm9yIHgsIHkgaW4gbGlzdChQb2x5Z29uKHEuZXh0ZXJpb3Ip"
"LmV4dGVyaW9yLmNvb3JkcylbOi0xXV0gZm9yIHEgaW4gZGFvICsgbG9dLAogICAgICAgICAgICB2ZW49W2RpY3QoZG9uZz1kZywgZGluaD1bW3gsIHldIGZvciB4LCB5IGluIHB0c10pIGZvciBkZywgcHRzIGluIHZlbl0sCiAgICAgICAgICAgIHNvX2N1YT1uX2N1"
"YSwgY2FuaF9kYXlfcmFfbWF0X2xvaT1uX2RheSwgdHJhbmdfdGhhaT10cmFuZywgZ2hpX2NodT0iOyAiLmpvaW4oZ2hpKSkpCgogICAgIyBoYXQgZ2lvbmcga2hvbmcgcm9pIHZhbyBvIGtpbiBuYW86IGdvbSB0aGVvIHZpIHRyaSAoPD0gMiBtKSAtPiAiY2hvIGNh"
"biB4ZW0iIChwaG9uZyBobywgdHVvbmcgdmUgbmV0IG1hbmgpCiAgICBsb3QgPSBbXQogICAgZm9yIGwsIHAsIG4gaW4ga2hvbmdfdmFvOgogICAgICAgIGcgPSBuZXh0KChnIGZvciBnIGluIGxvdCBpZiBtYXRoLmRpc3QoZ1siZGllbSJdLCBwKSA8PSAyMDAwKSwg"
"Tm9uZSkKICAgICAgICBpZiBnIGlzIE5vbmU6CiAgICAgICAgICAgIGxvdC5hcHBlbmQoZGljdChsb2FpPWwsIGRpZW09W3IxKHBbMF0pLCByMShwWzFdKV0sIG5ndW9uPVtuXSkpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZ1sibmd1b24iXS5hcHBlbmQobikK"
"ICAgIGtxID0gZGljdChmaWxlPWEuZHhmLCBjYWNoX3Zlbj1hLmNhY2hfdmVuLCBsYXllcj1MQVlFUl9WRSwgdnVuZz12dW5nLCBjaG9fY2FuX3hlbT1sb3QpCiAgICBqcCA9IG9zLnBhdGguam9pbihhLm91dF9kaXIsIHRlbiArICJfY2hvbmd0aGFtLmpzb24iKQog"
"ICAgd2l0aCBvcGVuKGpwLCAidyIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGZvOgogICAgICAgIGpzb24uZHVtcChrcSwgZm8sIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTEpCiAgICBpZiBhLmV4Y2VsOgogICAgICAgIHh1YXRfZXhjZWwodnVuZywgbG90LCBv"
"cy5wYXRoLmpvaW4oYS5vdXRfZGlyLCB0ZW4gKyAiX2Nob25ndGhhbS54bHN4IikpCiAgICBpZiBhLnh1YXRfbHNwOgogICAgICAgIHh1YXRfbHNwKHZ1bmcsIGxvdCwgYS54dWF0X2xzcCkKICAgIGlmIG5vdCBhLmtob25nX2FuaDoKICAgICAgICB4dWF0X2FuaCh2"
"dW5nLCBuZXQsIGN1YXMsIGxvdCwgb3MucGF0aC5qb2luKGEub3V0X2RpciwgdGVuICsgIl9jaG9uZ3RoYW0ucG5nIiksIGtodW5nX3hldCkKICAgIGRlbSA9IGRlZmF1bHRkaWN0KGludCkKICAgIGZvciB2IGluIHZ1bmc6CiAgICAgICAgZGVtWyh2WyJ0cmFuZ190"
"aGFpIl0sIHZbImxvYWkiXSldICs9IDEKICAgIHByaW50KCJLZXQgcXVhOiIsIGRpY3QoZGVtKSkKICAgIHByaW50KCJDaG8gY2FuIHhlbSAodGhpZXQgYmkgLyB0ZW4gcGhvbmcga2hvbmcgbmFtIHRyb25nIG8ga2luIG5hbyk6IiwgbGVuKGxvdCkpCiAgICBmb3Ig"
"ZyBpbiBsb3Q6CiAgICAgICAgcHJpbnQoIiAgIiwgZ1sibG9haSJdLCBnWyJkaWVtIl0sICIsICIuam9pbihzb3J0ZWQoc2V0KGdbIm5ndW9uIl0pKSlbOjgwXSkKICAgIHByaW50KGpwKQoKCmRlZiB4dWF0X2xzcCh2dW5nLCBsb3QsIHBhdGgpOgogICAgIiIiRHUg"
"bGlldSBjaG8gbGVuaCBMSVNQIENIT05HVEhBTSwgY2hpIGt5IHR1IEFTQ0lJIChkb2MgYmFuZyByZWFkLWxpbmUgKyByZWFkLCBraG9uZyBwaHUgdGh1b2MgbWEgaG9hKToKICAgICAgIChWVU5HIGlkICJsb2FpIiAidHJhbmdfdGhhaSIgImNhbiIgKCh4IHkpIC4u"
"LikgKCgoeCB5KSAuLi4pIC4uLikgKChkb25nICgoeCB5KSAuLi4pKSAuLi4pKQogICAgICAgKFhFTSAibG9haSIgeCB5ICJuZ3VvbiIpIiIiCiAgICBkZWYgcyh2KToKICAgICAgICByZXR1cm4gJyInICsgYm9fZGF1KHN0cih2KSkuZW5jb2RlKCJhc2NpaSIsICJy"
"ZXBsYWNlIikuZGVjb2RlKCkucmVwbGFjZSgiXFwiLCAiLyIpLnJlcGxhY2UoJyInLCAiJyIpICsgJyInCgogICAgZGVmIGRzKHB0cyk6CiAgICAgICAgcmV0dXJuICIoIiArICIgIi5qb2luKGYiKHt4Oi4xZn0ge3k6LjFmfSkiIGZvciB4LCB5IGluIHB0cykgKyAi"
"KSIKCiAgICB3aXRoIG9wZW4ocGF0aCwgInciLCBlbmNvZGluZz0iYXNjaWkiLCBuZXdsaW5lPSJcclxuIikgYXMgZm86CiAgICAgICAgZm9yIHYgaW4gdnVuZzoKICAgICAgICAgICAgZGFvID0gIigiICsgIiAiLmpvaW4oZHMoZCkgZm9yIGQgaW4gdlsiZGFvIl0p"
"ICsgIikiCiAgICAgICAgICAgIHZlbiA9ICIoIiArICIgIi5qb2luKGYiKHsxIGlmIGxbJ2RvbmcnXSBlbHNlIDB9IHtkcyhsWydkaW5oJ10pfSkiIGZvciBsIGluIHZbInZlbiJdKSArICIpIgogICAgICAgICAgICBmby53cml0ZShmIihWVU5HIHt2WydpZCddfSB7"
"cyh2Wydsb2FpJ10pfSB7cyh2Wyd0cmFuZ190aGFpJ10pfSB7cyh2WydjYW4nXSl9IHtkcyh2WydibyddKX0ge2Rhb30ge3Zlbn0pXG4iKQogICAgICAgIGZvciBnIGluIGxvdDoKICAgICAgICAgICAgZm8ud3JpdGUoZiIoWEVNIHtzKGdbJ2xvYWknXSl9IHtnWydk"
"aWVtJ11bMF06LjFmfSB7Z1snZGllbSddWzFdOi4xZn0ge3MoJywgJy5qb2luKHNvcnRlZChzZXQoZ1snbmd1b24nXSkpKSl9KVxuIikKCgpkZWYgeHVhdF9leGNlbCh2dW5nLCBsb3QsIHBhdGgpOgogICAgdHJ5OgogICAgICAgIGZyb20gb3BlbnB5eGwgaW1wb3J0"
"IFdvcmtib29rCiAgICBleGNlcHQgSW1wb3J0RXJyb3I6CiAgICAgICAgcmV0dXJuCiAgICB3YiA9IFdvcmtib29rKCkKICAgIHdzID0gd2IuYWN0aXZlCiAgICB3cy50aXRsZSA9ICJDaOG7kW5nIHRo4bqlbSIKICAgIHdzLmFwcGVuZChbIlNUVCIsICJMb+G6oWki"
"LCAiQ8SDbiIsICJUcuG6oW5nIHRow6FpIiwgIkRp4buHbiB0w61jaCAobcKyKSIsICJUw6JtIFgiLCAiVMOibSBZIiwgIlPhu5EgY+G7rWEgxJFpIiwgIlPhu5EgxJHhuqNvIiwKICAgICAgICAgICAgICAgIlPhu5EgxJFv4bqhbiBuw6l0IHbDqW4iLCAiTmjhuq1u"
"IHRoZW8iLCAiR2hpIGNow7oiXSkKICAgIGZvciB2IGluIHZ1bmc6CiAgICAgICAgd3MuYXBwZW5kKFt2WyJpZCJdLCB2WyJ0ZW5fbG9haSJdLCB2WyJjYW4iXSwgdlsidHJhbmdfdGhhaSJdLCB2WyJkaWVuX3RpY2giXSwgdlsidGFtIl1bMF0sIHZbInRhbSJdWzFd"
"LAogICAgICAgICAgICAgICAgICAgdlsic29fY3VhIl0sIGxlbih2WyJkYW8iXSksIGxlbih2WyJ2ZW4iXSksICIsICIuam9pbih2WyJuZ3VvbiJdKSwgdlsiZ2hpX2NodSJdXSkKICAgIGZvciBjb2wsIHcgaW4gemlwKCJBQkNERUZHSElKS0wiLCAoNiwgMTgsIDgs"
"IDEwLCAxMiwgMTAsIDEwLCA5LCA4LCAxMiwgNTAsIDUwKSk6CiAgICAgICAgd3MuY29sdW1uX2RpbWVuc2lvbnNbY29sXS53aWR0aCA9IHcKICAgIHdzMiA9IHdiLmNyZWF0ZV9zaGVldCgiQ2jhu5cgY+G6p24geGVtIikKICAgIHdzMi5hcHBlbmQoWyJTVFQiLCAi"
"TG/huqFpIiwgIlgiLCAiWSIsICJOaOG6rW4gdGhlbyIsICJHaGkgY2jDuiJdKQogICAgZm9yIGksIGcgaW4gZW51bWVyYXRlKGxvdCwgMSk6CiAgICAgICAgd3MyLmFwcGVuZChbaSwgVEVOX0xPQUkuZ2V0KGdbImxvYWkiXSwgZ1sibG9haSJdKSwgZ1siZGllbSJd"
"WzBdLCBnWyJkaWVtIl1bMV0sICIsICIuam9pbihzb3J0ZWQoc2V0KGdbIm5ndW9uIl0pKSksCiAgICAgICAgICAgICAgICAgICAgIktow7RuZyBraMOpcCDEkcaw4bujYyBwaMOybmcgKHTGsOG7nW5nIHbhur0gbsOpdCBt4bqjbmggLyBo4bufIG3hu5l0IHBow61h"
"KSAtIHbhur0gdGF5IGhv4bq3YyBjaOG6oXkgbOG6oWkgduG7m2kgLS10aGVtIl0pCiAgICBmb3IgY29sLCB3IGluIHppcCgiQUJDREVGIiwgKDYsIDE4LCAxMCwgMTAsIDUwLCA3MCkpOgogICAgICAgIHdzMi5jb2x1bW5fZGltZW5zaW9uc1tjb2xdLndpZHRoID0g"
"dwogICAgdHJ5OgogICAgICAgIHdiLnNhdmUocGF0aCkKICAgIGV4Y2VwdCBQZXJtaXNzaW9uRXJyb3I6CiAgICAgICAgcHJpbnQoIktob25nIGdoaSBkdW9jIEV4Y2VsIChkYW5nIG1vPyk6IiwgcGF0aCkKCgpkZWYgeHVhdF9hbmgodnVuZywgbmV0LCBjdWFzLCBs"
"b3QsIHBhdGgsIGtodW5nX3hldCk6CiAgICBpbXBvcnQgbWF0cGxvdGxpYgogICAgbWF0cGxvdGxpYi51c2UoIkFnZyIpCiAgICBpbXBvcnQgbWF0cGxvdGxpYi5weXBsb3QgYXMgcGx0CiAgICBpZiBraHVuZ194ZXQgaXMgbm90IE5vbmU6CiAgICAgICAgeDAsIHkw"
"LCB4MSwgeTEgPSBraHVuZ194ZXQuYm91bmRzCiAgICBlbGlmIHZ1bmc6CiAgICAgICAgeHMgPSBbcFswXSBmb3IgdiBpbiB2dW5nIGZvciBwIGluIHZbImJvIl1dCiAgICAgICAgeXMgPSBbcFsxXSBmb3IgdiBpbiB2dW5nIGZvciBwIGluIHZbImJvIl1dCiAgICAg"
"ICAgeDAsIHgxLCB5MCwgeTEgPSBtaW4oeHMpIC0gMzAwMCwgbWF4KHhzKSArIDMwMDAsIG1pbih5cykgLSAzMDAwLCBtYXgoeXMpICsgMzAwMAogICAgZWxzZToKICAgICAgICByZXR1cm4KICAgIFcgPSAyNAogICAgZmlnID0gcGx0LmZpZ3VyZShmaWdzaXplPShX"
"LCBtYXgoNCwgVyAqICh5MSAtIHkwKSAvIG1heCh4MSAtIHgwLCAxKSkpKQogICAgYXggPSBmaWcuYWRkX2F4ZXMoWzAsIDAsIDEsIDFdKQogICAga3ggPSBib3goeDAsIHkwLCB4MSwgeTEpCiAgICBmb3IgcyBpbiBuZXQ6CiAgICAgICAgaWYgcy5pbnRlcnNlY3Rz"
"KGt4KToKICAgICAgICAgICAgeHMsIHlzID0gcy54eQogICAgICAgICAgICBheC5wbG90KHhzLCB5cywgY29sb3I9IiM5YTlhOWEiLCBsdz0wLjMpCiAgICBmb3IgYyBpbiBjdWFzOgogICAgICAgIGZvciBwLCBxIGluIGNbImRvYW4iXToKICAgICAgICAgICAgYXgu"
"cGxvdChbcFswXSwgcVswXV0sIFtwWzFdLCBxWzFdXSwgY29sb3I9IiNjOGEwNjAiIGlmIGNbImxvYWkiXSA9PSAiY3VhX2RpIiBlbHNlICIjNjBhMGM4IiwgbHc9MC40KQogICAgbWF1ID0geyJzZV92ZSI6ICIjMjJhYTIyIiwgImRhX2NvIjogIiM4ODg4ODgiLCAi"
"Y2FuX3hlbSI6ICIjZmY4ODAwIn0KICAgIGZvciB2IGluIHZ1bmc6CiAgICAgICAgYiA9IHZbImJvIl0gKyBbdlsiYm8iXVswXV0KICAgICAgICBheC5maWxsKFtwWzBdIGZvciBwIGluIGJdLCBbcFsxXSBmb3IgcCBpbiBiXSwgY29sb3I9bWF1W3ZbInRyYW5nX3Ro"
"YWkiXV0sIGFscGhhPTAuMjUsIGx3PTApCiAgICAgICAgYXgucGxvdChbcFswXSBmb3IgcCBpbiBiXSwgW3BbMV0gZm9yIHAgaW4gYl0sIGNvbG9yPW1hdVt2WyJ0cmFuZ190aGFpIl1dLCBsdz0wLjgpCiAgICAgICAgZm9yIGQgaW4gdlsiZGFvIl06CiAgICAgICAg"
"ICAgIGQyID0gZCArIFtkWzBdXQogICAgICAgICAgICBheC5maWxsKFtwWzBdIGZvciBwIGluIGQyXSwgW3BbMV0gZm9yIHAgaW4gZDJdLCBjb2xvcj0id2hpdGUiLCBsdz0wLjUsIGVjPSIjMjI1NWZmIikKICAgICAgICBmb3IgbCBpbiB2WyJ2ZW4iXToKICAgICAg"
"ICAgICAgcHRzID0gbFsiZGluaCJdICsgKFtsWyJkaW5oIl1bMF1dIGlmIGxbImRvbmciXSBlbHNlIFtdKQogICAgICAgICAgICBheC5wbG90KFtwWzBdIGZvciBwIGluIHB0c10sIFtwWzFdIGZvciBwIGluIHB0c10sIGNvbG9yPSJyZWQiLCBsdz0xLjIpCiAgICAg"
"ICAgYXgudGV4dCh2WyJ0YW0iXVswXSwgdlsidGFtIl1bMV0sIGYne3ZbImlkIl19XG57dlsidGVuX2xvYWkiXS5zcGxpdCgiIC8iKVswXX0nLCBoYT0iY2VudGVyIiwgdmE9ImNlbnRlciIsCiAgICAgICAgICAgICAgICBmb250c2l6ZT02LCBjb2xvcj0iYmxhY2si"
"KQogICAgZm9yIGksIGcgaW4gZW51bWVyYXRlKGxvdCwgMSk6CiAgICAgICAgYXgucGxvdChbZ1siZGllbSJdWzBdXSwgW2dbImRpZW0iXVsxXV0sIG1hcmtlcj0iWCIsIG1zPTEyLCBjb2xvcj0iI2ZmODgwMCIpCiAgICAgICAgYXgudGV4dChnWyJkaWVtIl1bMF0g"
"KyA0MDAsIGdbImRpZW0iXVsxXSwgZiJYZW0ge2l9IiwgZm9udHNpemU9NywgY29sb3I9IiNmZjU1MDAiKQogICAgYXguc2V0X3hsaW0oeDAsIHgxKQogICAgYXguc2V0X3lsaW0oeTAsIHkxKQogICAgYXguc2V0X2FzcGVjdCgiZXF1YWwiKQogICAgYXguYXhpcygi"
"b2ZmIikKICAgIGZpZy5zYXZlZmlnKHBhdGgsIGRwaT0xNTAsIGZhY2Vjb2xvcj0id2hpdGUiKQogICAgcGx0LmNsb3NlKGZpZykKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbWFpbigpCg=="
)
("dien-tich-ch/scripts/tao_polyline_phong.py"
"IyEvdXNyL2Jpbi9lbnYgcHl0aG9uCiMgLSotIGNvZGluZzogdXRmLTggLSotCiIiIkR1bmcgcG9seWxpbmUgdGhvbmcgdGh1eSB0dW5nIHBob25nIHR1IG5ldCBob2FuIHRoaWVuL3R1b25nIHRyb25nIERYRiAoQXJjaGl2aW5hKS4KClkgdHVvbmc6IGdvbSBjYWMg"
"bmV0IGJpZW4gKHZ1YSB0cmF0LCB0dW9uZywgY290LCBsYW4gY2FuIGxvLWdpYS4uLikgdGhhbmggbWFuZyBsdW9pLCBkb25nIGNhYwpvIGN1YSA8PSAxLDIgbSBiYW5nIGRvYW4gdGhhbmcgbyBDQSBIQUkgTUFUIHR1b25nIChvIGN1YSB0aGFuaCB2dW5nIHJpZW5n"
"LCBraG9uZyB0aHVvYyBwaG9uZyBuYW8pLApyb2kgbGF5IHZ1bmcga2luIGNodWEgZGllbSBkYXQgdGVuIHBob25nICh0ZXh0KSBsYW0gcG9seWxpbmUgcGhvbmcuCgpDaGluaCBoaW5oICgxMC8xMC8yMDI2LCBkdW5nIGNodW5nIGNoaW5oX2hpbmgucHkgdm9pIG1h"
"dF9iYW5nX3RhbmcucHkpOiBzYXUga2hpIGxheSB2dW5nIGtpbiwgcG9seWdvbiBwaG9uZyBkdW9jCm5hbiBjYW5oIHhpZW4sIGJvIGdhaS9raGFjLCBjYXQgcGhhbiBsb2kgcmEga2luaCBuZ29haSBtYXQgdHVvbmcsIHRydSBvcCBXQyAxMCBtbSwgbHVpIHRyYXQg"
"MTUgbW0gbyBtYXQgZGF1IHR1b25nCig8PSAzNTAgbW0pIGNodWEgdmUgdHJhdCwga2VvIGxvIGdpYSByYSBtYXQgdHJvbmcgYmF1LiBUYXQgYmFuZyAtLWtob25nLWNoaW5oLWhpbmguCgpLaG9uZyBzdWEgZmlsZSBEWEYgZGF1IHZhby4gWHVhdDogSlNPTiB0b20g"
"dGF0IChzdGRvdXQpLCAuc2NyIHZlIHBvbHlsaW5lLCAueGxzeCwgLnBuZyB4ZW0gbGFpLgoKICAgIHB5dGhvbiB0YW9fcG9seWxpbmVfcGhvbmcucHkgPGZpbGUuZHhmPiAtLW91dC1kaXIgPHRodSBtdWM+IFstLWdhcC1tYXggMTIwMF0gWy0tZGVidWddCiIiIgpp"
"bXBvcnQgYXJncGFyc2UKaW1wb3J0IGltcG9ydGxpYi51dGlsCmltcG9ydCBpbwppbXBvcnQganNvbgppbXBvcnQgbWF0aAppbXBvcnQgb3MKaW1wb3J0IHJlCmltcG9ydCBzeXMKaW1wb3J0IHVuaWNvZGVkYXRhCmZyb20gY29sbGVjdGlvbnMgaW1wb3J0IGRlZmF1"
"bHRkaWN0CmZyb20gZGVjaW1hbCBpbXBvcnQgRGVjaW1hbCwgUk9VTkRfSEFMRl9VUAoKaW1wb3J0IGV6ZHhmCmltcG9ydCBzaGFwZWx5CmZyb20gZXpkeGYgaW1wb3J0IHBhdGggYXMgZXpwYXRoCmZyb20gc2hhcGVseS5nZW9tZXRyeSBpbXBvcnQgTGluZVN0cmlu"
"ZywgUG9pbnQsIFBvbHlnb24KZnJvbSBzaGFwZWx5Lm9wcyBpbXBvcnQgcG9seWdvbml6ZSwgdW5hcnlfdW5pb24KCl9zcGVjX2NoID0gaW1wb3J0bGliLnV0aWwuc3BlY19mcm9tX2ZpbGVfbG9jYXRpb24oImNoaW5oX2hpbmgiLCBvcy5wYXRoLmpvaW4ob3MucGF0"
"aC5kaXJuYW1lKG9zLnBhdGguYWJzcGF0aChfX2ZpbGVfXykpLCAiY2hpbmhfaGluaC5weSIpKQpjaGggPSBpbXBvcnRsaWIudXRpbC5tb2R1bGVfZnJvbV9zcGVjKF9zcGVjX2NoKQpfc3BlY19jaC5sb2FkZXIuZXhlY19tb2R1bGUoY2hoKQoKTEFZRVJfUEhPTkcg"
"PSAiQS0gRGllbiB0aWNoIHBob25nIgojIExheWVyIGxhbSByYW5oIHBob25nIChuZXQgaG9hbiB0aGllbiwgdHVvbmcsIGNvdCwgbGFuIGNhbiBsby1naWEpLiBLSE9ORyBnb20gbm9pIHRoYXQsIHRoaWV0IGJpLCBjYW5oIGN1YS4KTEFZRVJfUkFOSCA9IFsiQS1W"
"dWEgdHJhdCIsICJBLVdhbGwiLCAiQS1Db2x1bW4iLCAiQS1MaW5lIl0KTEFZRVJfVEVOID0gIkEtVGV4dCIKIyBMYXllciBjdWEgZGkgLyBjdWEgc28gKGtlIGNhIGRvaSB0dW9uZyBBdXRvQ0FEIEFyY2hpdGVjdHVyZSBkYSBubyk6IGNoaSBsYXkgTkVUIEJBTyBL"
"SFVORyBuYW0gdHJvbmcgY2hpZXUgZGF5IHR1b25nCiMgbGFtIHJhbmg7IGNhbmggY3VhIG1vIHJhIG5nb2FpIHR1b25nIHZhIGN1bmcgcXVheSBjYW5oIGJpIGJvLgpMQVlFUl9DVUEgPSBbIkEtRG9vciIsICJBLVdpbmRvdyIsICJBLUdsYXoiLCAiQS1D4butYSIs"
"ICJBLUN1YSIsICJBLU9wZW5pbmciLCAiQS1XaW5kb3ctRyJdCkRBWV9UVU9OR19UT0lfREEgPSA0MDAuMCAgICMgbW06IG51YSBiZSBkYXkgdHVvbmcgbG9uIG5oYXQga2hpIHRpbSBoYWkgbWF0IHR1b25nIGhhaSBiZW4gY3VhClJFVF9NQVggPSA0MDAuMCAgICAg"
"ICMgZG8gZGFpIHRvaSBkYSBjdWEgZG9hbiAibWEgY3VhIiAoamFtYiByZXR1cm4pLCBtbQpUT0xfVEhBTkcgPSAyMC4wICAgICAjIHNhaSBzbyB0aGFuZyBoYW5nIGdpdWEgMiBkYXUgbyBjdWEsIG1tClNOQVAgPSA2LjAgICAgICAgICAgICMga2hlIGhvIG5obyBj"
"b2kgbmh1IGNoYW0gbmhhdSwgbW0KR0FQX0dPQyA9IDE1MC4wICAgICAgIyBraGUgaG8gbmhvIG8gR09DIChoYWkgbmV0IHZ1b25nIGdvYyBraG9uZyBjaGFtIG5oYXUpLCBtbQpMT0ksIENBTkhfQkFPLCBEQVQsIEdPSV9ZID0gIkzhu5dpIiwgIkPhuqNuaCBiw6Fv"
"IiwgIsSQ4bqhdCIsICJH4bujaSDDvSIKUkVfTkhBTiA9IHJlLmNvbXBpbGUociJcZCsoPzpbLixdXGQrKT9ccyooPzptMnxtwrJ8446hKSIsIHJlLkkpClRFTl9XQyA9IHIiXGJ3Y1xifHZlIHNpbmh8XGJ0YW1cYiIgICAgICAgICAgICAgICAgICAgIyByZWdleCAo"
"a2hvbmcgZGF1KSB0ZW4gcGhvbmcgdmUgc2luaDogdHJ1IG9wIDEwIG1tClJFX0xPX0dJQSA9IHJlLmNvbXBpbGUociJsb1tccy1dKmdpYXxiYW4gY29uZyIsIHJlLkkpICAgIyBsbyBnaWEgLyBiYW4gY29uZzoga2VvIGNhbmggcmEgbWF0IHRyb25nIGJhdQoKCmRl"
"ZiByMSh4KToKICAgIHJldHVybiBmbG9hdChEZWNpbWFsKHN0cih4KSkucXVhbnRpemUoRGVjaW1hbCgiMC4xIiksIHJvdW5kaW5nPVJPVU5EX0hBTEZfVVApKQoKCmRlZiBib19kYXUocyk6CiAgICBzID0gdW5pY29kZWRhdGEubm9ybWFsaXplKCJORkQiLCAocyBv"
"ciAiIikucmVwbGFjZSgixJEiLCAiZCIpLnJlcGxhY2UoIsSQIiwgIkQiKSkKICAgIHJldHVybiAiIi5qb2luKGMgZm9yIGMgaW4gcyBpZiB1bmljb2RlZGF0YS5jYXRlZ29yeShjKSAhPSAiTW4iKS5sb3dlcigpCgoKZGVmIG5vcm0ocyk6CiAgICByZXR1cm4gcmUu"
"c3ViKHIiXHMrIiwgIiAiLCAocyBvciAiIikuc3RyaXAoKSkubG93ZXIoKQoKCmRlZiBsYXllcl9nb2MobmFtZSk6CiAgICAiIiJUZW4gbGF5ZXIgc2F1IGtoaSBibyB0aWVuIHRvIHhyZWYvYmluZDogJ0NIMDZ8QS1WdWEgdHJhdCcsICckMCRBLVZ1YSB0cmF0JyB2"
"YSAnQ0gwMyQwJEEtVnVhIHRyYXQnCiAgICAoeHJlZiBkYSBiaW5kKSBkZXUgdGhhbmggJ2EtdnVhIHRyYXQnLiIiIgogICAgcyA9IChuYW1lIG9yICIiKS5zcGxpdCgifCIpWy0xXQogICAgcyA9IHJlLnNwbGl0KHIiXCRcZCtcJCIsIHMpWy0xXQogICAgcmV0dXJu"
"IG5vcm0ocykKCgojIEJsb2NrL3hyZWYga2hvbmcgY2h1YSByYW5oIHBob25nIChjaHUgdGhpY2gsIGNodSBnaWFpLCBraHVuZyB0ZW4sIGx1b2kgdHJ1YywgbWF0IGJhbmcgdHJhbi4uLik6IGJvIHF1YS4KQkxPQ0tfQk9fUVVBID0gcmUuY29tcGlsZShyIlxiKGdo"
"aSA/Y2hbdcO6XXxub3RlfGxlZ2VuZHxjaHUgZ2lhaXxraHVuZ3xsdW9pfHRyYW58bG9pIHRoYW5nKVxiIiwgcmUuSSkKCgpfQk9fUVVBID0gW0JMT0NLX0JPX1FVQV0gICAjIGNvIHRoZSBkb2kgYmFuZyAtLWJsb2NrLWJvLXF1YQoKCmRlZiB3YWxrKGVudGl0aWVz"
"LCBkZXB0aD0wLCBtYXhfZGVwdGg9MywgX3Bhcj1Ob25lKToKICAgICIiIkR1eWV0IGRvaSB0dW9uZyBNb2RlbCwgZGkgc2F1IHZhbyBibG9jay94cmVmIChJTlNFUlQpIGRhIGR1b2MgZXpkeGYgYmllbiBkb2kgdG9hIGRvIHZlIGhlIE1vZGVsLgoKICAgIERvaSB0"
"dW9uZyBsYXllciAwIHRyb25nIGJsb2NrIGxheSBsYXllciBjdWEgSU5TRVJUIGNodWEgbm8gKGR1bmcgcXV5IHVvYyBBdXRvQ0FEKTogdmkgZHUgbGFuIGNhbiB2ZSBvIGxheWVyIDAgdHJvbmcKICAgIGJsb2NrIGNoZW4gdHJlbiBsYXllciBBLUxhbmNhbiBkdW9j"
"IHRpbmggbGEgQS1MYW5jYW4gKENUMSB0YW5nIDVBLTEwOiB+Mi41MDAgbmV0IGxhbiBjYW4gbmFtIG8gbGF5ZXIgMCkuIiIiCiAgICBmb3IgZSBpbiBlbnRpdGllczoKICAgICAgICBpZiBlLmR4Zi5nZXQoImludmlzaWJsZSIsIDApOiAgICAgICAgICAgICMgcGhh"
"biB0dSBhbiAodHJhbmcgdGhhaSBoaWVuIHRoaSBjdWEgYmxvY2sgZG9uZykKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBlLmR4ZnR5cGUoKSA9PSAiSU5TRVJUIjoKICAgICAgICAgICAgaWYgZGVwdGggPj0gbWF4X2RlcHRoIG9yIChfQk9fUVVBWzBd"
"IGlzIG5vdCBOb25lIGFuZCBfQk9fUVVBWzBdLnNlYXJjaChlLmR4Zi5uYW1lIG9yICIiKSk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBsYXkgPSBfcGFyIGlmIChfcGFyIGFuZCBsYXllcl9nb2MoZS5keGYubGF5ZXIpID09ICIwIikgZWxz"
"ZSBlLmR4Zi5sYXllcgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBzdWJzID0gbGlzdChlLnZpcnR1YWxfZW50aXRpZXMoKSkKICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGZv"
"ciB2IGluIHN1YnM6ICAgICAgICAgICAgICAgICAgICAgICAjIGJhbiBzYW8gYW86IGRvaSBsYXllciBraG9uZyBhbmggaHVvbmcgYmFuIHZlCiAgICAgICAgICAgICAgICBpZiBsYXllcl9nb2Modi5keGYubGF5ZXIpID09ICIwIjoKICAgICAgICAgICAgICAgICAg"
"ICB2LmR4Zi5sYXllciA9IGxheQogICAgICAgICAgICB5aWVsZCBmcm9tIHdhbGsoc3VicywgZGVwdGggKyAxLCBtYXhfZGVwdGgsIGxheSkKICAgICAgICBlbHNlOgogICAgICAgICAgICB5aWVsZCBlCgoKZGVmIGRvY19jaGFpbnMobXNwLCBsYXllcnMpOgogICAg"
"IiIiVHJhIHZlIGxpc3QgKGNsb3NlZCwgWyh4LHkpLi4uXSkgdHUgTElORS9MV1BPTFlMSU5FIHRyZW4gY2FjIGxheWVyIGNobyBwaGVwIChrZSBjYSBiZW4gdHJvbmcgYmxvY2sveHJlZikuIiIiCiAgICB3YW50ID0ge2xheWVyX2dvYyh4KSBmb3IgeCBpbiBsYXll"
"cnN9CiAgICBjaGFpbnMgPSBbXQogICAgZm9yIGUgaW4gd2Fsayhtc3ApOgogICAgICAgIGlmIGUuZHhmdHlwZSgpIG5vdCBpbiAoIkxJTkUiLCAiTFdQT0xZTElORSIpIG9yIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgbm90IGluIHdhbnQ6CiAgICAgICAgICAgIGNv"
"bnRpbnVlCiAgICAgICAgaWYgZS5keGZ0eXBlKCkgPT0gIkxJTkUiOgogICAgICAgICAgICBjaGFpbnMuYXBwZW5kKChGYWxzZSwgWyhlLmR4Zi5zdGFydC54LCBlLmR4Zi5zdGFydC55KSwgKGUuZHhmLmVuZC54LCBlLmR4Zi5lbmQueSldKSkKICAgICAgICBlbGlm"
"IGUuZHhmdHlwZSgpID09ICJMV1BPTFlMSU5FIjoKICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgcHRzID0gWyh2LngsIHYueSkgZm9yIHYgaW4gZXpwYXRoLm1ha2VfcGF0aChlKS5mbGF0dGVuaW5nKDAuNSldCiAgICAgICAgICAgIGV4Y2VwdCBFeGNl"
"cHRpb246CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBpZiBsZW4ocHRzKSA8IDI6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBjbG9zZWQgPSBib29sKGUuY2xvc2VkKQogICAgICAgICAgICBpZiBtYXRoLmRpc3QocHRz"
"WzBdLCBwdHNbLTFdKSA8IDEuMDoKICAgICAgICAgICAgICAgIGNsb3NlZCA9IFRydWUKICAgICAgICAgICAgICAgIHB0cyA9IHB0c1s6LTFdCiAgICAgICAgICAgIGlmIGxlbihwdHMpID49IDI6CiAgICAgICAgICAgICAgICBjaGFpbnMuYXBwZW5kKChjbG9zZWQs"
"IHB0cykpCiAgICByZXR1cm4gY2hhaW5zCgoKZGVmIGRvY19uZXQobXNwLCB0aGVtX2tpbmg9KCkpOgogICAgIiIiRG9hbiB0aGFuZyBuZW4gcGhhbiBsb3AgdHJhdCAvIHR1b25nIC8gYmF1IC8ga2luaCBjaG8gY2hpbmhfaGluaCAodGhlbyBjaGguTE9QOyB0aGVt"
"X2tpbmg6IGxheWVyIGN1YSAvIGN1YSBzbyBjdWEKICAgIGJhbiB2ZSwgdmkgZHUgQS1HbGF6LCBBLVdpbmRvdyBjdWEgdHVvbmcgQUNBIGRhIG5vKS4gS2UgY2EgbmV0IHRyb25nIGJsb2NrL3hyZWYuIiIiCiAgICBsb3AgPSB7bDogayBmb3IgaywgdiBpbiBjaGgu"
"TE9QLml0ZW1zKCkgZm9yIGwgaW4gdn0KICAgIGZvciB4IGluIHRoZW1fa2luaDoKICAgICAgICBsb3Auc2V0ZGVmYXVsdChsYXllcl9nb2MoeCksICJraW5oIikKICAgIG91dCA9IFtdCiAgICBmb3IgZSBpbiB3YWxrKG1zcCk6CiAgICAgICAgaWYgZS5keGZ0eXBl"
"KCkgbm90IGluICgiTElORSIsICJMV1BPTFlMSU5FIiwgIlBPTFlMSU5FIik6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgayA9IGxvcC5nZXQobGF5ZXJfZ29jKGUuZHhmLmxheWVyKSkKICAgICAgICBpZiBrIGlzIE5vbmU6CiAgICAgICAgICAgIGNvbnRp"
"bnVlCiAgICAgICAgdHJ5OgogICAgICAgICAgICBwdHMgPSBbKHYueCwgdi55KSBmb3IgdiBpbiBlenBhdGgubWFrZV9wYXRoKGUpLmZsYXR0ZW5pbmcoMS4wKV0KICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGZv"
"ciAoeDEsIHkxKSwgKHgyLCB5MikgaW4gemlwKHB0cywgcHRzWzE6XSk6CiAgICAgICAgICAgIGlmIG1hdGguZGlzdCgoeDEsIHkxKSwgKHgyLCB5MikpID49IDAuNToKICAgICAgICAgICAgICAgIG91dC5hcHBlbmQoKHgxLCB5MSwgeDIsIHkyLCBrKSkKICAgIHJl"
"dHVybiBvdXQKCgpkZWYgdGFvX2NoaW5oKG1zcCwgYSk6CiAgICAiIiJIYW0gY2hpbmggaGluaCBwb2x5Z29uIHBob25nIHRoZW8gdGhhbSBzbyBkb25nIGxlbmg6IGNoaW5oKGcsIHRlbikgLT4gKGcsIGRlbSkuIE5vbmUgbmV1IC0ta2hvbmctY2hpbmgtaGluaC4i"
"IiIKICAgIGlmIGEua2hvbmdfY2hpbmhfaGluaDoKICAgICAgICByZXR1cm4gTm9uZQogICAgbmV0ID0gY2hoLk5ldE5lbihkb2NfbmV0KG1zcCwgW3guc3RyaXAoKSBmb3IgeCBpbiBhLmxheWVyX2N1YS5zcGxpdCgiLCIpIGlmIHguc3RyaXAoKV0pKQogICAgcmVf"
"d2MgPSByZS5jb21waWxlKGEudGVuX3djLCByZS5JKQoKICAgIGRlZiBjaGluaChnLCB0ZW4pOgogICAgICAgIGsgPSBib19kYXUodGVuKQogICAgICAgIHJldHVybiBjaGguY2hpbmhfcGhvbmcoZywgbmV0LCB3Yz1ib29sKHJlX3djLnNlYXJjaChrKSksIGxvX2dp"
"YT1ib29sKFJFX0xPX0dJQS5zZWFyY2goaykpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgb3A9YS5vcF93YywgdHJhdD1hLnRyYXRfZGF1X3R1b25nKQogICAgY2hpbmgubmV0ID0gbmV0CiAgICByZXR1cm4gY2hpbmgKCgpkZWYgdGhlbV90aGFtX3Nv"
"X2NoaW5oKGFwKToKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1raG9uZy1jaGluaC1oaW5oIiwgYWN0aW9uPSJzdG9yZV90cnVlIiwgaGVscD0iYm8gY2FjIGJ1b2MgY2hpbmggaGluaCBsb2kgMS03ICgwOC8xMC8yMDI2KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0t"
"b3Atd2MiLCB0eXBlPWZsb2F0LCBkZWZhdWx0PTEwLjAsIGhlbHA9ImJlIGRheSBsb3Agb3AgdHVvbmcgV0MgdHJ1IHZhbyAobW0pIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS10cmF0LWRhdS10dW9uZyIsIHR5cGU9ZmxvYXQsIGRlZmF1bHQ9MTUuMCwgaGVscD0i"
"bG9wIHRyYXQgbyBtYXQgZGF1IHR1b25nICg8PSAzNTAgbW0pIGNodWEgdmUgdHJhdCAobW0pIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS10ZW4td2MiLCBkZWZhdWx0PVRFTl9XQywgaGVscD0icmVnZXggKGtob25nIGRhdSkgdGVuIHBob25nIHZlIHNpbmgiKQoK"
"CmRlZiB1bml0KGEsIGIpOgogICAgbiA9IG1hdGguZGlzdChhLCBiKQogICAgcmV0dXJuIE5vbmUgaWYgbiA8IDFlLTkgZWxzZSAoKGJbMF0gLSBhWzBdKSAvIG4sIChiWzFdIC0gYVsxXSkgLyBuKQoKCmRlZiBtYWtlX3JheXMoY2hhaW5zKToKICAgICIiIkNhYyAn"
"dGlhIGtlbyBkYWknIHRhaSBkYXUgbXV0IHZhIHRhaSBnb2MgbWEgY3VhIChnb2MgfjkwIGRvIHZvaSBkb2FuIG5nYW4gPD0gUkVUX01BWCkuIiIiCiAgICByYXlzID0gW10KICAgIGZvciBjbG9zZWQsIHB0cyBpbiBjaGFpbnM6CiAgICAgICAgbiA9IGxlbihwdHMp"
"CiAgICAgICAgZm9yIGksIHAgaW4gZW51bWVyYXRlKHB0cyk6CiAgICAgICAgICAgIHByZXYgPSBwdHNbaSAtIDFdIGlmIChpID4gMCBvciBjbG9zZWQpIGVsc2UgTm9uZQogICAgICAgICAgICBueHQgPSBwdHNbKGkgKyAxKSAlIG5dIGlmIChpIDwgbiAtIDEgb3Ig"
"Y2xvc2VkKSBlbHNlIE5vbmUKICAgICAgICAgICAgaWYgcHJldiBpcyBub3QgTm9uZSBhbmQgbnh0IGlzIE5vbmU6CiAgICAgICAgICAgICAgICBkID0gdW5pdChwcmV2LCBwKQogICAgICAgICAgICAgICAgaWYgZDoKICAgICAgICAgICAgICAgICAgICByYXlzLmFw"
"cGVuZCgocCwgZCwgImRhdSIpKQogICAgICAgICAgICBlbGlmIG54dCBpcyBub3QgTm9uZSBhbmQgcHJldiBpcyBOb25lOgogICAgICAgICAgICAgICAgZCA9IHVuaXQobnh0LCBwKQogICAgICAgICAgICAgICAgaWYgZDoKICAgICAgICAgICAgICAgICAgICByYXlz"
"LmFwcGVuZCgocCwgZCwgImRhdSIpKQogICAgICAgICAgICBlbGlmIHByZXYgaXMgbm90IE5vbmUgYW5kIG54dCBpcyBub3QgTm9uZToKICAgICAgICAgICAgICAgIGQxLCBkMiA9IHVuaXQocHJldiwgcCksIHVuaXQocCwgbnh0KQogICAgICAgICAgICAgICAgaWYg"
"ZDEgaXMgTm9uZSBvciBkMiBpcyBOb25lOgogICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICBpZiBhYnMoZDFbMF0gKiBkMlswXSArIGQxWzFdICogZDJbMV0pIDwgMC4yOiAgICMgZ29jIH45MCBkbwogICAgICAgICAgICAgICAgICAg"
"IGwxLCBsMiA9IG1hdGguZGlzdChwcmV2LCBwKSwgbWF0aC5kaXN0KHAsIG54dCkKICAgICAgICAgICAgICAgICAgICBpZiBtaW4obDEsIGwyKSA8PSBSRVRfTUFYOgogICAgICAgICAgICAgICAgICAgICAgICAjIGdvYyBtYSBjdWE6IGtlbyBkYWkgY2EgaGFpIGNh"
"bmgsIGJ1b2MgZ2hlcCBzZSBsb2MgY2FuaCBuYW8gdGhhbmcgaGFuZyB2b2kgZGF1IGRvaSBkaWVuCiAgICAgICAgICAgICAgICAgICAgICAgIHJheXMuYXBwZW5kKChwLCBkMSwgImdvYyIpKQogICAgICAgICAgICAgICAgICAgICAgICByYXlzLmFwcGVuZCgocCwg"
"KC1kMlswXSwgLWQyWzFdKSwgImdvYyIpKQogICAgcmV0dXJuIHJheXMKCgpkZWYgcGFpcl9yYXlzKHJheXMsIGdhcF9tYXgsIGJhcnJpZXI9Tm9uZSk6CiAgICAiIiJHaGVwIGNhYyB0aWEgZG9pIGRpZW4sIHRoYW5nIGhhbmcsIGNhY2ggbmhhdSA8PSBnYXBfbWF4"
"IHRoYW5oIGRvYW4gZG9uZy4KCiAgICBiYXJyaWVyOiBoaW5oIGhvYyBjYWMgbmV0IHJhbmg7IGRvYW4gZG9uZyBjYXQgcXVhIG5ldCByYW5oIChraG9uZyBjaGkgY2hhbSBvIGhhaSBkYXUpIGJpIGxvYWkuCiAgICAiIiIKICAgICMgY2hpIHhldCBjYXAgdGlhIHRy"
"b25nIGJhbiBraW5oIGdhcF9tYXggKFNUUnRyZWUpIC0gbWF0IGJhbmcgY2EgdGFuZyBjbyBoYW5nIGNodWMgbmdoaW4gdGlhLCBkdXlldCBoZXQgY2FwIHF1YSBjaGFtOwogICAgIyB0aHUgdHUgZHV5ZXQgKGkgdGFuZywgaiB0YW5nKSB2YSB0aWV1IGNoaSBnaGVw"
"IGdpdSBuZ3V5ZW4gbmVuIGtldCBxdWEga2hvbmcgZG9pCiAgICBpZiBub3QgcmF5czoKICAgICAgICByZXR1cm4gW10KICAgIGdvY190aWEgPSBzaGFwZWx5LnBvaW50cyhbclswXSBmb3IgciBpbiByYXlzXSkKICAgIGNheSA9IHNoYXBlbHkuU1RSdHJlZShnb2Nf"
"dGlhKQogICAgaWYgYmFycmllciBpcyBub3QgTm9uZToKICAgICAgICBzaGFwZWx5LnByZXBhcmUoYmFycmllcikKICAgICMgYmFycmllcjogY2F5IFNUUnRyZWUgY2FjIHBoYW4gdHUgKGludGVyc2VjdHMgdHJlbiBoaW5oIGdvcCBsb24gcmF0IGNoYW06IG1hdCBi"
"YW5nIGNhIHRhbmcgfjAsNiBtcy9sYW4pCiAgICBjYXlfYmFyID0gc2hhcGVseS5TVFJ0cmVlKHNoYXBlbHkuZ2V0X3BhcnRzKGJhcnJpZXIpKSBpZiBiYXJyaWVyIGlzIG5vdCBOb25lIGVsc2UgTm9uZQoKICAgIGRlZiBjYXRfbmV0KGcpOgogICAgICAgIHJldHVy"
"biBsZW4oY2F5X2Jhci5xdWVyeShnLCBwcmVkaWNhdGU9ImludGVyc2VjdHMiKSkgPiAwCgogICAgY2FuZHMgPSBbXQogICAgZm9yIGksIChwLCBkLCBfKSBpbiBlbnVtZXJhdGUocmF5cyk6CiAgICAgICAgZm9yIGogaW4gc29ydGVkKGludChrKSBmb3IgayBpbiBj"
"YXkucXVlcnkoZ29jX3RpYVtpXSwgcHJlZGljYXRlPSJkd2l0aGluIiwgZGlzdGFuY2U9Z2FwX21heCkgaWYgayA+IGkpOgogICAgICAgICAgICBxLCBlMiwgXyA9IHJheXNbal0KICAgICAgICAgICAgZGlzdCA9IG1hdGguZGlzdChwLCBxKQogICAgICAgICAgICBp"
"ZiBkaXN0IDwgMC41IG9yIGRpc3QgPiBnYXBfbWF4OgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgdngsIHZ5ID0gcVswXSAtIHBbMF0sIHFbMV0gLSBwWzFdCiAgICAgICAgICAgIGlmICh2eCAqIGRbMF0gKyB2eSAqIGRbMV0pID4gMCBhbmQg"
"LSh2eCAqIGUyWzBdICsgdnkgKiBlMlsxXSkgPiAwIFwKICAgICAgICAgICAgICAgICAgICBhbmQgYWJzKC12eCAqIGRbMV0gKyB2eSAqIGRbMF0pIDw9IFRPTF9USEFORyBhbmQgYWJzKHZ4ICogZTJbMV0gLSB2eSAqIGUyWzBdKSA8PSBUT0xfVEhBTkc6CiAgICAg"
"ICAgICAgICAgICBpZiBiYXJyaWVyIGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgICAgICMgY2hpIHRpbmggcGhhbiBnaXVhIGN1YSBkb2FuLCBibyAzIG1tIG1vaSBkYXUgZGUga2hvbmcgYmkgdGluaCBjaGFtIHZhbyBjaGluaCBuZXQgcmFuaAogICAgICAg"
"ICAgICAgICAgICAgIGxuID0gTGluZVN0cmluZyhbcCwgcV0pCiAgICAgICAgICAgICAgICAgICAgaW5uZXIgPSBMaW5lU3RyaW5nKFtsbi5pbnRlcnBvbGF0ZSgzLjApLCBsbi5pbnRlcnBvbGF0ZShkaXN0IC0gMy4wKV0pIGlmIGRpc3QgPiA4IGVsc2UgbG4KICAg"
"ICAgICAgICAgICAgICAgICBpZiBjYXRfbmV0KGlubmVyKToKICAgICAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgICAgIGNhbmRzLmFwcGVuZCgoZGlzdCwgaSwgaikpCiAgICBjYW5kcy5zb3J0KCkKICAgIHVzZWQsIG91dCA9IHNldCgp"
"LCBbXQogICAgZm9yIGRpc3QsIGksIGogaW4gY2FuZHM6CiAgICAgICAgaWYgaSBpbiB1c2VkIG9yIGogaW4gdXNlZDoKICAgICAgICAgICAgY29udGludWUKICAgICAgICB1c2VkLmFkZChpKQogICAgICAgIHVzZWQuYWRkKGopCiAgICAgICAgb3V0LmFwcGVuZCgo"
"cmF5c1tpXVswXSwgcmF5c1tqXVswXSwgZGlzdCkpCiAgICAjIEdvYyBobyBuaG86IGRhdSBtdXQgY3VhIG1vdCBuZXQgbmFtIG5nYXkgdHJlbiBkdW9uZyBrZW8gZGFpIGN1YSBkYXUgbXV0IG5ldCB2dW9uZyBnb2Mgdm9pIG5vIChraGUgPD0gR0FQX0dPQyksCiAg"
"ICAjIHZpIGR1IGhvcCBreSB0aHVhdCBjbyBuZXQgbmdvYWkga2hvbmcgY2hhbSBuaGF1IG8gZ29jLiBEb25nIGJhbmcgZG9hbiB0aGFuZy4KICAgIGZvciBpLCAocCwgZCwgaykgaW4gZW51bWVyYXRlKHJheXMpOgogICAgICAgIGlmIGsgIT0gImRhdSIgb3IgaSBp"
"biB1c2VkOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGJlc3QgPSBOb25lCiAgICAgICAgZm9yIGogaW4gc29ydGVkKGludChrKSBmb3IgayBpbiBjYXkucXVlcnkoZ29jX3RpYVtpXSwgcHJlZGljYXRlPSJkd2l0aGluIiwgZGlzdGFuY2U9R0FQX0dPQykp"
"OgogICAgICAgICAgICBxLCBfZTIsIGsyID0gcmF5c1tqXQogICAgICAgICAgICBpZiBqID09IGkgb3IgazIgIT0gImRhdSI6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBkaXN0ID0gbWF0aC5kaXN0KHAsIHEpCiAgICAgICAgICAgIGlmIGRp"
"c3QgPCAwLjUgb3IgZGlzdCA+IEdBUF9HT0M6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICB2eCwgdnkgPSBxWzBdIC0gcFswXSwgcVsxXSAtIHBbMV0KICAgICAgICAgICAgaWYgKHZ4ICogZFswXSArIHZ5ICogZFsxXSkgPiAwIGFuZCBhYnMo"
"LXZ4ICogZFsxXSArIHZ5ICogZFswXSkgPD0gVE9MX1RIQU5HOgogICAgICAgICAgICAgICAgaWYgYmFycmllciBpcyBub3QgTm9uZSBhbmQgZGlzdCA+IDg6CiAgICAgICAgICAgICAgICAgICAgbG4gPSBMaW5lU3RyaW5nKFtwLCBxXSkKICAgICAgICAgICAgICAg"
"ICAgICBpZiBjYXRfbmV0KExpbmVTdHJpbmcoW2xuLmludGVycG9sYXRlKDMuMCksIGxuLmludGVycG9sYXRlKGRpc3QgLSAzLjApXSkpOgogICAgICAgICAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgaWYgYmVzdCBpcyBOb25lIG9yIGRp"
"c3QgPCBiZXN0WzBdOgogICAgICAgICAgICAgICAgICAgIGJlc3QgPSAoZGlzdCwgaikKICAgICAgICBpZiBiZXN0OgogICAgICAgICAgICB1c2VkLmFkZChpKQogICAgICAgICAgICBvdXQuYXBwZW5kKChwLCByYXlzW2Jlc3RbMV1dWzBdLCBiZXN0WzBdKSkKICAg"
"IHJldHVybiBvdXQKCgpkZWYgc25hcF9icmlkZ2VzKGNoYWlucyk6CiAgICAiIiJEb25nIGtoZSBobyByYXQgbmhvICg8PSBTTkFQKTogZGF1IG11dCBjaGFtIGdhbiBuZXQga2hhYyBuaHVuZyBraG9uZyBjaHVuZyBkaW5oLiIiIgogICAgc2VncyA9IFtMaW5lU3Ry"
"aW5nKHB0cyArIChbcHRzWzBdXSBpZiBjbG9zZWQgZWxzZSBbXSkpIGZvciBjbG9zZWQsIHB0cyBpbiBjaGFpbnNdCiAgICBvdXQgPSBbXQogICAgZW5kcyA9IFtwdHNbMF0gZm9yIGNsb3NlZCwgcHRzIGluIGNoYWlucyBpZiBub3QgY2xvc2VkXSArIFtwdHNbLTFd"
"IGZvciBjbG9zZWQsIHB0cyBpbiBjaGFpbnMgaWYgbm90IGNsb3NlZF0KICAgIGNheSA9IHNoYXBlbHkuU1RSdHJlZShzZWdzKSBpZiBzZWdzIGVsc2UgTm9uZQogICAgZm9yIHAgaW4gZW5kczoKICAgICAgICBQID0gUG9pbnQocCkKICAgICAgICBiZXN0ID0gTm9u"
"ZQogICAgICAgIGdhbiA9IHNvcnRlZChpbnQoaykgZm9yIGsgaW4gY2F5LnF1ZXJ5KFAsIHByZWRpY2F0ZT0iZHdpdGhpbiIsIGRpc3RhbmNlPVNOQVApKSBpZiBjYXkgaXMgbm90IE5vbmUgZWxzZSBbXQogICAgICAgIGZvciBzIGluIChzZWdzW2tdIGZvciBrIGlu"
"IGdhbik6CiAgICAgICAgICAgIGQgPSBzLmRpc3RhbmNlKFApCiAgICAgICAgICAgIGlmIDFlLTYgPCBkIDw9IFNOQVAgYW5kIChiZXN0IGlzIE5vbmUgb3IgZCA8IGJlc3RbMF0pOgogICAgICAgICAgICAgICAgYSA9IHMuaW50ZXJwb2xhdGUocy5wcm9qZWN0KFAp"
"KQogICAgICAgICAgICAgICAgYmVzdCA9IChkLCAoYS54LCBhLnkpKQogICAgICAgIGlmIGJlc3Q6CiAgICAgICAgICAgIG91dC5hcHBlbmQoTGluZVN0cmluZyhbcCwgYmVzdFsxXV0pKQogICAgcmV0dXJuIG91dAoKCmRlZiBfZG9hbl9jdWEoZW50aXRpZXMpOgog"
"ICAgIiIiQ2FjIGRvYW4gdGhhbmcgKGEsIGIpIGN1YSBtb3QgY3VhL2N1YSBzbzsgQVJDIChjdW5nIHF1YXkgY2FuaCkgYmkgYm8uIFRyYSB2ZSAoZG9hbiwgc29fY3VuZykuIiIiCiAgICBvdXQsIG5fYXJjID0gW10sIDAKICAgIGZvciBlIGluIGVudGl0aWVzOgog"
"ICAgICAgIHQgPSBlLmR4ZnR5cGUoKQogICAgICAgIGlmIHQgPT0gIkxJTkUiOgogICAgICAgICAgICBvdXQuYXBwZW5kKCgoZS5keGYuc3RhcnQueCwgZS5keGYuc3RhcnQueSksIChlLmR4Zi5lbmQueCwgZS5keGYuZW5kLnkpKSkKICAgICAgICBlbGlmIHQgPT0g"
"IkxXUE9MWUxJTkUiOgogICAgICAgICAgICBwdHMgPSBbKHYueCwgdi55KSBmb3IgdiBpbiBlLnZlcnRpY2VzX2luX3djcygpXSAgICAgIyBXQ1M6IGN1YSBjaGVuIGxhdCBndW9uZyBjbyBleHRydXNpb24gKDAsMCwtMSkKICAgICAgICAgICAgaWYgZS5jbG9zZWQg"
"YW5kIGxlbihwdHMpID4gMjoKICAgICAgICAgICAgICAgIHB0cy5hcHBlbmQocHRzWzBdKQogICAgICAgICAgICBvdXQgKz0gWyhwdHNbaV0sIHB0c1tpICsgMV0pIGZvciBpIGluIHJhbmdlKGxlbihwdHMpIC0gMSkgaWYgbWF0aC5kaXN0KHB0c1tpXSwgcHRzW2kg"
"KyAxXSkgPiAwLjVdCiAgICAgICAgZWxpZiB0IGluICgiQVJDIiwgIkNJUkNMRSIsICJFTExJUFNFIiwgIlNQTElORSIpOgogICAgICAgICAgICBuX2FyYyArPSAxCiAgICByZXR1cm4gb3V0LCBuX2FyYwoKCmRlZiBfbmhvbV9jdWEoZW50aXRpZXMsIHdhbnQsIGRl"
"cHRoPTAsIG1heF9kZXB0aD0zKToKICAgICIiIk1vaSBJTlNFUlQgdHJlbiBsYXllciBjdWEvY3VhIHNvIGxhIE1PVCBjdWEgKHNpbmggbGlzdCBkb2kgdHVvbmcgY29uIGRhIHRyYWkgcGhhbmcpOyBkaSBzYXUgdmFvIGJsb2NrL3hyZWYga2hhYy4iIiIKICAgIGZv"
"ciBlIGluIGVudGl0aWVzOgogICAgICAgIGlmIGUuZHhmdHlwZSgpICE9ICJJTlNFUlQiOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGlmIGRlcHRoID49IG1heF9kZXB0aCBvciAoX0JPX1FVQVswXSBpcyBub3QgTm9uZSBhbmQgX0JPX1FVQVswXS5zZWFy"
"Y2goZS5keGYubmFtZSBvciAiIikpOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHRyeToKICAgICAgICAgICAgc3VicyA9IGxpc3QoZS52aXJ0dWFsX2VudGl0aWVzKCkpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgY29udGludWUK"
"ICAgICAgICBpZiBsYXllcl9nb2MoZS5keGYubGF5ZXIpIGluIHdhbnQ6CiAgICAgICAgICAgIGZsYXQsIHN0YWNrID0gW10sIHN1YnMKICAgICAgICAgICAgd2hpbGUgc3RhY2s6CiAgICAgICAgICAgICAgICBzID0gc3RhY2sucG9wKCkKICAgICAgICAgICAgICAg"
"IGlmIHMuZHhmdHlwZSgpID09ICJJTlNFUlQiOgogICAgICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICAgICAgc3RhY2sgKz0gbGlzdChzLnZpcnR1YWxfZW50aXRpZXMoKSkKICAgICAgICAgICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9u"
"OgogICAgICAgICAgICAgICAgICAgICAgICBwYXNzCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIGZsYXQuYXBwZW5kKHMpCiAgICAgICAgICAgIHlpZWxkIGZsYXQKICAgICAgICBlbHNlOgogICAgICAgICAgICB5aWVsZCBmcm9tIF9u"
"aG9tX2N1YShzdWJzLCB3YW50LCBkZXB0aCArIDEsIG1heF9kZXB0aCkKCgpkZWYgZG9jX2todW5nX2N1YShtc3AsIGNoYWlucywgbGF5ZXJzX2N1YSk6CiAgICAiIiJOZXQgYmFvIGtodW5nIGN1YSBkaSAvIGN1YSBzbyBsYW0gcmFuaCBwaG9uZy4KCiAgICBWb2kg"
"bW9pIGN1YSAoSU5TRVJUIHRyZW4gbGF5ZXIgY3VhKTogaHVvbmcgdHVvbmcgPSBodW9uZyB0cm9pIGN1YSBjYWMgbmV0IHR1b25nIHF1YW5oIGN1YTsgZGFpIHR1b25nID0ga2hvYW5nIGdpdWEKICAgIGhhaSBtYXQgdHVvbmcgbmdvYWkgY3VuZyBzb25nIHNvbmcs"
"IG5hbSBoYWkgYmVuIHRydWMgY3VhICg8PSBEQVlfVFVPTkdfVE9JX0RBKS4gQ2hpIGdpdSBjYWMgZG9hbiBjdWEgY28gY2EgaGFpIGRhdSBuYW0KICAgIHRyb25nIGRhaSB0dW9uZyAoa2h1bmcsIGtpbmgsIGNhbmggZG9uZykuIENhbmggY3VhIG1vIHJhIHBob25n"
"ICh2dW90IHJhIG5nb2FpIGRhaSB0dW9uZykgdmEgY3VuZyBxdWF5IGNhbmggYmkgYm8uCiAgICBLaG9uZyB0aW0gZHVvYyBkYWkgdHVvbmcgKGN1YSBkdW5nIHR1IGRvLCBraG9uZyBjbyB0dW9uZyk6IGdpdSBkb2FuIHNvbmcgc29uZyBodW9uZyBjdWEgdmEgZG9h"
"biBuZ2FuIDw9IFJFVF9NQVguCiAgICAiIiIKICAgIHdhbnQgPSB7bGF5ZXJfZ29jKHgpIGZvciB4IGluIGxheWVyc19jdWF9CiAgICBpZiBub3Qgd2FudDoKICAgICAgICByZXR1cm4gW10sIGRpY3Qoc29fY3VhPTApCiAgICB3YWxsID0gW10KICAgIGZvciBjbG9z"
"ZWQsIHB0cyBpbiBjaGFpbnM6CiAgICAgICAgcSA9IHB0cyArIChbcHRzWzBdXSBpZiBjbG9zZWQgZWxzZSBbXSkKICAgICAgICB3YWxsICs9IFtMaW5lU3RyaW5nKFtxW2ldLCBxW2kgKyAxXV0pIGZvciBpIGluIHJhbmdlKGxlbihxKSAtIDEpIGlmIG1hdGguZGlz"
"dChxW2ldLCBxW2kgKyAxXSkgPiAwLjVdCiAgICB0cmVlID0gc2hhcGVseS5TVFJ0cmVlKHdhbGwpIGlmIHdhbGwgZWxzZSBOb25lCiAgICBvdXQsIHNvX2N1YSwgYm9fY2FuaCwgYm9fY3VuZywga2hvbmdfZGFpID0gW10sIDAsIDAsIDAsIDAKCiAgICBkZWYgZ29j"
"KGEsIGIpOgogICAgICAgIHJldHVybiBtYXRoLmRlZ3JlZXMobWF0aC5hdGFuMihiWzFdIC0gYVsxXSwgYlswXSAtIGFbMF0pKSAlIDE4MC4wCgogICAgZGVmIGN1bmdfaHVvbmcoZzEsIGcyLCB0b2w9My4wKToKICAgICAgICBkID0gYWJzKGcxIC0gZzIpICUgMTgw"
"LjAKICAgICAgICByZXR1cm4gbWluKGQsIDE4MC4wIC0gZCkgPD0gdG9sCgogICAgZm9yIGVudHMgaW4gX25ob21fY3VhKG1zcCwgd2FudCk6CiAgICAgICAgZG9hbiwgbl9hcmMgPSBfZG9hbl9jdWEoZW50cykKICAgICAgICBpZiBub3QgZG9hbjoKICAgICAgICAg"
"ICAgY29udGludWUKICAgICAgICBzb19jdWEgKz0gMQogICAgICAgIGJvX2N1bmcgKz0gbl9hcmMKICAgICAgICB4cyA9IFtwWzBdIGZvciBzIGluIGRvYW4gZm9yIHAgaW4gc10KICAgICAgICB5cyA9IFtwWzFdIGZvciBzIGluIGRvYW4gZm9yIHAgaW4gc10KICAg"
"ICAgICB2dW5nID0gc2hhcGVseS5ib3gobWluKHhzKSAtIDUwLCBtaW4oeXMpIC0gNTAsIG1heCh4cykgKyA1MCwgbWF4KHlzKSArIDUwKQogICAgICAgIGdhbiA9IFt3YWxsW2ldIGZvciBpIGluIHRyZWUucXVlcnkodnVuZyldIGlmIHRyZWUgaXMgbm90IE5vbmUg"
"ZWxzZSBbXQogICAgICAgICMgaHVvbmcgdHVvbmc6IGdvYyBjbyB0b25nIGNoaWV1IGRhaSBuZXQgdHVvbmcgKGNhdCB0cm9uZyB2dW5nIGN1YSkgbG9uIG5oYXQKICAgICAgICBoaXN0ID0gZGVmYXVsdGRpY3QoZmxvYXQpCiAgICAgICAgZm9yIHcgaW4gZ2FuOgog"
"ICAgICAgICAgICBjID0gdy5pbnRlcnNlY3Rpb24odnVuZykKICAgICAgICAgICAgaWYgbm90IGMuaXNfZW1wdHkgYW5kIGMubGVuZ3RoID4gMToKICAgICAgICAgICAgICAgICh4MCwgeTApLCAoeDEsIHkxKSA9IHcuY29vcmRzWzBdLCB3LmNvb3Jkc1stMV0KICAg"
"ICAgICAgICAgICAgIGhpc3Rbcm91bmQoZ29jKCh4MCwgeTApLCAoeDEsIHkxKSkpICUgMTgwXSArPSBjLmxlbmd0aAogICAgICAgIGlmIG5vdCBoaXN0OgogICAgICAgICAgICBmb3IgYV8sIGJfIGluIGRvYW46CiAgICAgICAgICAgICAgICBoaXN0W3JvdW5kKGdv"
"YyhhXywgYl8pKSAlIDE4MF0gKz0gbWF0aC5kaXN0KGFfLCBiXykKICAgICAgICBnMCA9IG1heChoaXN0LCBrZXk9aGlzdC5nZXQpCiAgICAgICAgdXgsIHV5ID0gbWF0aC5jb3MobWF0aC5yYWRpYW5zKGcwKSksIG1hdGguc2luKG1hdGgucmFkaWFucyhnMCkpCiAg"
"ICAgICAgbngsIG55ID0gLXV5LCB1eAogICAgICAgIG9mZiA9IGxhbWJkYSBwOiBwWzBdICogbnggKyBwWzFdICogbnkgICAgICAgIyBub3FhOiBFNzMxCiAgICAgICAgZGwgPSBsYW1iZGEgcDogcFswXSAqIHV4ICsgcFsxXSAqIHV5ICAgICAgICMgbm9xYTogRTcz"
"MQogICAgICAgIHNzID0gW3MgZm9yIHMgaW4gZG9hbiBpZiBjdW5nX2h1b25nKGdvYygqcyksIGcwKV0KICAgICAgICBpZiBzczoKICAgICAgICAgICAgd18gPSBzb3J0ZWQoKG9mZigoKHNbMF1bMF0gKyBzWzFdWzBdKSAvIDIsIChzWzBdWzFdICsgc1sxXVsxXSkg"
"LyAyKSksIG1hdGguZGlzdCgqcykpIGZvciBzIGluIHNzKQogICAgICAgICAgICBoYWxmLCBhY2MsIGMwID0gc3VtKEwgZm9yIF8sIEwgaW4gd18pIC8gMiwgMC4wLCB3X1swXVswXQogICAgICAgICAgICBmb3IgbywgTCBpbiB3XzoKICAgICAgICAgICAgICAgIGFj"
"YyArPSBMCiAgICAgICAgICAgICAgICBpZiBhY2MgPj0gaGFsZjoKICAgICAgICAgICAgICAgICAgICBjMCA9IG8KICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGMwID0gb2ZmKCgobWluKHhzKSArIG1heCh4cykpIC8g"
"MiwgKG1pbih5cykgKyBtYXgoeXMpKSAvIDIpKQogICAgICAgIHRfbWluID0gbWluKGRsKHApIGZvciBzIGluIGRvYW4gZm9yIHAgaW4gcykKICAgICAgICB0X21heCA9IG1heChkbChwKSBmb3IgcyBpbiBkb2FuIGZvciBwIGluIHMpCiAgICAgICAgb2ZmcyA9IFtd"
"CiAgICAgICAgZm9yIHcgaW4gKHdhbGxbaV0gZm9yIGkgaW4gdHJlZS5xdWVyeSh2dW5nLmJ1ZmZlcihEQVlfVFVPTkdfVE9JX0RBKSkpIGlmIHRyZWUgaXMgbm90IE5vbmUgZWxzZSBbXToKICAgICAgICAgICAgcDAsIHAxID0gdy5jb29yZHNbMF0sIHcuY29vcmRz"
"Wy0xXQogICAgICAgICAgICBpZiBub3QgY3VuZ19odW9uZyhnb2MocDAsIHAxKSwgZzApOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgbyA9IG9mZihwMCkKICAgICAgICAgICAgaWYgYWJzKG8gLSBjMCkgPiBEQVlfVFVPTkdfVE9JX0RBOgog"
"ICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgYTAsIGExID0gc29ydGVkKChkbChwMCksIGRsKHAxKSkpCiAgICAgICAgICAgIGlmIGExIDwgdF9taW4gLSA1MCBvciBhMCA+IHRfbWF4ICsgNTA6ICAgICAjIG5ldCB0dW9uZyBwaGFpIG5hbSBuZ2Fu"
"ZyBxdWEgaG9hYyBjaGFtIGRhdSBjdWEKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIG9mZnMuYXBwZW5kKG8pCiAgICAgICAgdHJlbiA9IFtvIGZvciBvIGluIG9mZnMgaWYgbyA+PSBjMCAtIDFdCiAgICAgICAgZHVvaSA9IFtvIGZvciBvIGlu"
"IG9mZnMgaWYgbyA8PSBjMCArIDFdCiAgICAgICAgZGFpID0gKG1pbihkdW9pICsgW2MwXSkgaWYgZHVvaSBlbHNlIE5vbmUsIG1heCh0cmVuICsgW2MwXSkgaWYgdHJlbiBlbHNlIE5vbmUpCiAgICAgICAgY29fZGFpID0gYm9vbChkdW9pKSBhbmQgYm9vbCh0cmVu"
"KSBhbmQgZGFpWzFdIC0gZGFpWzBdID4gMjAKICAgICAgICBpZiBub3QgY29fZGFpOgogICAgICAgICAgICBraG9uZ19kYWkgKz0gMQogICAgICAgIGZvciBzIGluIGRvYW46CiAgICAgICAgICAgIGlmIGNvX2RhaToKICAgICAgICAgICAgICAgIG9rID0gYWxsKGRh"
"aVswXSAtIDE1IDw9IG9mZihwKSA8PSBkYWlbMV0gKyAxNSBmb3IgcCBpbiBzKQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgb2sgPSBjdW5nX2h1b25nKGdvYygqcyksIGcwKSBvciBtYXRoLmRpc3QoKnMpIDw9IFJFVF9NQVgKICAgICAgICAgICAg"
"aWYgb2s6CiAgICAgICAgICAgICAgICBvdXQuYXBwZW5kKExpbmVTdHJpbmcocykpCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBib19jYW5oICs9IDEKICAgIHJldHVybiBvdXQsIGRpY3Qoc29fY3VhPXNvX2N1YSwgc29fZG9hbl9raHVuZz1sZW4o"
"b3V0KSwgYm9fY2FuaF9uZ29haV90dW9uZz1ib19jYW5oLCBib19jdW5nX3F1YXk9Ym9fY3VuZywKICAgICAgICAgICAgICAgICAgICAgY3VhX2tob25nX2NvX3R1b25nPWtob25nX2RhaSkKCgpkZWYgYnVpbGRfZmFjZXMoY2hhaW5zLCBnYXBfbWF4LCBraHVuZz1O"
"b25lKToKICAgICIiImtodW5nOiBkb2FuIGtodW5nIGN1YSAoZG9jX2todW5nX2N1YSkgLSBjaGkgdGhlbSB2YW8gbHVvaSBuZXQsIEtIT05HIHNpbmggdGlhIGRvbmcgbyBjdWEgdmEga2hvbmcgY2hhbiB0aWEgZG9uZwogICAgKGNhbmgga2h1bmcgbmFtIHRyZW4g"
"bWF0IHR1b25nLCBuZXUgZHVuZyBsYW0gdmF0IGNoYW4gc2UgbGFtIGhvbmcgZG9hbiBkb25nIG8gY3VhKS4iIiIKICAgIHJheXMgPSBtYWtlX3JheXMoY2hhaW5zKQogICAgc2VncyA9IFtMaW5lU3RyaW5nKHB0cyArIChbcHRzWzBdXSBpZiBjbG9zZWQgZWxzZSBb"
"XSkpIGZvciBjbG9zZWQsIHB0cyBpbiBjaGFpbnNdCiAgICBwYWlycyA9IHBhaXJfcmF5cyhyYXlzLCBnYXBfbWF4LCB1bmFyeV91bmlvbihzZWdzKSkKICAgIGJyaWRnZXMgPSBbTGluZVN0cmluZyhbYSwgYl0pIGZvciBhLCBiLCBfIGluIHBhaXJzXSArIHNuYXBf"
"YnJpZGdlcyhjaGFpbnMpCiAgICAjIGdyaWRfc2l6ZSAwLDAxIG1tOiBkYXUgbXV0IGNoaSBsZWNoIH4xZS03IG1tIHNvIHZvaSBuZXQga2UgYmVuIHZhbiBkdW9jIGNvaSBsYSBjaGFtIChudXQgZ2lhbyB0aGF0IHN1KSwgbmV1IGtob25nCiAgICAjIHBvbHlnb25p"
"emUgc2UgY29pIGxhIGRhdSB0dSBkbyB2YSBuaGlldSBwaG9uZyBiaSBnb3AgdmFvIG5oYXUgKGxvaSBnYXAgbyBiYW4gdmUgY28gZG9pIHR1b25nIEFDQSBkYSBubykuCiAgICBub2RlZCA9IHNoYXBlbHkudW5pb25fYWxsKHNlZ3MgKyBicmlkZ2VzICsgbGlzdChr"
"aHVuZyBvciBbXSksIGdyaWRfc2l6ZT0wLjAxKQogICAgZmFjZXMgPSBsaXN0KHBvbHlnb25pemUobm9kZWQpKQogICAgcmV0dXJuIGZhY2VzLCBwYWlycywgYnJpZGdlcwoKCmRlZiB0aG9uZ19zb190ZXh0KGUsIGRvYyk6CiAgICAiIiJEb2Mgc3R5bGUsIGNhbywg"
"bGF5ZXIsIG1hdSwgZ29jIHhvYXksIHRhbSBoaW5oIGhvYyBjdWEgdGV4dCB0ZW4gcGhvbmcgZGUgZGF0IG5oYW4gZGllbiB0aWNoIG5nYXkgYmVuIGR1b2kuCgogICAgVHJhIHZlIGRpY3Q6IGtpbmQsIGxheWVyLCBzdHlsZSwgaCwgc3R5bGVfaCwgY29sb3IsIHJv"
"dCwgY3gsIGN5ICh0YW0gdGV4dCB0ZW4pLCBkIChraG9hbmcgdHUgdGFtIHRleHQgdGVuCiAgICBkZW4gdGFtIG5oYW4gPSBudWEgY2hpZXUgY2FvIGtob2kgY2h1ICsgMSBsYW4gY2FvIGNodTogbmhhbiBuYW0gZHVvaSwgY2FjaCAwLDUgbGFuIGNhbyBjaHUpLgog"
"ICAgR2hpIGNodTogY2hpZXUgcm9uZyB0ZXh0IHVvYyBsdW9uZyA9IHNvIGt5IHR1IHggMCw1NSB4IGNhbyB4IGhlIHNvIHJvbmcgKGNoaSBkdW5nIGtoaSB0ZXh0IGNhbiBsZSB0cmFpL3BoYWkpLgogICAgIiIiCiAgICBkID0gZS5keGYKICAgIHN0eWxlID0gZC5n"
"ZXQoInN0eWxlIiwgIlN0YW5kYXJkIikKICAgIHN0ID0gZG9jLnN0eWxlcy5nZXQoc3R5bGUpIGlmIHN0eWxlIGVsc2UgTm9uZQogICAgc3R5bGVfaCA9IGZsb2F0KHN0LmR4Zi5oZWlnaHQpIGlmIHN0IGlzIG5vdCBOb25lIGFuZCBzdC5keGYuaGFzYXR0cigiaGVp"
"Z2h0IikgZWxzZSAwLjAKICAgIGNvbG9yID0gZC5nZXQoImNvbG9yIiwgMjU2KQogICAgaWYgZS5keGZ0eXBlKCkgPT0gIk1URVhUIjoKICAgICAgICBoID0gZmxvYXQoZC5nZXQoImNoYXJfaGVpZ2h0IiwgMi41KSkKICAgICAgICB0eHQgPSBlLnBsYWluX3RleHQo"
"KQogICAgICAgIGxpbmVzID0gdHh0LmNvdW50KCJcbiIpICsgMQogICAgICAgIG1heGxlbiA9IG1heChsZW4ocykgZm9yIHMgaW4gdHh0LnNwbGl0KCJcbiIpKQogICAgICAgIHdmID0gZmxvYXQoc3QuZHhmLndpZHRoKSBpZiBzdCBpcyBub3QgTm9uZSBhbmQgc3Qu"
"ZHhmLmhhc2F0dHIoIndpZHRoIikgZWxzZSAxLjAKICAgICAgICB3ID0gZmxvYXQoZC5nZXQoIndpZHRoIiwgMC4wKSkgb3IgbWF4bGVuICogMC41NSAqIGggKiB3ZgogICAgICAgIGhiID0gKDEuNSAqIGxpbmVzIC0gMC41KSAqIGgKICAgICAgICB0cnk6ICAgICAg"
"ICAgICAgICAgICAgICAgICAgICAgICAgICMgZG8gYmFuZyBzbyBkbyBwaG9uZyBjaHUgdGhhdCAoVFRGKSwgY2hpbmggeGFjIGhvbiB1b2MgbHVvbmcKICAgICAgICAgICAgZnJvbSBlemR4Zi50b29scy50ZXh0X3NpemUgaW1wb3J0IG10ZXh0X3NpemUKICAgICAg"
"ICAgICAgbXMgPSBtdGV4dF9zaXplKGUpCiAgICAgICAgICAgIHcgPSBmbG9hdChkLmdldCgid2lkdGgiLCAwLjApKSBvciBtcy50b3RhbF93aWR0aAogICAgICAgICAgICBoYiA9IG1zLnRvdGFsX2hlaWdodCBvciBoYgogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246"
"CiAgICAgICAgICAgIHBhc3MKICAgICAgICBhcCA9IGludChkLmdldCgiYXR0YWNobWVudF9wb2ludCIsIDEpKQogICAgICAgIGNvbCwgcm93ID0gKGFwIC0gMSkgJSAzLCAoYXAgLSAxKSAvLyAzCiAgICAgICAgeCwgeSA9IGQuaW5zZXJ0LngsIGQuaW5zZXJ0LnkK"
"ICAgICAgICBjeCA9IHggaWYgY29sID09IDEgZWxzZSB4ICsgdyAvIDIgaWYgY29sID09IDAgZWxzZSB4IC0gdyAvIDIKICAgICAgICBjeSA9IHkgaWYgcm93ID09IDEgZWxzZSB5IC0gaGIgLyAyIGlmIHJvdyA9PSAwIGVsc2UgeSArIGhiIC8gMgogICAgICAgIHJv"
"dCA9IGZsb2F0KGQuZ2V0KCJyb3RhdGlvbiIsIDAuMCkgb3IgMC4wKQogICAgICAgIGtpbmQgPSAiTVRFWFQiCiAgICBlbHNlOgogICAgICAgIGggPSBmbG9hdChkLmhlaWdodCkKICAgICAgICB3ZiA9IGZsb2F0KGQuZ2V0KCJ3aWR0aCIsIDEuMCkpCiAgICAgICAg"
"dHh0ID0gZC50ZXh0CiAgICAgICAgdyA9IGxlbih0eHQpICogMC41NSAqIGggKiB3ZgogICAgICAgIHRyeTogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyBkbyBiYW5nIHNvIGRvIHBob25nIGNodSB0aGF0IChUVEYpLCBjaGluaCB4YWMgaG9uIHVvYyBs"
"dW9uZwogICAgICAgICAgICBmcm9tIGV6ZHhmLnRvb2xzLnRleHRfc2l6ZSBpbXBvcnQgdGV4dF9zaXplCiAgICAgICAgICAgIHcgPSB0ZXh0X3NpemUoZSkud2lkdGgKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCiAgICAgICAgaGEs"
"IHZhID0gaW50KGQuZ2V0KCJoYWxpZ24iLCAwKSksIGludChkLmdldCgidmFsaWduIiwgMCkpCiAgICAgICAgaXgsIGl5ID0gZC5pbnNlcnQueCwgZC5pbnNlcnQueQogICAgICAgIGlmIGhhIG9yIHZhOgogICAgICAgICAgICBheCwgYXkgPSBkLmFsaWduX3BvaW50"
"LngsIGQuYWxpZ25fcG9pbnQueQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGF4LCBheSA9IGl4LCBpeQogICAgICAgIGN4ID0gYXggaWYgaGEgaW4gKDEsIDQpIGVsc2UgKGl4ICsgYXgpIC8gMiBpZiBoYSBpbiAoMywgNSkgZWxzZSBheCArIHcgLyAyIGlmIGhh"
"ID09IDAgZWxzZSBheCAtIHcgLyAyCiAgICAgICAgY3kgPSBheSBpZiAodmEgPT0gMiBvciBoYSA9PSA0KSBlbHNlIGF5IC0gaCAvIDIgaWYgdmEgPT0gMyBlbHNlIGF5ICsgaCAvIDIKICAgICAgICBoYiwgbGluZXMgPSBoLCAxCiAgICAgICAgcm90ID0gZmxvYXQo"
"ZC5nZXQoInJvdGF0aW9uIiwgMC4wKSBvciAwLjApCiAgICAgICAga2luZCA9ICJURVhUIgogICAgZGQgPSBoYiAvIDIgKyBoCiAgICB0aCA9IG1hdGgucmFkaWFucyhyb3QpCiAgICByZXR1cm4gZGljdChraW5kPWtpbmQsIGxheWVyPWQubGF5ZXIsIHN0eWxlPXN0"
"eWxlLCBoPWgsIHN0eWxlX2g9c3R5bGVfaCwgY29sb3I9Y29sb3IsIHJvdD1yb3QsCiAgICAgICAgICAgICAgICBjeD1jeCwgY3k9Y3ksIGQ9ZGQsIHg9Y3ggKyBkZCAqIG1hdGguc2luKHRoKSwgeT1jeSAtIGRkICogbWF0aC5jb3ModGgpLCB3PXcsIGhiPWhiKQoK"
"CmRlZiBkb190ZXh0KGRvYywga2luZCwgc3R5bGUsIGgsIHRleHQpOgogICAgIiIiRG8gKHJvbmcsIGNhbykgY3VhIG1vdCBjaHVvaSBjaHUgdGhlbyBzdHlsZSAoZm9udCB0aOG6rXQpOyB1b2MgbHVvbmcgbmV1IGtob25nIGRvIGR1b2MuIiIiCiAgICBtc3AgPSBk"
"b2MubW9kZWxzcGFjZSgpCiAgICB0cnk6CiAgICAgICAgaWYga2luZCA9PSAiTVRFWFQiOgogICAgICAgICAgICBmcm9tIGV6ZHhmLnRvb2xzLnRleHRfc2l6ZSBpbXBvcnQgbXRleHRfc2l6ZQogICAgICAgICAgICBlID0gbXNwLmFkZF9tdGV4dCh0ZXh0LCBkeGZh"
"dHRyaWJzPXsic3R5bGUiOiBzdHlsZSwgImNoYXJfaGVpZ2h0IjogaH0pCiAgICAgICAgICAgIG1zID0gbXRleHRfc2l6ZShlKQogICAgICAgICAgICB3LCBoYiA9IG1zLnRvdGFsX3dpZHRoLCBtcy50b3RhbF9oZWlnaHQgb3IgaAogICAgICAgIGVsc2U6CiAgICAg"
"ICAgICAgIGZyb20gZXpkeGYudG9vbHMudGV4dF9zaXplIGltcG9ydCB0ZXh0X3NpemUKICAgICAgICAgICAgZSA9IG1zcC5hZGRfdGV4dCh0ZXh0LCBkeGZhdHRyaWJzPXsic3R5bGUiOiBzdHlsZSwgImhlaWdodCI6IGh9KQogICAgICAgICAgICB3LCBoYiA9IHRl"
"eHRfc2l6ZShlKS53aWR0aCwgaAogICAgICAgIG1zcC5kZWxldGVfZW50aXR5KGUpCiAgICAgICAgcmV0dXJuIHcsIGhiCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHJldHVybiBsZW4odGV4dCkgKiAwLjU1ICogaCwgaAoKCmRlZiBsZW5oX25oYW4obiwg"
"bmhhbik6CiAgICAiIiJDYWMgZG9uZyBsZW5oIC5zY3IgdmUgbW90IG5oYW4gY28gdGhvbmcgc28gbiAobGF5ZXIsIHN0eWxlLCBjYW8sIG1hdSwgZ29jIHhvYXksIHZpIHRyaSB0YW0pIHZvaSBub2kgZHVuZyBuaGFuLiIiIgogICAgTCA9IFsiXy4tTEFZRVIiLCAi"
"X00iLCBmJyJ7YWNhZF9zdHIoblsibGF5ZXIiXSl9IicsICIiXSAgICAgICAjIE1ha2U6IHRhbyBuZXUgY2h1YSBjbywgZGEgY28gdGhpIGNoaSBkYXQgaGllbiBoYW5oCiAgICBzdCA9IGYnInthY2FkX3N0cihuWyJzdHlsZSJdKX0iJwogICAgaWYgblsia2luZCJd"
"ID09ICJNVEVYVCI6CiAgICAgICAgTCArPSBbIl8uLU1URVhUIiwgZid7blsieCJdOi4yZn0se25bInkiXTouMmZ9JywgIl9TIiwgc3QsICJfSCIsIGYne25bImgiXTpnfScsICJfSiIsICJfTUMiXQogICAgICAgIGlmIGFicyhuWyJyb3QiXSkgPiAxZS02OgogICAg"
"ICAgICAgICBMICs9IFsiX1IiLCBmJ3tuWyJyb3QiXTpnfSddCiAgICAgICAgTCArPSBbIl9XIiwgIjAiLCBuaGFuLCAiIl0KICAgIGVsc2U6CiAgICAgICAgTCArPSBbIl8uLVRFWFQiLCAiX1MiLCBzdCwgIl9KIiwgIl9NQyIsIGYne25bIngiXTouMmZ9LHtuWyJ5"
"Il06LjJmfSddCiAgICAgICAgaWYgblsic3R5bGVfaCJdID09IDA6ICAgICAjIHN0eWxlIGNvIGNoaWV1IGNhbyBjbyBkaW5oIHRoaSBBdXRvQ0FEIGtob25nIGhvaSBjaGlldSBjYW8KICAgICAgICAgICAgTC5hcHBlbmQoZid7blsiaCJdOmd9JykKICAgICAgICBM"
"ICs9IFtmJ3tuWyJyb3QiXTpnfScsIG5oYW5dCiAgICBpZiBuWyJjb2xvciJdIG5vdCBpbiAoMjU2LCAwKToKICAgICAgICBMICs9IFsiXy5DSFBST1AiLCAiX0wiLCAiIiwgIl9DIiwgc3RyKG5bImNvbG9yIl0pLCAiIl0KICAgIHJldHVybiBMCgoKZGVmIGRvY19z"
"ZWVkcyhtc3AsIGxheWVyX3RlbiwgZG9jPU5vbmUpOgogICAgb3V0ID0gW10KICAgICMgVGVuIHBob25nIGNoaSBsYXkgbyBNb2RlbCAoa2hvbmcgbGF5IHRyb25nIGJsb2NrL3hyZWYpOiB0ZXh0IHRyb25nIHhyZWYgdGh1b25nIGxhIGNodSB0aGljaCwga2hvbmcg"
"cGhhaSB0ZW4gcGhvbmcuCiAgICBmb3IgZSBpbiBtc3A6CiAgICAgICAgaWYgZS5keGZ0eXBlKCkgaW4gKCJURVhUIiwgIk1URVhUIikgYW5kIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgPT0gbGF5ZXJfZ29jKGxheWVyX3Rlbik6CiAgICAgICAgICAgIGlmIGUuZHhm"
"dHlwZSgpID09ICJURVhUIjoKICAgICAgICAgICAgICAgIHAgPSBlLmR4Zi5hbGlnbl9wb2ludCBpZiAoZS5keGYuaGFsaWduIG9yIGUuZHhmLnZhbGlnbikgZWxzZSBlLmR4Zi5pbnNlcnQKICAgICAgICAgICAgICAgIHQgPSBlLmR4Zi50ZXh0CiAgICAgICAgICAg"
"IGVsc2U6CiAgICAgICAgICAgICAgICBwLCB0ID0gZS5keGYuaW5zZXJ0LCBlLnBsYWluX3RleHQoKQogICAgICAgICAgICB0ID0gKHQgb3IgIiIpLnN0cmlwKCkKICAgICAgICAgICAgaWYgdDoKICAgICAgICAgICAgICAgIGluZm8gPSBOb25lCiAgICAgICAgICAg"
"ICAgICBpZiBkb2MgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgICAgICBpbmZvID0gdGhvbmdfc29fdGV4dChlLCBkb2MpCiAgICAgICAgICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAg"
"ICAgICAgICAgICAgICAgaW5mbyA9IE5vbmUKICAgICAgICAgICAgICAgIG91dC5hcHBlbmQoKHQsIChwLngsIHAueSksIGluZm8pKQogICAgcmV0dXJuIG91dAoKCkRBWV9MT1BfVFJBVCA9IDE1LjAgICAjIG1tOiBsb3AgdHJhdCBob2FuIHRoaWVuIChnaGkgY2h1"
"IGJhbiB2ZTogIlRSQVQgSE9BTiBUSElFTiBEQVkgMTUiKQoKCmRlZiBwaGF0X2hpZW5fbG9wX3RyYXQobXNwLCBkYXk9REFZX0xPUF9UUkFUKToKICAgICIiIk7DqXQgJ0EtVnVhIHRyYXQnIFRSVU5HIHZvaSBuw6l0ICdBLVdhbGwnIChtYXQgdHVvbmcpID0gYmFu"
"IHZlIENIVUEgVkUgbG9wIHRyYXQgcmllbmc6IHRyYSB2ZSBgZGF5YCwgbmd1b2MgbGFpIDAuCiAgICBDaGkgZHVuZyBkZSBHSEkgQ0hVLiBRdXkgdGFjIGRhIGNob3QgKDA1LzEwLzIwMjYpOiBkdW9uZyBibyBiYW0gZHVuZyBuZXQgZGEgdmU7IGxvcCB0cmF0IGto"
"b25nIHZlIHRoaSBLSE9ORyBsdWkgMTUgbW0uCiAgICBNdW9uIGx1aSB0aGkgbmd1b2kgZHVuZyBwaGFpIHlldSBjYXUgcm8gKC0tbG9wLXRyYXQgMTUpLiIiIgogICAgdnQsIHdsID0gW10sIFtdCiAgICBmb3IgZSBpbiB3YWxrKG1zcCk6CiAgICAgICAgaWYgZS5k"
"eGZ0eXBlKCkgIT0gIkxJTkUiOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGxzID0gTGluZVN0cmluZyhbKGUuZHhmLnN0YXJ0LngsIGUuZHhmLnN0YXJ0LnkpLCAoZS5keGYuZW5kLngsIGUuZHhmLmVuZC55KV0pCiAgICAgICAgbGF5ID0gbGF5ZXJfZ29j"
"KGUuZHhmLmxheWVyKQogICAgICAgIGlmIGxheSA9PSAiYS12dWEgdHJhdCI6CiAgICAgICAgICAgIHZ0LmFwcGVuZChscykKICAgICAgICBlbGlmIGxheSA9PSAiYS13YWxsIjoKICAgICAgICAgICAgd2wuYXBwZW5kKGxzKQogICAgaWYgbm90IHZ0IG9yIG5vdCB3"
"bDoKICAgICAgICByZXR1cm4gMC4wCiAgICB1ID0gdW5hcnlfdW5pb24od2wpLmJ1ZmZlcigxLjApCiAgICB0b25nID0gc3VtKGwubGVuZ3RoIGZvciBsIGluIHZ0KQogICAgcGh1ID0gc3VtKGwuaW50ZXJzZWN0aW9uKHUpLmxlbmd0aCBmb3IgbCBpbiB2dCkKICAg"
"IHJldHVybiBkYXkgaWYgdG9uZyA+IDAgYW5kIHBodSAvIHRvbmcgPiAwLjUgZWxzZSAwLjAKCgpkZWYgY2hvbl9sb3BfdHJhdChtc3AsIGdpYV90cmkpOgogICAgIiIiU28gbW0gbHVpIHZhbyAobWFjIGRpbmggMCkgKyBnaGkgY2h1IGtoaSBiYW4gdmUgY2h1YSB2"
"ZSBsb3AgdHJhdCByaWVuZy4gJ2F1dG8nIChjYWNoIGN1KSBuYXkgY3VuZyA9IDAuIiIiCiAgICBzID0gc3RyKGdpYV90cmkpLnN0cmlwKCkubG93ZXIoKQogICAgdCA9IDAuMCBpZiBzIGluICgiIiwgImF1dG8iKSBlbHNlIGZsb2F0KHMpCiAgICBub3RlID0gTm9u"
"ZQogICAgaWYgcGhhdF9oaWVuX2xvcF90cmF0KG1zcCkgPiAwOgogICAgICAgIG5vdGUgPSAoIk7DqXQgQS1WdWEgdHJhdCB0csO5bmcgbeG6t3QgdMaw4budbmcgQS1XYWxsIChi4bqjbiB24bq9IGNoxrBhIHbhur0gbOG7m3AgdHLDoXQgcmnDqm5nKTogxJHGsOG7"
"nW5nIGJvIHRoZW8gxJHDum5nIG3hurd0IHTGsOG7nW5nIMSRw6MgduG6vSIKICAgICAgICAgICAgICAgICsgKCIsIGtow7RuZyBsw7lpIGzhu5twIHRyw6F0LiIgaWYgbm90IHQgZWxzZSBmIjsgxJHDoyBsw7lpIHt0Omd9IG1tIHRoZW8gecOqdSBj4bqndS4iKSkK"
"ICAgIHJldHVybiB0LCBub3RlCgoKZGVmIGluc2V0X2ZhY2UoZiwgdCk6CiAgICAiIiJMdWkgbWF0IGBmYCB2YW8gdHJvbmcgdCBtbSAoZ29jIG5ob24gZ2l1IG5ndXllbik7IHRyYSB2ZSBQb2x5Z29uIGxvbiBuaGF0IGhvYWMgTm9uZS4iIiIKICAgIGlmIG5vdCB0"
"OgogICAgICAgIHJldHVybiBmCiAgICBnID0gZi5idWZmZXIoLXQsIGpvaW5fc3R5bGU9MiwgbWl0cmVfbGltaXQ9NSkuc2ltcGxpZnkoMC4wMSkKICAgIGlmIGcuaXNfZW1wdHk6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIHJldHVybiBtYXgoZ2V0YXR0cihnLCAi"
"Z2VvbXMiLCBbZ10pLCBrZXk9bGFtYmRhIHA6IHAuYXJlYSkKCgpkZWYgYWNhZF9zdHIocyk6CiAgICAiIiJDaHVvaSBhbiB0b2FuIGNobyAuc2NyIEFTQ0lJOiBreSB0dSBuZ29haSBBU0NJSSB0aGFuaCBcXFUrWFhYWCAoQXV0b0NBRCBoaWV1IGtoaSBuaGFwIGxl"
"bmgpLiIiIgogICAgcmV0dXJuICIiLmpvaW4oYyBpZiBvcmQoYykgPCAxMjggZWxzZSAiXFxVKyUwNFgiICUgb3JkKGMpIGZvciBjIGluIHMpCgoKZGVmIGRhbmdsaW5nX25lYXIoY2hhaW5zLCBwb2ludCwgcmFkaXVzKToKICAgIHB0cyA9IFtdCiAgICBmb3IgY2xv"
"c2VkLCBjaCBpbiBjaGFpbnM6CiAgICAgICAgaWYgbm90IGNsb3NlZDoKICAgICAgICAgICAgZm9yIHAgaW4gKGNoWzBdLCBjaFstMV0pOgogICAgICAgICAgICAgICAgaWYgbWF0aC5kaXN0KHAsIHBvaW50KSA8PSByYWRpdXM6CiAgICAgICAgICAgICAgICAgICAg"
"cHRzLmFwcGVuZCgocm91bmQocFswXSksIHJvdW5kKHBbMV0pKSkKICAgIHJldHVybiBzb3J0ZWQoc2V0KHB0cykpCgoKZGVmIHBhcnNlX3RoZW1fcmFuaCh0ZXh0KToKICAgICIiIid4MSx5MSx4Mix5Mjt4MSx5MSx4Mix5MicgLT4gbGlzdCBjaHVvaSAoRmFsc2Us"
"IFsoeDEseTEpLCh4Mix5MildKS4iIiIKICAgIG91dCA9IFtdCiAgICBmb3IgcGFydCBpbiAodGV4dCBvciAiIikuc3BsaXQoIjsiKToKICAgICAgICBwYXJ0ID0gcGFydC5zdHJpcCgpCiAgICAgICAgaWYgbm90IHBhcnQ6CiAgICAgICAgICAgIGNvbnRpbnVlCiAg"
"ICAgICAgdiA9IFtmbG9hdCh0KSBmb3IgdCBpbiBwYXJ0LnJlcGxhY2UoIiAiLCAiIikuc3BsaXQoIiwiKV0KICAgICAgICBpZiBsZW4odikgIT0gNDoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcihmIkRvYW4gZG9uZyByYW5oIHNhaSBkaW5oIGRhbmcgKGNh"
"biA0IHNvIHgxLHkxLHgyLHkyKToge3BhcnR9IikKICAgICAgICBvdXQuYXBwZW5kKChGYWxzZSwgWyh2WzBdLCB2WzFdKSwgKHZbMl0sIHZbM10pXSkpCiAgICByZXR1cm4gb3V0CgoKZGVmIGtoZV9ob19nYW4oY2hhaW5zLCBwb2ludCwgcmFkaXVzLCB0b3A9Nik6"
"CiAgICAiIiJDYWMgY2FwIGRhdSBobyBnYW4gZGllbSBkYXQgdGVuLCBkZSBnb2kgeSBjaG8gbmd1b2kgZHVuZyBub2kgbyBkYXUgY2FuIGRvbmcgcmFuaC4iIiIKICAgIGVuZHMgPSBbXQogICAgZm9yIGNsb3NlZCwgY2ggaW4gY2hhaW5zOgogICAgICAgIGlmIG5v"
"dCBjbG9zZWQ6CiAgICAgICAgICAgIGVuZHMuZXh0ZW5kKFtjaFswXSwgY2hbLTFdXSkKICAgIG5lYXIgPSBbZSBmb3IgZSBpbiBlbmRzIGlmIG1hdGguZGlzdChlLCBwb2ludCkgPD0gcmFkaXVzXQogICAgcGFpcnMgPSBbXQogICAgZm9yIGksIHAgaW4gZW51bWVy"
"YXRlKG5lYXIpOgogICAgICAgIGZvciBxIGluIG5lYXJbaSArIDE6XToKICAgICAgICAgICAgZCA9IG1hdGguZGlzdChwLCBxKQogICAgICAgICAgICBpZiBkID4gNToKICAgICAgICAgICAgICAgIHBhaXJzLmFwcGVuZCgocm91bmQoZCksIChyb3VuZChwWzBdKSwg"
"cm91bmQocFsxXSkpLCAocm91bmQocVswXSksIHJvdW5kKHFbMV0pKSkpCiAgICBwYWlycy5zb3J0KCkKICAgIHJldHVybiBbZGljdChkYWk9ZCwgdHU9cCwgZGVuPXEpIGZvciBkLCBwLCBxIGluIHBhaXJzWzp0b3BdXQoKCmRlZiBhbmhfeGVtX2xhaShwYXRoLCBj"
"aGFpbnMsIHJvb21zLCBmYWlsZWQsIGV4dHJhKToKICAgIGltcG9ydCBtYXRwbG90bGliCiAgICBtYXRwbG90bGliLnVzZSgiQWdnIikKICAgIGltcG9ydCBtYXRwbG90bGliLnB5cGxvdCBhcyBwbHQKICAgIGZpZyA9IHBsdC5maWd1cmUoZmlnc2l6ZT0oMTIsIDEy"
"KSwgZHBpPTkwKQogICAgYXggPSBmaWcuYWRkX2F4ZXMoWzAuMDMsIDAuMDMsIDAuOTUsIDAuOTVdKQogICAgZm9yIGNsb3NlZCwgY2ggaW4gY2hhaW5zOgogICAgICAgIHhzLCB5cyA9IHppcCgqKGNoICsgKFtjaFswXV0gaWYgY2xvc2VkIGVsc2UgW10pKSkKICAg"
"ICAgICBheC5wbG90KHhzLCB5cywgY29sb3I9IiM4NjhlOTYiLCBsdz0xKQogICAgY29scyA9IFsiI2U2MTk0YiIsICIjM2NiNDRiIiwgIiM0MzYzZDgiLCAiI2Y1ODIzMSIsICIjOTExZWI0IiwgIiMwMDgwODAiLCAiIzlhNjMyNCIsICIjODAwMDAwIiwgIiM4MDgw"
"MDAiXQogICAgZm9yIGksIHIgaW4gZW51bWVyYXRlKHJvb21zKToKICAgICAgICB4cywgeXMgPSB6aXAoKihyWyJkaW5oIl0gKyBbclsiZGluaCJdWzBdXSkpCiAgICAgICAgYyA9IGNvbHNbaSAlIGxlbihjb2xzKV0KICAgICAgICBheC5maWxsKHhzLCB5cywgY29s"
"b3I9YywgYWxwaGE9MC4yKQogICAgICAgIGF4LnBsb3QoeHMsIHlzLCBjb2xvcj1jLCBsdz0yKQogICAgICAgIGF4LnRleHQoclsibmhhbl94eSJdWzBdLCByWyJuaGFuX3h5Il1bMV0sIGYne3JbInRlbiJdfVxue3JbImR0X2xhbV90cm9uIl06LjFmfSBtMicsIGhh"
"PSJjZW50ZXIiLCBmb250c2l6ZT05KQogICAgZm9yIGYgaW4gZmFpbGVkOgogICAgICAgIGF4LnBsb3QoKmZbInh5Il0sICJyeCIsIG1zPTE0LCBtZXc9MykKICAgICAgICBheC50ZXh0KGZbInh5Il1bMF0sIGZbInh5Il1bMV0sICIgICIgKyBmWyJ0ZW4iXSArICIg"
"KGjhu58pIiwgY29sb3I9InJlZCIsIGZvbnRzaXplPTkpCiAgICAgICAgZm9yIHAgaW4gZlsiZGF1X2hvX2dhbiJdOgogICAgICAgICAgICBheC5wbG90KCpwLCAicm8iLCBtcz02LCBtZmM9Im5vbmUiKQogICAgZm9yIGFfLCBiXyBpbiBleHRyYToKICAgICAgICBh"
"eC5wbG90KFthX1swXSwgYl9bMF1dLCBbYV9bMV0sIGJfWzFdXSwgY29sb3I9IiMxYzdlZDYiLCBsdz0yLCBscz0iLS0iKQogICAgYXguc2V0X2FzcGVjdCgiZXF1YWwiKQogICAgYXguZ3JpZChUcnVlLCBsdz0wLjMpCiAgICBmaWcuc2F2ZWZpZyhwYXRoKQogICAg"
"cGx0LmNsb3NlKGZpZykKCgpkZWYgc2NyX2Zvcihyb29tcywgbGF5ZXIsIGxhYmVsX2gsIGxhYmVsX2xheWVyLCBjbGF5ZXI9IjAiKToKICAgICIiIlNpbmggbGVuaCBBdXRvQ0FEIHZlIHBvbHlsaW5lIHBob25nICsgbmhhbiBtMiAoY2hheSB0cmVuIEJBTiBTQU8g"
"RFdHKS4iIiIKICAgICMgVHJvbmcgLnNjciwgZG9uZyB0cm9uZyA9IHBoaW0gRW50ZXI7ICIiIHNlIGJpIGhpZXUgbGEga3kgdHUgbmVuIGtob25nIGR1bmcuIE1vaSB0dXkgY2hvbiBtb3QgZG9uZy4KICAgIEwgPSBbIkNNREVDSE8iLCAiMCIsICJPU01PREUiLCAi"
"MCIsCiAgICAgICAgICJfLi1MQVlFUiIsICJfTSIsIGYnIntsYWJlbF9sYXllcn0iJywgIiIsICAgICAgICAgICAgICAgICAgICAgICAjIHRhby9kYXQgbGF5ZXIgbmhhbiAoZGEgY28gdGhpIGNoaSBkYXQpCiAgICAgICAgICJfLi1MQVlFUiIsICJfTSIsIGYnInts"
"YXllcn0iJywgIl9DIiwgIjIyMiIsICIiLCAiIl0gICAgICAgICAgICMgdGFvIGxheWVyIHBob25nLCBtYXUgMjIyICh0aGVvIGJhbiBtYXUpCiAgICBmb3IgciBpbiByb29tczoKICAgICAgICBpZiBub3Qgci5nZXQoImNoaV9uaGFuIik6CiAgICAgICAgICAgIEwg"
"Kz0gWyJfLi1MQVlFUiIsICJfUyIsIGYnIntsYXllcn0iJywgIiJdCiAgICAgICAgICAgIEwuYXBwZW5kKCJfLlBMSU5FICIgKyAiICIuam9pbihmInt4Oi40Zn0se3k6LjRmfSIgZm9yIHgsIHkgaW4gclsiZGluaCJdKSArICIgX0MiKQogICAgICAgICAgICAjIGNv"
"dC9ob3Aga3kgdGh1YXQgbmFtIHJpZW5nIHRyb25nIHBob25nOiB2ZSBwb2x5bGluZSBsb2FpIHRydSBjdW5nIGxheWVyLCBkZSBEVCBuaGFuID0gZHVvbmcgYm8gLSBsb2FpIHRydQogICAgICAgICAgICBmb3IgaG8gaW4gci5nZXQoImhvIiwgW10pOgogICAgICAg"
"ICAgICAgICAgTC5hcHBlbmQoIl8uUExJTkUgIiArICIgIi5qb2luKGYie3g6LjRmfSx7eTouNGZ9IiBmb3IgeCwgeSBpbiBobykgKyAiIF9DIikKICAgICAgICBpZiByLmdldCgibmhhbl9jb19zYW4iKToKICAgICAgICAgICAgY29udGludWUgICAgICAgICAgICAg"
"ICAgICAgICAgIyBwaG9uZyBkYSBjbyBuaGFuIG0yIHRyZW4gbG9wIGluIGR1b2M6IGtob25nIGdoaSB0aGVtCiAgICAgICAgbmhhbiA9IGYne3JbImR0X2xhbV90cm9uIl06LjFmfSBtMicKICAgICAgICBuID0gci5nZXQoIm5oYW4iKQogICAgICAgIGlmIG46CiAg"
"ICAgICAgICAgICMgTmhhbiBkaWVuIHRpY2g6IGN1bmcgbGF5ZXIsIHN0eWxlLCBjYW8sIG1hdSwgZ29jIHhvYXkgdm9pIHRleHQgdGVuIHBob25nOyBjYW4gZ2l1YSwgbmFtIGJlbiBkdW9pIHRlbiBwaG9uZy4KICAgICAgICAgICAgTCArPSBsZW5oX25oYW4obiwg"
"bmhhbikKICAgICAgICBlbHNlOgogICAgICAgICAgICAjIHBob25nIGtoYWkgYmFvIGJhbmcgLS10aGVtLXBob25nIChraG9uZyBjbyB0ZXh0IHRlbik6IGRhdCBuaGFuIHRhaSB0YW0gdnVuZyBiYW5nIGdpYSB0cmkgbWFjIGRpbmgKICAgICAgICAgICAgTCArPSBb"
"Il8uLUxBWUVSIiwgIl9TIiwgZicie2xhYmVsX2xheWVyfSInLCAiIl0KICAgICAgICAgICAgY3gsIGN5ID0gclsibmhhbl94eSJdCiAgICAgICAgICAgIEwgKz0gWyJfLi1URVhUIiwgIl9KIiwgIl9NQyIsIGYie2N4Oi4yZn0se2N5Oi4yZn0iLCBmIntsYWJlbF9o"
"Omd9IiwgIjAiLCBuaGFuXQogICAgTCArPSBbIl8uLUxBWUVSIiwgIl9TIiwgZicie2FjYWRfc3RyKGNsYXllcil9IicsICIiXSAgICAgICAjIHRyYSBsYWkgbGF5ZXIgaGllbiBoYW5oIGN1YSBiYW4gdmUKICAgIEwgKz0gWyJfLlFTQVZFIiwgIl8uUVVJVCBfWSJd"
"CiAgICByZXR1cm4gIlxuIi5qb2luKEwpICsgIlxuIgoKCmRlZiBtYWluKCk6CiAgICBhcCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKCkKICAgIGFwLmFkZF9hcmd1bWVudCgiZHhmIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1vdXQtZGlyIiwgZGVmYXVsdD0i"
"LiIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tbGF5ZXItcGhvbmciLCBkZWZhdWx0PUxBWUVSX1BIT05HKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWxheWVyLXJhbmgiLCBkZWZhdWx0PSIsIi5qb2luKExBWUVSX1JBTkgpLCBoZWxwPSJjYWMgbGF5ZXIgbGFtIHJh"
"bmgsIGNhY2ggbmhhdSBkYXUgcGhheSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tbGF5ZXItdGVuIiwgZGVmYXVsdD1MQVlFUl9URU4pCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tZ2FwLW1heCIsIHR5cGU9ZmxvYXQsIGRlZmF1bHQ9MTIwMC4wKQogICAgYXAuYWRk"
"X2FyZ3VtZW50KCItLWxhYmVsLWgiLCB0eXBlPWZsb2F0LCBkZWZhdWx0PTI1MC4wKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWxhYmVsLWxheWVyIiwgZGVmYXVsdD0iQS1UZXh0IikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1sYXllci1kb25nLXJhbmgiLCBkZWZh"
"dWx0PSJBLURvbmcgcmFuaCBwaG9uZyIsCiAgICAgICAgICAgICAgICAgICAgaGVscD0ibGF5ZXIgY2h1YSBMSU5FL1BMSU5FIGRvIG5ndW9pIGR1bmcgdmUgZGUgZG9uZyByYW5oIGNobyBjaG8gaG8gKHR1eSBjaG9uKSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0t"
"dGhlbS1yYW5oIiwgZGVmYXVsdD0iIiwgaGVscD0iZG9hbiBkb25nIHJhbmggbmhhcCB0YXk6ICd4MSx5MSx4Mix5Mjt4MSx5MSx4Mix5MiciKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWJsb2NrLWJvLXF1YSIsIGRlZmF1bHQ9Tm9uZSwKICAgICAgICAgICAgICAg"
"ICAgICBoZWxwPSJyZWdleCB0ZW4gYmxvY2sveHJlZiBraG9uZyBsYXkgbGFtIHJhbmggKG1hYyBkaW5oOiBnaGkgY2h1LCBsZWdlbmQsIGtodW5nLCBsdW9pLCB0cmFuLCBsb2kgdGhhbmcpOyAnJyA9IGxheSBoZXQiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXRo"
"ZW0tcGhvbmciLCBkZWZhdWx0PSIiLAogICAgICAgICAgICAgICAgICAgIGhlbHA9ImtoYWkgYmFvIHBob25nIGtob25nIGNvIHRleHQgdGVuOiAnVGVuOngseTtUZW46eCx5JyAoZHVuZyB0b2EgZG8gZGllbSB0cm9uZyBwaG9uZykiKQogICAgYXAuYWRkX2FyZ3Vt"
"ZW50KCItLWxvcC10cmF0IiwgZGVmYXVsdD0iMCIsCiAgICAgICAgICAgICAgICAgICAgaGVscD0ic28gbW0gbHVpIHZhbyB0cm9uZyBuZXQgcmFuaC4gTWFjIGRpbmggMDogZHVvbmcgYm8gYmFtIGR1bmcgbmV0IGRhIHZlIChsb3AgdHJhdCBraG9uZyB2ZSB0aGkg"
"a2hvbmcgIgogICAgICAgICAgICAgICAgICAgICAgICAgImx1aSkuIENoaSBkYXQgMTUga2hpIG5ndW9pIGR1bmcgeWV1IGNhdSByby4iKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLWxheWVyLWN1YSIsIGRlZmF1bHQ9IiwiLmpvaW4oTEFZRVJfQ1VBKSwKICAgICAg"
"ICAgICAgICAgICAgICBoZWxwPSJsYXllciBjdWEgZGkvY3VhIHNvIGxheSBuZXQgYmFvIGtodW5nIGxhbSByYW5oIChibyBjYW5oIG1vLCBjdW5nIHF1YXkpOyAnJyA9IGtob25nIGR1bmciKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLW5oYW4tdGF0LWNhIiwgYWN0"
"aW9uPSJzdG9yZV90cnVlIiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJnaGkgdGhlbSBuaGFuIG0yIGNobyBjYSBwaG9uZyBkYSBjbyBwb2x5bGluZSAobWFjIGRpbmggY2hpIGdoaSBuaGFuIGNobyBwaG9uZyBkdW5nIG1vaSkiKQogICAgYXAuYWRkX2FyZ3Vt"
"ZW50KCItLXZlLWxhaSIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAgICAgICAgICAgaGVscD0iZHVuZyB2YSB2ZSBsYWkgY2EgcGhvbmcgZGEgY28gcG9seWxpbmUgdHJlbiBsYXllciBwaG9uZyAobWFjIGRpbmg6IGNoaSBkb2kgY2hpZXUsIGtob25n"
"IHZlIHRydW5nKSIpCiAgICB0aGVtX3RoYW1fc29fY2hpbmgoYXApCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tZGVidWciLCBhY3Rpb249InN0b3JlX3RydWUiKQogICAgYSA9IGFwLnBhcnNlX2FyZ3MoKQogICAgc3lzLnN0ZG91dCA9IGlvLlRleHRJT1dyYXBwZXIo"
"c3lzLnN0ZG91dC5idWZmZXIsIGVuY29kaW5nPSJ1dGYtOCIpCgogICAgZG9jID0gZXpkeGYucmVhZGZpbGUoYS5keGYpCiAgICBtc3AgPSBkb2MubW9kZWxzcGFjZSgpCiAgICBwcm9ibGVtcyA9IFtdCiAgICBpZiBkb2MuaGVhZGVyLmdldCgiJElOU1VOSVRTIiwg"
"MCkgIT0gNDoKICAgICAgICBwcm9ibGVtcy5hcHBlbmQoKExPSSwgIsSQxqFuIHbhu4sgYuG6o24gduG6vSIsIGYiSU5TVU5JVFM9e2RvYy5oZWFkZXIuZ2V0KCckSU5TVU5JVFMnLCAwKX0sIGNodeG6qW4gbMOgIDQgKG1tKS4iKSkKCiAgICBsYXllcnMgPSBbeC5z"
"dHJpcCgpIGZvciB4IGluIGEubGF5ZXJfcmFuaC5zcGxpdCgiLCIpIGlmIHguc3RyaXAoKV0KICAgIGNoYWlucyA9IGRvY19jaGFpbnMobXNwLCBsYXllcnMpCiAgICBkb25nX3JhbmggPSBkb2NfY2hhaW5zKG1zcCwgW2EubGF5ZXJfZG9uZ19yYW5oXSkgKyBwYXJz"
"ZV90aGVtX3JhbmgoYS50aGVtX3JhbmgpCiAgICBjaGFpbnMgPSBjaGFpbnMgKyBkb25nX3JhbmgKICAgIGlmIGEuYmxvY2tfYm9fcXVhIGlzIG5vdCBOb25lOgogICAgICAgIF9CT19RVUFbMF0gPSByZS5jb21waWxlKGEuYmxvY2tfYm9fcXVhLCByZS5JKSBpZiBh"
"LmJsb2NrX2JvX3F1YSBlbHNlIE5vbmUKICAgICAgICBjaGFpbnMgPSBkb2NfY2hhaW5zKG1zcCwgbGF5ZXJzKSArIGRvbmdfcmFuaCAgICMgdGluaCBsYWkgdm9pIGJvIGxvYyBtb2kKICAgIHNlZWRzID0gZG9jX3NlZWRzKG1zcCwgYS5sYXllcl90ZW4sIGRvYykK"
"ICAgIGZvciBwYXJ0IGluIChhLnRoZW1fcGhvbmcgb3IgIiIpLnNwbGl0KCI7Iik6CiAgICAgICAgaWYgIjoiIGluIHBhcnQ6CiAgICAgICAgICAgIHRlbiwgeHkgPSBwYXJ0LnJzcGxpdCgiOiIsIDEpCiAgICAgICAgICAgIHN4LCBzeSA9IFtmbG9hdCh0KSBmb3Ig"
"dCBpbiB4eS5zcGxpdCgiLCIpXQogICAgICAgICAgICBzZWVkcy5hcHBlbmQoKHRlbi5zdHJpcCgpLCAoc3gsIHN5KSwgTm9uZSkpCiAgICAjIG5oYW4gbTIgZGEgY28gdHJlbiBsb3AgaW4gZHVvYyAoa2hvbmcgdGluaCBEZWZwb2ludHMpOiBraG9uZyBnaGkgbmhh"
"biB0cnVuZwogICAgbmhhbl9jbyA9IFtdCiAgICBmb3IgZSBpbiBtc3A6CiAgICAgICAgaWYgZS5keGZ0eXBlKCkgaW4gKCJURVhUIiwgIk1URVhUIikgYW5kIGxheWVyX2dvYyhlLmR4Zi5sYXllcikgIT0gImRlZnBvaW50cyI6CiAgICAgICAgICAgIHQgPSBlLmR4"
"Zi50ZXh0IGlmIGUuZHhmdHlwZSgpID09ICJURVhUIiBlbHNlIGUucGxhaW5fdGV4dCgpCiAgICAgICAgICAgIG0gPSBSRV9OSEFOLnNlYXJjaCh0IG9yICIiKQogICAgICAgICAgICBpZiBtOgogICAgICAgICAgICAgICAgc28gPSByZS5tYXRjaChyIlxkKyg/Olsu"
"LF1cZCspPyIsIG0uZ3JvdXAoMCkpLmdyb3VwKDApLnJlcGxhY2UoIiwiLCAiLiIpCiAgICAgICAgICAgICAgICBuaGFuX2NvLmFwcGVuZCgoUG9pbnQoZS5keGYuaW5zZXJ0LngsIGUuZHhmLmluc2VydC55KSwgZmxvYXQoc28pLCBlLmR4Zi5oYW5kbGUpKQogICAg"
"aWYgbm90IHNlZWRzOgogICAgICAgIHByb2JsZW1zLmFwcGVuZCgoQ0FOSF9CQU8sICJLaMO0bmcgY8OzIHTDqm4gcGjDsm5nIiwKICAgICAgICAgICAgICAgICAgICAgICAgICJLaMO0bmcgdGjhuqV5IHRleHQgdMOqbiBwaMOybmcgKGxheWVyIEEtVGV4dCkg4buf"
"IE1vZGVsIHbDoCBraMO0bmcgY8OzIC0tdGhlbS1waG9uZzsgY2jhu4kgbGnhu4d0IGvDqiB2w7luZyBrw61uIGNoxrBhIMSR4bq3dCB0w6puLiIpKQogICAga2h1bmcsIHRrX2N1YSA9IGRvY19raHVuZ19jdWEobXNwLCBjaGFpbnMsIFt4LnN0cmlwKCkgZm9yIHgg"
"aW4gYS5sYXllcl9jdWEuc3BsaXQoIiwiKSBpZiB4LnN0cmlwKCldKQogICAgZmFjZXMsIHBhaXJzLCBicmlkZ2VzID0gYnVpbGRfZmFjZXMoY2hhaW5zLCBhLmdhcF9tYXgsIGtodW5nKQogICAgdF9pbiwgZ2hpX2NodV90cmF0ID0gY2hvbl9sb3BfdHJhdChtc3As"
"IGEubG9wX3RyYXQpCiAgICBpZiBnaGlfY2h1X3RyYXQ6CiAgICAgICAgcHJvYmxlbXMuYXBwZW5kKChHT0lfWSwgIkzhu5twIHRyw6F0IiwgZ2hpX2NodV90cmF0KSkKCiAgICAjIHBvbHlsaW5lIHBob25nIGRhIGNvIHNhbiB0cmVuIGxheWVyIHBob25nIChuaGFu"
"IHZpZW4vbmd1b2kgZHVuZyBkYSBibyk6IGRvaSBjaGlldSwga2hvbmcgdmUgdHJ1bmcKICAgIGV4aXN0aW5nID0gW10KICAgIGZvciBlIGluIG1zcDoKICAgICAgICBpZiBlLmR4ZnR5cGUoKSA9PSAiTFdQT0xZTElORSIgYW5kIG5vcm0oZS5keGYubGF5ZXIpID09"
"IG5vcm0oYS5sYXllcl9waG9uZyk6CiAgICAgICAgICAgIHB0cyA9IFsodi54LCB2LnkpIGZvciB2IGluIGV6cGF0aC5tYWtlX3BhdGgoZSkuZmxhdHRlbmluZygwLjUpXQogICAgICAgICAgICBpZiBsZW4ocHRzKSA+PSAzOgogICAgICAgICAgICAgICAgZyA9IFBv"
"bHlnb24ocHRzKQogICAgICAgICAgICAgICAgIyBkb25nID0gY28gYmF0IGNvIENsb3NlZCAoZGF1IGN1b2kgY2hpIHRydW5nIGRpZW0gdmFuIHRpbmggbGEgY2h1YSBkb25nKQogICAgICAgICAgICAgICAgZXhpc3RpbmcuYXBwZW5kKGRpY3QoaGFuZGxlPWUuZHhm"
"LmhhbmRsZSwgZG9uZz1ib29sKGUuY2xvc2VkKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGdlb209ZyBpZiBnLmlzX3ZhbGlkIGVsc2UgZy5idWZmZXIoMCkpKQoKICAgIHJvb21zLCBmYWlsZWQsIGRhX2NvLCBkYV9jb19jaHVhX2RjID0g"
"W10sIFtdLCBbXSwgW10KICAgIGNoaW5oID0gdGFvX2NoaW5oKG1zcCwgYSkKICAgIHRvbmdfY2ggPSB7fQogICAgIyBnb20gdGVuIHRoZW8gdnVuZyBraW4gdHJ1b2MgKGtob25nIGdpYW4gbW8gbmhpZXUgdGVuOiBjaGluaCBoaW5oIHRoZW8gdGVuIGRheSBkdSwg"
"dmkgZHUgIlBob25nIGtoYWNoICsgTG8gZ2lhIikKICAgIG5ob21fdGVuLCB0aHVfdHUgPSB7fSwgW10KICAgIGZvciBuYW1lLCAoeCwgeSksIHRpbmZvIGluIHNlZWRzOgogICAgICAgIGhpdCA9IFtmIGZvciBmIGluIGZhY2VzIGlmIGYuY29udGFpbnMoUG9pbnQo"
"eCwgeSkpXQogICAgICAgIGlmIG5vdCBoaXQ6CiAgICAgICAgICAgIGluZm8gPSBkaWN0KHRlbj1uYW1lLCB4eT0ocm91bmQoeCksIHJvdW5kKHkpKSwKICAgICAgICAgICAgICAgICAgICAgICAgZGF1X2hvX2dhbj1kYW5nbGluZ19uZWFyKGNoYWlucywgKHgsIHkp"
"LCA4MDAwKSwKICAgICAgICAgICAgICAgICAgICAgICAga2hlX2hvX2dhbl9uaGF0PWtoZV9ob19nYW4oY2hhaW5zLCAoeCwgeSksIDgwMDApKQogICAgICAgICAgICBleDAgPSBbcSBmb3IgcSBpbiBleGlzdGluZyBpZiBxWyJnZW9tIl0uY29udGFpbnMoUG9pbnQo"
"eCwgeSkpXQogICAgICAgICAgICBpZiBleDA6CiAgICAgICAgICAgICAgICAjIFBob25nIGRhIGNvIHBvbHlsaW5lIGN1YSBuZ3VvaSBkdW5nIG5odW5nIG5ldCByYW5oIGNodWEgZHUgZGUgZHVuZyBsYWk6IEtIT05HIHBoYWkgbG9pIGN1YSBwaG9uZywKICAgICAg"
"ICAgICAgICAgICMgY2hpIGxhIGNodWEgZG9pIGNoaWV1IGRvYyBsYXAgZHVvYy4gS2hvbmcgYmFvICJMb2kgLSBraG9uZyBkb25nIGtpbiIuCiAgICAgICAgICAgICAgICBxID0gbWluKGV4MCwga2V5PWxhbWJkYSB0OiB0WyJnZW9tIl0uYXJlYSkKICAgICAgICAg"
"ICAgICAgIGluZm8udXBkYXRlKGhhbmRsZT1xWyJoYW5kbGUiXSwgZHRfY29fc2FuPXFbImdlb20iXS5hcmVhIC8gMWU2LCBkb25nPXFbImRvbmciXSkKICAgICAgICAgICAgICAgIGRhX2NvX2NodWFfZGMuYXBwZW5kKGluZm8pCiAgICAgICAgICAgIGVsc2U6CiAg"
"ICAgICAgICAgICAgICBmYWlsZWQuYXBwZW5kKGluZm8pCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZiA9IG1pbihoaXQsIGtleT1sYW1iZGEgcDogcC5hcmVhKQogICAgICAgIGlmIGlkKGYpIG5vdCBpbiBuaG9tX3RlbjoKICAgICAgICAgICAgbmhvbV90"
"ZW5baWQoZildID0gZGljdChmYWNlPWYsIHRlbj1bXSwgeHk9KHgsIHkpLCBpbmZvPXRpbmZvKQogICAgICAgICAgICB0aHVfdHUuYXBwZW5kKGlkKGYpKQogICAgICAgIG5ob21fdGVuW2lkKGYpXVsidGVuIl0uYXBwZW5kKG5hbWUpCiAgICBmb3IgZmlkIGluIHRo"
"dV90dToKICAgICAgICBuZyA9IG5ob21fdGVuW2ZpZF0KICAgICAgICBmX2dvYywgKHgsIHkpLCB0aW5mbyA9IG5nWyJmYWNlIl0sIG5nWyJ4eSJdLCBuZ1siaW5mbyJdCiAgICAgICAgbmFtZSA9ICIgKyAiLmpvaW4obmdbInRlbiJdKQogICAgICAgIHdhcm4gPSBb"
"XQogICAgICAgIGlmIGxlbihuZ1sidGVuIl0pID4gMToKICAgICAgICAgICAgIyBOaGlldSB0ZW4gcGhvbmcgY3VuZyBuYW0gdHJvbmcgbW90IHZ1bmcga2luIChraG9uZyBnaWFuIG1vLCB2aSBkdSBwaG9uZyBraGFjaCArIGJlcCk6IGNoaSBkdW5nIE1PVCBwb2x5"
"bGluZS4KICAgICAgICAgICAgd2Fybi5hcHBlbmQoZiJLaMO0bmcgZ2lhbiBt4bufOiB7bmFtZX0gbuG6sW0gY2h1bmcgbeG7mXQgdsO5bmcga8OtbiAoa2jDtG5nIGPDsyB2w6FjaCBuZ8SDbikuIE114buRbiB0w6FjaCByacOqbmcsICIKICAgICAgICAgICAgICAg"
"ICAgICAgICAgZiJ24bq9IMSRb+G6oW4gY2hpYSByYW5oIHRyw6puIGxheWVyICd7YS5sYXllcl9kb25nX3Jhbmh9JyBob+G6t2MgZMO5bmcgLS10aGVtLXJhbmggcuG7k2kgY2jhuqF5IGzhuqFpLiIpCiAgICAgICAgZiA9IGluc2V0X2ZhY2UoZl9nb2MsIHRfaW4p"
"ICAgICAgICAgICMgbHVpIHZhbyBsb3AgdHJhdCAobmV1IG7DqXQgQS1WdWEgdHJhdCB0cnVuZyBtYXQgdHVvbmcpIC0+IG1hdCBob2FuIHRoaeG7h24KICAgICAgICBpZiBmIGlzIE5vbmU6CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZGVtID0ge30KICAg"
"ICAgICBpZiBjaGluaCBpcyBub3QgTm9uZToKICAgICAgICAgICAgZ18sIGRlbSA9IGNoaW5oKGYsIG5hbWUpCiAgICAgICAgICAgIGlmIGlzaW5zdGFuY2UoZ18sIFBvbHlnb24pIGFuZCBub3QgZ18uaXNfZW1wdHk6CiAgICAgICAgICAgICAgICBmID0gZ18KICAg"
"ICAgICAgICAgZm9yIGtfLCB2XyBpbiBkZW0uaXRlbXMoKToKICAgICAgICAgICAgICAgIHRvbmdfY2hba19dID0gdG9uZ19jaC5nZXQoa18sIDApICsgdl8KICAgICAgICByaW5nID0gbGlzdChmLmV4dGVyaW9yLmNvb3JkcylbOi0xXQogICAgICAgIGlmIHRfaW46"
"CiAgICAgICAgICAgIHdhcm4uYXBwZW5kKGYixJDDoyBsw7lpIHt0X2luOmd9IG1tIHbDoG8gdHJvbmcgbsOpdCByYW5oIHRoZW8gecOqdSBj4bqndSAoLS1sb3AtdHJhdCB7dF9pbjpnfSkuIikKICAgICAgICBpZiBsZW4oZi5pbnRlcmlvcnMpOgogICAgICAgICAg"
"ICBob2xlcyA9IHN1bShQb2x5Z29uKGkpLmFyZWEgZm9yIGkgaW4gZi5pbnRlcmlvcnMpIC8gMWU2CiAgICAgICAgICAgIHdhcm4uYXBwZW5kKGYiQ8OzIHtsZW4oZi5pbnRlcmlvcnMpfSB24bqtdCBu4bqxbSByacOqbmcgdHJvbmcgcGjDsm5nICh04buVbmcge2hv"
"bGVzOi4yZn0gbcKyKSDEkcOjIHRy4burIGto4buPaSBkaeG7h24gdMOtY2g7IGPhuqduIHjDoWMgbmjhuq1uIGPhu5l0L2jhu5lwIGvhu7kgdGh14bqtdC4iKQogICAgICAgIGMgPSBmLnJlcHJlc2VudGF0aXZlX3BvaW50KCkKICAgICAgICAjIERUIGdoaSBuaGFu"
"IHRpbmggdHUgY2hpbmggaGluaCBzZSB2ZSAoZHVvbmcgYm8gLSBjYWMgbG8gbG9haSB0cnUpLCBraG9uZyB0dSBnaWEgdHJpIGtoYWMKICAgICAgICBobyA9IFtsaXN0KGkuY29vcmRzKVs6LTFdIGZvciBpIGluIGYuaW50ZXJpb3JzXQogICAgICAgIGR0X3ZlID0g"
"KFBvbHlnb24ocmluZykuYXJlYSAtIHN1bShQb2x5Z29uKGgpLmFyZWEgZm9yIGggaW4gaG8pKSAvIDFlNgogICAgICAgIG5oYW5fdHJvbmcgPSBbKHYsIGhkKSBmb3IgcHQsIHYsIGhkIGluIG5oYW5fY28gaWYgZi5jb250YWlucyhwdCldCiAgICAgICAgZm9yIHYs"
"IGhkIGluIG5oYW5fdHJvbmc6CiAgICAgICAgICAgIGlmIGFicyh2IC0gcjEoZHRfdmUpKSA+IDAuMDU6CiAgICAgICAgICAgICAgICB3YXJuLmFwcGVuZChmIk5ow6NuIG3CsiBjw7Mgc+G6tW4ge2hkfSBnaGkge3Y6Z30gbcKyLCBraMOhYyBkaeG7h24gdMOtY2gg"
"cG9seWxpbmUge3IxKGR0X3ZlKTouMWZ9IG3CsjogIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgImtow7RuZyBnaGkgxJHDqCBuaMOjbiBjxaksIGPhuqduIHPhu61hIHRheS4iKQogICAgICAgICAgICAgICAgcHJvYmxlbXMuYXBwZW5kKChMT0ksICJOaMOj"
"biBkaeG7h24gdMOtY2ggc2FpIiwgZiIne25hbWV9JzogbmjDo24ge2hkfSBnaGkge3Y6Z30gbcKyLCBwb2x5bGluZSB7cjEoZHRfdmUpOi4xZn0gbcKyLiIpKQogICAgICAgIHJvb20gPSBkaWN0KHRlbj1uYW1lLCBkdD1kdF92ZSwgZHRfbGFtX3Ryb249cjEoZHRf"
"dmUpLCBkaW5oPXJpbmcsIGhvPWhvLAogICAgICAgICAgICAgICAgICAgIG5oYW5feHk9KGMueCwgYy55KSwgY2FuaF9iYW89d2Fybiwgbmhhbj10aW5mbywKICAgICAgICAgICAgICAgICAgICBuaGFuX2NvX3Nhbj1ib29sKG5oYW5fdHJvbmcpLCBkdF92dW5nX2tp"
"bj1mX2dvYy5hcmVhIC8gMWU2LAogICAgICAgICAgICAgICAgICAgIGNoaW5oX2hpbmg9e2tfOiB2XyBmb3Iga18sIHZfIGluIGRlbS5pdGVtcygpIGlmIHZffSkKICAgICAgICBleCA9IFtxIGZvciBxIGluIGV4aXN0aW5nIGlmIHFbImdlb20iXS5jb250YWlucyhQ"
"b2ludCh4LCB5KSldCiAgICAgICAgaWYgZXggYW5kIG5vdCBhLnZlX2xhaToKICAgICAgICAgICAgcSA9IG1pbihleCwga2V5PWxhbWJkYSB0OiB0WyJnZW9tIl0uYXJlYSkKICAgICAgICAgICAgY2hlbmggPSAocVsiZ2VvbSJdLmFyZWEgLSBmLmFyZWEpIC8gMWU2"
"CiAgICAgICAgICAgIHJvb21bImRhX2NvIl0gPSBkaWN0KGhhbmRsZT1xWyJoYW5kbGUiXSwgZHQ9cVsiZ2VvbSJdLmFyZWEgLyAxZTYsIGNoZW5oPWNoZW5oLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBjaGVuaF9wY3Q9Y2hlbmggLyAoZi5hcmVh"
"IC8gMWU2KSAqIDEwMCBpZiBmLmFyZWEgZWxzZSAwLCBkb25nPXFbImRvbmciXSkKICAgICAgICAgICAgaWYgbm90IHFbImRvbmciXToKICAgICAgICAgICAgICAgIHJvb21bImNhbmhfYmFvIl0uYXBwZW5kKGYiUG9seWxpbmUgY8OzIHPhurVuIGhhbmRsZSB7cVsn"
"aGFuZGxlJ119IGNoxrBhIGLhuq10IENsb3NlZC4iKQogICAgICAgICAgICBkYV9jby5hcHBlbmQocm9vbSkKICAgICAgICBlbHNlOgogICAgICAgICAgICByb29tcy5hcHBlbmQocm9vbSkKCiAgICAjIHBvbHlsaW5lIHRydW5nIGNob25nIHRyZW4gbGF5ZXIgcGhv"
"bmcKICAgIGZvciBpLCBwIGluIGVudW1lcmF0ZShleGlzdGluZyk6CiAgICAgICAgZm9yIHEgaW4gZXhpc3RpbmdbaSArIDE6XToKICAgICAgICAgICAgdWEgPSBwWyJnZW9tIl0udW5pb24ocVsiZ2VvbSJdKS5hcmVhCiAgICAgICAgICAgIGlmIHVhID4gMCBhbmQg"
"cFsiZ2VvbSJdLmludGVyc2VjdGlvbihxWyJnZW9tIl0pLmFyZWEgLyB1YSA+IDAuOTg6CiAgICAgICAgICAgICAgICBwcm9ibGVtcy5hcHBlbmQoKENBTkhfQkFPLCAiUG9seWxpbmUgdHLDuW5nIGNo4buTbmciLAogICAgICAgICAgICAgICAgICAgICAgICAgICAg"
"ICAgICBmIkhhbmRsZSB7cFsnaGFuZGxlJ119IHbDoCB7cVsnaGFuZGxlJ119IHRyw7luZyBuaGF1IHRyw6puIGxheWVyICd7YS5sYXllcl9waG9uZ30nLiIpKQogICAgZm9yIHAgaW4gZXhpc3Rpbmc6CiAgICAgICAgaWYgbm90IHBbImRvbmciXToKICAgICAgICAg"
"ICAgcHJvYmxlbXMuYXBwZW5kKChDQU5IX0JBTywgIlBvbHlsaW5lIGNoxrBhIMSRw7NuZyIsIGYiSGFuZGxlIHtwWydoYW5kbGUnXX0ga2jDtG5nIGLhuq10IENsb3NlZC4iKSkKCiAgICAjIHZ1bmcga2luIGNodWEgY28gdGVuIHBob25nICh2aSBkdSBXQyBjaGkg"
"Y28gbmhhbiBtMik6IGRlIG5ndW9pIGR1bmcgZGF0IHRlbgogICAgc2VlZF9wdHMgPSBbUG9pbnQoeCwgeSkgZm9yIF8sICh4LCB5KSwgX2kgaW4gc2VlZHNdCiAgICBjaHVhX3RlbiA9IFtdCiAgICBmb3IgZiBpbiBmYWNlczoKICAgICAgICBpZiBmLmFyZWEgPCAx"
"LjBlNiBvciBmLmFyZWEgPiAxMjAuMGU2IG9yIGYuYnVmZmVyKC0zMDApLmlzX2VtcHR5OiAgICMgYm8gbG9pIHR1b25nL2toZSBoZXAKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBhbnkoZi5jb250YWlucyhzKSBmb3IgcyBpbiBzZWVkX3B0cyk6CiAg"
"ICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgYyA9IGYucmVwcmVzZW50YXRpdmVfcG9pbnQoKQogICAgICAgIGNodWFfdGVuLmFwcGVuZChkaWN0KHh5PShyb3VuZChjLngpLCByb3VuZChjLnkpKSwgZHQ9cm91bmQoZi5hcmVhIC8gMWU2LCA0KSwgZHRfbGFtX3Ry"
"b249cjEoZi5hcmVhIC8gMWU2KSkpCgogICAgaWYgY2hpbmggaXMgbm90IE5vbmUgYW5kIGFueSh0b25nX2NoLnZhbHVlcygpKToKICAgICAgICBwcm9ibGVtcy5hcHBlbmQoKEdPSV9ZLCAiQ2jhu4luaCBow6xuaCIsICLEkMOjICIgKyBjaGgubW9fdGFfY2hpbmgo"
"dG9uZ19jaCkgKyAiIChxdXkgdOG6r2Mgc+G7rWEgbOG7l2kgMeKAkzcsIDA4LzEwLzIwMjY7ICIKICAgICAgICAgICAgICAgICAgICAgICAgICJ04bqvdCBi4bqxbmcgLS1raG9uZy1jaGluaC1oaW5oKS4iKSkKICAgIG9zLm1ha2VkaXJzKGEub3V0X2RpciwgZXhp"
"c3Rfb2s9VHJ1ZSkKICAgIHNjcl9wYXRoID0gb3MucGF0aC5qb2luKGEub3V0X2RpciwgInZlX3BvbHlsaW5lX3Bob25nLnNjciIpCiAgICB3aXRoIG9wZW4oc2NyX3BhdGgsICJ3IiwgZW5jb2Rpbmc9ImFzY2lpIiwgbmV3bGluZT0iXG4iKSBhcyBmaDoKICAgICAg"
"ICAjIC0tbmhhbi10YXQtY2E6IGdoaSB0aGVtIG5oYW4gY2hvIHBob25nIGRhIGNvIHBvbHlsaW5lIChjaGkgbmhhbiwga2hvbmcgdmUgbGFpIHBvbHlsaW5lKQogICAgICAgICMgbmhhbiBjdWEgcGhvbmcgZGEgY28gcG9seWxpbmUgbGF5IHRoZW8gQ0hJTkggcG9s"
"eWxpbmUgY28gc2FuIHRyb25nIGJhbiB2ZSAoa2hvbmcgdGhlbyB2dW5nIGR1bmcgbGFpKQogICAgICAgIGNoaV9uaGFuID0gW2RpY3QociwgY2hpX25oYW49VHJ1ZSwgZHRfbGFtX3Ryb249cjEoclsiZGFfY28iXVsiZHQiXSkpIGZvciByIGluIGRhX2NvXSBpZiBh"
"Lm5oYW5fdGF0X2NhIGVsc2UgW10KICAgICAgICBmaC53cml0ZShzY3JfZm9yKHJvb21zICsgY2hpX25oYW4sIGEubGF5ZXJfcGhvbmcsIGEubGFiZWxfaCwgYS5sYWJlbF9sYXllciwKICAgICAgICAgICAgICAgICAgICAgICAgIGRvYy5oZWFkZXIuZ2V0KCIkQ0xB"
"WUVSIiwgIjAiKSkpCgogICAgZnJvbSBvcGVucHl4bCBpbXBvcnQgV29ya2Jvb2sKICAgIGZyb20gb3BlbnB5eGwuc3R5bGVzIGltcG9ydCBGb250CiAgICB3YiA9IFdvcmtib29rKCkKICAgIHdzID0gd2IuYWN0aXZlCiAgICB3cy50aXRsZSA9ICJQaG9uZyIKICAg"
"IHdzLmFwcGVuZChbIlNUVCIsICJQaMOybmciLCAiRGnhu4duIHTDrWNoIHRow7RuZyB0aOG7p3kgKG3CsikiLCAiTMOgbSB0csOybiAxIHPhu5EgKG3CsikiLCAiVHLhuqFuZyB0aMOhaSIsICJN4bupYyDEkeG7mSIsICJHaGkgY2jDuiJdKQogICAgbiA9IDAKICAg"
"IGZvciByIGluIHJvb21zICsgZGFfY286CiAgICAgICAgbiArPSAxCiAgICAgICAgaWYgImRhX2NvIiBpbiByOgogICAgICAgICAgICBkID0gclsiZGFfY28iXQogICAgICAgICAgICBvayA9IGFicyhkWyJjaGVuaF9wY3QiXSkgPD0gMC41CiAgICAgICAgICAgIHdz"
"LmFwcGVuZChbbiwgclsidGVuIl0sIHJvdW5kKHJbImR0Il0sIDQpLCByWyJkdF9sYW1fdHJvbiJdLCAixJDDoyBjw7MgcG9seWxpbmUsIMSR4buRaSBjaGnhur91IiwKICAgICAgICAgICAgICAgICAgICAgICBEQVQgaWYgb2sgYW5kIG5vdCByWyJjYW5oX2JhbyJd"
"IGVsc2UgQ0FOSF9CQU8gaWYgYWJzKGRbImNoZW5oX3BjdCJdKSA8PSAxIGVsc2UgTE9JLAogICAgICAgICAgICAgICAgICAgICAgIGYiUG9seWxpbmUgc+G6tW4gY8OzIHtkWydoYW5kbGUnXX06IHtkWydkdCddOi40Zn0gbcKyLCBjaMOqbmgge2RbJ2NoZW5oJ106"
"Ky40Zn0gbcKyICh7ZFsnY2hlbmhfcGN0J106Ky4yZn0lKS4gIgogICAgICAgICAgICAgICAgICAgICAgICsgIiAiLmpvaW4oclsiY2FuaF9iYW8iXSldKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHdzLmFwcGVuZChbbiwgclsidGVuIl0sIHJvdW5kKHJbImR0"
"Il0sIDQpLCByWyJkdF9sYW1fdHJvbiJdLCAiROG7sW5nIG3hu5tpIiwKICAgICAgICAgICAgICAgICAgICAgICBDQU5IX0JBTyBpZiByWyJjYW5oX2JhbyJdIGVsc2UgREFULCAiICIuam9pbihyWyJjYW5oX2JhbyJdICsgKAogICAgICAgICAgICAgICAgICAgICAg"
"ICAgICBbIkNo4buJbmggaMOsbmg6ICIgKyBjaGgubW9fdGFfY2hpbmgoclsiY2hpbmhfaGluaCJdKSArICIuIl0gaWYgci5nZXQoImNoaW5oX2hpbmgiKSBlbHNlIFtdKSldKQogICAgZm9yIHIgaW4gZGFfY29fY2h1YV9kYzoKICAgICAgICBuICs9IDEKICAgICAg"
"ICB3cy5hcHBlbmQoW24sIHJbInRlbiJdLCByb3VuZChyWyJkdF9jb19zYW4iXSwgNCksIHIxKHJbImR0X2NvX3NhbiJdKSwgIsSQw6MgY8OzIHBvbHlsaW5lLCBjaMawYSDEkeG7kWkgY2hp4bq/dSDEkcaw4bujYyIsCiAgICAgICAgICAgICAgICAgICBDQU5IX0JB"
"TywKICAgICAgICAgICAgICAgICAgIGYiUG9seWxpbmUgc+G6tW4gY8OzIHtyWydoYW5kbGUnXX0gKHtyWydkdF9jb19zYW4nXTouNGZ9IG3CsikuIE7DqXQgcmFuaCBxdWFuaCBwaMOybmcgY2jGsGEgxJHhu6cgxJHhu4MgZOG7sW5nIGzhuqFpICIKICAgICAgICAg"
"ICAgICAgICAgIGYixJHhu5ljIGzhuq1wIChraGUgaOG7nyBn4bqnbiBuaOG6pXQ6IHtyWydraGVfaG9fZ2FuX25oYXQnXVs6Ml19KS4gTXXhu5FuIMSR4buRaSBjaGnhur91IGPhuqduIMSRw7NuZyByYW5oIGNo4buXIGjhu58uIgogICAgICAgICAgICAgICAgICAg"
"KyAoIiIgaWYgclsiZG9uZyJdIGVsc2UgIiBQb2x5bGluZSBjaMawYSBi4bqtdCBDbG9zZWQuIildKQogICAgZm9yIHIgaW4gZmFpbGVkOgogICAgICAgIHdzLmFwcGVuZChbTm9uZSwgclsidGVuIl0sIE5vbmUsIE5vbmUsICJLaMO0bmcgxJHDs25nIGvDrW4gxJHG"
"sOG7o2MiLCBMT0ksCiAgICAgICAgICAgICAgICAgICBmIlbDuW5nIHF1YW5oICh7clsneHknXVswXX0sIHtyWyd4eSddWzFdfSkuIEtoZSBo4bufIGfhuqduIG5o4bqldDoge3JbJ2toZV9ob19nYW5fbmhhdCddWzozXX0iXSkKICAgIGZvciByIGluIGNodWFfdGVu"
"OgogICAgICAgIHdzLmFwcGVuZChbTm9uZSwgZiIoY2jGsGEgxJHhurd0IHTDqm4pIHThuqFpIHtyWyd4eSddfSIsIHJbImR0Il0sIHJbImR0X2xhbV90cm9uIl0sICJWw7luZyBrw61uIGNoxrBhIGPDsyB0w6puIiwgQ0FOSF9CQU8sCiAgICAgICAgICAgICAgICAg"
"ICAiQ+G6p24gxJHhurd0IHTDqm4gcGjDsm5nICh0ZXh0IGxheWVyIEEtVGV4dCkgxJHhu4MgZOG7sW5nIHBvbHlsaW5lLiJdKQogICAgZm9yIGMgaW4gd3NbMV06CiAgICAgICAgYy5mb250ID0gRm9udChib2xkPVRydWUpCiAgICBmb3IgY29sLCB3IGluIHppcCgi"
"QUJDREVGRyIsIFs1LCAyOCwgMjQsIDE4LCAyNiwgMTEsIDkwXSk6CiAgICAgICAgd3MuY29sdW1uX2RpbWVuc2lvbnNbY29sXS53aWR0aCA9IHcKICAgIHhsc3hfcGF0aCA9IG9zLnBhdGguam9pbihhLm91dF9kaXIsICJEaWVuVGljaFBob25nLnhsc3giKQogICAg"
"d2Iuc2F2ZSh4bHN4X3BhdGgpCiAgICBwbmdfcGF0aCA9IG9zLnBhdGguam9pbihhLm91dF9kaXIsICJ4ZW1fbGFpLnBuZyIpCiAgICBhbmhfeGVtX2xhaShwbmdfcGF0aCwgY2hhaW5zICsgWyhGYWxzZSwgbGlzdChsLmNvb3JkcykpIGZvciBsIGluIGtodW5nXSwg"
"cm9vbXMgKyBkYV9jbywgZmFpbGVkLCBbKHAsIHEpIGZvciBwLCBxLCBfIGluIHBhaXJzXSkKCiAgICByZXN1bHQgPSBkaWN0KGZpbGU9b3MucGF0aC5iYXNlbmFtZShhLmR4ZiksIGdhcF9tYXg9YS5nYXBfbWF4LCBsb3BfdHJhdF9tbT10X2luLCBraHVuZ19jdWE9"
"dGtfY3VhLAogICAgICAgICAgICAgICAgICBzb19jaGFpbj1sZW4oY2hhaW5zKSwgc29fY2F1X25vaT1sZW4ocGFpcnMpLAogICAgICAgICAgICAgICAgICBjaGluaF9oaW5oPU5vbmUgaWYgY2hpbmggaXMgTm9uZSBlbHNlIHtrOiB2IGZvciBrLCB2IGluIHRvbmdf"
"Y2guaXRlbXMoKSBpZiB2fSwKICAgICAgICAgICAgICAgICAgZHVuZ19tb2k9W2RpY3QodGVuPXJbInRlbiJdLCBkdD1yb3VuZChyWyJkdCJdLCA0KSwgZHRfbGFtX3Ryb249clsiZHRfbGFtX3Ryb24iXSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
"ZHRfdnVuZ19raW49cm91bmQoclsiZHRfdnVuZ19raW4iXSwgNCksIGNoaW5oX2hpbmg9clsiY2hpbmhfaGluaCJdLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBzb19kaW5oPWxlbihyWyJkaW5oIl0pLCBjYW5oX2Jhbz1yWyJjYW5oX2JhbyJdKSBm"
"b3IgciBpbiByb29tc10sCiAgICAgICAgICAgICAgICAgIGRhX2NvX2RvaV9jaGlldT1bZGljdCh0ZW49clsidGVuIl0sIGR0X21vaT1yb3VuZChyWyJkdCJdLCA0KSwgY2hpbmhfaGluaD1yWyJjaGluaF9oaW5oIl0sCiAgICAgICAgICAgICAgICAgICAgICAgICAg"
"ICAgICAgICAgICAgICBoYW5kbGU9clsiZGFfY28iXVsiaGFuZGxlIl0sCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBkdF9jb19zYW49cm91bmQoclsiZGFfY28iXVsiZHQiXSwgNCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
"ICAgICAgICAgICBjaGVuaF9wY3Q9cm91bmQoclsiZGFfY28iXVsiY2hlbmhfcGN0Il0sIDMpLCBjYW5oX2Jhbz1yWyJjYW5oX2JhbyJdKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGZvciByIGluIGRhX2NvXSwKICAgICAgICAgICAgICAgICAg"
"ZGFfY29fY2h1YV9kb2lfY2hpZXU9W2RpY3QodGVuPXJbInRlbiJdLCBoYW5kbGU9clsiaGFuZGxlIl0sIGR0X2NvX3Nhbj1yb3VuZChyWyJkdF9jb19zYW4iXSwgNCksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGRvbmc9clsi"
"ZG9uZyJdLCBraGVfaG9fZ2FuX25oYXQ9clsia2hlX2hvX2dhbl9uaGF0Il1bOjNdKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZm9yIHIgaW4gZGFfY29fY2h1YV9kY10sCiAgICAgICAgICAgICAgICAgIGtob25nX2RvbmdfZHVvYz1m"
"YWlsZWQsIHZ1bmdfY2h1YV90ZW49Y2h1YV90ZW4sCiAgICAgICAgICAgICAgICAgIHZhbl9kZT1bZGljdChtdWM9bSwgaGFuZ19tdWM9aCwgbW9fdGE9ZCkgZm9yIG0sIGgsIGQgaW4gcHJvYmxlbXNdLAogICAgICAgICAgICAgICAgICBzY3I9c2NyX3BhdGgsIHhs"
"c3g9eGxzeF9wYXRoLCBhbmhfeGVtX2xhaT1wbmdfcGF0aCkKICAgIGlmIGEuZGVidWc6CiAgICAgICAgcmVzdWx0WyJjYXVfbm9pIl0gPSBbZGljdChhPShyb3VuZChwWzBdKSwgcm91bmQocFsxXSkpLCBiPShyb3VuZChxWzBdKSwgcm91bmQocVsxXSkpLCBkYWk9"
"cm91bmQoZCkpCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZm9yIHAsIHEsIGQgaW4gcGFpcnNdCiAgICBwcmludChqc29uLmR1bXBzKHJlc3VsdCwgZW5zdXJlX2FzY2lpPUZhbHNlLCBpbmRlbnQ9MikpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoK"
"ICAgIG1haW4oKQo="
)
("dien-tich-ch/scripts/chinh_hinh.py"
"IyEvdXNyL2Jpbi9lbnYgcHl0aG9uCiMgLSotIGNvZGluZzogdXRmLTggLSotCiIiIkNoaW5oIGhpbmggcG9seWxpbmUgcGhvbmcgLyBkdW9uZyBibyBjYW4gdGhlbyBjYWMgbG9pIG5ndW9pIGR1bmcgc3VhIHRheSAoQ1QxIHRhbmcgNUEtMTAsIDA4LzEwLzIwMjYp"
"LgoKUXV5IHRhYyAocmVmZXJlbmNlcy9xdXktdW9jLW1hdC1iYW5nLXRhbmcubWQsIHF1eWV0IGRpbmggMTEtMTcpOgogMS0yIGNhdF9raW5oICAgOiBvIG1vIC8gdmFjaCBraW5oIC8ga2h1bmcgY3VhIHNvIGRhdCBOR09BSSBtYXQgcGhhbmcgdHVvbmcgLT4gcmFu"
"aCB0aGVvIGR1b25nIGtlbyBkYWkgbWF0IHR1b25nCiAgICAgICAgICAgICAgICAgIHF1YSBkYXUgdHVvbmcgKHZ1b25nIGdvYyksIGJvIHBoYW4gbG9pIHJhIGtpbmggKHNhdSA8PSA0MDAgbW0pLgogMyAgIGRvbl9kaW5oICAgOiBibyBnYWkgLyBraGFjIG5obyAo"
"PD0gNjAgbW0pIHZhIHZhdCBjaGVvIG5nYW4gbyBnb2MgdHVvbmcgOTAgZG87IGRvYW4gdGhhbmcga2hvbmcgZ2FwIGtodWMuCiA0ICAgb3Bfd2MgICAgICA6IHBob25nIFdDIHRydSBsb3Agb3AgMTAgbW0gKHRoZW8gbmV0IG9wIG5ldSBkYSB2ZSwgbmV1IGtob25n"
"IGx1aSAxMCBtbSB0dSBtYXQgdHJhdCkuCiA1ICAgZGF1X3R1b25nICA6IGNhbmggbmFtIHRyZW4gbmV0IGxvaSB0dW9uZyAoQS1XYWxsL1MtV2FsbCwga2hvbmcgY28gbmV0IHRyYXQpID0gZGF1IHR1b25nIGdhY2ggY2h1YSB2ZSB0cmF0IC0+IGx1aSAxNSBtbS4K"
"IDYgICBkYWlfdHVvbmcgIDogZHVvbmcgYm8gY2FuIGNoaSBsYXAgZGFpIHR1b25nIEdJVUEgaGFpIG1hdCBwaG9uZyBkb2kgZGllbiAodHVvbmcgbmdhbiwgbyBjdWEpOyBraG9uZyBsYXAgZ29jIGxvbQogICAgICAgICAgICAgICAgICAtPiBraG9uZyBhbiB2YW8g"
"dHVvbmcgYmFvIG5nb2FpLgogNyAgIGJhdV9sb19naWEgOiBsbyBnaWEgLyBiYW4gY29uZyBkbyB0b2kgbWF0IHRyb25nIGJhdSBCVCAvIGxhbiBjYW4gKG5ldCBiYXUgZ2FuIG5oYXQgcGhpYSBuZ29haSwgPD0gODAgbW0pLgpDaGkgeHUgbHkgY2FuaCB0cnVjIGdp"
"YW8gKG1hdCBiYW5nIENUMSB2dW9uZyBnb2MpOyBjYW5oIHhpZW4gZ2l1IG5ndXllbi4KCkR1bmcgY2h1bmc6IG1hdF9iYW5nX3RhbmcucHkgKG1hdCBiYW5nIHRhbmcpLCB0YW9fcG9seWxpbmVfcGhvbmcucHkgdmEgdGFvX2R1b25nX2JvX2Nhbl9oby5weSAoY2Fu"
"IGRvbiBsZSwgMTAvMTAvMjAyNikKcXVhIGNoaW5oX3Bob25nKCkgKHRyaW5oIHR1IGNoaW5oIGhpbmggcG9seWdvbiBwaG9uZykgdmEgZHVvbmdfYm8oKSAoZGFpIHR1b25nICsgbGFwIGxvIG5obyBjaG8gZHVvbmcgYm8gY2FuKS4KIiIiCmltcG9ydCBjb2xsZWN0"
"aW9ucwppbXBvcnQgbWF0aAoKaW1wb3J0IHNoYXBlbHkKZnJvbSBzaGFwZWx5Lmdlb21ldHJ5IGltcG9ydCBMaW5lU3RyaW5nLCBNdWx0aVBvbHlnb24sIFBvbHlnb24sIGJveApmcm9tIHNoYXBlbHkuZ2VvbWV0cnkucG9seWdvbiBpbXBvcnQgb3JpZW50CmZyb20g"
"c2hhcGVseS5vcHMgaW1wb3J0IHNwbGl0LCB1bmFyeV91bmlvbgoKVE9MID0gMi4wCkxPUCA9IHsKICAgICJ0cmF0IjogeyJhLXZ1YSB0cmF0In0sCiAgICAidHVvbmciOiB7ImEtd2FsbCIsICJzLXdhbGwiLCAiYS1jb2x1bW4ifSwKICAgICJiYXUiOiB7ImFfd2Fs"
"bCBidCIsICJhLWxpbmUiLCAiYS1sYW5jYW4ifSwKICAgICMga2luaCAvIGtodW5nIGN1YSAvIGRvIChDVDE6IGtpbmggdmUgdHJlbiBBLURvb3IsIGRvIGN1YSBzbyAndGhhbmggZHVuZycgdHJlbiBsYXllciA0KQogICAgImtpbmgiOiB7ImEtZG9vciIsICJhLWPh"
"u61hIiwgImEtY3VhIiwgImEtd2luZG93IiwgImEtZ2xheiIsICJhLWdsYXNzIiwgIueOu+eSg+WxgiIsICJrw61uaCIsICJraW5oIiwgImEtd2FsbC1nIiwKICAgICAgICAgICAgICJhLXdpbmRvdy1nIiwgIm5ob20iLCAiNCJ9LAp9CgoKY2xhc3MgTmV0TmVuOgog"
"ICAgIiIiRG9hbiB0aGFuZyB0cnVjIGdpYW8gY3VhIG5lbiBraWVuIHRydWMsIHBoYW4gbG9wIHRyYXQgLyB0dW9uZyAvIGJhdS4iIiIKCiAgICBkZWYgX19pbml0X18oc2VsZiwgc2Vncyk6CiAgICAgICAgc2VsZi5kcyA9IHtrOiBbXSBmb3IgayBpbiBMT1B9CiAg"
"ICAgICAgZm9yIHgxLCB5MSwgeDIsIHkyLCBsb3AgaW4gc2VnczoKICAgICAgICAgICAgaWYgYWJzKHgxIC0geDIpIDw9IDAuNSBvciBhYnMoeTEgLSB5MikgPD0gMC41OgogICAgICAgICAgICAgICAgc2VsZi5kc1tsb3BdLmFwcGVuZCgoeDEsIHkxLCB4MiwgeTIp"
"KQogICAgICAgIHNlbGYudHJlZSA9IHtrOiAoc2hhcGVseS5TVFJ0cmVlKFtMaW5lU3RyaW5nKFsoYSwgYiksIChjLCBkKV0pIGZvciBhLCBiLCBjLCBkIGluIHZdKSBpZiB2IGVsc2UgTm9uZSwgdikKICAgICAgICAgICAgICAgICAgICAgZm9yIGssIHYgaW4gc2Vs"
"Zi5kcy5pdGVtcygpfQoKICAgIGRlZiBfY2FuZHMoc2VsZiwgbG9wcywgZyk6CiAgICAgICAgZm9yIGsgaW4gbG9wczoKICAgICAgICAgICAgdCwgdiA9IHNlbGYudHJlZVtrXQogICAgICAgICAgICBpZiB0IGlzIG5vdCBOb25lOgogICAgICAgICAgICAgICAgZm9y"
"IGkgaW4gdC5xdWVyeShnKToKICAgICAgICAgICAgICAgICAgICB5aWVsZCBrLCB2W2ldCgogICAgZGVmIGhvX3RybyhzZWxmLCBhLCBiLCBsb3BzLCB0b2w9VE9MKToKICAgICAgICAiIiJDaGlldSBkYWkgZG9hbiBhLWIgbmFtIHRyZW4gbmV0IHRodW9jIGNhYyBs"
"b3AgJ2xvcHMnIChjdW5nIHBodW9uZywgbGVjaCA8PSB0b2wpLiIiIgogICAgICAgIGRvYyA9IGFicyhhWzBdIC0gYlswXSkgPCBhYnMoYVsxXSAtIGJbMV0pCiAgICAgICAgazAsIGsxID0gKDEsIDApIGlmIGRvYyBlbHNlICgwLCAxKSAgICAgICAgICAjIGswOiB0"
"cnVjIGRvYyB0aGVvIGNhbmgsIGsxOiB0cnVjIHZ1b25nIGdvYwogICAgICAgIGxvLCBoaSA9IHNvcnRlZCgoYVtrMF0sIGJbazBdKSkKICAgICAgICBjID0gKGFbazFdICsgYltrMV0pIC8gMgogICAgICAgIGl2ID0gW10KICAgICAgICBmb3IgXywgcyBpbiBzZWxm"
"Ll9jYW5kcyhsb3BzLCBMaW5lU3RyaW5nKFthLCBiXSkuYnVmZmVyKHRvbCkpOgogICAgICAgICAgICBwLCBxID0gKHNbMF0sIHNbMV0pLCAoc1syXSwgc1szXSkKICAgICAgICAgICAgaWYgYWJzKHBbazFdIC0gYykgPiB0b2wgb3IgYWJzKHFbazFdIC0gYykgPiB0"
"b2w6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBzMCwgczEgPSBzb3J0ZWQoKHBbazBdLCBxW2swXSkpCiAgICAgICAgICAgIHgwLCB4MSA9IG1heChsbywgczApLCBtaW4oaGksIHMxKQogICAgICAgICAgICBpZiB4MSA+IHgwOgogICAgICAg"
"ICAgICAgICAgaXYuYXBwZW5kKCh4MCwgeDEpKQogICAgICAgIGl2LnNvcnQoKQogICAgICAgIHRvbmcsIGN1ciA9IDAuMCwgTm9uZQogICAgICAgIGZvciB4MCwgeDEgaW4gaXY6CiAgICAgICAgICAgIGlmIGN1ciBpcyBOb25lIG9yIHgwID4gY3VyWzFdOgogICAg"
"ICAgICAgICAgICAgaWYgY3VyOgogICAgICAgICAgICAgICAgICAgIHRvbmcgKz0gY3VyWzFdIC0gY3VyWzBdCiAgICAgICAgICAgICAgICBjdXIgPSBbeDAsIHgxXQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgY3VyWzFdID0gbWF4KGN1clsxXSwg"
"eDEpCiAgICAgICAgaWYgY3VyOgogICAgICAgICAgICB0b25nICs9IGN1clsxXSAtIGN1clswXQogICAgICAgIHJldHVybiB0b25nCgogICAgZGVmIHNvbmdfc29uZyhzZWxmLCBhLCBiLCBuLCBsb3BzLCBkbWluLCBkbWF4LCB0aV9sZT0wLjUpOgogICAgICAgICIi"
"Iktob2FuZyBjYWNoIHRvaSBjYWMgbmV0IHNvbmcgc29uZyBwaGlhIGh1b25nIG4gKHZlY3RvciBkb24gdmkpIHRyb25nIChkbWluLCBkbWF4XSwgcGh1ID49IHRpX2xlIGNhbmguIiIiCiAgICAgICAgZG9jID0gYWJzKGFbMF0gLSBiWzBdKSA8IGFicyhhWzFdIC0g"
"YlsxXSkKICAgICAgICBrMCwgazEgPSAoMSwgMCkgaWYgZG9jIGVsc2UgKDAsIDEpCiAgICAgICAgbG8sIGhpID0gc29ydGVkKChhW2swXSwgYltrMF0pKQogICAgICAgIEwgPSBoaSAtIGxvCiAgICAgICAgYyA9IChhW2sxXSArIGJbazFdKSAvIDIKICAgICAgICBz"
"ZyA9IG5bazFdCiAgICAgICAgdnVuZyA9IGJveCgqKGxhbWJkYSB4cywgeXM6IChtaW4oeHMpLCBtaW4oeXMpLCBtYXgoeHMpLCBtYXgoeXMpKSkoCiAgICAgICAgICAgIFthWzBdLCBiWzBdLCBhWzBdICsgblswXSAqIGRtYXgsIGJbMF0gKyBuWzBdICogZG1heF0s"
"IFthWzFdLCBiWzFdLCBhWzFdICsgblsxXSAqIGRtYXgsIGJbMV0gKyBuWzFdICogZG1heF0pKQogICAgICAgIHBodSA9IHt9CiAgICAgICAgZm9yIF8sIHMgaW4gc2VsZi5fY2FuZHMobG9wcywgdnVuZyk6CiAgICAgICAgICAgIHAsIHEgPSAoc1swXSwgc1sxXSks"
"IChzWzJdLCBzWzNdKQogICAgICAgICAgICBpZiBhYnMocFtrMV0gLSBxW2sxXSkgPiAwLjU6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBkID0gKHBbazFdIC0gYykgKiBzZwogICAgICAgICAgICBpZiBub3QgKGRtaW4gPCBkIDw9IGRtYXgp"
"OgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgczAsIHMxID0gc29ydGVkKChwW2swXSwgcVtrMF0pKQogICAgICAgICAgICBvdiA9IG1pbihoaSwgczEpIC0gbWF4KGxvLCBzMCkKICAgICAgICAgICAgaWYgb3YgPiAwOgogICAgICAgICAgICAg"
"ICAgcGh1W3JvdW5kKGQsIDEpXSA9IHBodS5nZXQocm91bmQoZCwgMSksIDAuMCkgKyBvdgogICAgICAgIHJldHVybiBzb3J0ZWQoZCBmb3IgZCwgdiBpbiBwaHUuaXRlbXMoKSBpZiB2ID49IHRpX2xlICogTCkKCiAgICBkZWYgZGllbV9kYXUoc2VsZiwgbG9wcywg"
"Zyk6CiAgICAgICAgb3V0ID0gW10KICAgICAgICBmb3IgXywgcyBpbiBzZWxmLl9jYW5kcyhsb3BzLCBnKToKICAgICAgICAgICAgb3V0ICs9IFsoc1swXSwgc1sxXSksIChzWzJdLCBzWzNdKV0KICAgICAgICByZXR1cm4gb3V0CgoKIyAtLS0tLS0tLS0tLS0tLS0t"
"LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIF92b25nKHBvbHkpOgogICAgcCA9IG9yaWVudChwb2x5LCAxLjApCiAgICBy"
"ZXR1cm4gW3R1cGxlKGMpIGZvciBjIGluIHAuZXh0ZXJpb3IuY29vcmRzWzotMV1dCgoKZGVmIF9wb2x5KHB0cywgaG89KCkpOgogICAgdHJ5OgogICAgICAgIGcgPSBQb2x5Z29uKHB0cywgaG8pCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHJldHVybiBO"
"b25lCiAgICByZXR1cm4gZyBpZiBnLmlzX3ZhbGlkIGFuZCBnLmFyZWEgPiAwIGVsc2UgTm9uZQoKCmRlZiBfdHJ1YyhhLCBiLCB0b2w9MC41KToKICAgIHJldHVybiBhYnMoYVswXSAtIGJbMF0pIDw9IHRvbCBvciBhYnMoYVsxXSAtIGJbMV0pIDw9IHRvbAoKCmRl"
"ZiBfa2NfZHVvbmcodiwgcCwgbik6CiAgICAiIiJLaG9hbmcgY2FjaCBkaWVtIHYgdG9pIGR1b25nIHRoYW5nIHAtbi4iIiIKICAgIEwgPSBtYXRoLmRpc3QocCwgbikKICAgIGlmIEwgPCAxZS05OgogICAgICAgIHJldHVybiBtYXRoLmRpc3QodiwgcCkKICAgIHJl"
"dHVybiBhYnMoKG5bMF0gLSBwWzBdKSAqIChwWzFdIC0gdlsxXSkgLSAocFswXSAtIHZbMF0pICogKG5bMV0gLSBwWzFdKSkgLyBMCgoKZGVmIGxhbV90aGFuZyhwdHMsIHRvbD0xLjUpOgogICAgIiIiQ2FuaCBsZWNoIHRydWMgPD0gdG9sIG1tIC0+IG5hbiB0aGFu"
"ZyAoZGF0IGxhaSB0b2EgZG8gZGluaCBzYXUpLiIiIgogICAgcHRzID0gW2xpc3QocCkgZm9yIHAgaW4gcHRzXQogICAgZm9yIGkgaW4gcmFuZ2UobGVuKHB0cykpOgogICAgICAgIGEsIGIgPSBwdHNbaV0sIHB0c1soaSArIDEpICUgbGVuKHB0cyldCiAgICAgICAg"
"aWYgMCA8IGFicyhhWzBdIC0gYlswXSkgPD0gdG9sIGFuZCBhYnMoYVsxXSAtIGJbMV0pID4gMTAgKiB0b2w6CiAgICAgICAgICAgIGJbMF0gPSBhWzBdCiAgICAgICAgZWxpZiAwIDwgYWJzKGFbMV0gLSBiWzFdKSA8PSB0b2wgYW5kIGFicyhhWzBdIC0gYlswXSkg"
"PiAxMCAqIHRvbDoKICAgICAgICAgICAgYlsxXSA9IGFbMV0KICAgIHJldHVybiBbdHVwbGUocCkgZm9yIHAgaW4gcHRzXQoKCmRlZiB2dW9uZ19nb2MocG9seSwgbmV0PU5vbmUsIGxlY2hfbWF4PTQwLjApOgogICAgIiIiTG9pIDEgKGRvIGNoZW8pOiBjYW5oIGdh"
"biB0cnVjIG5odW5nIGxlY2ggMSw1LWxlY2hfbWF4IG1tIChkbyBsYW0gZ29uIC8gbm9pIGRpbmgpIC0+IGJhYyB2dW9uZyBnb2MgMiBkb2FuLAogICAgZ29jIGNob24gdGhlbyBuZXQgbmVuIChkb2FuIGRhaSBuYW0gdHJlbiBuZXQgdHVvbmcvdHJhdC9iYXUpLiBT"
"dWEgdHVuZyBjYW5oLCBtb2kgbGFuIGtpZW0gdHJhIGhpbmggaG9wIGxlLgogICAgVHJhIHZlIChwb2x5LCBzb19jYW5oX3N1YSkuIiIiCiAgICBpZiBwb2x5IGlzIE5vbmUgb3IgcG9seS5pc19lbXB0eToKICAgICAgICByZXR1cm4gcG9seSwgMAogICAgaG8gPSBb"
"bGlzdChoLmNvb3JkcykgZm9yIGggaW4gcG9seS5pbnRlcmlvcnNdCiAgICBwdHMgPSBsYW1fdGhhbmcoX3ZvbmcocG9seSkpCiAgICBnMCA9IF9wb2x5KHB0cywgaG8pCiAgICBpZiBnMCBpcyBOb25lOgogICAgICAgIHJldHVybiBwb2x5LCAwCiAgICBzdWEgPSAw"
"CiAgICBpID0gMAogICAgd2hpbGUgaSA8IGxlbihwdHMpOgogICAgICAgIGEsIGIgPSBwdHNbaV0sIHB0c1soaSArIDEpICUgbGVuKHB0cyldCiAgICAgICAgZHgsIGR5ID0gYWJzKGFbMF0gLSBiWzBdKSwgYWJzKGFbMV0gLSBiWzFdKQogICAgICAgIG5obywgbG9u"
"ID0gbWluKGR4LCBkeSksIG1heChkeCwgZHkpCiAgICAgICAgaWYgMS41IDwgbmhvIDw9IGxlY2hfbWF4IGFuZCBsb24gPj0gMyAqIG5obzoKICAgICAgICAgICAgYzEsIGMyID0gKGFbMF0sIGJbMV0pLCAoYlswXSwgYVsxXSkKICAgICAgICAgICAgaWYgbmV0IGlz"
"IG5vdCBOb25lOgogICAgICAgICAgICAgICAgczEgPSBuZXQuaG9fdHJvKGEsIGMxLCAoInRyYXQiLCAidHVvbmciLCAiYmF1IikpICsgbmV0LmhvX3RybyhjMSwgYiwgKCJ0cmF0IiwgInR1b25nIiwgImJhdSIpKQogICAgICAgICAgICAgICAgczIgPSBuZXQuaG9f"
"dHJvKGEsIGMyLCAoInRyYXQiLCAidHVvbmciLCAiYmF1IikpICsgbmV0LmhvX3RybyhjMiwgYiwgKCJ0cmF0IiwgInR1b25nIiwgImJhdSIpKQogICAgICAgICAgICAgICAgdGh1ID0gW2MxLCBjMl0gaWYgczEgPj0gczIgZWxzZSBbYzIsIGMxXQogICAgICAgICAg"
"ICBlbHNlOgogICAgICAgICAgICAgICAgdGh1ID0gW2MxLCBjMl0gaWYgZHggPCBkeSBlbHNlIFtjMiwgYzFdCiAgICAgICAgICAgIGZvciBjIGluIHRodToKICAgICAgICAgICAgICAgIGNhbmQgPSBwdHNbOmkgKyAxXSArIFtjXSArIHB0c1tpICsgMTpdCiAgICAg"
"ICAgICAgICAgICBpZiBfcG9seShjYW5kLCBobykgaXMgbm90IE5vbmU6CiAgICAgICAgICAgICAgICAgICAgcHRzID0gY2FuZAogICAgICAgICAgICAgICAgICAgIHN1YSArPSAxCiAgICAgICAgICAgICAgICAgICAgaSArPSAxCiAgICAgICAgICAgICAgICAgICAg"
"YnJlYWsKICAgICAgICBpICs9IDEKICAgIGlmIG5vdCBzdWE6CiAgICAgICAgcmV0dXJuIChnMCwgMCkKICAgIGcgPSBfcG9seShwdHMsIGhvKQogICAgcmV0dXJuIChnLCBzdWEpIGlmIGcgaXMgbm90IE5vbmUgZWxzZSAocG9seSwgMCkKCgpkZWYgZG9uX2Rpbmgo"
"cG9seSwgbmV0PU5vbmUsIHRvbD02MC4wLCBjaGVvPTEyMC4wKToKICAgICIiIkxvaSAzOiBibyBkaW5oIHRodWEsIGdhaS9raGFjIDw9IHRvbCBtbSwgdmF0IGNoZW8gbmdhbiBvIGdvYyB2dW9uZy4gVHJhIHZlIChwb2x5LCBzb19kaW5oX2JvKS4iIiIKICAgIGlm"
"IHBvbHkgaXMgTm9uZSBvciBwb2x5LmlzX2VtcHR5OgogICAgICAgIHJldHVybiBwb2x5LCAwCiAgICBobyA9IFtsaXN0KGguY29vcmRzKSBmb3IgaCBpbiBwb2x5LmludGVyaW9yc10KICAgIHB0cyA9IGxhbV90aGFuZyhfdm9uZyhwb2x5KSkKICAgIGJvID0gMAog"
"ICAgZG9pID0gVHJ1ZQogICAgd2hpbGUgZG9pIGFuZCBsZW4ocHRzKSA+IDQ6CiAgICAgICAgZG9pID0gRmFsc2UKICAgICAgICBuID0gbGVuKHB0cykKICAgICAgICBmb3IgaSBpbiByYW5nZShuKToKICAgICAgICAgICAgcCwgdiwgcSA9IHB0c1tpIC0gMV0sIHB0"
"c1tpXSwgcHRzWyhpICsgMSkgJSBuXQogICAgICAgICAgICAjIGRpbmggdGhhbmcgaGFuZyAvIHRydW5nCiAgICAgICAgICAgIGlmIG1hdGguZGlzdChwLCB2KSA8IDAuNSBvciBfa2NfZHVvbmcodiwgcCwgcSkgPCAwLjU6CiAgICAgICAgICAgICAgICBjYW5kID0g"
"cHRzWzppXSArIHB0c1tpICsgMTpdCiAgICAgICAgICAgICMgZ2FpIC8ga2hhYyAxIGRpbmg6IGhhaSBkaW5oIGJlbiBjYW5oIGN1bmcgdHJ1YywgZGluaCBsZWNoIDw9IHRvbAogICAgICAgICAgICBlbGlmIF90cnVjKHAsIHEpIGFuZCBfa2NfZHVvbmcodiwgcCwg"
"cSkgPD0gdG9sIGFuZCBtYXRoLmRpc3QocCwgcSkgPiAxOgogICAgICAgICAgICAgICAgY2FuZCA9IHB0c1s6aV0gKyBwdHNbaSArIDE6XQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgY2FuZCA9IE5vbmUKICAgICAgICAgICAgaWYgY2FuZCBpcyBu"
"b3QgTm9uZToKICAgICAgICAgICAgICAgIGcsIGcwID0gX3BvbHkoY2FuZCwgaG8pLCBfcG9seShwdHMsIGhvKQogICAgICAgICAgICAgICAgaWYgZyBpcyBub3QgTm9uZSBhbmQgKGcwIGlzIE5vbmUgb3IgYWJzKGcuYXJlYSAtIGcwLmFyZWEpIDwgbWF4KHRvbCAq"
"IDQwMCwgMC4wMiAqIGcuYXJlYSkpOgogICAgICAgICAgICAgICAgICAgIHB0cywgZG9pLCBibyA9IGNhbmQsIFRydWUsIGJvICsgMQogICAgICAgICAgICAgICAgICAgIGJyZWFrCiAgICAgICAgaWYgZG9pOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIG4g"
"PSBsZW4ocHRzKQogICAgICAgIGZvciBpIGluIHJhbmdlKG4pOgogICAgICAgICAgICBwLCBhLCBiLCBxID0gcHRzW2kgLSAxXSwgcHRzW2ldLCBwdHNbKGkgKyAxKSAlIG5dLCBwdHNbKGkgKyAyKSAlIG5dCiAgICAgICAgICAgICMga2hhYyAyIGRpbmg6IHAsIHEg"
"Y3VuZyB0cnVjLCBhLCBiIHNhdCBkdW9uZyBwLXEKICAgICAgICAgICAgaWYgbiA+IDUgYW5kIF90cnVjKHAsIHEpIGFuZCBfa2NfZHVvbmcoYSwgcCwgcSkgPD0gdG9sIGFuZCBfa2NfZHVvbmcoYiwgcCwgcSkgPD0gdG9sIGFuZCBtYXRoLmRpc3QoYSwgYikgPD0g"
"Mi41ICogdG9sOgogICAgICAgICAgICAgICAgaWR4ID0ge2kgJSBuLCAoaSArIDEpICUgbn0KICAgICAgICAgICAgICAgIGNhbmQgPSBbcHRzW2tdIGZvciBrIGluIHJhbmdlKG4pIGlmIGsgbm90IGluIGlkeF0KICAgICAgICAgICAgIyB2YXQgY2hlbyBuZ2FuIGEt"
"YiBnaXVhIGhhaSBjYW5oIHRydWMgZ2lhbwogICAgICAgICAgICBlbGlmIG5vdCBfdHJ1YyhhLCBiLCAxLjApIGFuZCBtYXRoLmRpc3QoYSwgYikgPD0gY2hlbyBhbmQgX3RydWMocCwgYSwgMS4wKSBhbmQgX3RydWMoYiwgcSwgMS4wKToKICAgICAgICAgICAgICAg"
"IG5nYW5nX3BhID0gYWJzKHBbMV0gLSBhWzFdKSA8PSAxLjAKICAgICAgICAgICAgICAgIG5nYW5nX2JxID0gYWJzKGJbMV0gLSBxWzFdKSA8PSAxLjAKICAgICAgICAgICAgICAgIGlmIG5nYW5nX3BhICE9IG5nYW5nX2JxOiAgICAgICAgICAgICAgICAgICAgICAj"
"IHZ1b25nIGdvYyAtPiBnaWFvIGRpZW0KICAgICAgICAgICAgICAgICAgICBjID0gKGJbMF0sIGFbMV0pIGlmIG5nYW5nX3BhIGVsc2UgKGFbMF0sIGJbMV0pCiAgICAgICAgICAgICAgICBlbHNlOiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
"ICAgIyBzb25nIHNvbmcgLT4gYmFjIHZ1b25nLCBjaG9uIGdvYyBiYW0gbmV0CiAgICAgICAgICAgICAgICAgICAgYzEsIGMyID0gKGJbMF0sIGFbMV0pLCAoYVswXSwgYlsxXSkKICAgICAgICAgICAgICAgICAgICBpZiBuZXQgaXMgbm90IE5vbmU6CiAgICAgICAg"
"ICAgICAgICAgICAgICAgIHMxID0gbmV0LmhvX3RybyhhLCBjMSwgKCJ0cmF0IiwgInR1b25nIiwgImJhdSIpKSArIG5ldC5ob190cm8oYzEsIGIsICgidHJhdCIsICJ0dW9uZyIsICJiYXUiKSkKICAgICAgICAgICAgICAgICAgICAgICAgczIgPSBuZXQuaG9fdHJv"
"KGEsIGMyLCAoInRyYXQiLCAidHVvbmciLCAiYmF1IikpICsgbmV0LmhvX3RybyhjMiwgYiwgKCJ0cmF0IiwgInR1b25nIiwgImJhdSIpKQogICAgICAgICAgICAgICAgICAgICAgICBjID0gYzEgaWYgczEgPj0gczIgZWxzZSBjMgogICAgICAgICAgICAgICAgICAg"
"IGVsc2U6CiAgICAgICAgICAgICAgICAgICAgICAgIGMgPSBjMQogICAgICAgICAgICAgICAgY2FuZCA9IFtwdHNba10gZm9yIGsgaW4gcmFuZ2UobikgaWYgayBub3QgaW4ge2kgJSBuLCAoaSArIDEpICUgbn1dCiAgICAgICAgICAgICAgICBjYW5kLmluc2VydChp"
"ICUgbiBpZiBpICUgbiA8IGxlbihjYW5kKSArIDEgZWxzZSBsZW4oY2FuZCksIGMpCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBnLCBnMCA9IF9wb2x5KGNhbmQsIGhvKSwgX3BvbHkocHRzLCBobykKICAgICAg"
"ICAgICAgaWYgZyBpcyBub3QgTm9uZSBhbmQgKGcwIGlzIE5vbmUgb3IgYWJzKGcuYXJlYSAtIGcwLmFyZWEpIDwgbWF4KGNoZW8gKiBjaGVvLCAwLjAyICogZy5hcmVhKSk6CiAgICAgICAgICAgICAgICBwdHMsIGRvaSwgYm8gPSBjYW5kLCBUcnVlLCBibyArIDEK"
"ICAgICAgICAgICAgICAgIGJyZWFrCiAgICBnID0gX3BvbHkocHRzLCBobykKICAgIHJldHVybiAoZyBpZiBnIGlzIG5vdCBOb25lIGVsc2UgcG9seSksIGJvCgoKZGVmIF9raG9uZ19ob190cm8ocG9seSwgbmV0LCBsb3BzPSgidHJhdCIsICJ0dW9uZyIsICJiYXUi"
"KSk6CiAgICAiIiJDYWMgY2FuaCBjdWEgcG9seSBraG9uZyBuYW0gdHJlbiBuZXQgdHVvbmcvdHJhdC9iYXUgKGtpbmgsIGtodW5nIGN1YSwgZG9hbiBkb25nIG8gbW8pLiIiIgogICAgcHRzID0gX3ZvbmcocG9seSkKICAgIG91dCA9IFtdCiAgICBmb3IgaSBpbiBy"
"YW5nZShsZW4ocHRzKSk6CiAgICAgICAgYSwgYiA9IHB0c1tpXSwgcHRzWyhpICsgMSkgJSBsZW4ocHRzKV0KICAgICAgICBMID0gbWF0aC5kaXN0KGEsIGIpCiAgICAgICAgaWYgTCA+IDEgYW5kIF90cnVjKGEsIGIpIGFuZCBuZXQuaG9fdHJvKGEsIGIsIGxvcHMp"
"IDwgMC41ICogTDoKICAgICAgICAgICAgb3V0LmFwcGVuZCgoYSwgYikpCiAgICByZXR1cm4gb3V0CgoKZGVmIGNhdF9raW5oKHBvbHksIG5ldCwgc2F1PTQwMC4wLCB0aV9sZT0wLjYsIHRpX2xlX2tpbmg9MC4zLCBkdF9tYXg9My4wZTYpOgogICAgIiIiTG9pIDEt"
"MjogY2F0IHBoYW4gbG9pIHJhIGtpbmgva2h1bmcgY3VhIG5hbSBuZ29haSBkdW9uZyBrZW8gZGFpIG1hdCB0dW9uZyBxdWEgZGF1IHR1b25nLgoKICAgIER1b25nIGNhdDogZHVvbmcgdHJ1YyBnaWFvIHF1YSBkYXUgbXV0IG5ldCB0dW9uZy90cmF0IGdhbiBjYW5o"
"IGtpbmguIFBoYW4gYmkgY2F0OiBzYXUgPD0gJ3NhdScsIGJpZW4gKHRydSBkdW9uZyBjYXQpCiAgICA+PSB0aV9sZSBraG9uZyBiYW0gdHVvbmcvdHJhdC9iYXUgVkEgPj0gdGlfbGVfa2luaCBiYW0gbmV0IGtpbmgva2h1bmcgY3VhIChkZSBraG9uZyBjYXQgbmhh"
"bSBkb2FuIGRvbmcgbyBtbykuCiAgICBNb2kgdm9uZyBjaG9uIHBoYW4gY2F0IG5obyBuaGF0OyBjYW5oIG1vaSB0YW8gcmEgKHRyZW4gZHVvbmcgY2F0KSBjb2kgbmh1IGRhIGJhbSBuZXQuCiAgICAiIiIKICAgIGlmIHBvbHkgaXMgTm9uZSBvciBwb2x5LmlzX2Vt"
"cHR5OgogICAgICAgIHJldHVybiBwb2x5LCAwCiAgICBibyA9IDAKICAgIGRhX2NhdCA9IFtdCiAgICBmb3IgXyBpbiByYW5nZSgxMik6CiAgICAgICAga2ggPSBbZSBmb3IgZSBpbiBfa2hvbmdfaG9fdHJvKHBvbHksIG5ldCkgaWYgbmV0LmhvX3RybyhlWzBdLCBl"
"WzFdLCAoImtpbmgiLCksIHRvbD04KSA+IDAuMyAqIG1hdGguZGlzdCgqZSldCiAgICAgICAgaWYgbm90IGtoOgogICAgICAgICAgICBicmVhawogICAgICAgIHZ1bmcgPSB1bmFyeV91bmlvbihbTGluZVN0cmluZyhlKS5idWZmZXIoc2F1ICsgNTApIGZvciBlIGlu"
"IGtoXSkKICAgICAgICBkaWVtID0geyhyb3VuZCh4LCAxKSwgcm91bmQoeSwgMSkpIGZvciB4LCB5IGluIG5ldC5kaWVtX2RhdSgoInRyYXQiLCAidHVvbmciKSwgdnVuZyl9CiAgICAgICAgbWlueCwgbWlueSwgbWF4eCwgbWF4eSA9IHBvbHkuYm91bmRzCiAgICAg"
"ICAgZHVvbmcgPSBzZXQoKQogICAgICAgIGZvciB4LCB5IGluIGRpZW06CiAgICAgICAgICAgIGlmIG1pbnggKyAwLjUgPCB4IDwgbWF4eCAtIDAuNToKICAgICAgICAgICAgICAgIGR1b25nLmFkZCgoIngiLCB4KSkKICAgICAgICAgICAgaWYgbWlueSArIDAuNSA8"
"IHkgPCBtYXh5IC0gMC41OgogICAgICAgICAgICAgICAgZHVvbmcuYWRkKCgieSIsIHkpKQogICAgICAgIHRvdCA9IE5vbmUKICAgICAgICBmb3IgaywgdiBpbiBzb3J0ZWQoZHVvbmcpOgogICAgICAgICAgICBMID0gTGluZVN0cmluZyhbKHYsIG1pbnkgLSAxMCks"
"ICh2LCBtYXh5ICsgMTApXSkgaWYgayA9PSAieCIgZWxzZSBMaW5lU3RyaW5nKFsobWlueCAtIDEwLCB2KSwgKG1heHggKyAxMCwgdildKQogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBwY3MgPSBsaXN0KHNwbGl0KHBvbHksIEwpLmdlb21zKQogICAg"
"ICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgaWYgbGVuKHBjcykgPCAyOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgbG9uID0gbWF4KHBjcywga2V5PWxhbWJkYSBxOiBxLmFy"
"ZWEpCiAgICAgICAgICAgIGZvciBxIGluIHBjczoKICAgICAgICAgICAgICAgIGlmIHEgaXMgbG9uIG9yIHEuYXJlYSA+IGR0X21heCBvciBxLmFyZWEgPCAxMDAgb3IgKHRvdCBpcyBub3QgTm9uZSBhbmQgcS5hcmVhID49IHRvdC5hcmVhKToKICAgICAgICAgICAg"
"ICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgY3MgPSBsaXN0KHEuZXh0ZXJpb3IuY29vcmRzKQogICAgICAgICAgICAgICAgaWYgbWF4KEwuZGlzdGFuY2Uoc2hhcGVseS5Qb2ludChjKSkgZm9yIGMgaW4gY3MpID4gc2F1OgogICAgICAgICAgICAgICAg"
"ICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICB0b25nID0ga2h0ID0ga2luaCA9IDAuMAogICAgICAgICAgICAgICAgZm9yIGEsIGIgaW4gemlwKGNzLCBjc1sxOl0pOgogICAgICAgICAgICAgICAgICAgIGxuID0gbWF0aC5kaXN0KGEsIGIpCiAgICAgICAgICAg"
"ICAgICAgICAgc2cgPSBMaW5lU3RyaW5nKFthLCBiXSkKICAgICAgICAgICAgICAgICAgICBpZiBsbiA8IDAuNSBvciBzZy53aXRoaW4oTC5idWZmZXIoMC41KSkgb3IgYW55KHNnLndpdGhpbihjXy5idWZmZXIoMC41KSkgZm9yIGNfIGluIGRhX2NhdCk6CiAgICAg"
"ICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICAgICAgdG9uZyArPSBsbgogICAgICAgICAgICAgICAgICAgIGlmIF90cnVjKGEsIGIpOgogICAgICAgICAgICAgICAgICAgICAgICBraHQgKz0gbG4gLSBuZXQuaG9fdHJvKGEsIGIsICgi"
"dHJhdCIsICJ0dW9uZyIsICJiYXUiKSkKICAgICAgICAgICAgICAgICAgICAgICAga2luaCArPSBtaW4obG4sIG5ldC5ob190cm8oYSwgYiwgKCJraW5oIiwpLCB0b2w9OCkpCiAgICAgICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICAgICAg"
"a2h0ICs9IGxuCiAgICAgICAgICAgICAgICBpZiB0b25nID4gMCBhbmQga2h0ID49IHRpX2xlICogdG9uZyBhbmQga2luaCA+PSB0aV9sZV9raW5oICogdG9uZzoKICAgICAgICAgICAgICAgICAgICB0b3QsIHRvdF9MID0gcSwgTAogICAgICAgIGlmIHRvdCBpcyBO"
"b25lOgogICAgICAgICAgICBicmVhawogICAgICAgIGcgPSBwb2x5LmRpZmZlcmVuY2UodG90LmJ1ZmZlcigwLjAxLCBqb2luX3N0eWxlPTIpKQogICAgICAgIGcgPSBtYXgoZy5nZW9tcywga2V5PWxhbWJkYSBxOiBxLmFyZWEpIGlmIGlzaW5zdGFuY2UoZywgTXVs"
"dGlQb2x5Z29uKSBlbHNlIGcKICAgICAgICBwb2x5ID0gZy5idWZmZXIoMCkKICAgICAgICBkYV9jYXQuYXBwZW5kKHRvdF9MKQogICAgICAgIGJvICs9IDEKICAgIHJldHVybiBwb2x5LCBibwoKCmRlZiBkb2lfY2FuaChwb2x5LCBkaWNoKToKICAgICIiIkRvaSB0"
"dW5nIGNhbmggdmFvIHRyb25nIG1vdCBkb2FuIGRpY2hbaV0gKGFtID0gcmEgbmdvYWkpOyBkaW5oIG1vaSA9IGdpYW8gY3VhIGhhaSBjYW5oIGtlIGRhIGRvaS4KICAgIENhbmggeGllbiAvIGNvbmcgZ2l1IG5ndXllbiAoZGljaCAwKS4gVHJhIHZlIHBvbHkgbW9p"
"IGhvYWMgTm9uZSBuZXUgaGluaCBtb2kga2hvbmcgaG9wIGxlLiIiIgogICAgcHRzID0gX3ZvbmcocG9seSkKICAgIG4gPSBsZW4ocHRzKQogICAgTF8gPSBbXQogICAgZm9yIGkgaW4gcmFuZ2Uobik6CiAgICAgICAgYSwgYiA9IHB0c1tpXSwgcHRzWyhpICsgMSkg"
"JSBuXQogICAgICAgIEwgPSBtYXRoLmRpc3QoYSwgYikKICAgICAgICBpZiBMIDwgMWUtOToKICAgICAgICAgICAgcmV0dXJuIE5vbmUKICAgICAgICBueCwgbnkgPSAtKGJbMV0gLSBhWzFdKSAvIEwsIChiWzBdIC0gYVswXSkgLyBMICAgICAgIyBwaGFwIHR1eWVu"
"IHRyb25nIChDQ1cpCiAgICAgICAgZCA9IGRpY2hbaV0KICAgICAgICBMXy5hcHBlbmQoKChhWzBdICsgbnggKiBkLCBhWzFdICsgbnkgKiBkKSwgKChiWzBdIC0gYVswXSkgLyBMLCAoYlsxXSAtIGFbMV0pIC8gTCkpKQogICAgbW9pID0gW10KICAgIGZvciBpIGlu"
"IHJhbmdlKG4pOgogICAgICAgIChwMCwgdTApLCAocDEsIHUxKSA9IExfW2kgLSAxXSwgTF9baV0KICAgICAgICBjciA9IHUwWzBdICogdTFbMV0gLSB1MFsxXSAqIHUxWzBdCiAgICAgICAgaWYgYWJzKGNyKSA8IDFlLTk6ICAgICAgICAgICAgICAgICAgICAgICAg"
"ICAgICAgICAgIyBoYWkgY2FuaCB0aGFuZyBoYW5nOiBsYXkgZGllbSBkYXUgY2FuaCBpIGRhIGRvaQogICAgICAgICAgICBtb2kuYXBwZW5kKHAxKQogICAgICAgICAgICBjb250aW51ZQogICAgICAgIHQgPSAoKHAxWzBdIC0gcDBbMF0pICogdTFbMV0gLSAocDFb"
"MV0gLSBwMFsxXSkgKiB1MVswXSkgLyBjcgogICAgICAgIG1vaS5hcHBlbmQoKHAwWzBdICsgdTBbMF0gKiB0LCBwMFsxXSArIHUwWzFdICogdCkpCiAgICBnID0gX3BvbHkobW9pLCBbbGlzdChoLmNvb3JkcykgZm9yIGggaW4gcG9seS5pbnRlcmlvcnNdKQogICAg"
"aWYgZyBpcyBOb25lIG9yIGFicyhnLmFyZWEgLSBwb2x5LmFyZWEpID4gMC4wNSAqIHBvbHkuYXJlYToKICAgICAgICByZXR1cm4gTm9uZQogICAgcmV0dXJuIGcKCgpkZWYgX3BoYXBfdHV5ZW4oYSwgYik6CiAgICBMID0gbWF0aC5kaXN0KGEsIGIpCiAgICByZXR1"
"cm4gKC0oYlsxXSAtIGFbMV0pIC8gTCwgKGJbMF0gLSBhWzBdKSAvIEwpCgoKZGVmIG9wX3djKHBvbHksIG5ldCwgb3A9MTAuMCk6CiAgICAiIiJMb2kgNDogV0MgdHJ1IGxvcCBvcC4gQ2FuaCBuYW0gdHJlbiBtYXQgdHJhdC90dW9uZyBtYSBjaHVhIGNvIG5ldCBv"
"cCAobmV0IHRyYXQgc29uZyBzb25nIGNhY2ggNi0xNCBtbSBwaGlhIG5nb2FpKS4iIiIKICAgIHB0cyA9IF92b25nKHBvbHkpCiAgICBkID0gW10KICAgIGZvciBpIGluIHJhbmdlKGxlbihwdHMpKToKICAgICAgICBhLCBiID0gcHRzW2ldLCBwdHNbKGkgKyAxKSAl"
"IGxlbihwdHMpXQogICAgICAgIEwgPSBtYXRoLmRpc3QoYSwgYikKICAgICAgICBpZiBMIDwgMSBvciBub3QgX3RydWMoYSwgYikgb3IgbmV0LmhvX3RybyhhLCBiLCAoInRyYXQiLCAidHVvbmciKSkgPCAwLjUgKiBMOgogICAgICAgICAgICBkLmFwcGVuZCgwLjAp"
"CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgbmluID0gX3BoYXBfdHV5ZW4oYSwgYikKICAgICAgICByYSA9ICgtbmluWzBdLCAtbmluWzFdKQogICAgICAgIGQuYXBwZW5kKDAuMCBpZiBuZXQuc29uZ19zb25nKGEsIGIsIHJhLCAoInRyYXQiLCksIG9wIC0g"
"NCwgb3AgKyA0KSBlbHNlIG9wKQogICAgaWYgbm90IGFueShkKToKICAgICAgICByZXR1cm4gcG9seSwgMAogICAgZyA9IGRvaV9jYW5oKHBvbHksIGQpCiAgICByZXR1cm4gKGcsIHN1bSgxIGZvciB4IGluIGQgaWYgeCkpIGlmIGcgaXMgbm90IE5vbmUgZWxzZSAo"
"cG9seSwgMCkKCgpkZWYgZGF1X3R1b25nKHBvbHksIG5ldCwgdHJhdD0xNS4wLCBkYWlfbWF4PTM1MC4wKToKICAgICIiIkxvaSA1OiBNQVQgREFVIFRVT05HIChjYW5oIG5nYW4gPD0gZGFpX21heCkgbmFtIHRyZW4gbmV0IGxvaSB0dW9uZywga2hvbmcgY28gbmV0"
"IHRyYXQgLT4gbHVpIHRyYXQgbW0uCiAgICBNYXQgdHVvbmcgZGFpIGtob25nIHZlIHRyYXQgdGhpIGdpdSBuZ3V5ZW4gKHF1eSB0YWMgMDUvMTAvMjAyNjoga2hvbmcgdmUgdHJhdCB0aGkga2hvbmcgbHVpKS4iIiIKICAgIHB0cyA9IF92b25nKHBvbHkpCiAgICBk"
"ID0gW10KICAgIGZvciBpIGluIHJhbmdlKGxlbihwdHMpKToKICAgICAgICBhLCBiID0gcHRzW2ldLCBwdHNbKGkgKyAxKSAlIGxlbihwdHMpXQogICAgICAgIEwgPSBtYXRoLmRpc3QoYSwgYikKICAgICAgICBkLmFwcGVuZCh0cmF0IGlmICgxIDw9IEwgPD0gZGFp"
"X21heCBhbmQgX3RydWMoYSwgYikgYW5kIG5ldC5ob190cm8oYSwgYiwgKCJ0dW9uZyIsKSkgPj0gMC41ICogTAogICAgICAgICAgICAgICAgICAgICAgICAgIGFuZCBuZXQuaG9fdHJvKGEsIGIsICgidHJhdCIsKSkgPCAwLjUgKiBMKSBlbHNlIDAuMCkKICAgIGlm"
"IG5vdCBhbnkoZCk6CiAgICAgICAgcmV0dXJuIHBvbHksIDAKICAgIGcgPSBkb2lfY2FuaChwb2x5LCBkKQogICAgcmV0dXJuIChnLCBzdW0oMSBmb3IgeCBpbiBkIGlmIHgpKSBpZiBnIGlzIG5vdCBOb25lIGVsc2UgKHBvbHksIDApCgoKZGVmIGJhdV9sb19naWEo"
"cG9seSwgbmV0LCBkbWF4PTgwLjApOgogICAgIiIiTG9pIDc6IGNhbmggbG8gZ2lhIGtlbyByYSBtYXQgdHJvbmcgYmF1IEJUIC8gbGFuIGNhbiBnYW4gbmhhdCBwaGlhIG5nb2FpICg8PSBkbWF4KS4iIiIKICAgIHB0cyA9IF92b25nKHBvbHkpCiAgICBkID0gW10K"
"ICAgIGZvciBpIGluIHJhbmdlKGxlbihwdHMpKToKICAgICAgICBhLCBiID0gcHRzW2ldLCBwdHNbKGkgKyAxKSAlIGxlbihwdHMpXQogICAgICAgIEwgPSBtYXRoLmRpc3QoYSwgYikKICAgICAgICBpZiBMIDwgMTAwIG9yIG5vdCBfdHJ1YyhhLCBiKSBvciBuZXQu"
"aG9fdHJvKGEsIGIsICgiYmF1IiwpKSA+PSAwLjUgKiBMOgogICAgICAgICAgICBkLmFwcGVuZCgwLjApCiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgbmluID0gX3BoYXBfdHV5ZW4oYSwgYikKICAgICAgICBkcyA9IG5ldC5zb25nX3NvbmcoYSwgYiwgKC1u"
"aW5bMF0sIC1uaW5bMV0pLCAoImJhdSIsKSwgMC41LCBkbWF4KQogICAgICAgIGQuYXBwZW5kKC1kc1swXSBpZiBkcyBlbHNlIDAuMCkKICAgIGlmIG5vdCBhbnkoZCk6CiAgICAgICAgcmV0dXJuIHBvbHksIDAKICAgIGcgPSBkb2lfY2FuaChwb2x5LCBkKQogICAg"
"cmV0dXJuIChnLCBzdW0oMSBmb3IgeCBpbiBkIGlmIHgpKSBpZiBnIGlzIG5vdCBOb25lIGVsc2UgKHBvbHksIDApCgoKZGVmIGRhaV90dW9uZyhwb2x5cywgZG1heCk6CiAgICAiIiJMb2kgNjogZGFpIGNodSBuaGF0IGdpdWEgaGFpIGNhbmggZG9pIGRpZW4gc29u"
"ZyBzb25nIChjYWNoIDw9IGRtYXgpIGN1YSBjYWMgdnVuZyAtPiB0dW9uZyBuZ2FuIC8gbyBjdWEuIiIiCiAgICBFID0gW10KICAgIGZvciBnIGluIHBvbHlzOgogICAgICAgIHB0cyA9IF92b25nKGcpCiAgICAgICAgZm9yIGkgaW4gcmFuZ2UobGVuKHB0cykpOgog"
"ICAgICAgICAgICBhLCBiID0gcHRzW2ldLCBwdHNbKGkgKyAxKSAlIGxlbihwdHMpXQogICAgICAgICAgICBpZiBtYXRoLmRpc3QoYSwgYikgPCAxIG9yIG5vdCBfdHJ1YyhhLCBiLCAwLjUpOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgbiA9"
"IF9waGFwX3R1eWVuKGEsIGIpCiAgICAgICAgICAgIEUuYXBwZW5kKChhLCBiLCAoLW5bMF0sIC1uWzFdKSkpICAgICAgICAgICAgICAgICAgIyBwaGFwIHR1eWVuIG5nb2FpCiAgICBVID0gdW5hcnlfdW5pb24ocG9seXMpCiAgICByZWN0cyA9IFtdCiAgICBmb3Ig"
"aSwgKGEsIGIsIG4pIGluIGVudW1lcmF0ZShFKToKICAgICAgICBmb3IgYywgZCwgbSBpbiBFW2kgKyAxOl06CiAgICAgICAgICAgIGlmIGFicyhuWzBdICsgbVswXSkgPiAxZS02IG9yIGFicyhuWzFdICsgbVsxXSkgPiAxZS02OgogICAgICAgICAgICAgICAgY29u"
"dGludWUKICAgICAgICAgICAgazEgPSAxIGlmIGFicyhuWzFdKSA+IDAuNSBlbHNlIDAgICAgICAgICAgICAgICAgICAjIHRydWMgdnVvbmcgZ29jIGNhbmgKICAgICAgICAgICAgazAgPSAxIC0gazEKICAgICAgICAgICAgZ2FwID0gKGNbazFdIC0gYVtrMV0pICog"
"bltrMV0KICAgICAgICAgICAgaWYgbm90ICgwLjUgPCBnYXAgPD0gZG1heCk6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICBsbyA9IG1heChtaW4oYVtrMF0sIGJbazBdKSwgbWluKGNbazBdLCBkW2swXSkpCiAgICAgICAgICAgIGhpID0gbWlu"
"KG1heChhW2swXSwgYltrMF0pLCBtYXgoY1trMF0sIGRbazBdKSkKICAgICAgICAgICAgaWYgaGkgLSBsbyA8IDE6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAgICByID0gYm94KGxvLCBtaW4oYVsxXSwgY1sxXSksIGhpLCBtYXgoYVsxXSwgY1sx"
"XSkpIGlmIGsxID09IDEgZWxzZSBib3gobWluKGFbMF0sIGNbMF0pLCBsbywgbWF4KGFbMF0sIGNbMF0pLCBoaSkKICAgICAgICAgICAgaWYgci5pbnRlcnNlY3Rpb24oVSkuYXJlYSA+IDAuMDIgKiByLmFyZWE6CiAgICAgICAgICAgICAgICByID0gci5kaWZmZXJl"
"bmNlKFUpICAgICAgICAgICAgICAgICAgICAgICAgICAgIyBwaGFuIGRhaSBiaSB2dW5nIGtoYWMgY2hlbiB2YW86IGJvIHBoYW4gZG8KICAgICAgICAgICAgICAgIGlmIHIuaXNfZW1wdHk6CiAgICAgICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAg"
"cmVjdHMuYXBwZW5kKHIpCiAgICByZXR1cm4gcmVjdHMKCgpkZWYgbGFwX2xvX25obyhnLCBkdF9tYXg9MC4xNWU2KToKICAgIGlmIGlzaW5zdGFuY2UoZywgTXVsdGlQb2x5Z29uKToKICAgICAgICByZXR1cm4gTXVsdGlQb2x5Z29uKFtsYXBfbG9fbmhvKHEsIGR0"
"X21heCkgZm9yIHEgaW4gZy5nZW9tc10pCiAgICByZXR1cm4gUG9seWdvbihnLmV4dGVyaW9yLCBbaCBmb3IgaCBpbiBnLmludGVyaW9ycyBpZiBQb2x5Z29uKGgpLmFyZWEgPiBkdF9tYXhdKQoKCmRlZiBjaGluaF9waG9uZyhnLCBuZXQsIHdjPUZhbHNlLCBsb19n"
"aWE9RmFsc2UsIG9wPTEwLjAsIHRyYXQ9MTUuMCk6CiAgICAiIiJUcmluaCB0dSBjaGluaCBoaW5oIG1vdCBwb2x5Z29uIHBob25nIChnaW9uZyBtYXRfYmFuZ190YW5nLnh1YXQpOiB2dW9uZ19nb2MgLT4gZG9uX2RpbmggLT4gY2F0X2tpbmggLT4gb3Bfd2MgKFdD"
"KQogICAgLT4gZGF1X3R1b25nIC0+IGJhdV9sb19naWEgKGxvIGdpYSAvIGJhbiBjb25nKSAtPiBkb25fZGluaC4gVHJhIHZlIChwb2x5LCBDb3VudGVyIHNvIGNhbmgvZGluaCBkYSBzdWEgdGhlbyBsb2FpKS4iIiIKICAgIGRlbSA9IGNvbGxlY3Rpb25zLkNvdW50"
"ZXIoKQogICAgaWYgbmV0IGlzIE5vbmUgb3IgZyBpcyBOb25lIG9yIGcuaXNfZW1wdHk6CiAgICAgICAgcmV0dXJuIGcsIGRlbQogICAgZywgZGVtWyJjaGVvIl0gPSB2dW9uZ19nb2MoZywgbmV0KQogICAgZywgZGVtWyJnYWkiXSA9IGRvbl9kaW5oKGcsIG5ldCkK"
"ICAgIGcsIGRlbVsia2luaCJdID0gY2F0X2tpbmgoZywgbmV0KQogICAgaWYgd2M6CiAgICAgICAgZywgZGVtWyJvcCJdID0gb3Bfd2MoZywgbmV0LCBvcCkKICAgIGcsIGRlbVsiZGF1X3R1b25nIl0gPSBkYXVfdHVvbmcoZywgbmV0LCB0cmF0KQogICAgaWYgbG9f"
"Z2lhOgogICAgICAgIGcsIGRlbVsiYmF1Il0gPSBiYXVfbG9fZ2lhKGcsIG5ldCkKICAgIGcsIG5fID0gZG9uX2RpbmgoZywgbmV0KQogICAgZGVtWyJnYWkiXSArPSBuXwogICAgcmV0dXJuIGcsIGRlbQoKCmRlZiBtb190YV9jaGluaChkZW0pOgogICAgIiIiQ2h1"
"b2kgdGllbmcgVmlldCB0b20gdGF0IGNhYyBzdWEgZG9pIGNoaW5oIGhpbmggKGJvIGxvYWkgPSAwKS4iIiIKICAgIHRlbiA9IFsoImNoZW8iLCAibuG6r24ge30gY+G6oW5oIHhpw6puIiksICgiZ2FpIiwgImLhu48ge30gxJHhu4luaCB0aOG7q2EvZ2FpL2to4bql"
"Yy92w6F0IGNow6lvIiksICgia2luaCIsICJj4bqvdCB7fSBwaOG6p24gbOG7k2kgcmEga8Otbmggbmdvw6BpIG3hurd0IHTGsOG7nW5nIiksCiAgICAgICAgICAgKCJvcCIsICJsw7lpIOG7kXAgV0Mge30gY+G6oW5oIiksICgiZGF1X3R1b25nIiwgImzDuWkgdHLD"
"oXQgxJHhuqd1IHTGsOG7nW5nIHt9IGPhuqFuaCIpLCAoImJhdSIsICJrw6lvIGzDtCBnaWEgcmEgYuG6rXUge30gY+G6oW5oIildCiAgICByZXR1cm4gIjsgIi5qb2luKHQuZm9ybWF0KGRlbVtrXSkgZm9yIGssIHQgaW4gdGVuIGlmIGRlbS5nZXQoaykpCgoKZGVm"
"IGR1b25nX2JvKHJlZ3MsIGRtYXgsIGxvX21heD0wLjE1ZTYpOgogICAgIiIiTG9pIDY6IGhvcCBjYWMgdnVuZyBwaG9uZyAoZGEgY2hpbmggaGluaCkgKyBkYWkgdHVvbmcgZ2l1YSBoYWkgbWF0IHBob25nIGRvaSBkaWVuICg8PSBkbWF4OiB0dW9uZyBuZ2FuLCBv"
"IGN1YSk7CiAgICBraG9uZyBsYXAgZ29jIGxvbSAtPiBraG9uZyBhbiB2YW8gdHVvbmcgYmFvIG5nb2FpLiBMbyA8IGxvX21heCAoa2hlIGdpYW8gdHVvbmcpIGR1b2MgbGFwLCB0cnUgbG8gdm9uIGxhIGxvIGN1YSBwaG9uZwogICAgKGNvdCAvIGhvcCBreSB0aHVh"
"dCBuYW0gcmllbmcgdHJvbmcgcGhvbmcpLiBUcmEgdmUgUG9seWdvbiAvIE11bHRpUG9seWdvbi4iIiIKICAgIHUgPSB1bmFyeV91bmlvbihsaXN0KHJlZ3MpICsgZGFpX3R1b25nKHJlZ3MsIGRtYXgpKQogICAgdSA9IHUuYnVmZmVyKDAuNSwgam9pbl9zdHlsZT0y"
"KS5idWZmZXIoLTAuNSwgam9pbl9zdHlsZT0yKQogICAgbG9fcGhvbmcgPSB1bmFyeV91bmlvbihbUG9seWdvbihoXykgZm9yIHJfIGluIHJlZ3MgZm9yIGhfIGluIHJfLmludGVyaW9yc10pIGlmIGFueShyXy5pbnRlcmlvcnMgZm9yIHJfIGluIHJlZ3MpIGVsc2Ug"
"UG9seWdvbigpCgogICAgZGVmIGxhcChxKToKICAgICAgICBnaXUgPSBbaF8gZm9yIGhfIGluIHEuaW50ZXJpb3JzCiAgICAgICAgICAgICAgIGlmIFBvbHlnb24oaF8pLmFyZWEgPiBsb19tYXggb3IgUG9seWdvbihoXykuaW50ZXJzZWN0aW9uKGxvX3Bob25nKS5h"
"cmVhID4gMC41ICogUG9seWdvbihoXykuYXJlYV0KICAgICAgICByZXR1cm4gUG9seWdvbihxLmV4dGVyaW9yLCBnaXUpCiAgICByZXR1cm4gdW5hcnlfdW5pb24oW2xhcChxKSBmb3IgcSBpbiBnZXRhdHRyKHUsICJnZW9tcyIsIFt1XSldKQo="
)
))
(princ)
