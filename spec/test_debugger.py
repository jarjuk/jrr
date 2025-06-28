import pytest


import src.debug.debugger as debugger
from src.debug.debugger import (CMDS)
from src.publish_subsrcibe import Hub


def test_framework():
    assert 1 == 1


def mock_help(command, hub=None):
    print(f"help:{command}")
    return True


def mock_clear(command, hub=None):
    print(f"mock_clear:{command=}")
    return True


def mock_publish(command, topic, hub=None):
    print(f"moc_publish:{command=}, {topic=}")
    return True


def mock_variable(command, variable, value, hub=None):
    print(f"mock_variable:{command=}, {variable=}, {value=}")
    return True


def mock_message_type(command, message_type, hub=None):
    print(f"mock_message_type:{command=}, {message_type=}")
    return True


mock_actions = {
    CMDS.CMD_HELP: mock_help,
    CMDS.CMD_TOPIC_PUBLISH: mock_publish,
    CMDS.CMD_MESSAGE_TYPE: mock_message_type,
    CMDS.CMD_VARIABLE_VALUE: mock_variable,
    CMDS.CMD_CLEAR: mock_clear,
}

# ------------------------------------------------------------------
# Test constants

# ------------------------------------------------------------------
# Test processing stdininput


def test_command_empty():
    msg = ""
    ret = debugger.process_cmd(line=msg)
    assert ret


def test_command_help_2x():
    msg = "??"
    ret = debugger.process_cmd(line=msg)
    assert ret


def test_command_help(capsys):
    msg = " ?"
    ret = debugger.process_cmd(line=msg, actions=mock_actions)
    assert ret
    captured = capsys.readouterr()
    assert "help:?" in captured.out


def test_command_topic(capsys):
    msg = " !topiikki"
    ret = debugger.process_cmd(line=msg, actions=mock_actions)
    captured = capsys.readouterr()
    assert "moc_publish:command='!', topic='topiikki'" in captured.out


def test_command_msg_type(capsys):
    msg = " msg1|"
    ret = debugger.process_cmd(
        line=msg,
        actions=mock_actions)
    captured = capsys.readouterr()
    assert "message_type:command='|', message_type='msg1'" in captured.out


def test_variable(capsys):
    msg = " v1=abc"
    ret = debugger.process_cmd(
        line=msg,
        actions=mock_actions)
    captured = capsys.readouterr()
    assert "mock_variable:command='=', variable='v1', value='abc'" in captured.out


def test_string(capsys):
    topic = "Otsikko"
    v1 = "variable1"
    value1 = "123"
    msg1 = "msg_name"
    msg = f"  {msg1}| {v1}={value1} !{topic} ."
    ret = debugger.process_cmd(
        line=msg,
        actions=mock_actions)
    captured = capsys.readouterr()
    assert f"mock_variable:command='=', variable='{v1}', value='{value1}'" in captured.out
    assert f"moc_publish:command='!', topic='{topic}'" in captured.out
    assert f"message_type:command='|', message_type='{msg1}'" in captured.out
    assert f"mock_clear:command='.'" in captured.out
