from typing import Any, Sequence, Tuple

import pytest

from pyopath.xpath.AST.ast import (
    AnyKindTest,
    ASTNode,
    AxisStep,
    Literal,
    NameTest,
    PathOperator,
    PostfixExpr,
    Predicate,
)
from pyopath.xpath.AST.lexer import lex
from pyopath.xpath.AST.parser import parse

test_cases: Sequence[Tuple[str, Any]] = (
    # Basic axes and axes shortcuts
    ("child::a2", AxisStep("child", NameTest("a2"))),
    ("a2", AxisStep("child", NameTest("a2"))),
    ("attribute::a2", AxisStep("attribute", NameTest("a2"))),
    ("@a2", AxisStep("attribute", NameTest("a2"))),
    # Simple Path expressions
    ("a/b", PathOperator(AxisStep("child", NameTest("a")), AxisStep("child", NameTest("b")))),
    (
        "a/b/c",
        PathOperator(
            PathOperator(AxisStep("child", NameTest("a")), AxisStep("child", NameTest("b"))),
            AxisStep("child", NameTest("c")),
        ),
    ),
    # Descendants abbreviation
    (
        "a//b",
        PathOperator(
            PathOperator(AxisStep("child", NameTest("a")), AxisStep("descendant-or-self", AnyKindTest())),
            AxisStep("child", NameTest("b")),
        ),
    ),
    # Predicates
    ("a[1]", AxisStep("child", NameTest("a"), Predicate(Literal("1")))),
    ("a[1][b]", AxisStep("child", NameTest("a"), Predicate(Literal("1")), Predicate(AxisStep("child", NameTest("b"))))),
    ("a[b][1]", AxisStep("child", NameTest("a"), Predicate(AxisStep("child", NameTest("b"))), Predicate(Literal("1")))),
    ("a[b[1]]", AxisStep("child", NameTest("a"), Predicate(AxisStep("child", NameTest("b"), Predicate(Literal("1")))))),
    # PostFix filter
    ("1[b]", PostfixExpr(Literal("1"), Predicate(AxisStep("child", NameTest("b"))))),
    # Rooted expressions
    ("/a", ("ROOT", AxisStep("child", NameTest("a")))),
    ("//a", ("DESCENCANTS", AxisStep("child", NameTest("a")))),
    # ("child::a2/b", Path("a")),
    # ("a1/b", Path("a")),
    # ("2=2", Path(2 == 2)),
    # ("a.@b", Path("a")),
    # ("a[2]", Path("a")),
    #    ("a[b]", Conditions(Access("a"), Access("b"))),
)


@pytest.mark.parametrize("query, reference", test_cases)
def test_parser(query: str, reference: ASTNode):
    res = parse(query)
    tokens = list(lex(query))
    assert res, f"Failed to parse: {query}"
    if res != reference:
        print(query)
        print(tokens)
        print(res)
    assert res == reference, f"{res} != {reference}"
