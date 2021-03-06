## v.0.3.0 - 2022-05-25

**Added**

 - Now is possible to use the range notation in expression tokens.

## v.0.2.0 - 2021-12-28

**Added**

 - Now is possible to pass a list of dates which the job will not be executed.

## v.0.1.2 - 2021-12-13

**Added**

 - Additional validation in the `Scheduler` class to prevent duplicated executions.

## v.0.1.1 - 2021-12-10

**Changed**

 - Now is possible to set the verification frequency for running tasks using the `SCHEDULE_CHECK_INTERVAL`

## v.0.1.0 - 2021-04-29

**Added**

 - Now the `Schedule` class supports timezones.

**Changed**

 - The logger instances has been moved to inside the classes.

## v.0.0.5 - 2021-04-26

**Removed**

 - The signal handlers in order to block the uvicorn loop when working with fastapi.

## v.0.0.4 - 2021-04-25

**Fixed**

 - Now the schedule only runs if already finished the last execution.

## v0.0.3 - 2021-04-24

**Changed**

 - The method `_create_schedule` is a function now.

**Fixed**

 - When a job raises an exception the `Schedule` now logs the message instead of breaking.

## v0.0.2 - 2021-04-23

**Added**

 - Tests for the `Schedule` class

## v0.0.1 - 2021-04-23

**Added**

 - First working version