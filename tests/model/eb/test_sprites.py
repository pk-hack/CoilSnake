from nose.tools import assert_equal, assert_not_equal, assert_not_in, assert_false

from coilsnake.model.eb.sprites import SpriteGroup
from tests.coilsnake_test import SpriteGroupTestCase


class TestEbSpriteGroup(SpriteGroupTestCase):
    def test_from_image(self):
        sg = SpriteGroup(16)
        sg.from_image(self.spritegroup_1_img)

    def test_calculate_unique_sprites_1(self):
        sg = SpriteGroup(16)
        sg.from_image(self.spritegroup_1_img)

        unique_sprites, unique_sprite_usages = sg.calculate_unique_sprites()

        # Two unused sprites which are identical
        sprite_4_hash, sprite_4_flip = unique_sprite_usages[4]
        assert_false(sprite_4_flip)
        assert_equal(unique_sprite_usages[5], (sprite_4_hash, sprite_4_flip))

        # Two used sprites which are identical
        assert_equal(unique_sprite_usages[0], (sprite_4_hash, sprite_4_flip))
        assert_equal(unique_sprite_usages[1], (sprite_4_hash, sprite_4_flip))

        # Two used-as-flipped sprites which are identical
        assert_equal(unique_sprite_usages[6], (sprite_4_hash, not sprite_4_flip))
        assert_equal(unique_sprite_usages[7], (sprite_4_hash, not sprite_4_flip))

        # Two mirrored sprites, the first of which is used
        assert_equal(unique_sprite_usages[2], (sprite_4_hash, sprite_4_flip))
        assert_equal(unique_sprite_usages[3], (sprite_4_hash, not sprite_4_flip))

        # Two mirrored sprites, the second of which is used
        assert_equal(unique_sprite_usages[14], (sprite_4_hash, not sprite_4_flip))
        assert_equal(unique_sprite_usages[15], (sprite_4_hash, sprite_4_flip))

        # Two mirrored sprites, neither of which are used
        sprite_12_hash, sprite_12_flip = unique_sprite_usages[12]
        assert_not_equal(sprite_4_hash, sprite_12_hash)
        assert_equal(unique_sprite_usages[13], (sprite_12_hash, not sprite_12_flip))

        # Two sprites, both of which are used
        assert_equal(unique_sprite_usages[10], (sprite_4_hash, sprite_4_flip))
        assert_equal(unique_sprite_usages[11], (sprite_12_hash, sprite_12_flip))
        assert_equal(unique_sprite_usages[10][1], unique_sprite_usages[11][1])

        # Two flipped sprites, both of which are used
        assert_equal(unique_sprite_usages[8], (sprite_4_hash, not sprite_4_flip))
        assert_equal(unique_sprite_usages[9], (sprite_12_hash, not sprite_12_flip))
        assert_equal(unique_sprite_usages[8][1], unique_sprite_usages[9][1])

    def test_calculate_unique_sprites_2(self):
        sg = SpriteGroup(16)
        sg.from_image(self.spritegroup_2_img)

        unique_sprites, unique_sprite_usages = sg.calculate_unique_sprites()

        hashes = dict()

        # Two unused sprites which are identical
        sprite_4_hash, sprite_4_flip = unique_sprite_usages[4]
        assert_equal(unique_sprite_usages[5], (sprite_4_hash, sprite_4_flip))
        hashes[sprite_4_hash] = True

        # One used sprite and one unused sprite
        assert_equal(unique_sprite_usages[0], (sprite_4_hash, sprite_4_flip))
        sprite_1_hash, sprite_1_flip = unique_sprite_usages[1]
        assert_not_equal(sprite_4_hash, sprite_1_hash)
        hashes[sprite_1_hash] = True

        # One used-as-flipped sprite and one unused sprite
        assert_equal(unique_sprite_usages[6], (sprite_4_hash, not sprite_4_flip))
        sprite_7_hash, sprite_7_flip = unique_sprite_usages[7]
        assert_not_in(sprite_7_hash, hashes)
        assert_equal(not sprite_4_flip, sprite_7_flip)
        hashes[sprite_7_hash] = True

        # One unused sprite and one used sprite
        sprite_2_hash, sprite_2_flip = unique_sprite_usages[2]
        assert_not_in(sprite_2_hash, hashes)
        assert_equal(unique_sprite_usages[3], unique_sprite_usages[4])
        hashes[sprite_2_hash] = True

        # One unused sprite and one used-as-flipped sprite
        sprite_14_hash, sprite_14_flip = unique_sprite_usages[14]
        assert_not_in(sprite_14_hash, hashes)
        assert_equal(unique_sprite_usages[15], (sprite_4_hash, not sprite_4_flip))
        hashes[sprite_14_hash] = True

        # Two unused sprites
        sprite_12_hash, sprite_12_flip = unique_sprite_usages[12]
        assert_not_in(sprite_12_hash, hashes)
        sprite_13_hash, sprite_13_flip = unique_sprite_usages[13]
        assert_not_equal(sprite_12_hash, sprite_13_hash)
        assert_not_in(sprite_13_hash, hashes)
        assert_equal(sprite_12_flip, sprite_13_flip)
        hashes[sprite_12_hash] = True
        hashes[sprite_13_hash] = True

        # One unused sprite
        sprite_10_hash, sprite_10_flip = unique_sprite_usages[10]
        assert_not_in(sprite_10_hash, hashes)