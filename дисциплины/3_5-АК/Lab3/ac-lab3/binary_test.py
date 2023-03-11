#!/usr/bin/python3
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name
# pylint: disable=too-many-branches
# pylint: disable=missing-module-docstring

import unittest

from isa import Instruction, Opcode, inst_encode, FormatAddr


class TestBin(unittest.TestCase):

    def test_register_instruction(self):
        init = [
            {"opcode": Opcode.ADD, "arg": 19, "format": FormatAddr.DIRECT},
            {"opcode": Opcode.SUB, "arg": 20, "format": FormatAddr.INDIRECT},
            {"opcode": Opcode.AND, "arg": 21, "format": FormatAddr.DIRECT},
            {"opcode": Opcode.DIV, "arg": 22, "format": FormatAddr.INDIRECT},
            {"opcode": Opcode.MOD, "arg": 32, "format": FormatAddr.DIRECT},

        ]

        for instr in init:
            encoded = inst_encode(instr)
            instr32 = int.from_bytes(encoded, "big")
            print(instr32)
            opcode = Opcode(Instruction.fetch_opcode(instr32))

            arg = Instruction.fetch_arg(instr32)
            f = Instruction.fetch_addressing(instr32)

            self.assertEqual(opcode, instr["opcode"])
            self.assertEqual(arg, instr["arg"])
            self.assertEqual(f, instr["format"])

    def test_addr(self):
        init = [
            {"opcode": Opcode.LD, "arg": 14, "format": FormatAddr.DIRECT},
            {"opcode": Opcode.LD, "arg": 14, "format": FormatAddr.INDIRECT},
            {"opcode": Opcode.LD, "arg": 14, "format": FormatAddr.IMMEDIATE},

        ]
        for instr in init:
            encoded = inst_encode(instr)
            instr32 = int.from_bytes(encoded, "big")
            print(instr32)
            opcode = Opcode(Instruction.fetch_opcode(instr32))

            arg = Instruction.fetch_arg(instr32)
            f = Instruction.fetch_addressing(instr32)

            self.assertEqual(opcode, instr["opcode"])
            self.assertEqual(arg, instr["arg"])
            self.assertEqual(f, instr["format"])
