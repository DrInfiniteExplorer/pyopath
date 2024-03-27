import ply.yacc

from pyopath.xpath.AST.ast import (
    AnyKindTest,
    ASTNode,
    AxisStep,
    Context,
    Expressions,
    GeneralCompare,
    Literal,
    NameTest,
    NodeCompare,
    PathOperator,
    PostfixExpr,
    Predicate,
    StaticFunctionCall,
    TextTest,
    ValueCompare,
    VarRef,
)
from pyopath.xpath.AST.lexer import PathLexer

# https://www.w3.org/TR/xpath-31/#id-expressions


class PathParser:
    def p_Path(self, p):
        """
        path : Expr
        """
        p[0] = p[1]

    def p_Expr(self, p):
        """
        Expr : ExprList
        """
        if len(p[1]) > 1:
            p[0] = Expressions(p[1])
        else:
            p[0] = p[1][0]

    def p_ExprList(self, p):
        """
        ExprList : ExprSingle
                 | ExprList ',' ExprSingle
        """
        if len(p) > 2:
            p[0] = p[1]
            p[0].append(p[3])
        else:
            p[0] = [p[1]]

    def p_ExprSingle(self, p):
        """
        ExprSingle : OrExpr
        """
        p[0] = p[1]

    def p_OrExpr(self, p):
        """
        OrExpr : AndExpr OR AndExpr
               | AndExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("OR", p[1], p[3])
        else:
            p[0] = p[1]

    def p_AndExpr(self, p):
        """
        AndExpr : ComparisonExpr AND ComparisonExpr
                | ComparisonExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("AND", p[1], p[3])
        else:
            p[0] = p[1]

    def p_ComparisonExpr(self, p):
        """
        ComparisonExpr : StringConcatExpr ValueComp StringConcatExpr
                       | StringConcatExpr GeneralComp StringConcatExpr
                       | StringConcatExpr NodeComp StringConcatExpr
                       | StringConcatExpr
        """
        if len(p) > 2:
            if p[2][0] == "VALUE":
                p[0] = ValueCompare(p[3], p[1], p[2][1].strip())
            elif p[2][0] == "GENERAL":
                p[0] = GeneralCompare(p[3], p[1], p[2][1].strip())
            elif p[2][0] == "NODE":
                p[0] = NodeCompare(p[3], p[1], p[2][1].strip())
            else:
                assert False, f"What is this? {p[2]}"
        else:
            p[0] = p[1]

    def p_StringConcatExpr(self, p):
        """
        StringConcatExpr : StringConcatList
        """
        if isinstance(p[1], list):
            assert False, "Not implemented"
            # p[0] = StringConcat(p[1])
        else:
            p[0] = p[1]

    def p_StringConcatList(self, p):
        """
        StringConcatList : StringConcatList CONCAT RangeExpr
                         | RangeExpr
        """
        if len(p) > 2:
            p[0] = p[1]
            if isinstance(p[0], list):
                p[0].append(p[3])
            else:
                p[0] = [p[1], p[3]]

        else:
            p[0] = p[1]

    def p_RangeExpr(self, p):
        """
        RangeExpr : AdditiveExpr TO AdditiveExpr
                  | AdditiveExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
        else:
            p[0] = p[1]

    def p_ValueComp(self, p):
        """
        ValueComp : EQstr
                  | NEstr
                  | LTstr
                  | LEstr
                  | GTstr
                  | GEstr
        """
        p[0] = ("VALUE", p[1])

    def p_GeneralComp(self, p):
        """
        GeneralComp : EQsym
                    | NEsym
                    | LTsym
                    | LEsym
                    | GTsym
                    | GEsym
        """
        p[0] = ("GENERAL", p[1])

    def p_NodeComp(self, p):
        """
        NodeComp : IS
        """
        p[0] = ("NODE", p[1])

    def p_AdditiveExpr(self, p):
        """
        AdditiveExpr : MultiplicativeExpr '+' MultiplicativeExpr
                     | MultiplicativeExpr '-' MultiplicativeExpr
                     | MultiplicativeExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("ADD", p[1], p[2], p[3])
        else:
            p[0] = p[1]

    def p_MultiplicativeExpr(self, p):
        """
        MultiplicativeExpr : UnionExpr '*' UnionExpr
                           | UnionExpr DIV UnionExpr
                           | UnionExpr IDIV UnionExpr
                           | UnionExpr MOD UnionExpr
                           | UnionExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("MULTIPLY", p[1], p[2], p[3])
        else:
            p[0] = p[1]

    def p_UnionExpr(self, p):
        """
        UnionExpr : IntersectExceptExpr UNION IntersectExceptExpr
                  | IntersectExceptExpr '|' IntersectExceptExpr
                  | IntersectExceptExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("UNION", p[1], p[2], p[3])
        else:
            p[0] = p[1]

    def p_IntersectExceptExpr(self, p):
        """
        IntersectExceptExpr : UnaryExpr INTERSECT UnaryExpr
                            | UnaryExpr EXCEPT UnaryExpr
                            | UnaryExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("INTERSECT", p[1], p[2], p[3])
        else:
            p[0] = p[1]

    def p_UnaryExpr(self, p):
        """
        UnaryExpr : '+' ValueExpr %prec UNARYSUM
                  | '-' ValueExpr %prec UNARYSUM
                  | ValueExpr
        """
        if len(p) > 2:
            assert False, "Not implemented"
            p[0] = ("UNARY", p[1], p[2])
        else:
            p[0] = p[1]

    def p_ValueExpr(
        self, p
    ):  # Not represented in AST; Parser should insert <root>/, <root>, <root//> in place of the leading relatives.
        """
        ValueExpr : SLASH RelativePathExpr
                  | SLASH
                  | DOUBLESLASH RelativePathExpr
                  | RelativePathExpr
        """
        if len(p) > 2:
            if p[1] == "/":
                assert False, "Not implemented"
                p[0] = ("ROOT", p[2])
            elif p[1] == "//":
                assert False, "Not implemented"
                p[0] = ("DESCENCANTS", p[2])
        else:
            if p[1] == "/":
                assert False, "Not implemented"
                p[0] = "ROOT"
            else:
                p[0] = p[1]

    def p_RelativePathExpr(self, p):
        """
        RelativePathExpr : RelativePathList

        """
        p[0] = p[1]

    def p_RelativePathList(self, p):
        """
        RelativePathList : StepExpr
                         | RelativePathList SLASH StepExpr
                         | RelativePathList DOUBLESLASH StepExpr
        """
        if len(p) > 2:
            left = p[1]
            right = p[3]
            if p[2] == "/":
                p[0] = PathOperator(left, right)
            else:
                p[0] = PathOperator(PathOperator(left, AxisStep("descendant-or-self", AnyKindTest())), right)
        else:
            p[0] = p[1]

    def p_StepExpr(self, p):
        """
        StepExpr : PostfixExpr
                 | AxisStep
        """
        p[0] = p[1]

    def p_PostfixExpr(self, p):
        """
        PostfixExpr : PrimaryExpr PostfixListChain
                    | PrimaryExpr
        """
        if len(p) > 2:
            p[0] = PostfixExpr(p[1], *p[2])
        else:
            p[0] = p[1]

    def p_PostfixListChain(self, p):
        """
        PostfixListChain : Predicate
                         | PostfixListChain Predicate
        """
        if len(p) > 2:
            p[0] = p[1]
            p[0].append(p[2])
        elif len(p) == 2:
            p[0] = [p[1]]

    # When evaluating these predicates, position() depends on the direction of the axis
    def p_AxisStep(self, p):
        """
        AxisStep : ReverseStep PredicateList
                 | ForwardStep PredicateList
        """
        axis, nodetest = p[1]
        predicates = p[2]
        p[0] = AxisStep(axis, nodetest, *predicates)

    def p_PredicateList(self, p):
        """
        PredicateList : Predicate
                      | PredicateList Predicate
                      |
        """
        if len(p) > 2:
            p[0] = p[1]
            p[0].append(p[2])
        elif len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = []

    def p_Predicate(self, p):
        """
        Predicate : '[' Expr ']'
        """
        p[0] = Predicate(p[2])

    def p_ReverseStep(self, p):
        """
        ReverseStep : ReverseAxis NodeTest
                    | AbbrevReverseStep
        """
        if len(p) > 2:
            p[0] = (p[1], p[2])
        else:
            a, b = p[1]
            p[0] = (a, b)

    def p_ReverseAxis(self, p):
        """
        ReverseAxis : PARENT AXIS
                    | ANCESTOR AXIS
                    | PRECEDING_SIBLING AXIS
                    | PRECEDING AXIS
                    | ANCESTOR_OR_SELF AXIS
        """
        p[0] = p[1]

    def p_AbbrevReverseStep(self, p):
        """
        AbbrevReverseStep : DOUBLEDOT
        """
        assert False, "Not implemented"
        p[0] = ("PARENT",)

    def p_ForwardStep(self, p):
        """
        ForwardStep : ForwardAxis NodeTest
                    | AbbrevForwardStep
        """
        if len(p) > 2:
            p[0] = (p[1], p[2])
        else:
            a, b = p[1]
            p[0] = (a, b)

    def p_ForwardAxis(self, p):
        """
        ForwardAxis : CHILD AXIS
                    | DESCENDANT AXIS
                    | ATTRIBUTE AXIS
                    | SELF AXIS
                    | DESCENDANT_OR_SELF AXIS
                    | FOLLOWING_SIBLING AXIS
                    | FOLLOWING AXIS
                    | NAMESPACE AXIS
        """
        p[0] = p[1]

    def p_AbbrevForwardStep(self, p):
        """
        AbbrevForwardStep : '@' NodeTest
                          | NodeTest
        """
        if len(p) > 2:
            p[0] = ("attribute", p[2])
        else:
            p[0] = ("child", p[1])

    def p_NodeTest(self, p):
        """
        NodeTest : KindTest
                 | NameTest
        """
        p[0] = p[1]

    def p_KindTest(self, p):
        """
        KindTest : ElementTest
                 | AttributeTest
                 | TextTest
                 | AnyKindTest
        """
        p[0] = p[1]

    def p_ElementTest(self, p):
        """
        ElementTest : ELEMENT '(' ElementNameOrWildcard ')'
                    | ELEMENT '(' ')'
        """
        assert False, "Not implemented yet"
        p[0] = ("ELEMENT_TEST", p[3])

    def p_ElementNameOrWildcard(self, p):
        """
        ElementNameOrWildcard : ElementName
                              | '*'
        """
        p[0] = p[1]

    def p_ElemenName(self, p):
        """
        ElementName : EQNAME
        """
        p[0] = p[1]

    def p_AttributeTest(self, p):
        """
        AttributeTest : ATTRIBUTE '(' AttributeNameOrWildcard ')'
                      | ATTRIBUTE '(' ')'
        """
        assert False, "Not implemented"
        p[0] = ("ATTRIBUTE_TEST", p[3])

    def p_AttributeNameOrWildcard(self, p):
        """
        AttributeNameOrWildcard : AttributeName
                                | '*'
        """
        p[0] = p[1]

    def p_AttributeName(self, p):
        """
        AttributeName : EQNAME
        """
        p[0] = p[1]

    def p_TextTest(self, p):
        """
        TextTest : TEXT '(' ')'
        """
        p[0] = TextTest()

    def p_AnyKindTest(self, p):
        """
        AnyKindTest : NODE '(' ')'
        """
        assert False, "Not implemented"
        p[0] = ("NODE_TEST",)

    def p_NameTest(self, p):
        """
        NameTest : EQNAME
                 | '*'
        """
        p[0] = NameTest(p[1])

    def p_PrimaryExpr_Literal(self, p):
        """
        PrimaryExpr : Literal
        """
        p[0] = p[1]

    def p_PrimaryExpr_Parens(self, p):
        """
        PrimaryExpr : ParenthesizedExpr
        """
        p[0] = p[1]

    def p_PrimaryExpr_Context(self, p):
        """
        PrimaryExpr : CONTEXT
        """
        p[0] = Context()

    def p_PrimaryExpr(self, p):
        """
        PrimaryExpr : VarRef
                    | FunctionCall

        """
        p[0] = p[1]

    def p_Literal_str(self, p):
        """
        Literal : STRING
        """
        p[0] = Literal(p[1])

    def p_Literal_num(self, p):
        """
        Literal : NUMBER
        """
        try:
            p[0] = Literal(int(p[1]))
        except ValueError:
            p[0] = Literal(float(p[1]))

    def p_VarRef(self, p):
        """
        VarRef : '$' VarName
        """
        p[0] = VarRef(p[2])

    def p_VarName(self, p):
        "VarName : EQNAME"
        p[0] = p[1]

    def p_ParenthesizedExpr(self, p):
        """
        ParenthesizedExpr : '(' ')'
                          | '(' Expr ')'
        """
        # Parens are only needed to order things while building AST
        p[0] = p[2]

    def p_FunctionCall(self, p):
        """
        FunctionCall : EQNAME ArgumentList
        """
        p[0] = StaticFunctionCall(p[1], p[2])

    def p_ArgumentList(self, p):
        """
        ArgumentList : '(' ')'
        ArgumentList : '(' ArgumentExpr ')'
        """
        p[0] = tuple(["ARGLIST"] + p[1:])

    def p_ArgumentExpr_single(self, p):
        """
        ArgumentExpr : Argument
        """
        p[0] = [p[1]]

    def p_ArgumentExpr_chain(self, p):
        """
        ArgumentExpr : ArgumentExpr ',' Argument
        """
        p[0] = p[1]
        p[0].append(p[3])

    def p_Argument(self, p):
        """
        Argument : Expr
        """
        p[0] = p[1:]

    EITHER = "left"
    NA = "nonassoc"
    precedence = (
        (EITHER, ","),
        # (NA, "FOR", "LET", "SOME", "EVERY", "IF"),
        (EITHER, "OR"),
        (EITHER, "AND"),
        (
            NA,
            "EQstr",
            "EQsym",
            "NEstr",
            "NEsym",
            "LTstr",
            "LTsym",
            "LEstr",
            "LEsym",
            "GTstr",
            "GTsym",
            "GEstr",
            "GEsym",
            "IS",
        ),
        ("left", "CONCAT"),
        (NA, "TO"),
        ("left", "+", "-"),
        ("left", "*", "DIV", "IDIV", "MOD"),
        (EITHER, "|", "UNION"),
        ("left", "INTERSECT", "EXCEPT"),
        # (NA, 'INSTANCEOF'),
        # (NA, 'TREATAS'),
        # (NA, 'CASTABLEAS'),
        # (NA, 'CASTAS'),
        # ('left', '=>'),
        ("right", "UNARYSUM"),
        ("left", "SLASH", "DOUBLESLASH"),
        ("left", "[", "]"),  # "?"),
        # (NA, 'UNARYQUESTION'),
    )

    def p_error(self, p):
        msg = f"ERROR!! {p}"
        print(msg)
        raise RuntimeError(msg)


def parse(input: str, debug_yacc: bool = True, debug_parse: bool = False, debug: bool = False) -> ASTNode:
    lexa = PathLexer()
    lexer: ply.lex.Lexer = ply.lex.lex(object=lexa)  # type: ignore
    path_parser = PathParser()
    path_parser.tokens = lexa.tokens  # type: ignore
    parser: ply.yacc.LRParser = ply.yacc.yacc(module=path_parser, write_tables=True, debug=debug or debug_yacc)

    return parser.parse(input, lexer=lexer, debug=debug or debug_parse)
