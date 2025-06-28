import pytest
import os

from src import kb


def test_framework():
    assert 1 == 1

# ------------------------------------------------------------------
# edit_buffer -


def test_backspace_end():
    buf, pos = kb.edit_buffer("123", key=kb.BS)
    print(f"{buf=}, {pos=}")
    assert buf == "12"
    assert pos == 2

    buf, pos = kb.edit_buffer("12", key=kb.BS)
    print(f"{buf=}, {pos=}")
    assert buf == "1"
    assert pos == 1

    buf, pos = kb.edit_buffer("1", key=kb.BS)
    print(f"{buf=}, {pos=}")
    assert buf == ""
    assert pos == 0


def test_backspace_1():
    buf, pos = kb.edit_buffer("123", key=kb.BS, pos=3)
    print(f"{buf=}, {pos=}")
    assert buf == "12"
    assert pos == 2


def test_backspace_1_input_error():
    buf, pos = kb.edit_buffer("123", key=kb.BS, pos=3, )
    print(f"{buf=}, {pos=}")
    assert buf == "12"
    assert pos == 2

    buf, pos = kb.edit_buffer("123", key=kb.BS, pos=300, )
    print(f"{buf=}, {pos=}")
    assert buf == "12"
    assert pos == 2


def test_backspace_2_middle():
    buf, pos = kb.edit_buffer("123", key=kb.BS, pos=2, )
    print(f"{buf=}, {pos=}")
    assert buf == "13"
    assert pos == 1


def test_backspace_3_first():
    buf, pos = kb.edit_buffer("123", key=kb.BS, pos=1, )
    print(f"{buf=}, {pos=}")
    assert buf == "23"
    assert pos == 0


def test_backspace_seq():
    buf = "123"
    pos = None
    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == "12"

    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == "1"

    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == ""

    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == ""


def test_backspace_seq2():
    buf = "123"
    pos = len(buf)-1
    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == "13"

    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == "3"
    assert pos == 0

    buf, pos = kb.edit_buffer(buf, key=kb.BS, pos=pos)
    assert buf == "3"
    assert pos == 0


# ------------------------------------------------------------------
# format_buffer


def test_format_buffer_short():
    buf = "123"
    formatted_buf = kb.split_buffer(buf)
    assert buf == formatted_buf


def test_format_buffer_long():
    buf = "1234567890123456789"
    formatted_buf = kb.split_buffer(buf)
    assert buf == formatted_buf

    buf = "12345678901234567890"
    formatted_buf = kb.split_buffer(buf)
    assert buf == formatted_buf

    buf = "123456789012345678901"
    buf_expect = "12345678901234567890\n1"
    formatted_buf = kb.split_buffer(buf)
    assert buf_expect == formatted_buf


def test_format_multi_line():
    buf = "123"
    formatted_buf = kb.split_buffer(buf, line_limit=3)
    assert buf == formatted_buf

    buf = "1234"
    buf_expect = "123\n4"
    formatted_buf = kb.split_buffer(buf, line_limit=3)
    assert buf_expect == formatted_buf

    buf = "12345"
    buf_expect = "123\n45"
    formatted_buf = kb.split_buffer(buf, line_limit=3)
    assert buf_expect == formatted_buf

    buf = "123456"
    buf_expect = "123\n456"
    formatted_buf = kb.split_buffer(buf, line_limit=3)
    assert buf_expect == formatted_buf

    buf = "1234567"
    buf_expect = "123\n456\n7"
    formatted_buf = kb.split_buffer(buf, line_limit=3)
    assert buf_expect == formatted_buf
