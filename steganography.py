from PIL import Image
from math import ceil

class Steganography:
    def __init__(self, path):
        self.image = Image.open(path)
        self.image.close()

    def pixel_merge(self, p1, p2):
        result = tuple()
        for i, j in zip(p1, p2):
            result += (i & 0b11110000| (j & 0b11110000) >> 4,)
        return tuple(result)

    def normalize_modes(self, other):
        if self.image.mode == other.image.mode:
            return
        elif self.image.getbands() > other.image.getbands():
            with Image.open(other.image.filename) as img:
                other.image = img.convert(self.image.mode)
        else:
            with Image.open(self.image.filename) as img:
                self.image = img.convert(other.image.mode)

    def encode_size(self, img):
        # Get how many chunks of four bits are needed to store
        # each dimension
        nibbles = ceil(len(bin(max(img.size))[2:]) / 4)
        size = self.image.size[1] << nibbles * 4 | self.image.size[0]
        bands = len(img.getbands())
        mask = 0b1111
        flag = False
        px = img.load()
        for i in range(ceil((nibbles * 2 + 1) / bands)):
            colors = tuple()
            for j in range(bands):
                if not i and not j:
                    colors += (nibbles << 4,)
                elif flag:
                    colors += (px[0, i][j],)
                else:
                    shift = len(bin(mask)[2:])
                    if shift > 8:
                        colors += ((size & mask) >> shift - 8,)
                    else:
                        colors += ((size & mask) << 8 - shift,)
                    mask <<= 4
                    if mask > 2 ** (nibbles * 8):
                        flag = True
            px[0, i] = colors
            if flag: break
        return img

    def decode_size(self):
        with Image.open(self.image.filename) as img:
            px = img.load()
            nibbles = 0b1111 & px[0, 0][0]
            bands = len(self.image.getbands())
            acc = ''
            for i in range(ceil((nibbles * 2 + 1) / bands)):
                for j in range(bands):
                    if not i and not j: continue
                    if i * bands + j >= nibbles * 2 + 1:
                        return (int(acc[nibbles * 4:], 2),
                                int(acc[:nibbles * 4], 2))
                    acc = "{:04b}".format(px[0, i][j] & 15) + acc

    def merge(self, other):
        if self.image.width * self.image.height \
           <  other.image.width * other.image.height:
            print("Error: hidden image can't be bigger than source image.")
            return
        self.normalize_modes(other)
        out = Image.new(self.image.mode, self.image.size)
        with Image.open(self.image.filename) as img1, \
             Image.open(other.image.filename) as img2:
            other.encode_size(img2)
            pxout = out.load()
            px1 = img1.load()
            px2 = img2.load()
            w2 = h2 = 0
            for w1 in range(self.image.width):
                 for h1 in range(self.image.height):
                    if w2 == other.image.width:
                        pxout[w1, h1] = px1[w1, h1]
                    else:
                        pxout[w1, h1] = self.pixel_merge(px1[w1, h1], px2[w2, h2])
                        h2 += 1
                        if h2 == other.image.height:
                            h2 = 0
                            w2 += 1
        out.save("merged_image.png")
        out.close()

    def unmerge(self):
        with Image.open(self.image.filename) as img:
            out = Image.new(self.image.mode, self.decode_size())
            pxout = out.load()
            px = img.load()
            w2 = h2 = 0
            for w1 in range(self.image.width):
                for h1 in range(self.image.height):
                    if w2 == out.width: break
                    colors = tuple()
                    colors_out = tuple()
                    for color in px[w1, h1]:
                        colors += (color & 0b11110000,)
                        colors_out += ((color & 0b1111 ) << 4,)
                    px[w1, h1] = colors
                    pxout[w2, h2] = colors_out
                    h2 += 1
                    if h2 == out.height:
                        h2 = 0
                        w2 += 1
            img.save("decoded_" + self.image.filename)
        out.save("hidden.png")
        out.close()
