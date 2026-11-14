# -*- coding: utf-8 -*-
"""Ghi o_cfg.json cho ctchung.dxf: 7 tờ, 49 ô. Ranh ô đọc từ nét khung của CAD (kq\\ks3.txt). Tỉ lệ từng tờ SUY RA từ cỡ
khung (cùng ra 695,5 x 560,8 mm giấy), file CAD không ghi tỉ lệ. Tên ô lấy theo tiêu đề trong CAD (ô dài thì rút gọn)."""
import json, io, os

TO = [
    {'ma': 'A', 'ti_le': 50, 'ten': u'CHI TIẾT CHUNG (CAD) 01 - CHỐNG MỐI MẠCH NGỪNG'},
    {'ma': 'B', 'ti_le': 50, 'ten': u'CHI TIẾT CHUNG (CAD) 02 - CHỐNG MỐI ĐƯỜNG ỐNG'},
    {'ma': 'C', 'ti_le': 30, 'ten': u'CHI TIẾT CHUNG (CAD) 03 - CHỐNG THẤM KIỂU 1-15'},
    {'ma': 'D', 'ti_le': 30, 'ten': u'CHI TIẾT CHUNG (CAD) 04 - CHỐNG THẤM CỔ ỐNG, CỬA'},
    {'ma': 'E', 'ti_le': 10, 'ten': u'CHI TIẾT CHUNG (CAD) 05 - CHỐNG THẤM CÁC VỊ TRÍ'},
    {'ma': 'F', 'ti_le': 30, 'ten': u'CHI TIẾT CHUNG (CAD) 06 - CHỐNG THẤM TƯỜNG, HƯỚNG DẪN'},
    {'ma': 'G', 'ti_le': 200, 'ten': u'CHI TIẾT CHUNG (CAD) 07 - KÝ HIỆU'},
]
O = []


def them(to, ten, x0, y0, x1, y1):
    O.append({'to': to, 'ten': ten, 'bounds': [x0, y0, x1, y1]})


def hang(to, y0, y1, xs, tens):
    for i, ten in enumerate(tens):
        them(to, ten, xs[i], y0, xs[i + 1], y1)


# A: block "T 1". Khung 149709..184484 x -57950..-29910; 2 hàng tách ở giữa 2 nét -43561 / -43725 (nét dưới bị xiên).
# Mép trái nới tới 144300 vì 2 tiêu đề lớn có điểm chèn nằm ngoài khung (đặt bằng thụt lề đoạn).
them('A', u'CM-01 CHỐNG MỐI MẠCH NGỪNG CHÂN TƯỜNG VÂY', 144300, -43643, 170812, -29910)
them('A', u'PHÒNG CHỐNG MỐI MẠCH NGỪNG ĐỨNG TƯỜNG VÂY', 170812, -43643, 184800, -29910)
them('A', u'CM-02 CHỐNG MỐI MẠCH NGỪNG ĐỈNH TƯỜNG VÂY', 144300, -57950, 166586, -43643)
them('A', u'CM-03 PHÒNG CHỐNG MỐI MẠCH NGỪNG ĐỨNG TƯỜNG VÂY', 166586, -57950, 175276, -43643)
them('A', u'MẶT CẮT ĐIỂN HÌNH TẦNG HẦM', 175276, -57950, 184800, -43643)
# B: block "CT2". Khung 200200..234976; 2 hàng tách giữa -45487 / -45882. Hai mép nới theo khung bao block.
them('B', u'CM-04 PHÒNG CHỐNG MỐI ĐƯỜNG ỐNG KỸ THUẬT XUYÊN VÁCH TẦNG HẦM', 199700, -45684, 237100, -29910)
them('B', u'HÀO PHÒNG MỐI PHÍA NGOÀI', 199700, -57950, 210426, -45684)
them('B', u'QUY TRÌNH LẮP ĐẶT ĐƯỜNG ỐNG BẢO TRÌ ALTIS PHÍA NGOÀI', 210426, -57950, 237100, -45684)
# C: 3 hàng x 5 ô
kieu = lambda a, b: [u'CHI TIẾT CHỐNG THẤM KIỂU %d' % i for i in range(a, b + 1)]
hang('C', -77389, -71688, [151753, 155787, 159586, 163125, 167960, 172158], kieu(1, 5))
hang('C', -82486, -77389, [151753, 155253, 159022, 163328, 167643, 172158], kieu(6, 10))
hang('C', -88512, -82486, [151753, 156480, 160698, 164161, 168166, 172158], kieu(11, 15))
# D: khung trong 188483..205181, cột QUY CÁCH 205188..209348 (ranh lấy 205184). Mép trái nới 200 mm (MTEXT thụt lề).
them('D', u'CHỐNG THẤM LỖ MỞ, CỔ ỐNG KHOAN RÚT LÕI', 188280, -78798, 205184, -71688)
them('D', u'CHI TIẾT XỬ LÝ ỐNG ĐẶT CHỜ', 188280, -83749, 195923, -78798)
them('D', u'CHI TIẾT CHỐNG THẤM CỬA WC, CỬA QUAY LÔ GIA', 195923, -83749, 205184, -78798)
them('D', u'CHI TIẾT CHỐNG THẤM CHÂN CỬA LÙA LOGIA', 188280, -88512, 205184, -83749)
them('D', u'QUY CÁCH CHỐNG THẤM', 205184, -88512, 209348, -71688)
# E: 4 hàng, mỗi ô gồm cả dải tiêu đề phía trên. Khung hơi xiên (1,6 mm) nên mép ngoài nới 6 mm.
xa, xb, ya, yb = 151724, 158692, -99192, -93645
hang('E', -94719, yb, [xa, 153445, 154384, 156164, 157770, xb],
     [u'Chống thấm sàn tầng hầm 3', u'Chống thấm vách tường vây', u'Chống thấm rãnh thu nước, rãnh thoát nước',
      u'Chống thấm hố pít thang máy', u'Chống thấm cột bê tông trong bể'])
hang('E', -96260, -94719, [xa, 153710, 157159, xb],
     [u'Chống thấm mái tầng hầm (sàn ground)', u'Chống thấm bể xử lý nước thải, bể nước sinh hoạt',
      u'Chống thấm bể bơi, bể cân bằng, bể cảnh'])
hang('E', -97645, -96260, [xa, 153710, 155489, 157096, xb],
     [u'Chống thấm cổ ống kỹ thuật xuyên sàn', u'Chống thấm hộp kỹ thuật, tường xây ngoài trời',
      u'Chống thấm nhà vệ sinh, ban công, lôgia, phòng KT nước', u'Chống thấm Tầng mái, Tầng Tum, sê nô'])
hang('E', ya, -97645, [xa, 153710, 155489, 157093, xb],
     [u'Chống thấm bồn trồng cây, mái xanh', u'CHỐNG THẤM GIẰNG MÓNG VÀ SÀN TẦNG HẦM',
      u'CHỐNG THẤM ĐÀI CỌC VÀ SÀN TẦNG HẦM', u'BĂNG CẢN NƯỚC SIKA WATERBAR V20'])
# F
them('F', u'CHI TIẾT CHỐNG THẤM TƯỜNG VỆ SINH TẠI VỊ TRÍ VÒI TẮM ĐỨNG', 188280, -104098, 197225, -93916)
them('F', u'CHI TIẾT CHỐNG THẤM TƯỜNG PHÒNG KỸ THUẬT ƯỚT, PHÒNG RÁC', 188280, -110740, 202910, -104098)
them('F', u'BẢNG KHU VỰC CHỐNG THẤM - QUY CÁCH CẤU TẠO', 197225, -104098, 202910, -93916)
them('F', u'HƯỚNG DẪN QUY TRÌNH CHỐNG THẤM', 202910, -110740, 209348, -93916)
# G: bảng ký hiệu nằm xa cụm chính
them('G', u'KÝ HIỆU CHỐNG THẤM', -248200, -181300, -203500, -167300)

ra = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'o_cfg.json')
json.dump({'to': TO, 'o': O}, io.open(ra, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(TO), 'tờ,', len(O), 'ô ->', ra)
