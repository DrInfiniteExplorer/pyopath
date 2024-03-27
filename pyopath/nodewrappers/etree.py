from typing import Any, Dict, Generator, Optional, Union
from xml.etree.ElementTree import Element as XMLElement

from typing_extensions import TypeAlias

from pyopath.nodewrappers.base import AttributeBase, ElementBase, NodeBase, TextBase
from pyopath.nodewrappers.registry import register_nodetype

try:
    from lxml.etree import _Element as LXMLElement  # type: ignore
except ImportError:

    class LXMLElement:
        tag: str
        attrib: Dict[str, str]
        text: str

        def __iter__(self) -> Generator["LXMLElement", None, None]: ...


Element: TypeAlias = Union[XMLElement, LXMLElement]


class EtreeElement(ElementBase):
    parent_element: Optional["EtreeElement"]
    element: Element

    def __init__(self, parent_element: Optional["EtreeElement"], element: Element):
        self.parent_element = parent_element
        self.element = element

    def node_name(self) -> str:
        return self.element.tag

    def string_value(self) -> str:
        # Should be able to use etree to quickly grab the string value of the element?
        raise NotImplementedError()

    def attributes(self) -> Generator[AttributeBase, None, None]:
        for name, value in self.element.attrib.items():
            yield EtreeAttribute(self, name, value)

    def children(self) -> Generator[NodeBase, None, None]:
        for child in self.element:
            yield EtreeElement(self, child)
        yield EtreeText(self)

    def parent(self) -> Optional[NodeBase]:
        return self.parent_element

    def unwrap(self) -> Any:
        return self.element


class EtreeAttribute(AttributeBase):
    element: EtreeElement
    name: str
    value: str

    def __init__(self, element: EtreeElement, name: str, value: str):
        self.name = name
        self.value = value

    def node_name(self) -> str:
        return self.name

    def string_value(self) -> str:
        # Todo: Make sure is normalized?
        # https://www.w3.org/TR/xpath-datamodel-31/#const-infoset-attribute
        return self.value

    def parent(self) -> Optional[NodeBase]:
        return self.element

    def unwrap(self) -> Any:
        return self.value


class EtreeText(TextBase):
    parent_element: Optional[EtreeElement]

    def __init__(self, parent_element: Optional[EtreeElement] = None):
        self.parent_element = parent_element

    def node_name(self) -> str:
        return ""

    def string_value(self) -> str:
        if not self.parent_element:
            return ""
        return self.parent_element.element.text or ""

    def typed_value(self) -> Generator[Any, None, None]:
        yield self.string_value()

    def attributes(self) -> Generator["AttributeBase", None, None]: ...
    def children(self) -> Generator["NodeBase", None, None]: ...
    def parent(self) -> Optional["NodeBase"]:
        return self.parent_element

    def unwrap(self) -> Any:
        return self.string_value()


def wrap_xml_element(obj: Any) -> EtreeElement:
    assert isinstance(obj, (XMLElement, LXMLElement))
    return EtreeElement(None, obj)


register_nodetype(XMLElement, wrap_xml_element)
register_nodetype(LXMLElement, wrap_xml_element)
