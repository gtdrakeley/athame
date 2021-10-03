# Athame

> A ceremonial black-handled knife used in pagan rituals as an implement to scribe magical circles for controlling summoned daemons.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About](#about)
- [Installation](#installation)
- [Usage & Examples](#usage--examples)
  - [DSL](#dsl)
  - [Querying the Schedule](#querying-the-schedule)
  - [Defining a Schedule](#defining-a-schedule)
  - [Minimal Example](#minimal-example)
- [License](#license)

## About

The `athame` package provides tools for scheduling allowed execution periods for persistently running daemon processes and other kinds of looping background workers.

While building various daemons of the type described above and considering existing tools such as `cron` I noticed that nearly every relevant scheduling tool I encountered was designed for use with processes which run a single time when triggered. This lack of options for limiting and defining blocks of allowed time for workers which run in a loop inspired the creation of this package.

### Into the Future

`Athame` is currently in very early beta and thus the API is subject to breaking changes.

Potential future features include:
- Supporting blocks of time beyond weeks such as months and years.
- Changing ranges to be exclusive on the terminating side to better align with user expectations.
- Providing a class rather than a top level factory function
- Additional construction methods beyond `from_dsl`.

## Installation

You can install `athame` as you would other python packages.

```
pip install athame
```

```
poetry add athame
```

```
pipenv install athame
```

## Usage & Examples

### DSL

`Athame` defines a simple domain specific language for defining what times are allowed in a given execution schedule.

Currently `athame` only supports defining weekly schedules with time precision down to minutes.

#### Grammar

```
schedule  : schedule days agendas
          | days agendas

days      : DAY_OF_WEEK '-' DAY_OF_WEEK
          | DAY_OF_WEEK

agendas   : agendas agenda
          | agenda

agenda    : ALLOW intervals
          | FORBID intervals

intervals : intervals interval
          | interval

interval  : TIME '-' TIME
          | '-' TIME
          | TIME
```

The behavior of these constructs are defined as follows.

- [Interval(s)](#intervals)
- [Agenda(s)](#agendas)
- [Days](#days)
- [Schedule](#schedule)

#### Interval(s)

Intervals are hyphen-seperated times. They expect 24 hour clock style times without colons such as `0000`, `0800`, and `1430`. Days end at `2359`. Examples include:

```
0000-1800
0100-0859
0900-2359
```

Intervals specified as a time with no hyphen are assumed to go to the end of the day. The following intervals are equivalent:

```
1000
1000-2359
```

Intervals preceded by a hyphen without an associated starting time are assumed to start at the beginning of the day. The following are equivalent. The following intervals are equivalent:

```
-1330
0000-1330
```

In the grammar above can be seen a distinction between an `interval` and `intervals` plural. Multiple `interval` can be chained side-by-side to be understood by the DSL as an `intervals` which is a collection of `interval` as in the following example:

```
0000-0759 2000
```

Intervals are inclusive ranges and thus both ends of the interval are included. This means that the common phrase

> 8:00am until 8:00pm

would be commonly specified by the interval `0800-1959` since most people assume it is implied that execution would immediately begin at 8:00pm.

#### Agenda(s)

Agendas are one of the words `allow` or `forbid` followed by an `intervals` construct such as the following:

```
allow 0000
forbid 0200-1459
```

Like `interval` and `intervals` above the DSL recognized a disctinction between constructs for `agenda` and `agendas` such that the multiple `agenda` side-by-side define an `agendas` collection as follows:

```
allow 0100-0659 1800-2159
```

#### Days

Days are specified as the names of the 7 days of the week, either alone or as a hyphen-seperated range.

```
sunday
monday-friday
```

The 3-letter abbreviation for each day is also acceptable as in:

```
mon-fri
```

Days, while assuming the week starts on Sunday, will wrap around appropriately. You can include the days Friday, Saturday, Sunday, and Monday like so:

```
friday-monday
```

#### Schedule

Schedules are collections of the previous constructs that specify allowed execution times during the week.

```
sunday allow 0000
mon-fri allow 0500-1659
```

Further examples for schedule can be seen in the code samples in the [Schedule Examples](#schedule-examples) section below.

### Querying the Schedule

Once a schedule is specified, `athame` provides simple functions for querying the schedule to see if executions is allowed at a specific moment in time.

```python
# checking a specific moment
if schedule.is_allowed_at(moment):
  ...

# checking a specific moment, raising a ScheduleError if not allowed.
schedule.is_allowed_at_or_raise(moment)

# checking now
while schedule.is_allowed_now():
  ...

# checking now, raising a ScheduleError if not allowed
schedule.is_allowed_now_or_raise()

# getting the moment at the start of the next allowed period after a given moment
next_allowed_moment = schedule.next_moment_allowed_after(moment)

# sleeping until the next allowed period of time
schedule.sleep_until_allowed()
```

It is this author's opinion that Python's built-in [datetime](https://docs.python.org/3/library/datetime.html) library is lacking some key features and makes hazardous decisions--namely that datetimes are by default naive without a timezone--which makes it both difficult to work with and code using it prone to errors. For this reason, `athame` adopts use of the absolutely fantastic [pendulum](https://pendulum.eustace.io/docs/) library by Sébastien Eustace and thus expects `pendulum.DateTime` objects with timezones for the `moment` variables in examples above. I highly recommend you give [pendulum](https://pendulum.eustace.io/docs/) a try.

### Defining a Schedule

To build a schedule use the `from_dsl` function.


```python
from athame import from_dsl

# all day all week
schedule = from_dsl("sun-sat allow 0000")

# the Schedule class also has convenience method for generating an all day all week schedule.
from athame import Schedule

schedule = Schedule.always_allowed()

# all day all week except between 8:00 and 20:00
#   notice we used 19:59 as the terminating time as range's in athame are inclusive
#   and we want to start executing right at 20:00 rather than at 20:01.
schedule = from_dsl("sun-sat allow 0000 forbid 0800-1959")

# monday through friday during business hours
schedule = from_dsl("mon-fri allow 0800-1659")

# all day all week except during business hours
schedule = from_dsl(
  """
  sun-sat allow 0000
  mon-fri forbid 0800-1659
  """
)
```

### Minimal Example

```python
from athame import Schedule, from_dsl


def get_work():
  """
  an exercise for the reader :^)
  """


def worker(schedule: Schedule):
  while True:
    schedule.sleep_until_allowed()

    work = get_work()

    for task in work:
      # do stuff

      if not schedule.is_allowed_now():
        break

if __name__ == "__main__":
  # work hours only
  schedule = from_dsl("sun-sat allow 0800-1659")
  worker(schedule)
```

## License

`Athame` is distributed under the [MIT License](https://opensource.org/licenses/mit-license.php).
