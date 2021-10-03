import pendulum
from athame.ast import Schedule
from athame.lexer import Lexer
from athame.parser import Parser


def from_dsl(string: str, tz: str = pendulum.local_timezone().name) -> Schedule:
    lexer = Lexer.from_string(string)
    parser = Parser(lexer)
    schedule = parser.parse()
    schedule.tz = tz
    return schedule
