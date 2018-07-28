import inspect
import unittest
from unittest.mock import MagicMock

import hypothesis

from traitlite import traits


def magic_mock_with_single_argument(*args, **kwargs):
    mock = MagicMock(*args, **kwargs)
    mock.__signature__ = inspect.signature(lambda _: None)
    return mock


def magic_mock_with_two_arguments(*args, **kwargs):
    mock = MagicMock(*args, **kwargs)
    mock.__signature__ = inspect.signature(lambda _1, _2: None)
    return mock


def strategy_BaseTrait():
    """
    A strategy that returns anything in the traits submodule that inherits from
    BaseTrait.
    """
    return hypothesis.strategies.sampled_from([
        obj[1] for obj in inspect.getmembers(traits)
        if isinstance(obj[1], type) and issubclass(obj[1], traits.BaseTrait)
    ])


def strategy_Types():
    """
    A strategy that returns any kind of type with a default constructor.
    """
    types = []
    for type_ in __builtins__.values():
        if not isinstance(type_, type):
            continue

        try:
            type_()
            types.append(type_)
        except Exception:
            continue

    return hypothesis.strategies.sampled_from(types)


class TestBaseTrait(unittest.TestCase):
    @hypothesis.given(strategy_BaseTrait())
    def test__set_name__(self, Trait):
        """Test that combined traits get the correct name."""
        class Foo:
            bar = Trait.__new__(Trait)
            fizz = Trait.__new__(Trait) + Trait.__new__(Trait)

        self.assertEqual(Foo.bar.name, 'bar')
        self.assertEqual(Foo.fizz.name, 'fizz')

    def test__get__and__set__(self):
        """Test that __get__ and __set__ work correctly."""
        class Foo:
            bar = traits.BaseTrait()

        foo = Foo()
        self.assertNotIn(foo, Foo.bar.value)

        obj = object()
        foo.bar = obj
        self.assertIn(foo, Foo.bar.value)
        self.assertIs(Foo.bar.value[foo], obj)
        self.assertIs(foo.bar, obj)

    @hypothesis.given(strategy_BaseTrait(), strategy_BaseTrait())
    def test__dict__on__add__(self, Trait_1, Trait_2):
        """Test that the state of a combined trait is correct."""
        fizz = object()
        foo = object()
        trait_1 = Trait_1.__new__(Trait_1)
        trait_1.__dict__['fizz'] = fizz
        trait_1.__dict__['foobar'] = foo

        buzz = object()
        bar = object()
        trait_2 = Trait_2.__new__(Trait_2)
        trait_2.__dict__['buzz'] = buzz
        trait_1.__dict__['foobar'] = bar

        new_obj = trait_1 + trait_2
        self.assertIs(new_obj.fizz, fizz)
        self.assertIs(new_obj.buzz, buzz)
        self.assertIs(new_obj.foobar, bar)

    @hypothesis.given(strategy_BaseTrait(), strategy_BaseTrait())
    def test_mro_on__add__(self, Trait_1, Trait_2):
        """Test that the mro for combined traits is correct."""
        trait_1 = Trait_1.__new__(Trait_1)
        trait_2 = Trait_2.__new__(Trait_2)
        new_trait = trait_1 + trait_2

        self.assertIsInstance(new_trait, Trait_1)
        self.assertIsInstance(new_trait, Trait_2)

    @hypothesis.given(strategy_BaseTrait(), strategy_BaseTrait())
    def test_class_name_on__add__(self, Trait_1, Trait_2):
        """Test that combined traits get the correct name."""
        trait_1 = Trait_1.__new__(Trait_1)
        trait_2 = Trait_2.__new__(Trait_2)
        new_trait = trait_1 + trait_2

        # HasCallback and HasValidator have a special ordering when added.
        if isinstance(trait_1, traits._BaseHasValidator) and \
                isinstance(trait_2, traits._BaseHasCallback):
            trait_1, trait_2 = trait_2, trait_1

        self.assertEqual(
            new_trait.__class__.__name__,
            '_'.join([trait_1.__class__.__name__, trait_2.__class__.__name__]),
        )

    def test_use_before_set(self):
        """Test that an AttributeError is raised when the property is accessed before it is set."""
        class Foo:
            a = traits.BaseTrait()

        foo = Foo()
        with self.assertRaises(AttributeError):
            foo.a

    def test_incorrect_add(self):
        """Test that adding a non-BaseTrait will raise an exception."""
        with self.assertRaisesRegex(Exception, 'only be added'):
            traits.BaseTrait() + 3


class TestReadOnly(unittest.TestCase):
    def test_is_read_only(self):
        class Foo:
            a = traits.ReadOnly()
        foo = Foo()

        # The first time it is set is okay.
        foo.a = 3

        # The second time should raise an exception.
        with self.assertRaisesRegex(Exception, 'read-only'):
            foo.a = 4


class TestTypeChecked(unittest.TestCase):
    @hypothesis.given(strategy_Types(), strategy_Types())
    def test_typechecking_different_types(self, type_1, type_2):
        """Test that setting a different type will raise an exception."""
        # Make sure that the second type is not the same type as the first.
        hypothesis.assume(not issubclass(type_2, type_1))

        class Foo:
            a = traits.TypeChecked(type_1)
        foo = Foo()

        # The same type as specified is okay.
        foo.a = type_1()

        # A different type should raise an exception.
        with self.assertRaisesRegex(Exception, 'is of type'):
            foo.a = type_2()

    @hypothesis.given(strategy_Types())
    def test_typechecking_same_types(self, type_1):
        """Test that the type checking works correctly with subclasses."""
        # Booleans are the only non-subclassable objects in python.
        hypothesis.assume(type_1 != bool)

        class Foo:
            a = traits.TypeChecked(type_1)
        foo = Foo()

        # The same type as specified is okay.
        foo.a = type_1()

        # Create a subclass of the type, which should be okay.
        NewType = type('NewType', (type_1,), {})
        foo.a = NewType()

        # A sub-subclass should also be okay.
        NewestType = type('NewestType', (NewType,), {})
        foo.a = NewestType()

    @hypothesis.given(hypothesis.strategies.booleans())
    def test_bool_int_checking(self, boolean):
        """Test that bools and ints are not interchangable as types."""
        # Bool is actually a subclass of int, so make sure that we properly handle it.
        class Foo:
            a = traits.TypeChecked(int)
        foo = Foo()

        self.assertIsInstance(boolean, int)

        with self.assertRaisesRegex(Exception, 'is of type'):
            foo.a = boolean


class TestHasCallback(unittest.TestCase):
    def test_add_callback(self):
        """Test adding a callback on a HasCallback trait."""
        class Foo:
            a = traits.HasCallback()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        callback = magic_mock_with_single_argument()
        Foo.a.add_callback(foo, callback)

        # The callback should be in the list.
        self.assertIn(foo, Foo.a.callbacks)
        self.assertIn(callback, Foo.a.callbacks[foo])

        # Changing the value should call the callback.
        callback.assert_not_called()
        foo.a = 5
        callback.assert_called_with(5)

    def test_add_bad_callback(self):
        """Test adding a callback which takes a wrong number of arguments."""
        class Foo:
            a = traits.HasCallback()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        callback = magic_mock_with_two_arguments()
        with self.assertRaisesRegex(Exception, 'a single'):
            Foo.a.add_callback(foo, callback)


class TestHasCallbackDelta(unittest.TestCase):
    def test_add_callback(self):
        """Test adding a callback on a HasCallback trait."""
        class Foo:
            a = traits.HasCallbackDelta()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        callback = magic_mock_with_two_arguments()
        Foo.a.add_callback(foo, callback)

        # The callback should be in the list.
        self.assertIn(foo, Foo.a.callbacks)
        self.assertIn(callback, Foo.a.callbacks[foo])

        # Changing the value should call the callback.
        callback.assert_not_called()
        foo.a = 5
        callback.assert_called_with(None, 5)

    def test_add_bad_callback(self):
        """Test adding a callback which takes a wrong number of arguments."""
        class Foo:
            a = traits.HasCallbackDelta()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        callback = magic_mock_with_single_argument()
        with self.assertRaisesRegex(Exception, 'take two'):
            Foo.a.add_callback(foo, callback)


class TestHasValidator(unittest.TestCase):
    def test_add_validator(self):
        """Test adding a validator on a HasValidator trait."""
        class Foo:
            a = traits.HasValidator()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        validator_1 = magic_mock_with_single_argument(return_value=3)
        validator_2 = magic_mock_with_single_argument(return_value=4)
        Foo.a.add_validator(foo, validator_1)
        Foo.a.add_validator(foo, validator_2)

        # The validator should be in the list.
        self.assertIn(foo, Foo.a.validators)
        self.assertIn(validator_1, Foo.a.validators[foo])
        self.assertIn(validator_2, Foo.a.validators[foo])

        # Changing the value should call the validator.
        validator_1.assert_not_called()
        validator_2.assert_not_called()
        foo.a = 5

        # The value passed to each validator should change with the return values of the
        # previous ones.
        validator_1.assert_called_with(5)
        validator_2.assert_called_with(3)
        self.assertEqual(foo.a, 4)

    def test_callback_validator_mixup(self):
        """Test that the order of HasCallback and HasValidator will not cause problems."""
        class Foo:
            a = traits.HasCallback() + traits.HasValidator()
        foo = Foo()
        foo.a = None

        callback = magic_mock_with_single_argument()
        validator = magic_mock_with_single_argument(return_value=5)

        Foo.a.add_callback(foo, callback)
        Foo.a.add_validator(foo, validator)
        foo.a = 4

        callback.assert_called_with(5)
        validator.assert_called_with(4)

    def test_callback_validator_correct_order(self):
        """Test the order of HasCallback and HasValidator when 'correct'."""
        class Foo:
            a = traits.HasValidator() + traits.HasCallback()
        foo = Foo()
        foo.a = None

        callback = magic_mock_with_single_argument()
        validator = magic_mock_with_single_argument(return_value=5)

        Foo.a.add_callback(foo, callback)
        Foo.a.add_validator(foo, validator)
        foo.a = 4

        callback.assert_called_with(5)
        validator.assert_called_with(4)

    def test_add_bad_validator(self):
        """Test adding a validator that takes the wrong number of arguments."""
        class Foo:
            a = traits.HasValidator()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        validator = magic_mock_with_two_arguments(return_value=3)
        with self.assertRaisesRegex(Exception, 'a single'):
            Foo.a.add_validator(foo, validator)


class TestHasValidatorDelta(unittest.TestCase):
    def test_add_validator(self):
        """Test adding a validator on a HasValidator trait."""
        class Foo:
            a = traits.HasValidatorDelta()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        validator_1 = magic_mock_with_two_arguments(return_value=3)
        validator_2 = magic_mock_with_two_arguments(return_value=4)
        Foo.a.add_validator(foo, validator_1)
        Foo.a.add_validator(foo, validator_2)

        # The validator should be in the list.
        self.assertIn(foo, Foo.a.validators)
        self.assertIn(validator_1, Foo.a.validators[foo])
        self.assertIn(validator_2, Foo.a.validators[foo])

        # Changing the value should call the validator.
        validator_1.assert_not_called()
        validator_2.assert_not_called()
        foo.a = 5

        # The value passed to each validator should change with the return values of the
        # previous ones.
        validator_1.assert_called_with(None, 5)
        validator_2.assert_called_with(5, 3)
        self.assertEqual(foo.a, 4)

    def test_add_bad_validator(self):
        """Test adding a validator that takes the wrong number of arguments."""
        class Foo:
            a = traits.HasValidatorDelta()
        foo = Foo()

        # Create a callback function - here a mock - and add it.
        validator = magic_mock_with_single_argument(return_value=3)
        with self.assertRaisesRegex(Exception, 'take two'):
            Foo.a.add_validator(foo, validator)


class TestResolve_mro(unittest.TestCase):
    def test_resolve_mro(self):
        """Test resolving the mro of multiple objects."""
        class A: pass
        class B(A): pass
        class C(B): pass
        class D(A): pass

        # Make sure that A only shows up once and that the order is correct.
        self.assertEqual(
            traits.resolve_mro(C(), D()),
            (D, C, B, A, object),
        )
