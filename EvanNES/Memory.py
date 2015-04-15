__author__ = 'Evan'


class Memory(object):
    RAM = bytearray(2048)

    def __init__(self, filename):
        with open(filename, 'rb') as f:
            self.header = f.read(16)
            header = self.header
            self.PRGROM = bytes(f.read(header[4] * 0x4000))
            #for i in range(0, header[4]):
            #    self.PRGROM += bytes(f.read(0x4000))
            self.CHRROM = bytes(f.read(header[5] * 0x2000))
            #for i in range(0, header[5]):
            #    self.CHRROM += bytes(f.read(0x2000))
            self.stack = Stack(self)

    def __getitem__(self, item):
        if item < 0x2000:
            return self.RAM[item & 0x7FF]
        elif item >= 0x8000 and item <= 0xFFFF:
            if self.header[4] == 1:
                return self.PRGROM[item & 0x3FFF]
            else:
                return self.PRGROM[item & 0x7FFF]
        else:
            return self.CHRROM[item & 0x3FFF]

    def __setitem__(self, key, value):
        if key < 0x2000:
            self.RAM[key & 0x7FF] = value


class Stack(object):
    def __init__(self, m):
        self.memory = m

    def __getitem__(self, item):
        if item < 0x100:
            return self.memory[0x100 + item]
        else:
            raise ValueError('%d not in stack' % item)

    def __setitem__(self, key, value):
        if key < 0x100:
            self.memory[0x100 + key] = value
        else:
            raise ValueError('%d not in stack' % key)