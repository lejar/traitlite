import copy
import inspect
from weakref import WeakKeyDictionary
from typing import (
    Any,
    Callable,
    List,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from .weakref_utilities import DefaultWeakKeyDictionary


Owner = TypeVar('Owner')
Value = TypeVar('Value')


def resolve_mro(obj1: 'BaseTrait', obj2: 'BaseTrait') -> Tuple[Type, ...]:
    """
    Create a type tuple which contains no duplicates and is in an order
    which can be used to instantiate a subclass.
    """
    obj1_mro = inspect.getmro(obj1.__class__)
    obj2_mro = inspect.getmro(obj2.__class__)

    # Get the reverse order of the mro so we start at object and add only new
    # classes.
    mro = ([i for i in obj1_mro[::-1]] +
           [i for i in obj2_mro[::-1] if i not in obj1_mro])

    # Having generic in here causes problems at runtime.
    if Generic in mro:
        mro.remove(Generic)  # type: ignore

    # Reverse again to get the correct ordering.
    return tuple(mro[::-1])


class BaseTrait(Generic[Owner, Value]):
    """
    The base class of all traits. While this can be instantiated, it does
    not provide any functionality by itself.
    """
    def __init__(self) -> None:
        self.name: Optional[str] = None
        self.value: WeakKeyDictionary[Owner, Value] = WeakKeyDictionary()

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

    def __add__(self, other: 'BaseTrait') -> 'BaseTrait':
        if not isinstance(other, BaseTrait):
            raise Exception('Traits can only be added with other traits')

        name = self.__class__.__name__ + '_' + other.__class__.__name__
        bases = resolve_mro(self, other)

        new_obj_type: Type[object] = type(name, bases, {})
        new_obj = object.__new__(new_obj_type)
        new_obj.__dict__.update(other.__dict__)
        new_obj.__dict__.update(self.__dict__)
        return new_obj


class ReadOnly(BaseTrait):
    """
    A trait which makes an attribute read-only after it has been set for the
    first time.
    ::

        from traitlite import ReadOnly

        class Foo:
            bar = ReadOnly()

            def __init__(self, bar):
                self.bar = bar # Setting it the first time is allowed

        foo = Foo(3)
        foo.bar = 4 # This raises an exception
    """
    def __set__(self, obj: Owner, value: Value) -> None:
        if obj in self.value:
            raise Exception(
                f"The attribute '{obj.__class__.__name__}.{self.name}' is read-only")
        super().__set__(obj, value)


class TypeChecked(BaseTrait):
    """
    A trait which performs a type check whenever the attribute is given a
    new value.
    ::

        from traitlite import TypeChecked

        class Foo:
            bar = TypeChecked(int)

            def __init__(self, bar):
                self.bar = bar

        foo = Foo(3) # This is okay
        foo = Foo(3.0) # This raises an exception
    """
    def __init__(self, type_: Type[object]) -> None:
        """
        :param type_: The type to check against:
        :type type_:  type
        """
        super().__init__()
        self.type: Type[object] = type_

    def __set__(self, obj: Owner, value: Value) -> None:
        if (isinstance(value, bool) and not issubclass(self.type, bool)) \
                or not isinstance(value, self.type):
            raise Exception(
                f"The attribute '{obj.__class__.__name__}.{self.name}' "
                f"is of type '{self.type.__name__}', not '{type(value).__name__}'")
        super().__set__(obj, value)


class _BaseHasCallback(BaseTrait):
    """
    A base trait for traits implementing callbacks on value change.
    This class should not be instantiated.
    """
    pass


class HasCallback(_BaseHasCallback, Generic[Owner, Value]):
    """
    A trait which introduces callbacks which are called after the given
    attribute has been given a new value. The callbacks are callable
    objects which take the new value as an argument.
    ::

        from traitlite import HasCallback

        class Foo:
            bar = HasCallback()

        def print_value(value):
            print('New value is:', value)

        foo = Foo()

        # We have to use the class here instead of the instance, and the
        # instance is passed as the first argument.
        Foo.bar.add_callback(foo, print_value)

        foo.bar = 3 # New value is: 3

    Additionally, a list of default callbacks can be passed to the constructor:
    ::

        from traitlite import HasCallback

        def print_value(value):
            print('New value is:', value)

        class Foo:
            bar = HasCallback([print_value])

        foo = Foo()

        foo.bar = 3 # New value is: 3
    """
    def __init__(self, callbacks: Optional[List[Callable[[Value], None]]] = None) -> None:
        """
        :param callbacks: A list of callbacks to use for every instance of this trait.
        :type callbacks:  list
        """
        super().__init__()

        for callback in callbacks or []:
            self.check_callback(callback)

        self.callbacks: DefaultWeakKeyDictionary[Any, List[Callable[[Value], None]]] = \
            DefaultWeakKeyDictionary(lambda: copy.copy(callbacks or []))

    def __set__(self, obj: Owner, value: Value) -> None:
        super().__set__(obj, value)

        for callback in self.callbacks[obj]:
            self.check_callback(callback)
            callback(value)

    def add_callback(self, obj: Owner, func: Callable[[Value], None]) -> None:
        """
        Adds a callback to be called after the value is changed. The callback
        must be a callable object which takes the new value as its argument.

        For example, a callback which prints the new value would be:
        ::

            def print_value(value):
                print('New value:', value)

            ObjClass.add_callback(obj, print_value)

        Note: The callable passed to :func:`add_callback` must have a signature,
        i.e. builtin functions like ``max`` cannot be used directly, but must be
        wrapped in a lambda.
        """
        self.check_callback(func)
        self.callbacks[obj].append(func)

    @staticmethod
    def check_callback(func: Callable[[Value], None]) -> None:
        """
        Raises an exception if the given callback function is not compatible with
        this trait.

        :param func: A compatible callback function.
        :type func:  Callable[[Value], None]
        """
        if len(inspect.signature(func).parameters) != 1:
            raise Exception('The callback must only take a single argument.')


class HasCallbackDelta(_BaseHasCallback, Generic[Owner, Value]):
    """
    A trait which introduces callbacks which are called after the given
    attribute has been given a new value. The callbacks are callable
    objects which take the old and new values as an argument.
    ::

        from traitlite import HasCallbackDelta

        class Foo:
            bar = HasCallbackDelta()

        def print_value(old_value, new_value):
            print('Old value: {}, New value: {}'.format(
                old_value, new_value))

        foo = Foo()

        # We have to use the class here instead of the instance, and the
        # instance is passed as the first argument.
        Foo.bar.add_callback(foo, print_value)

        foo.bar = 3 # Old value: None, New value: 3
        foo.bar = 4 # Old value: 3, New value: 4

    Additionally, a list of default callbacks can be passed to the constructor:
    ::

        from traitlite import HasCallbackDelta

        def print_value(old_value, new_value):
            print('Old value: {}, New value: {}'.format(
                old_value, new_value))

        class Foo:
            bar = HasCallbackDelta([print_value])

        foo = Foo()

        foo.bar = 3 # Old value: None, New value: 3
        foo.bar = 4 # Old value: 3, New value: 4
    """
    def __init__(self, callbacks: Optional[List[Callable[[Value, Value], None]]] = None) -> None:
        """
        :param callbacks: A list of callbacks to use for every instance of this trait.
        :type callbacks:  list
        """
        super().__init__()
        for callback in callbacks or []:
            self.check_callback(callback)

        self.callbacks: DefaultWeakKeyDictionary[Any, List[Callable[[Value, Value], None]]] = \
            DefaultWeakKeyDictionary(lambda: copy.copy(callbacks or []))

    def __set__(self, obj: Owner, value: Value) -> None:
        # Save a reference to the old value for the callback.
        old_value = self.value.get(obj, None)

        super().__set__(obj, value)

        # This provides the callback function with the old and new values,
        # respectively.
        for callback in self.callbacks[obj]:
            callback(old_value, value)

    def add_callback(self, obj: Owner, func: Callable[[Value, Value], None]) -> None:
        """
        Adds a callback to be called after the value is changed. The callback
        must be a callable object which takes the new and old values as its
        arguments.

        For example, a callback which prints the old and new values would be:
        ::

            def print_value(old_value, new_value):
                print('Old value:', old_value)
                print('New value:', new_value)

            ObjClass.add_callback(obj, print_value)

        Note: The callable passed to :func:`add_callback` must have a signature,
        i.e. builtin functions like ``max`` cannot be used directly, but must be
        wrapped in a lambda.
        """
        self.check_callback(func)
        self.callbacks[obj].append(func)

    @staticmethod
    def check_callback(func: Callable[[Value, Value], None]) -> None:
        """
        Raises an exception if the given callback function is not compatible with
        this trait.

        :param func: A compatible callback function.
        :type func:  Callable[[Value, Value], None]
        """
        if len(inspect.signature(func).parameters) != 2:
            raise Exception('The callback must take two arguments.')


class _BaseHasValidator(BaseTrait):
    """
    A base class for traits implementing value validation. This should not
    be instantiated.

    The add method is overridden in order to make sure that any traits
    with callbacks are called after the validators have run.
    """
    def __add__(self, other: BaseTrait) -> BaseTrait:
        """
        Make sure that validator always comes before callback when compounding
        traits, so that the respective validators and callbacks are called in
        the correct order.
        """
        if isinstance(other, _BaseHasCallback):
            return other.__add__(self)
        return super().__add__(other)


class HasValidator(_BaseHasValidator, Generic[Owner, Value]):
    """
    A trait which introduces validators which are called before the given
    attribute is given a new value. The validators take the new value as
    a single argument and must return the value which should be used.
    ::

        from traitlite import HasValidator

        class Foo:
            bar = HasValidator()

        foo = Foo()

        # We have to use the class here instead of the instance, and the
        # instance is passed as the first argument.
        Foo.bar.add_validator(foo, lambda x: max(0, x))
        Foo.bar.add_validator(foo, lambda x: min(10, x))

        foo.bar = 3
        print(foo.bar) # 3
        foo.bar = -1
        print(foo.bar) # 0
        foo.bar = 11
        print(foo.bar) # 10

    Additionally, a list of default validators can be passed to the constructor:
    ::

        from traitlite import HasValidator

        class Foo:
            bar = HasValidator([lambda x: max(0, x)])

        foo = Foo()

        foo.bar = 3
        print(foo.bar) # 3
        foo.bar = -1
        print(foo.bar) # 0
    """
    def __init__(self, validators: Optional[List[Callable[[Value], Value]]] = None) -> None:
        """
        :param validators: A list of validators to use for every instance of this trait.
        :type validators:  list
        """
        super().__init__()
        for validator in validators or []:
            self.check_validator(validator)

        self.validators: DefaultWeakKeyDictionary[Any, List[Callable[[Value], Value]]] = \
            DefaultWeakKeyDictionary(lambda: copy.copy(validators or []))

    def __set__(self, obj: Owner, value: Value) -> None:
        for validator in self.validators[obj]:
            value = validator(value)
        super().__set__(obj, value)

    def add_validator(self, obj: Owner, func: Callable[[Value], Value]) -> None:
        """
        Adds a validator to be called before the value is changed. The validator
        must be a callable object which takes the new value as its argument and
        must return the value which should be used.

        For example, a validator which
        makes sure that the value is always greater or equal to zero would be:
        ::

            ObjClass.add_validator(obj, lambda x: max(0, x))

        Note: The callable passed to :func:`add_validator` must have a signature,
        i.e. builtin functions like ``max`` cannot be used directly, but must be wrapped
        in a lambda.
        """
        self.check_validator(func)
        self.validators[obj].append(func)

    @staticmethod
    def check_validator(func: Callable[[Value], Value]):
        """
        Raises an exception if the given validator function is not compatible with
        this trait.

        :param func: A compatible validator function.
        :type func:  Callable[[Value], Value]
        """
        if len(inspect.signature(func).parameters) != 1:
            raise Exception('The validator must take a single argument.')


class HasValidatorDelta(_BaseHasValidator, Generic[Owner, Value]):
    """
    A trait which introduces validators which are called before the given
    attribute is given a new value. The validators take the new value as
    a single argument and must return the value which should be used.
    ::

        from traitlite import HasValidatorDelta

        class Foo:
            bar = HasValidatorDelta()

            def __init__(self):
                self.bar = 0

        foo = Foo()

        # We have to use the class here instead of the instance, and the
        # instance is passed as the first argument.
        Foo.bar.add_validator(foo, lambda x, y: max(x, y))

        foo.bar = 3
        print(foo.bar) # 3
        foo.bar = 2
        print(foo.bar) # 3
        foo.bar = 4
        print(foo.bar) # 4

    Additionally, a list of default validators can be passed to the constructor:
    ::

        from traitlite import HasValidatorDelta

        class Foo:
            bar = HasValidatorDelta([lambda old, new: max(old or 0, new)])

        foo = Foo()

        foo.bar = 3
        print(foo.bar) # 3
        foo.bar = -1
        print(foo.bar) # 3
    """
    def __init__(self, validators: Optional[List[Callable[[Value, Value], Value]]] = None) -> None:
        """
        :param validators: A list of validators to use for every instance of this trait.
        :type validators:  list
        """
        super().__init__()
        for validator in validators or []:
            self.check_validator(validator)

        self.validators: DefaultWeakKeyDictionary[Any, List[Callable[[Value, Value], Value]]] = \
            DefaultWeakKeyDictionary(lambda: copy.copy(validators or []))

    def __set__(self, obj: Owner, value: Value) -> None:
        old_value = self.value.get(obj, None)

        # Each validator gets the output from the previous one as the
        # old value.
        for validator in self.validators[obj]:
            prev_value = value
            value = validator(old_value, value)
            old_value = prev_value

        super().__set__(obj, value)

    def add_validator(self, obj: Owner, func: Callable[[Value, Value], Value]) -> None:
        """
        Adds a validator to be called before the value is changed. The validator
        must be a callable object which takes the old and new values as its arguments
        and must return the value which should be used.

        For example, a validator which only accepts increases in value would be:
        ::

            ObjClass.add_validator(obj, lambda x, y: max(x, y))

        Note: The callable passed to :func:`add_validator` must have a signature,
        i.e. builtin functions like ``max`` cannot be used directly, but must be wrapped
        in a lambda.
        """
        self.check_validator(func)
        self.validators[obj].append(func)

    @staticmethod
    def check_validator(func: Callable[[Value, Value], Value]):
        """
        Raises an exception if the given validator function is not compatible with
        this trait.

        :param func: A compatible validator function.
        :type func:  Callable[[Value], Value]
        """
        if len(inspect.signature(func).parameters) != 2:
            raise Exception('The validator must take two arguments.')
