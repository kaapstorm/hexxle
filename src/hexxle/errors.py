"""The tool's own error type."""


class HexxleError(Exception):
    """A problem with the user's input or setup.

    The command line reports it as ``error: <message>`` without a
    traceback; any other exception is a bug and keeps its traceback.
    """
