import pytest
from datetime import datetime

from timewheel.schedule import Schedule, EXPRESSION_VALIDATOR_REGEXP


# Instance creation tests

def test_create_schedule_running_every_minute():
    s = Schedule('some-schedule', '* * * * *', print)
    assert s.name == 'some-schedule'
    assert s.schedule_table.minutes
    assert s.schedule_table.hours
    assert s.schedule_table.days
    assert s.schedule_table.months
    assert s.schedule_table.weekdays


def test_create_schedule_with_nth_expression():
    s = Schedule('some-schedule', '*/2 * * * *', print)

    assert isinstance(s.schedule_table.minutes, list)
    assert len(s.schedule_table.minutes) == 30


def test_create_schedule_with_multi_tokens():
    s = Schedule('some-schedule', '1,2,3,4,5 * * * *', print)

    assert isinstance(s.schedule_table.minutes, list)
    assert len(s.schedule_table.minutes) == 5


def test_create_schedule_with_nth_token_having_value_over_the_max():
    expression = "*/100 * * * *"
    with pytest.raises(ValueError) as error:
        Schedule('some-schedule', expression, print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: The nth token value 100 is higher then the " \
           f"max value (59) for the field type." == str(error.value)


def test_create_schedule_with_token_having_value_over_the_max():
    expression = "100 * * * *"
    with pytest.raises(ValueError) as error:
        Schedule('some-schedule', expression, print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: The token value 100 is higher then the " \
           f"max value (59) for the field type." == str(error.value)


def test_create_schedule_with_multi_token_and_all():
    expression = "1,2,3,4,* * * * *"

    with pytest.raises(ValueError) as error:
        Schedule('some-schedule', expression, print)

    assert f"The expression {expression} contains an invalid token. " \
           f"Details: Invalid syntax for the token 1,2,3,4,*" == str(error.value)


def test_create_schedule_with_invalid_expression():

    with pytest.raises(ValueError) as error:
        Schedule('some-schedule', '* * * *', print)

    assert f"The expression must match the pattern '{EXPRESSION_VALIDATOR_REGEXP.pattern}'" == str(error.value)


# Schedule validation

def test_should_run_true():
    current_time = datetime.strptime('2021-10-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    s = Schedule('my-schedule', '* * * * *', print)
    assert s.schedule_table.should_run(current_time)


def test_should_run_false():
    current_time = datetime.strptime('2021-10-01 00:05:00', '%Y-%m-%d %H:%M:%S')
    s = Schedule('my-schedule', '*/7 * * * *', print)

    assert not s.schedule_table.should_run(current_time)


@pytest.mark.asyncio
async def test_finish_scheduler():
    s = Schedule('my-schedule', '* * * * *', print)
    await s.finish()
    assert s.stop_signal_received
    assert not s.running


@pytest.mark.asyncio
async def test_run_with_stop_signal_received():
    current_time = datetime.strptime('2021-10-01 00:05:00', '%Y-%m-%d %H:%M:%S')

    s = Schedule('my-schedule', '* * * * *', print)
    s.stop_signal_received = True

    r = await s.run(current_time)
    assert not r

