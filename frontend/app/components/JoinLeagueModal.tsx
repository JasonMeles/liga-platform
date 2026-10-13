"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/components/AuthProvider";

type JoinLeagueModalProps = {
  onClose: () => void;
};

export default function JoinLeagueModal({ onClose }: JoinLeagueModalProps) {
  // --- Hooks : TOUJOURS à l'intérieur du composant ---
  const router = useRouter();
  const { accessToken, authFetch } = useAuth();
  const [code, setCode] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErrorMessage("");
    if (!accessToken) return;

    try {
      const response = await authFetch(`${process.env.NEXT_PUBLIC_API_URL}/leagues/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invite_code: code }),
      });

      if (response.ok) {
        router.push("/leagues");
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
        <h2 className="font-display text-2xl text-white">Rejoindre une ligue</h2>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          {errorMessage && <p className="text-sm text-orange-500">{errorMessage}</p>}

          <input
            className="w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 focus:border-white/60 focus:outline-none"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Code d'invitation"
            type="text"
            maxLength={6}
            required
          />

          <div className="flex justify-center gap-3">
            <button type="button" onClick={onClose} className="cursor-pointer rounded-full border border-white/40 px-6 py-2 text-white">
              Annuler
            </button>
            <button type="submit" className="cursor-pointer rounded-full bg-chalk px-6 py-2 font-semibold text-ink">
              Rejoindre
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} // ← fin du composant