import pytest

from core.formatting import id_number


@pytest.mark.parametrize("value,dec,expected", [
    (221.64, 2, "221,64"),
    (0.5, 2, "0,50"),
    (1234567.891, 2, "1.234.567,89"),
    (1000, 0, "1.000"),
    (-12.3, 1, "-12,3"),
    (0, 2, "0,00"),
])
def test_id_number(value, dec, expected):
    assert id_number(value, dec) == expected
