"use client";
import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { useAuth } from "../../components/AuthProvider";
import { useRequireAuth } from "../../hooks/useRequireAuth";
import type { LeagueDetail } from "@/app/types/league";
import InviteCode from "./InviteCode";
import TeamList from "./TeamList";


export default function LeaguePage() {
    const { id } = useParams<{ id: string }>();
    const { accessToken, authFetch } = useAuth();
    const isAuthorized = useRequireAuth("protected");
    const [error, setError] = useState<string | null>(null);
    const [league, setLeague] = useState<LeagueDetail | null>(null); // null = pas encore chargé

    useEffect(() => {
        if (!accessToken) return;
        authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/${id}`)
            .then((res) => {
                if (res.status === 404) throw new Error("Ligue introuvable");
                if (!res.ok) throw new Error("Impossible de charger la ligue");
                return res.json();
            })
            .then((data) => setLeague(data))
            .catch((err) => {
                if (err.message === "Ligue introuvable") setError(err.message);
                else setError("Impossible de charger la ligue");
            });
    }, [accessToken, id]);

    if (!isAuthorized) return null;

    if (error) {
        return (
            <main className="flex min-h-screen flex-col items-center px-6 pt-24 text-center">
                <p className="text-red-600">{error}</p>
            </main>
        );
    }

    if (league === null) {
        return (
            <main className="flex min-h-screen flex-col items-center px-6 pt-24 text-center">
                <p>Chargement…</p>
            </main>
        );
    }

    return (
        <main className="mx-auto flex min-h-screen flex-col items-center px-6 pt-24 text-center">
            <h1 className="font-display text-3xl text-ink">Ligue : {league.name}</h1>
            {league.my_role === "manager" && <InviteCode leagueId={id} />} 
            <p className="mt-4">Manager : {league.manager_username}</p>
            <p>Sport : {league.sport_type}</p>
            <p>État : {league.is_active ? "Active" : "Inactive"}</p>
            <p>Journées : {league.total_journeys}</p>
            <p>Rôle : {league.my_role}</p>
            <TeamList leagueId={id} maxTeams={league.max_teams} maxPerPlayer={league.max_per_player} myRole={league.my_role}/>
        </main>
    );
}