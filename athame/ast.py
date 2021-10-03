from __future__ import annotations

import enum
import itertools
import typing as tp
from time import sleep

import pendulum
from athame import exceptions
from pydantic import BaseModel, Field, conint


class Time(BaseModel):
    hour: conint(ge=0, le=23)
    minute: conint(ge=0, le=59)

    @classmethod
    def from_string(cls, string: str) -> Time:
        return Time(hour=int(string[:2]), minute=int(string[2:]))

    @classmethod
    def start_of_day(cls) -> Time:
        return cls(hour=0, minute=0)

    @classmethod
    def end_of_day(cls) -> Time:
        return cls(hour=23, minute=59)


class Interval(BaseModel):
    start: Time
    end: Time


# normally I would define this as a member of Agenda but
# 'from __future__ import annotations' forces us to do it this way
class Directive(enum.Enum):
    ALLOW = enum.auto()
    FORBID = enum.auto()


class Agenda(BaseModel):
    intervals: tp.List[Interval]
    directive: Directive


class WeekdayInterval(BaseModel):
    """
    Interval of time within a single day of the week.
    """

    day_of_week: conint(ge=0, le=6)
    interval: Interval

    def __contains__(self, dt: pendulum.DateTime):
        """
        Determines if a datetime is within this weekday interval.

        The boolean logic is as follows:
            - First make sure the day of the week is correct.
            - Then check that one of the following conditions is true:
                1. The datetime hour is between (exclusive) the start and end hour.
                2. The datetime hour is equal to the starting hour, not equal to the ending hour,
                   and the datetime minute is at or after the starting minute.
                3. The datetime hour is equal to the ending hour, not equal to the starting hour,
                   and the datetime minute is at or before the ending minute.
                4. The datetime hour is equal to both the starting and ending hour and the
                   datetime minute is between (inclusive) the starting and ending minutes.
        """
        return self.day_of_week == dt.day_of_week and (
            self.interval.start.hour < dt.hour < self.interval.end.hour
            or self.interval.start.hour == dt.hour != self.interval.end.hour
            and self.interval.start.minute <= dt.minute
            or self.interval.start.hour != dt.hour == self.interval.end.hour
            and self.interval.end.minute >= dt.minute
            or self.interval.start.hour == self.interval.end.hour == dt.hour
            and self.interval.start.minute <= dt.minute <= self.interval.end.minute
        )

    def next_start_after(self, moment: pendulum.DateTime) -> pendulum.DateTime:
        """
        Returns the next datetime at the start of this interval after the given moment.

        Example:
            In this example we have an interval which starts at 00:00 on Mondays. When we ask for its next start after
            00:00 on 2017-01-01 (a Sunday) it returns 00:00 on 2017-01-02.

            >>> interval = Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())
            >>> weekday_interval = WeekdayInterval(day_of_week=1, interval=interval)
            >>> moment = pendulum.datetime(2017, 1, 1, hour=0, minute=0)  # sunday
            >>> weekday_interval.next_start_after(moment)
            DateTime(2017, 1, 2, 0, 0, ...)

            If we were to ask it for the next start after a time on a Tuesday (or a time after 00:00 on a Monday) it would
            return 00:00 the following Monday.
        """
        # since pendulum.DateTime.next never returns the current day, we must manually check if the next occurence
        # of <target> is today when the days of week match.
        if moment.day_of_week == self.day_of_week:
            time_shifted_moment = moment.at(hour=self.interval.start.hour, minute=self.interval.start.minute)
            return (
                time_shifted_moment
                if time_shifted_moment >= moment
                else time_shifted_moment.next(self.day_of_week, keep_time=True)
            )

        return moment.next(self.day_of_week).at(hour=self.interval.start.hour, minute=self.interval.start.minute)

    def next_end_after(self, moment: pendulum.DateTime) -> pendulum.DateTime:
        """
        Returns the next datetime *after* the next end of this interval after the given moment. That is to say, 1 minute after
        the next end of this interval.

        Example:
            In this example we have an interval which ends at 01:30 on Mondays. When we ask for its next end after
            00:00 on 2017-01-01 (a Sunday) it returns 01:31 on 2017-01-02.

            >>> interval = Interval(start=Time.start_of_day(), end=Time(hour=1, minute=30))
            >>> weekday_interval = WeekdayInterval(day_of_week=1, interval=interval)
            >>> moment = pendulum.datetime(2017, 1, 1, hour=0, minute=0)  # sunday
            >>> weekday_interval.next_end_after(moment)
            DateTime(2017, 1, 2, 1, 31, ...)

            If we were to ask it for the next end after a time on a Tuesday (or a time after 01:31 on a Monday) it would
            return 01:31 the following Monday.
        """
        # since pendulum.DateTime.next never returns the current day, we must manually check if the next occurence
        # of <target> is today when the days of week match.
        if moment.day_of_week == self.day_of_week:
            time_shifted_moment = moment.at(hour=self.interval.end.hour, minute=self.interval.end.minute).add(minutes=1)
            return (
                time_shifted_moment
                if time_shifted_moment > moment
                else time_shifted_moment.next(self.day_of_week, keep_time=True)
            )

        return (
            moment.next(self.day_of_week)
            .at(hour=self.interval.end.hour, minute=self.interval.end.minute)
            .add(minutes=1)
        )


class Schedule(BaseModel):
    """
    This is a class for specifying intervals of time during the week in which a background worker
    is allowed to perform its work. This differs from a tool like cron in that cron is designed to
    unconditionally kick off the execution of a task at certain times whereas this is to designed
    specify the intervals of time during a week when a endlessly running worker is permitted to
    execute.
    """

    allowed: tp.List[WeekdayInterval] = Field(default_factory=list)
    forbidden: tp.List[WeekdayInterval] = Field(default_factory=list)
    tz: str = pendulum.local_timezone().name

    @classmethod
    def always_allowed(cls, tz: str = pendulum.local_timezone().name) -> Schedule:
        allowed = [
            WeekdayInterval(
                day_of_week=day_of_week,
                interval=Interval(
                    start=Time.start_of_day(),
                    end=Time.end_of_day(),
                ),
            )
            for day_of_week in range(7)
        ]
        tz = tz or pendulum.local_timezone().name
        return cls(allowed=allowed, tz=tz)

    def add_agenda_on_days(self, agenda: Agenda, days: tp.List[int]):
        weekday_intervals = [
            WeekdayInterval(day_of_week=day_of_week, interval=interval)
            for interval, day_of_week in itertools.product(agenda.intervals, days)
        ]
        if agenda.directive is Directive.ALLOW:
            self.allowed.extend(weekday_intervals)
        elif agenda.directive is Directive.FORBID:
            self.forbidden.extend(weekday_intervals)
        else:
            raise ValueError("invalid agenda type")

    def add_agendas_on_days(self, agendas: tp.List[Agenda], days: tp.List[int]):
        for agenda in agendas:
            self.add_agenda_on_days(agenda, days)

    def is_allowed_at(self, moment: pendulum.DateTime) -> bool:
        moment = moment.in_tz(self.tz)
        return any(moment in weekday_interval for weekday_interval in self.allowed) and not any(
            moment in weekday_interval for weekday_interval in self.forbidden
        )

    def is_allowed_at_or_raise(self, moment: pendulum.DateTime):
        if not self.is_allowed_at(moment):
            raise exceptions.ScheduleError(f"{moment.format('dddd HH:mm')} is not allowed")

    def is_allowed_now(self) -> bool:
        return self.is_allowed_at(pendulum.now())

    def is_allowed_now_or_raise(self):
        self.is_allowed_at_or_raise(pendulum.now())

    def next_moment_allowed_after(self, moment: pendulum.DateTime) -> pendulum.DateTime:
        # the next allowed moment will always be among the following candidates:
        #   1. the given moment
        #   2. the start of an allowed interval
        #   3. the end of a forbidden interval
        moment = moment.in_tz(self.tz)
        allowed_starts = [wdi.next_start_after(moment) for wdi in self.allowed]
        forbidden_ends = [wdi.next_end_after(moment) for wdi in self.forbidden]
        candidates = [moment] + allowed_starts + forbidden_ends
        allowed_only = filter(self.is_allowed_at, candidates)
        with exceptions.ScheduleError.handle_errors("no allowed intervals in the schedule", exception_class=ValueError):
            best, *_ = sorted(allowed_only)

        return best

    def sleep_until_allowed(self):
        moment = pendulum.now()

        if self.is_allowed_at(moment):
            return

        next_allowed_moment = self.next_moment_allowed_after(moment)
        sleep_duration = next_allowed_moment - moment
        sleep(sleep_duration.total_seconds())
