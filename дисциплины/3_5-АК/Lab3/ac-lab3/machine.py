#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью\
# pylint: disable=missing-class-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис
# pylint: disable=too-many-branches     # мне нравятся такое название:(
# pylint: disable=line-too-long # ну не перенести всю строчку
# pylint: disable=too-many-instance-attributes #у DataPath много регистров

"""Модель процессора, позволяющая выполнить бинарный код программы на языке asm.
"""
import logging
import sys
from collections import deque

from isa import read_code, Instruction, Opcode, WORD_SIZE, print_inst_from_bin


class DataPath:
    IN = 1
    OUT = 2

    memory: list[int]
    inst_point: int
    data_addr: int
    acc: int
    alu_f: [bool, bool]  # alu_f[0] - Z; alu_f[1] - N

    def __init__(self, program: list[int], input_buffer: deque):
        self.memory = program
        self.inst_point = 0
        self.acc = 0
        self.inst_reg = 0
        self.data_addr = 0
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.alu_f = [False, False]
        self.alu_result = 0
        self.a, self.b = 0, 0
        self.input_buffer.extend([0, 0])
        self.memory[1] = input_buffer.popleft()

    def select_inst(self) -> int:
        self.latch_dr_from_ip()
        self.inst_reg = self.memory[self.data_addr]
        self.inc_ip()
        return Instruction.fetch_opcode(self.inst_reg)

    def latch_dr_from_ip(self):
        self.data_addr = self.inst_point

    def latch_dr_from_mem(self):
        self.data_addr = self.memory[self.data_addr]

    def latch_dr_from_arg(self):
        self.data_addr = Instruction.fetch_arg(self.inst_reg)

    def latch_mem_from_acc(self):
        self.memory[self.data_addr] = self.acc
        if self.data_addr == self.OUT:  # Если это на выход, то сразу добавляем символ в наш временный буфер
            self.output_buffer.append(chr(self.acc))

    def latch_acc_from_mem(self):
        self.acc = self.memory[self.data_addr]
        if self.data_addr == self.IN:  # Если выгрузили символ, то сразу закидываем новый из буфера
            assert len(self.input_buffer) > 0, 'Не хватает символов на вход'
            self.memory[1] = self.input_buffer.popleft()

    def latch_acc_from_alu(self):
        self.acc = self.alu_result

    def latch_acc_from_arg(self):
        self.acc = Instruction.fetch_arg(self.inst_reg)

    def latch_a_alu_from_acc(self):
        self.a = self.acc

    # def latch_a_alu_from_0(self):
    #     self.a = 0

    def latch_b_alu_from_mem(self):
        self.b = self.memory[self.data_addr]

    # def latch_neg_b_alu_from_mem(self):
    #     self.b = ~self.memory[self.data_addr]

    def latch_b_alu_from_arg(self):
        self.b = Instruction.fetch_arg(self.inst_reg)

    # def latch_neg_b_alu_from_arg(self):
    #     self.b = ~Instruction.fetch_arg(self.inst_reg)

    NEG_MASK = 1 << (WORD_SIZE - 1)

    def calc(self, opc: Opcode):
        match opc:
            case Opcode.ADD:
                self.alu_result = self.a + self.b
            case Opcode.SUB:
                self.alu_result = self.a - self.b
            case Opcode.CMP:
                self.alu_result = self.a - self.b
            case Opcode.AND:
                self.alu_result = self.a & self.b
            case Opcode.OR:
                self.alu_result = self.a | self.b
            case Opcode.DIV:
                self.alu_result = self.a // self.b
            case Opcode.MOD:
                self.alu_result = self.a % self.b
            case _:
                assert False, f'Ошибка, команда {opc.name} попала в ALU инструкция {self.inst_reg:0b}'
        self.alu_result = int(self.alu_result)
        self.alu_f[0] = self.alu_result == 0
        self.alu_f[1] = (self.alu_result & self.NEG_MASK) != 0

    def latch_ip_from_arg(self):
        self.inst_point = Instruction.fetch_arg(self.inst_reg)

    def latch_ip_from_mem(self):
        self.inst_point = self.memory[self.data_addr]

    def inc_ip(self):
        self.inst_point += 1


class ControlUnit:

    def __init__(self, data_path: DataPath):
        self.data_path = data_path
        self.tick = 0
        self.inst_count = 0
        self.new_tick()

    def get_tick(self):
        return self.tick

    def new_tick(self):
        state = f"{{TICK: {self.tick}" \
                f" IP: {self.data_path.inst_point}" \
                f" DA: {self.data_path.data_addr}}}" \
                f" IR: {hex(self.data_path.inst_reg)}" \
                f" ACC: {self.data_path.acc}"

        alu = f"ALU [a:{self.data_path.a} b:{self.data_path.b} => {self.data_path.alu_result}]" \
              f" FLAGS: [Z:{int(self.data_path.alu_f[0])} N:{int(self.data_path.alu_f[1])}]"
        action = f" Action: {print_inst_from_bin(self.data_path.inst_reg)}"
        s = f'{state} {alu} {action}'
        logging.debug("%s", s)
        self.tick += 1

    def decode_and_execute_inst(self):
        opc = Opcode(self.data_path.select_inst())
        self.new_tick()

        if opc == Opcode.NOP:
            return
        if opc == Opcode.HLT:
            raise StopIteration

        form = Instruction.fetch_addressing(self.data_path.inst_reg)
        if opc in [Opcode.JMP, Opcode.JE, Opcode.JNE, Opcode.JL, Opcode.JNL]:
            if any([
                opc == Opcode.JMP,
                opc == Opcode.JE and self.data_path.alu_f[0],
                opc == Opcode.JNE and not self.data_path.alu_f[0],
                opc == Opcode.JL and self.data_path.alu_f[1],
                opc == Opcode.JNL and not self.data_path.alu_f[1]
            ]):
                if form == 1:
                    self.data_path.latch_dr_from_arg()
                    self.new_tick()
                    self.data_path.latch_dr_from_mem()
                    self.new_tick()
                    self.data_path.latch_ip_from_mem()
                else:
                    self.data_path.latch_ip_from_arg()
                self.new_tick()
            return
        if form < 2:
            self.data_path.latch_dr_from_arg()
            self.new_tick()
            if form == 1:
                self.data_path.latch_dr_from_mem()
                self.new_tick()

        if opc == Opcode.LD:
            if form == 2:
                self.data_path.latch_acc_from_arg()
            else:
                self.data_path.latch_acc_from_mem()

        if opc == Opcode.ST:
            assert form < 2, 'У команды ST не может быть прямая ввод'
            self.data_path.latch_mem_from_acc()

        if 4 <= opc <= 10:
            self.data_path.latch_a_alu_from_acc()
            if form == 2:
                self.data_path.latch_b_alu_from_arg()
            else:
                self.data_path.latch_b_alu_from_mem()
            self.data_path.calc(opc)
            if opc != Opcode.CMP:
                self.data_path.latch_acc_from_alu()

        self.new_tick()


def print_memory(memory: list[int]):
    answer = ''
    for i in memory:
        answer += print_inst_from_bin(i) + '\n'
    return answer


def simulation(code: list, input_ch: deque, limit=10000):

    logging.info("{ INPUT MESSAGE } [ `%s` ]", "".join([chr(ch) for ch in input_ch]))
    logging.info("{ INPUT TOKENS  } [ %s ]", ",".join([str(item) for item in input_ch]))

    inst_count = 0
    data_path = DataPath(code, input_ch)
    control_unit = ControlUnit(data_path)

    try:
        while inst_count < limit:
            control_unit.decode_and_execute_inst()
            inst_count += 1
        print(f"Количество операций оказалось больше лимита = {limit}")
    except StopIteration:
        pass
    finally:
        logging.debug("%s", f"Memory after stop\n{print_memory(code)}")

    return data_path.output_buffer, inst_count, control_unit.get_tick()


def main(args):
    assert 1 <= len(args) <= 3, "Wrong arguments: machine.py <code.bin> <input_file>? <output_file>?"
    code_file, input_file, output_file = args[0], None if len(args) < 2 else args[1], None if len(args) < 3 else args[2]

    code = read_code(code_file)
    input_chars = deque()
    if input_file is not None:
        with open(input_file, encoding="utf-8") as file:
            input_text = file.read()
            for char in input_text:
                input_chars.append(ord(char))
    output, inst_counter, ticks = simulation(code, input_chars, limit=10000)

    print(''.join(output))
    print("instr_counter: ", inst_counter, "ticks:", ticks)
    if output_file is not None:
        with open(output_file, 'w', encoding="utf-8") as file:
            file.write(''.join(output))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
