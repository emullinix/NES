__author__ = 'Evan'


class Memory(object):
    RAM = bytearray(2048)
    

    def __init__(self, filename):
        f = open(filename, 'rb')
        header = f.read(16)
        for i in range(0, header[4]):
            self.PRGROM = bytes(f.read(0x4000))
        for i in range(0, header[5]):
            self.CHRROM = bytes(f.read(0x2000))

    def __getitem__(self, item):
        if item < 0x2000:
            return self.RAM[item & 0x7FF]
        elif item < 0x8000:
            pass
        elif item < 0x10000:
            return self.CHRROM[item & 0x3FFF]

    def __setitem__(self, key, value):
        if key < 0x2000:
            self.RAM[key & 0x7FF] = value

