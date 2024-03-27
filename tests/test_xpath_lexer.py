from typing import Any, Sequence, Tuple

import pytest

from pyopath.xpath.AST.lexer import lex

test_cases: Sequence[Tuple[str, Any]] = (
    ("a", (("EQNAME", "a"),)),
    ("/", (("SLASH", "/"),)),
    ("a/b", (("EQNAME", "a"), ("SLASH", "/"), ("EQNAME", "b"))),
    ("child::a", (("CHILD", "child"), ("AXIS", "::"), ("EQNAME", "a"))),
    ("child::a[2]", (("CHILD", "child"), ("AXIS", "::"), ("EQNAME", "a"), ("[", "["), ("NUMBER", "2"), ("]", "]"))),
    ("@a", (("@", "@"), ("EQNAME", "a"))),
    ("/a", (("SLASH", "/"), ("EQNAME", "a"))),
    ("//a", (("DOUBLESLASH", "//"), ("EQNAME", "a"))),
    ("text()", (("TEXT", "text"), ("(", "("), (")", ")"))),
    ("a==b", (("EQNAME", "a"), ("EQsym", "=="), ("EQNAME", "b"))),
    ("a||b||c", (("EQNAME", "a"), ("CONCAT", "||"), ("EQNAME", "b"), ("CONCAT", "||"), ("EQNAME", "c"))),
    ("9 to 5", (("NUMBER", "9"), ("TO", " to "), ("NUMBER", "5"))),
    ("'hello'", (("STRING", "hello"),)),
    ('"hello"', (("STRING", "hello"),)),
    ("$variable", (("$", "$"), ("EQNAME", "variable"))),
)


@pytest.mark.parametrize("query, reference", test_cases)
def test_lexer(query: str, reference: Tuple[str, str]):
    res = tuple(list((res.type, res.value) for res in lex(query)))
    if res != reference:
        print(query)
        print(res)
        assert res == reference
