"use client";
import {usePathname} from "next/navigation";
import Link from "next/link";

export default function SiteHeader() {
    const pathname = usePathname();
    if (pathname.startsWith("/auth")) {
        return null;
    }
    else {
        return (<header className="mx-auto flex max-w-5xl items-center justify-center px-6 py-6">
          <Link href="/" className="font-display text-2xl text-ink">Liga Platform</Link>
        </header>)
    };
}
