"""Package import regressions. Run after installing pycrane2s/requirements.txt."""

import pathlib
import subprocess
import sys
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageImportTests(unittest.TestCase):
    def run_python(self, source):
        result = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(source)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_controller_and_presets_are_exported(self):
        self.run_python("""
            from pycrane2s import Crane2S, Crane2SPresets
            from pycrane2s.main import Crane2S as Controller, Crane2SPresets as Presets
            assert Crane2S is Controller
            assert Crane2SPresets is Presets
        """)

    def test_characteristic_constants_remain_exported(self):
        self.run_python("""
            from pycrane2s import WRITE_UUID, NOTIFY_UUID
            from pycrane2s.constants import WRITE_UUID as WRITE, NOTIFY_UUID as NOTIFY
            assert WRITE_UUID == WRITE == 'd44bc439-abfd-45a2-b575-925416129600'
            assert NOTIFY_UUID == NOTIFY == 'd44bc439-abfd-45a2-b575-925416129601'
        """)

    def test_controller_submodule_can_build_packet_offline(self):
        self.run_python("""
            from binascii import crc_hqx
            from pycrane2s.main import Crane2S
            controller = Crane2S('offline-test')
            packet = controller._build_cmd(2, 2048, 1)
            assert controller._client is None
            assert packet[:12] == bytes.fromhex('243c08001812000102000801')
            assert int.from_bytes(packet[12:], 'little') == crc_hqx(packet[4:12], 0)
        """)

    def test_protocol_submodule_can_build_packet(self):
        self.run_python("""
            from pycrane2s.Crane2SProtocol import Crane2SProtocol
            generator = Crane2SProtocol()
            assert generator.pan(2048, 1) == bytes.fromhex('243c0800181200010200080147aa')
        """)

    def test_import_and_construction_do_not_create_ble_client(self):
        self.run_python("""
            from unittest.mock import patch
            with patch('bleak.BleakClient', side_effect=AssertionError('unexpected BLE client')) as client:
                from pycrane2s import Crane2S, Crane2SPresets
                controller = Crane2S('offline-test')
                presets = Crane2SPresets(controller)
                assert presets.gimbal is controller
                client.assert_not_called()
        """)


if __name__ == '__main__':
    unittest.main()
