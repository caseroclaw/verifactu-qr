"""Servidor MCP (stdio, sin dependencias) con las herramientas de verifactu-qr.

Expone para agentes de IA:
- ``verifactu_qr_url``: URL del QR tributario validada.
- ``validar_identificacion_fiscal``: NIF/NIE/CIF válido o no.
- ``url_consulta_json``: variante de la URL para consultar la AEAT en JSON.

Arranque:  verifactu-qr-mcp   |   python -m verifactu_qr.mcp_server
Transporte: JSON-RPC 2.0 delimitado por líneas nuevas sobre stdin/stdout.
"""
from __future__ import annotations

import json
import sys

from . import __version__
from .nif import es_valido, tipo
from .qr import QRError, build_qr_url, url_consulta_json

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "verifactu-qr", "version": __version__}

TOOLS = [
    {
        "name": "verifactu_qr_url",
        "description": (
            "Genera la URL del código QR tributario de una factura española (VeriFactu, "
            "RD 1007/2023 y Orden HAC/1177/2024) validando NIF, número de serie, fecha e importe."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "nif": {"type": "string", "description": "NIF del obligado a expedir la factura (9 caracteres)"},
                "numserie": {"type": "string", "description": "serie y número de factura, máximo 60 caracteres"},
                "fecha": {"type": "string", "description": "fecha de expedición en formato DD-MM-AAAA"},
                "importe": {"type": "string", "description": "importe total, punto decimal, máximo 12 enteros y 2 decimales"},
                "verifactu": {
                    "type": "boolean",
                    "description": "true si el sistema remite los registros a la AEAT (VERI*FACTU); por defecto true",
                },
                "entorno": {"type": "string", "enum": ["produccion", "pruebas"], "description": "por defecto produccion"},
            },
            "required": ["nif", "numserie", "fecha", "importe"],
        },
    },
    {
        "name": "validar_identificacion_fiscal",
        "description": "Comprueba si un NIF, NIE o CIF español tiene formato y dígito de control correctos.",
        "inputSchema": {
            "type": "object",
            "properties": {"identificacion": {"type": "string"}},
            "required": ["identificacion"],
        },
    },
    {
        "name": "url_consulta_json",
        "description": "Añade formato=json a una URL de QR para consultar el servicio de la AEAT en JSON (no va dentro del QR).",
        "inputSchema": {
            "type": "object",
            "properties": {"url_qr": {"type": "string"}},
            "required": ["url_qr"],
        },
    },
]


def _texto(texto: str, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": texto}], "isError": error}


def _llamar(nombre: str, argumentos: dict) -> dict:
    if nombre == "verifactu_qr_url":
        url = build_qr_url(
            argumentos.get("nif", ""),
            argumentos.get("numserie", ""),
            argumentos.get("fecha", ""),
            argumentos.get("importe", ""),
            verifactu=argumentos.get("verifactu", True),
            entorno=argumentos.get("entorno", "produccion"),
        )
        return _texto(json.dumps({"url_qr": url, "url_consulta_json": url_consulta_json(url)}, ensure_ascii=False))
    if nombre == "validar_identificacion_fiscal":
        valor = str(argumentos.get("identificacion", ""))
        clase = tipo(valor)
        return _texto(json.dumps({"identificacion": valor.strip().upper(), "valido": es_valido(valor), "tipo": clase}, ensure_ascii=False))
    if nombre == "url_consulta_json":
        return _texto(url_consulta_json(str(argumentos.get("url_qr", ""))))
    raise ValueError("Herramienta desconocida: %s" % nombre)


def handle(mensaje: dict) -> dict | None:
    """Procesa un mensaje JSON-RPC y devuelve la respuesta (None en notificaciones)."""
    metodo = mensaje.get("method")
    ident = mensaje.get("id")
    if ident is None:
        return None  # notificación (notifications/initialized, ...)
    if metodo == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": ident,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if metodo == "tools/list":
        return {"jsonrpc": "2.0", "id": ident, "result": {"tools": TOOLS}}
    if metodo == "tools/call":
        parametros = mensaje.get("params") or {}
        try:
            resultado = _llamar(parametros.get("name", ""), parametros.get("arguments") or {})
        except QRError as error:
            resultado = _texto("error %d: %s" % (error.code, error.message), error=True)
        except (ValueError, TypeError) as error:
            resultado = _texto(str(error), error=True)
        return {"jsonrpc": "2.0", "id": ident, "result": resultado}
    if metodo == "ping":
        return {"jsonrpc": "2.0", "id": ident, "result": {}}
    return {
        "jsonrpc": "2.0",
        "id": ident,
        "error": {"code": -32601, "message": "Método no soportado: %s" % metodo},
    }


def main() -> int:
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        try:
            mensaje = json.loads(linea)
        except json.JSONDecodeError:
            continue
        respuesta = handle(mensaje)
        if respuesta is not None:
            sys.stdout.write(json.dumps(respuesta, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
