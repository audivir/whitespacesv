# whitespacesv

Parser and serializer for the WSV (Whitespace Separated Values) format, with a Rust core
exposed to Python through PyO3.

## Prerequisites

- Python >=3.10, \<3.15

## Installation

```shell
pip install whitespacesv
```

## Usage

```python
from whitespacesv import WsvDocument, from_polars, to_polars

document = WsvDocument.parse("a b c\nd e f\n")
document.serialize("compact")
document.to_string()
document.save("output.wsv")

loaded = WsvDocument.load("output.wsv")

frame = to_polars(document)
from_polars(frame)
```

## Acknowledgments

Ported from [stenway/WSV-Python](https://github.com/Stenway/WSV-Python) by Stefan John / Stenway,
originally released under the MIT license. See `NOTICE` for details.

## License

MIT
