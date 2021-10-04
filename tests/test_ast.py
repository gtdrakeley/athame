from unittest import mock

import pendulum
import pytest

from athame import exceptions
from athame.ast import (
    Agenda,
    Directive,
    Interval,
    Schedule,
    Time,
    WeekdayInterval,
)
from tests import tools as test_tools


class TestTime:
    def test_from_string(self):
        assert Time.from_string("1337") == Time(hour=13, minute=37)

    def test_start_of_day(self):
        assert Time.start_of_day() == Time(hour=0, minute=0)

    def test_end_of_day(self):
        assert Time.end_of_day() == Time(hour=23, minute=59)


class TestWeekdayInterval:
    def test___contains__(self):
        # Jan 1st 2017 is a Sunday which is convenient
        moment = pendulum.local(year=2017, month=1, day=1)

        weekday_interval = WeekdayInterval(
            day_of_week=0,
            interval=Interval(start=Time(hour=2, minute=15), end=Time(hour=14, minute=45)),
        )
        assert moment.at(hour=2, minute=15) in weekday_interval
        assert moment.at(hour=14, minute=45) in weekday_interval
        assert moment.at(hour=2, minute=45) in weekday_interval
        assert moment.at(hour=14, minute=15) in weekday_interval
        assert moment.at(hour=8, minute=30) in weekday_interval
        assert moment.at(hour=8, minute=0) in weekday_interval
        assert moment.at(hour=8, minute=50) in weekday_interval
        assert moment.at(hour=0) not in weekday_interval
        assert moment.at(hour=2, minute=14) not in weekday_interval
        assert moment.at(hour=15) not in weekday_interval
        assert moment.at(hour=14, minute=46) not in weekday_interval
        assert moment.add(days=1).at(hour=8, minute=30) not in weekday_interval

        weekday_interval = WeekdayInterval(
            day_of_week=0,
            interval=Interval(start=Time(hour=12, minute=15), end=Time(hour=12, minute=45)),
        )
        assert moment.at(hour=12, minute=30) in weekday_interval
        assert moment.at(hour=12, minute=15) in weekday_interval
        assert moment.at(hour=12, minute=45) in weekday_interval
        assert moment.at(hour=11) not in weekday_interval
        assert moment.at(hour=13) not in weekday_interval
        assert moment.at(hour=12, minute=14) not in weekday_interval
        assert moment.at(hour=12, minute=46) not in weekday_interval
        assert moment.add(days=1).at(hour=12, minute=30) not in weekday_interval

    @pytest.mark.parametrize(
        "moment,day_of_week,start,expected",
        [
            (
                pendulum.local(2017, 1, 1),
                0,
                Time.start_of_day(),
                pendulum.local(2017, 1, 1),
            ),
            (
                pendulum.local(2017, 1, 1),
                0,
                Time(hour=1, minute=30),
                pendulum.local(2017, 1, 1, hour=1, minute=30),
            ),
            (
                pendulum.local(2017, 1, 1, hour=1),
                0,
                Time.start_of_day(),
                pendulum.local(2017, 1, 8),
            ),
            (
                pendulum.local(2017, 1, 1, hour=1),
                3,
                Time.start_of_day(),
                pendulum.local(2017, 1, 4),
            ),
        ],
    )
    def test_next_start_after(self, moment, day_of_week, start, expected):
        weekday_interval = WeekdayInterval(
            day_of_week=day_of_week,
            interval=Interval(
                start=start,
                end=Time.end_of_day(),
            ),
        )
        assert weekday_interval.next_start_after(moment) == expected

    @pytest.mark.parametrize(
        "moment,day_of_week,end,expected",
        [
            (
                pendulum.local(2017, 1, 1),
                0,
                Time(hour=1, minute=0),
                pendulum.local(2017, 1, 1, hour=1, minute=1),
            ),
            (
                pendulum.local(2017, 1, 1, hour=1),
                0,
                Time(hour=1, minute=0),
                pendulum.local(2017, 1, 1, hour=1, minute=1),
            ),
            (
                pendulum.local(2017, 1, 1, hour=1),
                0,
                Time(hour=0, minute=59),
                pendulum.local(2017, 1, 8, hour=1),
            ),
            (
                pendulum.local(2017, 1, 1),
                3,
                Time(hour=0, minute=0),
                pendulum.local(2017, 1, 4, minute=1),
            ),
            (
                pendulum.local(2017, 1, 1, second=1),
                0,
                Time(hour=0, minute=0),
                pendulum.local(2017, 1, 1, minute=1),
            ),
        ],
    )
    def test_next_end_after(self, moment, day_of_week, end, expected):
        weekday_interval = WeekdayInterval(
            day_of_week=day_of_week,
            interval=Interval(
                start=Time.start_of_day(),
                end=end,
            ),
        )
        assert weekday_interval.next_end_after(moment) == expected


class TestSchedule:
    def test_always_allowed(self):
        gmt_schedule = Schedule.always_allowed(tz="Etc/GMT+0")
        gmt_plus12_schedule = Schedule.always_allowed(tz="Etc/GMT+12")
        interval = Interval(start=Time.start_of_day(), end=Time.end_of_day())
        assert gmt_schedule.allowed == [
            WeekdayInterval(day_of_week=0, interval=interval),
            WeekdayInterval(day_of_week=1, interval=interval),
            WeekdayInterval(day_of_week=2, interval=interval),
            WeekdayInterval(day_of_week=3, interval=interval),
            WeekdayInterval(day_of_week=4, interval=interval),
            WeekdayInterval(day_of_week=5, interval=interval),
            WeekdayInterval(day_of_week=6, interval=interval),
        ]
        assert gmt_schedule.tz == "Etc/GMT+0"
        assert gmt_plus12_schedule.allowed == [
            WeekdayInterval(day_of_week=0, interval=interval),
            WeekdayInterval(day_of_week=1, interval=interval),
            WeekdayInterval(day_of_week=2, interval=interval),
            WeekdayInterval(day_of_week=3, interval=interval),
            WeekdayInterval(day_of_week=4, interval=interval),
            WeekdayInterval(day_of_week=5, interval=interval),
            WeekdayInterval(day_of_week=6, interval=interval),
        ]
        assert gmt_plus12_schedule.tz == "Etc/GMT+12"

    def test_add_agenda_on_days(self):
        schedule = Schedule()
        agenda1 = Agenda(
            intervals=[
                Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
                Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            ],
            directive=Directive.ALLOW,
        )
        agenda2 = Agenda(
            intervals=[
                Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
                Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            ],
            directive=Directive.FORBID,
        )
        schedule.add_agenda_on_days(agenda1, days=[0, 1])
        schedule.add_agenda_on_days(agenda2, days=[2, 3])

        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=2,
                interval=Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=3,
                interval=Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=2,
                interval=Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=3,
                interval=Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            )
            in schedule.forbidden
        )

    def test_add_agendas_on_days(self):
        schedule = Schedule()
        agenda1 = Agenda(
            intervals=[
                Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
                Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            ],
            directive=Directive.ALLOW,
        )
        agenda2 = Agenda(
            intervals=[
                Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
                Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            ],
            directive=Directive.FORBID,
        )
        schedule.add_agendas_on_days([agenda1, agenda2], days=[0, 1])
        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            )
            in schedule.allowed
        )
        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            )
            in schedule.forbidden
        )
        assert (
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            )
            in schedule.forbidden
        )

    def test_is_allowed_at(self):
        # Jan 1st 2017 is a Sunday which is convenient
        moment = pendulum.local(year=2017, month=1, day=1)
        schedule = Schedule()

        assert not schedule.is_allowed_at(moment)
        schedule.allowed.append(
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(
                    start=Time(hour=1, minute=0),
                    end=Time(hour=2, minute=0),
                ),
            )
        )
        assert not schedule.is_allowed_at(moment)
        assert schedule.is_allowed_at(moment.at(hour=1))
        assert schedule.is_allowed_at(moment.at(hour=2))
        assert not schedule.is_allowed_at(moment.at(hour=3))
        assert not schedule.is_allowed_at(moment.at(hour=2, minute=1))
        assert not schedule.is_allowed_at(moment.add(days=1).at(hour=1))
        schedule.forbidden.append(
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(
                    start=Time(hour=1, minute=15),
                    end=Time(hour=1, minute=45),
                ),
            )
        )
        assert not schedule.is_allowed_at(moment.at(hour=1, minute=15))
        assert schedule.is_allowed_at(moment.at(hour=1))
        schedule.allowed.append(
            WeekdayInterval(
                day_of_week=1,
                interval=Interval(
                    start=Time(hour=0, minute=0),
                    end=Time.end_of_day(),
                ),
            )
        )
        assert schedule.is_allowed_at(moment.add(days=1))

    def test_is_allowed_at_coerces_tz(self):
        time = Time(hour=8, minute=0)
        schedule = Schedule(
            allowed=[
                WeekdayInterval(
                    day_of_week=0,
                    interval=Interval(
                        start=time,
                        end=time,
                    ),
                )
            ],
            tz="Etc/GMT+0",
        )

        # these timezones look backwards and that is because, by design, they are
        # reading: https://stackoverflow.com/questions/53076575/time-zones-etc-gmt-why-it-is-other-way-round
        #          https://en.wikipedia.org/wiki/Tz_database#Area
        assert schedule.is_allowed_at(pendulum.datetime(2017, 1, 1, hour=7, tz="Etc/GMT+1"))
        assert not schedule.is_allowed_at(pendulum.datetime(2017, 1, 1, hour=8, tz="Etc/GMT+1"))

    def test_is_allowed_at_or_raise(self):
        moment = pendulum.local(2017, 1, 1)
        schedule = Schedule()
        with pytest.raises(exceptions.ScheduleError, match=r"Sunday 00:00 is not allowed"):
            schedule.is_allowed_at_or_raise(moment)

        schedule.allowed.append(
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(
                    start=Time.start_of_day(),
                    end=Time.end_of_day(),
                ),
            )
        )
        schedule.is_allowed_at_or_raise(moment)

    @pytest.mark.parametrize("moment", [pendulum.local(2017, 1, 1), pendulum.local(2017, 1, 2)])
    def test_is_allowed_now(self, moment):
        schedule = Schedule()
        with test_tools.frozen_time(moment):
            assert not schedule.is_allowed_now()
            time = Time(hour=moment.hour, minute=moment.minute)
            schedule.allowed.append(
                WeekdayInterval(
                    day_of_week=moment.day_of_week,
                    interval=Interval(
                        start=time,
                        end=time,
                    ),
                )
            )
            assert schedule.is_allowed_now()

    @pytest.mark.parametrize("moment", [pendulum.local(2017, 1, 1), pendulum.local(2017, 1, 2)])
    def test_is_allowed_now_or_raise(self, moment):
        schedule = Schedule()
        with test_tools.frozen_time(moment):
            with pytest.raises(exceptions.ScheduleError):
                schedule.is_allowed_now_or_raise()
            time = Time(hour=moment.hour, minute=moment.minute)
            schedule.allowed.append(
                WeekdayInterval(
                    day_of_week=moment.day_of_week,
                    interval=Interval(
                        start=time,
                        end=time,
                    ),
                )
            )
            schedule.is_allowed_now_or_raise()

    @pytest.mark.parametrize(
        "moment,allowed,forbidden,expected",
        [
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [],
                pendulum.local(2017, 1, 1),
            ),
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time(hour=1, minute=0),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [],
                pendulum.local(2017, 1, 1, hour=1),
            ),
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time(hour=1, minute=0),
                        ),
                    )
                ],
                pendulum.local(2017, 1, 1, hour=1, minute=1),
            ),
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time(hour=1, minute=0),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time(hour=1, minute=0),
                            end=Time(hour=4, minute=0),
                        ),
                    )
                ],
                pendulum.local(2017, 1, 1, hour=4, minute=1),
            ),
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=4,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [],
                pendulum.local(2017, 1, 5),
            ),
            (
                pendulum.local(2017, 1, 2),
                [
                    WeekdayInterval(
                        day_of_week=0,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    )
                ],
                [],
                pendulum.local(2017, 1, 8),
            ),
            (
                pendulum.local(2017, 1, 1),
                [
                    WeekdayInterval(
                        day_of_week=3,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    ),
                    WeekdayInterval(
                        day_of_week=2,
                        interval=Interval(
                            start=Time.start_of_day(),
                            end=Time.end_of_day(),
                        ),
                    ),
                ],
                [],
                pendulum.local(2017, 1, 3),
            ),
        ],
    )
    def test_next_moment_allowed_after(self, moment, allowed, forbidden, expected):
        schedule = Schedule(allowed=allowed, forbidden=forbidden)
        assert schedule.next_moment_allowed_after(moment) == expected

    def test_next_moment_allowed_after_coerces_tz(self):
        time1 = Time(hour=8, minute=0)
        time2 = Time(hour=20, minute=0)
        schedule = Schedule(
            allowed=[
                WeekdayInterval(day_of_week=0, interval=Interval(start=time2, end=time2)),
                WeekdayInterval(day_of_week=1, interval=Interval(start=time1, end=time1)),
            ],
            tz="Etc/GMT+0",
        )

        moment = pendulum.datetime(2017, 1, 2, hour=8, tz="Etc/GMT-12")
        expected = pendulum.datetime(2017, 1, 1, hour=20, tz="Etc/GMT+0")
        assert schedule.next_moment_allowed_after(moment) == expected

    def test_next_moment_allowed_after_raises_ScheduleError_when_no_times_allowed(self):
        moment = pendulum.local(2017, 1, 1)
        schedule = Schedule()
        with pytest.raises(exceptions.ScheduleError, match=r"no allowed intervals in the schedule"):
            schedule.next_moment_allowed_after(moment)

        weekday_interval = WeekdayInterval(
            day_of_week=0,
            interval=Interval(
                start=Time.start_of_day(),
                end=Time.end_of_day(),
            ),
        )
        schedule.allowed.append(weekday_interval)
        schedule.forbidden.append(weekday_interval)

        with pytest.raises(exceptions.ScheduleError, match=r"no allowed intervals in the schedule"):
            schedule.next_moment_allowed_after(moment)

    def test_sleep_until_allowed(self):
        schedule = Schedule()
        schedule.allowed.append(
            WeekdayInterval(
                day_of_week=0,
                interval=Interval(
                    start=Time(hour=0, minute=5),
                    end=Time.end_of_day(),
                ),
            )
        )

        def mock_pendulum_now():
            return pendulum.local(2017, 1, 1)

        with mock.patch("pendulum.now", new=mock_pendulum_now):
            with mock.patch("athame.ast.sleep") as mock_sleep:
                schedule.sleep_until_allowed()

        mock_sleep.assert_called_once_with(300.0)
