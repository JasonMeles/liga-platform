import Link from "next/link";

export default function Home() {
  return (
    <>
      <section
        className="relative h-[640px] bg-cover bg-[center_35%] px-6"
        style={{ backgroundImage: "url('/landing.png')" }}
      >
        <div className="hero-copy absolute left-1/2 top-[33%] w-[88%] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-3xl bg-ink/55 px-6 py-6 text-center backdrop-blur-sm sm:px-10 sm:py-7">
          <h1 className="font-display text-4xl leading-[0.95] text-white sm:text-6xl">
            Deux sports.<br />Un seul terrain.
          </h1>
          <p className="mx-auto mt-4 max-w-lg font-sans text-lg text-white/90">
            Crée ta ligue FIFA ou NBA 2K, laisse le calendrier se générer automatiquement.
          </p>
          <Link href="/auth" className="mt-6 inline-block rounded-full bg-chalk px-7 py-3 font-sans font-semibold text-ink transition hover:bg-white">
            Créer / rejoindre la ligue
          </Link>
        </div>
      </section>

      <div className="overflow-hidden border-y border-line bg-ink py-3">
        <div className="ticker-track flex w-max gap-10 whitespace-nowrap font-sans text-sm font-semibold uppercase tracking-wide text-gold">
          {[0, 1].map((i) => (
            <span key={i} className="flex items-center gap-10">
              <span>2 sports — football & basket</span><span>•</span>
              <span>classements en temps réel</span><span>•</span>
              <span>calendriers générés automatiquement</span><span>•</span>
              <span>conférences de presse entre joueurs</span><span>•</span>
            </span>
          ))}
        </div>
      </div>

      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="grid gap-8 sm:grid-cols-3">
          <article className="border-l-4 border-pitch pl-5">
            <h3 className="font-display text-2xl text-ink">Classements</h3>
            <p className="mt-2 font-sans text-ink/75">Chaque victoire compte : ton classement se met à jour à la fin de chaque journée, saison après saison.</p>
          </article>
          <article className="border-l-4 border-hardwood pl-5">
            <h3 className="font-display text-2xl text-ink">Calendrier automatique</h3>
            <p className="mt-2 font-sans text-ink/75">Le calendrier s'organise seul, journée par journée, en évitant que tu affrontes toujours les mêmes adversaires.</p>
          </article>
          <article className="border-l-4 border-gold pl-5">
            <h3 className="font-display text-2xl text-ink">Vestiaire & conférences de presse</h3>
            <p className="mt-2 font-sans text-ink/75">Discute avec les autres joueurs de ta ligue dans un espace pensé comme une vraie conférence de presse d'après-match.</p>
          </article>
        </div>
      </section>

      <section id="comment-ca-marche" className="border-t border-line py-24">
        <div className="mx-auto max-w-3xl px-6">
          <h2 className="font-display text-3xl text-ink">Comment ça marche</h2>
          <ol className="mt-10 space-y-8">
            <li className="flex gap-5">
              <span className="font-display text-3xl text-ink/25">1</span>
              <p className="pt-1 font-sans text-ink/85">Crée ta ligue ou rejoins-en une avec un code d'invitation.</p>
            </li>
            <li className="flex gap-5">
              <span className="font-display text-3xl text-ink/25">2</span>
              <p className="pt-1 font-sans text-ink/85">Réclame ton équipe : le calendrier se génère automatiquement.</p>
            </li>
            <li className="flex gap-5">
              <span className="font-display text-3xl text-ink/25">3</span>
              <p className="pt-1 font-sans text-ink/85">Joue tes matchs, publie les scores, grimpe au classement.</p>
            </li>
          </ol>
        </div>
      </section>

      <footer className="border-t border-line px-6 py-8">
        <p className="mx-auto max-w-5xl font-sans text-sm text-ink/60">Liga Platform — fait par des joueurs, pour des joueurs.</p>
      </footer>
    </>
  );
}