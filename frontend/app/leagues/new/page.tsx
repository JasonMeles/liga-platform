"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useRequireAuth } from "@/app/hooks/useRequireAuth";
import {useAuth } from "@/app/components/AuthProvider";


export default function CreateLeaguePage() {
  const [form, setForm] = useState({
  name: "",
  max_teams: "",
  max_per_player: "",
  total_journeys: "",
  sport_type: "football",
  allow_same_owner_matches: true,
});
  const [errorMessage, setErrorMessage] = useState("");
  const router = useRouter();
  const isAuthorized = useRequireAuth("protected");
  const { accessToken, authFetch } = useAuth();
  

  function handleChanges(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const changesName = e.target.name;
    const nouvelleValeur = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    const nouvelObjet = { ...form, [changesName]: nouvelleValeur };
    setForm(nouvelObjet);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    setErrorMessage("");
    e.preventDefault();

    if (!accessToken) return;
    try {
        const response = await authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({...form, max_teams : Number(form.max_teams), max_per_player : Number(form.max_per_player), total_journeys : Number(form.total_journeys)}),
        });

        if (response.ok) {
        const data = await response.json();
        router.push(`/leagues/${data.id}`);
        } else {
        const errorData = await response.json();
        if (Array.isArray(errorData.detail)) {
            setErrorMessage(errorData.detail[0].msg.replace("Value error, ", ""));   // erreur de validation Pydantic : une liste
            } else {
            setErrorMessage(errorData.detail);          // HTTPException : une chaîne
            }
        console.error("Erreur lors de la création de la ligue :", errorData.detail);
        }
    }
    catch{
        setErrorMessage("Impossible de contacter le serveur");
    }
  }
 // --- Zone 2 : décider quoi afficher ---
  if (!isAuthorized) return null;

  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center text-center">
      <div className=" relative h-screen bg-cover  px-6 w-full">
        <div className="absolute inset-0 bg-ink/50" />
        <div className="absolute inset-y-0 left-0 w-full max-w-md backdrop-blur-md bg-ink/40 flex flex-col items-center justify-center px-8">
        <section className="max-w-md">
        <h1 className="relative z-10 font-display text-3xl text-white">Créer une ligue</h1>
        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        {errorMessage && (
          <div className="relative z-10 text-sm text-orange-500">
            <p>{errorMessage}</p>
          </div>
        )}
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="name" value={form.name} onChange={handleChanges} placeholder="Nom de la ligue" type="text" maxLength={30} required />
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="max_teams" value={form.max_teams} onChange={handleChanges} placeholder="Nombre d'équipes maximum" type="number" min={2} max={100} required />
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="max_per_player" value={form.max_per_player} onChange={handleChanges} placeholder="Nombre d'équipe maximum contrôlé par joueur" type="number" min={1} max={100} required />
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="total_journeys" value={form.total_journeys} onChange={handleChanges} placeholder="Nombre de journées" type="number" min={1} max={100} required />
        <select className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="sport_type" value={form.sport_type} onChange={handleChanges} required>
          <option value="football">Football</option>
          <option value="basketball">Basketball</option>
        </select>
        <label className="relative z-10 flex items-center gap-2 text-white">
          <input type="checkbox" name="allow_same_owner_matches" checked={form.allow_same_owner_matches} onChange={handleChanges} className="h-4 w-4 rounded border-white/30 bg-white/10 text-white focus:ring-white/60" />
          Autoriser les matchs entre équipes du même joueur
        </label>
        <button className="relative z-10 mt-2 inline-block rounded-full bg-chalk px-7 py-3 font-sans font-semibold text-ink transition hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-white/70" type="submit">Créer la ligue</button>
        </form>
        </section>
        </div>
      </div>
    </main>
  );
}