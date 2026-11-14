# -*- coding: utf-8 -*-
r"""Chuyển chữ bảng mã cũ (TCVN3 / ABC và VNI) trong bản vẽ CAD về Unicode, theo FONT của từng đoạn chữ.

Bản vẽ gom từ nhiều nguồn thường lẫn 3 loại: chữ Unicode (font Arial...), chữ TCVN3 (font .VnArial, .VnArialH, vnsimli.shx...
vd. "M¹CH NGõNG" = MẠCH NGỪNG) và chữ VNI (font VNI-Helve... vd. "MAËT CAÉT" = MẶT CẮT). Đưa nguyên sang Revit (font Arial)
thì ra ký tự lạ. Không đoán theo nội dung: ký tự Latin-1 (ê, ô, ã...) vừa là chữ Unicode thật vừa là mã TCVN3 của chữ khác,
nên bảng mã lấy theo font; trong MTEXT font đổi giữa chừng bằng mã \f...; thì mỗi đoạn xét riêng.
Font chữ HOA (.VnArialH, vntimeh.shx...): gõ chữ thường nhưng hiện chữ hoa -> đổi xong thì viết hoa.
"""
import os, re, unicodedata

_T3 = {
    'µ': 'à', '¸': 'á', '¶': 'ả', '·': 'ã', '¹': 'ạ',
    '¨': 'ă', '»': 'ằ', '¾': 'ắ', '¼': 'ẳ', '½': 'ẵ', 'Æ': 'ặ',
    '©': 'â', 'Ç': 'ầ', 'Ê': 'ấ', 'È': 'ẩ', 'É': 'ẫ', 'Ë': 'ậ',
    '®': 'đ',
    'Ì': 'è', 'Ð': 'é', 'Î': 'ẻ', 'Ï': 'ẽ', 'Ñ': 'ẹ',
    'ª': 'ê', 'Ò': 'ề', 'Õ': 'ế', 'Ó': 'ể', 'Ô': 'ễ', 'Ö': 'ệ',
    '×': 'ì', 'Ý': 'í', 'Ø': 'ỉ', 'Ü': 'ĩ', 'Þ': 'ị',
    'ß': 'ò', 'ã': 'ó', 'á': 'ỏ', 'â': 'õ', 'ä': 'ọ',
    '«': 'ô', 'å': 'ồ', 'è': 'ố', 'æ': 'ổ', 'ç': 'ỗ', 'é': 'ộ',
    '¬': 'ơ', 'ê': 'ờ', 'í': 'ớ', 'ë': 'ở', 'ì': 'ỡ', 'î': 'ợ',
    'ï': 'ù', 'ó': 'ú', 'ñ': 'ủ', 'ò': 'ũ', 'ô': 'ụ',
    '\xad': 'ư', 'õ': 'ừ', 'ø': 'ứ', 'ö': 'ử', '÷': 'ữ', 'ù': 'ự',
    'ú': 'ỳ', 'ý': 'ý', 'û': 'ỷ', 'ü': 'ỹ', 'þ': 'ỵ',
    '¡': 'Ă', '¢': 'Â', '£': 'Ê', '¤': 'Ô', '¥': 'Ơ', '¦': 'Ư', '§': 'Đ',
}
# VNI: nguyên âm + 1 ký tự dấu. (mũ / trăng, thanh)
_MU, _TRANG, _MOC = '̂', '̆', '̛'
_SAC, _HUYEN, _HOI, _NGA, _NANG = '́', '̀', '̉', '̃', '̣'
_VNI_DAU = {
    'ù': ('', _SAC), 'ø': ('', _HUYEN), 'û': ('', _HOI), 'õ': ('', _NGA), 'ï': ('', _NANG),
    'â': (_MU, ''), 'á': (_MU, _SAC), 'à': (_MU, _HUYEN), 'å': (_MU, _HOI), 'ã': (_MU, _NGA), 'ä': (_MU, _NANG),
    'ê': (_TRANG, ''), 'é': (_TRANG, _SAC), 'è': (_TRANG, _HUYEN), 'ú': (_TRANG, _HOI), 'ü': (_TRANG, _NGA), 'ë': (_TRANG, _NANG),
}
_VNI_DAU.update({k.upper(): v for k, v in list(_VNI_DAU.items())})
_VNI_DON = {'ñ': 'đ', 'Ñ': 'Đ', 'ô': 'ơ', 'Ô': 'Ơ', 'ö': 'ư', 'Ö': 'Ư', 'æ': 'ỉ', 'Æ': 'Ỉ', 'ó': 'ĩ', 'Ó': 'Ĩ',
            'ò': 'ị', 'Ò': 'Ị', 'î': 'ỵ', 'Î': 'Ỵ'}       # í ì Í Ì giữ nguyên
_NGUYEN_AM = set('aeiouyAEIOUY')


def tcvn3(s):
    return ''.join(_T3.get(c, c) for c in s)


def vni(s):
    kq = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        nx = s[i + 1] if i + 1 < n else ''
        if c in _NGUYEN_AM and nx in _VNI_DAU:
            mu, thanh = _VNI_DAU[nx]
            if mu == _TRANG and c not in 'aA':
                mu = ''                       # trăng chỉ có ở a
            if mu == _MU and c not in 'aeoAEO':
                mu = ''
            kq.append(unicodedata.normalize('NFC', c + mu + thanh)); i += 2; continue
        if c in 'ôÔöÖ':                       # ơ, ư (+ thanh)
            goc = _VNI_DON[c]
            if nx in _VNI_DAU and _VNI_DAU[nx][0] == '':
                kq.append(unicodedata.normalize('NFC', goc + _VNI_DAU[nx][1])); i += 2; continue
            kq.append(goc); i += 1; continue
        kq.append(_VNI_DON.get(c, c)); i += 1
    return ''.join(kq)


_VNI_FILE = re.compile(r'^(vni|vhelve|vavo|vtimes|vcent|vbook|vcour|vpala|vswiss|vuniv|vmaria)')
_T3_FILE = re.compile(r'^v[nh](arial|time|avan|3d|couri|book|black|centu|clear|gothic|helvet|koala|linus|lucida|memor|monot|paris|presen|revue|shell|souv|ster|teknic|univer|vogue)')


def bang_ma(ten_font):
    """Tên typeface (trong mã \\f của MTEXT) hoặc tên file font của text style -> ('tcvn3' / 'vni' / None, có phải font HOA)."""
    t = (ten_font or '').strip().lower()
    if not t:
        return None, False
    if t == 'symbol':
        return 'symbol', False            # font Symbol: ký tự 0xB7 là chấm đầu dòng
    if t.startswith('.vn'):
        return 'tcvn3', t.endswith('h')
    if t.startswith('vni'):
        return 'vni', False
    goc = os.path.splitext(os.path.basename(t))[0]
    if _VNI_FILE.match(goc):
        return 'vni', False
    if t.endswith('.shx'):
        if goc.startswith('vn'):              # vnsimli.shx, vntime.shx, vntimeh.shx, vns.shx...
            return 'tcvn3', goc.endswith('h')
        return None, False
    if _T3_FILE.match(goc):
        return 'tcvn3', goc.startswith('vh')
    return None, False


# Chữ TCVN3 bị gán nhầm font Unicode (Arial...): trong CAD đã hiện sai ("chèng thÊm GI»NG MãNG"). Chỉ nhận khi chắc:
# không có ký tự ngoài Latin-1 và có ≥ 2 ký tự chỉ-TCVN3 (không phải chữ cái tiếng Việt Unicode) dính liền chữ cái.
_T3_RIENG = 'µ¸¶·¹¨»¾¼½Æ©ÇË®ÐÎÏÑªÖ×ØÜÞßäåæç«¬\xadø÷þûü¡¢£¤¥¦§'
_RE_T3_RIENG = re.compile('[A-Za-z][%s]|[%s][A-Za-z]' % (re.escape(_T3_RIENG), re.escape(_T3_RIENG)))


def giong_tcvn3(s):
    if not s or any(ord(c) > 0xFF for c in s):
        return False
    return len(_RE_T3_RIENG.findall(s)) >= 2


def doi_theo_noi_dung(s):
    """Đổi chữ TCVN3 gán nhầm font. Từ nào lẫn chữ HOA không dấu với chữ thường có dấu (gõ cho font chữ HOA) thì cả
    chuỗi viết hoa."""
    kq = tcvn3(s)
    for a, b in zip(kq, kq[1:]):
        if (a.isascii() and a.isupper() and not b.isascii() and b.islower()) or \
           (b.isascii() and b.isupper() and not a.isascii() and a.islower()):
            return kq.upper()
    return kq


def doi(s, ma, hoa, dem=None):
    """Đổi 1 đoạn chữ thường (không chứa mã định dạng) theo bảng mã."""
    if not s:
        return s
    if ma is None:
        if giong_tcvn3(s):
            if dem is not None:
                dem['tcvn3_theo_noi_dung'] = dem.get('tcvn3_theo_noi_dung', 0) + 1
            return doi_theo_noi_dung(s)
        return s
    if ma == 'symbol':
        return s.replace('\xb7', '•')
    kq = tcvn3(s) if ma == 'tcvn3' else vni(s)
    return kq.upper() if hoa else kq


_CO_THAM_SO = set('fFHWACcTQpS')        # mã có tham số, kết thúc bằng ';'


def doi_mtext(raw, font_style, dem=None):
    """Chuỗi thô của MTEXT (còn mã định dạng) -> chuỗi thô đã đổi các đoạn chữ bảng mã cũ sang Unicode. font_style = tên
    file font của text style; mã \\f<typeface>|...; đổi font cho phần sau nó, { } giữ / trả font."""
    hien = bang_ma(font_style)
    chong = []
    kq = []
    dem_ = []
    i, n = 0, len(raw)

    def xa():
        if dem_:
            s = ''.join(dem_)
            s2 = doi(s, hien[0], hien[1], dem)
            if dem is not None and s2 != s and hien[0]:
                dem[hien[0]] = dem.get(hien[0], 0) + 1
            kq.append(s2)
            del dem_[:]

    while i < n:
        c = raw[i]
        if c == '\\' and i + 1 < n:
            d = raw[i + 1]
            if d in '\\{}':
                xa(); kq.append(raw[i:i + 2]); i += 2; continue
            if d == 'U' and raw[i + 2:i + 3] == '+':
                xa(); kq.append(raw[i:i + 7]); i += 7; continue
            if d in _CO_THAM_SO:
                j = raw.find(';', i)
                if j < 0:
                    j = n - 1
                xa()
                ma = raw[i:j + 1]
                if d in 'fF':
                    hien = bang_ma(ma[2:].split('|')[0].rstrip(';'))
                kq.append(ma); i = j + 1; continue
            xa(); kq.append(raw[i:i + 2]); i += 2; continue
        if c == '{':
            xa(); chong.append(hien); kq.append(c); i += 1; continue
        if c == '}':
            xa()
            if chong:
                hien = chong.pop()
            kq.append(c); i += 1; continue
        dem_.append(c); i += 1
    xa()
    return ''.join(kq)


def doi_text(s, font_style, dem=None):
    """Chuỗi của TEXT / ATTRIB (1 font cho cả chuỗi; mã %%u, %%c... là ASCII nên không bị ảnh hưởng)."""
    ma, hoa = bang_ma(font_style)
    # giữ nguyên mã %%x và \U+XXXX
    manh = re.split(r'(%%[a-zA-Z%]|%%\d{3}|\\U\+[0-9A-Fa-f]{4})', s)
    kq = ''.join(m if (i % 2) else doi(m, ma, hoa, dem) for i, m in enumerate(manh))
    if dem is not None and kq != s and ma:
        dem[ma] = dem.get(ma, 0) + 1
    return kq


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    for s, f in (('M¹CH NGõNG THI C¤NG ', 'VHARIAL.TTF'), ('L¦íI THÐP KH¤NG GØ TERMIMESH\\P(HO{\\fArial|b0|i0|c0|p34;ẶC TƯƠNG ĐƯƠNG})', 'VHARIAL.TTF'),
                 ('\\pxi0.24829;MAËT CAÉT ÑIEÅN HÌNH VÒ TRÍ ÑÖÔØNG \\P\\pi1.19386;OÁNG XUYEÂN VAÙCHTAÀNG HAÀM', 'VHELVEN.TTF'),
                 ('{\\W0.9;bª t«ng v¸ch hÇm}', 'VHARIAL.TTF'), ('\\pxb0.25,a0.25,qj;®ai kẸP/ BRACKET', 'VHARIALN.TTF'),
                 ('chèng thÊm GI»NG MãNG Vµ SµN TÇNG HÇM', 'VHARIAL.TTF'), ('M{\\fArial|b0|i0|c0|p34;ẶT }CAÉT A-A', 'VHELVEN.TTF'),
                 ('Bê tông cốt thép', 'arial.ttf')):
        print(repr(s), '->', repr(doi_mtext(s, f)))
