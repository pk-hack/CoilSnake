from nose.tools import assert_equal, assert_not_equal, assert_not_in

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
        sprite_0_hash, sprite_0_flip = unique_sprite_usages[0]
        assert_equal(unique_sprite_usages[1], (sprite_0_hash, sprite_0_flip))

        # Two used sprites which are identical
        assert_equal(unique_sprite_usages[2], (sprite_0_hash, sprite_0_flip))
        assert_equal(unique_sprite_usages[3], (sprite_0_hash, sprite_0_flip))

        # Two used-as-flipped sprites which are identical
        assert_equal(unique_sprite_usages[4], (sprite_0_hash, not sprite_0_flip))
        assert_equal(unique_sprite_usages[5], (sprite_0_hash, not sprite_0_flip))

        # Two mirrored sprites, the first of which is used
        assert_equal(unique_sprite_usages[6], (sprite_0_hash, sprite_0_flip))
        assert_equal(unique_sprite_usages[7], (sprite_0_hash, not sprite_0_flip))

        # Two mirrored sprites, the second of which is used
        assert_equal(unique_sprite_usages[8], (sprite_0_hash, not sprite_0_flip))
        assert_equal(unique_sprite_usages[9], (sprite_0_hash, sprite_0_flip))

        # Two mirrored sprites, neither of which are used
        sprite_10_hash, sprite_10_flip = unique_sprite_usages[10]
        assert_not_equal(sprite_0_hash, sprite_10_hash)
        assert_equal(unique_sprite_usages[11], (sprite_10_hash, not sprite_10_flip))

        # Two sprites, both of which are used
        assert_equal(unique_sprite_usages[12], (sprite_0_hash, sprite_0_flip))
        assert_equal(unique_sprite_usages[13], (sprite_10_hash, sprite_10_flip))
        assert_equal(unique_sprite_usages[12][1], unique_sprite_usages[13][1])

        # Two flipped sprites, both of which are used
        assert_equal(unique_sprite_usages[14], (sprite_0_hash, not sprite_0_flip))
        assert_equal(unique_sprite_usages[15], (sprite_10_hash, not sprite_10_flip))
        assert_equal(unique_sprite_usages[14][1], unique_sprite_usages[15][1])

    def test_calculate_unique_sprites_2(self):
        sg = SpriteGroup(16)
        sg.from_image(self.spritegroup_2_img)

        unique_sprites, unique_sprite_usages = sg.calculate_unique_sprites()

        hashes = dict()

        # Two unused sprites which are identical
        sprite_0_hash, sprite_0_flip = unique_sprite_usages[0]
        assert_equal(unique_sprite_usages[1], (sprite_0_hash, sprite_0_flip))
        hashes[sprite_0_hash] = True

        # One used sprite and one unused sprite
        assert_equal(unique_sprite_usages[2], (sprite_0_hash, sprite_0_flip))
        sprite_3_hash, sprite_3_flip = unique_sprite_usages[3]
        assert_not_equal(sprite_0_hash, sprite_3_hash)
        hashes[sprite_3_hash] = True

        # One used-as-flipped sprite and one unused sprite
        assert_equal(unique_sprite_usages[4], (sprite_0_hash, not sprite_0_flip))
        sprite_5_hash, sprite_5_flip = unique_sprite_usages[5]
        assert_not_in(sprite_5_hash, hashes)
        assert_equal(not sprite_0_flip, sprite_5_flip)
        hashes[sprite_5_hash] = True

        # One unused sprite and one used sprite
        sprite_6_hash, sprite_6_flip = unique_sprite_usages[6]
        assert_not_in(sprite_6_hash, hashes)
        assert_equal(unique_sprite_usages[7], unique_sprite_usages[0])
        hashes[sprite_6_hash] = True

        # One unused sprite and one used-as-flipped sprite
        sprite_8_hash, sprite_8_flip = unique_sprite_usages[8]
        assert_not_in(sprite_8_hash, hashes)
        assert_equal(unique_sprite_usages[9], (sprite_0_hash, not sprite_0_flip))
        hashes[sprite_8_hash] = True

        # Two unused sprites
        sprite_10_hash, sprite_10_flip = unique_sprite_usages[10]
        assert_not_in(sprite_10_hash, hashes)
        sprite_11_hash, sprite_11_flip = unique_sprite_usages[11]
        assert_not_equal(sprite_10_hash, sprite_11_hash)
        assert_not_in(sprite_11_hash, hashes)
        assert_equal(sprite_10_flip, sprite_11_flip)
        hashes[sprite_10_hash] = True
        hashes[sprite_11_hash] = True

        # One unused sprite
        sprite_12_hash, sprite_12_flip = unique_sprite_usages[12]
        assert_not_in(sprite_12_hash, hashes)