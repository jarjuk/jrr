"""Manage ffmpeg streamer."""

from typing import cast, Tuple
import asyncio
import logging
import os
import signal


from .constants import (TOPICS, APP_CONTEXT)
from .publish_subsrcibe import Hub, Subscription
from .messages import (MsgStreamerStart, is_message_type, message_create)
from .helpers import cancel_and_wait

# ------------------------------------------------------------------
# Module state

logger = logging.getLogger(__name__)

# Stremer task managing os-process 'streamer_proc'
runner_task: asyncio.Task | None = None

# Os-process streaming audio - running within 'runner_task'
streamer_proc: asyncio.subprocess.Process | None = None

# ------------------------------------------------------------------
# Module actions managing asyncio task and os-process


# async def _streamer_runner_debug(url: str):
#     while True:
#         print(f"runner here {url}")
#         await asyncio.sleep(4)


async def _streamer_stop(name: str):
    """Stops streamer created in _streamer_run.

    Can be called even if no stream running.

    :name: name to coro where called from 
    """
    logger.debug("_streamer_stop starting")
    global streamer_proc

    if streamer_proc is not None:
        logger.info(
            "Stopping streamer streamer proc %s (and its childs)", streamer_proc)

        # runner_proc.send_signal(signal.SIGTERM)
        # https://stackoverflow.com/questions/32222681/how-to-kill-a-process-group-using-python-subprocess
        # get process group and kill processes
        try:

            logger.debug("Locate process group for pid %s", streamer_proc.pid)
            pgrp = os.getpgid(streamer_proc.pid)
            logger.debug("Find process group pgrp: %s", pgrp)
            os.killpg(pgrp, signal.SIGTERM)

        except ProcessLookupError as e:
            logging.warning(
                f"Error '{e}' in 'os.getpgid(streamer_proc.pid)' {streamer_proc} ")

        # propably 'streamer_proc' already terminated?
        try:
            logger.debug(
                "_streamer_stop: before streamer_proc.terminate() streamer_proc='%s'",
                streamer_proc)
            streamer_proc.terminate()
        except ProcessLookupError as e:
            logging.warning(
                f"Error '{e}' in 'streamer_proc.terminate)' {streamer_proc} ")
        finally:
            streamer_proc = None

        # logger.debug(
        #     "Entering await runner_proc.communicate: %s", streamer_proc)
        # await streamer_proc.communicate()
        # logger.debug(
        #     "Returned await runner_proc.communicate: %s", streamer_proc)

    # Cancel runner task (this may be gone already -> try)
    global runner_task
    try:
        if runner_task is not None:
            logger.info(
                "%s: cancellling runner_task: %s", name, runner_task)
            await cancel_and_wait(
                runner_task, msg=f"cancel_and_wait 'runner_task' in streamer_coro {name}")
            logger.debug( "Return from cancel_and_wait")
        else:
            logger.warning(
                "No task to cancel - nothing done")
    except UnboundLocalError as e:
        logger.warning(f"Excpetion '{e}' when accessing 'runner_task'")
    finally:
        runner_task = None


async def _streamer_run(url: str):
    """
    Start sub-process and wait for its returns.

    Details
    ----
    Ref: https://superfastpython.com/asyncio-subprocess/#Create_Process_with_create_subprocess_shell

    Launches shell script 'APP_CONTEXT.STREAMER_SCRIPT'

    Updates globals 'runner_task' and 'runner_proc'.

    Parameters
    ----
    :url: to stream

    Return
    -----
    """


    global streamer_proc
    params = [
        APP_CONTEXT.STREAMER_SCRIPT,
        "--mono",
        "--file", url,
        "--gain", "1",
        "play",
    ]
    # runner_proc = await asyncio.create_subprocess_shell(
    #     script)
    logger.info("create_subprocess: param='%s'", ' '.join([ str(p) for p in params]))
    streamer_proc = await asyncio.create_subprocess_exec(
        *params,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # https://stackoverflow.com/questions/32222681/how-to-kill-a-process-group-using-python-subprocess
        preexec_fn=os.setsid
    )
    # streamer_proc = await asyncio.create_subprocess_exec(
    #     APP_CONTEXT.STREAMER_SCRIPT,
    #     "--mono",
    #     "--file", url,
    #     "--gain", "1",
    #     cmd,
    #     stdout=asyncio.subprocess.PIPE,
    #     stderr=asyncio.subprocess.PIPE,
    #     # https://stackoverflow.com/questions/32222681/how-to-kill-a-process-group-using-python-subprocess
    #     preexec_fn=os.setsid
    # )
    logger.info(
        "_streamer_runner: call 'await streamer_proc.wait', streamer_proc: %s", streamer_proc)
    await streamer_proc.wait()
    # stdout, stderr = await runner_proc.communicate()
    # logger.info("_streamer_runner  communicate return runner_proc: %s  %s %s",
    #             runner_proc, stdout, stderr)
    # await runner_proc.wait()
    istat = streamer_proc.returncode
    logger.info(
        "_streamer_runner:  url: %s, streamer_proc.returncode: %s", url, istat)
    return istat


def is_streaming(name: str) -> Tuple[str, bool]:
    """Return streaming status"""
    running = False
    if runner_task is None:
        status_string = f"{name} - not started"
    else:
        if (not runner_task.cancelled() and
            not runner_task.cancelling() and
                not runner_task.done()):
            running = True
        status_string = (f"{name} - started:" +
                         f" cancelled?={runner_task.cancelled()}" +
                         f" cancelling?={runner_task.cancelling()}" +
                         f" done?={runner_task.done()}")
    logger.debug(
        "streamer %s: - stream runner status= %s -> running=%s",
        name, status_string, running)

    return status_string, running


# ------------------------------------------------------------------
# Corourintine listening on topic

async def streamer_coro(
        name: str,
        hub: Hub,
        topic: str,
):
    """
    Listen on 'topic' and manage os-process audio streaming.

    Details
    ----
    Accepts messages:
    - STREAM_START
    - STREAM_STOP
    - STATUS_QUERY : -> publish on TOPICS.CONTROL
    - EXIT

    Parameters
    ----
    :name: just a string to identify coro

    :hub: publish/subscribe patter data manager

    :topic: for receiving messages

    Return
    -----

    String informing on exit

    """
    logger.info("streamer_coro '%s' has decided to subscribe now!", name)
    global runner_task

    with Subscription(hub, topic=topic) as queue:
        msg = ""
        while msg not in [TOPICS.COMMON_MESSAGES.EXIT]:
            msg = await queue.get()

            logger.debug("streamer_coro: %s got msg: '%s'", name, msg)

            if is_message_type(msg, TOPICS.STREAMER_MESSAGES.START):
                # Maybe stop previous stream
                _, running = is_streaming(name=name)
                await _streamer_stop(name=name)

                if running:
                    # short sleep befero starting new stream
                    await asyncio.sleep(2)

                # START - streaming
                msg_start = cast(MsgStreamerStart, msg)
                logger.info(
                    "streamer_coro: start streaming from url '%s'", msg_start.url)
                runner_task = asyncio.create_task(
                    _streamer_run(url=msg_start.url))

            elif is_message_type(msg, TOPICS.STREAMER_MESSAGES.STATUS_QUERY):
                # STATUS_QUERY
                status_string, running = is_streaming(name=name)
                status_reply = message_create(
                    d={"status_str": status_string,
                       "running": running,
                       },
                    message_type=TOPICS.CONTROL_MESSAGES.STREAMER_STATUS_REPLY
                )
                hub.publish(topic=TOPICS.CONTROL, message=status_reply)

            elif is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
                # EXIT - rememeber to stop child processes!
                await _streamer_stop(name=name)
                break
            elif is_message_type(msg, TOPICS.STREAMER_MESSAGES.STOP):
                # STOP
                logger.info("streamer_coro: %s message stop on msg: '%s'",
                            name, msg)
                # Rememeber to stop child processes!
                await _streamer_stop(name=name)
                logger.debug("await _streamer_stop - done")
                # Send signal to the running process
            else:
                logger.warning("%s: unknown message '%s':%s",
                               name, msg, type(msg))

    exit_msg = f"streamer_coro '{name}' is exiting on '{msg=}'"
    logger.info("'%s' exit_msg: '%s'", name, exit_msg)
    return exit_msg
