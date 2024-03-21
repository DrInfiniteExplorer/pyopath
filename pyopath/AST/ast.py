from abc import ABC
from typing import Any, List, Union


class PathyInterface(ABC): ...


def Pretty(*members: str):
    def stringify(a: Any):
        if isinstance(a, str):
            return f"'{a}'"
        return str(a)

    def wrappy(cls: type):
        def repr(selfy: object):
            myname: str = cls.__name__
            a = ",".join([f"{stringify(getattr(selfy, name))}" for name in members])
            return f"{myname}({a})"

        def eq(self: object, other: object):
            return isinstance(other, cls) and all(getattr(self, name) == getattr(other, name) for name in members)

        cls.__repr__ = repr
        cls.__eq__ = eq

        return cls

    return wrappy


@Pretty("expressions")
class Expressions(PathyInterface):
    """
    Represents a sequence of expressions, ie. the results are concatenated into a single sequence.
    """

    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty("expressions")
class OrExpr(PathyInterface):
    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty("expressions")
class AndExpr(PathyInterface):
    expressions: List[PathyInterface]

    def __init__(self, expressions: List[PathyInterface]):
        self.expressions = expressions


@Pretty("a", "b", "op")
class ComparisonExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty("a", "b", "op")
class AdditiveExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty("a", "b", "op")
class MultiplicativeExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface
    op: str

    def __init__(self, a: PathyInterface, b: PathyInterface, op: str):
        self.a = a
        self.b = b
        self.op = op


@Pretty("a", "b")
class UnionExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


@Pretty("a", "b")
class IntersectExpr(PathyInterface):
    a: PathyInterface
    b: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


@Pretty("expression", "sign")
class UnaryExpr(PathyInterface):
    expression: PathyInterface
    sign: str

    def __init__(self, expression: PathyInterface, sign: str):
        self.expression = expression
        self.sign = sign


@Pretty("a", "b")
class PathOperator(PathyInterface):
    a: PathyInterface
    a: PathyInterface

    def __init__(self, a: PathyInterface, b: PathyInterface):
        self.a = a
        self.b = b


class DescendantPathExpr(PathyInterface):
    a: "StepExpr"
    b: "StepExpr"


class StepExpr(PathyInterface):
    """
    [Definition: A step is a part of a path expression that generates a sequence
     of items and then filters the sequence by zero or more predicates.
    The value of the step consists of those items that satisfy the predicates,
     working from left to right. A step may be either an axis step or a postfix expression.]
    """

    ...


@Pretty("axis", "nodetest", "predicates")
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
    predicates: List[PathyInterface]

    def __init__(self, axis: str, nodetest: "NodeTest", predicates: List[PathyInterface]):
        self.axis = axis
        self.nodetest = nodetest
        self.predicates = predicates


class NodeTest: ...


class KindTest(NodeTest): ...


@Pretty("name")
class NameTest(NodeTest):
    name: str

    def __init__(self, name: str):
        self.name = name


@Pretty()
class AnyKindTest(KindTest): ...


@Pretty("value")
class Literal(PathyInterface):
    value: Union[str, int, float]

    def __init__(self, value: Union[str, int, float]):
        self.value = value
