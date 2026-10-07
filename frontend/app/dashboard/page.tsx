"use client";
import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import { useRequireAuth } from "../hooks/useRequireAuth";

export default function DashboardPage() {
  const { accessToken, authFetch } = useAuth();
  const [username, setUsername] = useState<string | null>(null);
  const [isJoinOpen, setIsJoinOpen] = useState(false)
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
    <main className="mx-auto flex min-h-screen flex-col items-center px-6 pt-24 text-center">
  <h1 className="font-display text-3xl text-ink">Bienvenue {username} !</h1>

  <div className="mt-12 grid w-full max-w-5xl grid-cols-1 gap-6 sm:grid-cols-3">
    <div className="rounded-3xl bg-ink/55 px-6 py-6 text-center backdrop-blur-sm sm:px-10 sm:py-7">
      Créer une ligue
    </div>
    <div className="rounded-3xl bg-ink/55 px-6 py-6 text-center backdrop-blur-sm sm:px-10 sm:py-7">
      Rejoindre une ligue
    </div>
    <div className="rounded-3xl bg-ink/55 px-6 py-6 text-center backdrop-blur-sm sm:px-10 sm:py-7">
      Mes ligues
    </div>
  </div>
</main>
  );
}