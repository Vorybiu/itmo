# pylint: disable=missing-class-docstring     # чтобы не быть Капитаном Очевидностью
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=line-too-long               # строки с ожидаемым выводом
"""Интеграционные тесты транслятора и машины
"""

import contextlib
import io
import logging
import os
import tempfile

import pytest

import machine
import translator


@pytest.mark.golden_test("golden/*.yml")
def test_whole_by_golden(golden, caplog):
    # Установим уровень отладочного вывода на DEBUG
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source = os.path.join(tmpdirname, "source.asm")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target_txt = os.path.join(tmpdirname, "target.txt")
        target_bin = os.path.join(tmpdirname, "target.bin")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["input"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную
        # stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target_bin, target_txt])
            print("============================================================")
            machine.main([target_bin, input_stream])

        # Выходные данные также считываем в переменные.
        with open(target_bin, "rb") as file:
            binary_code = file.read()

        with open(target_txt, encoding="utf-8") as file:
            struct_code = file.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert binary_code == golden.out["binary_code"]
        assert struct_code == golden.out["struct_code"]
        assert stdout.getvalue() == golden.out["output"]

        assert caplog.text == golden.out["log"]
