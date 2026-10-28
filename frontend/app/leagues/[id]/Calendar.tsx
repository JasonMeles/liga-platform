"use client";
import { useState, useEffect } from "react";
import { useAuth } from "../../components/AuthProvider";
import type { Match } from "@/app/types/league";

const STATE_LABELS: Record<Match["state"], string> = {
    PENDING: "À jouer",
    IN_PROGRESS: "En cours",
    FINISHED: "Terminé",
};

export default function Calendar({ leagueId }: { leagueId: string}) {
    const { accessToken, authFetch } = useAuth();
    const [error, setError] = useState<string | null>(null);
    const [calendar, setCalendar] = useState<Match[] | null>(null);

    useEffect(() => {
        if (!accessToken) return;
        authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/${leagueId}/calendar`)
            .then((res) => {
                if (!res.ok) throw new Error("Impossible de charger le calendrier");
                return res.json();
            })
            .then((data) => setCalendar(data))
            .catch(() => setError("Impossible de charger le calendrier"));
    }, [accessToken, leagueId]);



    return (
        <section className="mt-12 w-full max-w-5xl">
            <h2 className="font-display text-2xl text-ink">Calendrier</h2>
            {error &&
                <p className="mt-6 text-red-600">{error}</p>
            }
            {!error &&
                calendar === null &&
                <p className="mt-6">Chargement…</p>
            }
            {calendar && calendar.length > 0 && (
                <ul className="mt-6 flex flex-col gap-2">
                    {calendar.map((match) => (
                        <li key={match.id}>
                            J{match.round_number} · {match.team_home} vs {match.team_away} · Stade : {match.stadium} · état : {STATE_LABELS[match.state]} · score :{match.score_home ?? "–"} vs {match.score_away ?? "–"}
                        </li>
                    ))}
                </ul>
            )
        }</section>
    )
}
