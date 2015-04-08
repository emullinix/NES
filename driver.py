__author__ = 'Evan'
filename   = 'E:\\Downloads\\nestest.nes'

f = open(filename, 'rb')
header = f.read(16)
if header[0] != ord('N') or header[1] != ord('E') or header[2] != ord('S'):
    print('Invalid NES file header: %c%c%c' % (header[0], header[1], header[2]))
    exit(1)

print('File has %d program ROM pages (16kB ROM banks)'   % header[4])
print('File has %d character ROM pages (8kB VROM banks)' % header[5])
mappernum = (header[6] >> 4) & 0xF
print('Four screen mode = %s' % ['yes', 'no'][header[6] & 0x8 == 0])
print(['512 byte trainer at 0x7000-0x71FF', 'No trainer present'][header[6] & 0x4 == 0])
print('SRAM at 0x6000-0x7FFF is battery backed = %s' % ['yes', 'no'][header[6] & 0x2 == 0])
print('Mirroring = %s' % ['vertical', 'horizontal'][header[6] & 0x1 == 0])
mappernum |= (header[7] & 0xF0)
print('Using NES 2.0 rules = %s' % ['no', 'yes'][header[7] & 0xC == 0x8])
print('Playchoice 10 = %s' % ['yes', 'no'][header[7] & 0x2 == 0])
print('Vs. Unisystem = %s' % ['yes', 'no'][header[7] & 0x1 == 0])
print('Mapper number is %d' % mappernum)
print('Program RAM size is %dKB' % (max(header[8], 1) * 8))
print('TV System = %s' % ['PAL', 'NTSC'][header[9] & 0x1 == 0])
print('TV System = %s' % {0: 'NTSC', 1: 'dual compatible', 2: 'PAL', 3: 'dual compatible'}[header[10] & 0x3])
print('SRAM at 0x6000-0x7FFF is battery backed = %s' % ['no', 'yes'][header[10] & 0x10 == 0])
print('Bus conflicts = %s' % ['yes', 'no'][header[10] & 0x20 == 0])
for i in [11, 12, 13, 14, 15]:
    if header[i] != 0:
        print('Warning: header byte %d is not zero (%c)' % (i, header[i]))

