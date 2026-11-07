# py-crane2s
Control over the Zhiyun Crane 2s gimbal via Python

## Offline regression tests

With Python 3.10 or newer, run from the repository root:

```sh
python -m pip install -r pycrane2s/requirements.txt
python -m unittest discover -s tests -v
```

These tests check package imports, exported classes and constants, and packet
construction without connecting to Bluetooth hardware. Package imports currently
require Bleak, including imports of the protocol submodule.
