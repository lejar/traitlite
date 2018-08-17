.. traitlite documentation master file, created by
   sphinx-quickstart on Sat Jul 21 21:44:05 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Traitlite
=====================================

Traitlite is a package which provides simple descriptors which you can use as class attributes to provide functionality such as type checking, variable validation, callbacks, making a variable read-only, etc. It does not require you to subclass anything in order to start using it.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Basic Example
=============

In order to use a trait, simply define it as a class attribute for your variable.
::

    from traitlite import TypeChecked
    class Foo:
        bar = TypeChecked(int)
    
        def __init__(self, bar):
            self.bar = bar
    
    Foo(3) # Is fine
    Foo(3.0) # Raises exception

Accessing your variable is done just like with any normal variable.
::

    foo = Foo(3)
    print(foo.bar) # 3

To get the actual traitlite instance, access the class attribute (capital F in Foo).
::

    print(Foo.bar) # <traitlite.traits.TypeChecked object at 0x10f1334a8>

To use different properties at the same time, simply add the traits to your variable.
::

    from traitlite import ReadOnly, TypeChecked
    class Foo:
        bar = TypeChecked(int) + ReadOnly()
    
        def __init__(self, bar):
            self.bar = bar
    
    Foo(3.0) # Raises exception
    foo = Foo(3) # Okay
    foo.b = 2 # Raises exception because of read-only


Traits Documentation
====================

.. class:: traitlite.ReadOnly

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

.. class:: traitlite.TypeChecked(type_)

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


.. class:: traitlite.HasCallback

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

    .. function:: add_callback(obj: Owner, func: Callable[[Value], NoneType]) -> NoneType

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

.. class:: traitlite.HasCallbackDelta

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

    .. function:: add_callback(obj: Owner, func: Callable[[Value, Value], NoneType]) -> NoneType:

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

.. class:: traitlite.HasValidator

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

    .. function:: add_validator(obj: Owner, func: Callable[[Value], Value]) -> NoneType:

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

.. class:: traitlite.HasValidatorDelta

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

    .. function:: add_validator(obj: Owner, func: Callable[[Value, Value], Value]) -> NoneType

        Adds a validator to be called before the value is changed. The validator
        must be a callable object which takes the old and new values as its arguments
        and must return the value which should be used.

        For example, a validator which only accepts increases in value would be:
        ::

            ObjClass.add_validator(obj, lambda x, y: max(x, y))

        Note: The callable passed to :func:`add_validator` must have a signature,
        i.e. builtin functions like ``max`` cannot be used directly, but must be wrapped
        in a lambda.


.. AutoDoc
.. =======

.. .. automodule:: traitlite
..     :members:
