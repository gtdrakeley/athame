import pytest
from athame import exceptions
from athame.ast import Agenda, Directive, Interval, Time, WeekdayInterval
from athame.lexer import Lexer, TokenType
from athame.parser import Parser


def test_parse():
    lexer = Lexer.from_string(
        """
        sunday allow 0000
        monday-friday allow 0000 forbid 0800-2000
        saturday allow -1400
        """
    )
    parser = Parser(lexer)
    schedule = parser.parse()

    assert schedule.allowed == [
        WeekdayInterval(day_of_week=0, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=6, interval=Interval(start=Time.start_of_day(), end=Time(hour=14, minute=0))),
    ]
    assert schedule.forbidden == [
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
    ]


def test_parse_schedule():
    lexer = Lexer.from_string(
        """
        sunday allow 0000
        monday-friday allow 0000 forbid 0800-2000
        saturday allow -1400
        """
    )
    parser = Parser(lexer)
    lexer.next_token()
    schedule = parser.parse_schedule()

    assert schedule.allowed == [
        WeekdayInterval(day_of_week=0, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=0, minute=0), end=Time.end_of_day())),
        WeekdayInterval(day_of_week=6, interval=Interval(start=Time.start_of_day(), end=Time(hour=14, minute=0))),
    ]
    assert schedule.forbidden == [
        WeekdayInterval(day_of_week=1, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=2, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=3, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=4, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
        WeekdayInterval(day_of_week=5, interval=Interval(start=Time(hour=8, minute=0), end=Time(hour=20, minute=0))),
    ]


@pytest.mark.parametrize(
    "string,expected",
    [
        ("sunday", [0]),
        ("sun", [0]),
        ("monday", [1]),
        ("mon", [1]),
        ("tuesday", [2]),
        ("tue", [2]),
        ("wednesday", [3]),
        ("wed", [3]),
        ("thursday", [4]),
        ("thu", [4]),
        ("friday", [5]),
        ("fri", [5]),
        ("saturday", [6]),
        ("sat", [6]),
        ("monday-friday", [1, 2, 3, 4, 5]),
        ("wed-tue", [3, 4, 5, 6, 0, 1, 2]),
    ],
)
def test_parse_days(string, expected):
    lexer = Lexer.from_string(string)
    parser = Parser(lexer)
    lexer.next_token()
    assert parser.parse_days() == expected
    assert lexer.token.type == TokenType.END_INPUT


@pytest.mark.parametrize("inp", ["", "-", "0000", "sunday-", "sunday-0000"])
def test_parse_days_raises_ParserError_when_expected(inp):
    lexer = Lexer.from_string(inp)
    parser = Parser(lexer)
    lexer.next_token()
    with pytest.raises(exceptions.ParserError):
        parser.parse_days()


def test_parse_agendas():
    lexer = Lexer.from_string(
        """
        allow 0101-0202 0303-0404
        forbid 0505-0606 0707-0808
        """
    )
    parser = Parser(lexer)
    lexer.next_token()
    assert parser.parse_agendas() == [
        Agenda(
            directive=Directive.ALLOW,
            intervals=[
                Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
                Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
            ],
        ),
        Agenda(
            directive=Directive.FORBID,
            intervals=[
                Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
                Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
            ],
        ),
    ]


def test_parse_agenda():
    lexer = Lexer.from_string(
        """
        allow 0101-0202 0303-0404
        forbid 0505-0606 0707-0808
        """
    )
    parser = Parser(lexer)
    lexer.next_token()
    assert parser.parse_agenda() == Agenda(
        directive=Directive.ALLOW,
        intervals=[
            Interval(start=Time(hour=1, minute=1), end=Time(hour=2, minute=2)),
            Interval(start=Time(hour=3, minute=3), end=Time(hour=4, minute=4)),
        ],
    )
    assert parser.parse_agenda() == Agenda(
        directive=Directive.FORBID,
        intervals=[
            Interval(start=Time(hour=5, minute=5), end=Time(hour=6, minute=6)),
            Interval(start=Time(hour=7, minute=7), end=Time(hour=8, minute=8)),
        ],
    )


def test_parse_agenda_raises_ParserError_when_expected():
    lexer = Lexer.from_string("sunday")
    parser = Parser(lexer)
    lexer.next_token()
    with pytest.raises(exceptions.ParserError):
        parser.parse_agenda()


def test_parse_intervals():
    lexer = Lexer.from_string("0042-1337 -1234 1010")
    parser = Parser(lexer)
    lexer.next_token()
    assert parser.parse_intervals() == [
        Interval(start=Time(hour=0, minute=42), end=Time(hour=13, minute=37)),
        Interval(start=Time.start_of_day(), end=Time(hour=12, minute=34)),
        Interval(start=Time(hour=10, minute=10), end=Time.end_of_day()),
    ]


def test_parse_interval():
    lexer = Lexer.from_string("0042-1337 -1234 1010")
    parser = Parser(lexer)
    lexer.next_token()
    assert parser.parse_interval() == Interval(start=Time(hour=0, minute=42), end=Time(hour=13, minute=37))
    assert parser.parse_interval() == Interval(start=Time.start_of_day(), end=Time(hour=12, minute=34))
    assert parser.parse_interval() == Interval(start=Time(hour=10, minute=10), end=Time.end_of_day())


@pytest.mark.parametrize("inp", ["", "sunday", "0000-sunday", "-sunday"])
def test_parse_interval_raises_ParserError_when_expected(inp):
    lexer = Lexer.from_string(inp)
    parser = Parser(lexer)
    lexer.next_token()
    with pytest.raises(exceptions.ParserError):
        parser.parse_interval()


def test_unexpected_token():
    lexer = Lexer.from_string("sunday")
    parser = Parser(lexer)
    lexer.next_token()

    with pytest.raises(exceptions.ParserError) as excinfo:
        parser.unexpected_token(expected=[TokenType.TIME])

    assert excinfo.value.message.endswith("expected one of: TIME\ngot: DAY_OF_WEEK")

    with pytest.raises(exceptions.ParserError) as excinfo:
        parser.unexpected_token(expected=[TokenType.DASH, TokenType.ALLOW])

    assert excinfo.value.message.endswith("expected one of: DASH, ALLOW\ngot: DAY_OF_WEEK")
