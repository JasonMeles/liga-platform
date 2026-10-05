import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";

type AuthMode = "protected" | "guest";

export function useRequireAuth(mode: AuthMode): boolean {
  const { accessToken } = useAuth();
  const router = useRouter();

  const isLoggedIn = !!accessToken;

  // protected : on redirige si PAS connecté
  // guest     : on redirige si DÉJÀ connecté
  const mustRedirect = mode === "protected" ? !isLoggedIn : isLoggedIn;
  const destination = mode === "protected" ? "/auth/login" : "/dashboard";

  useEffect(() => {
    if (mustRedirect) {
      router.replace(destination);
    }
  }, [mustRedirect, destination, router]);

  return !mustRedirect;
}