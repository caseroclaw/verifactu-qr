# verifactu-qr

<!-- mcp-name: io.github.caseroclaw/verifactu-qr -->

**URL del código QR tributario de VeriFactu (AEAT) y validación de NIF/CIF/NIE — sin dependencias, en una sola línea.**

[![listed on awesome-spain](https://img.shields.io/badge/listed%20on-awesome--spain-c60b1e?style=flat-square&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDIwIDE0Ij48cmVjdCB3aWR0aD0iMjAiIGhlaWdodD0iMTQiIGZpbGw9IiNjNjBiMWUiLz48cmVjdCB5PSIzLjUiIHdpZHRoPSIyMCIgaGVpZ2h0PSI3IiBmaWxsPSIjZmZjNDAwIi8+PC9zdmc+&labelColor=ffc400)](https://github.com/GeiserX/awesome-spain#readme)

Herramienta en Python para generar la URL que debe llevar el QR obligatorio de las facturas
españolas (RD 1007/2023 · Orden HAC/1177/2024) validando antes NIF, número de serie, fecha e
importe, con los **códigos de error oficiales** de la AEAT (2001-2006). Incluye CLI y servidor
**MCP** para agentes de IA.

> Mantenido por [Plataforma IA](https://plataformaia.com), consultora de automatización con IA
> para pymes en Madrid y toda España. Guía de plazos y preparación:
> [VeriFactu 2027 para pymes](https://plataformaia.com/es/blog/verifactu-2027-pymes-fechas-preparacion).

## Instalación

```bash
pip install verifactu-qr            # solo librería + CLI (0 dependencias)
pip install "verifactu-qr[svg]"     # + exportar el QR a SVG (segno)
```

## Uso rápido (CLI)

```bash
$ verifactu-qr qr --nif 89890001K --numserie "12345678&G33" --fecha 01-01-2024 --importe 241.4
https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=89890001K&numserie=12345678%26G33&fecha=01-01-2024&importe=241.4

# entorno de pruebas, sistema que NO remite registros (no VERI*FACTU) y QR en SVG
$ verifactu-qr qr --nif 89890001K --numserie "12345678&G33" --fecha 01-01-2024 --importe 241.4 \
    --pruebas --no-verifactu --svg qr.svg

$ verifactu-qr validar 89890001K
VALIDO: 89890001K (DNI)
```

## Uso como librería

```python
from verifactu_qr import build_qr_url, nif_valido, url_consulta_json

url = build_qr_url(
    nif="89890001K",
    numserie="12345678&G33",   # se codifica como 12345678%26G33 (URL encoding UTF-8)
    fecha="01-01-2024",        # o un datetime.date
    importe=241.4,             # o "241.40", Decimal
    verifactu=True,            # False -> .../ValidarQRNoVerifactu
    entorno="produccion",      # o "pruebas"
)
print(url)
print(url_consulta_json(url))   # añade &formato=json para parsear la respuesta de la AEAT
```

Errores con el código oficial: `QRError.code` ∈ {2001 NIF inválido, 2002 nº de serie demasiado
largo, 2003 caracteres no permitidos, 2004 fecha inválida, 2005 importe inválido, 2006 importe
demasiado largo}.

## Uso como servidor MCP (agentes de IA)

```json
{
  "mcpServers": {
    "verifactu-qr": { "command": "verifactu-qr-mcp" }
  }
}
```

Herramientas expuestas: `verifactu_qr_url`, `validar_identificacion_fiscal`, `url_consulta_json`.
Probarlo a mano:

```bash
$ printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | verifactu-qr-mcp
```

## Qué cubre y qué no

- **Cubre**: los 4 parámetros obligatorios del QR (`nif`, `numserie`, `fecha`, `importe`), las 4
  URLs base (producción/pruebas × VERI*FACTU/no verificable), el *URL encoding* con la misma
  semántica que `java.net.URLEncoder` (el detalle que más falla: `&` → `%26`, espacio → `+`), la
  validación con dígito de control de NIF/NIE/CIF y los códigos de error de la AEAT.
- **No cubre**: la huella (*hash*) de encadenamiento de registros, la firma electrónica XAdES, el
  envío SOAP de registros ni el diseño/maquetación del QR dentro del PDF (30-40 mm, nivel M).
  Para eso, ver `pyverifactu` o `verifactu` en PyPI.

Aviso: herramienta no oficial, sin vinculación con la AEAT. Verifica siempre el resultado con el
[portal de pruebas de la AEAT](https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR) antes de producción.

## Referencias

- Real Decreto 1007/2023, de 5 de diciembre ([BOE-A-2023-24840](https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840)).
- Orden HAC/1177/2024, arts. 20 y 21 (contenido del QR: NIF, serie y número, fecha, importe).
- AEAT, «Características del QR y especificaciones del servicio de cotejo» ([sede electrónica](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica/caracteristicas-qr-especificaciones-servicio-cotejo-factura.html)).

Los tests incluyen el vector de ejemplo oficial de la AEAT
(`nif=89890001K`, `numserie=12345678&G33` → `12345678%26G33`, `fecha=01-01-2024`, `importe=241.4`).

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Licencia

MIT — úsalo libremente en tu software de facturación.

---

## English

`verifactu-qr` builds the URL that Spanish invoices must embed in their mandatory tax QR code
(VeriFactu, RD 1007/2023) while validating the Spanish tax ID, invoice number, date and amount,
returning the official AEAT error codes. Zero dependencies, plus a CLI and a stdio MCP server so
AI agents can generate compliant QR URLs. Maintained by [Plataforma IA](https://plataformaia.com),
an AI automation consultancy based in Madrid, Spain.
