## PyOPath

Test-status: [![Status](https://github.com/DrInfiniteExplorer/pyopath/actions/workflows/python-package.yml/badge.svg)](https://github.com/DrInfiniteExplorer/pyopath/actions/workflows/python-package.yml)


### Overview

PyOPath is a Python library designed to facilitate querying structures of
objects within application space. Inspired by XPath, JSONPath, and ObjectPath,
PyOPath extends the querying capabilities beyond traditional XML and JSON
documents to include a broader range of data structures.

### Key Features

- **Flexible Querying**: PyOPath allows querying of any kind of model as long
  as it meets certain criteria, expanding beyond the limitations of XML and
  JSON documents.
  
- **Application Space Integration**: Unlike traditional querying libraries,
  PyOPath enables querying directly within the application's data structures,
  leveraging Python's runtime introspection capabilities.

### Getting Started

To begin using PyOPath in your project:

1. Install PyOPath via pip:

    ```bash
    pip install pyopath
    ```

2. Import PyOPath into your Python script:

    ```python
    import pyopath
    ```

3. Start querying your application's data structures using PyOPath's compact
   syntax.

### Example

    ```python
    # Assume we have a data structure 'my_data' representing a nested dictionary

    my_data = {
        "name": "John",
        "age": 30,
        "address": {
            "city": "New York",
            "zipcode": "10001"
        },
        "pets": [
            {"type": "dog", "name": "Buddy"},
            {"type": "cat", "name": "Whiskers"}
        ]
    }

    # Querying the data structure with PyOPath

    result = pyopath.query(my_data, "/address/city")
    print(result)  # Output: "New York"

    ```

### Roadmap

Currently, PyOPath is focused on building a robust XPath AST. Future plans
 include expanding query capabilities and enhancing integration with various
 data structures and application models.

### Contributing

Contributions to PyOPath are welcome! Feel free to submit bug reports,
 feature requests, or pull requests via GitHub.

### License

PyOPath is licensed under the MIT License. See the LICENSE file for details.

# Notes and links

ply docs
https://github.com/dabeaz/ply/blob/master/doc/ply.md
https://ply.readthedocs.io/en/latest/ply.html

good parser review
https://tratt.net/laurie/blog/2020/which_parsing_approach.html

another xpathy thing using ply
https://github.com/emory-libraries/eulxml/blob/master/eulxml/xpath/__init__.py

parsing c with ply
https://github.com/dabeaz/ply/blob/master/example/ansic/cparse.py

Sanxion documentation
https://www.saxonica.com/documentation12/index.html#!expressions

xpath language reference
https://www.w3.org/TR/xpath-31/#doc-xpath31-PostfixExpr


