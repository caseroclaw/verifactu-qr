import unittest

from verifactu_qr import nif_valido, tipo_nif
from verifactu_qr.mcp_server import handle


class TestNif(unittest.TestCase):
    def test_dni_valido(self):
        self.assertEqual("DNI", tipo_nif("89890001K"))
        self.assertEqual("DNI", tipo_nif("12345678Z"))
        self.assertTrue(nif_valido("00000000T"))

    def test_nie_valido(self):
        self.assertEqual("NIE", tipo_nif("X1234567L"))
        self.assertEqual("NIE", tipo_nif("Y1234567X"))

    def test_cif_valido(self):
        self.assertEqual("CIF", tipo_nif("A58818501"))
        self.assertEqual("CIF", tipo_nif("B58378431"))
        self.assertEqual("CIF", tipo_nif("Q2826004J"))

    def test_invalidos(self):
        for valor in ("12345678A", "89890001X", "", "A58818502", "X1234567A", "1234567"):
            with self.subTest(valor=valor):
                self.assertFalse(nif_valido(valor), valor)

    def test_normaliza_separadores(self):
        self.assertTrue(nif_valido("12345678-z"))


class TestMCP(unittest.TestCase):
    def test_initialize_y_tools_list(self):
        respuesta = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual("verifactu-qr", respuesta["result"]["serverInfo"]["name"])
        herramientas = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(
            ["verifactu_qr_url", "validar_identificacion_fiscal", "url_consulta_json"],
            [h["name"] for h in herramientas],
        )

    def test_notificacion_sin_respuesta(self):
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_tools_call_ok(self):
        respuesta = handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "verifactu_qr_url",
                    "arguments": {
                        "nif": "89890001K",
                        "numserie": "12345678&G33",
                        "fecha": "01-01-2024",
                        "importe": "241.4",
                        "entorno": "pruebas",
                    },
                },
            }
        )
        self.assertFalse(respuesta["result"]["isError"])
        self.assertIn("numserie=12345678%26G33", respuesta["result"]["content"][0]["text"])

    def test_tools_call_error_aeat(self):
        respuesta = handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "verifactu_qr_url", "arguments": {"nif": "12345678A", "numserie": "A1", "fecha": "01-01-2024", "importe": "1.0"}},
            }
        )
        self.assertTrue(respuesta["result"]["isError"])
        self.assertIn("2001", respuesta["result"]["content"][0]["text"])

    def test_metodo_desconocido(self):
        respuesta = handle({"jsonrpc": "2.0", "id": 5, "method": "resources/list"})
        self.assertEqual(-32601, respuesta["error"]["code"])


if __name__ == "__main__":
    unittest.main()
