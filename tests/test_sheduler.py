import logging

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from timewheel.schedule import Schedule, EXPRESSION_VALIDATOR_REGEXP


# Instance creation tests

def test_create_schedule_running_every_minute():
    s = Schedule(name='some-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    assert s.name == 'some-schedule'
    assert s.schedule_table.minutes
    assert s.schedule_table.hours
    assert s.schedule_table.days
    assert s.schedule_table.months
    assert s.schedule_table.weekdays


def test_create_schedule_with_nth_expression():
    s = Schedule(name='some-schedule',
                 expression='*/2 * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    assert isinstance(s.schedule_table.minutes, list)
    assert len(s.schedule_table.minutes) == 30


def test_create_schedule_with_multi_tokens():
    s = Schedule(name='some-schedule',
                 expression='1,2,3,4,5 * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    assert isinstance(s.schedule_table.minutes, list)
    assert len(s.schedule_table.minutes) == 5


def test_create_schedule_with_nth_token_having_value_over_the_max():
    expression = '*/100 * * * *'
    with pytest.raises(ValueError) as error:
        Schedule(name='some-schedule',
                 expression=expression,
                 timezone='America/Sao_Paulo',
                 job=print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: The nth token value 100 is higher then the " \
           f"max value (59) for the field type." == str(error.value)


def test_create_schedule_with_token_having_value_over_the_max():
    expression = '100 * * * *'
    with pytest.raises(ValueError) as error:
        Schedule(name='some-schedule',
                 expression=expression,
                 timezone='America/Sao_Paulo',
                 job=print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: The token value 100 is higher then the " \
           f"max value (59) for the field type." == str(error.value)


def test_create_schedule_with_multi_token_and_all():
    expression = '1,2,3,4,* * * * *'

    with pytest.raises(ValueError) as error:
        Schedule(name='some-schedule',
                 expression=expression,
                 timezone='America/Sao_Paulo',
                 job=print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: Invalid syntax for the token 1,2,3,4,*" == str(error.value)


def test_create_schedule_with_invalid_expression():

    with pytest.raises(ValueError) as error:
        Schedule(name='some-schedule',
                 expression='* * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    assert f"The expression must match the pattern '{EXPRESSION_VALIDATOR_REGEXP.pattern}'" == str(error.value)


# Schedule validation

def test_should_run_true():
    current_time = datetime.strptime('2021-10-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)
    assert s.schedule_table.should_run(current_time)


def test_should_run_false():
    current_time = datetime.strptime('2021-10-01 00:05:00', '%Y-%m-%d %H:%M:%S')
    s = Schedule(name='my-schedule',
                 expression='*/7 * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    assert not s.schedule_table.should_run(current_time)


@pytest.mark.asyncio
async def test_finish_scheduler():
    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)

    await s.finish()
    assert s.stop_signal_received
    assert not s.running


@pytest.mark.asyncio
async def test_run_with_stop_signal_received():
    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=print)
    s.stop_signal_received = True

    r = await s.run()
    assert not r


@pytest.mark.asyncio
async def test_run_with_excluded_date_set(caplog):

    excluded_dates = [
        datetime.today().date()
    ]

    job = Mock()

    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=job,
                 excluded_dates=excluded_dates)
    with caplog.at_level(logging.INFO):
        await s.run()

        job.assert_not_called()
        assert "has been added to the exclusion list" in caplog.text


@pytest.mark.asyncio
async def test_run_sync_job_successfully(caplog):

    job = Mock()

    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=job)
    with caplog.at_level(logging.INFO):
        await s.run()

        job.assert_called_once()
        assert "Running the schedule with the job" in caplog.text


@pytest.mark.asyncio
async def test_run_sync_job_ensure_running_once_per_minute(caplog):
    job = Mock()

    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=job)
    with caplog.at_level(logging.INFO):
        for _ in range(10):
            await s.run()

        job.assert_called_once()
        assert "Running the schedule with the job" in caplog.text


@pytest.mark.asyncio
async def test_run_coro_job_successfully(caplog):
    job = AsyncMock()

    s = Schedule(name='my-schedule',
                 expression='* * * * *',
                 timezone='America/Sao_Paulo',
                 job=job)

    with caplog.at_level(logging.INFO):
        await s.run()

        job.assert_called_once()
        assert "Running the schedule with the job" in caplog.text
