"use client";
import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import { useRequireAuth } from "../hooks/useRequireAuth";

export default function DashboardPage() {
  const { accessToken, authFetch } = useAuth();
  const [username, setUsername] = useState<string | null>(null);

  // Utiliser le hook de protection
  const isAuthorized = useRequireAuth("protected");


  // Effet 2 : chargement du profil, une seule fois
  useEffect(() => {
    if (!accessToken) return;
    authFetch(`${process.env.NEXT_PUBLIC_API_URL}/players/profil`)
      .then((res) => res.json())
      .then((data) => setUsername(data.username));
  }, []);

  if (!isAuthorized) {
  return null;
}

  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl text-ink">Bienvenue {username} !</h1>
      <p className="mx-auto mt-4 max-w-lg break-all text-sm">{accessToken}</p>
    </main>
  );
}