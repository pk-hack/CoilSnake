class OutOfBoundsError(Exception):
    pass

class InvalidArgumentError(Exception):
    pass

class NotImplementedError(Exception):
    pass

class CouldNotAllocateError(Exception):
    pass

class NotEnoughUnallocatedSpaceError(CouldNotAllocateError):
    pass

class FileAccessError(Exception):
    pass

class ValueNotUnsignedByteError(Exception):
    pass