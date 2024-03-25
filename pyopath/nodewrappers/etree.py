from typing import Any, Generator, Optional
from xml.etree.ElementTree import Element

from pyopath.nodewrappers.base import AttributeBase, ElementBase, NodeBase, TextBase
from pyopath.nodewrappers.registry import register_nodetype


class EtreeElement(ElementBase):
    parent_element: Optional["EtreeElement"]
    element: Element

    def __init__(self, parent_element: Optional["EtreeElement"], element: Element):
        self.parent_element = parent_element
        self.element = element

    def node_name(self) -> str:
        return self.element.tag

    def string_value(self) -> str:
        return self.element.text or ""

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

    def attributes(self) -> Generator["AttributeBase", None, None]: ...
    def children(self) -> Generator["NodeBase", None, None]: ...
    def parent(self) -> Optional["NodeBase"]:
        return self.parent_element

    def unwrap(self) -> Any:
        return self.string_value()


def wrap_etree_element(obj: Any) -> EtreeElement:
    assert isinstance(obj, Element)
    return EtreeElement(None, obj)


register_nodetype(Element, wrap_etree_element)
