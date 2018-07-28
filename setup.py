from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='traitlite',
    version='0.0.1',
    author='Christopher Pezley',
    author_email='pypi@pezley.net',
    description='A light-weight module that aims to provide control ' \
                'for class attributes.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lejar/traitlite',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
