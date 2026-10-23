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
;;; Cách hoạt động: phần nhận diện phòng (khép phòng từ tường / cửa ACA, khoét giếng thang, nhận lô gia
;;; theo cửa trượt / lan can...) dùng chung bộ dò Python của skill (đã kiểm chứng trên tầng 4 Tháp B 254HQV
;;; và CT1 tầng 5A-10), chạy ngầm trên BẢN SAO của file đã lưu trên đĩa (File gốc không bị sửa). LISP đọc
;;; kết quả rồi vẽ thẳng vào bản vẽ đang mở.
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước. Bản vẽ phải được lưu (lệnh đọc file trên đĩa; thay đổi chưa lưu
;;;      thì lệnh hỏi có lưu không).
;;;   2. APPLOAD -> chọn CHONGTHAM.lsp. Gõ CHONGTHAM.
;;;   3. Nhận diện chạy ngầm, không hiện cửa sổ (3 - 6 phút với mặt bằng tầng 50 MB, AutoCAD tạm dừng
;;;      trong lúc chờ). Xong lệnh vẽ luôn và in:
;;;      số phòng theo loại, các vùng "cần xem" (không vẽ), thư mục chứa ảnh xem lại (không tạo Excel).
;;;   4. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ (cả phần đổi màu layer).
;;;   Chạy lại lần 2: phòng đã có hatch chống thấm (block CHONG THAM*) không vẽ trùng.
;;;
;;; Yêu cầu máy: Python venv D:\AI\_tools\venv (ezdxf, shapely, openpyxl, matplotlib), skill
;;;   D:\AI\.claude\skills\chong-tham-mat-bang và dien-tich-ch, AutoCAD Core Console (tự tìm trong
;;;   C:\Program Files\Autodesk\AutoCAD * và D:\autocad\AutoCAD *). Sửa đường dẫn ở ct:cfg nếu khác.
;;;   AutoCAD 2021+ (có AutoCAD Architecture để giữ tường / cửa ACA), LISPSYS = 1, file lưu UTF-8.
;;; Giới hạn: khu giặt thông thẳng phòng khách / bếp (không tường, không cửa) không tách được -> "cần xem",
;;;   không vẽ. Phòng rác / KT nước nhận theo ký hiệu chữ R / N / KTN đúng nguyên văn.

(vl-load-com)

;;; ---------- Cấu hình ----------
(defun ct:cfg (k)
  (cdr
    (assoc
      k
      '((scripts . "D:\\AI\\.claude\\skills\\chong-tham-mat-bang\\scripts\\")
        (thu-muc-tam . "D:\\AI\\_tmp\\")
        (layer-ve . "A-Material")
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

;;; ---------- Tiện ích ----------
(defun ct:khop (s pats) (and s (vl-some '(lambda (p) (wcmatch s p)) pats)))

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
               (strcat (itoa (/ tc 65536)) "," (itoa (rem (/ tc 256) 256)) "," (itoa (rem tc 256))) (car g) "")
      (command "_.-LAYER" "_C" (itoa c) (car g) "")
    )
  )
  ;; layer hiện hành không tắt được: chuyển sang layer vẽ trước
  (setvar "CLAYER" lay)
  (foreach n an (command "_.-LAYER" "_OFF" n ""))
  (princ (strcat "\nĐã tắt " (itoa (length an)) " layer nội thất / thiết bị vệ sinh, đổi các layer khác sang màu "
                 (ct:cfg 'mau-mo) ", giữ màu " (itoa (length giu)) " layer khung tên"
                 (if layerstate-save (strcat ". Layer state cũ: \"" ls "\".") ".")))
  (length an)
)

;;; ---------- Vẽ từ file dữ liệu (dùng cho lệnh và cho chạy thử bằng Core Console) ----------
(defun ct:ve-tu-file (path / *error* bien cu lay ds vung xem kq tb dem k)
  (defun *error* (msg)
    (if cu (mapcar '(lambda (b v) (if v (setvar b v))) bien cu))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*"))) (princ (strcat "\nLỗi: " msg)))
    (command-s "_.UNDO" "_E")
    (princ)
  )
  (setq bien '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO" "TILEMODE" "HPISLANDDETECTION")
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
      (command "_.UNDO" "_BE")
      (ct:tao-layer lay)
      (setvar "OSMODE" 0)
      (setvar "HPASSOC" 1)
      (if (getvar "HPLAYER") (setvar "HPLAYER" "."))
      (if (getvar "HPCOLOR") (setvar "HPCOLOR" "."))
      (setvar "HPISLANDDETECTION" 1)
      (setvar "CLAYER" lay)
      (setvar "CECOLOR" "3")
      (setq kq (ct:ve vung lay))
      (setvar "CECOLOR" "BYLAYER")
      (setq tb (ct:gom-block (cadddr kq) lay))
      (ct:lam-mo lay)
      (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
      (command "_.UNDO" "_E")
      (princ (strcat "\nĐã vẽ " (itoa (car kq)) " đường bo, " (itoa (cadr kq)) " hatch, " (itoa (caddr kq))
                     " nét vén chân tường trên layer " lay ", block " (if tb tb "(không gom được)")
                     ". Ctrl+Z một lần để hoàn tác."))
    )
    (progn
      (mapcar '(lambda (b v) (if v (setvar b v))) bien cu)
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

;;; ---------- Lệnh ----------
(defun c:CHONGTHAM (/ dwg tg out ps cmd sh ma f dong)
  (cond
    ((= (getvar "DWGTITLED") 0)
     (princ "\nBản vẽ chưa được lưu lần nào. Lưu bản vẽ rồi chạy lại CHONGTHAM."))
    (t
     (if (/= (getvar "DBMOD") 0)
       (progn
         (initget "Co Khong Thoat")
         (setq f (getkword "\nBản vẽ có thay đổi chưa lưu, lệnh chỉ đọc file đã lưu trên đĩa. Lưu ngay? [Co/Khong/Thoat] <Co>: "))
         (cond ((or (null f) (= f "Co")) (command "_.QSAVE"))
               ((= f "Thoat") (setq dwg 'thoat)))
       )
     )
     (if (/= dwg 'thoat)
       (progn
         (setq dwg (strcat (getvar "DWGPREFIX") (getvar "DWGNAME"))
               tg (vl-string-translate "." "_" (rtos (getvar "CDATE") 2 6))
               out (strcat (ct:cfg 'thu-muc-tam) "chongtham_lisp_" tg)
               ps (strcat (ct:cfg 'scripts) "chay_cho_lisp.ps1")
               cmd (strcat "powershell -NoProfile -ExecutionPolicy Bypass -File \"" ps "\" -Dwg \"" dwg "\" -OutDir \"" out "\""))
         (if (not (findfile ps))
           (princ (strcat "\nKhông thấy " ps " - kiểm tra đường dẫn trong ct:cfg."))
           (progn
             (princ "\nĐang nhận diện phòng ướt trên bản sao (chạy ngầm, 3 - 6 phút, AutoCAD tạm dừng đến khi xong)...")
             ;; hiện dòng thông báo trước khi AutoCAD chờ tiến trình ngầm
             (if (vl-cmdf "_.DELAY" 1) nil)
             (setq sh (vlax-create-object "WScript.Shell"))
             ;; 0 = chạy ẩn, không hiện cửa sổ PowerShell (người dùng chốt 23/10/2026); :vlax-true = chờ chạy xong
             (setq ma (vlax-invoke-method sh 'Run cmd 0 :vlax-true))
             (vlax-release-object sh)
             (setq f (open (strcat out "\\xong.txt") "r") dong (if f (read-line f)))
             (if f (close f))
             (if (and dong (= dong "OK") (findfile (strcat out "\\du_lieu.txt")))
               (progn
                 (ct:ve-tu-file (strcat out "\\du_lieu.txt"))
                 (princ (strcat "\nẢnh xem lại: " out)))
               (princ (strcat "\nNhận diện lỗi (mã " (itoa ma) "): " (if dong dong "không có kết quả")
                              ". Xem thư mục " out))
             )
           )
         )
       )
     )
    )
  )
  (princ)
)

(princ "\nĐã nạp lệnh CHONGTHAM: vẽ mặt bằng chống thấm (WC, lô gia, phòng rác, buồng đệm, phòng KT nước).")
(princ)
