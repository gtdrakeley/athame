import pathlib
import re
import tempfile

import pytest
from athame import exceptions
from athame.lexer import Lexer, Position, Token, TokenType


def test_from_file():
    inp = """
    this is
    test input
    """
    with tempfile.NamedTemporaryFile("w") as source_file:
        source_file.write(inp)
        source_file.flush()
        lexer1 = Lexer.from_file(source_file.name)
        lexer2 = Lexer.from_file(pathlib.Path(source_file.name))
        lexer1.source.seek(0)
        lexer2.source.seek(0)
        assert lexer1.source.read() == inp
        assert lexer2.source.read() == inp
        # explicitly delete lexers so their reference to the file won't
        # prevent the temp file context manager from deleting the file
        del lexer1
        del lexer2


def test_from_string():
    inp = """
    this is
    test input
    """
    lexer = Lexer.from_string(inp)
    lexer.source.seek(0)
    assert lexer.source.read() == inp


def test_next_token():
    inp = "allow"
    inp += "\n forbid"
    inp += "\n  sunday"
    inp += "\n   0123"
    inp += "\n    -"
    lexer = Lexer.from_string(inp)
    assert lexer.next_token() == Token(type=TokenType.ALLOW, lexeme="allow", position=Position(column=0, lineno=0))
    assert lexer.next_token() == Token(type=TokenType.FORBID, lexeme="forbid", position=Position(column=1, lineno=1))
    assert lexer.next_token() == Token(
        type=TokenType.DAY_OF_WEEK,
        lexeme="sunday",
        position=Position(column=2, lineno=2),
    )
    assert lexer.next_token() == Token(type=TokenType.TIME, lexeme="0123", position=Position(column=3, lineno=3))
    assert lexer.next_token() == Token(type=TokenType.DASH, lexeme="-", position=Position(column=4, lineno=4))
    assert lexer.next_token() == Token(type=TokenType.END_INPUT, lexeme="", position=Position(column=0, lineno=5))


def test_next_token_raises_LexerError_when_lexing_fails():
    lexer = Lexer.from_string("!")
    with pytest.raises(exceptions.LexerError):
        lexer.next_token()


@pytest.mark.parametrize(
    "inp,token",
    [
        ("allow", Token(type=TokenType.ALLOW, lexeme="allow", position=Position(column=0, lineno=0))),
        ("forbid", Token(type=TokenType.FORBID, lexeme="forbid", position=Position(column=0, lineno=0))),
        ("sunday", Token(type=TokenType.DAY_OF_WEEK, lexeme="sunday", position=Position(column=0, lineno=0))),
        ("sun", Token(type=TokenType.DAY_OF_WEEK, lexeme="sun", position=Position(column=0, lineno=0))),
        ("monday", Token(type=TokenType.DAY_OF_WEEK, lexeme="monday", position=Position(column=0, lineno=0))),
        ("mon", Token(type=TokenType.DAY_OF_WEEK, lexeme="mon", position=Position(column=0, lineno=0))),
        ("tuesday", Token(type=TokenType.DAY_OF_WEEK, lexeme="tuesday", position=Position(column=0, lineno=0))),
        ("tue", Token(type=TokenType.DAY_OF_WEEK, lexeme="tue", position=Position(column=0, lineno=0))),
        ("wednesday", Token(type=TokenType.DAY_OF_WEEK, lexeme="wednesday", position=Position(column=0, lineno=0))),
        ("wed", Token(type=TokenType.DAY_OF_WEEK, lexeme="wed", position=Position(column=0, lineno=0))),
        ("thursday", Token(type=TokenType.DAY_OF_WEEK, lexeme="thursday", position=Position(column=0, lineno=0))),
        ("thu", Token(type=TokenType.DAY_OF_WEEK, lexeme="thu", position=Position(column=0, lineno=0))),
        ("friday", Token(type=TokenType.DAY_OF_WEEK, lexeme="friday", position=Position(column=0, lineno=0))),
        ("fri", Token(type=TokenType.DAY_OF_WEEK, lexeme="fri", position=Position(column=0, lineno=0))),
        ("saturday", Token(type=TokenType.DAY_OF_WEEK, lexeme="saturday", position=Position(column=0, lineno=0))),
        ("sat", Token(type=TokenType.DAY_OF_WEEK, lexeme="sat", position=Position(column=0, lineno=0))),
    ],
)
def test_allow_or_forbid_or_day_of_week_token(inp, token):
    lexer = Lexer.from_string(inp)
    assert lexer.next_token() == token


@pytest.mark.parametrize("inp", ["all", "allowed"])
def test_allow_or_forbid_or_day_of_week_token_raises_LexerError_when_lexing_fails(inp):
    lexer = Lexer.from_string(inp)
    with pytest.raises(exceptions.LexerError):
        lexer.next_token()


@pytest.mark.parametrize(
    "inp,token",
    [
        ("0000", Token(type=TokenType.TIME, lexeme="0000", position=Position(column=0, lineno=0))),
        ("2359", Token(type=TokenType.TIME, lexeme="2359", position=Position(column=0, lineno=0))),
        ("0100", Token(type=TokenType.TIME, lexeme="0100", position=Position(column=0, lineno=0))),
        ("0017", Token(type=TokenType.TIME, lexeme="0017", position=Position(column=0, lineno=0))),
        ("1230", Token(type=TokenType.TIME, lexeme="1230", position=Position(column=0, lineno=0))),
    ],
)
def test_time_token(inp, token):
    lexer = Lexer.from_string(inp)
    assert lexer.next_token() == token


@pytest.mark.parametrize("inp", ["0060", "0099", "2400", "2410", "1260"])
def test_time_token_raises_LexerError_when_lexing_fails(inp):
    lexer = Lexer.from_string(inp)
    with pytest.raises(exceptions.LexerError):
        lexer.next_token()


def test_hour_partial():
    inp = "0023061016"
    lexer = Lexer.from_string(inp)
    buffer = ""
    while lexer.char != lexer.end_of_line:
        buffer += lexer.hour_partial()
    assert buffer == inp


@pytest.mark.parametrize("inp", ["24", "25", "26", "27", "28", "29"])
def test_hour_partial_raises_LexerError_when_lexing_fails(inp):
    lexer = Lexer.from_string(inp)
    with pytest.raises(exceptions.LexerError):
        lexer.hour_partial()


def test_minute_partial():
    inp = "0059011011"
    lexer = Lexer.from_string(inp)
    buffer = ""
    while lexer.char != lexer.end_of_line:
        buffer += lexer.minute_partial()
    assert buffer == inp


@pytest.mark.parametrize("inp", ["60", "70", "80", "90"])
def test_minute_partial_raises_LexerError_when_lexing_fails(inp):
    lexer = Lexer.from_string(inp)
    with pytest.raises(exceptions.LexerError):
        lexer.minute_partial()


@pytest.mark.parametrize("inp", ["a", " a", "\na", " \na", "\n a", "\n\na", "  a", "\n \n  \n   a"])
def test_skip_whitespace(inp):
    lexer = Lexer.from_string(inp)
    lexer.skip_whitespace()
    assert lexer.char == "a"


def test_next_line():
    inp = "a\nbc\ndef\n"
    lexer = Lexer.from_string(inp)
    assert lexer.line == "a\n"
    assert lexer.char == "a"
    assert lexer.lineno == 0
    lexer.next_line()
    assert lexer.line == "bc\n"
    assert lexer.char == "b"
    assert lexer.lineno == 1
    lexer.next_line()
    assert lexer.line == "def\n"
    assert lexer.char == "d"
    assert lexer.lineno == 2
    lexer.column = 100
    lexer.next_line()
    assert lexer.column == 0


def test_next_char():
    lexer = Lexer.from_string("abc")
    assert lexer.next_char() == "b"
    assert lexer.column == 1
    assert lexer.next_char() == "c"
    assert lexer.column == 2
    assert lexer.next_char() == lexer.end_of_line
    assert lexer.column == 3
    assert lexer.next_char() == lexer.end_of_line
    assert lexer.column == 4


@pytest.mark.parametrize("inp,identifier", [("a", "a"), ("abcd", "abcd"), ("ab cd", "ab")])
def test_extract_ascii_identifier(inp, identifier):
    lexer = Lexer.from_string(inp)
    assert lexer.extract_ascii_identifier() == identifier


def test_mark_position():
    lexer = Lexer.from_string("")
    lexer.column = 42
    lexer.lineno = 123
    lexer.mark_position()
    assert lexer.position == Position(column=42, lineno=123)


# regular expressions are high magic
# in this test we are checking that the arrow is pointing to the char we expect
# we are also checking for line length truncations when applicable
@pytest.mark.parametrize(
    "inp,shift,pattern_string",
    [
        ("a", 0, r".+\n\n {5}a\n {5}\^"),  # easy case
        ("abcd", 0, r".+\n\n {5}abcd\n {5}\^"),  # multiple characters
        ("abcd", 3, r".+\n\n {5}abcd\n {8}\^"),  # passed first character in line
        (r" " * 100 + r"a" * 100 + r" " * 100, 150, r".+\n\n {5}" + r"a" * 80 + r"\n {44}\^"),  # truncating huge line
    ],
)
def test_unexpected_char_error(inp, shift, pattern_string):
    lexer = Lexer.from_string(inp)
    pattern = re.compile(pattern_string, re.MULTILINE)
    for _ in range(shift):
        lexer.next_char()

    with pytest.raises(exceptions.LexerError) as excinfo:
        lexer.unexpected_char_error()

    assert pattern.match(excinfo.value.message) is not None


@pytest.mark.parametrize(
    "offset,pattern_string",
    [
        (-3, r".+\n\n {5}0123456789\n {7}\^"),  # char should be '2' offset -3 from '5'
        (3, r".+\n\n {5}0123456789\n {13}\^"),  # char should be '8' offset +3 from '5'
    ],
)
def test_unexpected_char_error_with_offset(offset, pattern_string):
    lexer = Lexer.from_string("0123456789")
    pattern = re.compile(pattern_string, re.MULTILINE)
    for _ in range(5):
        lexer.next_char()

    with pytest.raises(exceptions.LexerError) as excinfo:
        lexer.unexpected_char_error(offset=offset)

    assert pattern.match(excinfo.value.message) is not None


def test_unexpected_char_error_with_expected():
    lexer = Lexer.from_string("a")

    with pytest.raises(exceptions.LexerError) as excinfo:
        lexer.unexpected_char_error(expected=["a"])

    assert excinfo.value.message.endswith("expected one of: 'a'")

    with pytest.raises(exceptions.LexerError) as excinfo:
        lexer.unexpected_char_error(expected=["b", "a"])

    assert excinfo.value.message.endswith("expected one of: 'b', 'a'")


@pytest.mark.parametrize(
    "inp,column,pattern_string",
    [
        ("0123456789", 0, r" {5}0123456789\n {5}\^"),  # beginning
        ("0123456789", 1, r" {5}0123456789\n {6}\^"),  # shift
        ("0123456789", 9, r" {5}0123456789\n {14}\^"),  # end
        (" " * 100 + "a" * 40 + " " * 100, 119, r" {25}a{40} {20}\n {44}\^"),  # truncated
    ],
)
def test_build_error_string(inp, column, pattern_string):
    lexer = Lexer.from_string(inp)
    pattern = re.compile(pattern_string, re.MULTILINE)
    assert pattern.match(lexer.build_error_string(column)) is not None
