"""Misc helps functions
"""

import asyncio
import logging
logger = logging.getLogger(__name__)

# cancel task and wait for it to complete


async def cancel_and_wait(task, msg=None):
    """cancel task and wait for it to complete."""
    # https://superfastpython.com/asyncio-cancel-task-and-wait/
    logger.debug("cancel task msg: '%s'", msg)
    task.cancel(msg)
    try:
        # wait for the task to be done
        logger.debug("await for cancel start: msg='%s'", msg)
        await task
        logger.debug("await for cancel done: %s", msg)
    except asyncio.CancelledError as e:
        # the target was canceled, perhaps log
        logger.warning(
            f"cancel_and_wait: CancelledError='%s', msg='%s'", e, msg)
    except OSError as e:
        logger.warning(f"cancel_and_wait: OSError: '%s', msg='%s", e, msg)
