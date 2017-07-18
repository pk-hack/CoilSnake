from PIL import Image, ImageDraw

from coilsnake.exceptions.common.exceptions import InvalidArgumentError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.util.common.type import EqualityMixin


SWIRL_IMAGE_PALETTE = EbPalette(num_subpalettes=1, subpalette_length=2,
                                rgb_list=[255, 255, 255, 0, 0, 0])


class SwirlFrameRow(EqualityMixin):
    def __init__(self, x1=0, x2=0, x3=0, x4=0):
        self.set(x1, x2, x3, x4)

    def set(self, x1, x2, x3, x4):
        self.x1 = x1
        self.x2 = x2
        self.x3 = x3
        self.x4 = x4

    def from_block(self, block, offset, is_mode_01):
        self.x1 = block[offset]
        self.x2 = block[offset+1]
        if is_mode_01:
            self.x3 = 0xff
            self.x4 = 0
        else:
            self.x3 = block[offset+2]
            self.x4 = block[offset+3]

    def to_block(self, block, offset, is_mode_01):
        if is_mode_01 and self.x3 != 0xff and self.x4 != 0:
            raise InvalidArgumentError("Cannot write row with two lines in only two bytes")
        block[offset] = self.x1
        block[offset+1] = self.x2
        if not is_mode_01:
            block[offset+2] = self.x3
            block[offset+3] = self.x4

    def from_image_data(self, image_data, y):
        x1, x2, x3, x4 = None, None, None, None
        for x in range(256):
            if x1 is None:
                if image_data[x, y] == 1:
                    x1 = x
            elif x2 is None:
                if image_data[x, y] == 0:
                    x2 = x-1
            elif x3 is None:
                if image_data[x, y] == 1:
                    x3 = x
            elif x4 is None:
                if image_data[x, y] == 0:
                    x4 = x-1
            else:
                if image_data[x, y] == 1:
                    raise InvalidArgumentError("There are more than two lines on the same row at y={}".format(y))

        if x1 is None:
            self.x1 = 0xff
            self.x2 = 0
        elif x2 is None:
            self.x1 = x1
            self.x2 = 0xff
        else:
            if x1 == x2:
                raise InvalidArgumentError("Line at ({},{}) must be at least 2 pixels wide".format(x1, y))
            self.x1 = x1
            self.x2 = x2

        if x3 is None:
            self.x3 = 0xff
            self.x4 = 0
        elif x4 is None:
            self.x3 = x3
            self.x4 = 0xff
        else:
            if x3 == x4:
                raise InvalidArgumentError("Line at ({},{}) must be at least 2 pixels wide".format(x1, y))
            self.x3 = x3
            self.x4 = x4

    def __repr__(self):
        return "<{}(x1={},x2={},x3={},x4={})>".format(
            self.__class__.__name__, self.x1, self.x2, self.x3, self.x4
        )


class SwirlFrame(object):
    def __init__(self):
        self.rows = [SwirlFrameRow() for i in range(224)]

    def from_block(self, block, offset):
        is_mode_01 = block[offset] == 1
        num_of_scanlines = block[offset+1]
        offset += 2

        current_scanline = 0

        while num_of_scanlines > 0:
            if num_of_scanlines & 0x80 == 0:  # repeating mode
                for i in range(current_scanline, current_scanline + num_of_scanlines):
                    self.rows[i].from_block(block, offset, is_mode_01)

                if is_mode_01:
                    offset += 2
                else:
                    offset += 4
            else:  # continuous mode
                num_of_scanlines -= 0x80

                for i in range(current_scanline, current_scanline + num_of_scanlines):
                    self.rows[i].from_block(block, offset, is_mode_01)

                    if is_mode_01:
                        offset += 2
                    else:
                        offset += 4

            current_scanline += num_of_scanlines
            num_of_scanlines = block[offset]
            offset += 1

    def block_rep(self):
        # First, find out if this frame should use "Mode 01" or not.
        # Mode 01 restricts each scanline to only having one line instead of two, but it saves space in storage
        is_mode_01 = True
        for row in self.rows:
            if row.x3 != 0xff and row.x4 != 0:
                is_mode_01 = False
                break

        # Next, figure out how this data is going to be written to the ROM
        frame_schema = []
        y = 0
        current_continuous_entry_size = 0
        while y < len(self.rows):
            row = self.rows[y]
            if y + 1 < len(self.rows) and row == self.rows[y+1]:
                # If we're currently in the middle of a continuous entry, complete it
                if current_continuous_entry_size != 0:
                    frame_schema.append((y - current_continuous_entry_size, False, current_continuous_entry_size))
                    current_continuous_entry_size = 0

                # Find out how many repetitions there are
                repetitions = 2
                for x in self.rows[y+2:]:
                    if row == x:
                        repetitions += 1
                    else:
                        break

                # There can only be 0x7f repetitions at maximum
                if repetitions >= 0x80:
                    repetitions = 0x7f
                frame_schema.append((y, True, repetitions))
                y += repetitions
            else:
                # There can only be 0x7f scanlines in a continuous entry
                if current_continuous_entry_size == 0x7f:
                    frame_schema.append((y - 0x7f, False, 0x7f))
                    current_continuous_entry_size = 0
                current_continuous_entry_size += 1
                y += 1
        if current_continuous_entry_size != 0:
            frame_schema.append((y - current_continuous_entry_size, False, current_continuous_entry_size))

        # After that, figure out how much space this will take up in the block
        data_len = 2
        for y, is_repeat, size in frame_schema:
            data_len += 1
            if is_repeat:
                if is_mode_01:
                    data_len += 2
                else:
                    data_len += 4
            else:
                if is_mode_01:
                    data_len += 2 * size
                else:
                    data_len += 4 * size

        # Create a block
        block = Block(size=data_len)
        offset = 0

        # Finally, write the data to the block
        if is_mode_01:
            block[offset] = 1
        else:
            block[offset] = 4
        offset += 1
        for y, is_repeat, size in frame_schema:
            if is_repeat:
                block[offset] = size
                offset += 1
                self.rows[y].to_block(block, offset, is_mode_01)
                if is_mode_01:
                    offset += 2
                else:
                    offset += 4
            else:
                block[offset] = size | 0x80
                offset += 1

                for row in self.rows[y:y+size]:
                    row.to_block(block, offset, is_mode_01)
                    if is_mode_01:
                        offset += 2
                    else:
                        offset += 4
        block[offset] = 0

        # Return the block
        return block

    def image(self):
        image = Image.new("P", (256, 224), None)
        self.to_image(image)
        return image

    def to_image(self, image):
        SWIRL_IMAGE_PALETTE.to_image(image)
        draw = ImageDraw.Draw(image)
        for y, row in enumerate(self.rows):
            draw.line((0, y, 255, y), fill=0)
            if row.x1 != 0xff and row.x1 < row.x2:
                draw.line((row.x1, y, row.x2, y), fill=1)
                if row.x3 != 0xff and row.x3 < row.x4:
                    draw.line((row.x3, y, row.x4, y), fill=1)

    def from_image(self, image):
        image_data = image.load()
        for y, row in enumerate(self.rows):
            row.from_image_data(image_data, y)


class Swirl(object):
    def __init__(self, speed=0):
        self.speed = speed
        self.frames = []

    def frames_from_block(self, block, frame_offsets):
        self.frames = [SwirlFrame() for i in frame_offsets]
        for frame, frame_offset in zip(self.frames, frame_offsets):
            frame.from_block(block, frame_offset)

    def frames_to_block(self, block):
        frame_offsets = []
        for frame in self.frames:
            offset, length = frame.to_block(block)
            frame_offsets.append(offset)
        return frame_offsets

    def add_frame_from_image(self, image):
        frame = SwirlFrame()
        frame.from_image(image)
        self.frames.append(frame)


def write_swirl_frames(block, swirl, all_frame_hashes):
    frame_blocks = [x.block_rep() for x in swirl.frames]
    frame_hashes = [hash(x) for x in frame_blocks]
    offsets = []
    for frame_block, frame_hash in zip(frame_blocks, frame_hashes):
        if frame_hash in all_frame_hashes:
            offsets.append(all_frame_hashes[frame_hash])
        else:
            offset = block.allocate(data=frame_block)
            all_frame_hashes[frame_hash] = offset
            offsets.append(offset)
    return offsets