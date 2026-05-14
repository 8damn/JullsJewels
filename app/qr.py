"""
SPAYD QR kód pro přímý bankovní převod (český standard).
Vrátí PNG jako bytes — použij v Jinja2 šabloně jako base64 data URI.
"""
import base64
import io

import qrcode


IBAN = "CZ0000000000000000000000"  # Nahraď reálným IBAN v .env (přidat do config)
BIC = "AIRACZPP"                   # Nahraď reálným BIC


def build_spayd(amount: float, var_symbol: str, message: str = "Jullsjewels") -> str:
    amount_str = f"{amount:.2f}"
    return (
        f"SPD*1.0*"
        f"ACC:{IBAN}+{BIC}*"
        f"AM:{amount_str}*"
        f"CC:CZK*"
        f"X-VS:{var_symbol}*"
        f"MSG:{message}"
    )


def generate_qr_png(amount: float, var_symbol: str) -> bytes:
    spayd = build_spayd(amount, var_symbol)
    img = qrcode.make(spayd)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_base64(amount: float, var_symbol: str) -> str:
    """Vrátí base64 PNG použitelný přímo jako <img src='data:image/png;base64,...'>"""
    return base64.b64encode(generate_qr_png(amount, var_symbol)).decode()
