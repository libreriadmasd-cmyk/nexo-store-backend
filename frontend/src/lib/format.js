export const formatARS = (value) => {
  const n = Number(value) || 0;
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 2,
  }).format(n);
};

export const slugifyCategory = (c) =>
  (c || "").toString().trim();
