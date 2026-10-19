"use client";
import { useState, useEffect } from "react";
import { useAuth } from "../../components/AuthProvider";
import type { LeagueDetail, Team } from "@/app/types/league";
import CreateTeamModal from "./CreateTeamModal";

export default function TeamList({ leagueId, maxTeams, maxPerPlayer, myRole, isActive, onLaunchLeague }: { leagueId: string, maxTeams: number, maxPerPlayer: number, myRole: LeagueDetail["my_role"], isActive: boolean, onLaunchLeague: () => void }) {

    const { accessToken, username, authFetch } = useAuth();
    // --- États ---
    const [teams, setTeams] = useState<Team[] | null>(null); // null = pas encore chargé
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [launchError, setLaunchError] = useState<string | null>(null);

    async function handleLaunch() {
        setLaunchError(null);
        try {
            const res = await authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/${leagueId}/validate`, {
                method: "POST",
            });
            if (!res.ok) {
                const errorData = await res.json();
                setLaunchError(errorData.detail);
                return;
            }
            onLaunchLeague();   // « page.tsx, la ligue est lancée »
        } catch {
            setLaunchError("Impossible de contacter le serveur");
        }
    }

    useEffect(() => {
        if (!accessToken) return;
        authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/${leagueId}/teams`)
            .then((res) => {
                if (!res.ok) throw new Error("Impossible de charger les équipes");
                return res.json();
            })
            .then((data) => setTeams(data))
            .catch(() => setError("Impossible de charger les équipes"));
    }, [accessToken, leagueId]);

    // avant le return, après les useEffect
    const myTeamsCount = teams ? teams.filter((t) => t.owner_username === username).length : 0;
    const placesLeft = teams ? maxTeams - teams.length : 0;
    const myPlacesLeft = Math.min(maxPerPlayer - myTeamsCount, placesLeft);
    const canAddTeam = myPlacesLeft > 0 || (myRole === "manager" && placesLeft > 0);


    return (
        <section className="mt-12 w-full max-w-5xl">
            <h2 className="font-display text-2xl text-ink">Équipes</h2>
            {showModal &&
                <CreateTeamModal onClose={() => setShowModal(false)} leagueId={leagueId} onCreated={(team) => setTeams([...(teams ?? []), team])} myRole={myRole} />}
            <div className="mt-4 flex justify-center gap-4">
                {!isActive &&
                    <button className="rounded border border-ink px-3 py-1" onClick={() => setShowModal(true)} disabled={!canAddTeam} >Inscrire une équipe</button>}
                {myRole === "manager" &&
                    !isActive &&
                    teams &&
                    teams.length >= 2 &&
                    <button className="rounded border border-ink px-3 py-1" onClick={handleLaunch}>  Lancer la ligue</button>
                }
            </div>
            {launchError &&
                <p className="mt-2 text-red-600">{launchError}</p>
            }
            {error &&
                <p className="mt-6 text-red-600">{error}</p>
            }
            {!error &&
                teams === null &&
                <p className="mt-6">Chargement…</p>
            }
            {!isActive &&
                !error &&
                teams !== null
                && <p className="mt-6"> Nombre d'equipes totales restantes à inscrire : {placesLeft} / {maxTeams} </p>
            }

            {!isActive &&
                !error &&
                teams !== null &&
                <p className="mt-6"> Nombre d'equipes restantes pour toi : {myPlacesLeft} / {maxPerPlayer} </p>
            }
            {!isActive &&
                teams?.length === 0 &&
                <p className="mt-6">Aucune équipe inscrite.</p>
            }
            {
                teams && teams.length > 0 && (
                    <div className="mt-6 grid w-full grid-cols-1 gap-6 sm:grid-cols-3">
                        {teams.map((team) => (
                            <div key={team.id} className="rounded-lg border border-gray-300 p-4">
                                <h3 className="font-semibold text-lg">{team.nom}</h3>
                                <p>Stade : {team.nom_stade}</p>
                                <p>Propriétaire : {team.owner_username === "AI" ? "IA" : team.owner_username}</p>
                                <p>Journées restantes : {team.journeys_remaining}</p>
                            </div>
                        ))}
                    </div>
                )
            }</section>
    );
}