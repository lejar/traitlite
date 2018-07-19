import collections
import unittest

import hypothesis
from hypothesis.strategies import data, integers, lists

from traitlite import weakref_utilities


class TestOrderedSet(unittest.TestCase):
    def test_inheritance(self):
        """Test that we inherit from collections Set and implement the required methods"""
        # The set from collections is the correct set to inherit from.
        self.assertTrue(issubclass(weakref_utilities.OrderedSet, collections.abc.Set))

        # The interface requires these methods to exist.
        self.assertIn('__contains__', weakref_utilities.OrderedSet.__dict__)
        self.assertIn('__iter__', weakref_utilities.OrderedSet.__dict__)
        self.assertIn('__len__', weakref_utilities.OrderedSet.__dict__)

    @hypothesis.given(lists(integers(), unique=True))
    def test_argument_and_order(self, list_):
        """Test passing an argument to the constructor"""
        oset = weakref_utilities.OrderedSet(list_)
        self.assertSequenceEqual(list(oset), list_)

    @hypothesis.given(lists(integers(), unique=True))
    def test_contains(self, list_):
        """Test querying the presence of an item in the set"""
        oset = weakref_utilities.OrderedSet(list_)
        for item in list_:
            self.assertIn(item, oset)

    @hypothesis.given(lists(integers(), unique=True))
    def test_add(self, list_):
        """Test adding an item to the set"""
        oset = weakref_utilities.OrderedSet()
        self.assertEqual(len(oset), 0)

        for item in list_:
            oset.add(item)
            self.assertIn(item, oset)

        self.assertEqual(len(oset), len(list_))

    @hypothesis.given(lists(integers(), unique=True))
    def test_remove(self, list_):
        """Test removing an item from the set"""
        oset = weakref_utilities.OrderedSet(list_)
        self.assertEqual(len(oset), len(list_))

        for item in list_:
            oset.remove(item)
            self.assertNotIn(item, oset)

        self.assertEqual(len(oset), 0)

    @hypothesis.given(lists(integers(), unique=True))
    def test_clear(self, list_):
        """Test clearing the set"""
        oset = weakref_utilities.OrderedSet(list_)
        self.assertEqual(len(oset), len(list_))
        oset.clear()
        self.assertEqual(len(oset), 0)

    @hypothesis.given(lists(integers(), unique=True))
    def test_pop(self, list_):
        """Test popping an item from the end of the set"""
        oset = weakref_utilities.OrderedSet(list_)
        for item in reversed(list_):
            self.assertEqual(oset.pop(), item)

    @hypothesis.given(lists(integers(), unique=True, min_size=2, max_size=2))
    def test_discard(self, list_):
        """Test discarding an item from the set"""
        a, b = list_
        oset = weakref_utilities.OrderedSet([a])

        # Discarding something not in the set should not cause an error.
        # Anything in the set should remain there.
        oset.discard(b)
        self.assertIn(a, oset)
        self.assertNotIn(b, oset)

        # Discarding something that is in the set should remove it.
        oset.discard(a)
        self.assertNotIn(a, oset)
        self.assertNotIn(b, oset)

    @hypothesis.given(lists(integers(), unique=True))
    def test_str_repr(self, list_):
        oset = weakref_utilities.OrderedSet(list_)

        # The string representation should be the same as a list with
        # parenthesis.
        self.assertEqual(
            str(oset),
            str(list_).replace('[', '(').replace(']', ')'),
        )

        # repr should produce the same output as str.
        self.assertEqual(
            repr(oset),
            str(oset),
        )


class TestOrderedWeakSet(unittest.TestCase):
    def test_gc(self):
        """Test that items are correctly garbage collected"""
        # We use an ordered set to test garbage collecting.
        oset = weakref_utilities.OrderedSet()

        # Adding the ordered set should work like normal.
        wset = weakref_utilities.OrderedWeakSet()
        wset.add(oset)
        self.assertIn(oset, wset)

        # Deleting the ordered set should also remove it from the
        # weakref set.
        del oset
        self.assertEqual(len(wset), 0)


class TestDefaultWeakKeyDictionary(unittest.TestCase):
    def test_factors(self):
        """Test setting the factory for the default values"""
        # A dummy class, since the weakref dict required an object to index.
        class Foo: pass

        # Check a couple of different factory functions.
        for factory in [list, set, dict]:
            dset = weakref_utilities.DefaultWeakKeyDictionary(factory)
            obj = Foo()
            self.assertIsInstance(dset[obj], factory)
