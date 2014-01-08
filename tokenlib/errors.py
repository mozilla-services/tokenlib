# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""

Error classes for tokenlib.

"""


class Error(ValueError):
    """Base error class for all tokenlib exceptions."""
    pass


class MalformedTokenError(Error):
    """Error raised when tokenlib encounters a badly-formed token."""

    def __init__(self, message="token is malformed", *args):
        super(MalformedTokenError, self).__init__(message, *args)


class ExpiredTokenError(Error):
    """Error raised when tokenlib encounters an expired token."""

    def __init__(self, message="token has expired", *args):
        super(ExpiredTokenError, self).__init__(message, *args)


class InvalidSignatureError(Error):
    """Error raised when tokenlib encounters an invalid signature."""

    def __init__(self, message="token has invalid signature", *args):
        super(InvalidSignatureError, self).__init__(message, *args)
