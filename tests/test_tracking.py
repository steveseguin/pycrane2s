"""Offline tracking regressions: python -m unittest discover -s tests -v.

Install pycrane2s/requirements.txt first. The controller module is loaded directly
so these tests are independent of the separate package-initializer import fix.
"""

import binascii
import importlib.util
import pathlib
import unittest
from unittest.mock import AsyncMock


PATH = pathlib.Path(__file__).resolve().parents[1] / 'pycrane2s' / 'main.py'
SPEC = importlib.util.spec_from_file_location('crane_controller_under_test', PATH)
CONTROLLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROLLER)


class TrackingTests(unittest.IsolatedAsyncioTestCase):
    async def test_tracking_calls_existing_normalized_motion_methods(self):
        controller = CONTROLLER.Crane2S('offline-test')
        controller.pan_pct = AsyncMock()
        controller.tilt_pct = AsyncMock()
        presets = CONTROLLER.Crane2SPresets(controller)

        await presets.track_2d(480, 270, 1920, 1080, speed_pct=0.25)

        controller.pan_pct.assert_awaited_once_with(-0.5, 0.25)
        controller.tilt_pct.assert_awaited_once_with(0.5, 0.25)

    async def test_tracking_builds_both_packets_through_real_controller(self):
        controller = CONTROLLER.Crane2S('offline-test')
        writes = []

        class RecordingTransport:
            async def write_gatt_char(self, uuid, payload, response):
                writes.append((uuid, bytes(payload), response))

        controller._client = RecordingTransport()
        presets = CONTROLLER.Crane2SPresets(controller)
        targets = [
            (960, 540, 2048, 2048),
            (0, 0, 1, 1),
            (1920, 1080, 4095, 4095),
            (0, 1080, 1, 4095),
            (1920, 0, 4095, 1),
            (480, 270, 1024, 1024),
        ]
        for x, y, pan, tilt in targets:
            with self.subTest(x=x, y=y):
                before = len(writes)
                await presets.track_2d(x, y, 1920, 1080, speed_pct=0.25)
                self.assertEqual(len(writes), before + 2)
                for index, (command, value) in enumerate(((2, pan), (1, tilt))):
                    uuid, packet, response = writes[before + index]
                    self.assertEqual(uuid, controller.write_uuid)
                    self.assertFalse(response)
                    self.assertEqual(len(packet), 14)
                    self.assertEqual(packet[:6], bytes.fromhex('243c08001812'))
                    self.assertEqual(packet[6], (before + index) & 0xff)
                    self.assertEqual(packet[7], 1)
                    self.assertEqual(packet[8], command)
                    self.assertEqual(int.from_bytes(packet[9:11], 'little'), value)
                    self.assertEqual(packet[11], 63)
                    self.assertEqual(int.from_bytes(packet[12:], 'little'),
                                     binascii.crc_hqx(packet[4:12], 0))

    async def test_named_preset_control_uses_same_public_methods(self):
        controller = CONTROLLER.Crane2S('offline-test')
        controller.pan_pct = AsyncMock()
        controller.tilt_pct = AsyncMock()
        presets = CONTROLLER.Crane2SPresets(controller)
        presets.save_preset('center', 0, 0)
        await presets.goto_preset('center', speed_pct=0.5)
        controller.pan_pct.assert_awaited_once_with(0, 0.5)
        controller.tilt_pct.assert_awaited_once_with(0, 0.5)


if __name__ == '__main__':
    unittest.main()
