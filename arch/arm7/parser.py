__author__ = 'mandrake'

from binreader import BinaryReader
from util.instruction import Instruction
from array import array
import time
import cProfile
import pstats


p = cProfile.Profile()

class ARMv7Parser(object):

    # Shift (immediate), add, subtract, move, and compare on page A5-157
    @staticmethod
    def _thumb16_decode_cat1(i):
        opcode = [i & 0x3800, i & 0x3e00]
        # Logical Shift Left
        if opcode[0] == 0x0000:
            j = Instruction('LSL', i, [])
        # Logical Shift Left
        elif opcode[0] == 0x0800:
            j = Instruction('LSR', i, [])
        # Arithmetic Shift Right
        elif opcode[0] == 0x1000:
            j = Instruction('ASR', i, [])
        # Add register
        elif opcode[1] == 0x1800:
            j = Instruction('ADD', i, [])
        # Subtract register
        elif opcode[1] == 0x1a00:
            j = Instruction('SUB', i, [])
        # Add 3-bit immediate
        elif opcode[1] == 0x1c00:
            j = Instruction('ADD', i, [])
        # Subtract 3-bit immediate
        elif opcode[1] == 0x1e00:
            j = Instruction('SUB', i, [])
        # Move
        elif opcode[0] == 0x2000:
            j = Instruction('MOV', i, [])
        # Compare
        elif opcode[0] == 0x2800:
            j = Instruction('CMP', i, [])
        # Add 8-bit immediate
        elif opcode[0] == 0x3000:
            j = Instruction('ADD', i, [])
        # Subtract 8-bit immediate
        elif opcode[0] == 0x3800:
            j = Instruction('SUB', i, [])
        else:
            j = 'This should not happen (cat1) %04x %18s' % (i, str(bin(i)))
        return j

    # Data processing on page A5-158
    @staticmethod
    def _thumb16_decode_cat2(i):
        opcode = (i & 0x03c0) >> 6

        # Bitwise AND
        if opcode == 0x00:
            j = Instruction('AND', i, [])
        # Exclusive OR
        elif opcode == 0x01:
            j = Instruction('EOR', i, [])
        # Logical Shift Left
        elif opcode == 0x02:
            j = Instruction('LSL', i, [])
        # Logical Shift Right
        elif opcode == 0x03:
            j = Instruction('LSR', i, [])
        # Arithmetic Shift Right
        elif opcode == 0x04:
            j = Instruction('ASR', i, [])
        # Add with Carry
        elif opcode == 0x05:
            j = Instruction('ADC', i, [])
        # Subtract with
        elif opcode == 0x06:
            j = Instruction('SBC', i, [])
        # Rotate Right
        elif opcode == 0x07:
            j = Instruction('ROR', i, [])
        # Set flags on bitwise AND
        elif opcode == 0x08:
            j = Instruction('TST', i, [])
        # Reverse Subtract from 0
        elif opcode == 0x09:
            j = Instruction('RSB', i, [])
        # Compare Registers
        elif opcode == 0x0a:
            j = Instruction('CMP', i, [])
        # Compare Negative
        elif opcode == 0x0b:
            j = Instruction('CMN', i, [])
        # Logical OR
        elif opcode == 0x0c:
            j = Instruction('ORR', i, [])
        # Multiply Two Registers
        elif opcode == 0x0d:
            j = Instruction('MUL', i, [])
        # Bit Clear
        elif opcode == 0x0e:
            j = Instruction('BIC', i, [])
        # Bitwise NOT
        elif opcode == 0x0f:
            j = Instruction('MVN', i, [])
        else:
            j = 'This should not happen (cat2)'
        return j

    # Special data instructions and branch and exchange on page A5-159
    @staticmethod
    def _thumb16_decode_cat3(i):
        op = (i & 0x03c0) >> 6
        opcode = [0, op & 0x8, op & 0xc, op & 0xe, op & 0xf]
        opers = None
        if opcode[2] == 0x0:    # ADD (register) on page A7-223
            opname = 'ADD'
        elif opcode[4] == 0x4:  # -
            opname = 'UNPREDICTABLE - ???'
        elif opcode[4] == 0x5 or\
             opcode[3] == 0x6:  # CMP (register) on page A7-263
            opname = 'CMP'
        elif opcode[2] == 0x8:  # MOV (register) on page A7-349
            opname = 'MOV'
        elif opcode[3] == 0xc:  # BX on page A7-250
            opname = 'BX'
        elif opcode[3] == 0xe:  # BLX (register) on page A7-249
            opname = 'BLX'
        else:
            opname = 'This should not happen (cat3)'

        return Instruction(opname, i, [])

    # Load from Literal Pool, see LDR (literal) on page A7-289
    @staticmethod
    def _thumb16_decode_cat4(i):
        pass

    # Load/store single data item on page A5-160
    @staticmethod
    def _thumb16_decode_cat5(i):
        opA = (i & 0xf000) >> 12
        opB = (i & 0x0e00) >> 9

        if opA == 0x5:
            if opB == 0o0:      # STR (register) on page A7-475
                opname = 'STR'
            elif opB == 0o1:    # STRH (register) on page A7-491
                opname = 'STRH'
            elif opB == 0o2:    # STRB (register) on page A7-479
                opname = 'STRB'
            elif opB == 0o3:    # LDRSB (register) on page A7-321
                opname = 'LDRSB'
            elif opB == 0o4:    # LDR (register) on page A7-291
                opname = 'LDR'
            elif opB == 0o5:    # LDRH (register) on page A7-313
                opname = 'LDRH'
            elif opB == 0o6:    # LDRB (register) on page A7-297
                opname = 'LDRB'
            elif opB == 0o7:    # LDRSH (register) on page A7-329
                opname = 'LDRSH'
        else:
            b0 = opB & 0o4
            if opA == 0x6:
                if b0 == 0:     # STR (immediate) on page A7-473
                    opname = 'STR'
                else:           # LDR (immediate) on page A7-287
                    opname = 'LDR'
            elif opA == 0x7:
                if b0 == 0:     # STRB (immediate) on page A7-477
                    opname = 'STRB'
                else:           # LDRB (immediate) on page A7-293
                    opname = 'LDRB'
            elif opA == 0x8:
                if b0 == 0:     # STRH (immediate) on page A7-489
                    opname = 'STRH'
                else:           # LDRH (immediate) on page A7-309
                    opname = 'LDRH'
            elif opA == 0x9:
                if b0 == 0:     # STR (immediate) on page A7-473
                    opname = 'STR'
                else:           # LDR (immediate) on page A7-287
                    opname = 'LDR'
            else:
                opname = 'This should not happen (cat5) opA = %01x, opB = %01x' % (opA, opB)
        return Instruction(opname, i, [])

    # Miscellaneous 16-bit instructions on page A5-161
    @staticmethod
    def _thumb16_decode_cat8(i):
        op = (i & 0x0fe0) >> 5
        opcode = [0, op & 0x80, op & 0xc0, op & 0xe0, op & 0xe8, op & 0xec, op, 0xee, op]
        if opcode[7] == 0x33:   # CPS on page B5-801
            opname = 'CPS'
        elif opcode[5] == 0x00: # ADD (SP plus immediate) on page A7-225
            opname = 'ADD'
        elif opcode[5] == 0x04: # SUB (SP minus immediate) on page A7-499
            opname = 'SUB'
        elif opcode[4] == 0x08: # CBNZ, CBZ on page A7-251
            opname = 'CBNZ or CBZ not parsed yet'
        elif opcode[6] == 0x10: # SXTH on page A7-515
            opname = 'SXTH'
        elif opcode[6] == 0x12: # SXTB on page A7-511
            opname = 'SXTB'
        elif opcode[6] == 0x14: # UXTH on page A7-563
            opname = 'UXTH'
        elif opcode[6] == 0x16: # UXTB on page A7-559
            opname = 'UXTB'
        elif opcode[4] == 0x18: # CBNZ, CBZ on page A7-251
            opname = 'CBNZ, CBZ not parsed yet'
        elif opcode[3] == 0x20: # PUSH on page A7-389
            opname = 'PUSH'
        elif opcode[4] == 0x48: # CBNZ, CBZ on page A7-251
            opname = 'CBNZ, CBZ not parsed yet'
        elif opcode[6] == 0x50: # REV on page A7-402
            opname = 'REV'
        elif opcode[6] == 0x52: # REV16 on page A7-403
            opname = 'REV16'
        elif opcode[6] == 0x56: # REVSH on page A7-404
            opname = 'REVSH'
        elif opcode[4] == 0x38: # CBNZ, CBZ on page A7-251
            opname = 'CBNZ, CBZ not parsed yet'
        elif opcode[3] == 0x60: # POP on page A7-387
            opname = 'POP'
        elif opcode[4] == 0x70: # BKPT on page A7-247
            opname = 'BKPT'
        elif opcode[4] == 0x78: # If-Then, and hints on page A5-162
            opA = (i & 0x00f0) >> 4
            opB = (i & 0x000f)
            if opB != 0:        # IT on page A7-277
                opname = 'IT'
            else:
                if opA == 0x00:     # NOP on page A7-366
                    opname = 'NOP'
                elif opA == 0x01:   # YIELD on page A7-612
                    opname = 'YIELD'
                elif opA == 0x2:    # WFE on page A7-610
                    opname = 'WFE'
                elif opA == 0x03:   # WFI on page A7-611
                    opname = 'WFI'
                elif opA == 0x04:   # SEV on page A7-426
                    opname = 'SEV'
                else:
                    return 'This should not happen (cat8) - ifthenhints'
        else:
            return 'This should not happen (cat8)'
        return Instruction(opname, i, [])

    @staticmethod
    def _thumb16_decode_cat12(i):
        opcode = (i & 0x0f00) >> 12

        if opcode & 0xe != 0xe: # B on page A7-239
            opname = 'B'
        elif opcode == 0xe:     # -
            opname = 'Permanently undefined'
        elif opcode == 0xf:     # SVC on page A7-503
            opname = 'SVC'
        else:
            opname = 'This should not happen (cat12)'
        return Instruction(opname, i, [])

    @staticmethod
    def _thumb16_decode(i):
        masks = [0, i & 0x8000, i & 0xc000, i & 0xe000, i & 0xf000, i & 0xf800, i & 0xfc00]

        # See page 156
        if masks[2] == 0x0000:      # cat1: Shift (immediate), add, subtract, move, and compare
            return ARMv7Parser._thumb16_decode_cat1(i)
        elif masks[6] == 0x4000:    # cat2: Data processing
            return ARMv7Parser._thumb16_decode_cat2(i)
        elif masks[6] == 0x4400:    # cat3: Special data instructions and branch and exchange
            return ARMv7Parser._thumb16_decode_cat3(i)
        elif masks[5] == 0x4800:    # cat4: Load from Literal Pool
            return ARMv7Parser._thumb16_decode_cat4(i)
        elif masks[4] == 0x5000 or\
             masks[3] == 0x6000 or\
             masks[3] == 0x8000:    # cat5: Load/store single data item
            return ARMv7Parser._thumb16_decode_cat5(i)
        elif masks[5] == 0xa000:    # cat6: Generate PC-relative address
            j = 'Generate PC-relative address'
        elif masks[5] == 0xa800:    # cat7: Generate SP-relative address
            j = 'Generate SP-relative address'
        elif masks[4] == 0xb000:    # cat8: Miscellaneous 16-bit instructions
            return ARMv7Parser._thumb16_decode_cat8(i)
        elif masks[5] == 0xc000:    # cat9: Store multiple registers
            j = 'Store multiple registers'
        elif masks[5] == 0xc800:    # cat10: Load multiple registers
            j = 'Load multiple registers'
        elif masks[4] == 0xd000:    # cat11: Conditional branch, and supervisor call
            j = 'Conditional branch, and supervisor call'
        elif masks[5] == 0xe000:    # cat12: Unconditional Branch
            j = 'Unconditional Branch'
        else:
            j = Instruction('UNKNOWN 16 bit', i, [])
            pass
        return j

    @staticmethod
    def from_file(path):
        f = open(path, 'rb')
        q = ARMv7Parser.from_buffer(f.read(1000000))
        #q = ARMv7Parser.from_buffer(f.read())
        f.close()
        return q

    @staticmethod
    def from_buffer(b):
        p.enable()
        binrdr = BinaryReader(b)
        instrs = []
        # Page 152 documentation
        start = time.clock()
        try:
            #while not binrdr.eof():
            while True:
                is32bit =\
                    ((binrdr.data[binrdr.position + 3] & 0xf0) == 0xf0) or\
                    ((binrdr.data[binrdr.position + 3] & 0xf8) == 0xe8)

                j = None

                if is32bit:
                    i = binrdr.get_uint32()
                else:
                    i = binrdr.get_uint16()
                    # A list to save the first i bits of the word, needed to understand the
                    # type of the instruction
                    j = ARMv7Parser._thumb16_decode(i)

                instrs.append(j if j is not None else i)
        except IndexError:
            pass
            #import traceback
            #print(traceback.format_exc())

        p.disable()
        end = time.clock()
        print(end-start)
        return instrs

#cProfile.run('ARMv7Parser.from_file(\'../../test/robbeasm\')')
i = ARMv7Parser.from_file('../../test/robbeasm')
f = open('qcavallomuro', 'w')
f.write('\n'.join([str(q) if type(q) != int else ('%08x' % q if q >= 2**16 else '%04x' % q) for q in i]))
f.close()
import io
s = io.StringIO()
ps = pstats.Stats(p, stream=s).sort_stats('cumulative')
ps.print_stats()
print(s.getvalue())