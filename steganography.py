from PIL import Image

class Steganography:
    def __init__(self, image):
        self.image = image
        self.px = image.load()


    def pixel_merge(self, p1, p2):
        return (p1[0] & 240 | (p2[0] & 240) >> 4,
                p1[1] & 240 | (p2[1] & 240) >> 4,
                p1[2] & 240 | (p2[2] & 240) >> 4)

    def encode_size(self):
        self.px[0,0] = ((self.image.width & 15) << 4,
                       (self.image.width & 240),
                        (self.image.width & 3840) >> 4)
        self.px[0,1] = ((self.image.width & 61440) >> 8,
                       (self.image.height & 15) << 4,
                       (self.image.height & 240))
        self.px[0,2] = ((self.image.height & 3840) >> 4,
                       (self.image.height & 61440) >> 8,
                       self.px[0, 2][2])

    def decode_size(self):
        width = self.px[0,0][0] & 15
        width += (self.px[0,0][1] & 15) << 4
        width += (self.px[0,0][2] & 15) << 8
        width += (self.px[0,1][0] & 15) << 12
        height = self.px[0,1][1] & 15
        height += (self.px[0,1][2] & 15) << 4
        height += (self.px[0,2][0] & 15) << 8
        height += (self.px[0,2][1] & 15) << 12
        return (width, height)

    def merge(self, other):
        if self.image.width * self.image.height \
           <  other.image.width * other.image.height:
            print("Error: hidden image can't be bigger than source image.")
            return None
        else:
            other.encode_size()
            out = Steganography(Image.new('RGB', self.image.size))
            w2 = h2 = 0
            for w1 in range(self.image.width):
                for h1 in range(self.image.height):
                    if h2 == other.image.height:
                        h2 = 0
                        w2 += 1
                    if w2 == other.image.width:
                        out.px[w1, h1] = self.px[w1, h1]
                    else:
                        out.px[w1, h1] = self.pixel_merge(self.px[w1, h1],
                                                          other.px[w2, h2])
                        h2 += 1
            return out

    def unmerge(self):
        out = Steganography(Image.new('RGB', self.decode_size()))
        width, height = self.decode_size()
        w2 = h2 = 0
        for w1 in range(self.image.width):
            for h1 in range(self.image.height):
                if h2 == height:
                    h2 = 0
                    w2 += 1
                if w2 == width:
                    break
                out.px[w2, h2] = ((self.px[w1, h1][0] & 15) << 4,
                               (self.px[w1, h1][1] & 15) << 4,
                               (self.px[w1, h1][2] & 15) << 4)
                self.px[w1, h1] = ((self.px[w1, h1][0] & 240),
                                      (self.px[w1, h1][1] & 240),
                                      (self.px[w1, h1][2] & 240))
                h2 += 1
        return out
# def main():
image = Steganography(Image.open("anon.jpg"))
hidden = Steganography(Image.open("cove.jpg"))
target = image.merge(hidden)
target.image.save('merged.jpg')
new = target.unmerge()
new.image.save('unmerged.jpg')
