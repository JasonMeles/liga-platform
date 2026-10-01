"use client";
import { useAuth } from "../components/AuthProvider";

export default function DashboardPage() {
  const { accessToken } = useAuth();
  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl text-ink">Bienvenue sur Liga Platform</h1>
      <p className="mx-auto mt-4 max-w-lg font-sans text-lg text-ink/70">
        La page du dashboard est en cours de construction. Restez à l'écoute pour les mises à jour et les nouvelles fonctionnalités !
        </p>
        <p className="mx-auto max-w-lg  mt-4 break-all text-sm">{accessToken ?? "Aucun token"}</p>
    </main>
  );
}