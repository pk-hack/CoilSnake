# coding: utf-8
from nose.tools import assert_list_equal
from nose.tools.nontrivial import raises

from coilsnake.util.eb.text import standard_text_to_block, CharacterSubstitutions, standard_text_to_byte_list
from coilsnake.model.common.blocks import Block


def test_standard_text_to_block():
    b = Block()

    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="Test", max_length=10)
    assert_list_equal(b.to_list(), [132, 149, 163, 164, 0, 0, 0, 0, 0, 0])

    b.from_list([0x66] * 10)
    standard_text_to_block(block=b, offset=0, text="Test", max_length=10)
    assert_list_equal(b.to_list(), [132, 149, 163, 164, 0, 0x66, 0x66, 0x66, 0x66, 0x66])


@raises(ValueError)
def test_standard_text_to_block_too_long():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="12345678901", max_length=10)


def test_standard_text_to_block_with_brackets():
    b = Block()

    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[01 02 03 04]", max_length=10)
    assert_list_equal(b.to_list(), [0x01, 0x02, 0x03, 0x04, 0, 0, 0, 0, 0, 0])

    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[]", max_length=10)
    assert_list_equal(b.to_list(), [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="Te[ab cd ef]st", max_length=10)
    assert_list_equal(b.to_list(), [132, 149, 0xab, 0xcd, 0xef, 163, 164, 0, 0, 0])


@raises(ValueError)
def test_standard_text_to_block_with_brackets_not_two_digits():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[1 02 03 04]", max_length=10)


@raises(ValueError)
def test_standard_text_to_block_with_brackets_not_hex():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[ag]", max_length=10)


@raises(ValueError)
def test_standard_text_to_block_with_brackets_not_ended_with_bracket():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[01 02 03", max_length=10)


@raises(ValueError)
def test_standard_text_to_block_with_brackets_too_long():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="[01 02 03 04 05 06 07 08 09 0a 0b]", max_length=10)


@raises(ValueError)
def test_standard_text_to_block_with_brackets_too_long2():
    b = Block()
    b.from_list([0] * 10)
    standard_text_to_block(block=b, offset=0, text="abcd[01 02 03 04 05 06 07]", max_length=10)


def test_standard_text_to_byte_list_replacement():
    CharacterSubstitutions.character_substitutions = {'A': 'B'}
    assert_list_equal([114, 114, 115, 116, 114, 117, 118, 119, 114],
                      standard_text_to_byte_list("ABCDAEFGA", 9))


def test_standard_text_to_byte_list_replacement_unicode():
    CharacterSubstitutions.character_substitutions = {'я': 'B'}
    assert_list_equal([114, 114, 115, 116, 114, 117, 118, 119, 114],
                      standard_text_to_byte_list("яBCDяEFGя", 9))