import logging
import signal
import asyncio
from typing import List
from datetime import datetime
from functools import partial

from timewheel.schedule import Schedule

SIGNALS = ['SIGTERM', 'SIGINT']
SLEEP_TIME = 1

logger = logging.getLogger("timewheel")


class TimeWheel:

    def __init__(self, schedules: List[Schedule]):
        self.schedules = schedules
        self.running = True

        # Setup de signal handler method
        for sig in SIGNALS:
            asyncio.get_running_loop().add_signal_handler(getattr(signal, sig),
                                                          partial(asyncio.create_task,
                                                                  self.kill_jobs()))

    async def run(self):
        """
        Starts the scheduler loop

        :return:
        """

        timer = 0
        while self.running:
            # Only check the schedule every 60 seconds
            if timer % 60 == 0:
                timer = 0
                now = datetime.now()
                for schedule in self.schedules:
                    if not schedule.running:
                        asyncio.create_task(schedule.run(now))
            await asyncio.sleep(SLEEP_TIME)
            timer += SLEEP_TIME
        logger.warning("Finished the timewheel loop!")

    async def kill_jobs(self):
        """
            When the application receives a system signal to terminate
            invokes the finish methods for all schedules in order to
            wait them finish the jobs if there are any running.
        """

        logger.warning("Received system signal to finish!")
        for schedule in self.schedules:
            logger.debug(f"Waiting for the schedule {schedule.name} to finish...")
            await schedule.finish()
        self.running = False
