"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";

export default function DashboardPage() {
  const { accessToken } = useAuth();
  const router = useRouter();

  // S'exécute APRÈS l'affichage, puis à chaque changement de accessToken
  useEffect(() => {
    if (!accessToken) {
      router.replace("/auth/login");
    }
  }, [accessToken, router]);

  // Pas de token : on n'affiche rien pendant la redirection
  if (!accessToken) {
    return null;
  }

  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl text-ink">Bienvenue sur Liga Platform</h1>
      <p className="mx-auto mt-4 max-w-lg font-sans text-lg text-ink/70">
        La page du dashboard est en cours de construction. Restez à l'écoute pour les mises à jour et les nouvelles fonctionnalités !
      </p>
      <p className="mx-auto mt-4 max-w-lg break-all text-sm">{accessToken}</p>
    </main>
  );
}