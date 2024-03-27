import xml.etree.ElementTree as XMLET
from typing import Any, Dict, List, Optional, Sequence, Tuple

import lxml.etree as LXMLET
import pytest

import pyopath
import pyopath.nodewrappers.etree

basic_xml_str = """
<data asd="dsa">
    <country name="Liechtenstein">
        <rank>1</rank>
        <year>2008</year>
        <gdppc>141100</gdppc>
        <neighbor name="Austria" direction="E"/>
        <neighbor name="Switzerland" direction="W"/>
    </country>
    <country name="Singapore">
        <rank>4</rank>
        <year>2011</year>
        <gdppc>59900</gdppc>
        <neighbor name="Malaysia" direction="N"/>
    </country>
    <country name="Panama">
        <rank>68</rank>
        <year>2011</year>
        <gdppc>13600</gdppc>
        <neighbor name="Costa Rica" direction="W"/>
        <neighbor name="Colombia" direction="E"/>
    </country>
</data>
"""


def root(root_obj: Any) -> List[Any]:
    return [root_obj]


def all_countries(root: Any) -> List[Any]:
    return list(root.iter("country"))


def first_country(root: Any) -> List[Any]:
    return [all_countries(root)[0]]


def all_ranks(root: Any) -> List[Any]:
    return list(root.iterfind("country/rank"))


VarType = Optional[Dict[str, Any]]


class DummyType: ...


DummyVar = DummyType()

test_xml_cases: Sequence[Tuple[int, str, Any, VarType]] = (
    # Abbreviated axis
    (1, "@asd", ["dsa"], None),
    (1, "country", all_countries, None),
    # Full axis
    (1, "attribute::asd", ["dsa"], None),
    (1, "child::country", all_countries, None),
    # Conditionals
    (1, "country[@name]", all_countries, None),
    (1, "country[1]", first_country, None),
    # Paths
    (1, "country/rank", all_ranks, None),
    # Obtaining text results
    (1, "country/rank/text()", ["1", "4", "68"], None),
    # Conditional
    (3, "2 eq 2", [True], None),
    (3, "2 eq 3", [False], None),
    # ("'2' eq 2", [False], None), # Raises TypeError as expected!
    (3, "'2' eq '2'", [True], None),
    (3, "'2' eq '3'", [False], None),
    # Variables
    (1, "$var", ["hello"], dict(var="hello")),
    (1, "$var", root, dict(var=lambda x: root(x)[0])),  # value=element
    (1, "$var", root, dict(var=root)),  # value=element, but through singleton-unwrap of argument, since those are equal
    # (1, "$var", all_countries, dict(var=all_countries)), Need to implement proper array/sequence handling
    (1, "$var", [2], dict(var=2)),
    (-1, "$var", [DummyVar], dict(var=DummyVar)),  # -1 = don't support random types in pure lxml / xpath
    # Complex!
    (3, "country[1]/rank/text() eq '1'", [True], None),
    (3, "country[rank/text() eq '1']/year/text()", ["2008"], None),
    # test?
    (1, ".", root, None),
    (1, "./.", root, None),
    (1, "country/.", all_countries, None),
)

basic_xml_data = XMLET.fromstring(basic_xml_str)
basic_lxml_data = LXMLET.fromstring(basic_xml_str)


@pytest.mark.parametrize("lang_version, query, reference, variables", test_xml_cases)
def test_doer_xml(lang_version: int, query: str, reference: Any, variables: VarType):
    model = basic_xml_data
    if variables:
        variables = {key: value(model) if callable(value) else value for key, value in variables.items()}
    res = pyopath.query(model, query, variables=variables)
    ref: Any = reference(model) if callable(reference) else reference

    if res != ref:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == ref


@pytest.mark.parametrize("lang_version, query, reference, variables", test_xml_cases)
def test_doer_lxml(lang_version: int, query: str, reference: Any, variables: VarType):
    model = basic_lxml_data
    if variables:
        variables = {key: value(model) if callable(value) else value for key, value in variables.items()}
    res = pyopath.query(model, query, variables=variables)
    ref: Any = reference(model) if callable(reference) else reference

    if res != ref:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == ref


@pytest.mark.parametrize("lang_version, query, reference, variables", test_xml_cases)
def test_verify_testcases(lang_version: int, query: str, reference: Any, variables: VarType):
    if lang_version != 1:
        pytest.skip("lxml only supports 1.0 xpath features, can't verify this test")
    model = basic_lxml_data
    if variables:
        variables = {key: value(model) if callable(value) else value for key, value in variables.items()}
    res = model.xpath(query, **(variables or dict()))
    if isinstance(res, (str, int, float)):
        res = [res]

    ref: Any = reference(model) if callable(reference) else reference

    if res != ref:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == ref


basic_py_data = {
    "name": "John",
    "age": 30,
    "address": {"city": "New York", "zipcode": "10001"},
    "pets": [{"type": "dog", "name": "Buddy"}, {"type": "cat", "name": "Whiskers"}],
}

basic_py_cases = (
    ("a", basic_py_data, []),
    ("age", basic_py_data, [30]),
    # Conditional things
    ("age[1]", basic_py_data, [30]),
    ("age[.]", basic_py_data, 2),
    # ("address[town]", basic_py_data, []),
    # ("address[city]", basic_py_data, 2),
    # Index in array?
    # ("pets[2]", basic_py_data, 2),
)
