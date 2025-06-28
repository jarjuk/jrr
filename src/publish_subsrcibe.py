"""Publish subscribe
"""

# Forward declaration
import asyncio

# flake8 noqa: F811
# pylint disable=function-redefined
# pylint: disable=invalid-name
# mypy disable-error-code="no-redef"


# Subscription = typing.NewType("Subscription", Base)


class Hub():
    """Maintain list of topic subscribers and provide services for
    publish-subsribe pattern.

    """

    def __init__(self):
        self.topics = {}

    def _getTopicQ(self, topic: str):
        """Return set of subscribers for 'topic'."""
        if topic not in self.topics:
            self.topics[topic] = set()
        return self.topics[topic]

    def publish(self, topic, message):
        """Publish 'message' on 'topic'."""
        subscriptions = self._getTopicQ(topic)
        for queue in subscriptions:
            queue.put_nowait(message)

    def subscribe(self, topic, subscriber):
        """Add 'subscriber' on 'topic'."""
        self._getTopicQ(topic).add(subscriber.queue)

    def unsubscribe(self, topic, subscriber):
        """Remove 'subscriber' from 'topic'."""
        self._getTopicQ(topic).remove(subscriber)


class Subscription():
    """Context class for use in with -statement"""

    def __init__(self, hub: Hub, topic: str):
        self.hub = hub
        self.topic = topic
        self.queue: asyncio.Queue = asyncio.Queue()

    def __enter__(self):
        # hub.subscriptions.add(self.queue)
        self.hub.subscribe(topic=self.topic, subscriber=self)
        return self.queue

    def __exit__(self, tyyppi, value, traceback):
        self.hub.unsubscribe(self.topic, self.queue)
