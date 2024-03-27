import xml.etree.ElementTree as XMLET
from typing import Any, List, Sequence, Tuple

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


test_xml_cases: Sequence[Tuple[int, str, Any]] = (
    # Abbreviated axis
    (1, "@asd", ["dsa"]),
    (1, "country", all_countries),
    # Full axis
    (1, "attribute::asd", ["dsa"]),
    (1, "child::country", all_countries),
    # Conditionals
    (1, "country[@name]", all_countries),
    (1, "country[1]", first_country),
    # Paths
    (1, "country/rank", all_ranks),
    # Obtaining text results
    (1, "country/rank/text()", ["1", "4", "68"]),
    # Conditional
    (3, "2 eq 2", [True]),
    (3, "2 eq 3", [False]),
    # ("'2' eq 2", [False]), # Raises TypeError as expected!
    (3, "'2' eq '2'", [True]),
    (3, "'2' eq '3'", [False]),
    # Complex!
    (3, "country[1]/rank/text() eq '1'", [True]),
    (3, "country[rank/text() eq '1']/year/text()", ["2008"]),
    # test?
    (1, ".", root),
    (1, "./.", root),
    (1, "country/.", all_countries),
)

basic_xml_data = XMLET.fromstring(basic_xml_str)
basic_lxml_data = LXMLET.fromstring(basic_xml_str)


@pytest.mark.parametrize("lang_version, query, reference", test_xml_cases)
def test_doer_xml(lang_version: int, query: str, reference: Any):
    model = basic_xml_data
    res = pyopath.query(model, query)
    ref: Any = reference(model) if callable(reference) else reference

    if res != ref:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == ref


@pytest.mark.parametrize("lang_version, query, reference", test_xml_cases)
def test_doer_lxml(lang_version: int, query: str, reference: Any):
    model = basic_lxml_data
    res = pyopath.query(model, query)
    ref: Any = reference(model) if callable(reference) else reference

    if res != ref:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == ref


@pytest.mark.parametrize("lang_version, query, reference", test_xml_cases)
def test_verify_testcases(lang_version: int, query: str, reference: Any):
    if lang_version != 1:
        pytest.skip("lxml only supports 1.0 xpath features, can't verify this test")
    model = basic_lxml_data
    res = model.xpath(query)
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
