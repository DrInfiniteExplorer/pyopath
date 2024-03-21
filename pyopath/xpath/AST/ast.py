import sys
from abc import ABC
from typing import Any, Dict, List, Optional, Tuple, Union

from typing_extensions import TypeAlias, get_args, get_origin


class PathyInterface(ABC): ...


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


def Pretty(*members: str):
    def stringify(a: Any):
        if isinstance(a, str):
            return f"'{a}'"
        return str(a)

    annotations: Dict[str, type] = {}

    def wrappy(cls: type):
        nonlocal members, annotations
        if not members:
            members = tuple()
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
                    if value is None:
                        continue
                    if len(value):  # Maybe need to do some other check to see if it is a sequence ¯\_(ツ)_/¯
                        for val in value:
                            values.append(stringify(val))
                        continue
                values.append(stringify(value))

            a = ",".join(values)
            return f"{myname}({a})"

        def eq(self: object, other: object):
            return isinstance(other, cls) and all(getattr(self, name) == getattr(other, name) for name in members)

        cls.__repr__ = repr
        cls.__eq__ = eq

        return cls

    return wrappy


@Pretty()
class Expressions(PathyInterface):
    """
    Represents a sequence of expressions, ie. the results are concatenated into a single sequence.
    """

    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty()
class OrExpr(PathyInterface):
    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty()
class AndExpr(PathyInterface):
    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty()
class ComparisonExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty()
class AdditiveExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty()
class MultiplicativeExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty()
class UnionExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


@Pretty()
class IntersectExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


@Pretty()
class UnaryExpr(PathyInterface):
    expression: PathyInterface
    sign: str

    def __init__(self, expression: PathyInterface, sign: str):
        self.expression = expression
        self.sign = sign


@Pretty()
class PathOperator(PathyInterface):
    a: PathyInterface
    a: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


class DescendantPathExpr(PathyInterface):
    a: "StepExpr"
    b: "StepExpr"


@Pretty()
class Predicate(PathyInterface):
    predicate: PathyInterface

    def __init__(self, predicate: PathyInterface):
        self.predicate = predicate


class StepExpr(PathyInterface):
    """
    [Definition: A step is a part of a path expression that generates a sequence
     of items and then filters the sequence by zero or more predicates.
    The value of the step consists of those items that satisfy the predicates,
     working from left to right. A step may be either an axis step or a postfix expression.]
    """

    ...


class ArgumentList: ...


PostfixTypes: TypeAlias = Union[Predicate, ArgumentList]


@Pretty()
class PostfixExpr(StepExpr):
    """
    [Definition: An expression followed by a predicate (that is, E1[E2]) is referred to
     as a filter expression: its effect is to return those items from the value
     of E1 that satisfy the predicate in E2.]
    """

    primary: PathyInterface
    postfixes: Optional[Tuple[PostfixTypes]]  # Can be either function calls, predicates, or lookups

    def __init__(self, primary: PathyInterface, *postfixes: PostfixTypes):
        self.primary = primary
        self.postfixes = postfixes if len(postfixes) else None


@Pretty()
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
    predicates: Optional[Tuple[Predicate]]

    def __init__(self, axis: str, nodetest: "NodeTest", *predicates: Predicate):
        self.axis = axis
        self.nodetest = nodetest
        self.predicates = predicates if len(predicates) else None


class NodeTest: ...


class KindTest(NodeTest): ...


@Pretty()
class NameTest(NodeTest):
    name: str

    def __init__(self, name: str):
        self.name = name


@Pretty()
class AnyKindTest(KindTest): ...


@Pretty()
class Literal(PathyInterface):
    value: Union[str, int, float]

    def __init__(self, value: Union[str, int, float]):
        self.value = value
