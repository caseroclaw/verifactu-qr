"""CLI: verifactu-qr qr ... | verifactu-qr validar <NIF>"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .nif import es_valido, tipo
from .qr import QRError, build_qr_url, url_consulta_json


def _cmd_qr(args: argparse.Namespace) -> int:
    entorno = "pruebas" if args.pruebas else "produccion"
    try:
        url = build_qr_url(
            args.nif,
            args.numserie,
            args.fecha,
            args.importe,
            verifactu=not args.no_verifactu,
            entorno=entorno,
        )
    except QRError as error:
        print("error %d: %s" % (error.code, error.message), file=sys.stderr)
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "url_qr": url,
                    "url_consulta_json": url_consulta_json(url),
                    "modo": "no verificable" if args.no_verifactu else "VERI*FACTU",
                    "entorno": entorno,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(url)
    if args.svg:
        try:
            import segno
        except ImportError:
            print(
                "Para --svg instala el extra: pip install 'verifactu-qr[svg]'",
                file=sys.stderr,
            )
            return 2
        segno.make(url, error="m").save(args.svg, scale=8, border=4)
        print("QR (nivel M) guardado en %s" % args.svg, file=sys.stderr)
    return 0


def _cmd_validar(args: argparse.Namespace) -> int:
    resultado = tipo(args.identificacion)
    if resultado is None:
        print("NO VALIDO: %s" % args.identificacion)
        return 1
    print("VALIDO: %s (%s)" % (args.identificacion.strip().upper(), resultado))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verifactu-qr",
        description="Genera la URL del código QR tributario de VeriFactu (RD 1007/2023, Orden HAC/1177/2024) y valida NIF/CIF/NIE.",
    )
    parser.add_argument("--version", action="version", version="verifactu-qr %s" % __version__)
    sub = parser.add_subparsers(dest="comando")

    qr = sub.add_parser("qr", help="construye y valida la URL del QR de la factura")
    qr.add_argument("--nif", required=True, help="NIF del obligado a expedir la factura")
    qr.add_argument("--numserie", required=True, help="serie y número de factura (máx. 60)")
    qr.add_argument("--fecha", required=True, help="fecha de expedición DD-MM-AAAA")
    qr.add_argument("--importe", required=True, help="importe total (punto decimal, máx. 12 enteros y 2 decimales)")
    qr.add_argument("--pruebas", action="store_true", help="entorno de pruebas (prewww2.aeat.es)")
    qr.add_argument("--no-verifactu", action="store_true", help="sistema que NO remite registros a la AEAT")
    qr.add_argument("--svg", metavar="FICHERO", help="guarda además el QR en SVG (requiere extra [svg])")
    qr.add_argument("--json", action="store_true", help="salida JSON")
    qr.set_defaults(func=_cmd_qr)

    validar = sub.add_parser("validar", help="valida un NIF, NIE o CIF")
    validar.add_argument("identificacion")
    validar.set_defaults(func=_cmd_validar)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
