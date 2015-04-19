from nose.tools import assert_equal, assert_list_equal

from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.swirls import SwirlFrameRow, SwirlFrame
from tests.coilsnake_test import SwirlTestCase


class TestSwirlFrameRow(SwirlTestCase):
    def test_from_image_data(self):
        image_data = self.swirl_1_img.load()
        s = SwirlFrameRow()

        s.from_image_data(image_data=image_data, y=0)
        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=0xff, x4=0), s)

        s.from_image_data(image_data=image_data, y=1)
        assert_equal(SwirlFrameRow(x1=0xfe, x2=0xff, x3=0xff, x4=0), s)

        s.from_image_data(image_data=image_data, y=2)
        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=0xfe, x4=0xff), s)

        s.from_image_data(image_data=image_data, y=3)
        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=3, x4=4), s)

        s.from_image_data(image_data=image_data, y=4)
        assert_equal(SwirlFrameRow(x1=0xff, x2=0, x3=0xff, x4=0), s)

    def test_from_block(self):
        block = Block()
        block.from_list([1, 2, 4, 5, 6])
        s = SwirlFrameRow()

        s.from_block(block, 0, False)
        assert_equal(SwirlFrameRow(x1=1, x2=2, x3=4, x4=5), s)

        s.from_block(block, 3, True)
        assert_equal(SwirlFrameRow(x1=5, x2=6, x3=0xff, x4=0), s)

    def test_to_block(self):
        block = Block()

        s = SwirlFrameRow(x1=3, x2=5, x3=55, x4=92)
        block.from_list([33, 33, 33, 33, 33])
        s.to_block(block, 1, False)
        assert_equal([33, 3, 5, 55, 92], block.to_list())

        s = SwirlFrameRow(x1=3, x2=5, x3=0xff, x4=0)
        block.from_list([33, 33, 33, 33, 33])
        s.to_block(block, 2, True)
        assert_equal([33, 33, 3, 5, 33], block.to_list())


class TestSwirlFrame(SwirlTestCase):
    def test_from_image(self):
        s = SwirlFrame()
        s.from_image(self.swirl_1_img)

        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=0xff, x4=0), s.rows[0])
        assert_equal(SwirlFrameRow(x1=0xfe, x2=0xff, x3=0xff, x4=0), s.rows[1])
        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=0xfe, x4=0xff), s.rows[2])
        assert_equal(SwirlFrameRow(x1=0, x2=1, x3=3, x4=4), s.rows[3])
        assert_equal(SwirlFrameRow(x1=0xff, x2=0, x3=0xff, x4=0), s.rows[4])

    def test_from_block_repeating_mode_01(self):
        s = SwirlFrame()
        block = Block()
        block.from_list([1,
                         0x7f, 1, 2,
                         97, 3, 4,
                         0])
        s.from_block(block, 0)

        assert_equal(len(s.rows), 224)
        for row in s.rows[0:0x7f]:
            assert_equal(SwirlFrameRow(x1=1, x2=2, x3=0xff, x4=0), row)
        for row in s.rows[0x7f:]:
            assert_equal(SwirlFrameRow(x1=3, x2=4, x3=0xff, x4=0), row)

    def test_from_block_repeating_not_mode_01(self):
        s = SwirlFrame()
        block = Block()
        block.from_list([0,
                         0x7e, 0, 50, 120, 126,
                         98, 0, 0xff, 0xff, 0,
                         0])
        s.from_block(block, 0)

        assert_equal(len(s.rows), 224)
        for row in s.rows[0:0x7e]:
            assert_equal(SwirlFrameRow(x1=0, x2=50, x3=120, x4=126), row)
        for row in s.rows[0x7e:]:
            assert_equal(SwirlFrameRow(x1=0, x2=0xff, x3=0xff, x4=0), row)

    def test_from_block_continuous_mode_01(self):
        s = SwirlFrame()
        block = Block()
        block.from_list([1,
                         0x7f, 1, 2,
                         0x82, 50, 51, 52, 53,
                         95, 3, 4,
                         0])
        s.from_block(block, 0)

        assert_equal(len(s.rows), 224)
        for row in s.rows[0:0x7f]:
            assert_equal(SwirlFrameRow(x1=1, x2=2, x3=0xff, x4=0), row)
        assert_equal(SwirlFrameRow(x1=50, x2=51, x3=0xff, x4=0), s.rows[0x7f])
        assert_equal(SwirlFrameRow(x1=52, x2=53, x3=0xff, x4=0), s.rows[0x80])
        for row in s.rows[0x81:]:
            assert_equal(SwirlFrameRow(x1=3, x2=4, x3=0xff, x4=0), row)

    def test_from_block_continuous_not_mode_01(self):
        s = SwirlFrame()
        block = Block()
        block.from_list([0,
                         0x7f, 0, 50, 120, 126,
                         0x82, 50, 51, 52, 53, 54, 55, 0xff, 0,
                         95, 0, 0xff, 0xff, 0,
                         0])
        s.from_block(block, 0)

        assert_equal(len(s.rows), 224)
        for row in s.rows[0:0x7f]:
            assert_equal(SwirlFrameRow(x1=0, x2=50, x3=120, x4=126), row)
        assert_equal(SwirlFrameRow(x1=50, x2=51, x3=52, x4=53), s.rows[0x7f])
        assert_equal(SwirlFrameRow(x1=54, x2=55, x3=0xff, x4=0), s.rows[0x80])
        for row in s.rows[0x81:]:
            assert_equal(SwirlFrameRow(x1=0, x2=0xff, x3=0xff, x4=0), row)

    def test_block_rep_repeating_mode_01(self):
        s = SwirlFrame()
        for row in s.rows:
            row.set(1, 2, 0xff, 0)

        assert_list_equal([1,
                           0x7f, 1, 2,
                           97, 1, 2,
                           0],
                          s.block_rep().to_list())

    def test_to_block_repeating_not_mode_01(self):
        s = SwirlFrame()
        for row in s.rows:
            row.set(1, 2, 3, 4)

        assert_list_equal([4,
                           0x7f, 1, 2, 3, 4,
                           97, 1, 2, 3, 4,
                           0],
                          s.block_rep().to_list())

    def test_to_block_continuous_mode_01(self):
        s = SwirlFrame()
        for row in s.rows:
            row.set(1, 2, 0xff, 0)
        s.rows[55].set(5, 6, 0xff, 0)

        assert_list_equal([1,
                           55, 1, 2,
                           0x81, 5, 6,
                           0x7f, 1, 2,
                           41, 1, 2,
                           0],
                          s.block_rep().to_list())

    def test_to_block_continuous_not_mode_01(self):
        s = SwirlFrame()
        for row in s.rows:
            row.set(1, 2, 0xff, 0)
        s.rows[55].set(5, 6, 7, 8)

        assert_list_equal([4,
                           55, 1, 2, 0xff, 0,
                           0x81, 5, 6, 7, 8,
                           0x7f, 1, 2, 0xff, 0,
                           41, 1, 2, 0xff, 0,
                           0],
                          s.block_rep().to_list())

    def test_to_block_continuous_long(self):
        s = SwirlFrame()
        for i, row in enumerate(s.rows):
            row.set(i, i+1, 0xff, 0)

        assert_list_equal([1,

                           0xff, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13,
                           13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 23, 24, 24,
                           25, 25, 26, 26, 27, 27, 28, 28, 29, 29, 30, 30, 31, 31, 32, 32, 33, 33, 34, 34, 35, 35, 36,
                           36, 37, 37, 38, 38, 39, 39, 40, 40, 41, 41, 42, 42, 43, 43, 44, 44, 45, 45, 46, 46, 47, 47,
                           48, 48, 49, 49, 50, 50, 51, 51, 52, 52, 53, 53, 54, 54, 55, 55, 56, 56, 57, 57, 58, 58, 59,
                           59, 60, 60, 61, 61, 62, 62, 63, 63, 64, 64, 65, 65, 66, 66, 67, 67, 68, 68, 69, 69, 70, 70,
                           71, 71, 72, 72, 73, 73, 74, 74, 75, 75, 76, 76, 77, 77, 78, 78, 79, 79, 80, 80, 81, 81, 82,
                           82, 83, 83, 84, 84, 85, 85, 86, 86, 87, 87, 88, 88, 89, 89, 90, 90, 91, 91, 92, 92, 93, 93,
                           94, 94, 95, 95, 96, 96, 97, 97, 98, 98, 99, 99, 100, 100, 101, 101, 102, 102, 103, 103, 104,
                           104, 105, 105, 106, 106, 107, 107, 108, 108, 109, 109, 110, 110, 111, 111, 112, 112, 113,
                           113, 114, 114, 115, 115, 116, 116, 117, 117, 118, 118, 119, 119, 120, 120, 121, 121, 122,
                           122, 123, 123, 124, 124, 125, 125, 126, 126, 127,

                           0xe1, 127, 128, 128, 129, 129, 130, 130, 131, 131, 132, 132, 133, 133, 134, 134, 135, 135,
                           136, 136, 137,
                           137, 138, 138, 139, 139, 140, 140, 141, 141, 142, 142, 143, 143, 144, 144, 145, 145, 146,
                           146, 147, 147, 148, 148, 149, 149, 150, 150, 151, 151, 152, 152, 153, 153, 154, 154, 155,
                           155, 156, 156, 157, 157, 158, 158, 159, 159, 160, 160, 161, 161, 162, 162, 163, 163, 164,
                           164, 165, 165, 166, 166, 167, 167, 168, 168, 169, 169, 170, 170, 171, 171, 172, 172, 173,
                           173, 174, 174, 175, 175, 176, 176, 177, 177, 178, 178, 179, 179, 180, 180, 181, 181, 182,
                           182, 183, 183, 184, 184, 185, 185, 186, 186, 187, 187, 188, 188, 189, 189, 190, 190, 191,
                           191, 192, 192, 193, 193, 194, 194, 195, 195, 196, 196, 197, 197, 198, 198, 199, 199, 200,
                           200, 201, 201, 202, 202, 203, 203, 204, 204, 205, 205, 206, 206, 207, 207, 208, 208, 209,
                           209, 210, 210, 211, 211, 212, 212, 213, 213, 214, 214, 215, 215, 216, 216, 217, 217, 218,
                           218, 219, 219, 220, 220, 221, 221, 222, 222, 223, 223, 224,

                           0],
                          s.block_rep().to_list())