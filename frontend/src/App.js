import { useEffect, useState } from "react";
import { Routes, Route, NavLink, useNavigate, useParams } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Truck,
  Search,
  X,
  MessageCircle,
  ShoppingBag,
  Play,
} from "lucide-react";
import { buildWhatsAppProductUrl, buildWhatsAppUrl } from "./lib/whatsapp";
import { cldHero, cldThumb } from "./lib/cloudinary";
import {
  adminCreateKit,
  adminDeleteKit,
  adminLogin,
  adminUpdateKit,
  adminUpdateProduct,
  adminUpdateStoreConfig,
  adminVerify,
  fetchCategories,
  fetchFacets,
  fetchFeatured,
  fetchKits,
  fetchProducts,
  fetchProduct,
  fetchStoreConfig,
} from "./lib/api";

const formatCurrency = (value) =>
  new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(value || 0);

const heroCategories = [
  "Librería",
  "Marroquinería",
  "Juguetería",
  "Regalería",
  "Tecno",
];

function App() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_top_left,_rgba(46,196,182,0.16),transparent_28%),linear-gradient(180deg,#f8fafc_0%,#ffffff_100%)] text-slate-900">
      <Header />
      <div className="mx-auto max-w-7xl px-4 pb-24 pt-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/categoria/:categoria" element={<CategoryPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
      <Footer />
      <WhatsAppFab />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/70 bg-white/95 backdrop-blur-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <NavLink to="/" className="inline-flex items-center gap-3 text-lg font-extrabold text-brand-blue">
          <div className="flex h-11 w-11 items-center justify-center rounded-3xl bg-brand-teal text-white shadow-lg shadow-brand-teal/20">
            N
          </div>
          <span>Nexo Store</span>
        </NavLink>
        <nav className="flex items-center gap-4 text-sm font-semibold text-slate-600">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? "text-brand-blue" : "transition hover:text-brand-blue"
            }
          >
            Inicio
          </NavLink>
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              isActive ? "text-brand-blue" : "transition hover:text-brand-blue"
            }
          >
            Panel
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

function HomePage() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [kits, setKits] = useState([]);
  const [storeConfig, setStoreConfig] = useState(null);
  const [status, setStatus] = useState("Cargando...");

  useEffect(() => {
    const load = async () => {
      try {
        const [catData, featuredData, kitData, configData] = await Promise.all([
          fetchCategories(),
          fetchFeatured(),
          fetchKits(),
          fetchStoreConfig(),
        ]);
        setCategories(catData.categories || []);
        setFeatured(featuredData);
        setKits(kitData.items || []);
        setStoreConfig(configData);
      } catch (error) {
        setStatus(error.message || "Hubo un error cargando la tienda.");
      }
    };
    load();
  }, []);

  const heroCategory = categories.find((cat) => heroCategories.includes(cat.name));

  return (
    <div className="space-y-14">
      <section className="relative overflow-hidden rounded-[2rem] border border-slate-200/70 bg-white/80 p-8 shadow-2xl shadow-slate-200/80 sm:p-12">
        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-brand-teal/20 to-transparent" />
        <div className="relative grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-teal/10 px-4 py-2 text-sm font-semibold text-brand-teal shadow-sm shadow-brand-teal/10">
              <Sparkles className="h-4 w-4" />
              Nexo Store renovada: diseño cuidado, soluciones rápidas y stock verificado.
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">
                Librería • Marroquinería • Juguetería
              </p>
              <h1 className="mt-4 max-w-3xl text-4xl font-black leading-tight text-slate-950 sm:text-5xl">
                Conectamos lo que necesitás con experiencias más claras y prácticas.
              </h1>
            </div>
            <p className="max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
              Descubrí productos curados, kits imperdibles y respuestas inmediatas por WhatsApp.
            </p>
            <div className="flex flex-wrap gap-4">
              <button
                type="button"
                onClick={() => navigate(`/categoria/${encodeURIComponent(heroCategory?.name || "Librería")}`)}
                className="btn-primary"
              >
                Lo quiero
                <ArrowRight className="ml-2 h-4 w-4" />
              </button>
              <a
                href={buildWhatsAppUrl([], 0)}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary"
              >
                Consultar ahora
              </a>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {heroCategories.slice(0, 3).map((category) => (
                <button
                  key={category}
                  type="button"
                  onClick={() => navigate(`/categoria/${encodeURIComponent(category)}`)}
                  className="rounded-3xl border border-slate-200/80 bg-slate-50 px-5 py-4 text-left transition hover:border-brand-teal/80 hover:bg-white"
                >
                  <p className="text-sm uppercase tracking-[0.3em] text-brand-blue/70">Categoría</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{category}</p>
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-6 rounded-[2rem] border border-slate-200/70 bg-brand-blue/5 p-6 shadow-xl shadow-brand-blue/10 sm:p-10">
            <div className="rounded-3xl bg-gradient-to-br from-brand-blue to-brand-teal p-6 text-white shadow-lg shadow-brand-blue/20">
              <p className="text-sm uppercase tracking-[0.35em] text-brand-teal-100/90">Recomendado</p>
              <h2 className="mt-4 text-3xl font-bold">Nexos Recomendados</h2>
              <p className="mt-3 text-sm leading-6 text-brand-teal-100/90">
                Cada sección está pensada para que encuentres lo mejor de cada categoría con facilidad.
              </p>
            </div>
            <div className="grid gap-4">
              {(categories.slice(0, 3) || []).map((category) => (
                <button
                  key={category.name}
                  type="button"
                  onClick={() => navigate(`/categoria/${encodeURIComponent(category.name)}`)}
                  className="rounded-3xl border border-slate-200/80 bg-white px-5 py-4 text-left transition hover:border-brand-blue/80"
                >
                  <p className="text-sm font-semibold text-slate-800">{category.name}</p>
                  <p className="mt-2 text-sm text-slate-500">{category.count} productos</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Nexos Recomendados</p>
            <h2 className="text-3xl font-bold text-slate-950">Selección destacada</h2>
          </div>
          <p className="max-w-xl text-sm leading-6 text-slate-600">
            Productos destacados por categoría, verificados para que puedas comprar con confianza.
          </p>
        </div>
        {featured ? (
          <div className="grid gap-8">
            {Object.entries(featured.sections || {}).slice(0, 3).map(([section, items]) => (
              <div key={section} className="space-y-4 rounded-[2rem] border border-slate-200/70 bg-white/85 p-6 shadow-sm shadow-slate-200/50">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">{section}</p>
                    <h3 className="mt-2 text-2xl font-semibold text-slate-950">Lo mejor en {section}</h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/categoria/${encodeURIComponent(section)}`)}
                    className="btn-secondary"
                  >
                    Ver todos
                  </button>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  {items.map((item) => (
                    <article key={item.sku} className="overflow-hidden rounded-3xl border border-slate-200/80 bg-slate-50 shadow-sm">
                      <img
                        src={cldThumb(item.imagen)}
                        alt={item.nombre}
                        className="h-56 w-full object-cover"
                      />
                      <div className="p-5">
                        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-brand-blue/70">{item.marca || item.categoria}</p>
                        <h4 className="mt-3 text-lg font-semibold text-slate-950">{item.nombre}</h4>
                        <div className="mt-4 flex items-center gap-3">
                          <span className="text-xl font-bold text-brand-blue">{formatCurrency(item.precio_oferta || item.precio)}</span>
                          {item.precio_oferta ? <span className="text-sm text-slate-500 line-through">{formatCurrency(item.precio)}</span> : null}
                        </div>
                        <a
                          href={buildWhatsAppProductUrl(item)}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-5 inline-flex w-full items-center justify-center rounded-full bg-brand-blue px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-blueDark"
                        >
                          Consultar ahora
                        </a>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-slate-200/80 bg-white/80 p-8 text-slate-700 shadow-sm">{status}</div>
        )}
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Kits Imperdibles</p>
            <h2 className="text-3xl font-bold text-slate-950">Armá tu combo ideal</h2>
          </div>
          <p className="max-w-xl text-sm leading-6 text-slate-600">
            Seleccionamos kits con precio especial para que compres rápido y sin dudas.
          </p>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {(kits.length > 0 ? kits : Array.from({ length: 3 })).map((kit, index) => (
            <div key={kit?.id || index} className="group rounded-[2rem] border border-slate-200/70 bg-white/95 p-6 shadow-lg shadow-slate-200/40 transition hover:-translate-y-1">
              <div className="relative overflow-hidden rounded-3xl bg-slate-100">
                <img
                  src={cldHero(kit?.imagen || `https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80`)}
                  alt={kit?.nombre || "Kit Nexo"}
                  className="h-56 w-full object-cover"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 to-transparent p-4">
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-white">Kit</p>
                </div>
              </div>
              <div className="mt-6 space-y-4">
                <div>
                  <h3 className="text-xl font-semibold text-slate-950">{kit?.nombre || "Cargando kit"}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{kit?.descripcion || "Ejemplo de kit para tu próxima compra"}</p>
                </div>
                <div className="flex items-center gap-3 text-slate-700">
                  <span className="text-2xl font-bold text-brand-blue">{formatCurrency(kit?.precio || 0)}</span>
                  {kit?.precio_original > kit?.precio ? (
                    <span className="text-sm text-slate-500 line-through">{formatCurrency(kit?.precio_original)}</span>
                  ) : null}
                </div>
                <div className="grid gap-2">
                  <span className="rounded-full bg-brand-teal/10 px-3 py-2 text-sm font-semibold text-brand-teal">
                    {kit?.productos?.length || 0} productos incluidos
                  </span>
                  <a
                    href={buildWhatsAppMessageForKit(kit)}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-primary"
                  >
                    Lo quiero
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 rounded-[2rem] border border-slate-200/70 bg-white/85 p-8 sm:grid-cols-4 sm:gap-6">
        {[
          { icon: Truck, label: "Envíos rápidos", detail: "Retiro y reparto ágil en Rosario" },
          { icon: ShieldCheck, label: "Compra segura", detail: "Pagos claros y atención personalizada" },
          { icon: CheckCircle2, label: "Stock confiable", detail: "Solo productos listos para retirar" },
          { icon: Sparkles, label: "Atención por WhatsApp", detail: "Consultas directas y respuestas inmediatas" },
        ].map((item) => (
          <div key={item.label} className="rounded-3xl border border-slate-200/80 bg-slate-50 p-6 shadow-sm">
            <item.icon className="h-6 w-6 text-brand-blue" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">{item.label}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.detail}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-8 rounded-[2rem] border border-slate-200/70 bg-brand-blue/5 p-8 sm:grid-cols-[1.5fr_1fr]">
        <div className="space-y-4">
          <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Nexo Store</p>
          <h2 className="text-3xl font-bold text-slate-950">Listo para tu próxima compra</h2>
          <p className="max-w-xl text-base leading-8 text-slate-700">
            {storeConfig?.about_text || "Un lugar pensado para conectar tus necesidades con la mejor selección de productos."}
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Teléfono</p>
              <p className="mt-2 text-lg font-semibold text-slate-950">{storeConfig?.phone || "+54 9 3465 53-8232"}</p>
            </div>
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Email</p>
              <p className="mt-2 text-lg font-semibold text-slate-950">{storeConfig?.email || "contacto@nexostore.com.ar"}</p>
            </div>
          </div>
        </div>
        <div className="rounded-[2rem] bg-white p-6 shadow-lg shadow-slate-200/50">
          <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Ubicación</p>
          <h3 className="mt-3 text-xl font-semibold text-slate-950">Visitamos</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600">{storeConfig?.address || "Alcorta, Santa Fe"}</p>
          {storeConfig?.maps_url ? (
            <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
              <iframe
                title="Nexo Store ubicación"
                src={storeConfig.maps_url}
                className="h-64 w-full"
                loading="lazy"
              />
            </div>
          ) : (
            <div className="mt-5 rounded-3xl bg-slate-100 p-6 text-sm text-slate-600">Actualizá la URL de Google Maps desde el panel administrativo.</div>
          )}
        </div>
      </section>
    </div>
  );
}

function buildWhatsAppMessageForKit(kit) {
  const items = (kit?.productos || []).map((product) => ({
    nombre: product.nombre,
    sku: product.sku,
    precio: product.precio_oferta || product.precio,
    cantidad: 1,
  }));
  const total = items.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
  const textLines = ["Hola Nexo Store, quiero comprar este kit:", "", ...items.map((item, idx) => `${idx + 1}. ${item.nombre} (SKU ${item.sku}) — x${item.cantidad} — ${formatCurrency(item.precio)}`), "", `Total: ${formatCurrency(total)}`];
  return `https://wa.me/${process.env.REACT_APP_WHATSAPP_NUMBER || "5493465538232"}?text=${encodeURIComponent(textLines.join("\n"))}`;
}

function CategoryPage() {
  const { categoria } = useParams();
  const decodedCategory = decodeURIComponent(categoria || "");
  const [products, setProducts] = useState([]);
  const [facets, setFacets] = useState({ brands: [], colors: [] });
  const [searchText, setSearchText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBrand, setSelectedBrand] = useState("");
  const [selectedColor, setSelectedColor] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Cargando productos...");

  useEffect(() => {
    const loadFacets = async () => {
      try {
        const data = await fetchFacets({ categoria: decodedCategory });
        setFacets(data);
      } catch (error) {
        console.error(error);
      }
    };
    loadFacets();
  }, [decodedCategory]);

  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      try {
        const data = await fetchProducts({
          categoria: decodedCategory,
          q: searchQuery,
          marca: selectedBrand,
          color: selectedColor,
          min_price: minPrice ? Number(minPrice) : undefined,
          max_price: maxPrice ? Number(maxPrice) : undefined,
          limit: 48,
        });
        setProducts(data.items || []);
        setMessage(data.items?.length ? "" : "No encontramos productos para estos filtros.");
      } catch (error) {
        setMessage(error.message || "Error cargando productos.");
      } finally {
        setLoading(false);
      }
    };
    loadProducts();
  }, [decodedCategory, searchQuery, selectedBrand, selectedColor, minPrice, maxPrice]);

  const clearFilters = () => {
    setSelectedBrand("");
    setSelectedColor("");
    setMinPrice("");
    setMaxPrice("");
    setSearchText("");
    setSearchQuery("");
  };

  return (
    <div className="space-y-10">
      <section className="rounded-[2rem] border border-slate-200/70 bg-white/85 p-8 shadow-lg shadow-slate-200/40">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Categoría</p>
            <h1 className="mt-2 text-4xl font-bold text-slate-950">{decodedCategory}</h1>
          </div>
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                placeholder="Buscar dentro de la categoría"
                className="w-full rounded-full border border-slate-200 bg-white py-3 pl-11 pr-12 text-sm text-slate-900 shadow-sm focus:border-brand-blue focus:ring-brand-teal/30"
              />
              {searchText ? (
                <button
                  type="button"
                  onClick={() => {
                    setSearchText("");
                    setSearchQuery("");
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-slate-100 p-2 text-slate-500 transition hover:bg-slate-200"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => setSearchQuery(searchText)}
              className="btn-primary"
            >
              Buscar
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="space-y-6 rounded-[2rem] border border-slate-200/70 bg-white/85 p-6 shadow-sm shadow-slate-200/40">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Filtros</p>
            <p className="mt-2 text-sm text-slate-600">Seleccioná marca, color o rango de precios.</p>
          </div>
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-800">Marca</label>
              <select
                value={selectedBrand}
                onChange={(event) => setSelectedBrand(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              >
                <option value="">Todas</option>
                {facets.brands?.slice(0, 10).map((brand) => (
                  <option key={brand.name} value={brand.name}>{brand.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-800">Color</label>
              <select
                value={selectedColor}
                onChange={(event) => setSelectedColor(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              >
                <option value="">Todos</option>
                {facets.colors?.slice(0, 10).map((color) => (
                  <option key={color.name} value={color.name}>{color.name}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm font-semibold text-slate-800">Precio mínimo</label>
              <input
                type="number"
                value={minPrice}
                onChange={(event) => setMinPrice(event.target.value)}
                placeholder="0"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <label className="block text-sm font-semibold text-slate-800">Precio máximo</label>
              <input
                type="number"
                value={maxPrice}
                onChange={(event) => setMaxPrice(event.target.value)}
                placeholder="0"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
            </div>
          </div>
          <button type="button" onClick={clearFilters} className="btn-secondary w-full">
            Limpiar filtros
          </button>
        </aside>
        <div className="space-y-6">
          <div className="rounded-[2rem] border border-slate-200/70 bg-white/85 p-6 shadow-sm shadow-slate-200/40">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Resultados</p>
                <h2 className="mt-2 text-2xl font-bold text-slate-950">{decodedCategory}</h2>
              </div>
              <p className="text-sm text-slate-600">{products.length} productos disponibles</p>
            </div>
          </div>
          {loading ? (
            <div className="rounded-[2rem] border border-slate-200/70 bg-white/85 p-10 text-center text-slate-600 shadow-sm shadow-slate-200/40">
              Cargando productos...
            </div>
          ) : products.length === 0 ? (
            <div className="rounded-[2rem] border border-slate-200/70 bg-white/85 p-10 text-center text-slate-600 shadow-sm shadow-slate-200/40">{message}</div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {products.map((product) => (
                <article key={product.sku} className="overflow-hidden rounded-[2rem] border border-slate-200/70 bg-white/90 shadow-sm transition hover:-translate-y-0.5">
                  <div className="overflow-hidden rounded-t-[1.75rem] bg-slate-100">
                    <img
                      src={cldThumb(product.imagen)}
                      alt={product.nombre}
                      className="h-64 w-full object-cover"
                    />
                  </div>
                  <div className="space-y-4 p-5">
                    <div className="flex items-center justify-between gap-3">
                      <span className="rounded-full bg-brand-teal/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-brand-teal">{product.categoria}</span>
                      {product.precio_oferta ? (
                        <span className="rounded-full bg-brand-blue/10 px-3 py-1 text-xs font-semibold text-brand-blue">Oferta</span>
                      ) : null}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-950">{product.nombre}</h3>
                      <p className="mt-2 text-sm text-slate-600">SKU {product.sku}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xl font-bold text-brand-blue">{formatCurrency(product.precio_oferta || product.precio)}</span>
                      {product.precio_oferta ? <span className="text-sm text-slate-500 line-through">{formatCurrency(product.precio)}</span> : null}
                    </div>
                    {product.video_url ? (
                      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-100">
                        <video controls src={product.video_url} className="h-48 w-full object-cover" />
                      </div>
                    ) : null}
                    <div className="grid gap-3">
                      <a
                        href={buildWhatsAppProductUrl(product)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-primary"
                      >
                        Lo quiero
                      </a>
                      <a
                        href={buildWhatsAppProductUrl(product)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                      >
                        Consultar ahora
                      </a>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function AdminPage() {
  const [verified, setVerified] = useState(false);
  const [ready, setReady] = useState(false);
  const [status, setStatus] = useState("Cargando panel...");
  const [tab, setTab] = useState("kits");
  const [kits, setKits] = useState([]);
  const [config, setConfig] = useState({
    about_text: "",
    phone: "",
    email: "",
    address: "",
    maps_url: "",
    instagram_url: "",
    facebook_url: "",
    search_filters: [],
  });
  const [kitForm, setKitForm] = useState({
    id: "",
    nombre: "",
    descripcion: "",
    precio: "",
    imagen: "",
    skus: "",
    activo: true,
    orden: 0,
  });
  const [productForm, setProductForm] = useState({
    sku: "",
    nombre: "",
    categoria: "",
    marca: "",
    color: "",
    precio: "",
    precio_oferta: "",
    stock: "",
    imagen: "",
    imagenes: "",
    video_url: "",
  });
  const [loginPassword, setLoginPassword] = useState("");
  const [message, setMessage] = useState("");

  const loadAdminData = async () => {
    try {
      const [kitData, storeData] = await Promise.all([fetchKits(), fetchStoreConfig()]);
      setKits(kitData.items || []);
      setConfig({
        ...storeData,
        search_filters: storeData.search_filters || [],
      });
      setStatus("");
    } catch (error) {
      setMessage(error.message || "No se pudo cargar el panel.");
    }
  };

  useEffect(() => {
    const verify = async () => {
      try {
        const ok = await adminVerify();
        setVerified(ok);
        if (ok) {
          await loadAdminData();
        }
      } catch (error) {
        setVerified(false);
      } finally {
        setReady(true);
      }
    };
    verify();
  }, []);

  const doLogin = async (event) => {
    event.preventDefault();
    setMessage("");
    try {
      await adminLogin(loginPassword);
      setVerified(true);
      setLoginPassword("");
      await loadAdminData();
    } catch (error) {
      setMessage(error.message || "Contraseña incorrecta.");
    }
  };

  const saveKit = async (event) => {
    event.preventDefault();
    setMessage("");
    try {
      const payload = {
        nombre: kitForm.nombre,
        descripcion: kitForm.descripcion,
        precio: Number(kitForm.precio) || 0,
        imagen: kitForm.imagen,
        skus: kitForm.skus.split(",").map((sku) => sku.trim()).filter(Boolean),
        activo: kitForm.activo,
        orden: Number(kitForm.orden) || 0,
      };
      if (kitForm.id) {
        await adminUpdateKit(kitForm.id, payload);
      } else {
        await adminCreateKit(payload);
      }
      setKitForm({ id: "", nombre: "", descripcion: "", precio: "", imagen: "", skus: "", activo: true, orden: 0 });
      await loadAdminData();
      setMessage("Kit guardado correctamente.");
    } catch (error) {
      setMessage(error.message || "Error guardando kit.");
    }
  };

  const editKit = (kit) => {
    setTab("kits");
    setKitForm({
      id: kit.id,
      nombre: kit.nombre || "",
      descripcion: kit.descripcion || "",
      precio: String(kit.precio || 0),
      imagen: kit.imagen || "",
      skus: (kit.skus || []).join(", "),
      activo: Boolean(kit.activo),
      orden: kit.orden || 0,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const removeKit = async (kitId) => {
    if (!window.confirm("¿Eliminar este kit?")) {
      return;
    }
    try {
      await adminDeleteKit(kitId);
      await loadAdminData();
      setMessage("Kit eliminado.");
    } catch (error) {
      setMessage(error.message || "No se pudo eliminar el kit.");
    }
  };

  const searchProduct = async (event) => {
    event.preventDefault();
    setMessage("");
    try {
      const product = await fetchProduct(productForm.sku.trim());
      setProductForm({
        sku: product.sku,
        nombre: product.nombre || "",
        categoria: product.categoria || "",
        marca: product.marca || "",
        color: product.color || "",
        precio: String(product.precio || 0),
        precio_oferta: String(product.precio_oferta || 0),
        stock: String(product.stock || 0),
        imagen: product.imagen || "",
        imagenes: (product.imagenes || []).join(", "),
        video_url: product.video_url || "",
      });
      setMessage("Producto cargado. Editá y guardá los cambios.");
    } catch (error) {
      setMessage(error.message || "No se encontró el producto.");
    }
  };

  const saveProduct = async (event) => {
    event.preventDefault();
    setMessage("");
    if (!productForm.sku.trim()) {
      setMessage("Ingresá un SKU válido.");
      return;
    }
    try {
      const patch = {
        categoria: productForm.categoria,
        marca: productForm.marca,
        color: productForm.color,
        precio: Number(productForm.precio) || 0,
        precio_oferta: Number(productForm.precio_oferta) || 0,
        stock: Number(productForm.stock) || 0,
        imagen: productForm.imagen,
        imagenes: productForm.imagenes.split(",").map((value) => value.trim()).filter(Boolean),
        video_url: productForm.video_url,
      };
      await adminUpdateProduct(productForm.sku.trim(), patch);
      setMessage("Producto actualizado correctamente.");
    } catch (error) {
      setMessage(error.message || "No se pudo actualizar el producto.");
    }
  };

  const saveConfig = async (event) => {
    event.preventDefault();
    setMessage("");
    try {
      await adminUpdateStoreConfig({
        about_text: config.about_text,
        phone: config.phone,
        email: config.email,
        address: config.address,
        maps_url: config.maps_url,
        instagram_url: config.instagram_url,
        facebook_url: config.facebook_url,
        search_filters: config.search_filters || [],
      });
      setMessage("Configuración guardada.");
    } catch (error) {
      setMessage(error.message || "No se pudo guardar la configuración.");
    }
  };

  if (!ready) {
    return <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-10 shadow-lg shadow-slate-200/40">Cargando panel administrativo...</div>;
  }

  if (!verified) {
    return (
      <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-10 shadow-lg shadow-slate-200/40">
        <h1 className="text-3xl font-bold text-slate-950">Panel administrativo</h1>
        <p className="mt-3 text-sm text-slate-600">Ingresá la contraseña para editar kits, productos y filtros.</p>
        <form onSubmit={doLogin} className="mt-8 grid gap-5 sm:max-w-md">
          <label className="space-y-3">
            <span className="text-sm font-semibold text-slate-800">Contraseña</span>
            <input
              type="password"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
              placeholder="••••••••"
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <button type="submit" className="btn-primary">
            Ingresar
          </button>
          {message ? <p className="text-sm text-destructive-foreground text-red-600">{message}</p> : null}
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-lg shadow-slate-200/40">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Panel de Nexo Store</p>
            <h1 className="mt-2 text-3xl font-bold text-slate-950">Administración rápida</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            {[
              { id: "kits", label: "Kits" },
              { id: "productos", label: "Productos" },
              { id: "configuracion", label: "Configuración" },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setTab(item.id)}
                className={`rounded-full px-5 py-3 text-sm font-semibold transition ${tab === item.id ? "bg-brand-blue text-white" : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      {message ? (
        <div className="rounded-[2rem] border border-brand-teal/40 bg-brand-teal/10 px-6 py-5 text-sm text-brand-blue shadow-sm">
          {message}
        </div>
      ) : null}
      {tab === "kits" && (
        <div className="grid gap-8 xl:grid-cols-[1fr_0.9fr]">
          <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm shadow-slate-200/40">
            <h2 className="text-2xl font-bold text-slate-950">Kits imperdibles</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">Creá y editá kits con imagen manual o video. Usá SKUs separados por comas.</p>
            <form onSubmit={saveKit} className="mt-8 space-y-5">
              <label className="block text-sm font-semibold text-slate-800">Nombre del kit</label>
              <input
                value={kitForm.nombre}
                onChange={(event) => setKitForm((prev) => ({ ...prev, nombre: event.target.value }))}
                placeholder="Kit de estudio completo"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <label className="block text-sm font-semibold text-slate-800">Descripción</label>
              <textarea
                value={kitForm.descripcion}
                onChange={(event) => setKitForm((prev) => ({ ...prev, descripcion: event.target.value }))}
                rows={4}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-800">Precio</label>
                <input
                  type="number"
                  step="0.01"
                  value={kitForm.precio}
                  onChange={(event) => setKitForm((prev) => ({ ...prev, precio: event.target.value }))}
                  placeholder="0"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">Orden</label>
                <input
                  type="number"
                  value={kitForm.orden}
                  onChange={(event) => setKitForm((prev) => ({ ...prev, orden: event.target.value }))}
                  placeholder="0"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
              </div>
              <label className="block text-sm font-semibold text-slate-800">Imagen / enlace Cloudinary</label>
              <input
                value={kitForm.imagen}
                onChange={(event) => setKitForm((prev) => ({ ...prev, imagen: event.target.value }))}
                placeholder="https://res.cloudinary.com/..."
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <label className="block text-sm font-semibold text-slate-800">SKUs incluidos</label>
              <input
                value={kitForm.skus}
                onChange={(event) => setKitForm((prev) => ({ ...prev, skus: event.target.value }))}
                placeholder="SKU1, SKU2, SKU3"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <div className="flex flex-wrap gap-3">
                <button type="submit" className="btn-primary">
                  {kitForm.id ? "Actualizar kit" : "Crear kit"}
                </button>
                <button
                  type="button"
                  onClick={() => setKitForm({ id: "", nombre: "", descripcion: "", precio: "", imagen: "", skus: "", activo: true, orden: 0 })}
                  className="btn-secondary"
                >
                  Limpiar formulario
                </button>
              </div>
            </form>
          </div>
          <div className="space-y-6">
            {kits.map((kit) => (
              <div key={kit.id} className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-6 shadow-sm shadow-slate-200/30">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">{kit.nombre}</p>
                    <p className="mt-2 text-sm text-slate-600">{kit.descripcion}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-brand-teal/10 px-3 py-1 text-sm font-semibold text-brand-teal">{kit.productos?.length || 0} productos</span>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">{formatCurrency(kit.precio)}</span>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button type="button" onClick={() => editKit(kit)} className="rounded-full border border-brand-blue px-4 py-2 text-sm font-semibold text-brand-blue transition hover:bg-brand-blue/5">
                    Editar
                  </button>
                  <button type="button" onClick={() => removeKit(kit.id)} className="rounded-full border border-destructive bg-destructive text-sm font-semibold text-white transition hover:bg-red-600">
                    Eliminar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {tab === "productos" && (
        <div className="grid gap-8 xl:grid-cols-[1fr_0.9fr]">
          <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm shadow-slate-200/40">
            <h2 className="text-2xl font-bold text-slate-950">Gestión de producto</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">Buscá por SKU y actualizá los campos de imagen, video y precios.</p>
            <form onSubmit={searchProduct} className="mt-8 space-y-5">
              <label className="block text-sm font-semibold text-slate-800">SKU del producto</label>
              <input
                value={productForm.sku}
                onChange={(event) => setProductForm((prev) => ({ ...prev, sku: event.target.value }))}
                placeholder="SKU12345"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <button type="submit" className="btn-primary">
                Cargar producto
              </button>
            </form>
          </div>
          <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-sm shadow-slate-200/40">
            <h3 className="text-xl font-semibold text-slate-950">Editar detalles</h3>
            <form onSubmit={saveProduct} className="mt-6 space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-800">Nombre</label>
                <input value={productForm.nombre} readOnly className="w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-500" />
                <label className="block text-sm font-semibold text-slate-800">Categoría</label>
                <input
                  value={productForm.categoria}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, categoria: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">Marca</label>
                <input
                  value={productForm.marca}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, marca: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">Color</label>
                <input
                  value={productForm.color}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, color: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-800">Precio</label>
                <input
                  type="number"
                  step="0.01"
                  value={productForm.precio}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, precio: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">Precio oferta</label>
                <input
                  type="number"
                  step="0.01"
                  value={productForm.precio_oferta}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, precio_oferta: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-semibold text-slate-800">Stock</label>
                <input
                  type="number"
                  value={productForm.stock}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, stock: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">Imagen principal</label>
                <input
                  value={productForm.imagen}
                  onChange={(event) => setProductForm((prev) => ({ ...prev, imagen: event.target.value }))}
                  placeholder="URL de imagen"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
              </div>
              <label className="block text-sm font-semibold text-slate-800">Imágenes adicionales (separadas por comas)</label>
              <input
                value={productForm.imagenes}
                onChange={(event) => setProductForm((prev) => ({ ...prev, imagenes: event.target.value }))}
                placeholder="https://... , https://..."
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <label className="block text-sm font-semibold text-slate-800">Video</label>
              <input
                value={productForm.video_url}
                onChange={(event) => setProductForm((prev) => ({ ...prev, video_url: event.target.value }))}
                placeholder="https://...mp4"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
              />
              <button type="submit" className="btn-primary">
                Guardar producto
              </button>
            </form>
          </div>
        </div>
      )}
      {tab === "configuracion" && (
        <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-8 shadow-lg shadow-slate-200/40">
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-slate-950">Datos de contacto</h2>
              <p className="mt-3 text-sm text-slate-600">Actualizá la info de la tienda y los enlaces visibles del sitio.</p>
              <form onSubmit={saveConfig} className="mt-8 space-y-5">
                <label className="block text-sm font-semibold text-slate-800">Texto de bienvenida</label>
                <textarea
                  value={config.about_text}
                  onChange={(event) => setConfig((prev) => ({ ...prev, about_text: event.target.value }))}
                  rows={4}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm font-semibold text-slate-800">Teléfono</label>
                  <input
                    value={config.phone}
                    onChange={(event) => setConfig((prev) => ({ ...prev, phone: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                  />
                  <label className="block text-sm font-semibold text-slate-800">Email</label>
                  <input
                    value={config.email}
                    onChange={(event) => setConfig((prev) => ({ ...prev, email: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                  />
                </div>
                <label className="block text-sm font-semibold text-slate-800">Dirección</label>
                <input
                  value={config.address}
                  onChange={(event) => setConfig((prev) => ({ ...prev, address: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <label className="block text-sm font-semibold text-slate-800">URL de Google Maps</label>
                <input
                  value={config.maps_url}
                  onChange={(event) => setConfig((prev) => ({ ...prev, maps_url: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm font-semibold text-slate-800">Instagram</label>
                  <input
                    value={config.instagram_url}
                    onChange={(event) => setConfig((prev) => ({ ...prev, instagram_url: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                  />
                  <label className="block text-sm font-semibold text-slate-800">Facebook</label>
                  <input
                    value={config.facebook_url}
                    onChange={(event) => setConfig((prev) => ({ ...prev, facebook_url: event.target.value }))}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                  />
                </div>
                <label className="block text-sm font-semibold text-slate-800">Filtros destacados</label>
                <input
                  value={(config.search_filters || []).join(", ")}
                  onChange={(event) => setConfig((prev) => ({ ...prev, search_filters: event.target.value.split(",").map((value) => value.trim()).filter(Boolean) }))}
                  placeholder="Librería, Tecno, Regalería"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900"
                />
                <button type="submit" className="btn-primary">
                  Guardar configuración
                </button>
              </form>
            </div>
            <div className="rounded-[2rem] border border-slate-200/70 bg-brand-blue/5 p-6">
              <h3 className="text-xl font-semibold text-slate-950">Mantenimiento rápido</h3>
              <p className="mt-3 text-sm leading-6 text-slate-700">Usá este panel para actualizar la comunicación pública y los filtros de búsqueda visibles para los usuarios.</p>
              <div className="mt-6 grid gap-4">
                <div className="rounded-3xl bg-white p-4 shadow-sm">
                  <p className="text-sm text-slate-600">Filtros activos</p>
                  <p className="mt-3 text-sm font-semibold text-slate-900">{(config.search_filters || []).join(" · ") || "No configurado"}</p>
                </div>
                <div className="rounded-3xl bg-white p-4 shadow-sm">
                  <p className="text-sm text-slate-600">Datos de contacto</p>
                  <p className="mt-3 text-sm font-semibold text-slate-900">{config.phone || "-"}</p>
                  <p className="text-sm text-slate-600">{config.email || "-"}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200/70 bg-white/90 py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 text-sm text-slate-600 sm:flex-row sm:px-6 lg:px-8">
        <p>© {new Date().getFullYear()} Nexo Store — Librería y marroquinería en Rosario.</p>
        <div className="flex flex-wrap items-center gap-3">
          <a href="/" className="transition hover:text-brand-blue">Inicio</a>
          <a href="/admin" className="transition hover:text-brand-blue">Panel</a>
          <a href={buildWhatsAppUrl([], 0)} target="_blank" rel="noreferrer" className="transition hover:text-brand-blue">
            WhatsApp
          </a>
        </div>
      </div>
    </footer>
  );
}

function WhatsAppFab() {
  return (
    <a
      href={buildWhatsAppUrl([], 0)}
      target="_blank"
      rel="noreferrer"
      className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-full bg-brand-teal px-5 py-3 text-sm font-semibold text-white shadow-2xl shadow-brand-teal/30 transition hover:bg-brand-tealDark"
    >
      <MessageCircle className="h-5 w-5" />
      Asesoría en WhatsApp
    </a>
  );
}

function NotFound() {
  return (
    <div className="rounded-[2rem] border border-slate-200/70 bg-white/90 p-16 text-center shadow-sm shadow-slate-200/40">
      <p className="text-sm uppercase tracking-[0.35em] text-brand-blue/70">Página no encontrada</p>
      <h1 className="mt-4 text-3xl font-bold text-slate-950">404 — No encontramos lo que buscás</h1>
      <p className="mt-4 text-sm leading-6 text-slate-600">Volvé al inicio para seguir buscando los mejores productos de Nexo Store.</p>
      <NavLink to="/" className="btn-primary mt-8 inline-flex">
        Volver al inicio
      </NavLink>
    </div>
  );
}

export default App;
