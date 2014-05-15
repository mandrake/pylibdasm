__author__ = 'mandrake'


# Type for an operator are
# rXX   - XX bits register
# frXX  - XX bits floating point register
# immXX - XX bits immediate value
# memXX - XX bits memory address
# offXX - XX bits memory offset


class Instruction(object):

    def __init__(self, opname, value, oplist=[]):
        self.opname = opname
        self.oplist = oplist
        # binary value of the instruction
        self.value = value

    @staticmethod
    def _print_hex(x, bits):
        if bits == 8:
            return '0x%02x' % x[1]
        elif bits == 16:
            return '0x%04x' % x[1]
        elif bits == 32:
            return '0x%08x' % x[1]
        elif bits == 64:
            return '0x%016x' % x[1]
        elif bits == 128:
            return '0x%032x' % x[1]

    @staticmethod
    def _opstr(x):
        if x[0][0] == 'r' or x[0][0:1] == 'fr':
            return x[1]
        elif x[0][0:2] == 'imm':
            return Instruction._print_hex(int(x[2:]))
        elif x[0][0:2] == 'mem':
            return '(' + Instruction._print_hex(int(x[2:])) + ')'

    def __str__(self):
        opname = self.opname + ' ' * (8 - len(self.opname))
        oplist = ', '.join([Instruction._opstr(x) for x in self.oplist])
        o1 = '%s%s' % (opname, oplist)
        o2 = o1 + ' ' * (40 - len(o1))
        o3 = '%04x' % self.value if self.value < (2**16-1) else '%08x' % self.value
        return o2 + o3