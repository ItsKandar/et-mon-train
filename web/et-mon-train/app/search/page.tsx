// app/search/page.tsx
'use client'; 
import { useState } from 'react';

export default function SearchPage() {
const [query, setQuery] = useState('');
const [results, setResults] = useState<any[]>([]);
const [loading, setLoading] = useState(false);

const handleSearch = async (e: React.FormEvent) => {
e.preventDefault();
if (!query) return;

setLoading(true);
setResults([]);

try {
  // Appeler l'API interne Next.js
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error(`Erreur lors de la recherche (${response.status})`);
  }
  const data = await response.json();

  // Extraire les "stop_area" uniquement
  const places = data.places || [];
  const stopAreas = places.filter((p: any) => p.embedded_type === 'stop_area');
  setResults(stopAreas);
} catch (error) {
  console.error('Erreur :', error);
  setResults([]);
} finally {
  setLoading(false);
}
};

return (
<section>
  <h1>Recherche de gare</h1>
  <form onSubmit={handleSearch} style={{ marginBottom: '1rem' }}>
    <input
      type="text"
      placeholder="Entrez un nom de gare, ex: Lyon, Paris..."
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      style={{ padding: '0.5rem', width: '200px' }}
    />
    <button type="submit" style={{ marginLeft: '1rem' }}>
      Rechercher
    </button>
  </form>

  {loading && <p>Recherche en cours...</p>}
  {results.length > 0 && (
    <ul>
      {results.map((r: any) => {
        const stopArea = r.stop_area;
        if (!stopArea) return null;

        const { id, name } = stopArea;
        return (
          <li key={id}>
            <strong>{name}</strong> ({id}){' '}
            {/* Lien vers la page dynamique arrivals ou departures */}
            <a href={`/arrivals/${encodeURIComponent(id)}`}>[Voir Arrivées]</a>{' '}
            <a href={`/departures/${encodeURIComponent(id)}`}>[Voir Départs]</a>
          </li>
        );
      })}
    </ul>
  )}
</section>
);
}