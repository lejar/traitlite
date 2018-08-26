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

.. automodule:: traitlite
    :members:
