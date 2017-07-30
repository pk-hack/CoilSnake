import os

from nose.tools import assert_equal

from coilsnake.util.common.yml import replace_field_in_yml, convert_values_to_hex_repr
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase, TEST_DATA_DIR, assert_files_equal


class TestReplaceFieldInYml(BaseTestCase, TemporaryWritableFileTestCase):
    def test_replace_field_in_yml(self):
        with open(os.path.join(TEST_DATA_DIR, "yml", "sample.yml"), "r") as sample_yml:
            def resource_open_r(name, extension, astext):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                assert_equal(astext, True)
                return open(os.path.join(TEST_DATA_DIR, "yml", "sample.yml"), encoding="utf-8", newline="\n")

            def resource_open_r2(name, extension, astext):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                assert_equal(astext, True)
                return open(self.temporary_wo_file_name, "r", encoding="utf-8", newline="\n")

            def resource_open_w(name, extension, astext):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                assert_equal(astext, True)
                return open(self.temporary_wo_file_name, "w", encoding="utf-8", newline="\n")

            replace_field_in_yml(resource_name="sample_resource",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Action type",
                                 new_key="Cool fish type")
            replace_field_in_yml(resource_name="sample_resource",
                                 resource_open_r=resource_open_r2,
                                 resource_open_w=resource_open_w,
                                 key="Target",
                                 value_map={"none": "nobody",
                                            "one": "just one guy"})
            replace_field_in_yml(resource_name="sample_resource",
                                 resource_open_r=resource_open_r2,
                                 resource_open_w=resource_open_w,
                                 key="Direction",
                                 new_key="Where At",
                                 value_map={"party": "back at ya",
                                            "enemy": "at them"})

            with open(self.temporary_wo_file_name, "r", encoding="utf-8", newline="\n") as f:
                print(f.read())

            with open(os.path.join(TEST_DATA_DIR, "yml", "sample-replaced.yml"), "r", encoding="utf-8", newline="\n") as f1:
                with open(self.temporary_wo_file_name, "r", encoding="utf-8", newline="\n") as f2:
                    assert_files_equal(f1, f2)


def test_convert_values_to_hex_repr():
    assert_equal(convert_values_to_hex_repr("ABC: 0", "ABC"), "ABC: 0x0")
    assert_equal(convert_values_to_hex_repr("ABC: 55", "ABC"), "ABC: 0x37")
    assert_equal(convert_values_to_hex_repr("ABC: 55", "ABCD"), "ABC: 55")
    assert_equal(convert_values_to_hex_repr("A:\n  - {ABC: 16}", "ABC"), "A:\n  - {ABC: 0x10}")