from typing import Any, Sequence, Tuple

import pytest

from pyopath.xpath.AST.ast import (
    AnyKindTest,
    ASTNode,
    AxisStep,
    Context,
    Literal,
    NameTest,
    PathOperator,
    PostfixExpr,
    Predicate,
    TextTest,
)
from pyopath.xpath.AST.lexer import lex
from pyopath.xpath.AST.parser import parse

test_cases: Sequence[Tuple[str, Any]] = (
    # Literals
    ("1", Literal(1)),
    ("1.5", Literal(1.5)),
    # Context
    (".", Context()),
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
    ("a[1]", AxisStep("child", NameTest("a"), Predicate(Literal(1)))),
    ("a[1][b]", AxisStep("child", NameTest("a"), Predicate(Literal(1)), Predicate(AxisStep("child", NameTest("b"))))),
    ("a[b][1]", AxisStep("child", NameTest("a"), Predicate(AxisStep("child", NameTest("b"))), Predicate(Literal(1)))),
    ("a[b[1]]", AxisStep("child", NameTest("a"), Predicate(AxisStep("child", NameTest("b"), Predicate(Literal(1)))))),
    # PostFix filter
    ("1[b]", PostfixExpr(Literal(1), Predicate(AxisStep("child", NameTest("b"))))),
    # Parenthesisesses
    ("(1)", Literal(1)),
    ("1/(2/3)", PathOperator(Literal(1), PathOperator(Literal(2), Literal(3)))),
    ("(1/2)/3", PathOperator(PathOperator(Literal(1), Literal(2)), Literal(3))),
    # text-node-test
    ("self::text()", AxisStep("self", TextTest())),
    ("text()", AxisStep("child", TextTest())),
    ## Rooted expressions
    # ("/a", ("ROOT", AxisStep("child", NameTest("a")))),
    # ("//a", ("DESCENCANTS", AxisStep("child", NameTest("a")))),
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
