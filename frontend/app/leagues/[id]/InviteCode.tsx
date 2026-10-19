"use client";
import { useState } from "react";
import { useAuth } from "@/app/components/AuthProvider";

export default function InviteCode({ leagueId }: { leagueId: string }) {
    const [code, setCode] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const { authFetch } = useAuth();
    const [copied, setCopied] = useState<boolean>(false);

    async function handleShow() {
        try {
            const res = await authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/${leagueId}/invite-code`);
            if (!res.ok) { setError("Impossible de récupérer le code d’invitation"); return; }
            const data = await res.json();
            setCode(data.invite_code);
        } catch {
            setError("Impossible de contacter le serveur");
        }
    }
    async function handleCopy() {
        if (code === null) return;
        await navigator.clipboard.writeText(code)
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }

    return (
        <section className="mt-8">
            {error && <p className="text-red-600">{error}</p>}
            {code === null
                ? <button onClick={handleShow}>Afficher le code d'invitation</button>
                : (
                    <>
                        <p>Code d'invitation : {code}</p>
                        <button onClick={handleCopy}>
                            {copied ? "Copié !" : "Copier"}
                        </button>
                    </>
                )}
        </section>
    );

}

