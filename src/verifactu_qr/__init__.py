"""verifactu-qr: URL del QR tributario de VeriFactu + validación fiscal española."""
from .nif import es_valido as nif_valido
from .nif import tipo as tipo_nif
from .qr import BASES, QRError, build_qr_url, url_consulta_json, urlencode

__version__ = "0.1.0"
__all__ = [
    "BASES",
    "QRError",
    "build_qr_url",
    "url_consulta_json",
    "urlencode",
    "nif_valido",
    "tipo_nif",
    "__version__",
]
