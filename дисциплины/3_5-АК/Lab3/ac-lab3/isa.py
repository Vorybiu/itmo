# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long # ну не перенести всю строчку

from collections import namedtuple
from enum import Enum

ARG_SIZE = 26
ADDR_SIZE = 2
OPCODE_SIZE = 4
WORD_SIZE = ARG_SIZE + ADDR_SIZE + OPCODE_SIZE

arg_offs = 0
addr_offs = ARG_SIZE
op_offs = ARG_SIZE + ADDR_SIZE

arg_m = 0b0000_00_11111111111111111111111111
addr_m = 0b0000_11_00000000000000000000000000
op_m = 0b1111_00_00000000000000000000000000


class FormatAddr(int, Enum):
    DIRECT = 0
    INDIRECT = 1
    IMMEDIATE = 2


class Opcode(int, Enum):
    NOP = 0
    HLT = 1
    LD = 2
    ST = 3
    ADD = 4
    SUB = 5
    AND = 6
    OR = 7
    DIV = 8
    MOD = 9
    CMP = 10
    JE = 11  # Z = 1
    JNE = 12  # Z = 0
    JL = 13  # N = 1
    JNL = 14  # N = 0
    JMP = 15


# opcodes_by_number = dict((opcode.value, opcode) for opcode in Opcode)
opcodes_by_name = dict((opcode.name, opcode) for opcode in Opcode)


class Instruction:
    @staticmethod
    def encode(opcode: int, addr: int, arg: int) -> int:
        instr = 0
        instr += (arg & arg_m)
        instr += (addr << addr_offs) & addr_m
        instr += (opcode << op_offs) & op_m
        return instr

    @staticmethod
    def fetch_opcode(instr: int) -> int:
        return (instr & op_m) >> op_offs

    @staticmethod
    def fetch_addressing(instr: int) -> int:
        return (instr & addr_m) >> addr_offs

    @staticmethod
    def fetch_arg(instr: int) -> int:
        return instr & arg_m


def inst_encode(inst):
    bin_inst = bytearray()
    opcode = inst["opcode"].value if inst["opcode"] else 0
    addr = inst["format"].value if not (inst["opcode"] is None) and inst["format"] else 0
    arg = inst['arg'] if not (inst["format"] is None) else 0
    int_inst = Instruction.encode(opcode, addr, arg)
    mask = 0b11111111_00000000_00000000_00000000
    for i in range(4):
        bin_inst.append((int_inst & mask) >> (8 * (3 - i)))
        mask = mask >> 8
    return bin_inst


def print_inst_from_bin(inst: int):
    opc = Opcode(Instruction.fetch_opcode(inst))
    if opc is Opcode.HLT:
        return f'{opc.name}'
    form = Instruction.fetch_addressing(inst)
    arg = Instruction.fetch_arg(inst)
    return f'{opc.name} {["", "$", "#"][form]}{arg} '


def get_opcodes_by_name(text):
    return opcodes_by_name[text]


class Term(namedtuple('Term', 'line pos symbol')):
    """Описание выражения из исходного текста программы"""


def write_mnem_file(filename: str, program: list):
    text = ''
    for i in program:
        text += f'{i["opcode"].name if i["opcode"] else " ":^4} ' \
                f'{"" if i["format"] is None else ["", "$", "#"][i["format"].value] + str(i["arg"])}\n'
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def write_bin_file(filename: str, program: list):
    code = bytearray()

    for inst in program:
        code.extend(inst_encode(inst))
    with open(filename, "wb") as file:
        file.write(code)

    return len(code)


def read_code(filename: str) -> list:
    memory = []
    with open(filename, "rb") as file:
        while bytes4 := file.read(4):
            memory.append(int.from_bytes(bytes4, 'big'))
    return memory
