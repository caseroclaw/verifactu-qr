"""URL del código QR tributario de VeriFactu y validaciones asociadas.

Especificación aplicada:
- Real Decreto 1007/2023 (BOE-A-2023-24840).
- Orden HAC/1177/2024, artículos 20 y 21.
- AEAT, «Detalles técnicos para la implementación del código QR y de la URL del
  servicio de cotejo o remisión de información» (URL encoding UTF-8 con las
  mismas reglas que `java.net.URLEncoder`).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .nif import es_valido

BASES = {
    ("produccion", True): "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR",
    ("pruebas", True): "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR",
    ("produccion", False): "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu",
    ("pruebas", False): "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu",
}

MAX_NUMSERIE = 60
MAX_ENTERA_IMPORTE = 12
_SAFE = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-*_")


class QRError(ValueError):
    """Error de validación con el código de error que devuelve la AEAT."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__("[%d] %s" % (code, message))
        self.code = code
        self.message = message


def urlencode(valor: str) -> str:
    """Codifica igual que `java.net.URLEncoder.encode(valor, "UTF-8")`.

    Deja intactos letras, dígitos y `. - * _`; convierte el espacio en `+` y el
    resto en `%XX` (UTF-8, hexadecimal en mayúsculas).
    """
    trozos = []
    for byte in str(valor).encode("utf-8"):
        caracter = chr(byte)
        if caracter in _SAFE:
            trozos.append(caracter)
        elif caracter == " ":
            trozos.append("+")
        else:
            trozos.append("%%%02X" % byte)
    return "".join(trozos)


def validar_nif(nif: str) -> str:
    nif = str(nif).strip()
    if not es_valido(nif):
        raise QRError(2001, "El NIF tiene un formato erróneo o no es válido: %r" % nif)
    return nif


def formatear_numserie(numserie: str) -> str:
    numserie = str(numserie)
    if len(numserie) > MAX_NUMSERIE:
        raise QRError(2002, "El número de serie excede los %d caracteres" % MAX_NUMSERIE)
    for caracter in numserie:
        if not 32 <= ord(caracter) <= 126:
            raise QRError(
                2003,
                "El número de serie contiene caracteres no permitidos (solo ASCII 32-126): %r" % numserie,
            )
    if not numserie.strip():
        raise QRError(2002, "El número de serie no puede estar vacío")
    return numserie


def formatear_fecha(fecha: date | datetime | str) -> str:
    if isinstance(fecha, (date, datetime)):
        return fecha.strftime("%d-%m-%Y")
    texto = str(fecha).strip()
    try:
        datetime.strptime(texto, "%d-%m-%Y")
    except ValueError:
        raise QRError(2004, "La fecha debe tener el formato DD-MM-AAAA: %r" % texto) from None
    return texto


def formatear_importe(importe) -> str:
    if isinstance(importe, bool):
        raise QRError(2005, "El importe tiene un formato incorrecto: %r" % importe)
    if isinstance(importe, str):
        texto = importe.strip().replace(",", ".")
    elif isinstance(importe, (int, float, Decimal)):
        texto = str(importe)
    else:
        raise QRError(2005, "El importe tiene un formato incorrecto: %r" % importe)
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise QRError(2005, "El importe tiene un formato incorrecto: %r" % importe) from None
    if not valor.is_finite() or "E" in texto.upper():
        raise QRError(2005, "El importe tiene un formato incorrecto: %r" % importe)
    entera = texto.split(".")[0].lstrip("-")
    if len(entera) > MAX_ENTERA_IMPORTE:
        raise QRError(2006, "El importe excede los %d dígitos de parte entera" % MAX_ENTERA_IMPORTE)
    if valor.quantize(Decimal("0.01")) != valor:
        raise QRError(2005, "El importe no admite más de 2 decimales: %r" % importe)
    return format(valor.normalize(), "f")


def build_qr_url(
    nif: str,
    numserie: str,
    fecha: date | datetime | str,
    importe,
    *,
    verifactu: bool = True,
    entorno: str = "produccion",
) -> str:
    """Devuelve la URL que debe contener el QR tributario de la factura.

    ``verifactu=True`` -> sistema VERI*FACTU (envía registros a la AEAT).
    ``entorno``: 'produccion' o 'pruebas'.
    """
    if entorno not in ("produccion", "pruebas"):
        raise ValueError("entorno debe ser 'produccion' o 'pruebas'")
    base = BASES[(entorno, bool(verifactu))]
    partes = (
        ("nif", validar_nif(nif)),
        ("numserie", formatear_numserie(numserie)),
        ("fecha", formatear_fecha(fecha)),
        ("importe", formatear_importe(importe)),
    )
    return base + "?" + "&".join("%s=%s" % (clave, urlencode(valor)) for clave, valor in partes)


def url_consulta_json(url_qr: str) -> str:
    """Añade `formato=json` para consultar el servicio y parsear la respuesta.

    Este parámetro **nunca** puede ir dentro del QR de la factura.
    """
    separador = "&" if "?" in url_qr else "?"
    if "formato=" in url_qr:
        return url_qr
    return url_qr + separador + "formato=json"
