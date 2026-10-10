"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../components/AuthProvider";
import { useRequireAuth } from "../hooks/useRequireAuth";
import type { League } from "../types/league";

export default function LeaguesPage() {
  const { accessToken, authFetch } = useAuth();
  const isAuthorized = useRequireAuth("protected");

  // --- États ---
  const [leagues, setLeagues] = useState<League[] | null>(null); // null = pas encore chargé
  const [error, setError] = useState<string | null>(null);        // null = pas d'erreur

  // --- Zone 1 : aller chercher les données ---
  useEffect(() => {
    if (!accessToken) return;
    authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/me`)
      .then((res) => {
        if (!res.ok) throw new Error("Impossible de charger tes ligues");
        return res.json();
      })
      .then((data) => setLeagues(data))
      .catch(() => setError("Impossible de charger tes ligues"));
  }, [accessToken]);

  // --- Zone 2 : décider quoi afficher ---
  if (!isAuthorized) return null;

  if (error) {
    return (
      <main className="flex min-h-screen flex-col items-center px-6 pt-24 text-center">
        <p className="text-red-600">{error}</p>
      </main>
    );
  }

  if (leagues === null) {
    return (
      <main className="flex min-h-screen flex-col items-center px-6 pt-24 text-center">
        <p>Chargement…</p>
      </main>
    );
  }

  if (leagues.length === 0) {
    return (
      <main className="flex min-h-screen flex-col items-center px-6 pt-24 text-center">
        <h1 className="font-display text-3xl text-ink">Mes ligues</h1>
        <p className="mt-6">Tu n'appartiens à aucune ligue pour l'instant.</p>
        <Link href="/dashboard" className="mt-4 underline">
          Créer ou rejoindre une ligue
        </Link>
      </main>
    );
  }

  // Ici, on sait que leagues contient au moins une ligue
  return (
    <main className="mx-auto flex min-h-screen flex-col items-center px-6 pt-24 text-center">
      <h1 className="font-display text-3xl text-ink">Mes ligues</h1>
      <div className="mt-12 grid w-full max-w-5xl grid-cols-1 gap-6 sm:grid-cols-3">
        {leagues.map((league) => (
          <Link
            key={league.id}
            href={`/leagues/${league.id}`}
            className="rounded-3xl bg-ink/55 px-6 py-6 text-center text-white backdrop-blur-sm sm:px-10 sm:py-7"
          >
            <h2 className="text-xl font-bold">{league.name}</h2>
            <p>Manager : {league.manager_username}</p>
            <p>Sport : {league.sport_type}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}