import Link from "next/link";

export default function RegisterPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
      <h1 className="font-display text-3xl text-ink">Créer un compte</h1>
      <p className="mt-4 font-sans text-ink/70">Le formulaire arrive à l'étape suivante.</p>
      <Link href="/auth" className="mt-8 font-sans text-sm text-ink/50 hover:text-ink/80">← Retour</Link>
    </main>
  );
}