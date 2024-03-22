"""
Interpreter? Executor? Executionist? Doer? Doer!
"""

from math import isnan
from typing import Any, Callable, Dict, Generator, Mapping, Optional, Sequence, cast

from typing_extensions import Self

from pyopath.xpath.AST.ast import ASTNode, AxisStep, NameTest, NodeTest, Predicate
from pyopath.xpath.AST.parser import parse


class StaticContext:
    """
    https://www.w3.org/TR/xpath-31/#context
    [Definition: The expression context for a given expression consists of all
     the information that can affect the result of the expression.]
    """

    varibles: Dict[str, Any]
    functions: Dict[str, Callable[..., Any]]

    def __init__(self):
        self.varibles = dict()
        self.functions = dict()

    def copy_static_context(self, other: "StaticContext") -> Self:
        self.varibles = dict(other.varibles)
        self.functions = dict(other.functions)
        return self


class DynamicContext(StaticContext):
    """
    https://www.w3.org/TR/xpath-31/#eval_context
    [Definition: The dynamic context of an expression is defined as information
     that is needed for the dynamic evaluation of an expression.]
    If evaluation of an expression relies on some part of the dynamic
     context that is absent, a dynamic error is raised [err:XPDY0002].
    """

    item: Any
    position: int
    size: Optional[int]
    name: Optional[str]

    def __init__(
        self, static: StaticContext, item: Any, position: int, size: Optional[int] = None, name: Optional[str] = None
    ):
        self.copy_static_context(static)
        self.item = item
        self.position = position
        self.size = size
        self.name = name


ATOMIC_TYPES = [int, str, float, bytes]


def is_atomic(data: Any) -> bool:
    return type(data) in ATOMIC_TYPES


def is_node(data: Any) -> bool:
    return not is_atomic(data) and not isinstance(data, (Sequence, Mapping))


def assert_is_node(data: Any):
    if not is_node(data):
        raise TypeError(
            f"Attempting to perform axis step on non-nodetype {type(data)}. Registered atomics are {ATOMIC_TYPES}"
        )


def enumerate_items(data: DynamicContext) -> Generator[DynamicContext, None, None]:
    # ensure it is an object
    assert_is_node(data.item)
    item = data.item

    dir_entries = dir(item)
    dir_len = len(dir_entries)
    for zindex, name in enumerate(dir_entries):
        value = getattr(item, name)
        yield DynamicContext(data, value, zindex + 1, dir_len, name=name)

    return

    if isinstance(item, Sequence):
        lst = cast(Sequence[Any], item)
        length = len(lst)
        for index, value in enumerate(lst):
            yield DynamicContext(data, value, index, length)
        return
    if isinstance(item, Mapping):
        ...


def nodetest(data: DynamicContext, test: NodeTest) -> bool:
    if isinstance(test, NameTest):
        return data.name == test.name
    assert False, f"Support for nodetest {type(test)} not implemented yet"


def nodetest_filter(
    items: Generator[DynamicContext, None, None], test: NodeTest
) -> Generator[DynamicContext, None, None]:
    while True:
        item = next(items, None)
        if item is None:
            return
        if nodetest(item, test):
            yield item


def effective_boolean(items: Generator[DynamicContext, None, None]) -> bool:
    """
    https://www.w3.org/TR/xpath-31/#id-ebv
    """

    try:
        val0 = next(items)
    except StopIteration:
        # Empty sequence -> False
        return False

    # Sequence of nodes: True
    if is_node(val0):
        return True

    # Sneaky way to check that it is a "singleton type" (1-sequence of atomic type)
    try:
        next(items)
    except StopIteration:
        if isinstance(val0, bool):
            return val0
        if isinstance(val0, str):
            return len(val0) != 0
        if isinstance(val0, (int, float)):
            return False if val0 == 0 or isnan(val0) else True
    raise TypeError("Could not reduce to effective boolean value!")


def predicate_filter(
    items: Generator[DynamicContext, None, None], predicate: Predicate
) -> Generator[DynamicContext, None, None]:
    while True:
        item = next(items, None)
        if item is None:
            return
        if effective_boolean(evaluate_node(predicate.predicate, item)):
            yield item


def evaluate_axis(node: AxisStep, data: DynamicContext) -> Generator[DynamicContext, None, None]:
    assert_is_node(data.item)

    if node.axis == "child":
        items: Generator[DynamicContext, None, None] = enumerate_items(data)
        items = nodetest_filter(items, node.nodetest)
        if node.predicates:
            for predicate in node.predicates:
                items = predicate_filter(items, predicate)
        for item in items:
            yield item


def evaluate_node(node: ASTNode, data: DynamicContext) -> Generator[DynamicContext, None, None]:
    if isinstance(node, AxisStep):
        yield from evaluate_axis(node, data)

    assert False, f"evalute not implemented for nodetype {type(node)}"


def evaluate(node: ASTNode, data: DynamicContext) -> Sequence[Any]:
    return list(data.item for data in evaluate_node(node, data))


def query(data: Any, query: str) -> Sequence[Any]:
    ast: ASTNode = parse(query)

    context: DynamicContext = DynamicContext(StaticContext(), data, 1, 1)

    return evaluate(ast, context)
