import unittest
from unittest.mock import patch

from traitlite import debug


class TestBreakOnRead(unittest.TestCase):
    def test__get__(self):
        """Test that breakpoint is called when the trait is accessed."""
        class Foo:
            bar = debug.BreakOnRead()

            def __init__(self, bar):
                super().__init__()
                self.bar = bar

        with patch('sys.breakpointhook') as mock:
            # Nothing has been accessed yet.
            foo = Foo(2)
            mock.assert_not_called()

            # Accessing the value should call breakpoint.
            _ = foo.bar
            mock.assert_called_once()


class TestBreakOnWrite(unittest.TestCase):
    def test__set__(self):
        """Test that breakpoint is called on the first set."""
        class Foo:
            bar = debug.BreakOnWrite()

            def __init__(self, bar):
                super().__init__()
                self.bar = bar

        with patch('sys.breakpointhook') as mock:
            # Breakpoint is called on the initial set because the default for
            # ignore_initial is False.
            foo = Foo(2)
            mock.assert_called_once()

            # Breakpoint is called because the value is changed.
            foo.bar += 2
            self.assertEqual(mock.call_count, 2)

    def test__set__with_ignore_initial(self):
        """Test that breakpoint is not called on the first set."""
        class Foo:
            bar = debug.BreakOnWrite(ignore_initial=True)

            def __init__(self, bar):
                super().__init__()
                self.bar = bar

        with patch('sys.breakpointhook') as mock:
            # Breakpoint is not called on the initial set because ignore_initial was set
            # to True.
            foo = Foo(2)
            mock.assert_not_called()

            # Breakpoint is called because the value is changed.
            foo.bar += 2
            mock.assert_called_once()


class TestBreakOnChange(unittest.TestCase):
    def test__set__(self):
        """Test that breaking on a certain value works correctly."""
        # The given callback should call breakpoint when the given value is below 0.
        class Foo:
            bar = debug.BreakOnChange(lambda value: value < 0)

            def __init__(self, bar):
                super().__init__()
                self.bar = bar

        with patch('sys.breakpointhook') as mock:
            foo = Foo(2)
            mock.assert_not_called()

            # Not called because the value is > 0.
            foo.bar = 4
            mock.assert_not_called()

            # Called because the value is < 0.
            foo.bar = -1
            mock.assert_called_once()


class TestBreakOnChangeDelta(unittest.TestCase):
    def test__set__(self):
        """Test that breaking on certain delta changes works correctly."""
        # The given callback should call breakpoint when the new value is lower than the
        # old.
        class Foo:
            bar = debug.BreakOnChangeDelta(lambda old, new: old is not None and new < old)

            def __init__(self, bar):
                super().__init__()
                self.bar = bar

        with patch('sys.breakpointhook') as mock:
            foo = Foo(2)
            mock.assert_not_called()

            # Not called because the new value is higher than the old.
            foo.bar = 4
            mock.assert_not_called()

            # Called because the new value is lower than the old.
            foo.bar = 3
            mock.assert_called_once()
