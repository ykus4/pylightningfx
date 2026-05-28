# pylightningfx

Python client for [bitFlyer Lightning API](https://lightning.bitflyer.com/docs).

[![PyPI](https://img.shields.io/pypi/v/pylightningfx)](https://pypi.org/project/pylightningfx/)
[![Python](https://img.shields.io/pypi/pyversions/pylightningfx)](https://pypi.org/project/pylightningfx/)
[![CI](https://github.com/ykus4/pylightningfx/actions/workflows/ci.yml/badge.svg)](https://github.com/ykus4/pylightningfx/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ykus4/pylightningfx)](LICENSE)

**[Documentation](https://ykus4.github.io/pylightningfx)** · [日本語](https://ykus4.github.io/pylightningfx/ja)

## Installation

```bash
pip install pylightningfx
```

## Usage

```python
from pylightningfx import Client

client = Client(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
print(client.get_ticker("BTC_JPY"))
```

See the [documentation](https://ykus4.github.io/pylightningfx) for the full API reference.
