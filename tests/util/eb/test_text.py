# coding: utf-8
from coilsnake.util.eb.text import standard_text_to_block, CharacterSubstitutions, standard_text_to_byte_list
from coilsnake.model.common.blocks import Block

from tests.coilsnake_test import BaseTestCase


class EbTextTestCase(BaseTestCase):
    def test_standard_text_to_block(self):
        b = Block()

        b.from_list([0] * 10)
        standard_text_to_block(block=b, offset=0, text="Test", max_length=10)
        self.assertListEqual(b.to_list(), [132, 149, 163, 164, 0, 0, 0, 0, 0, 0])

        b.from_list([0x66] * 10)
        standard_text_to_block(block=b, offset=0, text="Test", max_length=10)
        self.assertListEqual(b.to_list(), [132, 149, 163, 164, 0, 0x66, 0x66, 0x66, 0x66, 0x66])


    def test_standard_text_to_block_too_long(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="12345678901", max_length=10)


    def test_standard_text_to_block_with_brackets(self):
        b = Block()

        b.from_list([0] * 10)
        standard_text_to_block(block=b, offset=0, text="[01 02 03 04]", max_length=10)
        self.assertListEqual(b.to_list(), [0x01, 0x02, 0x03, 0x04, 0, 0, 0, 0, 0, 0])

        b.from_list([0] * 10)
        standard_text_to_block(block=b, offset=0, text="[]", max_length=10)
        self.assertListEqual(b.to_list(), [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        b.from_list([0] * 10)
        standard_text_to_block(block=b, offset=0, text="Te[ab cd ef]st", max_length=10)
        self.assertListEqual(b.to_list(), [132, 149, 0xab, 0xcd, 0xef, 163, 164, 0, 0, 0])


    def test_standard_text_to_block_with_brackets_not_two_digits(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="[1 02 03 04]", max_length=10)


    def test_standard_text_to_block_with_brackets_not_hex(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="[ag]", max_length=10)


    def test_standard_text_to_block_with_brackets_not_ended_with_bracket(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="[01 02 03", max_length=10)


    def test_standard_text_to_block_with_brackets_too_long(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="[01 02 03 04 05 06 07 08 09 0a 0b]", max_length=10)


    def test_standard_text_to_block_with_brackets_too_long2(self):
        b = Block()
        b.from_list([0] * 10)
        with self.assertRaises(ValueError):
            standard_text_to_block(block=b, offset=0, text="abcd[01 02 03 04 05 06 07]", max_length=10)


    def test_standard_text_to_byte_list_replacement(self):
        CharacterSubstitutions.character_substitutions = {'A': 'B'}
        self.assertListEqual([114, 114, 115, 116, 114, 117, 118, 119, 114],
                          standard_text_to_byte_list("ABCDAEFGA", 9))


    def test_standard_text_to_byte_list_replacement_unicode(self):
        CharacterSubstitutions.character_substitutions = {'я': 'B'}
        self.assertListEqual([114, 114, 115, 116, 114, 117, 118, 119, 114],
                          standard_text_to_byte_list("яBCDяEFGя", 9))
