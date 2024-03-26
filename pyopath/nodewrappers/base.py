from typing import Any, Generator, Optional

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class NodeBase(Protocol):
    def node_name(self) -> str: ...
    def string_value(self) -> str: ...

    def attributes(self) -> Generator["AttributeBase", None, None]: ...
    def children(self) -> Generator["NodeBase", None, None]: ...
    def parent(self) -> Optional["NodeBase"]: ...

    def node_kind(self) -> str: ...

    # def namespace_nodes(self) -> Generator["NodeBase", None, None]: ...
    # def base_uri(self) -> str: ...
    # def document_uri(self) -> str: ...
    # def is_id(self) -> bool: ...
    # def is_idrefs(self) -> bool: ...
    # def nilled(self) -> bool: ...
    # def type_name(self) -> str: ...
    def typed_value(self) -> Generator[Any, None, None]:
        raise NotImplementedError()

    # NodeBase and derivatives represents nodes in a tree produced from elsewhere
    # Call this to obtain the underlying value object that is wrapped.
    def unwrap(self) -> Any: ...


class ElementBase(NodeBase):
    def node_kind(self) -> str:
        return "element"

    def typed_value(self) -> Generator[Any, None, None]:
        yield self.string_value()


class AttributeBase(NodeBase):
    def attributes(self) -> Generator["AttributeBase", None, None]: ...
    def children(self) -> Generator[NodeBase, None, None]: ...

    def node_kind(self) -> str:
        return "attribute"

    def typed_value(self) -> Generator[Any, None, None]:
        yield self.string_value()


class DocumentBase(NodeBase): ...


class CommentBase(NodeBase): ...


class NamespaceBase(NodeBase): ...


class ProcessingInstructionBase(NodeBase): ...


class TextBase(NodeBase):
    def node_kind(self) -> str:
        return "text"


def node_name(node: NodeBase) -> str:
    return node.node_name()


def string_value(node: NodeBase) -> str:
    return node.string_value()


def attributes(node: NodeBase) -> Generator[AttributeBase, None, None]:
    yield from node.attributes()


def children(node: NodeBase) -> Generator[NodeBase, None, None]:
    yield from node.children()


def parent(node: NodeBase) -> Optional[NodeBase]:
    return node.parent()


def base_uri(node: NodeBase) -> str: ...
def document_uri(node: NodeBase) -> str: ...
def is_id(node: NodeBase) -> bool: ...
def is_idrefs(node: NodeBase) -> bool: ...
def namespace_nodes(node: NodeBase) -> Generator[NodeBase, None, None]: ...
def nilled(node: NodeBase) -> bool: ...
def node_kind(node: NodeBase) -> str: ...
def type_name(node: NodeBase) -> str: ...
def typed_value(node: NodeBase) -> Generator[Any, None, None]:
    yield from node.typed_value()


def unwrap(node: NodeBase) -> Any:
    return node.unwrap()
