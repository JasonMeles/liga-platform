"use client";

import { createContext, useContext, useState, ReactNode, useRef } from "react";

// La "forme" de ce que le Context partage, comme un modèle Pydantic
type AuthContextType = {
  accessToken: string | null;   // string | null ≈ Optional[str]
  refreshToken: string | null;
  login: (access: string, refresh: string) => void;
  logout: () => Promise<void>;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
};

// Déclare l'emplacement partagé, vide au départ
const AuthContext = createContext<AuthContextType | null>(null);

// Le composant qui détient réellement le state (l'objet C++ AuthManager)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const refreshPromise = useRef<Promise<string | null> | null>(null);

  function login(access: string, refresh: string) {
    setAccessToken(access);
    setRefreshToken(refresh);
  }

  async function logout() {
    if (refreshToken) {
        try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
        } catch (error) {
        console.error("Échec de la révocation côté serveur :", error);
        }
    }
    setAccessToken(null);
    setRefreshToken(null);
  }

  async function renewTokens(): Promise<string | null> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    logout();
    return null;
  }

  const data = await res.json();
  login(data.access_token, data.refresh_token);
  return data.access_token;
}

async function authFetch(url: string, options: RequestInit = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${accessToken}` },
  });

  if (response.status !== 401) {
    return response;
  }

  // Si aucun refresh n'est en cours, on en lance un et on range sa promesse
  if (!refreshPromise.current) {
    refreshPromise.current = renewTokens().finally(() => {
      refreshPromise.current = null; // on vide la boîte quand c'est fini
    });
  }

  // Tout le monde attend LE MÊME refresh
  const newAccessToken = await refreshPromise.current;

  if (!newAccessToken) {
    return response; // le refresh a échoué, logout() a déjà été appelé
  }

  return fetch(url, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${newAccessToken}` },
  });
}

  // .Provider rend ces valeurs accessibles à tout ce qui est à l'intérieur
  // ≈ setContextProperty en Qt
  return (
    <AuthContext.Provider value={{ accessToken, refreshToken, login, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
}

// Le hook que les pages appelleront : const { accessToken } = useAuth();
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    // "Fail loud, not silent", comme pour SECRET_KEY
    throw new Error("useAuth doit être utilisé à l'intérieur d'un AuthProvider");
  }
  return context;
}