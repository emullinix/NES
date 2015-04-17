from EvanNES import Memory
__author__ = 'Evan'

class CPU(object):

    A = 0
    X = 0
    Y = 0
    PC = 0
    SP = 0
    carry = 0
    zero  = 0
    imask = 0
    brk   = 0
    oflow = 0
    neg   = 0
    decimal = 0
    memory = None

    def getP(self):
        return [0, 1][self.carry] + [0, 2][self.zero] + [0,4][self.imask] + [0, 8][self.decimal] + 32 + [0, 64][self.oflow] + [0, 128][self.neg]

    def setP(self, p):
        self.carry   = p & 1
        self.zero    = (p >> 1) & 1
        self.imask   = (p >> 2) & 1
        self.decimal = (p >> 3) & 1
        self.oflow   = (p >> 6) & 1
        self.neg     = (p >> 7) & 1

    def __init__(self, filename):
        self.memory = Memory.Memory(filename)

    def implicitOp(self, op):
        op(self)
        return 0

    def accumulatorOp(self, op):
        op(self, imm = self.A)
        return 0

    def immediateOp(self, op):
        op(self, imm = self.memory[self.PC + 1])
        return 0

    def zeroPageOp(self, op):
        op(self, adr = self.memory[self.PC + 1])
        return 0

    def zeroPageXOp(self, op):
        op(self, adr = (self.memory[self.PC + 1] + self.X) & 0xFF)
        return 0

    def zeroPageYOp(self, op):
        op(self, adr = (self.memory[self.PC + 1] + self.Y) & 0xFF)
        return 0

    def absoluteOp(self, op):
        op(self, adr = self.memory[self.PC + 1] + (self.memory[self.PC + 2] << 8))
        return 0

    def absoluteXOp(self, op, checkpage = False):
        low = self.memory[self.PC + 1]
        cycles = [0, 1][checkpage and low + self.X > 0xFF] # TODO check negative?
        op(self, adr=((low + (self.memory[self.PC + 2] << 8) + self.X) & 0xFFFF))
        return cycles

    def absoluteYOp(self, op, checkpage = False):
        low = self.memory[self.PC + 1]
        cycles = [0, 1][checkpage and low + self.Y > 0xFF]
        op(self, adr=((low + (self.memory[self.PC + 2] << 8) + self.Y) & 0xFFFF))
        return cycles

    def indirectOp(self, op):
        target = self.memory[self.PC + 1] + (self.memory[self.PC + 2] << 8)
        if target & 0xFF == 0xFF:
            msbadr = target & 0xFF00
        else:
            msbadr = target + 1
        op(self, adr=(self.memory[target] + (self.memory[msbadr] << 8)) & 0xFFFF)
        return 0

    def indirectXOp(self, op):
        adrlsb = (self.memory[self.PC + 1] + self.X) & 0xFF
        op(self, adr=(self.memory[adrlsb] + (self.memory[adrlsb + 1] << 8)) & 0xFFFF)
        return 0

    def indirectYOp(self, op, checkpage = False):
        adrlsb = self.memory[self.PC + 1]
        cycles = [0, 1][checkpage and self.memory[adrlsb] + self.Y > 0xFF]
        op(self, adr=(self.memory[adrlsb] + (self.memory[(adrlsb + 1) & 0xFF] << 8) + self.Y) & 0xFFFF)
        return cycles

    def relativeOp(self, op):
        offset = self.memory[self.PC + 1]
        if offset > 127:
            offset -= 256
        pclow = self.PC & 0xFF
        cycles = 1
        if pclow + offset + 2 > 255 or pclow + offset + 2 < 0:
            cycles = 2
        return [0, cycles][op(self, adr=offset + self.PC)]

    def ADC(self, imm = 0, adr = -1):
        if adr != -1:
            imm += self.memory[adr]
        apos = (self.A & 0x80) == 0
        mpos = (imm    & 0x80) == 0
        self.A += imm + self.carry
        self.carry = (self.A & 0x100) != 0
        self.A &= 0xFF
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0
        self.oflow = (apos == mpos) and (self.neg == apos)

    def AND(self, imm = 0, adr = -1):
        if adr != -1:
            imm  |= self.memory[adr]
        self.A   &= imm
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    def ASL(self, imm = 0, adr = -1):
        if adr != -1:
            imm  |= self.memory[adr]
        self.carry = (imm & 0x80) != 0
        self.neg   = (imm & 0x40) != 0
        imm = (imm & 0x7F) << 1
        self.zero = imm == 0
        if adr == -1:
            self.A = imm
        else:
            self.memory[adr] = imm

    def BCC(self, adr):
        if not self.carry:
            self.PC = adr
            return 1
        else:
            return 0

    def BCS(self, adr):
        if self.carry:
            self.PC = adr
            return 1
        else:
            return 0

    def BEQ(self, adr):
        if self.zero:
            self.PC = adr
            return 1
        else:
            return 0

    def BIT(self, adr = -1):
        value = self.memory[adr]
        self.oflow = (value & 0x40) != 0
        self.neg   = (value & 0x80) != 0
        value = self.A & self.memory[adr]
        self.zero = value == 0

    def BMI(self, adr):
        if self.neg:
            self.PC = adr
            return 1
        else:
            return 0

    def BNE(self, adr):
        if not self.zero:
            self.PC = adr
            return 1
        else:
            return 0

    def BPL(self, adr):
        if not self.neg:
            self.PC = adr
            return 1
        else:
            return 0

    def BRK(self):
        tostore = self.PC + 2
        self.memory.stack[self.SP] = (tostore >> 8) & 0xFF
        self.memory.stack[self.SP - 1] = tostore & 0xFF
        self.memory.stack[self.SP - 2] = [0, 1][self.carry] + [0, 2][self.zero] + [0,4][self.imask] + 48 + [0, 64][self.oflow] + [0, 128][self.neg]
        self.SP -= 3
        self.brk = 1
        self.PC  = self.memory[0xFFFE] + (self.memory[0xFFFF] << 8) - 1 # because the execute code will add one for this inst

    def BVC(self, adr):
        if not self.oflow:
            self.PC = adr
            return 1
        else:
            return 0

    def BVS(self, adr):
        if self.oflow:
            self.PC = adr
            return 1
        else:
            return 0

    def CLC(self):
        self.carry = False

    def CLD(self):
        self.decimal = False

    def CLI(self):
        self.imask = False

    def CLV(self):
        self.oflow = False

    def CMP(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]

        diff = self.A - imm
        self.zero  =  diff == 0
        self.carry =  diff >= 0
        self.neg   = (diff & 0x80) != 0

    def CPX(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]

        diff = self.X - imm
        self.zero  =  diff == 0
        self.carry =  diff >= 0
        self.neg   = (diff & 0x80) != 0

    def CPY(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]

        diff = self.Y - imm
        self.zero  =  diff == 0
        self.carry =  diff >= 0
        self.neg   = (diff & 0x80) != 0

    def DEC(self, adr):
        value = (0xFF + self.memory[adr]) & 0xFF
        self.zero =  value == 0
        self.neg  = (value & 0x80) != 0
        self.memory[adr] = value

    def DEX(self):
        self.X = (0xFF + self.X) & 0xFF
        self.zero =  self.X == 0
        self.neg  = (self.X & 0x80) != 0

    def DEY(self):
        self.Y = (0xFF + self.Y) & 0xFF
        self.zero =  self.Y == 0
        self.neg  = (self.Y & 0x80) != 0

    def EOR(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]

        self.A = self.A ^ imm
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    def INC(self, adr):
        value = (0x1 + self.memory[adr]) & 0xFF
        self.zero =  value == 0
        self.neg  = (value & 0x80) != 0
        self.memory[adr] = value

    def INX(self):
        self.X = (0x1 + self.X) & 0xFF
        self.zero =  self.X == 0
        self.neg  = (self.X & 0x80) != 0

    def INY(self):
        self.Y = (0x1 + self.Y) & 0xFF
        self.zero =  self.Y == 0
        self.neg  = (self.Y & 0x80) != 0

    def JMP(self, adr):
        self.PC = adr - 3 # because my code increments the pc by 3 after jumps

    def JSR(self, adr):
        tostore = self.PC + 2
        self.memory.stack[self.SP]     = (tostore & 0xFF00) >> 8
        self.memory.stack[self.SP - 1] =  tostore & 0xFF
        self.SP -= 2
        self.PC  = adr - 3 # because my code increments the pc by 3 after jsrs

    def LDA(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        self.A = imm
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0

    def LDX(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        self.X = imm
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0

    def LDY(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        self.Y = imm
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0

    def LSR(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        self.carry = (imm & 0x1) == 1
        imm = (imm >> 1) & 0x7F
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0
        if adr == -1:
            self.A = imm
        else:
            self.memory[adr] = imm

    def NOP(self):
        pass

    def ORA(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        self.A |= imm
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    def PHA(self):
        self.memory.stack[self.SP] = self.A
        self.SP -= 1

    def PHP(self):
        self.memory.stack[self.SP] = [0, 1][self.carry] + [0, 2][self.zero] + [0,4][self.imask] + 48 + [0, 64][self.oflow] \
            + [0, 128][self.neg] + [0, 8][self.decimal]
        self.SP -= 1

    def PLA(self):
        self.SP  += 1
        self.A    = self.memory.stack[self.SP]
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    def PLP(self):
        self.SP += 1
        P = self.memory.stack[self.SP]
        self.carry = (P & 1) == 1
        self.zero  = (P & 2) == 2
        self.imask = (P & 4) == 4
        self.brk   = (P & 16) == 16
        self.oflow = (P & 64) == 64
        self.neg   = (P & 128) == 128

    def ROL(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        c = self.carry
        self.carry = (imm & 0x80) != 0
        imm = (imm << 1) & 0xFF
        if c:
            imm |= 1
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0
        if adr != -1:
            self.memory[adr] = imm
        else:
            self.A = imm

    def ROR(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        c = self.carry
        self.carry = (imm & 0x1) != 0
        imm = (imm >> 1) & 0xFF
        if c:
            imm |= 0x80
        self.zero =  imm == 0
        self.neg  = (imm & 0x80) != 0
        if adr != -1:
            self.memory[adr] = imm
        else:
            self.A = imm

    def RTI(self):
        P = self.memory.stack[self.SP + 1]
        self.PC = self.memory.stack[self.SP + 2] + (self.memory.stack[self.SP + 3] << 8) - 1 # execute code will add one
        self.SP += 3
        self.carry = (P & 1) == 1
        self.zero  = (P & 2) == 2
        self.imask = (P & 4) == 4
        self.brk   = (P & 16) == 16
        self.oflow = (P & 64) == 64
        self.neg   = (P & 128) == 128

    def RTS(self):
        self.PC = self.memory.stack[self.SP + 1] + (self.memory.stack[self.SP + 2] << 8)
        self.SP += 2

    def SBC(self, imm = 0, adr = -1):
        if adr != -1:
            imm = self.memory[adr]
        apos = (self.A & 0x80) == 0
        mpos = (imm    & 0x80) == 0
        self.A = self.A + (imm ^ 0xFF) + [0,1][self.carry]
        self.carry = (self.A & 0x100) != 0
        self.A &= 0xFF
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0
        self.oflow = (apos != mpos) and (self.neg == apos)

    def SEC(self):
        self.carry = True

    def SED(self):
        self.decimal = True

    def SEI(self):
        self.imask = True

    def STA(self, adr):
        self.memory[adr] = self.A

    def STX(self, adr):
        self.memory[adr] = self.X

    def STY(self, adr):
        self.memory[adr] = self.Y

    def TAX(self):
        self.X = self.A
        self.zero =  self.X == 0
        self.neg  = (self.X & 0x80) != 0

    def TAY(self):
        self.Y = self.A
        self.zero =  self.Y == 0
        self.neg  = (self.Y & 0x80) != 0

    def TSX(self):
        self.X = self.SP
        self.zero =  self.X == 0
        self.neg  = (self.X & 0x80) != 0

    def TXA(self):
        self.A = self.X
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    def TXS(self):
        self.SP = self.X

    def TYA(self):
        self.A = self.Y
        self.zero =  self.A == 0
        self.neg  = (self.A & 0x80) != 0

    ops = {
        0x69: ('Add with carry immediate',   2, (2, False), ADC, immediateOp),
        0x65: ('Add with carry zero page',   2, (3, False), ADC, zeroPageOp),
        0x75: ('Add with carry zero page x', 2, (4, False), ADC, zeroPageXOp),
        0x6D: ('Add with carry absolute',    3, (4, False), ADC, absoluteOp),
        0x7D: ('Add with carry absolute x',  3, (4, True),  ADC, absoluteXOp),
        0x79: ('Add with carry absolute y',  3, (4, True),  ADC, absoluteYOp),
        0x61: ('Add with carry indirect x',  2, (6, False), ADC, indirectXOp),
        0x71: ('Add with carry indirect y',  2, (5, True),  ADC, indirectYOp),
        0x29: ('Logical AND immediate',      2, (2, False), AND, immediateOp),
        0x25: ('Logical AND zero page',      2, (3, False), AND, zeroPageOp),
        0x35: ('Logical AND zero page x',    2, (4, False), AND, zeroPageXOp),
        0x2D: ('Logical AND absolute',       3, (4, False), AND, absoluteOp),
        0x3D: ('Logical AND absolute x',     3, (4, True),  AND, absoluteXOp),
        0x39: ('Logical AND absolute y',     3, (4, True),  AND, absoluteYOp),
        0x21: ('Logical AND indirect x',     2, (6, False), AND, indirectXOp),
        0x31: ('Logical AND indirect y',     2, (5, True),  AND, indirectYOp),
        0x0A: ('Ashift left immediate',      1, (2, False), ASL, accumulatorOp),
        0x06: ('Ashift left zero page',      2, (5, False), ASL, zeroPageOp),
        0x16: ('Ashift left zero page x',    2, (6, False), ASL, zeroPageXOp),
        0x0E: ('Ashift left absolute',       3, (6, False), ASL, absoluteOp),
        0x1E: ('Ashift left absolute x',     3, (7, False), ASL, absoluteXOp),
        0x90: ('Branch if carry clear',      2, (2, False), BCC, relativeOp),
        0xB0: ('Branch if carry set',        2, (2, False), BCS, relativeOp),
        0xF0: ('Branch if equal',            2, (2, False), BEQ, relativeOp),
        0x24: ('Bit test zero page',         2, (3, False), BIT, zeroPageOp),
        0x2C: ('Bit test absolute',          3, (4, False), BIT, absoluteOp),
        0x30: ('Branch if minus',            2, (2, False), BMI, relativeOp),
        0xD0: ('Branch if not equal',        2, (2, False), BNE, relativeOp),
        0x10: ('Branch if positive',         2, (2, False), BPL, relativeOp),
        0x00: ('Force interrupt',            1, (7, False), BRK, implicitOp),
        0x50: ('Branch if overflow clear',   2, (2, False), BVC, relativeOp),
        0x70: ('Branch if overflow set',     2, (2, False), BVS, relativeOp),
        0x18: ('Clear carry flag',           1, (2, False), CLC, implicitOp),
        0xD8: ('Clear decimal mode',         1, (2, False), CLD, implicitOp),
        0x58: ('Clear interrupt disable',    1, (2, False), CLI, implicitOp),
        0xB8: ('Clear overflow flag',        1, (2, False), CLV, implicitOp),
        0xC9: ('Compare immediate',          2, (2, False), CMP, immediateOp),
        0xC5: ('Compare zero page',          2, (3, False), CMP, zeroPageOp),
        0xD5: ('Compare zero page x',        2, (4, False), CMP, zeroPageXOp),
        0xCD: ('Compare absolute',           3, (4, False), CMP, absoluteOp),
        0xDD: ('Compare absolute x',         3, (4, True),  CMP, absoluteXOp),
        0xD9: ('Compare absolute y',         3, (4, True),  CMP, absoluteYOp),
        0xC1: ('Compare indirect x',         2, (6, False), CMP, indirectXOp),
        0xD1: ('Compare indirect y',         2, (5, True),  CMP, indirectYOp),
        0xE0: ('Compare x immediate',        2, (2, False), CPX, immediateOp),
        0xE4: ('Compare x zero page',        2, (3, False), CPX, zeroPageOp),
        0xEC: ('Compare x absolute',         3, (4, False), CPX, absoluteOp),
        0xC0: ('Compare y immediate',        2, (2, False), CPY, immediateOp),
        0xC4: ('Compare y zero page',        2, (3, False), CPY, zeroPageOp),
        0xCC: ('Compare y absolute',         3, (4, False), CPY, absoluteOp),
        0xC6: ('Dec memory zero page',       2, (5, False), DEC, zeroPageOp),
        0xD6: ('Dec memory zero page x',     2, (6, False), DEC, zeroPageXOp),
        0xCE: ('Dec memory absolute',        3, (6, False), DEC, absoluteOp),
        0xDE: ('Dec memory absolute x',      3, (7, False), DEC, absoluteXOp),
        0xCA: ('Decrement x register',       1, (2, False), DEX, implicitOp),
        0x88: ('Decrement y register',       1, (2, False), DEY, implicitOp),
        0x49: ('Exclusive or immediate',     2, (2, False), EOR, immediateOp),
        0x45: ('Exclusive or zero page',     2, (3, False), EOR, zeroPageOp),
        0x55: ('Exclusive or zero page x',   2, (4, False), EOR, zeroPageXOp),
        0x4D: ('Exclusive or absolute',      3, (4, False), EOR, absoluteOp),
        0x5D: ('Exclusive or absolute x',    3, (4, True),  EOR, absoluteXOp),
        0x59: ('Exclusive or absolute y',    3, (4, True),  EOR, absoluteYOp),
        0x41: ('Exclusive or indirect x',    2, (6, False), EOR, indirectXOp),
        0x51: ('Exclusive or indirect y',    2, (5, True),  EOR, indirectYOp),
        0xE6: ('Inc memory zero page',       2, (5, False), INC, zeroPageOp),
        0xF6: ('Inc memory zero page x',     2, (6, False), INC, zeroPageXOp),
        0xEE: ('Inc memory absolute',        3, (6, False), INC, absoluteOp),
        0xFE: ('Inc memory absolute x',      3, (7, False), INC, absoluteXOp),
        0xE8: ('Increment x register',       1, (2, False), INX, implicitOp),
        0xC8: ('Increment y register',       1, (2, False), INY, implicitOp),
        0x4C: ('Jump absolute',              3, (3, False), JMP, absoluteOp),
        0x6C: ('Jump indirect',              3, (5, False), JMP, indirectOp),
        0x20: ('Jump to subroutine',         3, (6, False), JSR, absoluteOp),
        0xA9: ('Load accum immediate',       2, (2, False), LDA, immediateOp),
        0xA5: ('Load accum zero page',       2, (3, False), LDA, zeroPageOp),
        0xB5: ('Load accum zero page x',     2, (4, False), LDA, zeroPageXOp),
        0xAD: ('Load accum absolute',        3, (4, False), LDA, absoluteOp),
        0xBD: ('Load accum absolute x',      3, (4, True),  LDA, absoluteXOp),
        0xB9: ('Load accum absolute y',      3, (4, True),  LDA, absoluteYOp),
        0xA1: ('Load accum indirect x',      2, (6, False), LDA, indirectXOp),
        0xB1: ('Load accum indirect y',      2, (5, True),  LDA, indirectYOp),
        0xA2: ('Load x reg immediate',       2, (2, False), LDX, immediateOp),
        0xA6: ('Load x reg zero page',       2, (3, False), LDX, zeroPageOp),
        0xB6: ('Load x reg zero page y',     2, (4, False), LDX, zeroPageYOp),
        0xAE: ('Load x reg absolute',        3, (4, False), LDX, absoluteOp),
        0xBE: ('Load x reg absolute y',      3, (4, True),  LDX, absoluteYOp),
        0xA0: ('Load y reg immediate',       2, (2, False), LDY, immediateOp),
        0xA4: ('Load y reg zero page',       2, (3, False), LDY, zeroPageOp),
        0xB4: ('Load y reg zero page x',     2, (4, False), LDY, zeroPageXOp),
        0xAC: ('Load y reg absolute',        3, (4, False), LDY, absoluteOp),
        0xBC: ('Load y reg absolute x',      3, (4, True),  LDY, absoluteXOp),
        0x4A: ('Lshift right immediate',     1, (2, False), LSR, accumulatorOp),
        0x46: ('Lshift right zero page',     2, (5, False), LSR, zeroPageOp),
        0x56: ('Lshift right zero page x',   2, (6, False), LSR, zeroPageXOp),
        0x4E: ('Lshift right absolute',      3, (6, False), LSR, absoluteOp),
        0x5E: ('Lshift right absolute x',    3, (7, False), LSR, absoluteXOp),
        0xEA: ('NOP',                        1, (2, False), NOP, implicitOp),
        0x09: ('Logical OR immediate',       2, (2, False), ORA, immediateOp),
        0x05: ('Logical OR zero page',       2, (3, False), ORA, zeroPageOp),
        0x15: ('Logical OR zero page x',     2, (4, False), ORA, zeroPageXOp),
        0x0D: ('Logical OR absolute',        3, (4, False), ORA, absoluteOp),
        0x1D: ('Logical OR absolute x',      3, (4, True),  ORA, absoluteXOp),
        0x19: ('Logical OR absolute y',      3, (4, True),  ORA, absoluteYOp),
        0x01: ('Logical OR indirect x',      2, (6, False), ORA, indirectXOp),
        0x11: ('Logical OR indirect y',      2, (5, True),  ORA, indirectYOp),
        0x48: ('Push Accumulator',           1, (3, False), PHA, implicitOp),
        0x08: ('Push Processor Status',      1, (3, False), PHP, implicitOp),
        0x68: ('Pull Accumulator',           1, (4, False), PLA, implicitOp),
        0x28: ('Pull Processor Status',      1, (4, False), PLP, implicitOp),
        0x2A: ('Rotate left immediate',      1, (2, False), ROL, accumulatorOp),
        0x26: ('Rotate left zero page',      2, (5, False), ROL, zeroPageOp),
        0x36: ('Rotate left zero page x',    2, (6, False), ROL, zeroPageXOp),
        0x2E: ('Rotate left absolute',       3, (6, False), ROL, absoluteOp),
        0x3E: ('Rotate left absolute x',     3, (7, False), ROL, absoluteXOp),
        0x6A: ('Rotate left immediate',      1, (2, False), ROR, accumulatorOp),
        0x66: ('Rotate left zero page',      2, (5, False), ROR, zeroPageOp),
        0x76: ('Rotate left zero page x',    2, (6, False), ROR, zeroPageXOp),
        0x6E: ('Rotate left absolute',       3, (6, False), ROR, absoluteOp),
        0x7E: ('Rotate left absolute x',     3, (7, False), ROR, absoluteXOp),
        0x40: ('Return from interrupt',      1, (6, False), RTI, implicitOp),
        0x60: ('Return from subroutine',     1, (6, False), RTS, implicitOp),
        0xE9: ('Sub with carry immediate',   2, (2, False), SBC, immediateOp),
        0xE5: ('Sub with carry zero page',   2, (3, False), SBC, zeroPageOp),
        0xF5: ('Sub with carry zero page x', 2, (4, False), SBC, zeroPageXOp),
        0xED: ('Sub with carry absolute',    3, (4, False), SBC, absoluteOp),
        0xFD: ('Sub with carry absolute x',  3, (4, True),  SBC, absoluteXOp),
        0xF9: ('Sub with carry absolute y',  3, (4, True),  SBC, absoluteYOp),
        0xE1: ('Sub with carry indirect x',  2, (6, False), SBC, indirectXOp),
        0xF1: ('Sub with carry indirect y',  2, (5, True),  SBC, indirectYOp),
        0x38: ('Set carry flag',             1, (2, False), SEC, implicitOp),
        0xF8: ('Set decimal flag',           1, (2, False), SED, implicitOp),
        0x78: ('Clear interrupt disable',    1, (2, False), SEI, implicitOp),
        0x85: ('Store accum zero page',      2, (3, False), STA, zeroPageOp),
        0x95: ('Store accum zero page x',    2, (4, False), STA, zeroPageXOp),
        0x8D: ('Store accum absolute',       3, (4, False), STA, absoluteOp),
        0x9D: ('Store accum absolute x',     3, (5, False), STA, absoluteXOp),
        0x99: ('Store accum absolute y',     3, (5, False), STA, absoluteYOp),
        0x81: ('Store accum indirect x',     2, (6, False), STA, indirectXOp),
        0x91: ('Store accum indirect y',     2, (6, False), STA, indirectYOp),
        0x86: ('Store x reg zero page',      2, (3, False), STX, zeroPageOp),
        0x96: ('Store x reg zero page y',    2, (4, False), STX, zeroPageYOp),
        0x8E: ('Store x reg absolute',       3, (4, False), STX, absoluteOp),
        0x84: ('Store y reg zero page',      2, (3, False), STY, zeroPageOp),
        0x94: ('Store y reg zero page x',    2, (4, False), STY, zeroPageXOp),
        0x8C: ('Store y reg absolute',       3, (4, False), STY, absoluteOp),
        0xAA: ('Transfer accumulator to x',  1, (2, False), TAX, implicitOp),
        0xA8: ('Transfer accumulator to y',  1, (2, False), TAY, implicitOp),
        0xBA: ('Transfer stack ptr to x',    1, (2, False), TSX, implicitOp),
        0x8A: ('Transfer x to accumulator',  1, (2, False), TXA, implicitOp),
        0x9A: ('Transfer x to stack ptr',    1, (2, False), TXS, implicitOp),
        0x98: ('Transfer y to accumulator',  1, (2, False), TYA, implicitOp),
    }

    def step(self):
        op = self.ops[self.memory[self.PC]]
        rv = op[2][0]
        if op[2][1]:
            rv += op[4](self, op[3], checkpage=True)
        else:
            rv += op[4](self, op[3])
        self.PC += op[1]
        return rv