import unittest

from verifactu_qr import QRError, build_qr_url, url_consulta_json, urlencode


class TestUrlEncode(unittest.TestCase):
    def test_igual_que_java_urlencoder(self):
        self.assertEqual("12345678%26G33", urlencode("12345678&G33"))
        self.assertEqual("FACTURA+1", urlencode("FACTURA 1"))
        self.assertEqual("A-B_1.2*3", urlencode("A-B_1.2*3"))

    def test_codifica_lo_que_encodeuricomponent_no_codifica(self):
        self.assertEqual("%7E", urlencode("~"))
        self.assertEqual("%28%29%21%27", urlencode("()!'"))

    def test_utf8_multibyte(self):
        self.assertEqual("%C3%A1%C3%B1", urlencode("áñ"))


class TestQROficial(unittest.TestCase):
    """Vector de ejemplo del documento técnico de la AEAT (apartado 8.2 / 4.1)."""

    OFICIAL = (
        "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR"
        "?nif=89890001K&numserie=12345678%26G33&fecha=01-01-2024&importe=241.4"
    )

    def test_vector_oficial(self):
        self.assertEqual(
            self.OFICIAL,
            build_qr_url("89890001K", "12345678&G33", "01-01-2024", "241.4", verifactu=True, entorno="pruebas"),
        )

    def test_bases(self):
        self.assertTrue(
            build_qr_url("89890001K", "A1", "01-01-2024", "1.0").startswith(
                "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=89890001K"
            )
        )
        self.assertTrue(
            build_qr_url("89890001K", "A1", "01-01-2024", "1.0", verifactu=False, entorno="pruebas").startswith(
                "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu?"
            )
        )

    def test_fecha_como_date_e_importe_numerico(self):
        import datetime

        self.assertEqual(
            self.OFICIAL,
            build_qr_url("89890001K", "12345678&G33", datetime.date(2024, 1, 1), 241.4, entorno="pruebas"),
        )

    def test_importe_normalizado(self):
        url = build_qr_url("89890001K", "A1", "01-01-2024", "241.40")
        self.assertTrue(url.endswith("importe=241.4"), url)
        self.assertTrue(build_qr_url("89890001K", "A1", "01-01-2024", 1000).endswith("importe=1000"))
        self.assertTrue(build_qr_url("89890001K", "A1", "01-01-2024", "-120.5").endswith("importe=-120.5"))

    def test_entorno_invalido(self):
        with self.assertRaises(ValueError):
            build_qr_url("89890001K", "A1", "01-01-2024", "1.0", entorno="staging")


class TestErroresAEAT(unittest.TestCase):
    def test_codigos_de_error(self):
        casos = [
            (("12345678A", "A1", "01-01-2024", "1.0"), 2001),
            (("89890001K", "X" * 61, "01-01-2024", "1.0"), 2002),
            (("89890001K", "FAC-ñ", "01-01-2024", "1.0"), 2003),
            (("89890001K", "A1", "01-13-2024", "1.0"), 2004),
            (("89890001K", "A1", "01-01-2024", "12,34,56"), 2005),
            (("89890001K", "A1", "01-01-2024", "1" * 13), 2006),
        ]
        for argumentos, esperado in casos:
            with self.subTest(argumentos=argumentos):
                with self.assertRaises(QRError) as ctx:
                    build_qr_url(*argumentos)
                self.assertEqual(esperado, ctx.exception.code)

    def test_mas_de_dos_decimales(self):
        with self.assertRaises(QRError) as ctx:
            build_qr_url("89890001K", "A1", "01-01-2024", "12.345")
        self.assertEqual(2005, ctx.exception.code)


class TestConsultaJson(unittest.TestCase):
    def test_anade_formato_json(self):
        url = build_qr_url("89890001K", "A1", "01-01-2024", "1.0")
        self.assertTrue(url_consulta_json(url).endswith("&formato=json"))
        self.assertEqual(url_consulta_json(url), url_consulta_json(url_consulta_json(url)))


if __name__ == "__main__":
    unittest.main()
