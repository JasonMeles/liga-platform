"use client";
import { useState } from "react";
import { useAuth } from "@/app/components/AuthProvider";


type CreateTeamModalProps = {
    leagueId: string;
    onClose: () => void;
};

export default function CreateTeamModal({ onClose, leagueId }: CreateTeamModalProps) {
    const { accessToken, authFetch } = useAuth();
    const [errorMessage, setErrorMessage] = useState("");
    const [equipe, setEquipe] = useState({
        nom: "",
        nom_stade: "",
        id_league: Number(leagueId),
        is_ia: false
    })

    function handleChanges(e: React.ChangeEvent<HTMLInputElement>) {
    const changes = e.target.name;
    const nouvelleValeur = e.target.value;
    const nouvelObjet = { ...equipe, [changes]: nouvelleValeur };
    setEquipe(nouvelObjet);
  }

    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setErrorMessage("");
        if (!accessToken) return;

        try {
            const response = await authFetch(`${process.env.NEXT_PUBLIC_API_URL}/teams/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(equipe),
            });

            if (response.ok) {
               onClose();
            } else {
                const errorData = await response.json();
                if (Array.isArray(errorData.detail)) {
                    setErrorMessage(errorData.detail[0].msg.replace("Value error, ", ""));
                } else {
                    setErrorMessage(errorData.detail);
                }
            }
        } catch {
            setErrorMessage("Impossible de contacter le serveur");
        }
    } // ← fin de handleSubmit

    return (
        <div onClick={onClose} className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 px-6">
            <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md rounded-3xl bg-ink p-6 text-center">
                <h2 className="font-display text-2xl text-white">Inscrire une équipe</h2>
                <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
                    {errorMessage && <p className="text-sm text-orange-500">{errorMessage}</p>}

                    <input
                        className="w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 focus:border-white/60 focus:outline-none"
                        name="nom"
                        placeholder="Nom de l'équipe"
                        value={equipe.nom}
                        onChange={handleChanges}
                        type="text"
                        maxLength={30}
                        required
                    />
                    <input
                        className="w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 focus:border-white/60 focus:outline-none"
                        name="nom_stade"
                        placeholder="Nom du stade"
                        value={equipe.nom_stade}
                        onChange={handleChanges}
                        type="text"
                        maxLength={30}
                        required
                    />
                    <div className="flex justify-center gap-3">
                        <button type="button" onClick={onClose} className="cursor-pointer rounded-full border border-white/40 px-6 py-2 text-white">
                            Annuler
                        </button>
                        <button type="submit" className="cursor-pointer rounded-full bg-chalk px-6 py-2 font-semibold text-ink">
                            Créer
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}