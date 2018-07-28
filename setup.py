from setuptools import setup, find_packages

setup(
    name='traitlite',
    version='0.0.1',
    author='Christopher Pezley',
    author_email='pypi@pezley.net',
    description='A light-weight module that aims to provide control ' \
                'for class attributes.',
    url='https://github.com/lejar/traitlite',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
