;;; xuat_du_lieu_block.lsp — chạy trong AutoCAD trên assets\VK_thu_vien.dwg (scripts\nhung_block.ps1 dán vào .scr).
;;; Đọc nguyên văn (entget) mọi đối tượng của block VK_DoDung / VK_CuaSoMo / VK_CuaDi, kiểu nét chúng dùng,
;;; layer A-Window, kiểu chữ + biến kích thước của kiểu dim "dim cua", ghi thành dữ liệu LISP (vk_du_lieu.lsp)
;;; để VK.lsp tự tạo block bằng entmake, không cần file thư viện ngoài.
;;; Số thực ghi 10 chữ số lẻ (prin1 của AutoLISP chỉ giữ 6 chữ số có nghĩa).

;;; bỏ tên đối tượng / handle / chủ sở hữu và mọi cặp trỏ tới đối tượng khác (không mang sang bản vẽ khác được)
(defun dl:bo (ed)
  (vl-remove-if '(lambda (p) (or (member (car p) '(-1 5 330 360 102 340 342 343 344))
                                 (and (listp p) (= 'ENAME (type (cdr p))))))
                ed))

(defun dl:so (x / s)
  (setq s (rtos x 2 10))
  (if (not (vl-string-search "." s)) (setq s (strcat s ".0")))
  s)

(defun dl:chuoi (s / kq)
  (foreach c (vl-string->list s)
    (setq kq (cons (cond ((= c 92) "\\\\") ((= c 34) "\\\"") (T (chr c))) kq)))
  (strcat "\"" (apply 'strcat (reverse kq)) "\""))

(defun dl:ra (x)
  (cond
    ((null x) "nil")
    ((= (type x) 'REAL) (dl:so x))
    ((= (type x) 'INT) (itoa x))
    ((= (type x) 'STR) (dl:chuoi x))
    ((= (type x) 'SYM) (vl-symbol-name x))
    ((and (listp x) (cdr x) (atom (cdr x)))
     (strcat "(" (dl:ra (car x)) " . " (dl:ra (cdr x)) ")"))
    ((listp x) (strcat "(" (vl-string-right-trim " " (apply 'strcat (mapcar '(lambda (y) (strcat (dl:ra y) " ")) x))) ")"))
    (T "nil")))

(defun dl:xuat (f / h e ed lt ds-lt bien gt dz)
  ;; kiểu dim "dim cua" làm hiện hành trước (đổi DIMZIN), lưu DIMZIN của kiểu rồi đặt 0 để rtos không bỏ số 0
  (command "_.-DIMSTYLE" "_R" "dim cua")
  (setq dz (getvar "DIMZIN"))
  (setvar "DIMZIN" 0)
  (setq h (open f "w"))
  (write-line "(setq vk:dl-block '(" h)
  (foreach ten '("VK_DoDung" "VK_CuaSoMo" "VK_CuaDi")
    (write-line (strcat "(" (dl:chuoi ten)) h)
    (setq e (cdr (assoc -2 (tblsearch "BLOCK" ten))))
    (while e
      (setq ed (dl:bo (entget e)))
      (if (and (setq lt (cdr (assoc 6 ed))) (not (member (strcase lt) '("BYLAYER" "BYBLOCK" "CONTINUOUS")))
               (not (member lt ds-lt)))
        (setq ds-lt (cons lt ds-lt)))
      (write-line (dl:ra ed) h)
      (setq e (entnext e)))
    (write-line ")" h))
  (write-line "))" h)
  (write-line "(setq vk:dl-ltype '(" h)
  (foreach lt ds-lt (write-line (dl:ra (dl:bo (entget (tblobjname "LTYPE" lt)))) h))
  (write-line "))" h)
  (write-line (strcat "(setq vk:dl-layer '" (dl:ra (dl:bo (entget (tblobjname "LAYER" "A-Window")))) ")") h)
  (write-line (strcat "(setq vk:dl-style '" (dl:ra (dl:bo (entget (tblobjname "STYLE" (getvar "DIMTXSTY"))))) ")") h)
  (write-line "(setq vk:dl-dimvar '(" h)
  (foreach bien '("DIMADEC" "DIMALT" "DIMALTD" "DIMALTF" "DIMALTRND" "DIMALTTD" "DIMALTTZ" "DIMALTU" "DIMALTZ"
                  "DIMAPOST" "DIMASZ" "DIMATFIT" "DIMAUNIT" "DIMAZIN" "DIMBLK" "DIMBLK1" "DIMBLK2" "DIMCEN"
                  "DIMCLRD" "DIMCLRE" "DIMCLRT" "DIMDEC" "DIMDLE" "DIMDLI" "DIMDSEP" "DIMEXE" "DIMEXO" "DIMFRAC"
                  "DIMFXL" "DIMFXLON" "DIMGAP" "DIMJOGANG" "DIMJUST" "DIMLDRBLK" "DIMLFAC" "DIMLIM" "DIMLUNIT"
                  "DIMLWD" "DIMLWE" "DIMPOST" "DIMRND" "DIMSAH" "DIMSCALE" "DIMSD1" "DIMSD2" "DIMSE1" "DIMSE2"
                  "DIMSOXD" "DIMTAD" "DIMTDEC" "DIMTFAC" "DIMTFILL" "DIMTFILLCLR" "DIMTIH" "DIMTIX" "DIMTM"
                  "DIMTMOVE" "DIMTOFL" "DIMTOH" "DIMTOL" "DIMTOLJ" "DIMTP" "DIMTSZ" "DIMTVP" "DIMTXSTY" "DIMTXT"
                  "DIMTZIN" "DIMUPT" "DIMZIN" "DIMARCSYM" "DIMTXTDIRECTION")
    (setq gt (vl-catch-all-apply 'getvar (list bien)))
    (if (and gt (not (vl-catch-all-error-p gt)))
      (write-line (dl:ra (cons bien (if (= bien "DIMZIN") dz gt))) h)))
  (write-line "))" h)
  (close h)
  (setvar "DIMZIN" dz)
  (princ))
