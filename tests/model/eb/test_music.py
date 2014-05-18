from nose.tools import assert_equal, assert_list_equal, assert_false
from nose.tools.nontrivial import raises
import mock

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.music import Chunk, Sequence, BrrWaveform
from coilsnake.util.common.yml import yml_load
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase


class TestChunk(BaseTestCase, TemporaryWritableFileTestCase):
    TEST_DATA = [
        # Normal case
        {"block data": [0x69, 0x06, 0x00, 0x34, 0x12, 0x01, 0x02, 0x03, 0xff, 0xfe, 0xfd],
         "block offset": 1,
         "spc address": 0x1234,
         "chunk data": [0x01, 0x02, 0x03, 0xff, 0xfe, 0xfd]},
        # Chunk of length 0
        {"block data": [0, 0, 0xab, 0xcd, 9, 10, 11],
         "block offset": 0,
         "spc address": 0xcdab,
         "chunk data": []},
        # Chunk at the edge of SPC memory
        {"block data": [1, 0, 0xff, 0xff, 9, 10, 11],
         "block offset": 0,
         "spc address": 0xffff,
         "chunk data": [9]},
    ]

    def test_create_from_block(self):
        for test_case in TestChunk.TEST_DATA:
            block_data, block_offset, expected_spc_address, expected_chunk_data = \
                test_case["block data"], test_case["block offset"], test_case["spc address"], test_case["chunk data"]
            block = Block()
            block.from_list(block_data)
            chunk = Chunk.create_from_block(block, block_offset)

            assert_list_equal(chunk.data.to_list(), expected_chunk_data)
            assert_equal(chunk.data_size(), len(expected_chunk_data))
            assert_equal(chunk.chunk_size(), len(expected_chunk_data) + 4)
            assert_equal(chunk.spc_address, expected_spc_address)

    @raises(InvalidArgumentError)
    def test_init_out_of_spc_memory_bounds(self):
        Chunk(spc_address=0xffff, data=[1, 2])

    def test_to_file(self):
        for test_case in TestChunk.TEST_DATA:
            block_data, block_offset, expected_spc_address, expected_chunk_data = \
                test_case["block data"], test_case["block offset"], test_case["spc address"], test_case["chunk data"]
            block = Block()
            block.from_list(block_data)
            chunk = Chunk.create_from_block(block, block_offset)

            with open(self.temporary_wo_file_name, "w") as f:
                chunk.to_file(f)
            with open(self.temporary_wo_file_name, "r") as f:
                file_data = list(bytearray(f.read()))

            assert_equal(file_data, block_data[block_offset:block_offset+chunk.chunk_size()])


class TestSubsequence(BaseTestCase, TemporaryWritableFileTestCase):
    def test_to_resource(self):
        subsequence = Sequence.create_from_spc_address(spc_address=0x1001, bgm_id=52, sequence_pack_id=2)
        sequence_pack_map = {
            2: [Sequence.create_from_chunk(chunk=Chunk(spc_address=0x3000, data=[1, 2, 3]),
                                           bgm_id=49,
                                           sequence_pack_id=2),
                Sequence.create_from_chunk(chunk=Chunk(spc_address=0x1000, data=[1, 2]),
                                           bgm_id=51,
                                           sequence_pack_id=2)],
            1: [Sequence.create_from_chunk(chunk=Chunk(spc_address=0x2000, data=[1, 2]),
                                           bgm_id=32,
                                           sequence_pack_id=1)],
        }

        subsequence.to_resource(resource_open=self.resource_open_temporary_wo_file,
                                sequence_pack_map=sequence_pack_map)
        with open(self.temporary_wo_file_name, "r") as f:
            subsequence_yml = yml_load(f)
            assert_equal(subsequence_yml["type"], "subsequence")
            assert_equal(subsequence_yml["song"], 51)
            assert_equal(subsequence_yml["offset"], 1)

    def test_to_resource_no_sequence_pack(self):
        subsequence = Sequence.create_from_spc_address(spc_address=0x1001, bgm_id=52, sequence_pack_id=0xff)
        sequence_pack_map = {
            1: [Sequence.create_from_chunk(chunk=Chunk(spc_address=0x3000, data=[1, 2, 3]),
                                           bgm_id=49,
                                           sequence_pack_id=2),
                Sequence.create_from_chunk(chunk=Chunk(spc_address=0x1000, data=[1, 2]),
                                           bgm_id=51,
                                           sequence_pack_id=2)],
            2: [Sequence.create_from_chunk(chunk=Chunk(spc_address=0x2000, data=[1, 2]),
                                           bgm_id=32,
                                           sequence_pack_id=1)],
        }

        subsequence.to_resource(resource_open=self.resource_open_temporary_wo_file,
                                sequence_pack_map=sequence_pack_map)
        with open(self.temporary_wo_file_name, "r") as f:
            subsequence_yml = yml_load(f)
            assert_equal(subsequence_yml["type"], "subsequence")
            assert_equal(subsequence_yml["song"], 51)
            assert_equal(subsequence_yml["offset"], 1)

    def test_to_resource_no_match(self):
        subsequence = Sequence.create_from_spc_address(spc_address=0x1001, bgm_id=52, sequence_pack_id=2)
        sequence_pack_map = {
            1: [],
            2: []
        }

        resource_open = mock.Mock()
        subsequence.to_resource(resource_open=resource_open,
                                sequence_pack_map=sequence_pack_map)
        assert_false(resource_open.called)

    def test_contains_spc_address(self):
        subsequence = Sequence.create_from_spc_address(spc_address=0x1001, bgm_id=52, sequence_pack_id=2)
        assert_false(subsequence.contains_spc_address(0x1000))

    def test_get_spc_address(self):
        subsequence = Sequence.create_from_spc_address(spc_address=0x1001, bgm_id=52, sequence_pack_id=2)
        assert_equal(subsequence.get_spc_address(), 0x1001)


class TestBrrWaveform(BaseTestCase):
    TEST_DATA = [
        # Filter 0, no shifting
        {"block data": [0b00000000, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
                        0b00000001, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45],
         "block offset": 0,
         "sampled waveform": [0, 1, 2, 3, 4, 5, 6, 7, -8, -7, -6, -5, -4, -3, -2, -1,
                              3, 1, 4, 1, 5, -7, 2, 6, -8, 6, 7, -8, 2, 3, 4, 5],
         "is looping": False},
        # Filter 0, with shifting
        {"block data": [0b00110010, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
                        0b10000011, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45],
         "block offset": 0,
         "sampled waveform": [0, 1 << 3, 2 << 3, 3 << 3, 4 << 3, 5 << 3, 6 << 3, 7 << 3, -8 << 3, -7 << 3, -6 << 3,
                              -5 << 3, -4 << 3, -3 << 3, -2 << 3, -1 << 3,
                              3 << 8, 1 << 8, 4 << 8, 1 << 8, 5 << 8, -7 << 8, 2 << 8, 6 << 8, -8 << 8, 6 << 8,
                              7 << 8, -8 << 8, 2 << 8, 3 << 8, 4 << 8, 5 << 8],
         "is looping": True},
        # Filter 1
        {"block data": [9, 0b11000000, 0, 0, 0, 0, 0, 0, 0, 4,
                        0b10000101, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45],
         "block offset": 1,
         "sampled waveform": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16384,
                              16128, 15376, 15439, 14730, 15089, 12353, 12092, 12872, 10019, 10928, 12037, 9236, 9170,
                              9364, 9802, 10469],
         "is looping": False},
        # Filter 2
        {"block data": [0b01100000, 0, 0, 0, 0, 0, 0, 0, 0x84,
                        0b01001001, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45],
         "block offset": 0,
         "sampled waveform": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -512, 256,
                              1016, 1712, 2375, 2938, 3454, 3718, 3881, 4009, 3876, 3726, 3581, 3205, 2784, 2351,
                              1935, 1564],
        "is looping": False},
        # Filter 2 then Filter 3
        {"block data": [0b01100000, 0, 0, 0, 0, 0, 0, 0, 0x84,
                        0b01001000, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45,
                        0b01011101, 0xde, 0xad, 0xbe, 0xef, 0xc0, 0x01, 0xf0, 0x0f],
         "block offset": 0,
         "sampled waveform": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -512, 256,
                              1016, 1712, 2375, 2938, 3454, 3718, 3881, 4009, 3876, 3726, 3581, 3205, 2784, 2351,
                              1935, 1564,
                              1142, 718, 171, -372, -967, -1499, -1972, -2358, -2763, -3049, -3234, -3302, -3338,
                              -3315, -3244, -3168],
        "is looping": False}

    ]

    def test_from_block(self):
        for test_case in TestBrrWaveform.TEST_DATA:
            block_data, block_offset, expected_sample_waveform, expected_is_looping = \
                test_case["block data"], test_case["block offset"], test_case["sampled waveform"],\
                test_case["is looping"]
            block = Block.create_from_list(block_data)
            brr = BrrWaveform.create_from_block(block, block_offset)

            assert_list_equal(brr.sampled_waveform.tolist(), expected_sample_waveform)

    @raises(InvalidArgumentError)
    def test_from_block_using_filter_too_early(self):
        block = Block.create_from_list([0b00001101, 0, 0, 0, 0, 0, 0, 0, 0])
        BrrWaveform.create_from_block(block, 0)