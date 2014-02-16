from coilsnake.exceptions import InvalidUserDataError, InvalidArgumentError


class InvalidEbTextPointerError(InvalidUserDataError):
    pass

class InvalidEbCompressedDataError(InvalidArgumentError):
    pass