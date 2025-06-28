import asyncio
import time
import sys

import pytest


def test_framework():
    assert 1 == 1

# ------------------------------------------------------------------
# Context checks

def test_python_version_creater_than():
    assert sys.version_info[0] == 3
    assert sys.version_info[1] >= 9

    

# ------------------------------------------------------------------

def test_yield():
    async def gen():
        try:
            while True:
                await asyncio.sleep(0.1)
                value = yield 'hello'
                print("got:", value)
        except ZeroDivisionError:
            await asyncio.sleep(0.2)
            yield 'world'

    async def main():
        now = time.time()
        g = gen()
        v = await g.asend(None)
        assert v == "hello"
        v = await g.asend('something')
        assert v == "hello"

        b = await g.asend(None)
        assert b == "hello"
        c = await g.asend(None)
        assert c == "hello"

        v = await g.athrow(ZeroDivisionError)
        assert v == "world"

    asyncio.run(main())



