import abc
from array import array
import logging
import wave

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.util.common.helper import min_max
from coilsnake.util.common.type import StringRepresentationMixin
from coilsnake.util.common.yml import yml_dump


log = logging.getLogger(__name__)

# The offset at which the sample pointer table is stored in SPC memory
SAMPLE_POINTER_TABLE_SPC_OFFSET = 0x6c00
# The maximum number of samples which can be in SPC memory at once
MAX_NUMBER_OF_SAMPLES = 128

# The offset at which the instrument table is stored in SPC memory
INSTRUMENT_TABLE_SPC_OFFSET = 0x6e00
# The maximum number of instruments which can be in SPC memory at once
MAX_NUMBER_OF_INSTRUMENTS = 0xAC

NOTE_STYLE_TABLES_SPC_OFFSET = 0x6F80


class Chunk(StringRepresentationMixin, object):
    def __init__(self, spc_address, data):
        if spc_address + len(data) > 0x10000:
            raise InvalidArgumentError(
                ("Could not create chunk with spc_address[{:#x}] and data of length[{}] as it would exceed "
                 "the bounds of the SPC's memory").format(spc_address, len(data)))

        self.spc_address = spc_address
        self.data = data

    @classmethod
    def create_from_block(cls, block, offset):
        size = block.read_multi(offset, 2)
        spc_address = block.read_multi(offset + 2, 2)
        if size > 0:
            data = block[offset + 4:offset + 4 + size]
        else:
            data = Block()
        return Chunk(spc_address=spc_address, data=data)

    def to_file(self, f):
        data_size = self.data_size()
        f.write(bytearray([data_size & 0xff, data_size >> 8, self.spc_address & 0xff, self.spc_address >> 8]))
        self.data.to_file(f)

    def data_size(self):
        return len(self.data)

    def chunk_size(self):
        return 4 + self.data_size()

    def contains_spc_address(self, spc_address):
        return self.spc_address <= spc_address < (self.spc_address + self.data_size())

    def truncate(self, length):
        self.data = self.data[0:length]


class Sequence(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def create_from_chunk(cls, chunk, bgm_id, sequence_pack_id):
        return ChunkSequence(chunk=chunk, bgm_id=bgm_id, sequence_pack_id=sequence_pack_id)

    @classmethod
    def create_from_spc_address(cls, spc_address, bgm_id, sequence_pack_id):
        return Subsequence(spc_address=spc_address, bgm_id=bgm_id, sequence_pack_id=sequence_pack_id)

    @abc.abstractmethod
    def write_to_project(self, resource_open, sequence_pack_map):
        """Write the sequence to a resource file"""
        return

    @abc.abstractmethod
    def contains_spc_address(self, spc_address):
        """Returns true iff this sequence is contains data at the given address"""
        return

    @abc.abstractmethod
    def get_spc_address(self):
        """Returns the address of this sequence in SPC memory"""
        return


class ChunkSequence(StringRepresentationMixin, Sequence):
    def __init__(self, chunk, bgm_id, sequence_pack_id):
        self.chunk = chunk
        self.bgm_id = bgm_id
        self.sequence_pack_id = sequence_pack_id

    @staticmethod
    def _resource_open_sequence(resource_open, bgm_id):
        return resource_open("Music/sequences/{:03d}".format(bgm_id), "ebm")

    def write_to_project(self, resource_open, sequence_pack_map):
        with ChunkSequence._resource_open_sequence(resource_open, self.bgm_id) as f:
            self.chunk.to_file(f)

    def contains_spc_address(self, spc_address):
        return self.chunk.contains_spc_address(spc_address)

    def get_spc_address(self):
        return self.chunk.spc_address


class Subsequence(StringRepresentationMixin, Sequence):
    def __init__(self, spc_address, bgm_id, sequence_pack_id):
        self.spc_address = spc_address
        self.bgm_id = bgm_id
        self.sequence_pack_id = sequence_pack_id

    @staticmethod
    def _resource_open_sequence(resource_open, bgm_id):
        return resource_open("Music/sequences/{:03d}".format(bgm_id), "yml")

    def write_to_project(self, resource_open, sequence_pack_map):
        # Get a list of possible sequences which this could be a subsequence of.
        # A subsequence can be of any sequence which is loaded. Sequences will only be loaded if they are either in
        # the loaded sequence pack or the program pack (1).
        if self.sequence_pack_id == 0xff:
            possible_sequences = []
        else:
            possible_sequences = sequence_pack_map[self.sequence_pack_id]

        if self.sequence_pack_id != 1 and 1 in sequence_pack_map:
            possible_sequences += sequence_pack_map[1]

        for possible_sequence in possible_sequences:
            if possible_sequence.contains_spc_address(self.spc_address):
                offset_in_sequence = self.spc_address - possible_sequence.get_spc_address()

                yml_rep = {"type": "subsequence",
                           "song": possible_sequence.bgm_id,
                           "offset": offset_in_sequence}
                with Subsequence._resource_open_sequence(resource_open, self.bgm_id) as f:
                    yml_dump(yml_rep=yml_rep, f=f, default_flow_style=False)
                break
        else:
            # This subsequence does not match against any sequence, so it must be invalid.
            # Don't write it to any resources.
            log.error("{} did not match any sequence, not saving it to the project".format(self))

    def contains_spc_address(self, spc_address):
        return False

    def get_spc_address(self):
        return self.spc_address


def _brr_filter_1(brr_waveform, i):
    s = brr_waveform.sampled_waveform[i]\
        + brr_waveform.sampled_waveform[i-1] * 15/16
    brr_waveform.sampled_waveform[i] = min_max(s, -32768, 32767)


def _brr_filter_2(brr_waveform, i):
    s = brr_waveform.sampled_waveform[i]\
        + (brr_waveform.sampled_waveform[i-1] * 61/32)\
        - (brr_waveform.sampled_waveform[i-2] * 15/16)
    brr_waveform.sampled_waveform[i] = min_max(s, -32768, 32767)


def _brr_filter_3(brr_waveform, i):
    s = brr_waveform.sampled_waveform[i]\
        + (brr_waveform.sampled_waveform[i-1] * 115/64)\
        - (brr_waveform.sampled_waveform[i-2] * 13/16)
    brr_waveform.sampled_waveform[i] = min_max(s, -32768, 32767)

_BRR_FILTERS = [None, _brr_filter_1, _brr_filter_2, _brr_filter_3]


class BrrWaveform(object):
    def __init__(self):
        self.sampled_waveform = None
        self.is_looping = False

    def from_block(self, block, offset):
        # First, determine how many sample blocks are in the waveform
        size_in_blocks = 0
        while (block[offset + size_in_blocks] & 1) == 0:
            size_in_blocks += 9
        size_in_blocks /= 9
        size_in_blocks += 1  # The block which included the "end" flag is also part of the waveform

        # Allocate the storage for the waveform's samples
        self.sampled_waveform = array('l', [0] * (size_in_blocks * 16))

        # Set whether this waveform loops, based purely on whether the first sample block has its loop flag set.
        # This may not work for other games, but it's sufficient for EarthBound.
        self.is_looping = block[offset] & 2 == 1

        # Read the samples
        for block_index in xrange(size_in_blocks):
            block_range = block[offset]
            offset += 1
            block_filter = (block_range >> 2) & 3
            if block_filter != 0 and block_index == 0:
                raise InvalidArgumentError("Can't apply filter[{}] to the first sample block in a BRR waveform".format(
                    block_filter))
            block_range >>= 4

            for i in xrange(16):
                s = block[offset + i/2]
                if i & 1 == 0:
                    s >>= 4
                else:
                    s &= 0xf

                if s >= 8:
                    s -= 16

                s <<= block_range

                self.sampled_waveform[block_index*16 + i] = s
            offset += 8

            if block_filter != 0:
                filter_function = _BRR_FILTERS[block_filter]
                for i in xrange(16):
                    filter_function(self, block_index * 16 + i)

    @classmethod
    def create_from_block(cls, block, offset):
        brr = cls()
        brr.from_block(block=block, offset=offset)
        return brr

    def to_wav_file(self, f, sampling_rate):
        wav = wave.open(f)
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sampling_rate)
        wav.writeframes(self.sampled_waveform)
        wav.close()


class EbSample(BrrWaveform):
    def __init__(self):
        super(EbSample, self).__init__()
        self.loop_point = 0

    @classmethod
    def create_from_chunk(cls, chunk, offset, loop_offset):
        loop_offset -= offset
        if loop_offset % 9 != 0:
            raise InvalidArgumentError("EbSample cannot have loop_point at offset[{}] which is not a multiple of 9"
                                       .format(loop_offset))
        sample = EbSample.create_from_block(chunk.data, offset - chunk.spc_address)
        sample.loop_point = loop_offset / 9
        return sample

    @staticmethod
    def _resource_open_wav(resource_open, instrument_set_id, sample_id):
        return resource_open("Music/instrument_sets/{:03d}/samples/{:03d}".format(instrument_set_id, sample_id), "wav")

    def write_wav_to_project(self, resource_open, instrument_set_id, sample_id):
        with EbSample._resource_open_wav(resource_open, instrument_set_id, sample_id) as f:
            self.to_wav_file(f, sampling_rate=32000)

    def yml_rep(self):
        return {"Loop Point": self.loop_point}


class EbInstrument(object):
    def __init__(self):
        self.sample_id = None
        self.adsr_setting_1 = None
        self.adsr_setting_2 = None
        self.gain = None
        self.frequency = None

    def from_block(self, block, offset):
        self.sample_id = block[offset]
        self.adsr_setting_1 = block[offset+1]
        self.adsr_setting_2 = block[offset+2]
        self.gain = block[offset+3]
        self.frequency = block.read_multi(offset+4, 2)

    @classmethod
    def create_from_block(cls, block, offset):
        instrument = EbInstrument()
        instrument.from_block(block, offset)
        return instrument

    def from_chunk(self, chunk, spc_offset):
        self.from_block(chunk.data, spc_offset - chunk.spc_address)

    @classmethod
    def create_from_chunk(cls, chunk, spc_offset):
        instrument = EbInstrument()
        instrument.from_chunk(chunk, spc_offset)
        return instrument

    def yml_rep(self):
        return {"Sample": self.sample_id,
                "ADSR Setting 1": self.adsr_setting_1,
                "ADSR Setting 2": self.adsr_setting_2,
                "Gain": self.gain,
                "Frequency": self.frequency}

    @classmethod
    def block_size(cls):
        return 6


class EbInstrumentSet(object):
    def __init__(self):
        self.samples = []
        self.instruments = []

    def read_from_pack(self, pack):
        chunks_containing_samples = self.read_samples_from_pack(pack)
        self.read_instruments_from_pack(pack, chunks_containing_samples)

    def read_samples_from_pack(self, pack):
        self.samples = [None] * MAX_NUMBER_OF_SAMPLES
        for sample_pointer_chunk_spc_address, sample_pointer_chunk in pack.iteritems():
            if SAMPLE_POINTER_TABLE_SPC_OFFSET <= sample_pointer_chunk_spc_address < \
                    (SAMPLE_POINTER_TABLE_SPC_OFFSET + MAX_NUMBER_OF_SAMPLES * 4):
                break
        else:
            return set()

        chunks_containing_samples = {sample_pointer_chunk_spc_address}

        sample_id = sample_pointer_chunk_spc_address - SAMPLE_POINTER_TABLE_SPC_OFFSET
        for i in range(0, sample_pointer_chunk.data_size(), 4):
            sample_offset = sample_pointer_chunk.data.read_multi(i, 2)
            if sample_offset == 0xffff:
                continue
            log.debug("Reading sample[{}] at spc_offset[{:#x}]".format(sample_id, sample_offset))
            sample_loop_offset = sample_pointer_chunk.data.read_multi(i + 2, 2)

            for sample_chunk in pack.itervalues():
                if sample_chunk.contains_spc_address(sample_offset):
                    break
            else:
                raise InvalidArgumentError("Instrument pack[{}] references sample at {:#x} which it does not contain"
                                           .format(pack, sample_offset))

            self.samples[sample_id] = EbSample.create_from_chunk(sample_chunk, sample_offset, sample_loop_offset)
            chunks_containing_samples.update([sample_chunk.spc_address])
            sample_id += 1

        return chunks_containing_samples

    def read_instruments_from_pack(self, pack, chunks_to_ignore):
        for instrument_chunk_spc_address, instrument_chunk in pack.iteritems():
            if instrument_chunk_spc_address in chunks_to_ignore:
                continue
            if INSTRUMENT_TABLE_SPC_OFFSET <= instrument_chunk_spc_address < \
                    ((INSTRUMENT_TABLE_SPC_OFFSET + MAX_NUMBER_OF_INSTRUMENTS * EbInstrument.block_size())):
                break
        else:
            return
        log.debug("Found instrument chunk[{}]".format(instrument_chunk))

        self.instruments = [None] * MAX_NUMBER_OF_INSTRUMENTS
        instrument_id = (instrument_chunk_spc_address - INSTRUMENT_TABLE_SPC_OFFSET) / EbInstrument.block_size()
        for i in range(instrument_chunk_spc_address, instrument_chunk_spc_address + instrument_chunk.data_size(),
                       EbInstrument.block_size()):
            log.debug("Reading instrument[{}] at spc_offset[{:#x}]".format(instrument_id, i))
            self.instruments[instrument_id] = EbInstrument.create_from_chunk(instrument_chunk, i)
            instrument_id += 1

    @classmethod
    def create_from_pack(cls, pack):
        instrument_set = EbInstrumentSet()
        instrument_set.read_from_pack(pack)
        return instrument_set

    def write_to_project(self, resource_open, instrument_set_id):
        self.write_instruments_to_project(resource_open, instrument_set_id)
        self.write_samples_to_project(resource_open, instrument_set_id)

    @staticmethod
    def _resource_open_instruments(resource_open, instrument_set_id):
        return resource_open("Music/instrument_sets/{:03d}/instruments".format(instrument_set_id), "yml")

    def write_instruments_to_project(self, resource_open, instrument_set_id):
        instruments_yml_rep = dict()
        for instrument_id, instrument in enumerate(self.instruments):
            if instrument:
                instruments_yml_rep[instrument_id] = instrument.yml_rep()

        with EbInstrumentSet._resource_open_instruments(resource_open, instrument_set_id) as f:
            yml_dump(instruments_yml_rep, f, default_flow_style=False)

    @staticmethod
    def _resource_open_samples(resource_open, instrument_set_id):
        return resource_open("Music/instrument_sets/{:03d}/samples".format(instrument_set_id), "yml")

    def write_samples_to_project(self, resource_open, instrument_set_id):
        samples_yml_rep = dict()
        for sample_id, sample in enumerate(self.samples):
            if sample:
                sample.write_wav_to_project(resource_open, instrument_set_id, sample_id)
                samples_yml_rep[sample_id] = sample.yml_rep()

        if samples_yml_rep:
            with EbInstrumentSet._resource_open_samples(resource_open, instrument_set_id) as f:
                yml_dump(samples_yml_rep, f, default_flow_style=False)


class EbNoteStyles(object):
    def __init__(self):
        self.release_settings = None
        self.volumes = None

    def read_from_packs(self, packs):
        for pack in packs:
            if pack:
                for chunk in pack.itervalues():
                    if chunk.contains_spc_address(NOTE_STYLE_TABLES_SPC_OFFSET):
                        break
                else:
                    continue
                break
        else:
            raise InvalidArgumentError("Packs do not contain any note styles data")

        offset = NOTE_STYLE_TABLES_SPC_OFFSET - chunk.spc_address
        self.release_settings = chunk.data[offset:offset+8].to_list()
        self.volumes = chunk.data[offset+8:offset+24].to_list()

    def yml_rep(self):
        return {"Release Settings": self.release_settings,
                "Volumes": self.volumes}

    def write_to_project(self, resource_open):
        with resource_open("Music/note_styles", "yml") as f:
            yml_dump(self.yml_rep(), f, default_flow_style=False)