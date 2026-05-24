# Nexo Store — Tienda Online (PRD)

## Problema original
Importar repo libreriadmasd-cmyk/12 y profesionalizar la tienda al estilo tomy.com.ar:
identidad visual con marca de agua, organización por categorías con íconos,
gestión de ofertas, panel admin ultra-simple, filtros inteligentes auto-extraídos,
Cloudinary unsigned upload, Mongo persistencia, WhatsApp con contexto.

## Stack
React 19 + craco + Tailwind · FastAPI · MongoDB · Cloudinary

## Personas
- **Cliente final** (móvil/desktop): explora catálogo, filtra, agrega a bolsa,
  consulta por WhatsApp.
- **Admin (papá del usuario)**: gestiona stock/precio/ofertas/fotos sin tocar links
  ni términos técnicos. Botones gigantes, español claro.

## Implementado (Apr 2026)
- ✅ Logo centrado en header + marca de agua repetida 5-6% opacidad fija full-screen
- ✅ TopBar "Funes | Rosario y alrededores"
- ✅ 5 categorías con íconos (Marroquinería 🎒, Librería 📚, Juguetería 🧸, Regalería 🎁, Tecno 📱)
- ✅ Vitrinas Home: 3 productos destacados por categoría + chips de subcategorías
- ✅ Banner "🔥 Ofertas activas" arriba de Home (auto-listadas por precio_oferta>0)
- ✅ Subcategorías auto-clasificadas con palabras clave del usuario (3490 productos clasificados)
  - Librería: Estudio (655), Oficina (209), Creatividad (94), Organización (209), Kits (216)
  - Juguetería: Juegos de Mesa, Muñecos, Didácticos, Aire Libre, Primera Infancia
  - Marroquinería: Mochilas (517), Carteras (269), Riñoneras (155), Valijas, Accesorios
  - Tecno: Audio, Computación, Gaming, Energía, Accesorios Celular
  - Regalería: Hogar/Bazar, Decoración, Mates/Termos, Regalos
- ✅ Sidebar filtros: Subcategoría · Marca · Color (27 colores) · Rango Precio · Solo ofertas
- ✅ Bug crítico fix: filtro precio min/max ahora usa precio efectivo (oferta si existe, else normal) vía $expr
- ✅ ProductCard: precio normal tachado + precio oferta en rojo + badge "-N% OFF"
- ✅ Breadcrumbs Inicio > Categoría > Subcategoría
- ✅ Admin: tabla con columnas Foto/Producto/Categoría/Precio Normal/Precio Oferta/Stock/⭐Destacar
- ✅ Admin: botón gigante "📷 Cambiar/Agregar Foto" en GalleryModal con Cloudinary unsigned upload
- ✅ Admin: switch "★ Destacar" 1-click + edición precio_oferta inline
- ✅ WhatsApp flotante con contexto: en PDP envía nombre + SKU + precio del producto
- ✅ Buscador predictivo + limpieza automática títulos (Title Case, quita códigos internos)
- ✅ MongoDB indexado en sku/categoria/destacado/precio_oferta/marca/color
- ✅ 8142 productos seedeados al iniciar desde initial_catalog.csv

## Endpoints clave
- GET /api/categories · /api/featured · /api/facets?categoria=X
- GET /api/products con filtros: categoria, subcategoria, marca, color, min_price, max_price, on_sale, q, sort
- POST /api/admin/login · /api/admin/extract-attributes · /api/admin/classify-subcategories · /api/admin/reclassify
- PUT /api/admin/products/{sku} (precio_oferta, destacado, etc.)
- POST/DELETE /api/admin/products/{sku}/images

## Backlog (P1)
- Hover-menu desplegable con subcategorías + emojis de colores (🟪🟦🟧🟩🟨)
- Vista de página dedicada por subcategoría con URL parametrizada (`/c/Librería/Estudio`)
- Importador de catálogo desde Cloudinary URL pattern automático

## Observación deployment
El preview URL devuelve cache stale (4351 prods, sin Tecno). El código en /app es correcto
(8142 prods, 5 cats). Usuario debe presionar "Stop → Start preview" en UI de Emergent
para regenerar el ingress.
