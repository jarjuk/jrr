"""Debugger for reading and sending messages over publish/subscriber.

"""
from typing import Dict
import re
import logging
import os

from ..publish_subsrcibe import Hub
from ..exceptions import JrrUserInput
from ..constants import TOPICS, APP_CONTEXT
from ..messages import (message_create, message_keys, message_types)
from ..config import app_config

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Debugger state


# Key in 'debugger_context'

CONTEXT_VARIABLES = "variables"
CONTEXT_MESSAGE_TYPE = "message_type"

# Context maintained/used in *_action -methods
debugger_context: Dict | None = {}


# ------------------------------------------------------------------
# Debugger presentation

DBG_LINE_START = ":DEBUG:"


def _debugger_content(hub=None):
    if 'topic' in debugger_context:
        print(f"topic         : {debugger_context['topic']}")
    if CONTEXT_MESSAGE_TYPE in debugger_context:
        print(f"message type  : {debugger_context[CONTEXT_MESSAGE_TYPE]}")
    if CONTEXT_VARIABLES in debugger_context and debugger_context[CONTEXT_VARIABLES] is not None:
        print("variables     :" +
              f"{','.join([k + '=' + v for k, v in debugger_context[CONTEXT_VARIABLES].items()])}")


def _debugger_error(error):
    print(error)


def _debugger_prompt():
    prompt = f"""{DBG_LINE_START} (Help: ?) >>"""
    print(prompt)


def _debugger_line(line):
    prompt = f"""{DBG_LINE_START} {line}"""
    print(prompt, end='')

# ------------------------------------------------------------------
# Debugger actions


def action_help(command, hub):
    help_text = f"""
    Commands:

    ?                 : help (this text)
    ??                : list message types
    # line            : Comment line (ignored)
    #! line           : Comment line (output stdout)
    ?MESSAGE          : document MESSAKE (KEYS)
    !TOPIC            : send MESSAGE with KEY VALUES to TOPIC
    MESSAGE|          : init MESSAGE -type
    KEY = VALUE       : set KEY = VALUE in MESSAGE
    .                 : clear context
    @FILE             : read commands from a file

    Examples:

    Shutdown -message to {TOPICS.CONTROL} -topic
    {TOPICS.CONTROL_MESSAGES.REBOOT}| !{TOPICS.CONTROL}

    Init and show messages to {TOPICS.SCREEN} -topic
    {TOPICS.SCREEN_MESSAGES.INIT}| !{TOPICS.SCREEN}
    {TOPICS.SCREEN_MESSAGES.UPDATE}| !{TOPICS.SCREEN}

    """
    print(help_text)
    return True


def action_help_message_types(command, hub):
    help_text = f"""

    Valid topics and listeners
    {TOPICS.CONTROL:<20} - econtroller
    {TOPICS.SCREEN:<20} - display manager
    {TOPICS.STREAMER:<20} - streamter manager
    {TOPICS.DEFAULT:<20} - NOT user

    Valid message types:  {','.join(message_types())}

    """
    print(help_text)
    return True


def action_help_message(command, message_type, hub):
    help_text = f"""

    Valid KEYs in {message_type} (set by KEY=VALUE):
    - {','.join(message_keys(message_type))}

    """
    print(help_text)
    return True


def action_variable(command, variable, value, hub=None):
    logger.debug("action_variable: variable: %s, value: %s", variable, value)

    # Init debugger_context - if needed
    if (CONTEXT_VARIABLES not in debugger_context or
            debugger_context[CONTEXT_VARIABLES] is None):
        debugger_context[CONTEXT_VARIABLES] = {}

    # Boolean value False strin to emtpy empty value
    if value in ["False", "FALSE", ]:
        value = False
    debugger_context[CONTEXT_VARIABLES][variable] = value
    return True


def action_message_type(command, message_type, hub=None):
    """Set message type and init variables hash."""
    logger.debug("action_message_type: message_type: %s", message_type)
    debugger_context[CONTEXT_MESSAGE_TYPE] = message_type
    debugger_context[CONTEXT_VARIABLES] = None
    return True


def action_clear(command=None, hub=None):
    """Clear debugger context."""
    global debugger_context
    debugger_context = {}
    return True


def action_comment_ignore(command=None, ignored=None, hub=None):
    """Comment ignored."""
    return True


def action_comment_output(command=None, line=None, hub=None):
    """Comment ignored."""
    _debugger_line(line)
    return True


def action_file(command, file_name, hub=None):
    """Process line by line commands from 'file_name'."""
    logger.debug("action_file:file: %s", file_name)

    file_path = os.path.join(app_config.debug_dir, file_name)

    try:
        with open(file_path, 'r') as file:
            # Read each line in the file
            for line in file:
                # logger.debug("line: %s", line)
                # Print each line
                goon = process_cmd(line=line, hub=hub)
                if not goon:
                    break

    except FileNotFoundError as err:
        dir_list = [f for f in os.listdir(
            app_config.debug_dir) if os.path.isfile(
                os.path.join(app_config.debug_dir, f)) and
                    f.endswith(APP_CONTEXT.DEBUG_SUFFIX)]
        # print(error)

        raise JrrUserInput(
            f"No such file '{file_name}'" +
            f" in directory {app_config.debug_dir}" +
            f"\nValid files:\n{','.join(dir_list)}"
        )

    return True


def action_topic(command, topic, hub: Hub = None):
    """Send 'message_type' with 'variables' to 'topic' in
    'debugger_context' -dict."""
    # Error messagage && quit on debugger context validation error
    if CONTEXT_MESSAGE_TYPE not in debugger_context:
        _debugger_error(
            "No message: use MESSAGE| -command to  set message_type")
        return

    logger.debug(f"action_topic: send message to {topic=},  " +
                 f"{debugger_context[CONTEXT_MESSAGE_TYPE]=} " +
                 f" {debugger_context[CONTEXT_VARIABLES]=}")

    # Construct message from 'debugger_context'

    try:
        message_object = message_create(
            debugger_context[CONTEXT_VARIABLES],
            debugger_context[CONTEXT_MESSAGE_TYPE])
    except KeyError as e:
        # User may enter invalid message_type
        action_clear()
        raise JrrUserInput(f"Invalid message type: '{e}'")

    # Publish message on topic
    logger.info("action_topic: publish topic='%s' message_object: '%s'",
                topic, message_object)
    hub.publish(topic=topic, message=message_object)

    # Mesage sent = debugger_context consumer --> clear
    action_clear()

    return True


# ------------------------------------------------------------------
# Parser


class CMDS:
    CMD_HELP = "help"
    CMD_HELP_HELP = "helphelp"
    CMD_HELP_MESSAGE = "help_message"
    CMD_TOPIC_PUBLISH = "publish"
    CMD_MESSAGE_TYPE = "msg_type"
    CMD_VARIABLE_VALUE = "variable"
    CMD_FILE = "file"
    CMD_CLEAR = "clear"
    CMD_COMMENT = "comment"
    CMD_COMMENT_OUTPUT = "comment!"


command_parser = {
    CMDS.CMD_HELP_MESSAGE:  r"^ *(?P<command>\?)(?P<message_type>[\w_]+)(?P<rest>.*)",
    CMDS.CMD_HELP_HELP:  r"^ *(?P<command>\?\?)(?P<rest>.*)",
    CMDS.CMD_HELP:  r"^ *(?P<command>\?)(?P<rest>.*)",
    CMDS.CMD_TOPIC_PUBLISH:  r"^ *(?P<command>\!)(?P<topic>[^ :]+)(?P<rest>.*)",
    CMDS.CMD_MESSAGE_TYPE:  r"^ *(?P<message_type>[\w_][\w_\d]+)(?P<command>\|)(?P<rest>.*)",
    CMDS.CMD_VARIABLE_VALUE:  r"^ *(?P<variable>[\w_][\w_\d]+)(?P<command>=)(?P<value>[^ ]*)(?P<rest>.*)",
    CMDS.CMD_CLEAR:  r"^ *(?P<command>\.)(?P<rest>.*)",
    CMDS.CMD_FILE:  r"^ *(?P<command>@)(?P<file_name>[\w_][\w_\./\d]+)(?P<rest>.*)",
    CMDS.CMD_COMMENT:  r"^ *(?P<command># )(?P<ignored>.*)(?P<rest>.*)",
    CMDS.CMD_COMMENT_OUTPUT:  r"^ *(?P<command>#!)(?P<line>.*)(?P<rest>.*)",
}


command_dispatcher = {
    CMDS.CMD_HELP:  action_help,
    CMDS.CMD_HELP_HELP:  action_help_message_types,
    CMDS.CMD_HELP_MESSAGE:  action_help_message,
    CMDS.CMD_TOPIC_PUBLISH:  action_topic,
    CMDS.CMD_MESSAGE_TYPE:  action_message_type,
    CMDS.CMD_VARIABLE_VALUE: action_variable,
    CMDS.CMD_CLEAR:  action_clear,
    CMDS.CMD_FILE:  action_file,
    CMDS.CMD_COMMENT:  action_comment_ignore,
    CMDS.CMD_COMMENT_OUTPUT:  action_comment_output,

}


# # Jump table for actions in process_cmd
# cmd_actions = {
#     CMDS.CMD_HELP: action_help
# }


def process_cmd(
        line: str,
        hub: Hub = None,
        actions: Dict = command_dispatcher):
    """Parse 'line' and invoke debugger actions. """
    while len(line) > 0:

        valid_command = False

        # Try to
        for k, rexp in command_parser.items():
            # print(f"{k=}, {rexp=}")
            match = re.search(rexp, line)
            if match is not None:
                valid_command = True
                # logger.debug(f"Matched {k=}, {match.groupdict()=}")
                # Command found : dispatch action
                args = match.groupdict()
                args.pop("rest", None)
                args['hub'] = hub
                # logger.debug("k: %s, args: %s", k, args)
                actions[k](**args)
                # Command found: advance to command = 'rest'
                line = match.group('rest')
                # Advance to
                break

        #
        if not valid_command:
            raise JrrUserInput(f"Non valid command: '{line}'")
    return True


def stdin_debugger(msg: str, hub: Hub):
    """
    Debugger

    Details
    ----
    Expect this method to passed to 'stdin_coro' to implement debugger.


    Parameters
    ----


    Return
    -----

    """
    goon = True
    try:
        goon = process_cmd(line=msg, hub=hub)
    except JrrUserInput as err:
        logger.warning(f"Error {err}")
        _debugger_error(err)

    if goon:
        _debugger_content()
        _debugger_prompt()

    return goon
