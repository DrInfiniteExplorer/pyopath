"""
Interpreter? Executor? Executionist? Doer? Doer!
"""

from inspect import signature
from math import isnan
from typing import Any, Callable, Dict, Generator, List, Mapping, Optional, Sequence, Tuple, cast

from typing_extensions import Self

from pyopath.nodewrappers.base import (
    NodeBase,
    TextBase,
    attributes,
    children,
    node_name,
    string_value,
    typed_value,
    unwrap,
)
from pyopath.nodewrappers.registry import wrap
from pyopath.xpath.AST.ast import (
    AnyKindTest,
    ASTNode,
    AxisStep,
    Context,
    Literal,
    NameTest,
    NodeTest,
    PathOperator,
    Predicate,
    StaticFunctionCall,
    TextTest,
    ValueCompare,
    VarRef,
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

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        self.varibles = (variables or dict()).copy()
        self.functions = dict()

    def copy_static_context(self, other: "StaticContext") -> Self:
        self.varibles = other.varibles.copy()
        self.functions = other.functions.copy()
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


def atomic_sequence(item: DynamicContext) -> ItemGenerator:
    yield item


def atomize_sequence(items: ItemGenerator, stream: bool = False) -> ItemGenerator:
    """
    https://www.w3.org/TR/xpath-31/#id-atomization
    """
    for item in items:
        if is_atomic(item.item):
            yield item
        elif is_node(item.item):
            # A sequence can not contain a sequence, it is flattened
            # atomize atomizes a sequence
            # typed-value for a node can produce a sequence
            # Hence it is flattened.
            # Dunno if we should rescope ¯\_(ツ)_/¯

            def work():
                cnt = 1
                for part in typed_value(item.item):
                    yield DynamicContext(item, part, cnt)
                    cnt += 1

            yield from rescope_sequence(work(), stream=stream)

        elif False:  # function except array
            raise TypeError("Functions/maps are illegal to atomize!")
        elif False:  # Array
            # Atomize content of array, recursively, (ie flatten arrays while atomizing content)
            assert False, "Not implemented"


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
        return atomic_sequence(val0), val0

    def restart() -> ItemGenerator:
        yield val0
        yield val1
        yield from sequence

    return restart(), None


def peek_is_empty(sequence: ItemGenerator) -> Tuple[ItemGenerator, bool]:
    """
    Checks if the sequence contains 0 items.
    """
    try:
        val0 = next(sequence)
    except StopIteration:
        return empty_sequence_generator(), True

    def restart() -> ItemGenerator:
        yield val0
        yield from sequence

    return restart(), False


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

    # TODO: Detect if there is anything that wants the dynamic context, bind to it with bound
    # Also do other signature matching and promotion
    raise NotImplementedError()

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


def value_compare(node: ValueCompare, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    """
    https://www.w3.org/TR/xpath-31/#id-value-comparisons
    """
    lhs = evaluate_ast_node(node.lhs, data, stream=stream)
    rhs = evaluate_ast_node(node.rhs, data, stream=stream)

    # Step 1: Atomize operands
    lhs = atomize_sequence(lhs)
    rhs = atomize_sequence(rhs)

    # Step 2: If any sequence is empty, produce empty sequence
    lhs, lhs_empty = peek_is_empty(lhs)
    rhs, rhs_empty = peek_is_empty(rhs)
    if lhs_empty or rhs_empty:
        return

    # Step 3: If not atomic, raise type error
    lhs, lhs_value = peek_atomic(lhs)
    if not lhs_value:
        raise TypeError("The left-hand side of the comparison was not atomic")
    rhs, rhs_value = peek_atomic(rhs)
    if not rhs_value:
        raise TypeError("The right-hand side of the comparison was not atomic")

    # Step 4: If an atomized operand is of type xs:untypedAtomic, it is cast to xs:string.
    #   TODO: Don't ignore this or something

    left, right = lhs_value.item, rhs_value.item

    # Step 5: If the two operands are instances of different primitive types (the 19 primitive types)
    if type(left) is not type(right):
        if isinstance(left, str) and isinstance(right, str):
            #  # types are string or uri
            left, right = str(left), str(right)
        elif isinstance(left, float) and isinstance(right, float):
            # types are float or decimal
            left, right = float(left), float(right)
        elif False:
            # If each operand is an instance of one of the types xs:decimal, xs:float, or xs:double, then both operands are cast to type xs:double.
            ...
        else:
            raise TypeError("Left and right side of comparison are not stringy/floaty")

    # Step 6: Finally, if the types of the operands are a valid combination for the given operator, the operator is applied to the operands.
    result = value_operator(left, right, node.op)
    assert isinstance(result, bool), f"The result {result} is of type {type(result)}, what happened??"
    yield DynamicContext(data, result, 1, 1, None)


import operator

OPERATORS: Dict[str, Callable[[Any, Any], Any]] = {
    "=": operator.eq,
    "==": operator.eq,
    "eq": operator.eq,
    "!=": operator.ne,
    "ne": operator.ne,
    ">": operator.gt,
    "gt": operator.gt,
    ">=": operator.ge,
    "ge": operator.ge,
    "<": operator.lt,
    "lt": operator.lt,
    "<=": operator.le,
    "le": operator.le,
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}


def value_operator(a: Any, b: Any, op: str) -> Any:
    """
    https://www.w3.org/TR/xpath-31/#mapping

    Keep it simple for now.
    But how to tabel'ize? There must be a lib for predefined binary operations
    """

    operator = OPERATORS.get(op, None)
    assert operator, f"Operator {op} not implemented?"
    return operator(a, b)


def variable_reference(node: VarRef, data: DynamicContext, stream: bool = False) -> ItemGenerator:
    name = node.name
    value = data.varibles.get(name, None)
    if value is None:
        # Should be detected during AST evaluation start
        raise ValueError(f"Variable {name} does not exist")

    yield DynamicContext(data, value, 1, 1, name)


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

    elif isinstance(node, ValueCompare):
        yield from value_compare(node, data, stream=stream)

    elif isinstance(node, VarRef):
        yield from variable_reference(node, data, stream=stream)

    else:
        assert False, f"evalute not implemented for nodetype {type(node)}"


def evaluate(node: ASTNode, data: DynamicContext) -> Sequence[Any]:
    return list(data.item for data in evaluate_ast_node(node, data))


def query(
    data: Any,
    query: str,
    unwrap_nodes: bool = True,
    static_context: Optional[StaticContext] = None,
    variables: Optional[Dict[str, Any]] = None,
) -> Sequence[Any]:
    ast: ASTNode = parse(query)

    wrapped = wrap(data)
    assert wrapped, f"Could not wrap type {type(data)}"

    variables = variables or dict()

    def wrap_var(var: Any) -> Any:
        if isinstance(var, Sequence) and not isinstance(var, (str, bytes)):
            if len(var) == 1:
                return wrap_var(var[0])
            assert False, "Need to implement proper array/sequence handling"
        return wrap(var) or var

    variables = {key: wrap_var(value) for key, value in variables.items()}

    if not static_context:
        static_context = StaticContext(variables=variables)
        static_context.functions["string"] = string_value

    context: DynamicContext = DynamicContext(static_context, wrapped, 1, 1)

    result = evaluate(ast, context)

    if unwrap_nodes:
        result = [unwrap(node) if isinstance(node, NodeBase) else node for node in result]

    return result
