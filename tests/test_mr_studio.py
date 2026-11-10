"""Pruebas para el procesador de releases de MR Studio."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1]/"scripts"/"mr_studio.py"
spec = importlib.util.spec_from_file_location("mr_studio", path)
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)

class StudioTests(unittest.TestCase):
    def test_bullets(self):
        self.assertEqual(studio.highlights("- **Nuevo:** Efectos en escena\n- Corrige problemas de música"),
                         ["Nuevo: Efectos en escena","Corrige problemas de música"])
    def test_no_unsubstantiated_news(self):
        self.assertTrue(studio.highlights("## Título")[0].startswith("Consulta"))
    def test_markdown(self):
        self.assertEqual(studio.clean("- [Nuevo panel](https://example.com) para jugar"),
                         "Nuevo panel para jugar")
    def test_old(self):
        self.assertFalse(studio.recent("2024-01-01T10:00:00Z"))
        self.assertFalse(studio.recent("invalid"))
    def test_draft_only(self):
        p={"name":"Prueba","repo":"mr-test","description":"Una herramienta",
           "landing":"https://github.com/ManuRomera/mr-test","rights":"pendiente"}
        r={"tag_name":"v1.0.0","html_url":"https://github.com/ManuRomera/mr-test/releases/tag/v1.0.0",
           "body":"- Corrige transiciones entre escenas."}
        c=studio.build(p,r)
        self.assertFalse(c["publication_enabled"])
        self.assertFalse(c["official_foundry_listing_eligible"])
        self.assertTrue(c["rights_review_required"])
        self.assertIn("BORRADOR",studio.markdown(c))

if __name__ == "__main__":
    unittest.main()
