const TOKEN_KEY = "exam_token";
const USER_KEY = "exam_user";

export const auth = {
  token: () => localStorage.getItem(TOKEN_KEY),
  user: () => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; }
  },
  save: (data) => {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({
      role: data.role, full_name: data.full_name, user_id: data.user_id,
    }));
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = auth.token();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the server. Check your connection.", 0);
  }

  if (res.status === 401) {
    auth.clear();
    if (!location.pathname.startsWith("/login")) location.href = "/login";
    throw new ApiError("Your session has expired. Sign in again.", 401);
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    let msg = "Something went wrong.";
    const d = data?.detail;
    if (typeof d === "string") msg = d;
    else if (Array.isArray(d)) msg = d.map((e) => e.msg).join(", ");
    throw new ApiError(msg, res.status);
  }
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  del: (p) => request(p, { method: "DELETE" }),
};
