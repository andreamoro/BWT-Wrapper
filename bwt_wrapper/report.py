"""
Report class for Bing Webmaster Tools Wrapper.

Mirrors the Report abstraction in the GSC Wrapper: wraps a list of result
rows and provides clean exports to pandas DataFrames, pickle files, and
in-memory byte streams.
"""

import pickle
import io
from typing import Any


class Report:
    """
    Wraps a list of normalised result rows from the Bing API and provides
    convenient export methods.

    Attributes
    ----------
    rows : list[dict]
        The raw result data, one dict per row.
    """

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)

    def __repr__(self) -> str:
        return f'<Report rows={len(self._rows)}>'

    @property
    def rows(self) -> list[dict]:
        """Return the underlying list of result rows."""
        return self._rows

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------

    def to_dataframe(self):
        """
        Convert the report to a pandas DataFrame.

        pandas is an optional dependency and is not listed in the package
        requirements.  An ImportError is raised with a clear message when
        it is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                'pandas is required to use to_dataframe(). '
                'Install it with: pip install pandas'
            ) from None
        return pd.DataFrame(self._rows)

    def to_disk(self, filename: str | None = None) -> str:
        """
        Persist the report to a pickle file.

        Parameters
        ----------
        filename : optional file path; when omitted a default name is
                   generated from the current date and time.

        Returns the path where the file was saved.
        """
        import datetime

        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bwt_report_{timestamp}.pck'

        with open(filename, 'wb') as fh:
            pickle.dump(self._rows, fh)

        return filename

    def to_datastream(self) -> bytes:
        """
        Serialise the report to an in-memory byte stream (pickle).
        Useful when you want to persist the data without writing to disk.
        """
        buffer = io.BytesIO()
        pickle.dump(self._rows, buffer)
        return buffer.getvalue()

    @classmethod
    def from_disk(cls, filename: str) -> 'Report':
        """
        Load a previously saved report from a pickle file.

        Parameters
        ----------
        filename : path to the .pck file written by to_disk()
        """
        with open(filename, 'rb') as fh:
            rows = pickle.load(fh)
        return cls(rows)

    @classmethod
    def from_datastream(cls, data: bytes) -> 'Report':
        """
        Reconstruct a Report from a byte stream created by to_datastream().
        """
        buffer = io.BytesIO(data)
        rows = pickle.load(buffer)
        return cls(rows)
