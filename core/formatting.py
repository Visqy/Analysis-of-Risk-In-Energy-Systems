"""Format angka gaya Indonesia (koma sebagai desimal)."""


def id_number(value, decimals=2):
    """221.64 -> '221,64'. Aman untuk int/float, termasuk negatif."""
    sign = "-" if value < 0 else ""
    whole, _, frac = f"{abs(value):,.{decimals}f}".partition(".")
    whole = whole.replace(",", ".")
    return f"{sign}{whole},{frac}" if frac else f"{sign}{whole}"
