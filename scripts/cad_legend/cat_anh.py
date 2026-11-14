import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, ra, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], *[float(v) for v in sys.argv[3:7]]
im = Image.open(src)
W, H = im.size
box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
c = im.crop(box)
if len(sys.argv) > 7:
    k = float(sys.argv[7]); c = c.resize((int(c.size[0] * k), int(c.size[1] * k)), Image.LANCZOS)
c.save(ra)
print(im.size, "->", c.size, ra)