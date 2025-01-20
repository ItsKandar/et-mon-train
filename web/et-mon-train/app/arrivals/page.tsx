// app/arrivals/page.tsx

export default async function ArrivalsPage() {
const SNCF_API_KEY = process.env.SNCF_API_KEY;
const defaultStopAreaId = 'stop_area:SNCF:87171009'; // Reims
const url = `https://api.sncf.com/v1/coverage/sncf/${defaultStopAreaId}/arrivals?count=10`;

const response = await fetch(url, {
  headers: {
    Authorization: 'Basic ' + Buffer.from(SNCF_API_KEY + ':').toString('base64'),
},
  // cache: 'no-store', // si on veut refetch à chaque fois
  // ou revalidate: 60 (voir plus bas)
});

if (!response.ok) {
  throw new Error(`Erreur API SNCF: ${response.status} ${response.statusText}`);
}

const data = await response.json();
const arrivals = data.arrivals || [];

return (
  <section>
    <h1>Arrivées – Reims</h1>
    <ul>
      {arrivals.map((arrival: any) => {
        const { id } = arrival;
        const train = arrival.display_informations.headsign;
        const from = arrival.display_informations.direction;
        const arrivalTime = arrival.stop_date_time.arrival_date_time;

        return (
          <li key={id}>
            <strong>Train {train}</strong> (Provenance : {from}) <br />
            Arrivée prévue : {arrivalTime}
          </li>
        );
      })}
    </ul>
  </section>
);
}  