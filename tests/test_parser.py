from typing import Any, Sequence, Tuple

import pytest

from pyopath.AST.ast import Path, PathyInterface
from pyopath.AST.lexer import lex
from pyopath.AST.parser import parse

Path(None)

test_cases: Sequence[Tuple[str, Any]] = (
    # Basic axes and axes shortcuts
    ("child::a2", ("PATH", ("AXISSTEP", (("FORWARD", "child"), ("NAME_TEST", "a2")), ("PREDLIST",)))),
    ("a2", ("PATH", ("AXISSTEP", (("FORWARD", "child"), ("NAME_TEST", "a2")), ("PREDLIST",)))),
    ("attribute::a2", ("PATH", ("AXISSTEP", (("FORWARD", "attribute"), ("NAME_TEST", "a2")), ("PREDLIST",)))),
    ("@a2", ("PATH", ("AXISSTEP", (("FORWARD", "attribute"), ("NAME_TEST", "a2")), ("PREDLIST",)))),
    # Rooted expressions
    ("/a", ("PATH", ("ROOT", ("AXISSTEP", (("FORWARD", "child"), ("NAME_TEST", "a")), ("PREDLIST",))))),
    ("//a", ("PATH", ("DESCENCANTS", ("AXISSTEP", (("FORWARD", "child"), ("NAME_TEST", "a")), ("PREDLIST",))))),
    # ("child::a2/b", Path("a")),
    # ("a1/b", Path("a")),
    # ("2=2", Path(2 == 2)),
    # ("a.@b", Path("a")),
    # ("a[2]", Path("a")),
    #    ("a[b]", Conditions(Access("a"), Access("b"))),
)


@pytest.mark.parametrize("query, reference", test_cases)
def test_parser(query: str, reference: PathyInterface):
    res = parse(query)
    tokens = list(lex(query))
    assert res, f"Failed to parse: {query}"
    if res != reference:
        print(query)
        print(tokens)
        print(res)
    assert res == reference, f"{res} != {reference}"
