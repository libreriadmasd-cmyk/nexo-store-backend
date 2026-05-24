"""Nexo Store — Feature tests for launch-day improvements.

Covers:
  * GET  /api/search/suggest (predictive search)
  * POST /api/admin/clean-titles (bulk title cleanup)
  * POST /api/admin/products/{sku}/images (append/replace)
  * DELETE /api/admin/products/{sku}/images/{index}
  * PUT  /api/admin/products/{sku} with imagenes=[...] syncs imagen=imagenes[0]
  * Migration: every product has 'imagenes' as array
  * CSV upload populates both 'imagen' and 'imagenes'
"""
import os
import io
import uuid
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://school-supplies-hub-12.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_PASSWORD = "Netri 437"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_headers(s):
    r = s.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return {"X-Admin-Token": r.json()["token"]}


@pytest.fixture()
def temp_product(s, admin_headers):
    """Create a TEST_ product and delete it after the test."""
    sku = f"TEST_{uuid.uuid4().hex[:10].upper()}"
    payload = {
        "sku": sku,
        "nombre": "TEST Mochila Escolar",
        "categoria": "Marroquinería",
        "precio": 1500.0,
        "stock": 10,
        "imagen": "https://example.com/initial.jpg",
        "imagenes": ["https://example.com/initial.jpg"],
    }
    r = s.post(f"{API}/admin/products", json=payload, headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text
    yield sku
    s.delete(f"{API}/admin/products/{sku}", headers=admin_headers, timeout=15)


# ---------------- Search suggest ----------------
class TestSearchSuggest:
    def test_suggest_returns_items_with_required_fields(self, s):
        r = s.get(f"{API}/search/suggest", params={"q": "mochila", "limit": 6}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("items"), list)
        assert len(d["items"]) <= 6
        assert d.get("query") == "mochila"
        for it in d["items"]:
            assert "_id" not in it
            assert "sku" in it
            assert "nombre" in it
            assert "precio" in it
            assert "categoria" in it
            assert "imagen" in it
            assert "imagenes" in it
            assert isinstance(it["imagenes"], list)

    def test_suggest_limit_respected(self, s):
        r = s.get(f"{API}/search/suggest", params={"q": "a", "limit": 3}, timeout=20)
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 3

    def test_suggest_missing_q_returns_422(self, s):
        r = s.get(f"{API}/search/suggest", timeout=15)
        assert r.status_code == 422

    def test_suggest_regex_special_chars_are_escaped(self, s):
        # Should not raise 500; regex special chars must be escaped
        r = s.get(f"{API}/search/suggest", params={"q": "(.*["}, timeout=15)
        assert r.status_code == 200


# ---------------- Clean titles ----------------
class TestCleanTitles:
    def test_clean_titles_requires_auth(self, s):
        r = s.post(f"{API}/admin/clean-titles", timeout=20)
        assert r.status_code == 401

    def test_clean_titles_wrong_token_401(self, s):
        r = s.post(f"{API}/admin/clean-titles", headers={"X-Admin-Token": "bad"}, timeout=20)
        assert r.status_code == 401

    def test_clean_titles_with_token_returns_shape(self, s, admin_headers):
        r = s.post(f"{API}/admin/clean-titles", headers=admin_headers, timeout=90)
        assert r.status_code == 200
        d = r.json()
        assert "updated" in d and isinstance(d["updated"], int)
        assert "sample_before" in d and isinstance(d["sample_before"], list)
        assert "sample_after" in d and isinstance(d["sample_after"], list)
        assert len(d["sample_before"]) == len(d["sample_after"])

    def test_clean_titles_reverts_dirty_product(self, s, admin_headers):
        # Create a product with dirty name then run clean
        sku = f"TEST_{uuid.uuid4().hex[:10].upper()}"
        dirty = 'cuaderno  rivadavia""  ABC123'
        create = s.post(
            f"{API}/admin/products",
            headers=admin_headers,
            json={
                "sku": sku,
                "nombre": dirty,
                "categoria": "Librería",
                "precio": 100,
                "stock": 1,
                "imagen": "",
                "imagenes": [],
            },
            timeout=20,
        )
        # create_product uses _title_case not _clean_name, so dirty chars remain.
        assert create.status_code == 200, create.text
        try:
            r = s.post(f"{API}/admin/clean-titles", headers=admin_headers, timeout=90)
            assert r.status_code == 200
            # Verify product was cleaned
            g = s.get(f"{API}/products/{sku}", timeout=15).json()
            clean = g["nombre"]
            assert '""' not in clean
            assert "ABC123" not in clean
            # collapsed spaces + title case
            assert "  " not in clean
        finally:
            s.delete(f"{API}/admin/products/{sku}", headers=admin_headers, timeout=15)


# ---------------- Gallery: add / replace / delete / sync ----------------
class TestGallery:
    def test_add_image_requires_auth(self, s, temp_product):
        r = s.post(
            f"{API}/admin/products/{temp_product}/images",
            json={"url": "https://x.com/a.jpg"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_add_image_appends(self, s, admin_headers, temp_product):
        url2 = "https://example.com/second.jpg"
        r = s.post(
            f"{API}/admin/products/{temp_product}/images",
            headers=admin_headers,
            json={"url": url2},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["imagenes"] == ["https://example.com/initial.jpg", url2]
        assert doc["imagen"] == "https://example.com/initial.jpg"  # first remains primary

    def test_add_image_replace_at_index(self, s, admin_headers, temp_product):
        new_first = "https://example.com/replaced-primary.jpg"
        r = s.post(
            f"{API}/admin/products/{temp_product}/images",
            headers=admin_headers,
            json={"url": new_first, "index": 0},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["imagenes"][0] == new_first
        assert doc["imagen"] == new_first  # primary in sync

    def test_add_image_empty_url_400(self, s, admin_headers, temp_product):
        r = s.post(
            f"{API}/admin/products/{temp_product}/images",
            headers=admin_headers,
            json={"url": "   "},
            timeout=15,
        )
        assert r.status_code == 400

    def test_add_image_unknown_sku_404(self, s, admin_headers):
        r = s.post(
            f"{API}/admin/products/NO_SUCH_SKU_XYZ/images",
            headers=admin_headers,
            json={"url": "https://x.com/a.jpg"},
            timeout=15,
        )
        assert r.status_code == 404

    def test_delete_image_out_of_range_400(self, s, admin_headers, temp_product):
        r = s.delete(
            f"{API}/admin/products/{temp_product}/images/99",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 400

    def test_delete_image_removes_and_resyncs_primary(self, s, admin_headers, temp_product):
        # add second then delete index 0 → imagen must become old second
        url2 = "https://example.com/B.jpg"
        s.post(
            f"{API}/admin/products/{temp_product}/images",
            headers=admin_headers,
            json={"url": url2},
            timeout=20,
        )
        r = s.delete(
            f"{API}/admin/products/{temp_product}/images/0",
            headers=admin_headers,
            timeout=20,
        )
        assert r.status_code == 200, r.text
        doc = r.json()
        assert url2 in doc["imagenes"]
        assert len(doc["imagenes"]) == 1
        assert doc["imagen"] == url2  # primary resynced

    def test_delete_all_images_clears_primary(self, s, admin_headers, temp_product):
        r = s.delete(
            f"{API}/admin/products/{temp_product}/images/0",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200
        doc = r.json()
        assert doc["imagenes"] == []
        assert doc["imagen"] == ""


# ---------------- PUT /admin/products sync imagen/imagenes ----------------
class TestPutSyncsImagenes:
    def test_put_imagenes_sets_imagen_to_first(self, s, admin_headers, temp_product):
        arr = [
            "https://example.com/1.jpg",
            "https://example.com/2.jpg",
            "https://example.com/3.jpg",
        ]
        r = s.put(
            f"{API}/admin/products/{temp_product}",
            headers=admin_headers,
            json={"imagenes": arr},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["imagenes"] == arr
        assert d["imagen"] == arr[0]

    def test_put_empty_imagenes_clears_primary(self, s, admin_headers, temp_product):
        r = s.put(
            f"{API}/admin/products/{temp_product}",
            headers=admin_headers,
            json={"imagenes": []},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["imagenes"] == []
        assert d["imagen"] == ""

    def test_put_imagen_only_mirrors_to_imagenes_zero(self, s, admin_headers, temp_product):
        new_primary = "https://example.com/only-primary.jpg"
        r = s.put(
            f"{API}/admin/products/{temp_product}",
            headers=admin_headers,
            json={"imagen": new_primary},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["imagen"] == new_primary
        assert d["imagenes"][0] == new_primary


# ---------------- Migration: imagenes field exists ----------------
class TestMigration:
    def test_all_products_have_imagenes_array(self, s):
        # Sample 3 pages
        for skip in (0, 2000, 4000):
            r = s.get(f"{API}/products", params={"skip": skip, "limit": 100}, timeout=25)
            assert r.status_code == 200
            for it in r.json()["items"]:
                assert "imagenes" in it, f"Missing imagenes in {it.get('sku')}"
                assert isinstance(it["imagenes"], list), f"imagenes is not a list in {it.get('sku')}"


# ---------------- CSV upload populates imagen + imagenes ----------------
class TestCSVUploadGallery:
    def test_csv_upsert_sets_imagenes_from_imagen(self, s, admin_headers):
        sku = f"TEST_{uuid.uuid4().hex[:10].upper()}"
        img = "https://example.com/csv-test.jpg"
        csv_text = (
            "SKU,Nombre,Categoria,Precio,Stock,Imagen URL\n"
            f"{sku},Mochila CSV Test,Marroquinería,2500,5,{img}\n"
        )
        files = {"file": ("test.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
        r = s.post(
            f"{API}/admin/csv-upload",
            files=files,
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text
        try:
            g = s.get(f"{API}/products/{sku}", timeout=15)
            assert g.status_code == 200
            d = g.json()
            assert d["imagen"] == img
            assert d["imagenes"] == [img]
        finally:
            s.delete(f"{API}/admin/products/{sku}", headers=admin_headers, timeout=15)

    def test_csv_no_image_gives_empty_imagenes(self, s, admin_headers):
        sku = f"TEST_{uuid.uuid4().hex[:10].upper()}"
        csv_text = (
            "SKU,Nombre,Categoria,Precio,Stock,Imagen URL\n"
            f"{sku},Producto Sin Imagen,Librería,100,1,\n"
        )
        files = {"file": ("test.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
        r = s.post(
            f"{API}/admin/csv-upload",
            files=files,
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200
        try:
            d = s.get(f"{API}/products/{sku}", timeout=15).json()
            assert d["imagen"] == ""
            assert d["imagenes"] == []
        finally:
            s.delete(f"{API}/admin/products/{sku}", headers=admin_headers, timeout=15)
