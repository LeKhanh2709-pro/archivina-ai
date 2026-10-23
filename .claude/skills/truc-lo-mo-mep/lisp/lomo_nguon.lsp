;;; Lomo.lsp - MỘT FILE DUY NHẤT, chỉ cần APPLOAD file này rồi gõ LOMO.
;;; Lệnh LOMO: tự tìm trục kỹ thuật / hộp kỹ thuật trên mặt bằng tầng và chèn block lỗ mở
;;; A-MEP (dynamic block) co giãn khít khung từng trục / hộp (bản LISP của skill truc-lo-mo-mep).
;;;
;;; FILE NÀY ĐƯỢC GỘP TỰ ĐỘNG, KHÔNG SỬA TAY: phần dò trục lấy từ fire_stop_shaft.lsp (skill
;;; ngan-chay-truc-hkt, bỏ lệnh NCL), phần lỗ mở lấy từ lomo_nguon.lsp (skill truc-lo-mo-mep).
;;; Sửa ở 2 file nguồn rồi chạy scripts\gop_lomo.ps1 của skill truc-lo-mo-mep để gộp lại.
;;;
;;; Nhận diện trục / hộp: hàm nc:do (cùng quy tắc với lệnh NCL của skill ngan-chay-truc-hkt): ô có
;;; dấu X của trục / hộp, lỗ mở "lo mo" có ống đứng, khung lỗ mở MEP có ống; bỏ thang máy, nội thất,
;;; lỗ mở sàn không có ống.
;;;
;;; Block A-MEP (mẫu: FILE MẪU LỖ MỞ.dwg, 22/10/2026): khung chữ nhật + X nét đứt + 2 dim + Field
;;; diện tích m2. Điểm chèn = góc dưới trái. Tham số:
;;;   Distance1 = cạnh theo trục Y của block (100 - 4000, bước 10)
;;;   Distance2 = cạnh theo trục X của block (100 - 3000, bước 10)
;;; Quy tắc bo: bo theo hình lỗ mở. Block chỉ co giãn được thành chữ nhật, nên vùng không chữ nhật
;;; (hộp chữ L, chữ T...) được tách thành nhiều khung chữ nhật, mỗi khung 1 A-MEP:
;;;   - vùng gộp từ nhiều ô X / lỗ mở: mỗi ô một A-MEP (đúng từng lỗ mở trên bản vẽ);
;;;   - khung MEP chữ L, ô chồng nhau: tách lưới đa giác, lấy cách ra ít khung nhất.
;;; Mỗi khung: cạnh dài -> Distance1, cạnh ngắn -> Distance2. Khung dọc (cao >= rộng) chèn góc 0,
;;; khung ngang chèn góc 90 (như block mẫu). Kích thước làm tròn bội 10 mm, sai lệch chia đều 2 đầu.
;;; LAYER LỖ MỞ LUÔN LÀ "A-MEP" (người dùng chốt 22/10/2026, tuân thủ tuyệt đối): mọi block A-MEP và block
;;; gom "LO MO MEP" đều đặt trên layer A-MEP. Bản vẽ chưa có layer này thì tạo mới theo thông số layer
;;; A_MEP của file mẫu (màu 32, Continuous, nét 0.05). Layer A-MEP đang khoá thì mở khoá tạm, xong khoá lại.
;;;
;;; Cách dùng:
;;;   1. SAO LƯU file bản vẽ trước (lệnh thêm block vào bản vẽ đang mở).
;;;   2. APPLOAD -> chọn Lomo.lsp (ở bất kỳ thư mục nào, máy nào). Chỉ một file, không cần file nào khác.
;;;   3. Gõ LOMO: quét toàn bộ Model, chèn A-MEP cho mọi trục / hộp chưa có, rồi in các ô cần xem lại.
;;;   4. KHÔNG BẮT BUỘC có block A-MEP (sửa 23/10/2026 để chạy được ở máy khác):
;;;      - Bản vẽ đã có A-MEP dynamic: dùng block có sẵn, không định nghĩa lại.
;;;      - Chưa có: chép định nghĩa từ file thư viện A-MEP_thu_vien.dwg nếu tìm thấy (biến môi trường
;;;        ARCHIVINA_AMEP, Support File Search Path, <ARCHIVINA_AI | %USERPROFILE% | <ổ cứng>:\AI>\.claude\skills\
;;;        truc-lo-mo-mep\assets\ - không gắn cứng ổ đĩa, sửa 23/10/2026).
;;;      - Không có file thư viện / A-MEP không phải dynamic: tự dựng block tĩnh "A-MEP <rộng>x<dài>" cho
;;;        từng kích thước, hình thể như A-MEP (khung, X nét đứt, 2 dim, số diện tích m2), không kéo giãn được.
;;;   5. Các A-MEP vừa chèn được gom vào 1 block "LO MO MEP" (trùng tên thì "LO MO MEP 2"...) chèn tại
;;;      0,0 trên layer A-MEP, giữ nguyên vị trí (người dùng chốt 22/10/2026: dễ kiểm soát). A-MEP bên trong
;;;      vẫn là dynamic block: sửa bằng REFEDIT / BEDIT block gom.
;;;   6. Kiểm tra trên bản vẽ. Sai thì Ctrl+Z một lần để hoàn tác toàn bộ.
;;;   Chạy lại lệnh: ô đã có A-MEP (chồng > 50%, kể cả A-MEP nằm trong block "LO MO MEP*") không chèn trùng.
;;;   Không chèn, chỉ liệt kê (Cần xác nhận lại): vùng có cạnh xiên (không tách được thành chữ nhật),
;;;   khung vượt giới hạn tham số block (cạnh ngắn > 3000 hoặc cạnh dài > 4000).
;;;
;;; Yêu cầu: AutoCAD đầy đủ 2025 / 2026 (chạy được cả 2021+), LISPSYS = 1, file lưu UTF-8.
;;;   KHÔNG chạy được trong AutoCAD Core Console (không có COM để gán tham số dynamic block).
;;;   Không phụ thuộc thiết lập máy (sửa 23/10/2026): tự đặt tạm rồi trả lại UCS World; UNDO Control None / One
;;;   thì bỏ nhóm undo; bản vẽ chưa có kiểu chữ "Arial" thì tạo (font arial.ttf) cho số diện tích block tĩnh.
;;; Hộp xoay xiên (cánh nhà xoay, sửa 23/10/2026): bo được ô dấu X xoay, khung MEP chữ nhật xoay và khung
;;;   chữ L / T xoay (tách thành chữ nhật xoay); A-MEP chèn theo góc của ô.
;;; Giới hạn: khung hình thang / tứ giác không đều (cạnh xiên lẫn cạnh thẳng) không bo được bằng block chữ
;;;   nhật: chỉ liệt kê (Cần xác nhận lại).

(vl-load-com)

;;; ---------- Cấu hình (sửa ở đây nếu dự án khác) ----------
(defun amep:cfg (k)
  (cdr
    (assoc
      k
      '((ten-block . "A-MEP")
        ;; layer lỗ mở: LUÔN là A-MEP (người dùng chốt 22/10/2026). Không đổi sang tên khác.
        (layer . "A-MEP")
        ;; thông số khi phải tạo mới layer A-MEP: theo layer A_MEP của file mẫu
        (layer-mau . 32) (layer-net . 5)
        ;; tên block gom các A-MEP vừa chèn (trùng thì thêm số: "LO MO MEP 2"...)
        (ten-gom . "LO MO MEP")
        ;; file thư viện chứa block A-MEP dynamic (tên file, tìm trên máy bằng amep:file-thu-vien). Không thấy
        ;; file (máy khác) thì lệnh tự dựng block tĩnh, không bắt buộc phải có file này.
        (thu-vien . "A-MEP_thu_vien.dwg")
        (thu-vien-con . "\\.claude\\skills\\truc-lo-mo-mep\\assets\\")
        ;; block tĩnh dựng sẵn khi không có A-MEP dynamic: tên "A-MEP <cạnh ngắn>x<cạnh dài>", hình thể
        ;; như A-MEP gốc (số đo lấy từ block A-MEP trong FILE MẪU LỖ MỞ.dwg, 22/10/2026)
        ;; kiểu dim của block gốc: _1-10_HKT (DIMSCALE 10, DIMTXT 2.0 -> chữ cao 20 mm). Bản vẽ chưa có thì tạo
        ;; kiểu cùng tên từ kiểu dim-goc (không có thì kiểu hiện hành), chỉ đổi DIMSCALE / DIMTXT theo block gốc
        (dim-ten . "_1-10_HKT") (dim-goc . "A 1-100") (dim-scale . 10.0) (dim-txt . 2.0)
        ;; dim cạnh dài: đường kích thước cách mép trái; dim cạnh ngắn: cách mép dưới
        (dim-x . 101.5) (dim-y . 202.6)
        ;; số diện tích m2
        (text-style . "Arial") (text-cao . 30.0) (text-x . 20.8) (text-y . 30.9)
        ;; nét đứt dấu X
        (net-x . "ACAD_ISO03W100") (lin-file . "acadiso.lin")
        ;; giới hạn và bước tham số, lấy theo block mẫu
        (buoc . 10.0)
        (d1-min . 100.0) (d1-max . 4000.0)
        (d2-min . 100.0) (d2-max . 3000.0)
        ;; diện tích vùng / diện tích khung bao dưới mức này: không phải chữ nhật -> tách khung
        (ti-le-chu-nhat . 0.95)
        ;; ô chồng lên A-MEP có sẵn quá tỉ lệ này: đã có
        (trung . 0.5)
       )
    )
  )
)

;;; ---------- Định nghĩa block ----------
;;; Chép một đối tượng tên ten trong tập coll (của file thư viện) sang tập dich (bản vẽ hiện hành)
(defun amep:chep (dbx coll ten dich / o sa)
  (setq o (vl-catch-all-apply 'vla-Item (list coll ten)))
  (if (not (vl-catch-all-error-p o))
    (progn
      (setq sa (vlax-make-safearray vlax-vbObject '(0 . 0)))
      (vlax-safearray-fill sa (list o))
      (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-CopyObjects (list dbx (vlax-make-variant sa) dich))))
    )
  )
)

;;; Bảo đảm có layer A-MEP: chưa có thì tạo (màu 32, Continuous, nét 0.05 theo mẫu)
(defun amep:tao-layer (lay)
  (if (not (tblsearch "LAYER" lay))
    (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord")
                   (cons 2 lay) '(70 . 0) (cons 62 (amep:cfg 'layer-mau)) '(6 . "Continuous")
                   (cons 370 (amep:cfg 'layer-net))))
  )
  (tblsearch "LAYER" lay)
)

;;; Block ten trong bản vẽ có phải dynamic block không
(defun amep:la-dong (ten / b)
  (and (tblsearch "BLOCK" ten)
       (setq b (vl-catch-all-apply 'vla-Item (list (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))) ten)))
       (not (vl-catch-all-error-p b))
       (= (vla-get-IsDynamicBlock b) :vlax-true))
)

;;; Ổ cứng cố định đang sẵn sàng ("C:" "D:"...), bỏ ổ mạng / ổ rời để không treo khi ổ mạng mất kết nối
(defun amep:o-dia (/ fso kq)
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

;;; File thư viện block A-MEP, tìm trên máy đang chạy (không gắn cứng ổ đĩa). nil nếu không thấy.
;;;   biến amep-thu-vien (nếu đặt; "KHONG" = coi như không có thư viện, dùng để thử chế độ block tĩnh)
;;;   -> biến môi trường ARCHIVINA_AMEP (đường dẫn file) -> Support File Search Path
;;;   -> <ARCHIVINA_AI | %USERPROFILE% | <ổ cứng>:\AI>\.claude\skills\truc-lo-mo-mep\assets\
;;;   (and / or của AutoLISP trả về T chứ không trả về chuỗi: lấy đường dẫn bằng setq trong cond)
(defun amep:file-thu-vien (/ ten con f)
  (setq ten (amep:cfg 'thu-vien) con (amep:cfg 'thu-vien-con))
  (cond
    ((= amep-thu-vien "KHONG") nil)
    ((and amep-thu-vien (setq f (findfile amep-thu-vien))) f)
    ((and (getenv "ARCHIVINA_AMEP") (setq f (findfile (getenv "ARCHIVINA_AMEP")))) f)
    ((findfile ten))
    ((vl-some '(lambda (g) (findfile (strcat (vl-string-right-trim "\\/" g) con ten)))
              (append (if (getenv "ARCHIVINA_AI") (list (getenv "ARCHIVINA_AI")))
                      (if (getenv "USERPROFILE") (list (getenv "USERPROFILE")))
                      (mapcar '(lambda (o) (strcat o "\\AI")) (amep:o-dia)))))
  )
)

;;; Kiểu chữ "Arial" (font arial.ttf, có sẵn trên mọi máy Windows) cho số diện tích của block tĩnh.
;;; Bản vẽ chưa có thì tạo; trả về tên kiểu hoặc nil.
(defun amep:kieu-chu (/ ten)
  (setq ten (amep:cfg 'text-style))
  (if (not (tblsearch "STYLE" ten))
    (entmake (list '(0 . "STYLE") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbTextStyleTableRecord")
                   (cons 2 ten) '(70 . 0) '(40 . 0.0) '(41 . 1.0) '(50 . 0.0) '(71 . 0) '(42 . 2.5)
                   '(3 . "arial.ttf") '(4 . "")))
  )
  (if (tblsearch "STYLE" ten) ten)
)

;;; Bảo đảm có layer A-MEP và chọn cách chèn, ghi vào biến toàn cục amep-che-do:
;;;   "dong": có block A-MEP dynamic (sẵn trong bản vẽ, hoặc chép từ file thư viện bằng ObjectDBX, chỉ đọc);
;;;   "tinh": không có (máy khác không có file thư viện, hoặc A-MEP trong bản vẽ không phải dynamic)
;;;           -> tự dựng block tĩnh "A-MEP <rộng>x<dài>" cho từng kích thước (amep:block-tinh).
;;; Luôn trả về chế độ (không bao giờ dừng vì thiếu block).
(defun amep:nap-block (/ acad doc dbx f ten lay)
  (setq ten (amep:cfg 'ten-block) lay (amep:cfg 'layer)
        acad (vlax-get-acad-object) doc (vla-get-ActiveDocument acad))
  (amep:tao-layer lay)
  (if (and (not (tblsearch "BLOCK" ten)) (setq f (amep:file-thu-vien)))
    (progn
      (setq dbx (vl-catch-all-apply 'vla-GetInterfaceObject
                                    (list acad (strcat "ObjectDBX.AxDbDocument." (substr (getvar "ACADVER") 1 2)))))
      (cond
        ((vl-catch-all-error-p dbx) (princ "\nKhông mở được ObjectDBX để chép block A-MEP."))
        ((vl-catch-all-error-p (vl-catch-all-apply 'vla-Open (list dbx f)))
         (princ (strcat "\nKhông mở được file thư viện: " f)))
        (t
         (amep:chep dbx (vla-get-Blocks dbx) ten (vla-get-Blocks doc))
         (if (tblsearch "BLOCK" ten) (princ (strcat "\nĐã chép block " ten " từ " f)))
        )
      )
      (if (and dbx (not (vl-catch-all-error-p dbx))) (vlax-release-object dbx))
    )
  )
  (setq amep-che-do (if (amep:la-dong ten) "dong" "tinh"))
  (if (= amep-che-do "tinh")
    (princ (strcat "\nKhông có block " ten " dynamic (không thấy file thư viện hoặc block trong bản vẽ không phải dynamic):"
                   "\n  tự dựng block tĩnh \"" ten " <rộng>x<dài>\" cho từng kích thước, hình thể như " ten
                   " (khung, X, 2 dim, số diện tích m2), không kéo giãn được."))
  )
  amep-che-do
)

;;; Số có đúng 2 chữ số lẻ (như Field %pr2 của block gốc), không phụ thuộc DIMZIN
(defun amep:so2 (v / n)
  (setq n (fix (+ (* v 100.0) 0.5)))
  (strcat (itoa (/ n 100)) "." (if (< (rem n 100) 10) "0" "") (itoa (rem n 100)))
)

;;; Nạp kiểu nét đứt của dấu X (acadiso.lin có sẵn ở mọi máy AutoCAD); trả về tên hoặc nil
(defun amep:nap-net (/ lt)
  (setq lt (amep:cfg 'net-x))
  (if (not (tblsearch "LTYPE" lt))
    (vl-catch-all-apply 'vla-Load (list (vla-get-Linetypes (vla-get-ActiveDocument (vlax-get-acad-object)))
                                        lt (amep:cfg 'lin-file)))
  )
  (if (tblsearch "LTYPE" lt) lt)
)

;;; Kiểu dim cho block tĩnh: _1-10_HKT như block gốc. Chưa có thì tạo từ kiểu dim-goc (hoặc kiểu hiện hành),
;;; đổi DIMSCALE / DIMTXT theo block gốc, rồi trả lại kiểu dim hiện hành cũ. Trả về tên kiểu hoặc nil.
(defun amep:dim-style (/ ten cu)
  (setq ten (amep:cfg 'dim-ten))
  (if (not (tblsearch "DIMSTYLE" ten))
    (progn
      (setq cu (getvar "DIMSTYLE"))
      (if (tblsearch "DIMSTYLE" (amep:cfg 'dim-goc)) (command "_.-DIMSTYLE" "_R" (amep:cfg 'dim-goc)))
      (setvar "DIMSCALE" (amep:cfg 'dim-scale))
      (setvar "DIMTXT" (amep:cfg 'dim-txt))
      (command "_.-DIMSTYLE" "_S" ten)
      (if (tblsearch "DIMSTYLE" cu) (command "_.-DIMSTYLE" "_R" cu))
      (if (tblsearch "DIMSTYLE" ten) (princ (strcat "\nĐã tạo kiểu dim " ten " (DIMSCALE 10, DIMTXT 2.0 như block A-MEP gốc).")))
    )
  )
  (if (tblsearch "DIMSTYLE" ten) ten)
)

;;; Block tĩnh cho một kích thước d1 (cạnh dài, theo Y block) x d2 (cạnh ngắn, theo X block), điểm chèn góc dưới
;;; trái như A-MEP gốc. Mọi đối tượng trong block trên layer 0 nên hiện theo layer A-MEP của INSERT.
;;; Đã có block cùng tên thì dùng lại. Trả về tên block.
(defun amep:block-tinh (d1 d2 / ten b sa pl l lt ds dcu dm tx)
  (setq ten (strcat (amep:cfg 'ten-block) " " (itoa (fix (+ d2 0.5))) "x" (itoa (fix (+ d1 0.5)))))
  (if (not (tblsearch "BLOCK" ten))
    (progn
      (setq b (vla-Add (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))) (vlax-3d-point 0 0 0) ten))
      ;; khung chữ nhật
      (setq sa (vlax-make-safearray vlax-vbDouble '(0 . 7)))
      (vlax-safearray-fill sa (list 0.0 0.0 d2 0.0 d2 d1 0.0 d1))
      (setq pl (vla-AddLightWeightPolyline b (vlax-make-variant sa)))
      (vla-put-Closed pl :vlax-true)
      (vla-put-Layer pl "0")
      ;; dấu X nét đứt
      (setq lt (amep:nap-net))
      (foreach c (list (list (list 0.0 0.0 0.0) (list d2 d1 0.0)) (list (list 0.0 d1 0.0) (list d2 0.0 0.0)))
        (setq l (vla-AddLine b (vlax-3d-point (car c)) (vlax-3d-point (cadr c))))
        (vla-put-Layer l "0")
        (if lt (vla-put-Linetype l lt))
      )
      ;; 2 dim: cạnh dài (đứng) và cạnh ngắn (ngang)
      ;; hình dim được dựng theo kiểu dim HIỆN HÀNH lúc tạo (đổi StyleName sau đó không vẽ lại hình dim trong
      ;; block): đặt kiểu _1-10_HKT làm hiện hành khi tạo, xong trả lại kiểu cũ
      (setq ds (amep:dim-style) dcu (getvar "DIMSTYLE"))
      (if (and ds (/= (strcase dcu) (strcase ds))) (command "_.-DIMSTYLE" "_R" ds))
      (foreach dm (list (vla-AddDimRotated b (vlax-3d-point 0 0 0) (vlax-3d-point 0 d1 0)
                                           (vlax-3d-point (amep:cfg 'dim-x) (/ d1 2.0) 0) (/ pi 2.0))
                        (vla-AddDimRotated b (vlax-3d-point 0 0 0) (vlax-3d-point d2 0 0)
                                           (vlax-3d-point (/ d2 2.0) (amep:cfg 'dim-y) 0) 0.0))
        (vla-put-Layer dm "0")
        (if ds (vl-catch-all-apply 'vla-put-StyleName (list dm ds)))
      )
      (if (and ds (/= (strcase dcu) (strcase ds)) (tblsearch "DIMSTYLE" dcu)) (command "_.-DIMSTYLE" "_R" dcu))
      ;; số diện tích m2 (giá trị tĩnh, block không kéo giãn nên không cần Field)
      (setq tx (vla-AddText b (amep:so2 (/ (* d1 d2) 1e6))
                            (vlax-3d-point (amep:cfg 'text-x) (amep:cfg 'text-y) 0) (amep:cfg 'text-cao)))
      (vla-put-Layer tx "0")
      (if (amep:kieu-chu) (vla-put-StyleName tx (amep:cfg 'text-style)))
    )
  )
  ten
)

;;; ---------- A-MEP có sẵn ----------
;;; Khung bao (x0 y0 x1 y1) của một đối tượng A-MEP (bản dynamic đã kéo giãn: tên *U..; bản tĩnh: "A-MEP 600x1500"),
;;; nil nếu không phải
(defun amep:khung-o (o / a b ten)
  (setq ten (strcase (amep:cfg 'ten-block)))
  (if (and (= (vla-get-ObjectName o) "AcDbBlockReference")
           (vlax-property-available-p o 'EffectiveName)
           (wcmatch (strcase (vla-get-EffectiveName o)) (strcat ten "," ten " *"))
           (not (vl-catch-all-error-p (vl-catch-all-apply 'vla-GetBoundingBox (list o 'a 'b)))))
    (progn
      (setq a (vlax-safearray->list a) b (vlax-safearray->list b))
      (list (car a) (cadr a) (car b) (cadr b))
    )
  )
)

;;; Đổi khung k trong hệ toạ độ block sang hệ thế giới theo INSERT d (điểm chèn, tỉ lệ, góc)
(defun amep:doi-khung (k d / p sx sy r g)
  (setq p (cdr (assoc 10 d)) sx (cdr (assoc 41 d)) sy (cdr (assoc 42 d)) r (cdr (assoc 50 d)))
  (setq g (mapcar '(lambda (q / x y)
                     (setq x (* sx (car q)) y (* sy (cadr q)))
                     (list (+ (car p) (- (* x (cos r)) (* y (sin r)))) (+ (cadr p) (* x (sin r)) (* y (cos r)))))
                  (list (list (nth 0 k) (nth 1 k)) (list (nth 2 k) (nth 1 k))
                        (list (nth 2 k) (nth 3 k)) (list (nth 0 k) (nth 3 k)))))
  (nc:khung g)
)

;;; Khung bao mọi A-MEP trong Model: chèn thẳng, hoặc nằm trong block gom "LO MO MEP*" của lần chạy trước
(defun amep:co-san (/ ss i e d o k blks trong kq)
  (setq kq nil blks (vla-get-Blocks (vla-get-ActiveDocument (vlax-get-acad-object))))
  (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model")
                                (cons 2 (strcat (amep:cfg 'ten-block) "," (amep:cfg 'ten-block) " *,`*U*,"
                                                (amep:cfg 'ten-gom) "*")))))
    (repeat (setq i (sslength ss))
      (setq e (ssname ss (setq i (1- i))) d (entget e) o (vlax-ename->vla-object e))
      (cond
        ((setq k (amep:khung-o o)) (setq kq (cons k kq)))
        ((wcmatch (strcase (cdr (assoc 2 d))) (strcat (strcase (amep:cfg 'ten-gom)) "*"))
         (setq trong nil)
         (vlax-for c (vla-Item blks (cdr (assoc 2 d)))
           (if (setq k (amep:khung-o c)) (setq trong (cons k trong)))
         )
         (setq kq (append (mapcar '(lambda (k) (amep:doi-khung k d)) trong) kq))
        )
      )
    )
  )
  kq
)

;;; Gom các A-MEP vừa chèn vào 1 block "LO MO MEP" (trùng tên thì "LO MO MEP 2"...), chèn lại tại 0,0
;;; trên layer A-MEP, giữ nguyên vị trí. Không định nghĩa lại block có sẵn. Trả về tên block hoặc nil.
(defun amep:gom-block (ds / ss ten goc i n lay)
  (setq ss (ssadd) goc (amep:cfg 'ten-gom) ten goc i 1 lay (amep:cfg 'layer))
  (foreach e ds (if (entget e) (ssadd e ss)))
  (while (tblsearch "BLOCK" ten) (setq i (1+ i) ten (strcat goc " " (itoa i))))
  (if (> (setq n (sslength ss)) 0)
    (progn
      (command "_.-BLOCK" ten "0,0,0" ss "")
      (if (tblsearch "BLOCK" ten)
        (progn
          ;; tuỳ bản AutoCAD, -BLOCK xoá đối tượng gốc hoặc tự đổi chúng thành block reference:
          ;; chỉ chèn khi chưa có INSERT của block này, tránh 2 block chồng nhau
          (if (not (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmake (list '(0 . "INSERT") '(100 . "AcDbEntity") (cons 8 lay) '(100 . "AcDbBlockReference")
                           (cons 2 ten) '(10 0.0 0.0 0.0) '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) '(50 . 0.0)))
          )
          (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmod (subst (cons 8 lay) (assoc 8 (entget (ssname ss 0))) (entget (ssname ss 0))))
          )
          (princ (strcat "\nĐã gom " (itoa n) " block " (amep:cfg 'ten-block) " vào block \"" ten "\" (layer " lay ")."))
          ten
        )
      )
    )
  )
)

;;; ---------- Tính chèn ----------
(defun amep:tron (v / b) (setq b (amep:cfg 'buoc)) (* b (fix (+ (/ v b) 0.5))))

;;; Tách đa giác trực giao thành các hình chữ nhật: lưới theo toạ độ đỉnh, gộp ô liền nhau theo hàng
;;; rồi gộp các dải trùng nhau ở hàng kế tiếp. dao = T: làm theo cột (đổi vai X, Y).
(defun amep:tach-luoi-1 (pts dao / p xs ys nx ny i j i0 chay mo moi kq x0 y0 x1 y1 tim)
  (if dao (setq pts (mapcar '(lambda (p) (list (cadr p) (car p))) pts)))
  (setq xs (nc:duy-nhat (mapcar 'car pts)) ys (nc:duy-nhat (mapcar 'cadr pts))
        nx (1- (length xs)) ny (1- (length ys)) mo nil kq nil j 0)
  (while (< j ny)
    ;; các dải ô liền nhau trong hàng j: (i0 i1)
    (setq chay nil i 0 i0 nil)
    (while (<= i nx)
      (if (and (< i nx)
               (nc:trong-dg (list (/ (+ (nth i xs) (nth (1+ i) xs)) 2.0) (/ (+ (nth j ys) (nth (1+ j) ys)) 2.0)) pts))
        (if (null i0) (setq i0 i))
        (if i0 (setq chay (cons (list i0 (1- i)) chay) i0 nil))
      )
      (setq i (1+ i))
    )
    ;; mo: hình đang mở (i0 i1 j0); dải trùng thì kéo dài, không thì đóng
    (setq moi nil)
    (foreach c chay
      (if (setq tim (vl-some '(lambda (m) (if (and (= (car m) (car c)) (= (cadr m) (cadr c))) m)) mo))
        (setq moi (cons tim moi) mo (vl-remove tim mo))
        (setq moi (cons (list (car c) (cadr c) j) moi))
      )
    )
    (foreach m mo (setq kq (cons (list (car m) (cadr m) (caddr m) (1- j)) kq)))
    (setq mo moi j (1+ j))
  )
  (foreach m mo (setq kq (cons (list (car m) (cadr m) (caddr m) (1- ny)) kq)))
  (mapcar '(lambda (r)
             (setq x0 (nth (nth 0 r) xs) x1 (nth (1+ (nth 1 r)) xs) y0 (nth (nth 2 r) ys) y1 (nth (1+ (nth 3 r)) ys))
             (if dao (list y0 x0 y1 x1) (list x0 y0 x1 y1)))
          kq)
)

;;; Tách theo hàng và theo cột, lấy cách ra ít hình hơn
(defun amep:tach-luoi (pts / a b)
  (setq a (amep:tach-luoi-1 pts nil) b (amep:tach-luoi-1 pts T))
  (if (<= (length a) (length b)) a b)
)

;;; Đa giác chỉ có cạnh song song X, Y
(defun amep:truc-giao (pts / n i a b)
  (setq n (length pts) i 0)
  (while (and (< i n)
              (setq a (nth i pts) b (nth (rem (1+ i) n) pts))
              (or (< (abs (- (car a) (car b))) 0.5) (< (abs (- (cadr a) (cadr b))) 0.5)))
    (setq i (1+ i))
  )
  (= i n)
)

;;; Các khung chữ nhật để bo một vùng, theo hình lỗ mở:
;;;   - vùng gộp từ nhiều ô X / lỗ mở không chồng nhau: mỗi ô một khung (bo theo từng lỗ mở);
;;;   - vùng chữ nhật: 1 khung;
;;;   - vùng không chữ nhật còn lại (ô chồng nhau, khung MEP chữ L): tách lưới đa giác;
;;;   - đa giác có cạnh xiên: nil (xem lại).
(defun amep:khung-bo (v / k o dt tong)
  (setq k (nth 2 v) o (nth 5 v) dt (abs (nc:dt-dg (cadr v))))
  (cond
    ((and (> (length o) 1)
          (setq tong (apply '+ (mapcar 'nc:dt-kh o)))
          (< (abs (- tong dt)) (* 0.03 dt)))
     o)
    ((>= (/ dt (nc:dt-kh k)) (amep:cfg 'ti-le-chu-nhat)) (list k))
    ((amep:truc-giao (cadr v)) (amep:tach-luoi (cadr v)))
  )
)

;;; Từ một vùng của nc:do (số thứ tự iv) -> danh sách bản ghi, mỗi khung bo một bản ghi:
;;; (trang-thai cx cy rong dai d1 d2 goc ins lech ti-le so-ong kieu vung so-khung)
;;; trang-thai: "se_chen" | "da_co" | "xem_lai" (không tách được) | "vuot" (vượt giới hạn block)
(defun amep:tinh (v co iv / ks tl c)
  (setq tl (/ (abs (nc:dt-dg (cadr v))) (nc:dt-kh (nth 2 v))))
  (cond
    ;; khung là chữ nhật xoay xiên (vd. hộp KT trong WC ở cánh nhà xoay 45°): bo theo góc xoay của khung
    ((and (< tl (amep:cfg 'ti-le-chu-nhat)) (setq c (amep:chu-nhat-xoay (cadr v))))
     (list (amep:tinh-xoay c co tl (nth 3 v) (strcat (car v) " (xoay)") iv 1)))
    ;; khung xoay xiên hình chữ L / T...: tách thành các chữ nhật xoay
    ((and (< tl (amep:cfg 'ti-le-chu-nhat)) (setq ks (amep:tach-xoay (cadr v))))
     (mapcar '(lambda (c) (amep:tinh-xoay c co tl (nth 3 v) (strcat (car v) " (xoay)") iv (length ks))) ks))
    ((setq ks (amep:khung-bo v))
     (mapcar '(lambda (k) (amep:tinh-kh k co tl (nth 3 v) (car v) iv (length ks))) ks))
    (t
     (setq ks (amep:tinh-kh (nth 2 v) co tl (nth 3 v) (car v) iv 1))
     (list (if (= (car ks) "da_co") ks (cons "xem_lai" (cdr ks)))))
  )
)

;;; Một khung chữ nhật k -> bản ghi
(defun amep:tinh-kh (k co tl so-ong kieu iv sk / w h d1 d2 goc ins tt)
  (setq w (- (nth 2 k) (nth 0 k))
        h (- (nth 3 k) (nth 1 k))
        d1 (amep:tron (max w h))
        d2 (amep:tron (min w h)))
  (if (>= h w)
    ;; ô dọc: góc 0, Distance1 theo Y
    (setq goc 0.0
          ins (list (+ (nth 0 k) (/ (- w d2) 2.0)) (+ (nth 1 k) (/ (- h d1) 2.0)) 0.0))
    ;; ô ngang: góc 90, trục Y của block hướng -X thế giới, điểm chèn ở góc dưới phải
    (setq goc 90.0
          ins (list (- (nth 2 k) (/ (- w d1) 2.0)) (+ (nth 1 k) (/ (- h d2) 2.0)) 0.0))
  )
  (setq tt
         (cond
           ((vl-some '(lambda (q) (> (nc:giao k q) (* (amep:cfg 'trung) (min (nc:dt-kh k) (nc:dt-kh q))))) co) "da_co")
           ((or (< d1 (amep:cfg 'd1-min)) (> d1 (amep:cfg 'd1-max))
                (< d2 (amep:cfg 'd2-min)) (> d2 (amep:cfg 'd2-max))) "vuot")
           ("se_chen")
         ))
  (list tt (/ (+ (nth 0 k) (nth 2 k)) 2.0) (/ (+ (nth 1 k) (nth 3 k)) 2.0) w h d1 d2 goc ins
        (max (abs (- (max w h) d1)) (abs (- (min w h) d2))) tl so-ong kieu iv sk)
)

;;; ---------- Khung xoay xiên (cạnh không song song X, Y) ----------
;;; Góc lệch nhỏ nhất của góc a (radian) so với phương X / Y, tính bằng độ
(defun amep:lech-truc (a / g)
  (setq g (rem (abs (* (/ 180.0 pi) a)) 90.0))
  (min g (- 90.0 g))
)

;;; Đa giác pts là chữ nhật xoay xiên: trả về 4 đỉnh theo thứ tự, không thì nil
(defun amep:chu-nhat-xoay (pts / c i a b ok)
  (setq c (nc:bo-thang-hang pts))
  (if (and (= (length c) 4) (> (amep:lech-truc (angle (nth 0 c) (nth 1 c))) 2.0))
    (progn
      (setq i 0 ok T)
      (while (and ok (< i 4))
        (setq a (mapcar '- (nth (rem (1+ i) 4) c) (nth i c))
              b (mapcar '- (nth (rem (+ i 2) 4) c) (nth (rem (1+ i) 4) c)))
        ;; 2 cạnh kề vuông góc (cos < 0.02)
        (if (> (abs (/ (+ (* (car a) (car b)) (* (cadr a) (cadr b)))
                       (* (distance '(0 0) a) (distance '(0 0) b)))) 0.02)
          (setq ok nil))
        (setq i (1+ i))
      )
      (if ok (mapcar '(lambda (p) (list (car p) (cadr p))) c))
    )
  )
)

;;; Xoay điểm p quanh gốc toạ độ một góc g (radian)
(defun amep:xoay-diem (p g)
  (list (- (* (car p) (cos g)) (* (cadr p) (sin g))) (+ (* (car p) (sin g)) (* (cadr p) (cos g))))
)

;;; Đa giác xoay xiên mà mọi cạnh song song / vuông góc với cạnh đầu (chữ L, T... nằm xiên): xoay về phương
;;; thẳng, tách lưới như hộp thẳng (amep:tach-luoi), rồi xoay các khung về góc cũ.
;;; Trả về danh sách chữ nhật (mỗi cái 4 đỉnh theo thứ tự), nil nếu không tách được.
(defun amep:tach-xoay (pts / c g p2)
  (setq c (nc:bo-thang-hang pts))
  (if (and (>= (length c) 4) (> (amep:lech-truc (setq g (angle (nth 0 c) (nth 1 c)))) 2.0))
    (progn
      (setq p2 (mapcar '(lambda (p) (amep:xoay-diem p (- g))) c))
      (if (amep:truc-giao p2)
        (mapcar '(lambda (k)
                   (mapcar '(lambda (p) (amep:xoay-diem p g))
                           (list (list (nth 0 k) (nth 1 k)) (list (nth 2 k) (nth 1 k))
                                 (list (nth 2 k) (nth 3 k)) (list (nth 0 k) (nth 3 k)))))
                (amep:tach-luoi p2))
      )
    )
  )
)

;;; Một chữ nhật xoay (4 đỉnh c theo thứ tự) -> bản ghi như amep:tinh-kh (rong = cạnh ngắn, dai = cạnh dài).
;;; Quy tắc góc như ô thẳng: hướng cạnh dài đưa về [90°, 270°), góc chèn = hướng đó - 90° (ô dọc 0, ô ngang 90).
;;; Trục X block theo cạnh ngắn, trục Y theo cạnh dài, điểm chèn là đỉnh nhỏ nhất theo cả 2 trục block.
(defun amep:tinh-xoay (c co tl so-ong kieu iv sk / lu lv a lg sh rot ux uy vx vy d1 d2 p0 ins k tt)
  (setq lu (distance (nth 0 c) (nth 1 c)) lv (distance (nth 1 c) (nth 2 c)))
  (if (>= lu lv)
    (setq a (angle (nth 0 c) (nth 1 c)) lg lu sh lv)
    (setq a (angle (nth 1 c) (nth 2 c)) lg lv sh lu))
  (if (or (< a (* 0.5 pi)) (>= a (* 1.5 pi))) (setq a (rem (+ a pi) (* 2.0 pi))))
  (setq rot (- a (* 0.5 pi))
        ux (cos rot) uy (sin rot) vx (- uy) vy ux
        d1 (amep:tron lg) d2 (amep:tron sh))
  (setq p0 (car (vl-sort c '(lambda (p q) (< (+ (* (car p) (+ ux vx)) (* (cadr p) (+ uy vy)))
                                             (+ (* (car q) (+ ux vx)) (* (cadr q) (+ uy vy))))))))
  ;; làm tròn bước 10: chia đều phần lệch 2 đầu
  (setq ins (list (+ (car p0) (* ux (/ (- sh d2) 2.0)) (* vx (/ (- lg d1) 2.0)))
                  (+ (cadr p0) (* uy (/ (- sh d2) 2.0)) (* vy (/ (- lg d1) 2.0))) 0.0)
        k (nc:khung c))
  (setq tt
         (cond
           ((vl-some '(lambda (q) (> (nc:giao k q) (* (amep:cfg 'trung) (min (nc:dt-kh k) (nc:dt-kh q))))) co) "da_co")
           ((or (< d1 (amep:cfg 'd1-min)) (> d1 (amep:cfg 'd1-max))
                (< d2 (amep:cfg 'd2-min)) (> d2 (amep:cfg 'd2-max))) "vuot")
           ("se_chen")))
  (list tt (/ (apply '+ (mapcar 'car c)) 4.0) (/ (apply '+ (mapcar 'cadr c)) 4.0) sh lg d1 d2
        (* (/ 180.0 pi) rot) ins (max (abs (- lg d1)) (abs (- sh d2))) tl so-ong kieu iv sk)
)

;;; Ô dấu X xoay xiên mà nc:do (chỉ nhận ô song song X, Y) bỏ sót: 2 nét chéo dài bằng nhau (lệch <= 15 mm),
;;; chung trung điểm (<= 15 mm), không song song, cạnh chữ nhật suy ra lệch trục > 2° và dài 150 - 4000 mm.
;;; Lọc như nc:do: bỏ thang máy / nội thất / layer bỏ qua / nét trong ký hiệu ống / nét A-Material vừa vẽ;
;;; bỏ thêm layer *DIM*. X của block lỗ mở "lo mo" chỉ nhận khi bên trong có ống đứng.
;;; Bỏ ô nằm trong vùng nc:do đã có (vd. khung MEP xoay đã bo). Trả về danh sách (4-đỉnh số-ống).
(defun amep:do-x-xoay (vung / ss i tat ds ong x lay fl fin tt p q l a b r e1 e2 c kq)
  (setq ss (ssget "X" '((410 . "Model"))) i 0 tat nil)
  (if ss (repeat (sslength ss) (setq tat (append (nc:doc-ent (entget (ssname ss i))) tat) i (1+ i))))
  (setq ds nil ong nil)
  (foreach x tat
    (cond
      ((and (= (car x) "C") (nth 5 x) (/= 0 (logand (nth 5 x) 4)) (<= 25.0 (nth 2 x) 160.0))
       (setq ong (cons (nth 1 x) ong)))
      ((= (car x) "S")
       (setq lay (nth 3 x) fl (nth 4 x) fin (nth 5 x) tt (nc:tt-layer lay))
       (if (and (= 0 (logand fl 3)) (not (cadr tt)) (not (and fin (/= 0 (logand fin 4))))
                (not (and (= fl 0) (null fin) (= (car tt) "A-MATERIAL")))
                (not (wcmatch (car tt) "*DIM*")))
         (progn
           (setq p (nth 1 x) q (nth 2 x) l (distance p q))
           (if (<= 212.0 l 5660.0)
             (setq ds (cons (list (/ (+ (car p) (car q)) 2.0) (/ (+ (cadr p) (cadr q)) 2.0) l p q
                                  (/= 0 (logand fl 8)) (angle p q))
                            ds)))))))
  )
  (setq tat nil ds (vl-sort ds '(lambda (a b) (< (car a) (car b)))) kq nil)
  (while ds
    (setq a (car ds) ds (cdr ds) r ds)
    (while (and r (< (- (car (car r)) (car a)) 15.0))
      (setq b (car r) r (cdr r))
      (if (and (< (abs (- (cadr a) (cadr b))) 15.0) (< (abs (- (nth 2 a) (nth 2 b))) 15.0)
               (> (amep:lech-truc (- (nth 6 a) (nth 6 b))) 5.0))
        (progn
          ;; đỉnh chữ nhật: đầu nét a, đầu nét b, cuối nét a, cuối nét b
          (setq c (list (nth 3 a) (nth 3 b) (nth 4 a) (nth 4 b))
                e1 (distance (nth 0 c) (nth 1 c)) e2 (distance (nth 1 c) (nth 2 c)))
          (if (and (> (amep:lech-truc (angle (nth 0 c) (nth 1 c))) 2.0)
                   (<= 150.0 e1 4000.0) (<= 150.0 e2 4000.0)
                   (not (vl-some '(lambda (k) (< (distance (list (car a) (cadr a)) (car k)) 20.0)) kq))
                   (not (vl-some '(lambda (v) (nc:trong-dg (list (car a) (cadr a)) (cadr v))) vung)))
            (setq kq (cons (list (list (car a) (cadr a)) c
                                 (length (vl-remove-if-not '(lambda (o) (nc:trong-dg o c)) ong))
                                 (or (nth 5 a) (nth 5 b)))
                           kq))
          )
        )
      )
    )
  )
  ;; X của block lỗ mở "lo mo" không có ống bên trong: không phải trục (như nc:do)
  (mapcar '(lambda (k) (list (mapcar '(lambda (p) (list (car p) (cadr p))) (nth 1 k)) (nth 2 k)))
          (vl-remove-if '(lambda (k) (and (nth 3 k) (= 0 (nth 2 k)))) kq))
)

;;; Gán giá trị tham số dynamic; trả về giá trị đọc lại
(defun amep:tham-so (o ten gt / kq)
  (foreach p (vlax-invoke o 'GetDynamicBlockProperties)
    (if (= (strcase (vla-get-PropertyName p)) (strcase ten))
      (progn
        (vl-catch-all-apply 'vlax-put (list p 'Value gt))
        (setq kq (vlax-get p 'Value))
      )
    )
  )
  kq
)

;;; Chèn 1 A-MEP theo kết quả amep:tinh; trả về ename hoặc nil.
;;; Chế độ "dong": chèn A-MEP dynamic rồi gán Distance1 / Distance2; "tinh": chèn block tĩnh đúng kích thước.
(defun amep:chen (ms r / o g1 g2 ten)
  (setq ten (if (= amep-che-do "tinh") (amep:block-tinh (nth 5 r) (nth 6 r)) (amep:cfg 'ten-block)))
  (setq o (vl-catch-all-apply 'vla-InsertBlock
                              (list ms (vlax-3d-point (nth 8 r)) ten 1.0 1.0 1.0
                                    (* pi (/ (nth 7 r) 180.0)))))
  (if (not (vl-catch-all-error-p o))
    (progn
      (vla-put-Layer o (amep:cfg 'layer))
      (if (/= amep-che-do "tinh")
        (progn
          (setq g1 (amep:tham-so o "Distance1" (nth 5 r))
                g2 (amep:tham-so o "Distance2" (nth 6 r)))
          (if (not (and g1 g2 (equal g1 (nth 5 r) 0.5) (equal g2 (nth 6 r) 0.5)))
            (princ (strcat "\n  Cảnh báo: block tại " (rtos (nth 1 r) 2 0) ", " (rtos (nth 2 r) 2 0)
                           " không nhận đúng tham số (Distance1/Distance2) - Cần xác nhận lại"))
          )
        )
      )
      (vlax-vla-object->ename o)
    )
  )
)

;;; ---------- Báo cáo ----------
(defun amep:nhan (tt)
  (cdr (assoc tt '(("se_chen" . "Sẽ chèn") ("da_co" . "Đã có A-MEP") ("xem_lai" . "Không tách được thành chữ nhật - Cần xác nhận lại")
                   ("vuot" . "Vượt giới hạn block - Cần xác nhận lại") ("da_chen" . "Đã chèn"))))
)

;;; In các khung cần xem lại (không tách được, vượt giới hạn block)
(defun amep:in-ds (ds / i)
  (setq i 0)
  (foreach r ds
    (setq i (1+ i))
    (if (member (car r) '("xem_lai" "vuot"))
      (princ (strcat "\n " (itoa i) " | " (itoa (nth 13 r))
                     (if (> (nth 14 r) 1) (strcat " (tách " (itoa (nth 14 r)) " khung)") "")
                     " | " (amep:nhan (car r)) " | " (rtos (nth 1 r) 2 0) " | " (rtos (nth 2 r) 2 0)
                     " | " (rtos (nth 3 r) 2 0) " x " (rtos (nth 4 r) 2 0)
                     " | " (rtos (nth 5 r) 2 0) " x " (rtos (nth 6 r) 2 0) " | " (rtos (nth 7 r) 2 0) " | " (nth 12 r)))
    )
  )
)

;;; CSV chỉ ghi ký tự ASCII (mã kiểu), Python đổi sang tiếng Việt khi xuất Excel
(defun amep:ma-kieu (s)
  (cond ((wcmatch s "* (xoay)") (strcat (amep:ma-kieu (substr s 1 (- (strlen s) 7))) "_XOAY"))
        ((= s "Dấu X trục / hộp") "X") ((= s "Lỗ mở có ống đứng") "LOMO_ONG")
        ((= s "Khung lỗ mở MEP có ống (không có X)") "KHUNG_ONG") ("KHAC"))
)

(defun amep:ghi-csv (ds f / fh i)
  (setq fh (open f "w") i 0)
  (write-line "stt,trang_thai,cx,cy,rong,dai,d1,d2,goc,ins_x,ins_y,lech,ti_le,so_ong,kieu,vung,so_khung" fh)
  (foreach r ds
    (setq i (1+ i))
    (write-line (strcat (itoa i) "," (car r) "," (rtos (nth 1 r) 2 1) "," (rtos (nth 2 r) 2 1) ","
                        (rtos (nth 3 r) 2 1) "," (rtos (nth 4 r) 2 1) "," (rtos (nth 5 r) 2 0) "," (rtos (nth 6 r) 2 0) ","
                        (rtos (nth 7 r) 2 0) "," (rtos (car (nth 8 r)) 2 1) "," (rtos (cadr (nth 8 r)) 2 1) ","
                        (rtos (nth 9 r) 2 1) "," (rtos (nth 10 r) 2 3) "," (itoa (nth 11 r)) "," (amep:ma-kieu (nth 12 r))
                        "," (itoa (nth 13 r)) "," (itoa (nth 14 r)))
                fh)
  )
  (close fh)
)

;;; ---------- Chạy ----------
;;; Khoá (khoa = T) / mở khoá (nil) layer lay. Khi mở khoá: trả về T nếu layer đang bị khoá.
(defun amep:khoa-layer (lay khoa / d f)
  (if (setq d (entget (tblobjname "LAYER" lay)))
    (progn
      (setq f (cdr (assoc 70 d)))
      (cond
        (khoa (entmod (subst (cons 70 (logior f 4)) (assoc 70 d) d)) T)
        ((/= 0 (logand f 4)) (entmod (subst (cons 70 (- f 4)) (assoc 70 d) d)) T)
      )
    )
  )
)

;;; Dò, chèn, gom block. csv: đường dẫn file CSV kết quả (nil = không ghi). Trả về số block đã chèn.
(defun amep:chay (csv / *error* nc-memo nc-co-cache nc-lay-cache bien cu kq co ds se ms ss n e dem tb khoa ucs undo)
  (defun *error* (msg)
    (if ucs (command-s "_.UCS" "_P"))
    (if cu (mapcar 'nc:dat bien cu))
    (if khoa (amep:khoa-layer (amep:cfg 'layer) T))
    (if (and msg (not (wcmatch (strcase msg) "*CANCEL*,*QUIT*,*EXIT*")))
      (princ (strcat "\nLỗi: " msg))
    )
    (if undo (command-s "_.UNDO" "_E"))
    (princ)
  )
  (setq bien nc:*bien*
        cu (mapcar 'getvar bien))
  (setvar "CMDECHO" 0)
  (if (= (getvar "TILEMODE") 0) (setvar "TILEMODE" 1))
  ;; biến toàn cục: tên block gom lần chạy này, cho script chen_amep_vao_ban_sao.ps1 ghi log
  (setq amep-gom-cuoi nil dem 0)
  (setq kq (nc:do) co (amep:co-san))
  (setq n 0 ds (apply 'append (mapcar '(lambda (v) (amep:tinh v co (setq n (1+ n)))) (car kq))))
  ;; ô dấu X xoay xiên (nc:do chỉ nhận ô song song X, Y): mỗi ô một vùng mới
  (foreach x (amep:do-x-xoay (car kq))
    (setq n (1+ n)
          ds (append ds (list (amep:tinh-xoay (car x) co 1.0 (cadr x) "Dấu X trục / hộp (xoay)" n 1)))))
  (setq se (vl-remove-if-not '(lambda (r) (= (car r) "se_chen")) ds))
  (princ (strcat "\n  Vùng trục / hộp: " (itoa (length (car kq))) " | khung bo: " (itoa (length ds))
                 " | sẽ chèn: " (itoa (length se))
                 " | đã có A-MEP: " (itoa (length (vl-remove-if-not '(lambda (r) (= (car r) "da_co")) ds)))
                 " | cần xem lại: " (itoa (length (vl-remove-if-not '(lambda (r) (member (car r) '("xem_lai" "vuot"))) ds)))))
  (if se
    (if (amep:nap-block)
      (progn
        (if (setq undo (nc:undo-ok)) (command "_.UNDO" "_BE"))
        ;; UCS khác World: -BLOCK "0,0,0" của block gom lấy theo UCS -> lệch vị trí; chuyển World, xong trả lại
        (setq ucs (nc:ucs-world))
        (setvar "OSMODE" 0)
        ;; layer A-MEP đang khoá: mở khoá tạm để chèn và gom block, xong khoá lại
        (setq khoa (amep:khoa-layer (amep:cfg 'layer) nil))
        (setq ms (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object))) ss (ssadd))
        (setq ds (mapcar '(lambda (r)
                            (if (and (= (car r) "se_chen") (setq e (amep:chen ms r)))
                              (progn (ssadd e ss) (setq dem (1+ dem)) (cons "da_chen" (cdr r)))
                              r))
                         ds))
        ;; cập nhật Field diện tích trong các block vừa chèn
        (if (> (sslength ss) 0) (command "_.UPDATEFIELD" ss ""))
        (princ (strcat "\nĐã chèn " (itoa dem) " block " (amep:cfg 'ten-block) " trên layer " (amep:cfg 'layer) "."))
        ;; gom vào 1 block để dễ kiểm soát (người dùng chốt 22/10/2026)
        (setq tb nil)
        (if (> (sslength ss) 0)
          (setq tb (amep:gom-block (vl-remove-if 'listp (mapcar 'cadr (ssnamex ss))))))
        (setq amep-gom-cuoi tb)
        (if khoa (amep:khoa-layer (amep:cfg 'layer) T))
        (nc:ucs-tra ucs)
        (setq ucs nil)
        (if undo (command "_.UNDO" "_E"))
        (princ "\nCtrl+Z một lần để hoàn tác.")
      )
    )
    (princ "\nKhông có trục / hộp mới cần chèn A-MEP.")
  )
  (amep:in-ds ds)
  (if csv (amep:ghi-csv ds csv))
  (mapcar 'nc:dat bien cu)
  (princ)
  dem
)

;;; LOMO: chèn luôn, không hỏi
(defun c:LOMO () (amep:chay nil) (princ))

;;; LISPSYS khác 1 (bộ LISP cũ): file UTF-8 đọc sai dấu tiếng Việt -> nhắc đổi (thông báo không dấu để đọc được)
(if (/= 1 (getvar "LISPSYS"))
  (princ "\nCANH BAO: LISPSYS khac 1 - thong bao tieng Viet se loi font. Go LISPSYS, dat 1, khoi dong lai AutoCAD.")
)

(princ "\nĐã nạp lệnh LOMO: tự chèn block A-MEP bo trục / hộp kỹ thuật, layer A-MEP.")
(princ)
