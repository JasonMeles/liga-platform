"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";

export default function DashboardPage() {
  const { accessToken, authFetch } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState<string | null>(null);

  // Effet 1 : protection de la route
  useEffect(() => {
    if (!accessToken) {
      router.replace("/auth/login");
    }
  }, [accessToken, router]);

  // Effet 2 : chargement du profil, une seule fois
  useEffect(() => {
    if (!accessToken) return;
    authFetch(`${process.env.NEXT_PUBLIC_API_URL}/players/profil`)
      .then((res) => res.json())
      .then((data) => setUsername(data.username));
  }, []);

  if (!accessToken) {
    return null;
  }

  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl text-ink">Bienvenue {username} !</h1>
      <p className="mx-auto mt-4 max-w-lg break-all text-sm">{accessToken}</p>
    </main>
  );
}