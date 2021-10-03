from unittest import mock

from athame.trie import Trie


def test_from_strings():
    strings = ["abcd", "abcde", "acde"]
    with mock.patch.object(Trie, "add") as mock_add:
        Trie.from_strings(*strings)

    calls = [mock.call(string) for string in strings]
    mock_add.assert_has_calls(calls)


def test___contains__():
    trie = Trie.from_strings("abcd")
    assert "abcd" in trie
    assert "abc" not in trie
    assert "abcde" not in trie
    assert "zzzz" not in trie
    assert "" not in trie


def test_add():
    trie = Trie()

    trie.add("ab")
    assert "a" in trie.root
    assert "b" in trie.root["a"]
    assert not trie.root["a"]["is_terminal"]
    assert trie.root["a"]["b"]["is_terminal"]

    trie.add("abc")
    assert not trie.root["a"]["is_terminal"]
    assert "c" in trie.root["a"]["b"]
    assert trie.root["a"]["b"]["c"]["is_terminal"]

    trie.add("a")
    assert trie.root["a"]["is_terminal"]


def test_contains_prefix():
    trie = Trie.from_strings("abcd")
    assert trie.contains_prefix("a")
    assert trie.contains_prefix("ab")
    assert trie.contains_prefix("abc")
    assert trie.contains_prefix("abcd")
    assert not trie.contains_prefix("abcde")
    assert not trie.contains_prefix("z")


def test_chars_after():
    trie = Trie.from_strings("prefix", "prerelease", "preordain")
    assert trie.chars_after("pre") == ["f", "o", "r"]
    assert trie.chars_after("q") == []


def test_max_match_for():
    trie = Trie.from_strings("prefix", "preface")
    assert trie.max_match_for("pre") == "pre"
    assert trie.max_match_for("preordain") == "pre"
    assert trie.max_match_for("prefrontal") == "pref"
    assert trie.max_match_for("zzzz") == ""
    assert trie.max_match_for("") == ""
