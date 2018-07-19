import collections
import weakref

from typing import (
    Any,
    Callable,
    Iterable,
    List,
)


class DefaultWeakKeyDictionary(weakref.WeakKeyDictionary):
    def __init__(self, factory: Callable[[], Any]) -> None:
        super().__init__()
        self.factory = factory

    def __getitem__(self, key: Any) -> Any:
        if key not in self:
            self[key] = self.factory()
        return super().__getitem__(key)


class OrderedSet(collections.abc.Set):
    def __init__(self, elements: Iterable[Any] = None) -> None:
        super().__init__()
        self.data: List[Any] = []

        if elements:
            for e in elements:
                self.add(e)

    def __contains__(self, item: Any) -> bool:
        return item in self.data

    def __iter__(self) -> Iterable[Any]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __str__(self) -> str:
        return '(' + ', '.join([str(i) for i in self]) + ')'

    def __repr__(self) -> str:
        return str(self)

    def add(self, item) -> None:
        if item not in self:
            self.data.append(item)

    def remove(self, item) -> None:
        self.data.remove(item)

    def discard(self, item) -> None:
        if item in self:
            self.remove(item)

    def pop(self) -> Any:
        return self.data.pop()

    def clear(self) -> None:
        self.data = []


class OrderedWeakSet(weakref.WeakSet):
    def __init__(self):
        super().__init__()
        self.data = OrderedSet()
