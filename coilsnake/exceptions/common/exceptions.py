from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin


class CoilSnakeError(Exception, EqualityMixin, StringRepresentationMixin):
    pass


class CoilSnakeInternalError(CoilSnakeError):
    pass


class CoilSnakeUserError(CoilSnakeError):
    pass


class OutOfBoundsError(CoilSnakeInternalError):
    pass


# For when an argument is incorrectly to a function, or if an argument is missing in a function call.
# This should generally be caused by some bug in the code.
class InvalidArgumentError(CoilSnakeInternalError):
    pass


class IndexOutOfRangeError(CoilSnakeInternalError):
    pass


class CouldNotAllocateError(CoilSnakeInternalError):
    pass


class NotEnoughUnallocatedSpaceError(CouldNotAllocateError):
    pass


class FileAccessError(CoilSnakeInternalError):
    pass


# For when the data is of the expected type or form, but the content of the data itself is invalid or unexpected.
# This should generally be caused by some error or inconsistency in the user's input.
class InvalidUserDataError(CoilSnakeUserError):
    pass


class MissingUserDataError(InvalidUserDataError):
    pass


class InvalidYmlRepresentationError(CoilSnakeError):
    pass


class TableEntryError(CoilSnakeError):
    pass


class TableEntryInvalidYmlRepresentationError(TableEntryError):
    pass


class TableEntryMissingDataError(TableEntryError):
    pass


class TableError(CoilSnakeError):
    def __init__(self, entry, field, cause):
        self.entry = entry
        self.field = field
        self.cause = cause