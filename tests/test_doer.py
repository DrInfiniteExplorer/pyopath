import xml.etree.ElementTree as ET
from typing import Any, Sequence, Tuple

import pytest

import pyopath

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

basic_xml_data = ET.fromstring(basic_xml_str)

root = basic_xml_data

all_countries = list(root.iter("country"))
first_country = all_countries[0]

all_ranks = list(root.iterfind("country/rank"))

test_xml_cases: Sequence[Tuple[str, Any, Any]] = (
    # Abbreviated axis
    ("@asd", root, ["dsa"]),
    ("country", root, all_countries),
    # Full axis
    ("attribute::asd", root, ["dsa"]),
    ("child::country", root, all_countries),
    # Conditionals
    ("country[@name]", root, all_countries),
    ("country[1]", root, [first_country]),
    # Paths
    ("country/rank", root, all_ranks),
    ("country/rank/text()", root, ["1", "4", "68"]),
    ("country[rank/text()='1']/year/text()", root, ["1", "4", "68"]),
)


@pytest.mark.parametrize("query, model, reference", test_xml_cases)
def test_doer(query: str, model: Any, reference: Any):
    res = pyopath.query(model, query)
    if res != reference:
        print(f"Query: {query}")
        print(f"Res: {res}")
        assert res == reference


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
