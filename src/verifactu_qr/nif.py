"""Validación de identificaciones fiscales españolas (NIF, DNI, NIE, CIF).

Algoritmos públicos: letra del DNI/NIE (módulo 23) y dígito/letra de control del
CIF (suma de posiciones pares + doble de impares).
"""
from __future__ import annotations

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
LETRAS_CIF = "JABCDEFGHI"  # índice 0 -> J ... índice 9 -> I

# CIF/números de entidad con control alfabético obligatorio y numérico obligatorio.
CIF_LETRA_OBLIGATORIA = set("PQSNWK")
CIF_DIGITO_OBLIGATORIO = set("ABEH")
CIF_PREFIJOS = set("ABCDEFGHJKLMNPQRSUVW")


def normalizar(valor: str) -> str:
    """Quita espacios, puntos y guiones y pasa a mayúsculas."""
    return (
        str(valor)
        .strip()
        .upper()
        .replace(" ", "")
        .replace(".", "")
        .replace("-", "")
    )


def _letra_dni(numero: int) -> str:
    return LETRAS_DNI[numero % 23]


def _cif_valido(valor: str) -> bool:
    prefijo, digitos, control = valor[0], valor[1:8], valor[8]
    if prefijo not in CIF_PREFIJOS:
        return False
    pares = sum(int(digitos[i]) for i in (1, 3, 5))
    impares = 0
    for i in (0, 2, 4, 6):
        doble = int(digitos[i]) * 2
        impares += doble // 10 + doble % 10
    digito_control = (10 - ((pares + impares) % 10)) % 10
    if prefijo in CIF_LETRA_OBLIGATORIA:
        return control == LETRAS_CIF[digito_control]
    if prefijo in CIF_DIGITO_OBLIGATORIO:
        return control == str(digito_control)
    return control in (str(digito_control), LETRAS_CIF[digito_control])


def tipo(valor: str) -> str | None:
    """Devuelve 'DNI', 'NIE', 'CIF' o None si no es válido."""
    v = normalizar(valor)
    if len(v) == 9 and v[:8].isdigit() and v[8].isalpha():
        return "DNI" if v[8] == _letra_dni(int(v[:8])) else None
    if len(v) == 9 and v[0] in "XYZ" and v[1:8].isdigit() and v[8].isalpha():
        numero = int({"X": "0", "Y": "1", "Z": "2"}[v[0]] + v[1:8])
        return "NIE" if v[8] == _letra_dni(numero) else None
    if len(v) == 9 and v[0].isalpha() and v[1:8].isdigit() and v[8].isalnum():
        return "CIF" if _cif_valido(v) else None
    return None


def es_valido(valor: str) -> bool:
    """True si la identificación fiscal tiene formato y dígito de control correctos."""
    return tipo(valor) is not None
