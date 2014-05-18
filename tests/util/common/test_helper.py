from nose.tools import assert_equal

from coilsnake.util.common.helper import min_max


def test_min_max():
    assert_equal(min_max(5, 1, 10), 5)
    assert_equal(min_max(0, 1, 10), 1)
    assert_equal(min_max(11, 1, 10), 10)