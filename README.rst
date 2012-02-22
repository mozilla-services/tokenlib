========
tokenlib
========

This is generic support library for doing token-based authentication.  You
might use it to build a login system using bearer tokens, two-legged oauth, or
MAC Access authentication.

Given a server-side master secret, you can serialize a dict of data into
an opaque, unforgeable authentication token::

   >>> token = tokenlib.make_token({"userid": 42}, secret="I_LIKE_UNICORNS")
   >>> print token
   eyJzYWx0IjogImY0NTU5NCIsICJleHBpcmVzIjogMTMyOTg3NTI2Ny4xNDQ5MzUsICJ1c2VyaWQiOiA0Mn0miXCe4NQQtXTE8NXSGcsL6dzSuQ==

Later, you can use the same secret to verify the token and extract the
embedded data::

    >>> data = tokenlib.parse_token(token, secret="I_LIKE_UNICORNS")
    >>> print data
    {u'userid': 42, u'expires': 1329875384.073159, u'salt': u'1c033f'}

Notice that the data includes an expiry time.  If you try to parse an expired
token, it will fail::

    >>> # Use now=XXX to simulate a time in the future.
    >>> tokenlib.parse_token(token, secret="I_LIKE_UNICORNS", now=9999999999)
    Traceback (most recent call last):
    ...
    ValueError: token has expired

Likewise, it will fail if the token was constructed with a non-matching secret
key::

    >>> tokenlib.parse_token(token, secret="I_HATE_UNICORNS")
    Traceback (most recent call last):
    ...
    ValueError: token has invalid signature

Each token also has an associated "token secret".  This is a secret key that
can be shared with the consumer of the token to enable authentication schemes
such as MAC Access Authentication of Two-Legged OAuth::

    >>> key = tokenlib.get_token_secret(token, secret="I_LIKE_UNICORNS")
    >>> print key
    EZslG8yEYTGyDvBjRnxGipL5Kd8=

For applications that are using the same settings over and over again, you
will probably want to create a TokenManager object rather than using the
module-level convenience functions::

    >>> manager = tokenlib.TokenManager(secret="I_LIKE_UNICORNS")
    >>> data = manager.parse_token(token)
    >>> print data
    {u'userid': 42, u'expires': 1329875384.073159, u'salt': u'1c033f'}

This will let you customize e.g. the token expiry timeout or hash module
without repeating the settings in each call.
