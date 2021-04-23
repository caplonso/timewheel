## Introduction

This is an asynchronous job scheduler with crontab syntax.

## How to use

Here is a basic example

```python
# Should run as-is
import time
import asyncio
from typing import Any
from functools import partial

from timewheel import TimeWheel
from timewheel.schedule import Schedule


async def my_job():
    print("hello from job!")
    await asyncio.sleep(3)


async def my_another_job(some_value: Any):
    print(f"Hey! This is my some_value {some_value}")
    await asyncio.sleep(1)


def my_sync_job():
    print("Hello from the sync job")
    time.sleep(10)


async def main():
    timewheel = TimeWheel(schedules=[
        # Runs every 29 minutes
        Schedule("my-schedule", "*/29 * * * *", my_job),
        # Runs every 5th, 10th and 20th minute on wednesday
        Schedule("another-schedule", "5,10,20 * * * 2", my_job),
        # Runs every 10 minutes
        Schedule("my-schedyle-with-fixed-param", "*/10 * * * *", partial(my_another_job,
                                                                         {"some_value": "My value"})),
        # Runs every minute
        Schedule("a-sync-job", "* * * * *", my_sync_job)])
    await timewheel.run()


asyncio.get_event_loop().run_until_complete(main())

```