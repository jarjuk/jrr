"""Main module parses command line options and dispatched commands.

"""

import argparse
import sys

import logging

from .constants import (CLI)
from .jrr_radio import radio_main
from .jrr_converter import converter_main
from .config import app_config

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Command line arguments

# https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output

class _HelpAction(argparse._HelpAction):
    """Sub parser helps"""

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print(f"Command '{choice}'")
                print(subparser.format_help())

        parser.exit()


def commandLineParser() -> argparse.ArgumentParser:
    """Return command line parser.

    laturi [options] [command]

    Options:

    -v                : versbosity

    Commands:

    kan1              : the simples kan model
    """

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--disable_existing_loggers", help="Default True (=imported loggers disabled)",
                        action="store_false")
    parser.add_argument('--help', action=_HelpAction,
                        help='help for help if you need some help')
    subparsers = parser.add_subparsers(help='Commands', dest="command")

    # --------------------
    # Radio
    radio_parser = subparsers.add_parser(
        CLI.CMD_RADIO, help="Run radio daemon")
    # radio_parser.add_argument(
    #     CLI.OPT_SYSTEM_HALT, action="store_false", default=True,
    #     help="call 'sudo halt' on shutdown knob",
    # )
    radio_parser.add_argument(
        CLI.OPT_CONSOLE_ALL_LINES, action="store_true", default=False,
        help="Output all journalctl lines to console (default no)",
    )

    # --------------------
    # Icon converter

    icon_cnv_parser = subparsers.add_parser(
        CLI.CMD_ICON_CONVERT, help="Convert icons")
    icon_cnv_parser.add_argument(
        CLI.OPT_ICON_SOURCE, type=str, default=CLI.DEFAULT_ICON_SOURCE_DIR,
        help=f"Icon images from  '{CLI.DEFAULT_ICON_SOURCE_DIR}')",
    )
    icon_cnv_parser.add_argument(
        CLI.OPT_ICON_TARGET, type=str, default=CLI.DEFAULT_ICON_DIR,
        help=f"Icon images to '{CLI.DEFAULT_ICON_DIR}')",
    )
    icon_cnv_parser.add_argument(
        CLI.OPT_STREAMING_ICON_WIDTH, type=str, default=CLI.DEFAULT_STREAMING_ICON_WIDTH,
        help=f"Display width '{CLI.DEFAULT_STREAMING_ICON_WIDTH}')",
    )
    icon_cnv_parser.add_argument(
        CLI.OPT_STREAMING_ICON_HEIGHT, type=str, default=CLI.DEFAULT_STREAMING_ICON_HEIGHT,
        help=f"Display height '{CLI.DEFAULT_STREAMING_ICON_HEIGHT}')",
    )
    icon_cnv_parser.add_argument(
        "--yes", "-y", action="store_true", default=False,
        help=f"Override '(default = False')",
    )
    icon_cnv_parser.add_argument(
        "--bw", action="store_true", default=False,
        help=f"Black and white '(default = False = color')",
    )

    return parser


def commandLineArgruments(args):
    """Process command line argurments"""
    parser = commandLineParser()
    parsed_args = parser.parse_args(args)

    # Init singleton config
    app_config.cliArgs = parsed_args

    return parsed_args

# ------------------------------------------------------------------
# main entry


def main(args):
    """Parse command line and dispatch commands."""

    parsed = commandLineArgruments(args)
    # Set output log level
    # logging.basicConfig(level=logging.DEBUG)
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        level=levels[min(parsed.verbose, len(levels)-1)],
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
    )
    logger.info("logging.level: %s", logger.level)

    if parsed.command == CLI.CMD_RADIO:
        radio_main(parsed)
    elif parsed.command == CLI.CMD_ICON_CONVERT:
        # converter_main(parsed)
        converter_main(
            image_dir=parsed.icons_from,
            icon_dir=parsed.icons_to,
            yes=parsed.yes,
            width=parsed.width,
            height=parsed.height,
            bw=parsed.bw
        )


# if __name__ == "__main__":
#     args = sys.argv[1:]
#     main(args)
