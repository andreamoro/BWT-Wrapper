"""
Tests for credential loading (bwt_wrapper.credentials.load_api_key).

These exercise the TOML parsing and the various failure modes a user is
likely to hit when setting up credentials.toml.
"""

import pytest

from bwt_wrapper.credentials import load_api_key


def test_loads_key_from_explicit_path(tmp_path):
    cred = tmp_path / "credentials.toml"
    cred.write_text('api_key = "secret-key-123"\n')
    assert load_api_key(cred) == "secret-key-123"


def test_strips_surrounding_whitespace(tmp_path):
    cred = tmp_path / "credentials.toml"
    cred.write_text('api_key = "  spaced-key  "\n')
    assert load_api_key(cred) == "spaced-key"


def test_default_filename_in_cwd(tmp_path, monkeypatch):
    # With no argument the loader looks for credentials.toml in the cwd.
    (tmp_path / "credentials.toml").write_text('api_key = "cwd-key"\n')
    monkeypatch.chdir(tmp_path)
    assert load_api_key() == "cwd-key"


def test_missing_file_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_api_key(tmp_path / "does-not-exist.toml")


def test_missing_api_key_field_raises_keyerror(tmp_path):
    cred = tmp_path / "credentials.toml"
    cred.write_text('something_else = "value"\n')
    with pytest.raises(KeyError):
        load_api_key(cred)


def test_empty_api_key_raises_valueerror(tmp_path):
    cred = tmp_path / "credentials.toml"
    cred.write_text('api_key = "   "\n')
    with pytest.raises(ValueError):
        load_api_key(cred)


def test_non_string_api_key_raises_valueerror(tmp_path):
    cred = tmp_path / "credentials.toml"
    cred.write_text("api_key = 12345\n")
    with pytest.raises(ValueError):
        load_api_key(cred)
