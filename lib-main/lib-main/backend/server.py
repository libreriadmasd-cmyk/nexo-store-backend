from fastapi import FastAPI, APIRouter, HTTPException, Header, UploadFile, File, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import csv
import io
import logging
import unicodedata
import re
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')

app = FastAPI(title="Nexo Store API")
api_router = APIRouter(prefix="/api")

# =========================================================
# Product model
# =========================================================

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sku: str
    nombre: str
    categoria: str = "General"
    subcategoria: Optional[str] = ""
    marca: Optional[str] = ""
    color: Optional[str] = ""
    precio: float = 0
    precio_oferta: Optional[float] = 0  # 0 = sin oferta
    destacado: bool = False
    stock: int = 0
    imagen: str = ""
    imagenes: List[str] = Field(default_factory=list)
    video_url: Optional[str] = ""
    updated_at: Optional[str] = None


class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    marca: Optional[str] = None
    color: Optional[str] = None
    precio: Optional[float] = None
    precio_oferta: Optional[float] = None
    destacado: Optional[bool] = None
    stock: Optional[int] = None
    imagen: Optional[str] = None
    imagenes: Optional[List[str]] = None
    video_url: Optional[str] = None


class ImageOp(BaseModel):
    url: str
    index: Optional[int] = None


class LoginBody(BaseModel):
    password: str


PUBLIC_PROJECTION = {"_id": 0}

# =========================================================
# Helpers
# =========================================================

_NAN_VALUES = {"nan", "none", "null", "", "-", "—"}
_SMALL_WORDS = {"de", "del", "la", "el", "las", "los", "en", "y", "a", "con", "para", "por", "un", "una"}

_TRAILING_CODE_RE = re.compile(r"\s+(?:[A-Z]{1,3}\d{3,6}|[A-Z0-9]{6,})\s*$")
_MULTI_QUOTE_RE = re.compile(r'["¨´`]{2,}')
_WEIRD_CHARS_RE = re.compile(r"[¨´`]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def _title_case(s: str) -> str:
    words = (s or "").strip().split()
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        if i > 0 and low in _SMALL_WORDS:
            out.append(low)
        elif len(w) <= 3 and w.isupper() and not any(c.islower() for c in w):
            out.append(w)
        else:
            out.append(low.capitalize())
    return " ".join(out)


def _clean_name(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return s
    s = _MULTI_QUOTE_RE.sub('"', s)
    s = _WEIRD_CHARS_RE.sub("", s)
    s = s.replace('"', "")
    prev = None
    while prev != s:
        prev = s
        s = _TRAILING_CODE_RE.sub("", s).rstrip(' .,-"')
    s = _MULTI_SPACE_RE.sub(" ", s).strip()
    return _title_case(s)


def _clean_category(raw: str) -> str:
    v = (raw or "").strip()
    if v.lower() in _NAN_VALUES:
        return "General"
    return v


# Brand & color extraction heuristics
KNOWN_BRANDS = [
    "Rivadavia", "Pelikan", "Maped", "Bic", "Faber-Castell", "Faber Castell",
    "Stabilo", "Pilot", "Filgo", "Cresko", "Mooving", "Wabro", "Top Model",
    "Disney", "Marvel", "Barbie", "Hot Wheels", "Lego", "Playmobil", "Sonic",
    "Paw Patrol", "Pokemon", "Frozen", "Spider", "Batman", "Avengers",
    "Minecraft", "Roblox", "Stitch", "Bandai", "Mattel", "Hasbro", "Samsung",
    "Xiaomi", "JBL", "Logitech", "Genius", "Noganet", "Philco", "Motorola",
    "Apple", "Sony", "HP", "Lenovo", "Acer", "Asus", "Microsoft", "Tomy",
    "Tomi", "Faber", "Cris", "Nuvita", "Nuvitas",
]

KNOWN_COLORS = [
    "Negro", "Blanco", "Rojo", "Azul", "Verde", "Amarillo", "Rosa", "Rosado",
    "Violeta", "Lila", "Lavanda", "Naranja", "Gris", "Plata", "Plateado", "Dorado", "Oro",
    "Marron", "Marrón", "Beige", "Crema", "Celeste", "Turquesa", "Aqua", "Menta",
    "Coral", "Salmón", "Salmon", "Fucsia", "Magenta", "Bordo", "Bordó", "Vino",
    "Multicolor", "Pastel", "Holografico", "Holográfico", "Metalizado", "Cobre",
    "Mostaza", "Caqui", "Khaki", "Verde Agua", "Verde Oliva", "Azul Marino",
    "Azul Francia", "Azul Petróleo", "Petroleo",
]


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s or "")
        if not unicodedata.combining(c)
    ).lower()


def _detect_brand(name: str) -> str:
    n = _strip_accents(name)
    for b in KNOWN_BRANDS:
        if _strip_accents(b) in n:
            return b
    return ""


def _detect_color(name: str) -> str:
    n = _strip_accents(name)
    for c in KNOWN_COLORS:
        if _strip_accents(c) in n:
            return c.replace("Marron", "Marrón")
    return ""


def _parse_csv_rows(raw_text: str):
    raw_text = raw_text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(raw_text))
    now = datetime.now(timezone.utc).isoformat()
    for row in reader:
        if not row:
            continue
        sku = (row.get("SKU") or row.get("sku") or "").strip()
        if not sku:
            continue
        nombre = _clean_name(row.get("Nombre") or row.get("nombre") or "")
        if not nombre:
            continue
        try:
            precio = float(row.get("Precio") or row.get("precio") or 0)
        except (ValueError, TypeError):
            precio = 0.0
        try:
            stock = int(float(row.get("Stock") or row.get("stock") or 0))
        except (ValueError, TypeError):
            stock = 0
        imagen = (row.get("Imagen URL") or row.get("imagen") or "").strip()
        cat = _clean_category(row.get("Categoria") or row.get("categoria") or "")
        marca = (row.get("Marca") or "").strip() or _detect_brand(nombre)
        color = (row.get("Color") or "").strip() or _detect_color(nombre)
        yield {
            "sku": sku,
            "nombre": nombre,
            "categoria": cat,
            "subcategoria": (row.get("Subcategoria") or "").strip(),
            "marca": marca,
            "color": color,
            "precio": round(precio, 2),
            "precio_oferta": 0,
            "destacado": False,
            "stock": max(0, stock),
            "imagen": imagen,
            "imagenes": [imagen] if imagen else [],
            "updated_at": now,
        }


def _require_admin(token: Optional[str]):
    if not ADMIN_PASSWORD:
        raise HTTPException(500, "Admin no configurado")
    if token != ADMIN_PASSWORD:
        raise HTTPException(401, "Credenciales inválidas")


# =========================================================
# Public catalog endpoints
# =========================================================

@api_router.get("/")
async def root():
    return {"service": "Nexo Store API", "ok": True}


@api_router.get("/products")
async def list_products(
    categoria: Optional[str] = Query(None),
    subcategoria: Optional[str] = Query(None),
    marca: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    on_sale: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("relevance"),
    skip: int = Query(0, ge=0),
    limit: int = Query(48, ge=1, le=200),
):
    query: dict = {}
    if categoria and categoria != "Todos":
        query["categoria"] = categoria
    if subcategoria:
        query["subcategoria"] = subcategoria
    if marca:
        query["marca"] = marca
    if color:
        query["color"] = color
    if on_sale:
        query["precio_oferta"] = {"$gt": 0}
    # Effective price filter: use precio_oferta if > 0 else precio
    if min_price is not None or max_price is not None:
        conds = []
        if min_price is not None:
            conds.append({
                "$gte": [
                    {"$cond": [
                        {"$gt": [{"$ifNull": ["$precio_oferta", 0]}, 0]},
                        "$precio_oferta",
                        "$precio",
                    ]},
                    float(min_price),
                ]
            })
        if max_price is not None:
            conds.append({
                "$lte": [
                    {"$cond": [
                        {"$gt": [{"$ifNull": ["$precio_oferta", 0]}, 0]},
                        "$precio_oferta",
                        "$precio",
                    ]},
                    float(max_price),
                ]
            })
        query["$expr"] = {"$and": conds} if len(conds) > 1 else conds[0]
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"nombre": rx}, {"sku": rx}, {"marca": rx}]

    sort_spec = {
        "relevance": [("destacado", -1), ("stock", -1), ("nombre", 1)],
        "price_asc": [("precio", 1)],
        "price_desc": [("precio", -1)],
        "name_asc": [("nombre", 1)],
        "newest": [("updated_at", -1)],
        "offers": [("precio_oferta", -1)],
    }.get(sort, [("nombre", 1)])

    total = await db.products.count_documents(query)
    cursor = db.products.find(query, PUBLIC_PROJECTION).sort(sort_spec).skip(skip).limit(limit)
    items = await cursor.to_list(limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@api_router.get("/products/{sku}")
async def get_product(sku: str):
    doc = await db.products.find_one({"sku": sku}, PUBLIC_PROJECTION)
    if not doc:
        raise HTTPException(404, "Producto no encontrado")
    return doc


@api_router.get("/featured")
async def featured(per_category: int = Query(3, ge=1, le=12)):
    """Returns up to `per_category` featured (or top-stock) items per main category."""
    cats = ["Marroquinería", "Librería", "Juguetería", "Regalería", "Tecno"]
    out = {}
    for c in cats:
        # First try destacados
        cursor = db.products.find(
            {"categoria": c, "destacado": True},
            PUBLIC_PROJECTION,
        ).limit(per_category)
        items = await cursor.to_list(per_category)
        if len(items) < per_category:
            need = per_category - len(items)
            existing_skus = {i["sku"] for i in items}
            cursor2 = db.products.find(
                {"categoria": c, "sku": {"$nin": list(existing_skus)}},
                PUBLIC_PROJECTION,
            ).sort([("stock", -1), ("imagen", -1)]).limit(need)
            extra = await cursor2.to_list(need)
            items = items + extra
        out[c] = items
    return {"sections": out}


@api_router.get("/search/suggest")
async def search_suggest(q: str = Query(..., min_length=1), limit: int = Query(6, ge=1, le=12)):
    qs = q.strip()
    if not qs:
        return {"items": []}
    rx = {"$regex": re.escape(qs), "$options": "i"}
    query = {"$or": [{"nombre": rx}, {"sku": rx}, {"marca": rx}]}
    cursor = db.products.find(
        query,
        {"_id": 0, "sku": 1, "nombre": 1, "precio": 1, "precio_oferta": 1, "categoria": 1, "marca": 1, "imagen": 1, "imagenes": 1},
    ).sort([("destacado", -1), ("stock", -1), ("nombre", 1)]).limit(limit)
    items = await cursor.to_list(limit)
    return {"items": items, "query": qs}


@api_router.get("/categories")
async def categories():
    pipeline = [
        {"$group": {"_id": "$categoria", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    rows = await db.products.aggregate(pipeline).to_list(200)
    total = await db.products.count_documents({})
    return {
        "total": total,
        "categories": [{"name": r["_id"] or "General", "count": r["count"]} for r in rows],
    }


@api_router.get("/facets")
async def facets(
    categoria: Optional[str] = Query(None),
    subcategoria: Optional[str] = Query(None),
):
    """Returns available facets for filters: brands, colors, price range, subcategories."""
    base: dict = {}
    if categoria and categoria != "Todos":
        base["categoria"] = categoria
    if subcategoria:
        base["subcategoria"] = subcategoria

    brand_pipe = [
        {"$match": {**base, "marca": {"$nin": ["", None]}}},
        {"$group": {"_id": "$marca", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 50},
    ]
    color_pipe = [
        {"$match": {**base, "color": {"$nin": ["", None]}}},
        {"$group": {"_id": "$color", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 50},
    ]
    sub_pipe = [
        {"$match": {**base, "subcategoria": {"$nin": ["", None]}}},
        {"$group": {"_id": "$subcategoria", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 30},
    ]
    price_pipe = [
        {"$match": {**base, "precio": {"$gt": 0}}},
        {"$group": {"_id": None, "min": {"$min": "$precio"}, "max": {"$max": "$precio"}}},
    ]
    brands = await db.products.aggregate(brand_pipe).to_list(50)
    colors = await db.products.aggregate(color_pipe).to_list(50)
    subs = await db.products.aggregate(sub_pipe).to_list(30)
    pr = await db.products.aggregate(price_pipe).to_list(1)

    return {
        "brands": [{"name": b["_id"], "count": b["count"]} for b in brands],
        "colors": [{"name": c["_id"], "count": c["count"]} for c in colors],
        "subcategorias": [{"name": s["_id"], "count": s["count"]} for s in subs],
        "price": {
            "min": (pr[0]["min"] if pr else 0) or 0,
            "max": (pr[0]["max"] if pr else 0) or 0,
        },
    }


# =========================================================
# Admin endpoints
# =========================================================

@api_router.post("/admin/login")
async def admin_login(body: LoginBody):
    if not ADMIN_PASSWORD:
        raise HTTPException(500, "Admin no configurado")
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(401, "Contraseña incorrecta")
    return {"token": ADMIN_PASSWORD}


@api_router.post("/admin/verify")
async def admin_verify(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    return {"ok": True}


@api_router.post("/admin/csv-upload")
async def upload_csv(
    file: UploadFile = File(...),
    mode: str = Query("upsert"),
    x_admin_token: Optional[str] = Header(None),
):
    _require_admin(x_admin_token)
    raw = (await file.read()).decode("utf-8", errors="ignore")
    rows = list(_parse_csv_rows(raw))
    if not rows:
        raise HTTPException(400, "El CSV no contiene filas válidas")

    if mode == "replace":
        await db.products.delete_many({})

    ops_inserted = 0
    ops_updated = 0
    for p in rows:
        res = await db.products.update_one(
            {"sku": p["sku"]}, {"$set": p}, upsert=True,
        )
        if res.upserted_id:
            ops_inserted += 1
        elif res.modified_count:
            ops_updated += 1

    total = await db.products.count_documents({})
    return {
        "received": len(rows),
        "inserted": ops_inserted,
        "updated": ops_updated,
        "total_in_db": total,
        "mode": mode,
    }


@api_router.put("/admin/products/{sku}")
async def update_product(
    sku: str, body: ProductUpdate, x_admin_token: Optional[str] = Header(None)
):
    _require_admin(x_admin_token)
    patch = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not patch:
        raise HTTPException(400, "Sin cambios")
    if "imagenes" in patch:
        patch["imagen"] = patch["imagenes"][0] if patch["imagenes"] else ""
    elif "imagen" in patch:
        cur = await db.products.find_one({"sku": sku}, {"imagenes": 1})
        cur_arr = (cur or {}).get("imagenes") or []
        if cur_arr:
            cur_arr[0] = patch["imagen"]
        else:
            cur_arr = [patch["imagen"]] if patch["imagen"] else []
        patch["imagenes"] = cur_arr
    if "nombre" in patch:
        patch["nombre"] = _clean_name(patch["nombre"])
    if "precio_oferta" in patch and (patch["precio_oferta"] is None or patch["precio_oferta"] < 0):
        patch["precio_oferta"] = 0
    patch["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.products.update_one({"sku": sku}, {"$set": patch})
    if res.matched_count == 0:
        raise HTTPException(404, "Producto no encontrado")
    doc = await db.products.find_one({"sku": sku}, PUBLIC_PROJECTION)
    return doc


@api_router.post("/admin/products/{sku}/images")
async def add_image(sku: str, body: ImageOp, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(400, "URL requerida")
    doc = await db.products.find_one({"sku": sku}, {"imagenes": 1})
    if not doc:
        raise HTTPException(404, "Producto no encontrado")
    arr = list(doc.get("imagenes") or [])
    if body.index is not None and 0 <= body.index < len(arr):
        arr[body.index] = url
    else:
        arr.append(url)
    await db.products.update_one(
        {"sku": sku},
        {"$set": {
            "imagenes": arr,
            "imagen": arr[0] if arr else "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    updated = await db.products.find_one({"sku": sku}, PUBLIC_PROJECTION)
    return updated


@api_router.delete("/admin/products/{sku}/images/{index}")
async def remove_image(sku: str, index: int, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    doc = await db.products.find_one({"sku": sku}, {"imagenes": 1})
    if not doc:
        raise HTTPException(404, "Producto no encontrado")
    arr = list(doc.get("imagenes") or [])
    if not (0 <= index < len(arr)):
        raise HTTPException(400, "Índice fuera de rango")
    arr.pop(index)
    await db.products.update_one(
        {"sku": sku},
        {"$set": {
            "imagenes": arr,
            "imagen": arr[0] if arr else "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    updated = await db.products.find_one({"sku": sku}, PUBLIC_PROJECTION)
    return updated


@api_router.post("/admin/clean-titles")
async def clean_titles(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.products.find({}, {"_id": 1, "nombre": 1})
    touched = 0
    sample_before, sample_after = [], []
    async for doc in cursor:
        old = doc.get("nombre") or ""
        new = _clean_name(old)
        if new and new != old:
            await db.products.update_one(
                {"_id": doc["_id"]},
                {"$set": {"nombre": new, "updated_at": now}},
            )
            if touched < 5:
                sample_before.append(old)
                sample_after.append(new)
            touched += 1
    return {"updated": touched, "sample_before": sample_before, "sample_after": sample_after}


@api_router.post("/admin/extract-attributes")
async def extract_attributes(x_admin_token: Optional[str] = Header(None)):
    """Auto-detect brand & color from product names for products that don't have them."""
    _require_admin(x_admin_token)
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.products.find({}, {"_id": 1, "nombre": 1, "marca": 1, "color": 1})
    touched = 0
    async for doc in cursor:
        name = doc.get("nombre") or ""
        patch = {}
        if not (doc.get("marca") or "").strip():
            b = _detect_brand(name)
            if b:
                patch["marca"] = b
        if not (doc.get("color") or "").strip():
            c = _detect_color(name)
            if c:
                patch["color"] = c
        if patch:
            patch["updated_at"] = now
            await db.products.update_one({"_id": doc["_id"]}, {"$set": patch})
            touched += 1
    return {"updated": touched}


@api_router.post("/admin/products")
async def create_product(body: Product, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    exists = await db.products.find_one({"sku": body.sku}, {"_id": 1})
    if exists:
        raise HTTPException(409, "Ya existe un producto con ese SKU")
    doc = body.model_dump()
    doc["categoria"] = _clean_category(doc.get("categoria", ""))
    doc["nombre"] = _clean_name(doc.get("nombre", ""))
    if not (doc.get("marca") or "").strip():
        doc["marca"] = _detect_brand(doc["nombre"])
    if not (doc.get("color") or "").strip():
        doc["color"] = _detect_color(doc["nombre"])
    if doc.get("imagen") and not doc.get("imagenes"):
        doc["imagenes"] = [doc["imagen"]]
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.delete("/admin/products/{sku}")
async def delete_product(sku: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    res = await db.products.delete_one({"sku": sku})
    if res.deleted_count == 0:
        raise HTTPException(404, "Producto no encontrado")
    return {"ok": True}


_KEYWORDS = {
    "Marroquinería": ["mochila", "cartera", "bolso", "bolsito", "billetera", "morral", "rinonera", "portanotebook", "cartuchera", " tula", "neceser", "maletin", "bandolera", "valija", "estuche"],
    "Juguetería": ["roller", "drone", "lego", "barbie", "baby", "muneco", "peluche", "pelota", "juguete", "puzzle", "rompecabezas", "bloque", "robot", "sonic", "paw patrol", "disney", "marvel", "pokemon", "hot wheels", "play-doh", "playdoh", "slime", "dinosaurio", "cars", "frozen", "spider", "batman", "superman", "hulk", "avengers", "minecraft", "roblox", "jenga", "potty", "nenuco", "cry babies", "magic tears", "monopatin", "triciclo", "patineta", "skateboard", "kinetic sand"],
    "Regalería": ["vela", "velon", "portaretrato", "portarretrato", "marco para foto", "taza", "mate", "termo", "adorno", "estatuilla", "llavero", "souvenir", "figurin", "cofre", "cajita", "joyero", "espejo", "bandeja", "regalo", "candelabro", "incienso", "decorativo", "globo ", "globos"],
    "Tecno": ["auricular", "audifono", "parlante", "speaker", "cargador", "cable usb", "usb", "tipo c", "lightning", "bateria portatil", "power bank", "powerbank", "mouse", "teclado", "pendrive", "memoria", "tarjeta sd", "sd card", "microsd", "headset", "webcam", "soporte celular", "selfie stick", "gamepad", "joystick", "smartwatch", "tablet", "notebook", "laptop", "monitor", "router", "wifi", "bluetooth"],
}
_DEFAULT_CAT = "Librería"


def _classify_name(name: str) -> str:
    n = _strip_accents(name)
    for cat, kws in _KEYWORDS.items():
        for k in kws:
            if k in n:
                return cat
    return _DEFAULT_CAT


SUBCATEGORY_MAP = {
    "Librería": [
        ("Estudio", ["escolar", "cuaderno", "repuesto", "lapiz", "goma", "carpeta", "regla", "compas", "transportador"]),
        ("Oficina", ["abrochadora", "folio", "bibliorato", "boligrafo", "resma", "calculadora", "perforadora", "engrampadora", "broche"]),
        ("Creatividad", ["tempera", "pincel", "bastidor", "acrilico", "dibujo", "tecnica", "oleo", "acuarela", "pastel", "carbonilla"]),
        ("Organización", ["agenda", "anotador", "post-it", "clasificador", "canopla", "organizador", "calendario"]),
        ("Kits", ["set", "pack", "kit escolar", "combo"]),
    ],
    "Juguetería": [
        ("Juegos de Mesa", ["mesa", "cartas", "mazo", "ludo", "ajedrez", "puzzle", "rompecabezas", "domino", "uno", "monopoly"]),
        ("Muñecos y Figuras", ["muneca", "figura", "barbie", "marvel", "peluche", "accion", "disney", "spider", "batman", "frozen"]),
        ("Didácticos", ["bloque", "encastre", "masa", "rasti", "lego", "madera", "aprendizaje", "didactic", "magnet"]),
        ("Aire Libre y Rodados", ["pelota", "inflable", "pileta", "triciclo", "monopatin", "andarin", "patineta", "skate", "bici"]),
        ("Primera Infancia", ["sonajero", "movil", "mordillo", "fisher-price", "bebe", "baby"]),
    ],
    "Marroquinería": [
        ("Mochilas", ["mochila", "espalda", "mochila carro", "jardin"]),
        ("Carteras y Bolsos", ["cartera", "bolso", "bandolera", "shopping bag", "shopper"]),
        ("Riñoneras y Neceser", ["rinonera", "neceser", "cartuchera", "porta cosmetico", "estuche"]),
        ("Valijas y Viaje", ["valija", "carry-on", "almohadilla de viaje", "identificador"]),
        ("Accesorios", ["billetera", "monedero", "llavero", "cinturon"]),
    ],
    "Tecno": [
        ("Audio", ["auricular", "parlante", "bluetooth", "headphone", "audifono"]),
        ("Computación", ["mouse", "teclado", "pad", "webcam", "monitor", "notebook", "laptop"]),
        ("Gaming", ["gamer", "silla gamer", "joystick", "consola", "gamepad"]),
        ("Energía", ["pila", "cargador", "cable usb", "fuente", "powerbank", "power bank", "bateria"]),
        ("Accesorios Celular", ["funda", "vidrio templado", "soporte celular", "selfie"]),
    ],
    "Regalería": [
        ("Hogar y Bazar", ["taza", "vaso", "plato", "cubierto", "botella", "hermetico"]),
        ("Decoración", ["cuadro", "vela", "difusor", "reloj", "portarretrato", "portaretrato", "adorno"]),
        ("Mates y Termos", ["mate", "termo", "bombilla", "yerbera", "set matero"]),
        ("Regalos", ["peluche", "caja de regalo", "tarjeta", "souvenir", "globo"]),
    ],
}


def _classify_subcategory(name: str, categoria: str) -> str:
    if categoria not in SUBCATEGORY_MAP:
        return ""
    n = _strip_accents(name)
    for sub, kws in SUBCATEGORY_MAP[categoria]:
        for k in kws:
            if k in n:
                return sub
    return ""


@api_router.post("/admin/classify-subcategories")
async def classify_subcategories(x_admin_token: Optional[str] = Header(None)):
    """Auto-classify subcategoria for every product based on its name + categoria."""
    _require_admin(x_admin_token)
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.products.find({}, {"_id": 1, "nombre": 1, "categoria": 1})
    counts: dict = {}
    touched = 0
    async for doc in cursor:
        sub = _classify_subcategory(doc.get("nombre") or "", doc.get("categoria") or "")
        if sub:
            await db.products.update_one(
                {"_id": doc["_id"]}, {"$set": {"subcategoria": sub, "updated_at": now}}
            )
            counts[sub] = counts.get(sub, 0) + 1
            touched += 1
    return {"updated": touched, "counts": counts}


class ReclassifyBody(BaseModel):
    scope: str = "general_only"
    apply: bool = False


@api_router.post("/admin/reclassify")
async def reclassify(body: ReclassifyBody, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    query = {} if body.scope == "all" else {"categoria": {"$in": ["General", "º", "-", ""]}}
    cursor = db.products.find(query, {"_id": 1, "nombre": 1, "categoria": 1})
    counts = {"Marroquinería": 0, "Librería": 0, "Juguetería": 0, "Regalería": 0, "Tecno": 0}
    touched = 0
    async for doc in cursor:
        new_cat = _classify_name(doc.get("nombre", ""))
        counts[new_cat] = counts.get(new_cat, 0) + 1
        touched += 1
        if body.apply:
            await db.products.update_one(
                {"_id": doc["_id"]}, {"$set": {"categoria": new_cat}}
            )
    return {"scope": body.scope, "applied": body.apply, "scanned": touched, "counts": counts}


@api_router.get("/admin/stats")
async def admin_stats(x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    total = await db.products.count_documents({})
    in_stock = await db.products.count_documents({"stock": {"$gt": 0}})
    missing_image = await db.products.count_documents({"imagen": ""})
    on_sale = await db.products.count_documents({"precio_oferta": {"$gt": 0}})
    featured_count = await db.products.count_documents({"destacado": True})
    return {
        "total": total,
        "in_stock": in_stock,
        "missing_image": missing_image,
        "on_sale": on_sale,
        "featured": featured_count,
    }


# =========================================================
# Kits (curated bundles)
# =========================================================

class Kit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"kit_{int(datetime.now(timezone.utc).timestamp() * 1000)}")
    nombre: str
    descripcion: Optional[str] = ""
    precio: float
    skus: List[str] = Field(default_factory=list)
    imagen: Optional[str] = ""
    activo: bool = True
    orden: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KitUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    skus: Optional[List[str]] = None
    imagen: Optional[str] = None
    activo: Optional[bool] = None
    orden: Optional[int] = None


async def _enrich_kit(kit: dict) -> dict:
    skus = kit.get("skus") or []
    cursor = db.products.find(
        {"sku": {"$in": skus}},
        {"_id": 0, "sku": 1, "nombre": 1, "imagen": 1, "imagenes": 1, "precio": 1, "precio_oferta": 1},
    )
    docs = await cursor.to_list(len(skus))
    by_sku = {d["sku"]: d for d in docs}
    products_in_order = [by_sku[s] for s in skus if s in by_sku]
    kit["productos"] = products_in_order
    kit["precio_original"] = sum(
        (p.get("precio_oferta") or 0) > 0 and p["precio_oferta"] or (p.get("precio") or 0)
        for p in products_in_order
    )
    return kit


@api_router.get("/kits")
async def list_kits(only_active: bool = Query(True)):
    q = {"activo": True} if only_active else {}
    cursor = db.kits.find(q, {"_id": 0}).sort([("orden", 1), ("created_at", -1)])
    items = await cursor.to_list(100)
    items = [await _enrich_kit(k) for k in items]
    return {"items": items}


@api_router.get("/kits/{kit_id}")
async def get_kit(kit_id: str):
    doc = await db.kits.find_one({"id": kit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Kit no encontrado")
    return await _enrich_kit(doc)


@api_router.post("/admin/kits")
async def create_kit(body: Kit, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    doc = body.model_dump()
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = doc["created_at"]
    await db.kits.insert_one(doc)
    doc.pop("_id", None)
    return await _enrich_kit(doc)


@api_router.put("/admin/kits/{kit_id}")
async def update_kit(
    kit_id: str, body: KitUpdate, x_admin_token: Optional[str] = Header(None)
):
    _require_admin(x_admin_token)
    patch = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not patch:
        raise HTTPException(400, "Sin cambios")
    patch["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.kits.update_one({"id": kit_id}, {"$set": patch})
    if res.matched_count == 0:
        raise HTTPException(404, "Kit no encontrado")
    doc = await db.kits.find_one({"id": kit_id}, {"_id": 0})
    return await _enrich_kit(doc)


@api_router.delete("/admin/kits/{kit_id}")
async def delete_kit(kit_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    res = await db.kits.delete_one({"id": kit_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "Kit no encontrado")
    return {"ok": True}


# =========================================================
# Store configuration (footer, contact info, map)
# =========================================================

DEFAULT_STORE_CONFIG = {
    "about_text": "Nexo Store · Conectamos lo que necesitás. Más de 8.000 artículos curados.",
    "phone": "+54 9 3465 53-8232",
    "email": "contacto@nexostore.com.ar",
    "address": "Alcorta, Santa Fe",
    "maps_url": "https://www.google.com/maps?q=Alcorta+Santa+Fe&output=embed",
    "instagram_url": "https://instagram.com/nexostore",
    "facebook_url": "https://facebook.com/NexoStore",
    "search_filters": ["Librería", "Marroquinería", "Juguetería", "Regalería", "Tecno"],
}


class StoreConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    about_text: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    maps_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    search_filters: Optional[List[str]] = None


@api_router.get("/store-config")
async def get_store_config():
    doc = await db.store_config.find_one({"_id": "default"}, {"_id": 0})
    if not doc:
        return DEFAULT_STORE_CONFIG
    # Merge defaults for any missing keys
    out = {**DEFAULT_STORE_CONFIG, **doc}
    return out


@api_router.put("/admin/store-config")
async def update_store_config(
    body: StoreConfig, x_admin_token: Optional[str] = Header(None)
):
    _require_admin(x_admin_token)
    patch = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not patch:
        raise HTTPException(400, "Sin cambios")
    patch["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.store_config.update_one(
        {"_id": "default"}, {"$set": patch}, upsert=True
    )
    doc = await db.store_config.find_one({"_id": "default"}, {"_id": 0})
    return {**DEFAULT_STORE_CONFIG, **(doc or {})}


# =========================================================
# Startup
# =========================================================

@app.on_event("startup")
async def startup():
    await db.products.create_index("sku", unique=True)
    await db.products.create_index("categoria")
    await db.products.create_index("destacado")
    await db.products.create_index("precio_oferta")
    await db.products.create_index("marca")
    await db.products.create_index("color")
    await db.products.create_index([("nombre", "text")])

    count = await db.products.count_documents({})
    seed_path = ROOT_DIR / "initial_catalog.csv"
    if count == 0 and seed_path.exists():
        try:
            raw = seed_path.read_text(encoding="utf-8")
            rows = list(_parse_csv_rows(raw))
            if rows:
                for p in rows:
                    try:
                        await db.products.update_one(
                            {"sku": p["sku"]}, {"$set": p}, upsert=True
                        )
                    except Exception:
                        pass
            logging.info(f"[Nexo Store] Seeded {len(rows)} products")
        except Exception as e:
            logging.warning(f"[Nexo Store] Seed failed: {e}")

    cursor = db.products.find(
        {"$or": [
            {"imagenes": {"$exists": False}},
            {"precio_oferta": {"$exists": False}},
            {"destacado": {"$exists": False}},
            {"marca": {"$exists": False}},
            {"color": {"$exists": False}},
            {"subcategoria": {"$exists": False}},
        ]},
        {"_id": 1, "imagen": 1, "imagenes": 1, "nombre": 1, "marca": 1, "color": 1},
    )
    n = 0
    async for doc in cursor:
        img = doc.get("imagen") or ""
        imgs = doc.get("imagenes")
        if imgs is None:
            imgs = [img] if img else []
        name = doc.get("nombre") or ""
        marca = doc.get("marca") or _detect_brand(name)
        color = doc.get("color") or _detect_color(name)
        await db.products.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "imagenes": imgs,
                "precio_oferta": 0 if doc.get("precio_oferta") is None else doc.get("precio_oferta", 0),
                "destacado": bool(doc.get("destacado") or False),
                "marca": marca,
                "color": color,
                "subcategoria": doc.get("subcategoria", ""),
            }},
        )
        n += 1
    if n:
        logging.info(f"[Nexo Store] Schema backfill: {n} products")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# Mount router + CORS
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    try:
        uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
    except Exception as e:
        print(f"ERROR EN PRODUCCIÓN: {e}", flush=True)
        raise
