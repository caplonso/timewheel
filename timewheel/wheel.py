import logging
import asyncio
from typing import List
from datetime import datetime

from timewheel.schedule import Schedule

SLEEP_TIME = 1


class TimeWheel:

    def __init__(self, schedules: List[Schedule]):
        self.logger = logging.getLogger("timewheel")
        self.schedules = schedules
        self.running = True

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
                for schedule in self.schedules:
                    if not schedule.running:
                        asyncio.create_task(schedule.run())
            await asyncio.sleep(SLEEP_TIME)
            timer += SLEEP_TIME
        self.logger.warning("Finished the timewheel loop!")

    async def kill_jobs(self):
        """
            When the application receives a system signal to terminate
            invokes the finish methods for all schedules in order to
            wait them finish the jobs if there are any running.
        """

        self.logger.warning("Received system signal to finish!")
        for schedule in self.schedules:
            self.logger.debug(f"Waiting for the schedule {schedule.name} to finish...")
            await schedule.finish()
        self.running = False
