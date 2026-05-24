import { formatARS } from "./format";

export const WHATSAPP_NUMBER =
  process.env.REACT_APP_WHATSAPP_NUMBER || "5493465538232";

export const buildWhatsAppMessage = (items, total) => {
  const lines = ["Hola Nexo Store, quiero comprar:", ""];
  if (!items || items.length === 0) {
    lines.push("(Aún sin productos)");
  } else {
    items.forEach((i, idx) => {
      const subtotal = i.precio * i.cantidad;
      lines.push(
        `${idx + 1}. ${i.nombre} (SKU ${i.sku || i.id}) — x${i.cantidad} — ${formatARS(i.precio)} c/u = ${formatARS(subtotal)}`
      );
    });
    lines.push("");
    lines.push(`Total: ${formatARS(total)}`);
  }
  return lines.join("\n");
};

export const buildWhatsAppUrl = (items, total) => {
  const text = encodeURIComponent(buildWhatsAppMessage(items, total));
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${text}`;
};

export const buildWhatsAppProductUrl = (product) => {
  if (!product) return `https://wa.me/${WHATSAPP_NUMBER}`;
  const lines = [
    "Hola Nexo Store, quiero consultar por este producto:",
    "",
    `• ${product.nombre}`,
    `• SKU: ${product.sku}`,
  ];
  if (product.precio_oferta && Number(product.precio_oferta) > 0) {
    lines.push(`• Precio oferta: ${formatARS(product.precio_oferta)}`);
  } else if (product.precio) {
    lines.push(`• Precio: ${formatARS(product.precio)}`);
  }
  const text = encodeURIComponent(lines.join("\n"));
  return `https://wa.me/${WHATSAPP_NUMBER}?text=${text}`;
};
