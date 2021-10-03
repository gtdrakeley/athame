from __future__ import annotations

import enum
import io
import pathlib
import typing as tp
from string import ascii_letters

from athame import exceptions
from athame.trie import Trie
from pydantic import BaseModel


class TokenType(enum.Enum):
    END_INPUT = enum.auto()
    ALLOW = enum.auto()
    FORBID = enum.auto()
    DAY_OF_WEEK = enum.auto()
    TIME = enum.auto()
    DASH = enum.auto()


class Position(BaseModel):
    column: int
    lineno: int


class Token(BaseModel):
    type: TokenType
    lexeme: str
    position: Position


class Lexer:
    HOUR_STARTS = ("0", "1", "2")
    HOUR_ENDS = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    HOUR_ENDS_2X = ("0", "1", "2", "3")
    MINUTE_STARTS = ("0", "1", "2", "3", "4", "5")
    MINUTE_ENDS = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    DAYS_OF_WEEK = (
        "sunday",
        "sun",
        "monday",
        "mon",
        "tuesday",
        "tue",
        "wednesday",
        "wed",
        "thursday",
        "thu",
        "friday",
        "fri",
        "saturday",
        "sat",
    )
    KEYWORDS = Trie.from_strings("allow", "forbid", *DAYS_OF_WEEK)

    def __init__(self, source: tp.TextIO, *, whitespace: str = " \t\f", end_of_line: str = "\n"):
        self.source = source
        self.whitespace = set(whitespace)
        self.end_of_line = end_of_line
        self.line: str = self.source.readline()
        self.char: tp.Optional[str] = None
        self.lineno = 0
        self.column = -1
        self.token: tp.Optional[Token] = None
        self.position: Position = None

        self.next_char()

    @classmethod
    def from_file(cls, file: tp.Union[str, pathlib.Path], **kwargs) -> Lexer:
        if isinstance(file, str):
            file = pathlib.Path(file)

        return cls(file.resolve().open("r"), **kwargs)

    @classmethod
    def from_string(cls, string: str, **kwargs) -> Lexer:
        source = io.StringIO(string)
        return cls(source, **kwargs)

    def next_token(self) -> Token:
        self.token = None
        self.skip_whitespace()
        self.mark_position()

        if self.char is None:
            self.next_char()
            self.token = Token(type=TokenType.END_INPUT, lexeme="", position=self.position)
        elif Lexer.is_ascii_identifier_start(self.char):
            self.allow_or_forbid_or_day_of_week_token()
        elif Lexer.is_hour_start(self.char):
            self.time_token()
        elif self.char == "-":
            self.next_char()
            self.token = Token(type=TokenType.DASH, lexeme="-", position=self.position)

        if self.token is None:
            self.unexpected_char_error()

        return self.token

    def allow_or_forbid_or_day_of_week_token(self):
        lexeme = self.extract_ascii_identifier()

        if lexeme not in Lexer.KEYWORDS:
            if Lexer.KEYWORDS.contains_prefix(lexeme):
                expected = Lexer.KEYWORDS.chars_after(lexeme)
                self.unexpected_char_error(expected=expected)

            max_match = Lexer.KEYWORDS.max_match_for(lexeme)
            offset = len(max_match) - len(lexeme)
            self.unexpected_char_error(offset=offset)

        if lexeme.lower() == "allow":
            self.token = Token(type=TokenType.ALLOW, lexeme=lexeme, position=self.position)
        elif lexeme.lower() == "forbid":
            self.token = Token(type=TokenType.FORBID, lexeme=lexeme, position=self.position)
        elif lexeme.lower() in Lexer.DAYS_OF_WEEK:
            self.token = Token(type=TokenType.DAY_OF_WEEK, lexeme=lexeme, position=self.position)

    def time_token(self):
        hour_part = self.hour_partial()
        minute_part = self.minute_partial()
        lexeme = hour_part + minute_part
        self.token = Token(type=TokenType.TIME, lexeme=lexeme, position=self.position)

    def hour_partial(self) -> str:
        buffer = self.char
        self.next_char()
        if not Lexer.is_hour_end(self.char, hour=buffer):
            expected = Lexer.HOUR_ENDS_2X if buffer == "2" else Lexer.HOUR_ENDS
            self.unexpected_char_error(expected=expected)
        buffer += self.char
        self.next_char()
        return buffer

    def minute_partial(self) -> str:
        if not Lexer.is_minute_start(self.char):
            self.unexpected_char_error(expected=Lexer.MINUTE_STARTS)
        buffer = self.char
        self.next_char()
        if not Lexer.is_minute_end(self.char):
            self.unexpected_char_error(expected=Lexer.MINUTE_ENDS)
        buffer += self.char
        self.next_char()
        return buffer

    def skip_whitespace(self):
        while self.char in self.whitespace or self.char == self.end_of_line:
            if self.char == self.end_of_line:
                self.next_line()
            else:
                self.next_char()

    def next_line(self):
        self.line = self.source.readline()
        self.column = -1
        self.lineno += 1
        self.next_char()

    def next_char(self) -> str:
        if not self.line:
            self.column = 0
            self.char = None
        elif self.column + 1 >= len(self.line):
            self.char = self.end_of_line
            self.column += 1
        else:
            self.column += 1
            self.char = self.line[self.column]

        return self.char

    def extract_ascii_identifier(self) -> str:
        start = self.column
        while self.char and self.char in ascii_letters:
            self.next_char()
        return self.line[start : self.column]

    def mark_position(self):
        self.position = Position(column=self.column, lineno=self.lineno)

    def unexpected_char_error(self, *, expected: tp.Sequence[str] = None, offset: int = 0):
        column = self.column + offset
        message = f"missing or unexpected character in input stream on line {self.lineno} column {column}"
        message += "\n\n"
        message += self.build_error_string(column)

        if expected is not None:
            message += "\n\n"
            message += "expected one of: {}".format(", ".join(f"'{exp}'" for exp in expected))

        raise exceptions.LexerError(message)

    def build_error_string(self, column: int) -> str:
        # max line characters to display 80, prefer arrow left of center when truncating
        col_start = max(0, column - 39)
        line_part = self.line[col_start : col_start + 80].rstrip(self.end_of_line)
        arrow_part = " " * (column - col_start) + "^"
        padding = " " * 5
        error_string = padding + line_part
        error_string += "\n"
        error_string += padding + arrow_part
        return error_string

    def build_position_error_string(self) -> str:
        return self.build_error_string(self.position.column)

    @staticmethod
    def is_ascii_identifier_start(char: str) -> bool:
        return char in ascii_letters

    @staticmethod
    def is_hour_start(char: str) -> bool:
        return char in Lexer.HOUR_STARTS

    @staticmethod
    def is_hour_end(char: str, hour: str):
        return char in Lexer.HOUR_ENDS_2X if hour == "2" else char in Lexer.HOUR_ENDS

    @staticmethod
    def is_minute_start(char: str) -> bool:
        return char in Lexer.MINUTE_STARTS

    @staticmethod
    def is_minute_end(char: str) -> bool:
        return char in Lexer.MINUTE_ENDS
