from __future__ import annotations

import typing as tp


class Trie:
    """
    A Trie (pronounced "try"), also known as a Prefix Tree, is a search tree for looking
    up specific keys from within a set. For our implementation our keys will be
    case-insensitive strings.

    More reading can be done here: https://en.wikipedia.org/wiki/Trie
    """

    def __init__(self):
        self.root = dict()

    @classmethod
    def from_strings(cls, *strings: tp.Sequence[str]) -> Trie:
        trie = cls()
        for string in strings:
            trie.add(string)
        return trie

    def __contains__(self, string: str) -> bool:
        string = string.lower()
        current = self.root
        for char in string:
            if (current := current.get(char)) is None:
                return False
        return current.get("is_terminal")

    def add(self, string: str):
        string = string.lower()
        current = self.root
        for char in string:
            current = current.setdefault(char, dict(is_terminal=False))
        current["is_terminal"] = True

    def contains_prefix(self, string: str) -> bool:
        string = string.lower()
        current = self.root
        for char in string:
            if (current := current.get(char)) is None:
                return False
        return True

    def chars_after(self, string: str) -> tp.List[str]:
        string = string.lower()
        current = self.root
        for char in string:
            if (current := current.get(char)) is None:
                return []
        return sorted(char for char in current if char != "is_terminal")

    def max_match_for(self, string: str) -> str:
        string = string.lower()
        buffer = ""
        current = self.root
        for char in string:
            if (current := current.get(char)) is None:
                return buffer
            buffer += char
        return buffer
