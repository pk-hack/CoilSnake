from PIL import Image

from coilsnake.exceptions.common.exceptions import CoilSnakeError, InvalidArgumentError


def open_image(f):
    try:
        image = Image.open(f)
        return image
    except IOError:
        raise InvalidArgumentError("Could not open file: {}".format(f.name))


def open_indexed_image(f):
    image = open_image(f)
    if image.mode != 'P':
        raise CoilSnakeError("Image does not use an indexed palette: {}".format(f.name))
    return image