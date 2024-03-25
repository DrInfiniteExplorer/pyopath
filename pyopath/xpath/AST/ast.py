import sys
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from typing_extensions import TypeAlias, dataclass_transform, get_args, get_origin


class ASTNode(ABC): ...


if sys.version_info >= (3, 10):
    import inspect

    def get_annotations(typ: type):
        return inspect.get_annotations(typ)
else:

    def get_annotations(typ: type) -> Dict[str, type]:
        return getattr(typ, "__annotations__", {})  # type: ignore


def is_optional(typ: type) -> bool:
    origin = get_origin(typ)
    args = get_args(typ)
    return origin is Union and type(None) in args


def stringify(a: Any):
    if isinstance(a, str):
        return f"'{a}'"
    return str(a)


T = TypeVar("T", bound=type)


@dataclass_transform()
def Pretty(cls: T) -> T:
    # Do actual dataclass init etc, with some extra lines to make the type checker behave, since dataclass ISNT marked with @dataclass_transform
    klass = type(cls)
    cls = dataclass(cls)  # type: ignore
    assert isinstance(cls, klass)

    annotations: Dict[str, type] = {}
    members: Tuple[str, ...] = tuple()
    annotations = get_annotations(cls)
    if annotations:
        members = tuple(annotations.keys())

    def repr(selfy: object):
        myname: str = cls.__name__
        values: List[str] = []
        for num, name in enumerate(members):
            value = getattr(selfy, name)
            annotation = annotations.get(name)
            if annotation and is_optional(annotation) and num + 1 == len(members):
                if not value:
                    continue
                if len(value):  # Maybe need to do some other check to see if it is a sequence ¯\_(ツ)_/¯
                    for val in value:
                        values.append(stringify(val))
                    continue
            values.append(stringify(value))

        a = ",".join(values)
        return f"{myname}({a})"

    cls.__repr__ = repr

    return cls


@Pretty
class Expressions(ASTNode):
    """
    Represents a sequence of expressions, ie. the results are concatenated into a single sequence.
    """

    expressions: List[ASTNode]


@Pretty
class OrExpr(ASTNode):
    expressions: List[ASTNode]

    def __init__(self, expressions: List[ASTNode]):
        self.expressions = expressions


@Pretty
class AndExpr(ASTNode):
    expressions: List[ASTNode]

    def __init__(self, expressions: List[ASTNode]):
        self.expressions = expressions


@Pretty
class ComparisonExpr(ASTNode):
    a: ASTNode
    b: ASTNode
    op: str

    def __init__(self, a: ASTNode, b: ASTNode, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty
class AdditiveExpr(ASTNode):
    a: ASTNode
    b: ASTNode
    op: str

    def __init__(self, a: ASTNode, b: ASTNode, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty
class MultiplicativeExpr(ASTNode):
    a: ASTNode
    b: ASTNode
    op: str

    def __init__(self, a: ASTNode, b: ASTNode, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty
class UnionExpr(ASTNode):
    a: ASTNode
    b: ASTNode

    def __init__(self, a: ASTNode, b: ASTNode):
        self.a = a
        self.b = b


@Pretty
class IntersectExpr(ASTNode):
    a: ASTNode
    b: ASTNode

    def __init__(self, a: ASTNode, b: ASTNode):
        self.a = a
        self.b = b


@Pretty
class UnaryExpr(ASTNode):
    expression: ASTNode
    sign: str

    def __init__(self, expression: ASTNode, sign: str):
        self.expression = expression
        self.sign = sign


@Pretty
class PathOperator(ASTNode):
    a: ASTNode
    b: ASTNode


class DescendantPathExpr(ASTNode):
    a: "StepExpr"
    b: "StepExpr"


@Pretty
class Predicate(ASTNode):
    predicate: ASTNode


class StepExpr(ASTNode):
    """
    [Definition: A step is a part of a path expression that generates a sequence
     of items and then filters the sequence by zero or more predicates.
    The value of the step consists of those items that satisfy the predicates,
     working from left to right. A step may be either an axis step or a postfix expression.]
    """

    ...


class ArgumentList: ...


PostfixTypes: TypeAlias = Union[Predicate, ArgumentList]


@Pretty
class PostfixExpr(StepExpr):
    """
    [Definition: An expression followed by a predicate (that is, E1[E2]) is referred to
     as a filter expression: its effect is to return those items from the value
     of E1 that satisfy the predicate in E2.]
    """

    primary: ASTNode
    postfixes: Optional[Tuple[PostfixTypes, ...]]  # Can be either function calls, predicates, or lookups

    def __init__(self, primary: ASTNode, *postfixes: PostfixTypes):
        self.primary = primary
        self.postfixes = postfixes if len(postfixes) else None


@Pretty
class AxisStep(StepExpr):
    """
    [Definition: An axis step returns a sequence of nodes that are reachable
     from the context node via a specified axis.
    Such a step has two parts: an axis, which defines the "direction of movement" for the step,
     and a node test, which selects nodes based on their kind, name, and/or type annotation.]

    If the context item is a node, an axis step returns a sequence of zero or more nodes; otherwise,
     a type error is raised [err:XPTY0020].
    The resulting node sequence is returned in document order.
    An axis step may be either a forward step or a reverse step, followed by zero or more predicates.
    """

    axis: str
    nodetest: "NodeTest"
    predicates: Optional[Tuple[Predicate, ...]]

    def __init__(self, axis: str, nodetest: "NodeTest", *predicates: Predicate):
        self.axis = axis
        self.nodetest = nodetest
        self.predicates = predicates if len(predicates) else None


class NodeTest: ...


class KindTest(NodeTest): ...


@Pretty
class NameTest(NodeTest):
    name: str


@Pretty
class AnyKindTest(KindTest): ...


@Pretty
class TextTest(KindTest): ...


@Pretty
class Context(ASTNode): ...


@Pretty
class Literal(ASTNode):
    value: Union[str, int, float]


@Pretty
class StaticFunctionCall(ASTNode):
    name: str
    arguments: List[Expressions]


@Pretty
class Compare(ASTNode):
    op: str
    lhs: Expressions
    rhs: Expressions
