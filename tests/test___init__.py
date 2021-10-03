import pendulum
from athame import from_dsl
from athame.ast import Interval, Time, WeekdayInterval


def test_from_dsl():
    schedule_local = from_dsl(
        """
        sunday allow 0000
        monday-friday allow 0000 forbid 0800-2000
        saturday allow -1400
        """
    )
    schedule_gmt = from_dsl(
        """
        sunday allow 0000
        monday-friday allow 0000 forbid 0800-2000
        saturday allow -1400
        """,
        tz="Etc/GMT+0",
    )
    schedule_gmt_plus12 = from_dsl(
        """
        sunday allow 0000
        monday-friday allow 0000 forbid 0800-2000
        saturday allow -1400
        """,
        tz="Etc/GMT+12",
    )

    assert schedule_local.allowed == [
        WeekdayInterval(day_of_week=0, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=6, interval=Interval(start=Time.start_of_day(), end=Time(hour=14, minute=0))),
    ]
    assert schedule_local.forbidden == [
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
    ]
    assert schedule_local.tz == pendulum.local_timezone().name
    assert schedule_gmt.allowed == [
        WeekdayInterval(day_of_week=0, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=6, interval=Interval(start=Time.start_of_day(), end=Time(hour=14, minute=0))),
    ]
    assert schedule_gmt.forbidden == [
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
    ]
    assert schedule_gmt.tz == "Etc/GMT+0"
    assert schedule_gmt_plus12.allowed == [
        WeekdayInterval(day_of_week=0, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=6, interval=Interval(start=Time.start_of_day(), end=Time(hour=14, minute=0))),
    ]
    assert schedule_gmt_plus12.forbidden == [
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
    ]
    assert schedule_gmt_plus12.tz == "Etc/GMT+12"
