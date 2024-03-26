from typing import Generator

import ply.lex


class PathLexer:
    tokens = (
        ["OR", "AND"]
        + ["CONCAT", "TO"]
        + ["EQstr", "NEstr", "LTstr", "LEstr", "GTstr", "GEstr"]
        + ["EQsym", "NEsym", "LTsym", "LEsym", "GTsym", "GEsym"]
        + ["IS"]
        + ["SLASH", "DOUBLESLASH"]
        + ["DIV", "IDIV", "MOD"]
        + ["UNION", "INTERSECT", "EXCEPT"]
        + [
            "CHILD",
            "DESCENDANT",
            "ATTRIBUTE",
            "SELF",
            "DESCENDANT_OR_SELF",
            "FOLLOWING_SIBLING",
            "FOLLOWING",
            "NAMESPACE",
        ]
        + ["PARENT", "ANCESTOR", "PRECEDING_SIBLING", "PRECEDING", "ANCESTOR_OR_SELF"]
        + ["AXIS"]
        + ["CONTEXT", "DOUBLEDOT"]
        + ["ELEMENT", "NODE", "TEXT"]  # ATTRIBUTE already defined elsewhere
        + ["STRING", "NUMBER", "EQNAME"]
    )

    t_OR = r"\bor\b"
    t_AND = r"\band\b"

    t_CONCAT = r"[|][|]"
    t_TO = r"\s+to\s+"

    t_EQstr = r"\s+eq\s+"
    t_NEstr = r"\s+ne\s+"
    t_LTstr = r"\s+lt\s+"
    t_LEstr = r"\s+le\s+"
    t_GTstr = r"\s+gt\s+"
    t_GEstr = r"\s+ge\s+"

    t_EQsym = r"==?"
    t_NEsym = r"!="
    t_LTsym = r"<"
    t_LEsym = r"<="
    t_GTsym = r">"
    t_GEsym = r">="

    t_IS = r"\bis\b"

    t_SLASH = r"/"
    t_DOUBLESLASH = r"//"

    t_DIV = r"\bdiv\b"
    t_IDIV = r"\bidiv\b"
    t_MOD = r"\bmod\b"

    t_UNION = r"\bunion\b"
    t_INTERSECT = r"\bintersect\b"
    t_EXCEPT = r"\bexcept\b"

    t_CHILD = r"\bchild\b"
    t_DESCENDANT = r"\bdescendant\b"
    t_ATTRIBUTE = r"\battribute\b"
    t_SELF = r"\bself\b"
    t_DESCENDANT_OR_SELF = r"\bdescendant_or_self\b"
    t_FOLLOWING_SIBLING = r"\bfollowing_sibling\b"
    t_FOLLOWING = r"\bfollowing\b"
    t_NAMESPACE = r"\bnamespace\b"

    t_PARENT = r"\bparent\b"
    t_ANCESTOR = r"\bancestor\b"
    t_PRECEDING_SIBLING = r"\bpreceding_sibling\b"
    t_PRECEDING = r"\bpreceding\b"
    t_ANCESTOR_OR_SELF = r"\bancestor_or_self\b"

    AxisNames = [
        "child",
        "descendant",
        "attribute",
        "self",
        "descendant-or-self",
        "following-sibling",
        "following",
        "namespace",
        # reverse axis names
        "parent",
        "ancestor",
        "preceding-sibling",
        "preceding",
        "ancestor-or-self",
    ]

    t_AXIS = r"::"
    t_CONTEXT = r"\."
    t_DOUBLEDOT = r"\.\."

    t_ELEMENT = r"\belement\b"
    t_NODE = r"\bnode\b"
    t_TEXT = r"\btext\b"

    TestNames = ["element", "node", "text"]

    def t_STRING(self, t):
        r"""(\"([^\\\n]|(\\.))*?\")|(\'([^\\\n]|(\\.))*?\')"""
        t.value = t.value[1:-1]
        return t

    t_NUMBER = r"[+-]?\d+(\.\d*)?"

    literals = "{}[]()@"

    def t_EQNAME(self, t):
        r"[a-zA-Z]\w*"
        if t.value in self.AxisNames:
            clone = t.lexer.clone()
            if clone.token().type == "AXIS":
                t.type = t.value.replace("-", "_").upper()
        if t.value in self.TestNames:
            clone = t.lexer.clone()
            if clone.token().type == "(":
                t.type = t.value.replace("-", "_").upper()
        return t

    def t_error(self, t):
        msg = f"Illegal character '{t.value[0]}'"
        print(msg)
        raise ValueError(msg)


def lex(input: str) -> Generator[ply.lex.LexToken, None, None]:
    lexer: ply.lex.Lexer = ply.lex.lex(object=PathLexer())  # type: ignore
    lexer.input(input)  # type: ignore
    for token in lexer:  # type: ignore
        yield token
