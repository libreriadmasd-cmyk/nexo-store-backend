"""Nexo Store backend API tests - public catalog + admin CMS."""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://school-supplies-hub-12.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_PASSWORD = "Netri 437"
SEED_CSV = "/app/backend/initial_catalog.csv"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ---------------- Public catalog ----------------
class TestPublicCatalog:
    def test_root(self, s):
        r = s.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_products_default(self, s):
        r = s.get(f"{API}/products", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["items"], list)
        assert d["total"] > 0
        assert d["limit"] == 48
        assert len(d["items"]) <= 48
        # _id MUST not leak
        for it in d["items"][:5]:
            assert "_id" not in it
            assert "sku" in it and "nombre" in it

    @pytest.mark.parametrize("sort", ["relevance", "price_asc", "price_desc", "name_asc", "newest"])
    def test_products_sort(self, s, sort):
        r = s.get(f"{API}/products", params={"sort": sort, "limit": 10}, timeout=20)
        assert r.status_code == 200
        items = r.json()["items"]
        if sort == "price_asc" and len(items) > 1:
            prices = [i["precio"] for i in items]
            assert prices == sorted(prices)
        if sort == "price_desc" and len(items) > 1:
            prices = [i["precio"] for i in items]
            assert prices == sorted(prices, reverse=True)
        if sort == "name_asc" and len(items) > 1:
            names = [i["nombre"] for i in items]
            assert names == sorted(names)

    def test_products_search(self, s):
        # First find a sku that exists
        r = s.get(f"{API}/products", params={"limit": 1}, timeout=20)
        sku = r.json()["items"][0]["sku"]
        r2 = s.get(f"{API}/products", params={"q": sku}, timeout=20)
        assert r2.status_code == 200
        skus = [i["sku"] for i in r2.json()["items"]]
        assert sku in skus

    def test_products_pagination(self, s):
        r1 = s.get(f"{API}/products", params={"skip": 0, "limit": 5}, timeout=20)
        r2 = s.get(f"{API}/products", params={"skip": 5, "limit": 5}, timeout=20)
        skus1 = {i["sku"] for i in r1.json()["items"]}
        skus2 = {i["sku"] for i in r2.json()["items"]}
        assert not (skus1 & skus2)

    def test_get_product_by_sku(self, s):
        r = s.get(f"{API}/products", params={"limit": 1}, timeout=20)
        sku = r.json()["items"][0]["sku"]
        r2 = s.get(f"{API}/products/{sku}", timeout=20)
        assert r2.status_code == 200
        assert r2.json()["sku"] == sku
        assert "_id" not in r2.json()

    def test_get_product_404(self, s):
        r = s.get(f"{API}/products/__NOPE__SKU__123", timeout=20)
        assert r.status_code == 404

    def test_categories(self, s):
        r = s.get(f"{API}/categories", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["total"] > 0
        assert isinstance(d["categories"], list)
        assert all("name" in c and "count" in c for c in d["categories"])


# ---------------- Admin auth ----------------
class TestAdminAuth:
    def test_login_success(self, s):
        r = s.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        assert r.json()["token"] == ADMIN_PASSWORD

    def test_login_wrong(self, s):
        r = s.post(f"{API}/admin/login", json={"password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_stats_no_token(self, s):
        r = s.get(f"{API}/admin/stats", timeout=15)
        assert r.status_code == 401

    def test_stats_with_token(self, s, admin_token):
        r = s.get(f"{API}/admin/stats", headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "total" in d and "in_stock" in d and "missing_image" in d
        assert d["total"] > 0


# ---------------- Admin CRUD ----------------
class TestAdminCrud:
    TEST_SKU = "TEST_SKU_DD_AUTO_001"
    TEST_SKU_DUP = "TEST_SKU_DD_AUTO_DUP"

    def test_cleanup_pre(self, s, admin_token):
        # ensure clean
        for sku in [self.TEST_SKU, self.TEST_SKU_DUP]:
            s.delete(f"{API}/admin/products/{sku}", headers={"X-Admin-Token": admin_token})

    def test_create_product(self, s, admin_token):
        body = {
            "sku": self.TEST_SKU,
            "nombre": "TEST producto auto",
            "categoria": "Marroquinería",
            "precio": 1234.5,
            "stock": 7,
            "imagen": "",
        }
        r = s.post(f"{API}/admin/products", json=body, headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["sku"] == self.TEST_SKU
        assert d["precio"] == 1234.5
        assert d["stock"] == 7
        assert "_id" not in d

        # GET to verify persistence
        r2 = s.get(f"{API}/products/{self.TEST_SKU}", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["stock"] == 7

    def test_create_duplicate_409(self, s, admin_token):
        body = {"sku": self.TEST_SKU, "nombre": "dup", "precio": 1, "stock": 1}
        r = s.post(f"{API}/admin/products", json=body, headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 409

    def test_update_product(self, s, admin_token):
        r = s.put(
            f"{API}/admin/products/{self.TEST_SKU}",
            json={"stock": 99, "precio": 555.0, "categoria": "Librería"},
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert d["stock"] == 99
        assert d["precio"] == 555.0
        assert d["categoria"] == "Librería"

        # GET to verify persistence
        r2 = s.get(f"{API}/products/{self.TEST_SKU}", timeout=15)
        assert r2.json()["stock"] == 99

    def test_update_no_token_401(self, s):
        r = s.put(f"{API}/admin/products/{self.TEST_SKU}", json={"stock": 1}, timeout=15)
        assert r.status_code == 401

    def test_update_404(self, s, admin_token):
        r = s.put(
            f"{API}/admin/products/__NOPE__",
            json={"stock": 1},
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert r.status_code == 404

    def test_delete_404(self, s, admin_token):
        r = s.delete(
            f"{API}/admin/products/__NOPE__SKU__",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert r.status_code == 404

    def test_delete_product(self, s, admin_token):
        r = s.delete(f"{API}/admin/products/{self.TEST_SKU}", headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 200
        # verify gone
        r2 = s.get(f"{API}/products/{self.TEST_SKU}", timeout=15)
        assert r2.status_code == 404


# ---------------- CSV upload ----------------
class TestCsvUpload:
    def test_upload_no_token(self, s):
        files = {"file": ("a.csv", io.BytesIO(b"SKU,Nombre,Precio,Stock\n"), "text/csv")}
        r = s.post(f"{API}/admin/csv-upload", files=files, timeout=15)
        assert r.status_code == 401

    def test_upload_small_csv(self, s, admin_token):
        csv_data = (
            "SKU,Nombre,Categoria,Precio,Stock,Imagen URL\n"
            "TEST_CSV_001,Producto Csv Uno,Marroquinería,100.5,5,\n"
            "TEST_CSV_002,Producto Csv Dos,Librería,250,10,\n"
        ).encode("utf-8")
        files = {"file": ("mini.csv", io.BytesIO(csv_data), "text/csv")}
        r = s.post(
            f"{API}/admin/csv-upload?mode=upsert",
            files=files,
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["received"] == 2
        assert d["mode"] == "upsert"
        assert d["total_in_db"] >= 2

        # verify persisted
        r2 = s.get(f"{API}/products/TEST_CSV_001", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["precio"] == 100.5

        # cleanup
        for sku in ["TEST_CSV_001", "TEST_CSV_002"]:
            s.delete(f"{API}/admin/products/{sku}", headers={"X-Admin-Token": admin_token})

    def test_upload_empty_csv_400(self, s, admin_token):
        files = {"file": ("empty.csv", io.BytesIO(b"SKU,Nombre,Precio,Stock\n"), "text/csv")}
        r = s.post(
            f"{API}/admin/csv-upload",
            files=files,
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert r.status_code == 400
