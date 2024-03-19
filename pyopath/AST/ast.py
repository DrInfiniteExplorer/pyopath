from abc import ABC
from typing import List


class PathyInterface(ABC): ...


def Pretty(*members):
    print(members)

    def wrappy(cls):
        def repr(selfy):
            myname = cls.__name__
            a = ",".join([f"{getattr(selfy, name)}" for name in members])
            return f"{myname}({a})"

        cls.__repr__ = repr

        return cls

    return wrappy


@Pretty("expression")
class Path(PathyInterface):
    expression: "ExpressionList"

    def __init__(self, expression):
        self.expression = expression


@Pretty("expressions")
class Expression(PathyInterface):
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


class ChildPathExpr(PathyInterface):
    a: "StepExpr"
    b: "StepExpr"


class DescendantPathExpr(PathyInterface):
    a: "StepExpr"
    b: "StepExpr"


class StepExpr(PathyInterface): ...


class PrimaryExpr(PathyInterface): ...


class Literal(PathyInterface): ...
