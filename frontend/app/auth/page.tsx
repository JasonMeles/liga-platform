import Link from "next/link";

export default function AuthChoice() {
  return (
    <main className="flex min-h-screen flex-col sm:grid sm:grid-cols-2">
      {/* Colonne Connexion */}
      <div className=" relative flex flex-col items-center justify-center overflow-hidden bg-ink px-8 py-12 text-center ">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/auth2.png')" }}
        />
        {/*<div className="absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-pitch to-transparent" />*/}
        <div className="absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-ink to-transparent" />
        <div className="absolute inset-0 bg-ink/50" />
        <h2 className="relative z-10 font-display text-3xl text-white">Se connecter</h2>
        <p className="relative z-10 mt-2 font-sans text-white/70">Tu as déjà un compte sur Liga Platform.</p>
        <Link
          href="/auth/login"
          className="relative z-10 mt-6 inline-block rounded-full bg-chalk px-7 py-3 font-sans font-semibold text-ink transition hover:bg-white"
        >
          Continuer
        </Link>
      </div>

      {/* Colonne Inscription */}
      <div className=" relative flex flex-col items-center justify-center overflow-hidden bg-ink px-8 py-12 text-center ">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/auth3.png')" }}
        />
        <div className="absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-ink to-transparent" />
        {/*<div className="absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-ink to-transparent" />*/}
        <div className="absolute inset-0 bg-ink/50" />
        <h2 className="relative z-10 font-display text-3xl text-white">Créer un compte</h2>
        <p className="relative z-10 mt-2 font-sans text-white/70">Nouveau sur Liga Platform ? Crée ton profil joueur.</p>
        <Link
          href="/auth/register"
          className="relative z-10 mt-6 inline-block rounded-full bg-chalk px-7 py-3 font-sans font-semibold text-ink transition hover:bg-white"
        >
          Continuer
        </Link>
      </div>
    </main>
  );
}