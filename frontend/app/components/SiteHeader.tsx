"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "./AuthProvider";

export default function SiteHeader() {
  const pathname = usePathname();
  const { accessToken, logout } = useAuth();

  if (pathname.startsWith("/auth")) {
    return null;
  }

  return (
    <header className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
      <Link href="/" className="font-display text-2xl text-ink">Liga Platform</Link>
      {accessToken && (
        <button
          onClick={logout}
          className="rounded-full bg-ink px-4 py-2 font-sans font-semibold text-chalk transition hover:bg-red-600 hover:text-white"
        >
          Se déconnecter
        </button>
      )}
    </header>
  );
}
