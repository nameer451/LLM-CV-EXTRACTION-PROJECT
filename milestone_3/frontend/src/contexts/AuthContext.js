import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ authenticated: false, loading: true });

  useEffect(() => {
    apiGet("/api/auth-status")
      .then((payload) => setAuth({ ...payload, loading: false }))
      .catch(() => setAuth({ authenticated: false, loading: false }));
  }, []);

  async function login(username, password) {
    const payload = await apiPost("/api/login", { username, password });
    setAuth({ ...payload, loading: false });
    return payload;
  }

  async function logout() {
    await apiPost("/api/logout");
    setAuth({ authenticated: false, loading: false });
  }

  const value = useMemo(() => ({ auth, login, logout }), [auth]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
