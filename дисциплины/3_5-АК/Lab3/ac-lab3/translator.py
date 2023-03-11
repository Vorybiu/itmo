#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис
# pylint: disable=too-many-branches     # что тут поделать, это импорт
# pylint: disable=line-too-long # ну не перенести всю строчку
"""
Транслятор ассемблера в машинный код
"""
import re
import sys
from collections import deque

from isa import Opcode, FormatAddr, get_opcodes_by_name, write_mnem_file, write_bin_file


def parse(text):
    data_name = {'IN': 0, 'OUT': 1}
    data = ['0', '0']
    code_label = {}
    code = deque()
    isData, isText = False, False
    text = re.sub(
        r"'.*'",
        lambda match: f'{",".join(map(lambda char: str(ord(char)), match.group()[1:-1]))}',
        text
    )
    for line_num, line in enumerate(text.split('\n'), 1):
        i = line.find(';')
        if i != -1:
            line = line[:i]
        tokens = line.split()

        # Пропуск пустых строк
        if len(tokens) == 0:
            continue

        # assert len(tokens) < 3, f'В строке {line_num} слов больше 2'

        if 'section' == tokens[0] and 'text:' == tokens[1]:
            isData, isText = False, True
            continue
        if 'section' == tokens[0] and 'data:' == tokens[1]:
            isData, isText = True, False
            continue
        assert isData or isText, f'Строка {line_num} вне какой-либо секции'

        if isData:
            label = tokens[0].replace(':', '')
            assert not(label in code_label or label in data_name),\
                f'Строка {line_num}: название метки {label} уже занято'
            data_name[label] = len(data)
            for i in tokens[1:]:
                sep_token = i.split(',')
                for j in sep_token:
                    if '' != j:
                        data.append(j)
        if isText:
            assert len(tokens) <= 2, f'Строка {line_num}: много аргументов у команды'
            if ':' == tokens[0][-1]:
                label = tokens[0][:-1]
                assert not (label in code_label or label in data_name),\
                    f'Строка {line_num}: название метки {label} уже занято'
                code_label[label] = len(code)
                continue
            code.append({'opcode': tokens[0].upper(), 'arg': '0', 'format': None})
            if len(tokens) == 2:
                first_ch = tokens[1][0]
                if '$' == first_ch:
                    code[-1]['format'] = FormatAddr.INDIRECT
                    code[-1]['arg'] = tokens[1][1:]
                elif '#' == first_ch:
                    code[-1]['format'] = FormatAddr.IMMEDIATE
                    code[-1]['arg'] = tokens[1][1:]
                else:
                    code[-1]['format'] = FormatAddr.DIRECT
                    code[-1]['arg'] = tokens[1]
    return data, data_name, code, code_label


def translate(text) -> list[dict]:
    data, data_name, inst, inst_label = parse(text)
    label = data_name.copy()
    for key, i in inst_label.items():
        label[key] = len(data) + i
    assert '_start' in label, 'Не найдена label _start'
    code = [{'opcode': Opcode.JMP, 'arg': label['_start'] + 1, 'format': FormatAddr.DIRECT}]
    for i in data:
        if i in label:
            code.append({'opcode': None, 'arg': label[i] + 1, 'format': FormatAddr.IMMEDIATE})
        else:
            try:
                code.append({'opcode': None, 'arg': int(i), 'format': FormatAddr.IMMEDIATE})
            except ValueError:
                assert False, f'{i} не является числом или меткой (из секции data)'
    for i in inst:
        if i['arg'] in label:
            code.append({'opcode': get_opcodes_by_name(i['opcode']), 'arg': label[i["arg"]] + 1,
                         'format': i['format']})
        else:
            try:
                code.append({'opcode': get_opcodes_by_name(i['opcode']), 'arg': int(i['arg']),
                             'format': i['format']})
            except ValueError:
                assert False, f'{i["arg"]} не является числом или меткой (из команды {i})'
            except KeyError:
                assert False, f'Не найдена команда {i["opcode"]} в команде {i}.'

    return code


def main(args):
    assert len(args) == 3, "Необходимо ввести translator.py <code.asm> <output.bin> <output.txt>"
    source, target, target_mnem = args

    with open(source, "rt", encoding="utf-8") as f:
        source = f.read()

    program = translate(source)
    write_mnem_file(target_mnem, program)
    count_byte = write_bin_file(target, program)
    print(f'Размер бинарного файла: {count_byte} байта, что равняется {count_byte//4} ячейкам')

    for i in program:
        print(f'{i["opcode"].name if i["opcode"] else "":^4}"'
              f'{"" if i["format"] is None else ["", "$", "#"][i["format"].value] + str(i["arg"])} ')


if __name__ == '__main__':
    main(sys.argv[1:])
