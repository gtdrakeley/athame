import typing as tp

from athame import exceptions
from athame.ast import Agenda, Directive, Interval, Schedule, Time
from athame.lexer import Lexer, TokenType


class Parser:
    GRAMMAR = """
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
    """

    def __init__(self, lexer: Lexer):
        self.lexer = lexer

    def parse(self) -> Schedule:
        self.lexer.next_token()
        return self.parse_schedule()

    def parse_schedule(self) -> Schedule:
        """
        schedule : schedule days agendas
                 | days agendas
        """

        schedule = Schedule()
        days = self.parse_days()
        agendas = self.parse_agendas()
        schedule.add_agendas_on_days(agendas, days)
        while self.lexer.token.type is TokenType.DAY_OF_WEEK:
            days = self.parse_days()
            agendas = self.parse_agendas()
            schedule.add_agendas_on_days(agendas, days)

        return schedule

    def parse_days(self) -> tp.List[int]:
        """
        days : DAY_OF_WEEK '-' DAY_OF_WEEK
             | DAY_OF_WEEK
        """

        if self.lexer.token.type is not TokenType.DAY_OF_WEEK:
            self.unexpected_token(expected=[TokenType.DAY_OF_WEEK])

        dow_int_map = dict(
            sunday=0,
            sun=0,
            monday=1,
            mon=1,
            tuesday=2,
            tue=2,
            wednesday=3,
            wed=3,
            thursday=4,
            thu=4,
            friday=5,
            fri=5,
            saturday=6,
            sat=6,
        )
        days = [dow_int_map.get(self.lexer.token.lexeme.lower())]
        self.lexer.next_token()
        if self.lexer.token.type is TokenType.DASH:
            self.lexer.next_token()
            if self.lexer.token.type is not TokenType.DAY_OF_WEEK:
                self.unexpected_token(expected=[TokenType.DAY_OF_WEEK])
            last_day = dow_int_map.get(self.lexer.token.lexeme.lower())
            self.lexer.next_token()
            next_day = (days[0] + 1) % 7
            while days[-1] != last_day:
                days.append(next_day)
                next_day = (next_day + 1) % 7

        return days

    def parse_agendas(self) -> tp.List[Agenda]:
        """
        agendas : agendas agenda
                | agenda
        """

        agendas = []
        agendas.append(self.parse_agenda())
        while self.lexer.token.type in {TokenType.ALLOW, TokenType.FORBID}:
            agendas.append(self.parse_agenda())

        return agendas

    def parse_agenda(self) -> Agenda:
        """
        agenda : ALLOW intervals
               | FORBID intervals
        """

        if self.lexer.token.type is TokenType.ALLOW:
            self.lexer.next_token()
            intervals = self.parse_intervals()
            agenda = Agenda(intervals=intervals, directive=Directive.ALLOW)
        elif self.lexer.token.type is TokenType.FORBID:
            self.lexer.next_token()
            intervals = self.parse_intervals()
            agenda = Agenda(intervals=intervals, directive=Directive.FORBID)
        else:
            self.unexpected_token(expected=[TokenType.ALLOW, TokenType.FORBID])

        return agenda

    def parse_intervals(self) -> tp.List[Interval]:
        """
        intervals : intervals interval
                  | interval
        """

        intervals = []
        intervals.append(self.parse_interval())
        while self.lexer.token.type is TokenType.TIME or self.lexer.token.type is TokenType.DASH:
            intervals.append(self.parse_interval())

        return intervals

    def parse_interval(self) -> Interval:
        """
        interval : TIME '-' TIME
                 | '-' TIME
                 | TIME
        """

        if self.lexer.token.type is TokenType.TIME:
            start = Time.from_string(self.lexer.token.lexeme)
            self.lexer.next_token()
            if self.lexer.token.type is TokenType.DASH:
                self.lexer.next_token()
                if self.lexer.token.type is not TokenType.TIME:
                    self.unexpected_token(expected=[TokenType.TIME])
                end = Time.from_string(self.lexer.token.lexeme)
                self.lexer.next_token()
            else:
                end = Time.end_of_day()

        elif self.lexer.token.type is TokenType.DASH:
            self.lexer.next_token()
            if self.lexer.token.type is not TokenType.TIME:
                self.unexpected_token(expected=[TokenType.TIME])
            start = Time.start_of_day()
            end = Time.from_string(self.lexer.token.lexeme)
            self.lexer.next_token()

        else:
            self.unexpected_token(expected=[TokenType.TIME, TokenType.DASH])

        return Interval(start=start, end=end)

    def unexpected_token(self, expected: tp.Sequence[TokenType]):
        message = f"missing or unexpected token in token stream on line {self.lexer.lineno} column {self.lexer.column}"
        message += "\n\n"
        message += self.lexer.build_position_error_string()
        message += "\n\n"
        message += "expected one of: {}".format(", ".join(token_type.name for token_type in expected))
        message += "\n"
        message += f"got: {self.lexer.token.type.name}"
        raise exceptions.ParserError(message)
