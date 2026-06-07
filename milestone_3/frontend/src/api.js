const API_BASE = import.meta.env.VITE_API_BASE || "";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof payload === "object" ? payload.error : payload;
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return payload;
}

export async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });
  return parseResponse(response);
}

export async function apiPost(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return parseResponse(response);
}

export async function apiDelete(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    credentials: "include",
  });
  return parseResponse(response);
}

export async function apiUpload(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  return parseResponse(response);
}
