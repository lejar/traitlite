from typing import Callable, Type

from .traits import (
    BaseTrait,
    HasCallback,
    HasCallbackDelta,
    Owner,
    Value,
)


class BreakOnRead(BaseTrait):
    """
    A trait which starts the debugger when it is accessed. The method called to
    start the debugger is the one set in the PYTHONBREAKPOINT environment
    variable, or `pdb.set_trace` if the variable is not defined.
    ::

        from traitlite import BreakOnRead

        class Foo:
            bar = BreakOnRead()

            def __init__(self, bar):
                self.bar = bar

        foo = Foo(3)
        print(foo.bar) # breakpoint() is called here.
    """
    def __get__(self, obj: Owner, objtype: Type[Owner]) -> Value:
        breakpoint()
        return super().__get__(obj, objtype)


class BreakOnWrite(BaseTrait):
    """
    A trait which starts the debugger when it is accessed. The method called to
    start the debugger is the one set in the PYTHONBREAKPOINT environment
    variable, or `pdb.set_trace` if the variable is not defined.
    ::

        from traitlite import BreakOnWrite

        class Foo:
            bar = BreakOnWrite(ignore_initial=True)

            def __init__(self, bar):
                self.bar = bar

        foo = Foo(3) # breakpoint is not called because of ignore_initial=True
        foo.bar = 4 # breakpoint() is called here.
    """
    def __init__(self, ignore_initial: bool = False) -> None:
        """
        :param ignore_initial: True if the first setting should not trigger
                               breakpoint.
        :type ignore_initial:  bool
        """
        super().__init__()
        self.ignore_initial = ignore_initial

    def __set__(self, obj: Owner, value: Value) -> None:
        if not self.ignore_initial:
            breakpoint()
        self.ignore_initial = False
        super().__set__(obj, value)


class BreakOnChange(HasCallback):
    """
    A trait which starts the debugger when its value causes the specified callback
    to return True.
    ::

        from traitlite import BreakOnChange

        class Foo:
            bar = BreakOnChange(lambda value: value < 0)

            def __init__(self, bar):
                self.bar = bar

        foo = Foo(3)
        foo.bar = 2 # breakpoint() is NOT called here.
        foo.bar = -1 # breakpoint() is called here.
    """
    def __init__(self, callback: Callable[[Value], bool]) -> None:
        def break_on_true(value: Value) -> None:
            """Call breakpoint if the specified callback evaluates to True."""
            if callback(value):
                breakpoint()

        # Pass the callback to the HasCallback base to be called when the value is
        # changed.
        super().__init__([break_on_true])


class BreakOnChangeDelta(HasCallbackDelta):
    """
    A trait which starts the debugger when its old and new values cause the specified
    callback to return True.
    ::

        from traitlite import BreakOnChangeDelta

        class Foo:
            bar = BreakOnChangeDelta(lambda old, new: old is not None and new < old)

            def __init__(self, bar):
                self.bar = bar

        foo = Foo(3)
        foo.bar = 5 # The new value is higher, so breakpoint is NOT called.
        foo.bar = 4 # The new value is lower, so breakpoint is called.
    """
    def __init__(self, callback: Callable[[Value, Value], bool]) -> None:
        def break_on_true(old: Value, new: Value) -> None:
            """Call breakpoint if the specified callback evaluates to True."""
            if callback(old, new):
                breakpoint()

        # Pass the callback to the HasCallback base to be called when the value is
        # changed.
        super().__init__([break_on_true])
