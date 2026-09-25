"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";


export default function RegisterPage() {
  const [formData, setFormData] = useState({ username: "", email: "", password: "" });
  const [errorMessage, setErrorMessage] = useState("");
  const router = useRouter();
  function handleChanges(e) {
  const changes = e.target.name
  const nouvelleValeur = e.target.value;
  const nouvelObjet = { ...formData, [changes]: nouvelleValeur };
  
  setFormData(nouvelObjet);
  }

  async function handleSubmit(e) {
  setErrorMessage("");
  e.preventDefault();
  
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  });
  
if (response.ok) {
  const data = await response.json();
  console.log(data); // pour l'instant, juste vérifier que ça marche
  router.push("/dashboard");
} else {
  const errorData = await response.json();
  setErrorMessage(errorData.detail);
  console.error("Erreur lors de l'inscription :", errorData.detail);
}
}


  return (
    <main className="mx-auto flex min-h-screen flex-col items-center justify-center text-center">
      <div className=" relative h-screen bg-cover  px-6 w-full">
        <div
          className="absolute inset-0 bg-cover bg-[center_35%] bg-no-repeat"
          style={{ backgroundImage: "url('/auth3.png')" }}
        />
        <div className="absolute inset-0 bg-ink/50" />
        <div className="absolute inset-y-0 left-0 w-full max-w-md backdrop-blur-md bg-ink/40 flex flex-col items-center justify-center px-8">
        <section className="max-w-md">
        <h1 className="relative z-10 font-display text-3xl text-white">Créer un compte</h1>
        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        {errorMessage && (
          <div className="relative z-10 text-sm text-orange-500">
            <p>{errorMessage}</p>
          </div>
        )}
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="username" value={formData.username} onChange={handleChanges} placeholder="Nom d'utilisateur" required />
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="email" value={formData.email} onChange={handleChanges} placeholder="Email" required />
        <input className="relative z-10 w-full rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-white placeholder:text-white/50 backdrop-blur-sm focus:border-white/60 focus:outline-none" name="password" type="password" value={formData.password} onChange={handleChanges} placeholder="Mot de passe" required />
        <button className="relative z-10 mt-2 inline-block rounded-full bg-chalk px-7 py-3 font-sans font-semibold text-ink transition hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-white/70" type="submit">Continuer</button>
        </form>
        </section>
        </div>
        <Link href="/" className="z-10 absolute top-8 left-8 font-display text-3xl text-white "> Liga Platform</Link>
      </div>
    </main>
  );
}