from nose.tools import assert_equal, assert_list_equal, assert_false, assert_dict_equal, assert_is_not_none, \
    assert_is_none
from nose.tools.nontrivial import raises
import mock

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.music import Chunk, Sequence, BrrWaveform, EbSample, EbInstrument, EbInstrumentSet, \
    MAX_NUMBER_OF_SAMPLES
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

        subsequence.write_to_project(resource_open=self.resource_open_temporary_wo_file,
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

        subsequence.write_to_project(resource_open=self.resource_open_temporary_wo_file,
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
        subsequence.write_to_project(resource_open=resource_open,
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
        {"block data": [0b11000000, 0, 0, 0, 0, 0, 0, 0, 4,
                        0b10000101, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45],
         "block offset": 0,
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


class TestEbSample(BaseTestCase):
    def test_from_block(self):
        for test_case in TestBrrWaveform.TEST_DATA:
            block_data, block_offset, expected_sample_waveform, expected_is_looping = \
                test_case["block data"], test_case["block offset"], test_case["sampled waveform"],\
                test_case["is looping"]
            chunk_data = [len(block_data) & 0xff, len(block_data) >> 8, 0x23, 0xa1] + block_data
            block = Block.create_from_list(chunk_data)
            chunk = Chunk.create_from_block(block, 0)

            assert_list_equal(chunk.data.to_list(), block_data)
            assert_equal(chunk.spc_address, 0xa123)

            sample = EbSample.create_from_chunk(chunk, 0xa123, 0xa123 + 9)
            assert_list_equal(sample.sampled_waveform.tolist(), expected_sample_waveform)
            assert_dict_equal(sample.yml_rep(), {"Loop Point": 1})

    @raises(InvalidArgumentError)
    def test_from_block_invalid_loop_point(self):
        test_case = TestBrrWaveform.TEST_DATA[0]

        block_data, block_offset, expected_sample_waveform, expected_is_looping = \
            test_case["block data"], test_case["block offset"], test_case["sampled waveform"],\
            test_case["is looping"]
        chunk_data = [len(block_data) & 0xff, len(block_data) >> 8, 0x23, 0xa1] + block_data
        block = Block.create_from_list(chunk_data)
        chunk = Chunk.create_from_block(block, 0)

        EbSample.create_from_chunk(chunk, 0xa123, 0xa123 + 7)


class TestEbInstrument(BaseTestCase):
    TEST_DATA = [
        {"block data": [6, 1, 2, 3, 4, 5],
         "block offset": 0,
         "yml rep": {"Sample": 6,
                     "ADSR Setting 1": 1,
                     "ADSR Setting 2": 2,
                     "Gain": 3,
                     "Frequency": 0x504}
         }
    ]

    def test_create_from_block(self):
        for test_case in TestEbInstrument.TEST_DATA:
            block_data, block_offset, yml_rep =\
                test_case["block data"], test_case["block offset"], test_case["yml rep"]
            block = Block.create_from_list(block_data)

            inst = EbInstrument.create_from_block(block, block_offset)
            assert_dict_equal(inst.yml_rep(), yml_rep)
            assert_equal(inst.block_size(), 6)

    def test_create_from_chunk(self):
        for test_case in TestEbInstrument.TEST_DATA:
            block_data, block_offset, yml_rep =\
                test_case["block data"], test_case["block offset"], test_case["yml rep"]
            chunk_data = [len(block_data) & 0xff, len(block_data) >> 8, 0x23, 0xa1] + block_data
            block = Block.create_from_list(chunk_data)
            chunk = Chunk.create_from_block(block, 0)

            inst = EbInstrument.create_from_chunk(chunk, 0xa123)
            assert_dict_equal(inst.yml_rep(), yml_rep)
            assert_equal(inst.block_size(), 6)


class TestEbInstrumentSet(BaseTestCase):
    TEST_DATA = [
        {
            # Happy case
            "pack": {
                0x6c04: Chunk.create_from_list(  # sample pointer table
                    spc_address=0x6c04,
                    data_list=[0x00, 0x80, 0x09, 0x80,
                               0xff, 0xff, 0x00, 0x00,
                               0x12, 0x80, 0x1b, 0x80]),
                0x8000: Chunk.create_from_list(  # samples
                    spc_address=0x8000,
                    data_list=[0b00000000, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
                               0b00000001, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45,
                               0b11000000, 0, 0, 0, 0, 0, 0, 0, 4,
                               0b10000101, 0x31, 0x41, 0x59, 0x26, 0x86, 0x78, 0x23, 0x45])},
            "samples": {
                1: EbSample.create_from_list(
                    data_list=[0, 1, 2, 3, 4, 5, 6, 7, -8, -7, -6, -5, -4, -3, -2, -1,
                               3, 1, 4, 1, 5, -7, 2, 6, -8, 6, 7, -8, 2, 3, 4, 5],
                    loop_point=1),
                3: EbSample.create_from_list(
                    data_list=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16384,
                               16128, 15376, 15439, 14730, 15089, 12353, 12092, 12872, 10019, 10928, 12037, 9236, 9170,
                               9364, 9802, 10469],
                    loop_point=1)},
        },
        {
            # No samples in pack
            "pack": {},
            "samples": {}
        }
    ]

    def test_read_samples_from_pack(self):
        for test_case in TestEbInstrumentSet.TEST_DATA:
            pack = test_case["pack"]
            samples = test_case["samples"]

            inst_set = EbInstrumentSet()
            inst_set.read_samples_from_pack(pack)

            for i in range(MAX_NUMBER_OF_SAMPLES):
                if i in samples:
                    assert_is_not_none(inst_set.samples[i])
                    assert_equal(inst_set.samples[i], samples[i])
                else:
                    assert_is_none(inst_set.samples[i])

    @raises(InvalidArgumentError)
    def test_read_samples_from_pack_not_in_pack(self):
        inst_set = EbInstrumentSet()
        inst_set.read_samples_from_pack({
            0x6c00: Chunk.create_from_list(  # sample pointer table
                    spc_address=0x6c00,
                    data_list=[0x00, 0x80, 0x09, 0x80]),
        })