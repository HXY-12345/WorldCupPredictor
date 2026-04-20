/* 核心功能：解析前端运行时的后端 API 基础地址，兼容本地开发和显式配置覆盖。 */
function normalizeBaseUrl(value) {
  if (typeof value !== "string") {
    return "";
  }

  return value.trim().replace(/\/$/, "");
}

function readMetaApiBaseUrl(documentRef) {
  if (!documentRef?.querySelector) {
    return "";
  }

  const meta = documentRef.querySelector('meta[name="worldcup-api-base-url"]');
  return normalizeBaseUrl(meta?.getAttribute("content") ?? "");
}

function isLocalHostname(hostname) {
  return hostname === "127.0.0.1" || hostname === "localhost";
}

export function resolveApiBaseUrl({
  windowRef = globalThis.window,
  documentRef = windowRef?.document,
  locationRef = windowRef?.location ?? globalThis.location
} = {}) {
  const configuredBaseUrl = normalizeBaseUrl(windowRef?.WORLDCUP_API_BASE_URL ?? "");
  if (configuredBaseUrl) {
    return configuredBaseUrl;
  }

  const metaBaseUrl = readMetaApiBaseUrl(documentRef);
  if (metaBaseUrl) {
    return metaBaseUrl;
  }

  if (!locationRef || (locationRef.protocol !== "http:" && locationRef.protocol !== "https:")) {
    return "";
  }

  if (locationRef.port && locationRef.port !== "8000" && isLocalHostname(locationRef.hostname)) {
    return `${locationRef.protocol}//${locationRef.hostname}:8000`;
  }

  return "";
}
