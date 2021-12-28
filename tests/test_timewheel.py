import asyncio
import logging
from unittest.mock import Mock

import pytest

from timewheel.schedule import Schedule
from timewheel.wheel import TimeWheel


def test_setup_timewheel_with_valid_parameters():
    my_tw = TimeWheel(schedules=[])

    assert isinstance(my_tw, TimeWheel)
    assert my_tw.running is True


@pytest.mark.asyncio
async def test_timewheel_runner(caplog):

    job = Mock(return_value=None)

    my_tw = TimeWheel(schedules=[Schedule(name='my-job',
                                          expression='* * * * *',
                                          timezone='America/Sao_Paulo',
                                          job=job)])

    with caplog.at_level(logging.INFO):
        t = asyncio.create_task(my_tw.run())
        await asyncio.sleep(.1)
        my_tw.running = False
        await asyncio.sleep(1)

        job.assert_called()
        assert "Finished the timewheel loop" in caplog.text
        t.cancel()


