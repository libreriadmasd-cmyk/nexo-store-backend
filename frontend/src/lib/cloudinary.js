// Cloudinary unsigned upload + URL transformations
const CLOUD_NAME = process.env.REACT_APP_CLOUDINARY_CLOUD_NAME;
const UPLOAD_PRESET = process.env.REACT_APP_CLOUDINARY_UPLOAD_PRESET;

export const isCloudinaryConfigured = () =>
  Boolean(CLOUD_NAME && UPLOAD_PRESET);

export const uploadToCloudinary = async (file) => {
  if (!isCloudinaryConfigured()) {
    throw new Error("Cloudinary no configurado (revisar .env)");
  }
  const fd = new FormData();
  fd.append("file", file);
  fd.append("upload_preset", UPLOAD_PRESET);
  const r = await fetch(
    `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`,
    { method: "POST", body: fd }
  );
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e?.error?.message || "Error subiendo a Cloudinary");
  }
  const data = await r.json();
  return data.secure_url || data.url;
};

/**
 * Transform a Cloudinary URL to apply automatic optimizations.
 * - f_auto: best format (webp/avif on supported browsers)
 * - q_auto: best quality vs size
 * - c_pad with white background for product thumbnails
 * - dpr_auto: retina handling
 *
 * Falls back to original URL if not a Cloudinary URL.
 */
export const cldOptimize = (url, opts = {}) => {
  if (!url || typeof url !== "string") return url;
  if (!url.includes("res.cloudinary.com") || !url.includes("/image/upload/")) {
    return url;
  }
  const w = opts.width;
  const h = opts.height;
  const mode = opts.mode || "pad"; // pad | fill | fit
  const bg = opts.background || "white";
  const transforms = ["f_auto", "q_auto", "dpr_auto"];
  if (w || h) {
    if (w) transforms.push(`w_${w}`);
    if (h) transforms.push(`h_${h}`);
    transforms.push(`c_${mode}`);
    if (mode === "pad") transforms.push(`b_${bg}`);
  }
  const t = transforms.join(",");
  return url.replace("/image/upload/", `/image/upload/${t}/`);
};

export const cldThumb = (url) => cldOptimize(url, { width: 400, height: 400, mode: "pad" });
export const cldHero = (url) => cldOptimize(url, { width: 900, height: 900, mode: "pad" });
export const cldTile = (url) => cldOptimize(url, { width: 600, height: 600, mode: "fill" });
