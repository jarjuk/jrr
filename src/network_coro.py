"""Monitor network connectivity
"""

import asyncio
import logging
from typing import Callable, Any

from .utils import check_inet
from .publish_subsrcibe import Hub, Subscription
from .constants import TOPICS
from .messages import message_network_status, is_message_type


logger = logging.getLogger(__name__)


def _default_action(msg: Any, hub: Hub) -> bool:
    if is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
        return False
    return True


# publish network status on status change
prev_status = None


def reset_network_status():
    global prev_status
    prev_status = None


async def network_coro(name: str,
                       hub: Hub,
                       topic: str,
                       action: Callable = _default_action,
                       status_topic: str = TOPICS.CONTROL,
                       ) -> str:
    """Accept control messages from topic, on time-out check for
    network status.

    Messages processed: EXIT

    :topic: receive control messages

    :status_topic: report MsgNetworkStatus message

    """

    # await asyncio.sleep(random.random() * 5)
    logger.info("network_coro: '%s' has decided to subscribe now!", name)

    global prev_status
    
    with Subscription(hub=hub, topic=topic) as queue:
        goon = True
        while goon:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=5)
                goon = action(msg, hub=hub)
            except asyncio.TimeoutError:
                network_status = await check_inet()
                if network_status != prev_status:
                    logger.info("network_status: %s, prev_status=%s",
                                network_status, prev_status)
                    hub.publish(
                        topic=status_topic,
                        message=message_network_status(status=network_status)
                    )
                    prev_status = network_status

    exit_msg = f"network_coro '{name}' is shutting down"
    logger.info("%s msg: %s", name, exit_msg)
    return exit_msg
