"""
Tests for Report (bwt_wrapper.report).

Covers the container protocol and the three export/round-trip paths:
pandas DataFrame, pickle file, and in-memory byte stream.
"""

import pytest

from bwt_wrapper.report import Report


@pytest.fixture
def sample_rows():
    return [
        {"Query": "a", "Clicks": 1},
        {"Query": "b", "Clicks": 2},
    ]


def test_len_iter_rows_and_repr(sample_rows):
    report = Report(sample_rows)
    assert len(report) == 2
    assert list(report) == sample_rows
    assert report.rows is sample_rows
    assert "rows=2" in repr(report)


def test_to_disk_default_filename_roundtrip(tmp_path, monkeypatch, sample_rows):
    monkeypatch.chdir(tmp_path)
    report = Report(sample_rows)
    filename = report.to_disk()
    assert filename.startswith("bwt_report_") and filename.endswith(".pck")
    restored = Report.from_disk(filename)
    assert restored.rows == sample_rows


def test_to_disk_explicit_filename(tmp_path, sample_rows):
    target = tmp_path / "my_report.pck"
    returned = Report(sample_rows).to_disk(str(target))
    assert returned == str(target)
    assert target.exists()
    assert Report.from_disk(str(target)).rows == sample_rows


def test_datastream_roundtrip(sample_rows):
    data = Report(sample_rows).to_datastream()
    assert isinstance(data, bytes)
    assert Report.from_datastream(data).rows == sample_rows


def test_to_dataframe():
    pd = pytest.importorskip("pandas")
    df = Report([{"Query": "a", "Clicks": 1}]).to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 2)
    assert list(df.columns) == ["Query", "Clicks"]
