from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin


class CoilSnakeError(Exception):
    def __str__(self):
        return "{}: {}".format(self.__class__.__name__, self.message)


class CoilSnakeInternalError(CoilSnakeError):
    pass


class CoilSnakeUserError(CoilSnakeError):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "User input error: {}".format(self.message)


class CoilSnakeTraceableError(CoilSnakeError):
    def __init__(self, message, cause):
        self.message = message
        self.cause = cause

    def __str__(self):
        return "{}\nCaused by: {}".format(self.message, self.cause)


class OutOfBoundsError(CoilSnakeInternalError):
    pass


class CoilSnakeUnexpectedError(CoilSnakeError):
    def __init__(self, traceback):
        self.traceback = traceback

    def __str__(self):
        return "{}: Unexpected error:\n{}".format(self.__class__.__name__, self.traceback)


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


class CCScriptCompilationError(CoilSnakeError):
    pass


class ResourceNotFoundError(CoilSnakeError):
    pass


# For when the data is of the expected type or form, but the content of the data itself is invalid or unexpected.
# This should generally be caused by some error or inconsistency in the user's input.
class InvalidUserDataError(CoilSnakeUserError):
    pass


class MissingUserDataError(InvalidUserDataError):
    pass


class InvalidYmlFileError(CoilSnakeError):
    pass


class InvalidYmlRepresentationError(CoilSnakeError):
    pass


class TableEntryError(CoilSnakeError):
    pass


class TableEntryInvalidYmlRepresentationError(TableEntryError):
    pass


class TableEntryMissingDataError(TableEntryError):
    pass


class TableSchemaError(EqualityMixin, StringRepresentationMixin, CoilSnakeError):
    def __init__(self, field, cause):
        self.field = field
        self.cause = cause

    def __str__(self):
        return "{}: Error while parsing \"{}\":\n{}".format(self.__class__.__name__, self.field, unicode(self.cause))


class TableError(EqualityMixin, StringRepresentationMixin, CoilSnakeError):
    def __init__(self, table_name=None, entry=None, field=None, cause=None):
        self.table_name = table_name
        self.entry = entry
        self.field = field
        self.cause = cause

    def __str__(self):
        str_rep = "{}: Error while parsing".format(self.__class__.__name__)
        if self.field is not None:
            str_rep += " in \"{}\"".format(self.field)
        if self.entry is not None:
            str_rep += " in entry #{}".format(self.entry)
        if self.table_name is not None:
            str_rep += " in table \"{}\"".format(self.table_name)
        str_rep += ":\n" + unicode(self.cause)

        return str_rep