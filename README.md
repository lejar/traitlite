[![Build Status](https://travis-ci.org/lejar/traitlite.svg?branch=master)](https://travis-ci.org/lejar/traitlite)

# traitlite

Traitlite is a light-weight (MIT-licensed) package which provides certain [descriptors](https://docs.python.org/3/howto/descriptor.html) to help control the attributes in a class, such as making them read-only<sup>\*</sup> or providing type-checking whenever the value is set. The documentation has examples for every trait, so check it out!

<sup>\*</sup> well, as read-only as you can get in python

## Installation

The easiest way to install traitlite is through pip:

```bash
pip install traitlite
```

## Running the tests

Traitlite uses the builtin python unit testing framework, along with [hypothesis](https://hypothesis.works/). Additionally, [cosmic-ray](https://github.com/sixty-north/cosmic-ray) is used for mutation testing.

To install the dependencies required to run the tests, run:
```bash
pip install -r unittest_requirements.txt
```
This will install both hypothesis and cosmic-ray.

To run the tests, simply execute the following from the package directory:

```bash
python setup.py test
```

To run mutation testing, execute:
```bash
python setup.py crtest
```

If you want to get the [coverage](https://github.com/nedbat/coveragepy) of the tests, execute:

```bash
python setup.py coverage
```

## Documentation

The docs can be found [here](https://traitlite.readthedocs.io/en/latest/). Alternatively, if you want to build them yourself simply run

```bash
make <target>
```
in the docs folder of the project. To see a list of all the different targets, simply run make without any arguments.
