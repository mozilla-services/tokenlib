# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.


try:
    import os
    if os.environ.get("DEBUG", None):
        from nose.tools import set_trace
        __builtins__["DEBUG"] = set_trace
except ImportError:
    pass
