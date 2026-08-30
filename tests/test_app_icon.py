import unittest
from pathlib import Path

from PIL import Image


MATERIAL_DIR = Path(__file__).parents[1] / 'utils' / 'material'


class AppIconTest(unittest.TestCase):
    def test_png_icon_has_real_transparency(self):
        with Image.open(MATERIAL_DIR / 'app_icon.png') as icon:
            self.assertEqual(icon.size, (1024, 1024))
            self.assertEqual(icon.mode, 'RGBA')
            self.assertEqual(icon.getchannel('A').getextrema(), (0, 255))

    def test_ico_contains_required_windows_sizes(self):
        with Image.open(MATERIAL_DIR / 'app_icon.ico') as icon:
            sizes = icon.info.get('sizes', set())

        self.assertTrue({(16, 16), (32, 32), (48, 48),
                         (128, 128), (256, 256)}.issubset(sizes))


if __name__ == '__main__':
    unittest.main()
