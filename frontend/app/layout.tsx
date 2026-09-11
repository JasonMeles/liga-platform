import type { Metadata } from "next";
import { Anton, Manrope } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const anton = Anton({ subsets: ["latin"], weight: "400", variable: "--font-anton" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });

export const metadata: Metadata = {
  title: "Liga Platform",
  description: "La plateforme de ligues gaming multi-sport — football et basket.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr" className={`${anton.variable} ${manrope.variable}`}>
      <body className="min-h-screen bg-chalk font-sans text-ink antialiased">
        <header className="mx-auto flex max-w-5xl items-center justify-center px-6 py-6">
          <Link href="/" className="font-display text-2xl text-ink">Liga Platform</Link>
        </header>
        {children}
      </body>
    </html>
  );
}