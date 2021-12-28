import re
import time
import asyncio
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import Callable, List, Union


# This regular expression is used to validate the crontab expression
# passed to the constructor.
EXPRESSION_VALIDATOR_REGEXP = re.compile(r"((([\d*]+|[\d*]/\d),?)+ ?){5}")
EXPRESSION_SEPARATOR = " "
EXPECTED_TOKENS = 5
ALL_TOKEN = "*"
NTH_TOKEN = "/"
MULTI_TOKEN = ","


@dataclass
class ScheduleTable:
    minutes: Union[List[int], bool]
    hours: Union[List[int], bool]
    days: Union[List[int], bool]
    months: Union[List[int], bool]
    weekdays: Union[List[int], bool]

    def should_run(self, current_time: datetime) -> bool:
        """
        Check if the current_timestamp is true for all tokens and return

        :param current_time: The current timestamp received from the external loop
        :return: Boolean informing if the action should be called
        """
        return all([self.minutes is True or current_time.minute in self.minutes,
                    self.hours is True or current_time.hour in self.hours,
                    self.days is True or current_time.day in self.days,
                    self.months is True or current_time.month in self.months,
                    self.weekdays is True or current_time.weekday() in self.weekdays])


class Schedule:
    """
        Class responsible for create the schedule
        table and check if the action should be run.
    """

    def __init__(self,
                 name: str,
                 expression: str,
                 timezone: str,
                 job: Callable,
                 excluded_dates: List[date] = None):
        """
        :param name: The schedule name
        :param expression: A crontab expression, for more information
            please check: https://en.wikipedia.org/wiki/Cron
        :param timezone: Timezone name based on IANA database. Please
            check: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        :param excluded_dates: List containing the date which the schedule
            will not run.
        :param job: An awaitable object to be run.
        """
        self.logger = logging.getLogger('timewheel.scheduler')
        self.name = name
        self.schedule_table = create_schedules(expression)
        self.timezone = ZoneInfo(timezone)
        self.excluded_dates = excluded_dates
        self.job = job
        self.running = False
        self.last_execution = None
        self.stop_signal_received = False

        self.logger.info(f"[{self.name}]: Created scheduler for the expression "
                         f"{expression} and job {job} using the timezone {timezone}")

        self.logger.debug(f"[{self.name}]: Schedule table data: {self.schedule_table}")

    async def run(self):
        """
        Checks if the job should be run in the current timestamp
        for the schedule timezone.
        If the scheduler received the signal to finish, than the
        execution is ignored.

        Important: The Callable should never return any value or
        the execution will be marked as error.

        :return: None
        """
        current_time = datetime.now(tz=self.timezone).replace(second=0, microsecond=0)
        self.logger.debug(f"[{self.name}]: Checking if should run at {current_time} using the tz {self.timezone}")

        if self.stop_signal_received:
            return

        if self.schedule_table.should_run(current_time):
            # Returns if the current_date is set as excluded
            if self.excluded_dates is not None and current_time.date() in self.excluded_dates:
                self.logger.info(f"[{self.name}]: The {self.job} should be executed, but the date "
                                 f"{current_time.date()} has been added to the exclusion list.")
                return
            # This check is used to avoid the execution of a task more then once in
            # a minute
            if self.last_execution is None or current_time != self.last_execution:
                self.last_execution = current_time
                self.running = True
                succeeded = True
                start = time.time()
                self.logger.info(f"[{self.name}]: Running the schedule with the job {self.job}")
                if asyncio.iscoroutinefunction(self.job):
                    result = await asyncio.gather(self.job(),
                                                  return_exceptions=True)
                else:
                    result = await asyncio.gather(
                        asyncio.get_running_loop().run_in_executor(None, self.job),
                        return_exceptions=True
                    )
                if result and result[0] is not None:
                    succeeded = False
                    self.logger.error(f"[{self.name}]: An unexpected error occurred "
                                      f"while running the job {self.job}. Details: "
                                      f"{result}")
                self.logger.info(f"[{self.name}]: Job finished in {time.time() - start} seconds with status {succeeded}.")
                self.running = False

    async def finish(self):
        """
        Set the stop signal as True in order to avoid
        new executions and waits the instance finish
        the action execution.
        """
        self.logger.warning(f"{self.name}: Finish signal received")

        self.stop_signal_received = True
        while self.running:
            await asyncio.sleep(0.5)


def create_schedules(expression: str) -> ScheduleTable:
    """
    Convert a cron expression into a ScheduleTable.

    The expression structure is the following:

     ┌───────────── minute (0 - 59)
     │ ┌───────────── hour (0 - 23)
     │ │ ┌───────────── day of the month (1 - 31)
     │ │ │ ┌───────────── month (1 - 12)
     │ │ │ │ ┌───────────── day of the week (0 - 6)
     │ │ │ │ │
     * * * * *

    :param expression: String containing the cron expression
    :return:
    """
    if not re.fullmatch(EXPRESSION_VALIDATOR_REGEXP, expression):
        raise ValueError(f"The expression must match the pattern "
                         f"'{EXPRESSION_VALIDATOR_REGEXP.pattern}'")

    tokens = expression.split(EXPRESSION_SEPARATOR)
    try:
        return ScheduleTable(minutes=parse_expression_token(tokens[0], 0, 59),
                             hours=parse_expression_token(tokens[1], 0, 23),
                             days=parse_expression_token(tokens[2], 1, 31),
                             months=parse_expression_token(tokens[3], 1, 12),
                             weekdays=parse_expression_token(tokens[4], 0, 6))

    except ValueError as error:
        raise ValueError(f"The expression {expression} contains an "
                         f"invalid token. Details: {''.join(error.args)}") from error


def parse_expression_token(token: str,
                           start_value: int,
                           max_value: int) -> Union[List[int], bool]:
    """
    Converts a token into a list of integers or a bool

    :param token: The string containing the token expression. Eg: */2,13
    :param start_value: The initial value used to create the range
    :param max_value: The max value allowed for the token. This value is
        also used to generate the values list.
    :return:
        If the token value is an asterisk returns True
        else returns a list containing the integer values
    """
    extracted_tokens = token.split(MULTI_TOKEN)

    if len(extracted_tokens) > 1 and ALL_TOKEN in extracted_tokens:
        raise ValueError(f"Invalid syntax for the token {token}")

    generated_tokens = []
    for extracted_token in extracted_tokens:
        if extracted_token == ALL_TOKEN:
            return True
        if NTH_TOKEN in extracted_token:
            generated_tokens.extend(parse_nth_token(extracted_token,
                                                    start_value,
                                                    max_value))
        else:
            extracted_token = int(extracted_token)
            if extracted_token > max_value:
                raise ValueError(f"The token value {extracted_token} is higher "
                                 f"then the max value ({max_value}) for the "
                                 f"field type.")
            generated_tokens.append(extracted_token)

    return sorted(generated_tokens)


def parse_nth_token(nth_token: str,
                    start_value: int,
                    max_value: int):
    """
    Parses a nth token expression and generates
    the corresponding list of integers.

    :param nth_token: nth expression. E.g: */2
    :param start_value: Initial value for the interval
    :param max_value: Max value for the interval
    :return: A list containing all values which the
        mod from the right value is zero
    """
    nth = int(nth_token.split(NTH_TOKEN)[1])
    if nth > max_value:
        raise ValueError(f"The nth token value {nth} is higher then the "
                         f"max value ({max_value}) for the field type.")

    return([value for value in range(start_value, max_value + 1)
            if value % nth == 0])
