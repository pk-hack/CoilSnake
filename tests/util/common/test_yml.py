import os

from nose.tools import assert_equal

from coilsnake.util.common.yml import replace_field_in_yml
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase, TEST_DATA_DIR, assert_files_equal


class TestReplaceFieldInYml(BaseTestCase, TemporaryWritableFileTestCase):
    def test_replace_field_in_yml(self):
        with open(os.path.join(TEST_DATA_DIR, "yml", "sample.yml"), "r") as sample_yml:
            def resource_open_r(name, extension):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                return open(os.path.join(TEST_DATA_DIR, "yml", "sample.yml"))

            def resource_open_r2(name, extension):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                return open(self.temporary_wo_file_name, "r")

            def resource_open_w(name, extension):
                assert_equal(name, "sample_resource")
                assert_equal(extension, "yml")
                return open(self.temporary_wo_file_name, "w")

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

            print (open(self.temporary_wo_file_name, "r")).read()

            assert_files_equal(
                open(os.path.join(TEST_DATA_DIR, "yml", "sample-replaced.yml"), "r"),
                open(self.temporary_wo_file_name, "r"))