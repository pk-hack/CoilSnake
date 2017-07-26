from nose.tools import assert_equal, raises, assert_list_equal, assert_raises

from coilsnake.model.common.blocks import Block
from coilsnake.exceptions.common.exceptions import InvalidArgumentError, MissingUserDataError, InvalidUserDataError
from coilsnake.model.eb.pointers import EbPointer, EbTextPointer
from coilsnake.exceptions.eb.exceptions import InvalidEbTextPointerError
from tests.coilsnake_test import BaseTestCase


class TestEbPointer(BaseTestCase):
    def setup(self):
        self.pointer = EbPointer()
        EbPointer.label_address_map["a.b"] = 0x1314ab

    @raises(InvalidArgumentError)
    def test_zero_size(self):
        EbPointer(size=0)

    @raises(InvalidArgumentError)
    def test_negative_size(self):
        EbPointer(size=-1)

    def test_from_block(self):
        block = Block()
        block.from_list(list(range(0, 0x100)))

        self.pointer.from_block(block, 0)
        assert_equal(self.pointer.address, 0x020100)
        self.pointer.from_block(block, 5)
        assert_equal(self.pointer.address, 0x070605)
        self.pointer.from_block(block, 0xfd)
        assert_equal(self.pointer.address, 0xfffefd)

    def test_to_block(self):
        block = Block()
        block.from_list(list(range(1, 6)))

        self.pointer.address = 0xabcdef
        self.pointer.to_block(block, 1)
        assert_list_equal(block[0:5].to_list(), [1, 0xef, 0xcd, 0xab, 5])

    def test_from_yml_rep(self):
        self.pointer.from_yml_rep("$123456")
        assert_equal(self.pointer.address, 0x123456)
        self.pointer.from_yml_rep("a.b")
        assert_equal(self.pointer.address, 0x1314ab)

        assert_raises(MissingUserDataError, self.pointer.from_yml_rep, None)
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "$")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "not.real_label")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, True)

    def test_yml_rep(self):
        self.pointer.address = 0xfe4392
        assert_equal(self.pointer.yml_rep(), "$fe4392")


class TestEbTextPointer(BaseTestCase):
    def setup(self):
        self.pointer = EbTextPointer(size=4)

    def test_from_block(self):
        block = Block()
        block.from_list([0xc0, 0xc1, 0xc2, 0x00,
                         0xff, 0xff, 0xff, 0x00,
                         0xef, 0xfe, 0x02, 0x00,
                         0x01, 0x02, 0x03, 0x01])

        self.pointer.from_block(block, 0)
        assert_equal(self.pointer.address, 0xc2c1c0)
        self.pointer.from_block(block, 4)
        assert_equal(self.pointer.address, 0xffffff)

        assert_raises(InvalidEbTextPointerError, self.pointer.from_block, block, 8)
        assert_raises(InvalidEbTextPointerError, self.pointer.from_block, block, 12)

    def test_from_yml_rep(self):
        self.pointer.from_yml_rep("$c30201")
        assert_equal(self.pointer.address, 0xc30201)

        assert_raises(InvalidEbTextPointerError, self.pointer.from_yml_rep, "$070102")
        assert_raises(InvalidEbTextPointerError, self.pointer.from_yml_rep, "$1000000")