from __future__ import annotations

import inspect
import weakref
from typing import (
    Callable,
    Optional,
    Tuple,
    Type,
    TypeVar,
    MutableMapping,
)

from .weakref_utilities import DefaultWeakKeyDictionary


Owner = TypeVar('Owner')
Value = TypeVar('Value')


def resolve_mro(obj1: BaseTrait, obj2: BaseTrait) -> Tuple[Type, ...]:
    """
    Create a type tuple which contains no duplicates and is in an order
    which can be used to instantiate a subclass.
    """
    obj1_mro = inspect.getmro(obj1.__class__)
    obj2_mro = inspect.getmro(obj2.__class__)

    # Get the reverse order of the mro so we start at object and add only new
    # classes.
    mro = tuple([i for i in obj1_mro[::-1]] +
                [i for i in obj2_mro[::-1] if i not in obj1_mro])

    # Reverse again to get the correct ordering.
    return mro[::-1]


class BaseTrait:
    """
    The base class of all traits. While this can be instantiated, it does
    not provide any functionality by itself.
    """
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.value: MutableMapping[Owner, Value] = weakref.WeakKeyDictionary()

    def __set_name__(self, owner: Type[Owner], name: str) -> None:
        self.name = name

    def __get__(self, obj: Owner, objtype: Type[Owner]) -> Value:
        if obj is None:
            return self
        elif obj not in self.value:
            raise AttributeError(
                f"'{objtype.__name__}' object has no attribute '{self.name}'")

        return self.value[obj]

    def __set__(self, obj: Owner, value: Value) -> None:
        self.value[obj] = value

    def __add__(self, other: BaseTrait) -> BaseTrait:
        if not isinstance(other, BaseTrait):
            raise Exception('Traits can only be added with other traits')

        name = self.__class__.__name__ + '_' + other.__class__.__name__
        bases = resolve_mro(self, other)

        new_obj_type = type(name, bases, {})
        new_obj = new_obj_type.__new__(new_obj_type)
        new_obj.__dict__.update(other.__dict__)
        new_obj.__dict__.update(self.__dict__)
        return new_obj


class ReadOnly(BaseTrait):
    """
    A trait which makes an attribute read-only after it has been set for the
    first time.
    """
    def __set__(self, obj, value) -> None:
        if obj in self.value:
            raise Exception(
                f"The attribute '{obj.__class__.__name__}.{self.name}' is read-only")
        super().__set__(obj, value)


class TypeChecked(BaseTrait):
    """
    A trait which performs a type check whenever the attribute is given a
    new value.
    """
    def __init__(self, type_) -> None:
        super().__init__()
        self.type = type_

    def __set__(self, obj, value) -> None:
        if (isinstance(value, bool) and self.type is not bool) or not isinstance(value, self.type):
            raise Exception(
                f"The attribute '{obj.__class__.__name__}.{self.name}' "
                f"is of type '{self.type.__name__}', not '{type(value).__name__}'")
        super().__set__(obj, value)


class _BaseHasCallback(BaseTrait):
    """
    A base trait for traits implementing callbacks on value change.
    This class should not be instantiated.
    """
    def __init__(self) -> None:
        super().__init__()
        self.callbacks = DefaultWeakKeyDictionary(list)


class HasCallback(_BaseHasCallback):
    """
    A trait which introduces callbacks which are called after the given
    attribute has been given a new value. The callbacks are callable
    objects which take the new value as an argument.
    """
    def __set__(self, obj: Owner, value: Value) -> None:
        super().__set__(obj, value)
        for callback in self.callbacks[obj]:
            callback(value)

    def add_callback(self, obj: Owner, func: Callable[[Value], None]) -> None:
        if len(inspect.signature(func).parameters) != 1:
            raise Exception('The callback must only take a single argument.')
        self.callbacks[obj].append(func)


class HasCallbackDelta(_BaseHasCallback):
    """
    A trait which introduces callbacks which are called after the given
    attribute has been given a new value. The callbacks are callable
    objects which take the old and new values as an argument.
    """
    def __set__(self, obj: Owner, value: Value) -> None:
        # Save a reference to the old value for the callback.
        old_value: Value = self.value.get(obj, None)

        super().__set__(obj, value)

        # This provides the callback function with the old and new values,
        # respectively.
        for callback in self.callbacks[obj]:
            callback(old_value, value)

    def add_callback(self, obj: Owner, func: Callable[[Value, Value], None]) -> None:
        if len(inspect.signature(func).parameters) != 2:
            raise Exception('The callback must take two arguments.')
        self.callbacks[obj].append(func)


class _BaseHasValidator(BaseTrait):
    """
    A base class for traits implementing value validation. This should not
    be instantiated.

    The add method is overridden in order to make sure that any traits
    with callbacks are called after the validators have run.
    """
    def __init__(self) -> None:
        super().__init__()
        self.validators = DefaultWeakKeyDictionary(list)

    def __add__(self, other: BaseTrait) -> BaseTrait:
        """
        Make sure that validator always comes before callback when compounding
        traits, so that the respective validators and callbacks are called in
        the correct order.
        """
        if isinstance(other, _BaseHasCallback):
            return other.__add__(self)
        return super().__add__(other)


class HasValidator(_BaseHasValidator):
    """
    A trait which introduces validators which are called before the given
    attribute is given a new value. The validators take the new value as
    a single argument and must return the value which should be used.
    """
    def __set__(self, obj: Owner, value: Value) -> None:
        for validator in self.validators[obj]:
            value = validator(value)
        super().__set__(obj, value)

    def add_validator(self, obj: Owner, func: Callable[[Value], Value]) -> None:
        if len(inspect.signature(func).parameters) != 1:
            raise Exception('The validator must take a single argument.')
        self.validators[obj].append(func)


class HasValidatorDelta(_BaseHasValidator):
    """
    A trait which introduces validators which are called before the given
    attribute is given a new value. The validators take the new value as
    a single argument and must return the value which should be used.
    """
    def __set__(self, obj: Owner, value: Value) -> None:
        old_value: Value = self.value.get(obj, None)

        # Each validator gets the output from the previous one as the
        # old value.
        for validator in self.validators[obj]:
            prev_value = value
            value = validator(old_value, value)
            old_value = prev_value

        super().__set__(obj, value)

    def add_validator(self, obj: Owner, func: Callable[[Value, Value], Value]) -> None:
        if len(inspect.signature(func).parameters) != 2:
            raise Exception('The validator must take two arguments.')
        self.validators[obj].append(func)
