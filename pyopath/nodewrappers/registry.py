from typing import Any, List, Optional, Tuple

from typing_extensions import Protocol

from pyopath.nodewrappers.base import NodeBase


class NodeInstantiator(Protocol):
    def __call__(self, obj: Any) -> NodeBase: ...


_registered_wrappers: List[Tuple[type, NodeInstantiator]] = []


def register_nodetype(cls: type, wrapper: NodeInstantiator):
    assert get_wrapper(cls) is None, f"A wrapper for the type {cls} is already registered"
    _registered_wrappers.append((cls, wrapper))


def get_wrapper(cls: type) -> Optional[NodeInstantiator]:
    for typ, instantiator in _registered_wrappers:
        if issubclass(cls, typ):
            return instantiator


def wrap(obj: Any) -> Optional[NodeBase]:
    typ = type(obj)
    wrapper = get_wrapper(typ)
    if wrapper:
        return wrapper(obj)
