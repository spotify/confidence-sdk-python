import unittest

from sdk.names import FlagName, VariantName


class NamesTest(unittest.TestCase):
    def test_flag_name_valid(self):
        self.assertEqual(str(FlagName("myFlag")), "flags/myFlag")

    def test_flag_parse(self):
        flag_name = FlagName.parse("flags/myFlag")
        self.assertEqual(flag_name.flag, "myFlag")
        self.assertEqual(str(flag_name), "flags/myFlag")

    def test_flag_parse_error(self):
        self.assertRaises(ValueError, FlagName.parse, "myFlag")

    def test_variant_parse(self):
        variant = VariantName.parse("flags/test-flag-2/variants/variant-1")
        self.assertEqual(variant.flag, "test-flag-2")
        self.assertEqual(variant.variant, "variant-1")

    def test_variant_parse_error(self):
        self.assertRaises(ValueError, VariantName.parse, "myFlag/variants/variant-1")
        self.assertRaises(ValueError, VariantName.parse, "flag/test-flag-2/variant-1")
        self.assertRaises(ValueError, VariantName.parse, "variant-1")


if __name__ == "__main__":
    unittest.main()
