"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("Chargement...");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((response) => response.json())
      .then((data) => setMessage(data.status))
      .catch((error) => setMessage("Erreur : " + error.message));
  }, []);

  return (
    <div>
      <h1>Test de connexion Backend/Frontend</h1>
      <p>Statut du backend : {message}</p>
    </div>
  );
}