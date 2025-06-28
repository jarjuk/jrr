"""dscreen - data content manager used by controller


# from __future__ import annotations"""

from .messages import MsgDScreen, message_dscreen
from .constants import DSCREEN, KEYBOARD

from typing import Any, List, Tuple, Dict
from dataclasses import dataclass
from functools import partial

import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers


def is_number(s):
    try:
        complex(s)  # for int, long, float and complex
    except ValueError:
        return False

    return True


class Keyboard:
    """Keyboard realated helpers collected togther"""

    def is_control(dataIn: Any) -> bool:
        """Check if it 'dataIn' control entry.

        Data entries are length 1 all other are control entries

        :return:
        """
        if len(dataIn) != 1:
            return True

        if dataIn in [KEYBOARD.TAB]:
            return True

        # Normal
        return False


# ------------------------------------------------------------------
# Class defintision


@dataclass
class Type:
    """Base class for type hierarchy. Implements 'validate' method to
    validate, which derived classes should extend to build up
    validation hierarchy..

    """

    def validate(self, value, dataIn) -> Tuple[bool, str | None]:
        """Validate the result of adding 'dataIn' to
        'value'. Everything goes.

        """
        return True, None
        raise NotImplementedError

    @property
    def inputAllowed(self):
        return True


@dataclass
class ReadonlyType(Type):
    """No -dataentry allowed"""

    def validate(self, value, dataIn):
        return False, "Read only field"

    @property
    def inputAllowed(self):
        return False


@dataclass
class BasicType(Type):
    """Abstract basetype guarding max-length"""

    max_len: int = None

    def validate(self, value, dataIn) -> Tuple[bool, str | None]:
        """
        Validation checks:
        - MUST not exceed max_len

        """
        # Base class checks priotized
        stat, msg = super().validate(value, dataIn)
        if not stat:
            return stat, msg

        value = "" if value is None else value
        dataIn = "" if dataIn is None else dataIn
        ctx = {
            "value": value,
            "dataIn": dataIn,
        }
        if self.max_len is not None and len(value + dataIn) > self.max_len:
            return False, DSCREEN.VALIDATION_ERRORS.INPUT_MAX_LEN.format(
                **ctx, expect=self.max_len
            )
        return True, None


@dataclass
class NumericType(BasicType):
    def validate(self, value, dataIn) -> Tuple[bool, str | None]:
        """
        Validation checks:
        - MUST be numeric

        """
        value = "" if value is None else value
        dataIn = "" if dataIn is None else dataIn

        # Base class checks priotized
        stat, msg = super().validate(value, dataIn)
        if not stat:
            return stat, msg

        # MUST BE numeric
        value = value + dataIn
        ctx = {
            "value": value,
            "dataIn": dataIn,
        }

        if not is_number(value):
            return False, DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH.format(
                **ctx, expect="numeric"
            )

        return True, None


@dataclass
class AlphanuNumericType(BasicType):
    def validate(self, value, dataIn) -> Tuple[bool, str | None]:
        """Validate the result of adding 'dataIn' to 'value'.

        Validation checks:
        - DataIn MUST be type(str)

        """
        value = "" if value is None else value
        dataIn = "" if dataIn is None else dataIn

        # Validate base class
        stat, msg = super().validate(value, dataIn)
        if not stat:
            return stat, msg

        ctx = {
            "value": value,
            "dataIn": dataIn,
        }

        # MUST be string
        if not isinstance(dataIn, str):
            return False, DSCREEN.VALIDATION_ERRORS.INPUT_TYPE_MISMATCH.format(
                **ctx, expect=str
            )
        return True, None


@dataclass
class FieldType:
    """Name and type of a screen field"""

    name: str  # name of field
    fieldType: Type  # type of field for validation

    def validate(self, value, dataIn) -> Tuple[bool, str | None]:
        """Delegate validation to 'fieldType'."""
        return self.fieldType.validate(value, dataIn)

    @property
    def inputAllowed(self):
        return self.fieldType.inputAllowed


@dataclass
class FieldValue:
    """Value of field of 'FieldType'."""

    fieldType: FieldType  # name and type
    value: Any  # field content
    fieldStatus: DSCREEN.FIELD_STATUS  # Status OK/ERR of field

    def __init__(
        self,
        fieldType: FieldType,
        value: Any = None,
        fieldStatus=DSCREEN.FIELD_STATUS.OK,
    ):
        self.fieldType = fieldType
        self.value = value
        self.fieldStatus = fieldStatus

    # ------------------------------------------------------------------
    # Properties & getters & setters

    @property
    def strValue(self) -> str:
        return "" if self.value is None else self.value

    @property
    def name(self) -> str:
        return self.fieldType.name

    @property
    def inputAllowed(self):
        return self.fieldType.inputAllowed

    # ------------------------------------------------------------------
    # Services

    def delChar(self, fieldPos: int):
        self.value = (
            self.value[0: 0 if fieldPos <= 0 else fieldPos - 1]
            + self.value[0 if fieldPos <= 0 else fieldPos:]
        )

    def putInput(self, dataIn: Any, fieldPos: int) -> int:
        """Put 'dataIn' to 'value[fieldPos]'

        :return: position where data was put into
        """
        if self.value is None:
            self.value = ""

        self.value = self.value[0:fieldPos] + dataIn + self.value[fieldPos:]
        return fieldPos + 1

    def validate(self, dataIn) -> Tuple[bool, str | None]:
        """Validate 'dataIn' for my 'value' -content."""
        return self.fieldType.validate(self.value, dataIn)


@dataclass
class Cursor:
    """Position (field, fieldPos) for data entry."""

    screen: "DScreen"  # screen where cursor is

    currentField: FieldValue  # current/active field
    fieldIdx: int  # count fieldValue in 'screen'
    fieldPos: int  # position within fieldValue

    def __init__(self, screen: "DScreen"):
        self.screen = screen
        # Set cursor to first 'inputAllowed' field
        self.fieldIdx = screen.tabFieldIdx(idx=-1, direction=+1)
        self.fieldPos = 0

        # Refernce to field in screen
        self.currentField = self.screen.fieldReference(idx=self.fieldIdx)

    # ------------------------------------------------------------------
    # Cursor services (validate, control, putInput)

    def validate(self, dataIn) -> Tuple[bool, str | None]:
        """Validate 'dataIn' for 'fieldValue' content."""
        return self.currentField.validate(dataIn)

    def control(self, dataIn) -> Tuple[bool, str | None]:
        """Process control input (i.e. if is_control('dataIn') == True ).

        Control characters intrepreted:
        - left: increment fieldPos
        - right: decrement fieldPos
        - tab: set currentField to next field

        """

        def move_left() -> Tuple[bool, str | None]:
            self.fieldPos = self.fieldPos - 1 if self.fieldPos > 0 else 0
            return True, None

        def move_right() -> Tuple[bool, str | None]:
            self.fieldPos = (
                self.fieldPos + 1
                if self.fieldPos < len(self.currentField.value)
                else len(self.currentField.value)
            )
            return True, None

        def backspace() -> Tuple[bool, str | None]:
            self.currentField.delChar(self.fieldPos)
            self.fieldPos = 0 if self.fieldPos <= 0 else self.fieldPos - 1
            return True, None

        # Previous/Next field
        def tab_field(direction: int) -> Tuple[bool, str | None]:
            self.fieldIdx = self.screen.tabFieldIdx(
                self.fieldIdx, direction=direction)
            self.currentField = self.screen.fieldReference(self.fieldIdx)
            self.fieldPos = len(self.currentField.strValue)
            return True, None

        actions = {
            KEYBOARD.LEFT: move_left,
            KEYBOARD.RIGHT: move_right,
            KEYBOARD.BACKSPACE: backspace,
            KEYBOARD.TAB: partial(tab_field, direction=1),
            KEYBOARD.STAB: partial(tab_field, direction=-1),
        }
        if dataIn in actions:
            stat, msg = actions[dataIn]()
        else:
            return False, DSCREEN.VALIDATION_ERRORS.UNKNOWN_INPUT.format(
                dataIn=dataIn,
                value=self.currentField.value,
                expect=[a for a in actions],
            )

        return stat, msg

    def putInput(self, dataIn):
        self.fieldPos = self.currentField.putInput(dataIn, self.fieldPos)


class DScreen:
    """Data content of 'fieldValues' and processing state 'cursor',
    'lastError' and facade to dscreen -module.

    :fieldValues: data content

    :cursor: data entry pointer

    """

    # Data content
    fieldValues: list[FieldValue]  # screen content

    # processing state
    cursor: Cursor  # data entry

    def __init__(self, fieldTypes: List[FieldType | Tuple[FieldType, str]]):
        """Construct list of empty 'FieldValue[FieldType]'
        -objects. Set 'cursor' pointing to the first 'inputAllowed'
        FielValue.

        :fieldTypes: List of 'FieldType' -objects or
        'FieldType'/string pairs (to set default values)

        """
        self.fieldValues = []
        for fieldType_or_tuple in fieldTypes:
            # Init with default value?
            if isinstance(fieldType_or_tuple, FieldType):
                fieldType = fieldType_or_tuple
                defaultValue = None
            else:
                fieldType = fieldType_or_tuple[0]
                defaultValue = fieldType_or_tuple[1]

            fieldValue = FieldValue(fieldType=fieldType, value=defaultValue)
            self.fieldValues.append(fieldValue)

        self.cursor = Cursor(screen=self)

    # ------------------------------------------------------------------
    # propeties
    @property
    def fieldCount(self):
        return len(self.fieldValues)

    @property
    def cursorFieldName(self) -> str:
        return self.cursor.currentField.fieldType.name

    @property
    def cursorFieldValue(self) -> str | None:
        return self.cursor.currentField.value

    @property
    def cursorStrValue(self) -> str:
        return self.cursor.currentField.strValue

    @property
    def cursorFieldPosition(self) -> int:
        return self.cursor.fieldPos

    def fieldReference(self, idx: int = 0) -> FieldValue:
        """Return refence to 'FieldValue' in 'DScreen'.

        :idx: index in list 'fieldValues' list. Default returs first

        :direction:

        :return: reference to first 'fieldValue' in 'fieldValues'.

        """
        return self.fieldValues[idx]

    def fieldByName(self, name: str) -> FieldValue:
        """Return refence to 'FieldValue' by name.

        :name: field name to locate

        :return: reference to first 'fieldValue' in 'fieldValues'.

        """
        g = (f for f in self.fieldValues if f.name == name)
        return next(g)

    def tabFieldIdx(self, idx: int, direction: int) -> int:
        """Advance 'idx' as an indexer to 'fieldValues' list.

        :direction: -1, +1

        """
        logger.debug("tabFieldIdx: idx='%s', direction='%s'", idx, direction)
        idx = idx + direction

        while True:
            if idx >= len(self.fieldValues):
                idx = 0
            if idx < 0:
                idx = len(self.fieldValues) - 1

            # WARNING: assumes that at least one field is inputAllowed
            if self.fieldValues[idx].inputAllowed:
                break
            else:
                idx = idx + direction
        logger.debug("tabFieldIdx: return idx='%s'", idx)
        return idx

    # ------------------------------------------------------------------
    # facade

    def message(self, screen_name: str):
        """Return message from 'fieldValue' on screen."""
        gen = ((fieldValue.name, fieldValue.value)
               for fieldValue in self.fieldValues)
        msg_dscreen = message_dscreen(screen_name=screen_name, key_values=gen)
        return msg_dscreen

    def putInput(self, dataIn) -> Tuple[bool, str | None]:
        """Put 'input' on screen to a place pointed by 'cursor'.

        Input is validated before being accepted to screen.

        :return: False on error, True when no error

        """

        cursorField = self.cursor.currentField

        if Keyboard.is_control(dataIn=dataIn):
            # control/edit input
            stat, msg = self.cursor.control(dataIn)
            return stat, msg

        # Validate normal input data
        stat, msg = cursorField.validate(dataIn)
        if not stat:
            # Validation error
            return stat, msg

        # Validation passed - add input to field
        self.cursor.putInput(dataIn)
        return True, msg

    def close(self):
        """Set all value fields to None"""
        for fieldValue in self.fieldValues:
            fieldValue.value = None


class DApp:
    """Collection of named dscreen objects, zero or one of the screens
    is current/active

    Current/active screen:
    - data input is dispatched to 'putInput'
    - content is returned in 'message'
    """

    screens: Dict[str, DScreen]  # map name -> Dscreen -instance

    # Current state
    currentScreenName: str  # key to 'screens' -dict
    currentScreen: DScreen  # value in 'screens' -dict
    lastError: str | None  #

    # ------------------------------------------------------------------
    # Constructores

    def __init__(self):
        self.screens = {}
        self.currentScreenName = None
        self.currentScreen = None

    def addScreen(self, name: str, screen: DScreen):
        self.screens[name] = screen

    # ------------------------------------------------------------------
    # properties & setters & getters & delegates
    @property
    def screenCount(self):
        return len(self.screens.keys())

    @property
    def currentFieldName(self):
        return self.currentScreen.cursorFieldName

    @property
    def currentStrValue(self):
        return self.currentScreen.cursorStrValue

    # ------------------------------------------------------------------
    # State change

    def activateScreen(self,
                       name: str,
                       init_values: List[Tuple[str, str | None]] = []) -> bool:
        """Set screen 'name' active and init field values."""
        self.currentScreenName = name
        if self.currentScreenName not in self.screens:
            self.lastError = DSCREEN.MISC_ERRORS.UNKNOWN_SCREEN.format(
                current=self.currentScreenName, screens=list(
                    self.screens.keys())
            )
            return False
        self.currentScreen:DScreen = self.screens[self.currentScreenName]

        for init_value in init_values:
            try:
                fieldValue = self.currentScreen.fieldByName(name=init_value[0])
            except StopIteration as ex:
                msg = f"No such field {init_value[0]} - in {f.name for f in self.currentScreen.fieldValues}"
                logger.error("activateScreen: msg='%s'", msg)
                raise KeyError(msg)
            fieldValue.value = init_value[1]

        return True

    def deActivateScreen(self):
        self.currentScreen = None

    # ------------------------------------------------------------------
    # service facad

    def message(self) -> MsgDScreen | None:
        """Return content in 'currentScreen' in a message.

        :return: MsgDScreen -object
        """
        if self.currentScreen is None:
            self.lastError = DSCREEN.MISC_ERRORS.NO_SCREEN_ACTIVE.format(
                screens=list(self.screens.keys())
            )
            return None

        return self.currentScreen.message(screen_name=self.currentScreenName)

    def putInput(self, dataIn) -> bool:
        """Put 'dataIn' on 'currentScreen'.

        :dataIn: Character input/simple edit actions BS,DEL and cursor
        movemetns LEFT,RIGHT, TAB, STAB.

        Input is validated before being accepted to screen.

        :return: False on error, True when no error. Last error be be
        read from 'lastError' -instance variable.

        """
        if self.currentScreen is None:
            self.lastError = DSCREEN.MISC_ERRORS.NO_SCREEN_ACTIVE.format(
                screens=list(self.screens.keys())
            )
            return False
        stat, self.lastError = self.currentScreen.putInput(dataIn)
        return stat


# ------------------------------------------------------------------
# Application
