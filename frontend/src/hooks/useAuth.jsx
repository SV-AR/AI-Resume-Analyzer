import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi, tokenStore } from "../services/api";

const AuthContext = createContext(null);

/**
 * Auth storage choice: the JWT lives in localStorage (simple for a SPA + REST API, expires after
 * ACCESS_TOKEN_EXPIRE_MINUTES). The trade-off is that any XSS bug could read it; React escapes output by
 * default and the app renders no raw HTML. A production system could use httpOnly cookies instead.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(tokenStore.get()));

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  useEffect(() => {
    window.addEventListener("sra:logout", logout);
    return () => window.removeEventListener("sra:logout", logout);
  }, [logout]);

  useEffect(() => {
    if (!tokenStore.get()) return;
    authApi.me().then(setUser).catch(() => tokenStore.clear()).finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login({ email, password });
    tokenStore.set(data.access_token);
    setUser(data.user);
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
