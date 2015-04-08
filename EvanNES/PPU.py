__author__ = 'Evan'

class PPU(object):
    scanLine = 261
    cycle = 0
    vblank = False
    sprite0 = False
    spriteOverflow = False
    status = 0
    bgPixelLo = 0   # 16 bits
    bgPixelHi = 0   # 16 bits
    bgPalAttrLo = 0  # 8 bits
    bgPalAttrHi = 0  # 8 bits
    primaryOAM  = OAM[64]
    secondaryOAM = OAM[8]
    oamAddr   = 0
    spPixelLo = bytearray(8)
    spPixelHi = bytearray(8)
    spAttr    = bytearray(8)
    spX       = bytearray(8)
    xScroll   = 0
    yScroll   = 0
    baseNameTableAddr = 0x2000
    spritePaTableAddr = 0x0000
    backgrPaTableAddr = 0x0000
    vramIncr = 1
    bigSprites = False
    nmiGen = False
    grayscale = False
    leftBG = False
    leftSP = False
    showBG = False
    showSP = False
    intensifyR = False
    intensifyG = False
    intensifyB = False
    firstWrite = True
    ppuAddr = 0
    ppuData = 0

    def step(self):
        fineXScroll = self.xScroll & 0x7
        bgAttrIndex = ((self.bgPixelLo >> fineXScroll) & 0x1) | \
                      ((self.bgPixelHi >> (fineXScroll - 1) & 0x2))
        palette = ((self.bgPalAttrLo >> fineXScroll) & 0x1) | \
                  ((self.bgPalAttrHi >> (fineXScroll - 1) &0x2))




        top  = (self.scanLine % 32) < 16
        left = (self.cycle % 32) < 16  # TODO use fineXScroll here?
        if top and left:
            palette = ((self.bgPalAttrLo >> 0) & 0x3) | ((self.bgPalAttrHi << 0) & 0x3)
        elif top and not left:
            palette = ((self.bgPalAttrLo >> 2) & 0x3) | ((self.bgPalAttrHi))

        self.cycle += 1
        if self.cycle > 340:
            self.cycle = 0
            self.scanLine = (self.scanLine + 1) % 262

    def __setitem__(self, key, value):
        if key >= 0x2000 and key <= 0x2007:
            self.status = value & 0x1F
        if key == 0x2000:
            # ignored for 30000 cycles after reset
            nameTableNum = value & 0x3
            if nameTableNum == 0:
                self.baseNameTableAddr = 0x2000
            elif nameTableNum == 1:
                self.baseNameTableAddr = 0x2400
            elif nameTableNum == 2:
                self.baseNameTableAddr = 0x2800
            elif nameTableNum == 3:
                self.baseNameTableAddr = 0x2C00
            if value & 0x4:
                self.vramIncr = 32
            else:
                self.vramIncr = 1
            if value & 0x8:
                self.spritePaTableAddr = 0x1000
            else:
                self.spritePaTableAddr = 0x0000
            if value & 0x10:
                self.backgrPaTableAddr = 0x1000
            else:
                self.backgrPaTableAddr = 0x0000
            self.bigSprites = (value & 0x40) == 0x40
            self.nmiGen = (value & 0x80) == 0x80
        elif key == 0x2001:
            self.grayscale = (value & 0x01) == 0x01
            self.leftBG = (value & 0x02) == 0x02
            self.leftSP = (value & 0x04) == 0x04
            self.showBG = (value & 0x08) == 0x08
            self.showSP = (value & 0x10) == 0x10
            self.intensifyR = (value & 0x20) == 0x20
            self.intensifyG = (value & 0x40) == 0x40
            self.intensifyB = (value & 0x80) == 0x80
        elif key == 0x2003:
            self.oamAddr = value & 0xFF
        elif key == 0x2004:
            if self.scanLine == 261 or self.scanLine <= 239:
                pass #ignore
            else:
                self.primaryOAM[self.oamAddr >> 2][self.oamAddr & 0x3] = value
                self.oamAddr += 1 #TODO handle vertical stepping
        elif key == 0x2005:
            if self.firstWrite:
                self.xScroll = value
            else:
                self.yScroll = value
            self.firstWrite = not self.firstWrite
        elif key == 0x2006:
            if self.firstWrite:
                self.ppuAddr = (value << 8) & (self.ppuAddr & 0xFF)
            else:
                self.ppuAddr = value & (self.ppuAddr & 0xFF00)
            self.firstWrite = not self.firstWrite
        elif key == 0x2007:
            self.vram[self.ppuAddr] = value
            if self.vramIncr:
                self.ppuAddr += 32
            else:
                self.ppuAddr += 1

        def __getitem__(self, item):
            if item == 0x2002:
                rv = self.status | (self.spriteOverflow << 5) | (self.sprite0 << 6) | (self.vblank << 7)
                self.vblank = False
            elif item == 0x2004:
                rv = self.primaryOAM[self.oamAddr >> 2][self.oamAddr & 0x3]
            elif item == 0x2007:
                item & 0x3FFF
            return rv




class OAM(object):
    x = 0
    y = 0 # 0xEF - 0xFF means hidden
    tileIndex = 0
    palette = 4 # 4 - 7
    inBack = False
    flipH = False
    flipV = False

    def __getitem__(self, item):
        if item == 0:
            return self.y
        elif item == 1:
            return self.tileIndex
        elif item == 2:
            return (self.palette & 0x3) | (self.inBack << 5) | (self.flipH << 6) | (self.flipV << 7)
        elif item == 3:
            return self.x

    def __setitem__(self, key, value):
        if key == 0:
            self.y = value
        elif key == 1:
            self.tileIndex = value
        elif key == 2:
            self.palette = (value & 0x3) | 0x4
            self.inBack  = (value & 0x20) == 0x20
            self.flipH   = (value & 0x40) == 0x40
            self.flipV   = (value & 0x80) == 0x80
        elif key == 3:
            self.x = value