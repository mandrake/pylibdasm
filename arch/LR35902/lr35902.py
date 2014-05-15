__author__ = 'mandrake'

### LR35902 is a CPU used in Nintendo™ GameBoy™ and Nintendo™ GameBoy Color™

from util.instruction import Instruction

'''class Z80instruction(object):
    def __init__(self, addr, instr, ops):
        self.addr = addr
        self.instr = instr
        self.ops = ops

    def __str__(self):
        #print self.instr, self.ops
        return "%08X: %s %s" % (self.addr, self.instr, ', '.join(map(str, self.ops)))'''


class LR35902(object):

    @staticmethod
    def from_file(path):
        f = open(path, 'rb')
        q = f.read()
        f.close()
        return LR35902.from_list(f)

    @staticmethod
    def from_list(data):
        ret = []
        idx = 0
        while idx < len(data):
            tidx = idx
            key = ''
            ops = 'opcodes-old.json'

            while (not ops.has_key(key)) and tidx < idx + 2 and tidx < len(data):
                key += "%02X" % data[tidx]
                tidx += 1

            if tidx == idx + 2 or (tidx == len(data) and not ops.has_key(key)):
                #print "Warning: this should never happen (%08X: %02Xh)" % (idx, data[idx])
                #ret.append(Z80instruction(base+idx, 'nop', ["%02Xh" % data[idx]]))
                ret.append(Instruction('nop', ))
                idx += 1
            else:
                instr = ops[key]['op']
                operands = list(ops[key]['operands'])
                params = []

                if ops[key].has_key('follows'):
                    for follow in ops[key]['follows']:
                        if follow == 'byte':
                            params.append(data[tidx])
                            tidx += 1
                        elif follow == 'word':
                            params.append(data[tidx] + data[tidx + 1] * 256)
                            tidx += 2
                        else:
                            raise Exception("Fuuuuuuuu")

                j = 0
                for i in range(0, len(operands)):
                    if operands[i] == 'byte':
                        operands[i] = ('i8', params[j])
                    elif operands[i] == 'word':
                        operands[i] = ('i16', params[j])
                    elif operands[i] == '(byte)':
                        operands[i] = ('mem8', params[j])
                    elif operands[i] == '(word)':
                        operands[i] = ('mem16', params[j])
                    else:
                        j -= 1
                    j += 1

                ret.append(Z80instruction(base+idx, instr, operands))
                found = True
                idx = tidx

        return ret

    @staticmethod
    def decodeStreamFile(data, path, base):
        f = open(path, 'w')
        r = LR35902.decodeStream(data, base)
        for i in r:
            f.write(str(i) + "\n")