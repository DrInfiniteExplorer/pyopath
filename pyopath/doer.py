"""
Interpreter? Executor? Executionist? Doer? Doer!
"""

from inspect import signature
from math import isnan
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Sequence, Tuple, cast

from typing_extensions import Self

from pyopath.nodewrappers.base import NodeBase, TextBase, attributes, children, node_name, string_value, unwrap
from pyopath.nodewrappers.registry import wrap
from pyopath.xpath.AST.ast import (
    AnyKindTest,
    ASTNode,
    AxisStep,
    Compare,
    Context,
    Literal,
    NameTest,
    NodeTest,
    PathOperator,
    Predicate,
    StaticFunctionCall,
    TextTest,
)
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
    return isinstance(data, NodeBase)


def assert_is_node(data: Any):
    if not is_node(data):
        raise TypeError(
            f"Attempting to perform axis step on non-nodetype {type(data)}. Registered atomics are {ATOMIC_TYPES}"
        )


ItemGenerator = Generator[DynamicContext, None, None]


def empty_sequence_generator() -> ItemGenerator:
    if False:
        yield None


def atomic_sequence_generator(item: DynamicContext) -> ItemGenerator:
    # TODO: check item type?
    yield item


def peek_atomic(sequence: ItemGenerator) -> Tuple[ItemGenerator, Optional[DynamicContext]]:
    """
    Checks if the sequence contains 1 item.
    TODO: Maybe should check if the sequence-type is also just 1 item?
    """
    try:
        val0 = next(sequence)
    except StopIteration:
        return empty_sequence_generator(), None
    try:
        val1 = next(sequence)
    except StopIteration:
        return atomic_sequence_generator(val0), val0

    def restart() -> ItemGenerator:
        yield val0
        yield val1
        yield from sequence

    return restart(), None


def rescope_sequence(items: ItemGenerator, stream: bool = False) -> ItemGenerator:
    if stream:
        cnt = 1
        for item in items:
            yield DynamicContext(item, item.item, cnt, None, item.name)
            cnt += 1
        return
    item_list: List[DynamicContext] = list(items)
    item_count = len(item_list)
    for zindex, item in enumerate(item_list):
        yield DynamicContext(item, item.item, zindex + 1, item_count, item.name)


def enumerate_children(data: DynamicContext, stream: bool = False) -> ItemGenerator:
    # ensure it is an object
    assert_is_node(data.item)
    kids = children(cast(NodeBase, data.item))

    total = None
    if not stream:
        kids = list(kids)
        total = len(kids)
    cnt = 1
    for child in kids:
        yield DynamicContext(data, child, cnt, total, name=node_name(child))
        cnt += 1
    return

    item = data.item

    mapping_entries: list[Any] = list(item.keys()) if isinstance(item, Mapping) else []
    mapping_length = len(mapping_entries)

    dir_entries = dir(item)
    dir_len = len(dir_entries)

    total_len = mapping_length + dir_len

    for zindex, name in enumerate(dir_entries):
        value = getattr(item, name)
        yield DynamicContext(data, value, zindex + 1, total_len, name=name)

    for zindex, name in enumerate(mapping_entries):
        value: Any = item.get(name)
        yield DynamicContext(data, value, dir_len + zindex + 1, total_len, name=name)

    return

    if isinstance(item, Sequence):
        lst = cast(Sequence[Any], item)
        length = len(lst)
        for index, value in enumerate(lst):
            yield DynamicContext(data, value, index, length)
        return
    if isinstance(item, Mapping):
        ...


def enumerate_attributes(data: DynamicContext, stream: bool = False) -> ItemGenerator:
    # ensure it is an object
    assert_is_node(data.item)
    kids = attributes(cast(NodeBase, data.item))

    total = None
    if not stream:
        kids = list(kids)
        total = len(kids)
    cnt = 1
    for child in kids:
        yield DynamicContext(data, child, cnt, total, name=node_name(child))
        cnt += 1
    return


def nodetest(data: DynamicContext, test: NodeTest) -> bool:
    if isinstance(test, NameTest):
        return data.name == test.name
    elif isinstance(test, AnyKindTest):
        return True
    elif isinstance(test, TextTest):
        return isinstance(data.item, TextBase)
    else:
        assert False, f"Support for nodetest {type(test)} not implemented yet"


def nodetest_filter(sequence: ItemGenerator, test: NodeTest, stream: bool = False) -> ItemGenerator:
    def filt(items: ItemGenerator) -> ItemGenerator:
        while True:
            item = next(items, None)
            if item is None:
                return
            if nodetest(item, test):
                yield item
                continue

    sequence = filt(sequence)
    sequence = rescope_sequence(sequence, stream=stream)
    return sequence


def effective_boolean(items: ItemGenerator) -> bool:
    """
    https://www.w3.org/TR/xpath-31/#id-ebv
    """

    atomic: Optional[DynamicContext]
    items, atomic = peek_atomic(items)

    if not atomic:
        return False

    val0: Any = atomic.item
    if is_node(val0):
        return True
    if isinstance(val0, bool):
        return val0
    if isinstance(val0, str):
        return len(val0) != 0
    if isinstance(val0, (int, float)):
        return False if val0 == 0 or isnan(val0) else True

    raise TypeError("Could not reduce to effective boolean value!")


def predicate_filter_impl(items: ItemGenerator, predicate: Predicate) -> ItemGenerator:
    """
    https://www.w3.org/TR/xpath-31/#id-filter-expression
    """
    while True:
        item = next(items, None)
        if item is None:
            return
        predicate_results = evaluate_ast_node(predicate.predicate, item)
        predicate_results, atomic = peek_atomic(predicate_results)
        if atomic and isinstance(atomic.item, (int, float)):
            if atomic.item == item.position:
                yield item
            continue
        if effective_boolean(predicate_results):
            yield item
            continue


def predicate_filter(items: ItemGenerator, predicate: Predicate, stream: bool = False) -> ItemGenerator:
    items = predicate_filter_impl(items, predicate)
    items = rescope_sequence(items, stream=stream)
    return items


def evaluate_axis(node: AxisStep, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    assert_is_node(data.item)

    if node.axis == "child":
        items: ItemGenerator = enumerate_children(data, stream=stream)
    elif node.axis == "attribute":
        items = enumerate_attributes(data, stream=stream)
    else:
        assert False, f"Axis not implemented for {node.axis}"

    items = nodetest_filter(items, node.nodetest, stream=stream)
    if node.predicates:
        for predicate in node.predicates:
            items = predicate_filter(items, predicate, stream=stream)
    yield from items


def path_operator(node: PathOperator, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    def work() -> ItemGenerator:
        lhs = evaluate_ast_node(node.a, data, stream=stream)
        # The path operator is defined to explicitly collect everything left-hand-side
        #  before applying right-hand-side
        # But then, how does that work with streaming? Who knows? Not me right now.
        lhs = rescope_sequence(lhs, stream=False)
        for item in lhs:
            yield from evaluate_ast_node(node.b, item, stream=stream)

    yield from rescope_sequence(work(), stream=False)


def static_function_call(node: StaticFunctionCall, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    function_name = node.name

    function = data.functions.get(function_name, None)
    if not function:
        # Should be detected during AST evaluation start
        raise ValueError(f"There is no function called {function_name}.")

    sig = signature(function)

    bound = sig.bind()

    for param in sig.parameters:
        print(param)
    asd()

    if len(sig.parameters) != len(node.arguments):
        # TODO: Should also be detected during AST evaluation start
        raise ValueError(
            f"Mismatching arguments to {function_name}. Expected {len(sig.parameters)}, got {node.arguments}."
        )


def dynamic_function_call():
    """
    If FC is a dynamic function call: FC's base expression is evaluated with respect to SC and DC.
    If this yields a sequence consisting of a single function with the same arity as the arity
     of the ArgumentList, let F denote that function. Otherwise, a type error is raised [err:XPTY0004].
    """
    ...


def compare(node: Compare, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    """
    There is difference in how value and general comparison (eq, ==) are evaluated.
    https://www.w3.org/TR/xpath-31/#id-comparisons
    """
    lhs = evaluate_ast_node(node.lhs, data, stream=stream)
    rhs = evaluate_ast_node(node.rhs, data, stream=stream)


def evaluate_ast_node(node: ASTNode, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    assert isinstance(node, ASTNode), f"{node} is not an ASTNode"
    assert isinstance(data, DynamicContext), f"{data} is not a DynamicContext"

    if isinstance(node, AxisStep):
        yield from evaluate_axis(node, data, stream=stream)
    elif isinstance(node, Literal):
        yield DynamicContext(data, node.value, 1, 1, None)
    elif isinstance(node, Context):
        yield data
        return

    elif isinstance(node, PathOperator):
        yield from path_operator(node, data, stream=stream)

    elif isinstance(node, StaticFunctionCall):
        yield from static_function_call(node, data, stream=stream)

    elif isinstance(node, Compare):
        yield from compare(node, data, stream=stream)

    else:
        assert False, f"evalute not implemented for nodetype {type(node)}"


def evaluate(node: ASTNode, data: DynamicContext) -> Sequence[Any]:
    return list(data.item for data in evaluate_ast_node(node, data))


def query(
    data: Any, query: str, unwrap_nodes: bool = True, static_context: Optional[StaticContext] = None
) -> Sequence[Any]:
    ast: ASTNode = parse(query)

    wrapped = wrap(data)

    if not static_context:
        static_context = StaticContext()
        static_context.functions["string"] = string_value

    context: DynamicContext = DynamicContext(static_context, wrapped, 1, 1)

    result = evaluate(ast, context)

    if unwrap_nodes:
        result = [unwrap(node) if isinstance(node, NodeBase) else node for node in result]

    return result
