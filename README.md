## Introduction

This is an asynchronous job scheduler with crontab syntax.

## How to use

Here is a basic example:

```python
# Should run as-is
import asyncio
from typing import Any
from datetime import datetime

from timewheel import TimeWheel
from timewheel.schedule import Schedule


async def my_job():
    print("hello from job!")
    await asyncio.sleep(3)


async def my_another_job(some_value: Any):
    print(f"Hey! This is my some_value {some_value}")
    await asyncio.sleep(1)

    
def my_special_job():
    print("Doing the special job!!")
    
async def main():
    timewheel = TimeWheel(schedules=[
        # Runs every 29 minutes using America/Sao_Paulo
        # as base
        Schedule(name="my-schedule", 
                 expression="*/29 * * * *",
                 timezone="America/Sao_Paulo",
                 job=my_job),
        # Runs every 5th, 10th and 20th minute on wednesday
        # using America/Los_Angeles tz as base
        Schedule(name="another-schedule", 
                 expression="5,10,20 * * * 2", 
                 timezone="America/Los_Angeles",
                 job=my_another_job),
        Schedule(name="special-job",
                 expression="* * * * *",
                 timezone="America/Sao_Paulo",
                 excluded_dates=[datetime.strptime('2021-12-31', '%Y-%m-%d')],
                 job=my_special_job)
    ])
    await timewheel.run()


asyncio.get_event_loop().run_until_complete(main())
```

The timezone information is based on [IANA](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).