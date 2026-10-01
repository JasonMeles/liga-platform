"use client";

import { createContext, useContext, useState, ReactNode } from "react";

// La "forme" de ce que le Context partage, comme un modèle Pydantic
type AuthContextType = {
  accessToken: string | null;   // string | null ≈ Optional[str]
  refreshToken: string | null;
  login: (access: string, refresh: string) => void;
  logout: () => void;
};

// Déclare l'emplacement partagé, vide au départ
const AuthContext = createContext<AuthContextType | null>(null);

// Le composant qui détient réellement le state (l'objet C++ AuthManager)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);

  function login(access: string, refresh: string) {
    setAccessToken(access);
    setRefreshToken(refresh);
  }

  function logout() {
    setAccessToken(null);
    setRefreshToken(null);
  }

  // .Provider rend ces valeurs accessibles à tout ce qui est à l'intérieur
  // ≈ setContextProperty en Qt
  return (
    <AuthContext.Provider value={{ accessToken, refreshToken, login, logout }}>
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