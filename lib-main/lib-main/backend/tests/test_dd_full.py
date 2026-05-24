"""Nexo Store full backend regression."""
import os
import pytest
import requests

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8001").rstrip("/")
ADMIN_PWD = "Netri 437"
API = f"{BASE}/api"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def token(s):
    r = s.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def sample_sku(s):
    r = s.get(f"{API}/products", params={"limit": 1}, timeout=30)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    return items[0]["sku"]


# ---------- Public ----------

def test_categories(s):
    r = s.get(f"{API}/categories", timeout=30)
    assert r.status_code == 200
    data = r.json()
    names = {c["name"] for c in data["categories"]}
    expected = {"Marroquinería", "Librería", "Juguetería", "Regalería", "Tecno"}
    assert expected.issubset(names), f"missing cats: {expected - names}"
    for c in data["categories"]:
        if c["name"] in expected:
            assert c["count"] > 0


@pytest.mark.parametrize("params", [
    {"categoria": "Librería"},
    {"on_sale": "true"},
    {"min_price": 100, "max_price": 5000},
    {"q": "lapiz"},
    {"sort": "offers"},
])
def test_products_filters(s, params):
    r = s.get(f"{API}/products", params={**params, "limit": 5}, timeout=30)
    assert r.status_code == 200, r.text
    assert "items" in r.json()


def test_featured(s):
    r = s.get(f"{API}/featured", timeout=30)
    assert r.status_code == 200
    sec = r.json()["sections"]
    for c in ["Marroquinería", "Librería", "Juguetería", "Regalería", "Tecno"]:
        assert c in sec, f"missing section {c}"
        assert len(sec[c]) <= 3


def test_facets(s):
    r = s.get(f"{API}/facets", params={"categoria": "Librería"}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "brands" in d and "colors" in d and "price" in d
    assert "min" in d["price"] and "max" in d["price"]


# ---------- Admin auth ----------

def test_admin_login_ok(s):
    r = s.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=30)
    assert r.status_code == 200
    assert "token" in r.json()


def test_admin_login_bad(s):
    r = s.post(f"{API}/admin/login", json={"password": "wrong"}, timeout=30)
    assert r.status_code == 401


# ---------- Admin product mutations ----------

def test_update_product_oferta_destacado(s, token, sample_sku):
    h = {"X-Admin-Token": token}
    r = s.put(f"{API}/admin/products/{sample_sku}", json={"precio_oferta": 1234.0, "destacado": True}, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    g = s.get(f"{API}/products/{sample_sku}", timeout=30).json()
    assert g["precio_oferta"] == 1234.0
    assert g["destacado"] is True
    # cleanup
    s.put(f"{API}/admin/products/{sample_sku}", json={"precio_oferta": 0, "destacado": False}, headers=h, timeout=30)


def test_image_add_remove(s, token, sample_sku):
    h = {"X-Admin-Token": token}
    test_url = "https://res.cloudinary.com/darxvchbt/image/upload/test_img.jpg"
    r = s.post(f"{API}/admin/products/{sample_sku}/images", json={"url": test_url}, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    imgs = r.json()["imagenes"]
    assert test_url in imgs
    idx = imgs.index(test_url)
    r2 = s.delete(f"{API}/admin/products/{sample_sku}/images/{idx}", headers=h, timeout=30)
    assert r2.status_code == 200
    assert test_url not in r2.json()["imagenes"]


def test_extract_attributes(s, token):
    h = {"X-Admin-Token": token}
    r = s.post(f"{API}/admin/extract-attributes", headers=h, timeout=180)
    assert r.status_code == 200
    assert "updated" in r.json()


def test_admin_stats(s, token):
    h = {"X-Admin-Token": token}
    r = s.get(f"{API}/admin/stats", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ["total", "in_stock", "missing_image", "on_sale", "featured"]:
        assert k in d
    assert d["total"] > 0
