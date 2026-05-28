# bitflyerpy

Python client for [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

[![PyPI](https://img.shields.io/pypi/v/bitflyerpy)](https://pypi.org/project/bitflyerpy/)
[![Python](https://img.shields.io/pypi/pyversions/bitflyerpy)](https://pypi.org/project/bitflyerpy/)
[![CI](https://github.com/ykus4/bitflyerpy/actions/workflows/ci.yml/badge.svg)](https://github.com/ykus4/bitflyerpy/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ykus4/bitflyerpy)](LICENSE)

**[Documentation](https://ykus4.github.io/bitflyerpy)** · [日本語](https://ykus4.github.io/bitflyerpy/ja)

## Installation

```bash
pip install bitflyerpy
```

## Usage

```python
from bitflyerpy import Client

client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
print(client.get_ticker("BTC_JPY"))
```

See the [documentation](https://ykus4.github.io/bitflyerpy) for the full API reference.
