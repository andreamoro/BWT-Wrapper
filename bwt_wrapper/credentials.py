"""
Credential loading for the Bing Webmaster Tools Wrapper.

Supports reading the API key from a local TOML file so that secrets
never need to be hard-coded in source files.

Expected file format (credentials.toml)::

    api_key = "your_api_key_here"
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

_DEFAULT_FILENAME = 'credentials.toml'


def load_api_key(credentials_file: str | os.PathLike | None = None) -> str:
    """
    Read the API key from a TOML credentials file.

    Parameters
    ----------
    credentials_file : path, optional
        Path to the TOML file.  Defaults to ``credentials.toml`` in the
        current working directory.

    Returns
    -------
    str
        The API key value.

    Raises
    ------
    FileNotFoundError
        If the credentials file does not exist.
    KeyError
        If the file does not contain an ``api_key`` field.
    """
    path = Path(credentials_file) if credentials_file else Path(_DEFAULT_FILENAME)

    if not path.is_file():
        raise FileNotFoundError(
            f'Credentials file not found: {path.resolve()}\n'
            f'Create one with the following content:\n\n'
            f'    api_key = "your_api_key_here"\n'
        )

    with open(path, 'rb') as fh:
        data = tomllib.load(fh)

    try:
        api_key = data['api_key']
    except KeyError:
        raise KeyError(
            f'The credentials file ({path}) does not contain an "api_key" field.'
        ) from None

    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError(
            f'The "api_key" field in {path} must be a non-empty string.'
        )

    return api_key.strip()
