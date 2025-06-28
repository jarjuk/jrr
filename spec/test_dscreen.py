from os import name
import pytest
import re

from src import dscreen
from src.constants import KEYBOARD, DSCREEN
from src.messages import MsgDScreen
# from constants import DSCREEN


# ------------------------------------------------------------------
# Constrcut test setup

type_type = dscreen.Type()
type_readnonly = dscreen.ReadonlyType()
type_alphanum = dscreen.AlphanuNumericType()
type_alphanum_10 = dscreen.AlphanuNumericType(max_len=10)
type_alphanum_4 = dscreen.AlphanuNumericType(max_len=4)
type_numeric = dscreen.NumericType(max_len=10)

ft_readonly = dscreen.FieldType("readonly", type_readnonly)
ft_text1 = dscreen.FieldType("text1", type_alphanum_10)
ft_text2 = dscreen.FieldType("text2", type_alphanum_4)
ft_text3 = dscreen.FieldType("text3", type_alphanum)


def test_framework():
    assert 1 == 1


# ------------------------------------------------------------------
#

def test_type_type():
    value = "aaaa"
    input = "1"
    # with pytest.raises(NotImplementedError) as ex:
    #     type_type.validate(value, input)
    stat, msg = type_type.validate(value, input)
    assert stat
    assert msg is None


def test_type_an():
    value = "aaaa"
    input = "1"

    type_sut = type_alphanum

    stat, msg = type_sut.validate(value, input)
    assert stat
    assert msg is None

    stat, msg = type_sut.validate("+"+value, None)
    assert stat
    assert msg is None


def test_type_numeric():
    value = "1234"
    input = "1"

    type_sut = type_numeric

    stat, msg = type_sut.validate(value, "1")
    assert stat
    assert msg is None

    stat, msg = type_sut.validate(value, "12")
    assert stat
    assert msg is None

    stat, msg = type_sut.validate(value, ".12")
    assert stat
    assert msg is None

    stat, msg = type_sut.validate("-"+value, ".12")
    assert stat
    assert msg is None

    stat, msg = type_sut.validate("+"+value, ".12")
    assert stat
    assert msg is None

    stat, msg = type_sut.validate("+"+value, None)
    assert stat
    assert msg is None

    stat, msg = type_sut.validate("+"+value, "a")
    assert not stat
    assert msg.startswith(
        dscreen.DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH[0:10], )

    stat, msg = type_sut.validate(value, "a")
    assert not stat
    assert msg.startswith(
        dscreen.DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH[0:10],)

    stat, msg = type_sut.validate("d"+value, "")
    assert not stat
    assert msg.startswith(
        dscreen.DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH[0:10], )


def test_type_an_fails():
    value = "aaaa"
    input = 1
    stat, msg = type_alphanum.validate(value, input)
    print(f"{msg=}")
    assert not stat
    assert msg.startswith(
        dscreen.DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH[0:10], )


def test_type_an_len():
    value = "123456789"
    input = "1"
    stat, msg = type_alphanum_10.validate(value, input)
    assert stat
    assert msg is None

    input = "12"
    stat, msg = type_alphanum_10.validate(value, input)
    assert not stat
    assert msg.startswith(
        dscreen.DSCREEN.VALIDATION_ERRORS.INPUT_MAX_LEN[0:10], )


# ------------------------------------------------------------------
# FieldValue

def test_field_1():

    # Sigle char
    fv1 = dscreen.FieldValue(type_alphanum, "a")
    assert fv1.strValue == "a"
    fv1.delChar(1)
    assert fv1.strValue == ""

    fv1 = dscreen.FieldValue(type_alphanum, "a")
    assert fv1.strValue == "a"
    fv1.delChar(0)
    assert fv1.strValue == "a"

    fv1 = dscreen.FieldValue(type_alphanum, "a")
    assert fv1.strValue == "a"
    fv1.delChar(2)
    assert fv1.strValue == "a"

    # Two chars
    fv1 = dscreen.FieldValue(type_alphanum, "ab")
    assert fv1.strValue == "ab"
    fv1.delChar(2)
    assert fv1.strValue == "a"

    fv1 = dscreen.FieldValue(type_alphanum, "ab")
    assert fv1.strValue == "ab"
    fv1.delChar(1)
    assert fv1.strValue == "b"

    fv1 = dscreen.FieldValue(type_alphanum, "ab")
    assert fv1.strValue == "ab"
    fv1.delChar(0)
    assert fv1.strValue == "ab"

    fv1 = dscreen.FieldValue(type_alphanum, "ab")
    assert fv1.strValue == "ab"
    fv1.delChar(-1)
    assert fv1.strValue == "ab"

    # Three chars
    fv1 = dscreen.FieldValue(type_alphanum, "abc")
    assert fv1.strValue == "abc"
    fv1.delChar(4)
    assert fv1.strValue == "abc"

    fv1 = dscreen.FieldValue(type_alphanum, "abc")
    assert fv1.strValue == "abc"
    fv1.delChar(3)
    assert fv1.strValue == "ab"

    fv1 = dscreen.FieldValue(type_alphanum, "abc")
    assert fv1.strValue == "abc"
    fv1.delChar(2)
    assert fv1.strValue == "ac"

    fv1 = dscreen.FieldValue(type_alphanum, "abc")
    assert fv1.strValue == "abc"
    fv1.delChar(1)
    assert fv1.strValue == "bc"

    fv1 = dscreen.FieldValue(type_alphanum, "abc")
    assert fv1.strValue == "abc"
    fv1.delChar(0)
    assert fv1.strValue == "abc"


# ------------------------------------------------------------------
# DScreen


def test_dscreen1():
    dscreen_sut = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])

    assert dscreen_sut.fieldCount == 3

    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue is None
    assert dscreen_sut.cursorStrValue == ""
    assert dscreen_sut.cursorFieldPosition == 0

    stat, lastError = dscreen_sut.putInput("a")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "a"
    assert dscreen_sut.cursorFieldPosition == 1

    stat, lastError = dscreen_sut.putInput("b")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "ab"
    assert dscreen_sut.cursorFieldPosition == 2

    stat, lastError = dscreen_sut.putInput("ä")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "abä"
    assert dscreen_sut.cursorFieldPosition == 3

    assert dscreen_sut.cursorFieldValue is not None
    dscreen_sut.close()
    assert dscreen_sut.cursorFieldValue is None


def test_dscreen_default():
    init1 = "init-val1"
    init3 = "init3"
    dscreen_sut = dscreen.DScreen(fieldTypes=[(ft_text1, init1),
                                              ft_text2,
                                              [ft_text3, init3]])

    assert dscreen_sut.fieldCount == 3

    assert dscreen_sut.cursorFieldValue is not None
    assert dscreen_sut.cursorStrValue == init1

    assert dscreen_sut.fieldReference(1).value is None
    assert dscreen_sut.fieldReference(1).strValue == ""

    assert dscreen_sut.fieldReference(2).value == init3


def test_dscreen_readonly():
    dscreen_sut = dscreen.DScreen(fieldTypes=[ft_readonly,
                                              ft_text2])

    assert not type_readnonly.inputAllowed
    assert not ft_readonly.inputAllowed

    assert dscreen_sut.fieldCount == 2
    assert dscreen_sut.cursorFieldName == ft_text2.name


def test_dscreen_tab():
    dscreen_sut = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])

    stat, lastError = dscreen_sut.putInput("a")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "a"
    assert dscreen_sut.cursorFieldPosition == 1

    stat, lastError = dscreen_sut.putInput(KEYBOARD.TAB)
    assert lastError is None
    assert stat
    assert dscreen_sut.cursorFieldName == "text2"
    assert dscreen_sut.cursorFieldValue is None
    assert dscreen_sut.cursorStrValue == ""
    assert dscreen_sut.cursorFieldPosition == 0

    stat, lastError = dscreen_sut.putInput(KEYBOARD.STAB)
    assert lastError is None
    assert stat
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorStrValue == "a"
    assert dscreen_sut.cursorFieldPosition == 1


def test_dscreen_message():
    dscreen_sut = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    assert dscreen_sut.fieldCount == 3

    stat, lastError = dscreen_sut.putInput("a")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "a"
    assert dscreen_sut.cursorFieldPosition == 1

    stat, lastError = dscreen_sut.putInput("x")
    assert stat
    assert lastError is None
    assert dscreen_sut.cursorFieldName == "text1"
    assert dscreen_sut.cursorFieldValue == "ax"
    assert dscreen_sut.cursorFieldPosition == 2

    screen_name = "name3"
    message = dscreen_sut.message(screen_name)
    assert isinstance(message, MsgDScreen)
    assert message.fieldCount == dscreen_sut.fieldCount
    assert message.screen_name == screen_name

    assert message.fields[0].value == "ax"

    for i in range(message.fieldCount):
        assert message.fields[i].name == dscreen_sut.fieldReference(i).name
        assert message.fields[i].value == dscreen_sut.fieldReference(i).value


# ------------------------------------------------------------------
# DApp

def test_dapp1():
    dapp = dscreen.DApp()

    assert dapp.screenCount == 0
    dscreen1 = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    screen1_name = "s1"
    dapp.addScreen(screen1_name, dscreen1)
    assert dapp.screenCount == 1

    dapp.activateScreen(screen1_name)
    assert dapp.currentFieldName == ft_text1.name
    assert dapp.currentStrValue == ""

    stat = dapp.putInput("A")
    assert stat
    assert dapp.currentStrValue == "A"

    stat = dapp.putInput(KEYBOARD.TAB)
    assert stat
    assert dapp.currentFieldName == ft_text2.name
    assert dapp.currentStrValue == ""

    screen_message = dapp.message()
    assert isinstance(screen_message, MsgDScreen)
    assert screen_message.fieldCount == 3


def test_dapp_init_values():
    dapp = dscreen.DApp()

    assert dapp.screenCount == 0
    dscreen1 = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    screen1_name = "s1"
    dapp.addScreen(screen1_name, dscreen1)
    assert dapp.screenCount == 1

    init2 = "init222"
    dapp.activateScreen(screen1_name, [(ft_text2.name, init2)])

    f2 = dscreen1.fieldByName(ft_text2.name)
    assert f2.name == ft_text2.name

    assert dscreen1.fieldReference(1).value == init2


def test_activate():
    dapp = dscreen.DApp()
    assert dapp.screenCount == 0

    # First
    dscreen1 = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    screen1_name = "s1"
    dapp.addScreen(screen1_name, dscreen1)
    assert dapp.screenCount == 1

    # Second
    dscreen2 = dscreen.DScreen(fieldTypes=[(ft_text2, "hei"), ft_text3])
    screen2_name = "s2"
    dapp.addScreen(screen2_name, dscreen2)
    assert dapp.screenCount == 2

    assert dapp.currentScreenName is None
    dapp.activateScreen(screen1_name)
    assert dapp.currentScreenName == screen1_name
    assert dapp.currentFieldName == ft_text1.name
    assert dapp.currentStrValue == ""
    stat = dapp.putInput("a")
    assert stat
    assert dapp.currentStrValue == "a"

    # Switch screen - assume cursort on first field, init with hei
    assert dapp.currentFieldName == ft_text1.name
    dapp.activateScreen(screen2_name)
    assert dapp.currentScreenName == screen2_name

    assert dapp.currentFieldName == ft_text2.name
    assert dapp.currentStrValue == "hei"
    stat = dapp.putInput(">")
    print(f"{dapp.lastError=}")

    assert stat
    assert dapp.currentStrValue == ">hei"


def test_dapp_no_screen_active():
    dapp = dscreen.DApp()
    assert dapp.screenCount == 0

    # Not screen - none active
    stat = dapp.putInput("a")
    assert not stat
    assert dapp.lastError.startswith(
        DSCREEN.MISC_ERRORS.NO_SCREEN_ACTIVE[0:10])

    msg = dapp.message()
    assert msg is None

    dscreen1 = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    screen1_name = "s1"
    dapp.addScreen(screen1_name, dscreen1)
    assert dapp.screenCount == 1

    stat = dapp.putInput("a")
    assert not stat
    assert dapp.lastError.startswith(
        DSCREEN.MISC_ERRORS.NO_SCREEN_ACTIVE[0:10])

    msg = dapp.message()
    assert msg is None

    # After activation putInput and message succeed
    dapp.activateScreen(screen1_name)
    stat = dapp.putInput("a")
    assert stat
    assert dapp.lastError is None

    msg = dapp.message()
    assert msg is not None

    # After de-activation putInput and message fail
    dapp.deActivateScreen()
    stat = dapp.putInput("a")
    assert not stat

    msg = dapp.message()
    assert msg is None


def test_dapp_no_such_screen():
    dapp = dscreen.DApp()
    assert dapp.screenCount == 0
    dscreen1 = dscreen.DScreen(fieldTypes=[ft_text1, ft_text2, ft_text3])
    screen1_name = "s1"
    dapp.addScreen(screen1_name, dscreen1)
    assert dapp.screenCount == 1

    stat = dapp.activateScreen(screen1_name)
    assert stat

    stat = dapp.activateScreen("noscush")
    assert not stat
    assert dapp.lastError is not None
    assert dapp.lastError.startswith(
        dscreen.DSCREEN.MISC_ERRORS.UNKNOWN_SCREEN[0:10])
