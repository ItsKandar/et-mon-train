// app/arrivals/[stopAreaId]/page.tsx
export const dynamic = 'force-dynamic'; // 1) On force le rendu dynamique

interface ArrivalsPageProps {
params: {
stopAreaId: string;
};
}

export default async function ArrivalsPage({ params }: ArrivalsPageProps) {
// 2) Décoder pour enlever les %3A
const decodedStopAreaId = decodeURIComponent(params.stopAreaId);

const SNCF_API_KEY = process.env.SNCF_API_KEY;
const url = `https://api.sncf.com/v1/coverage/sncf/${decodedStopAreaId}/arrivals?count=10`;

const response = await fetch(url, {
headers: {
    Authorization: 'Basic ' + Buffer.from(SNCF_API_KEY + ':').toString('base64'),
},
cache: 'no-store', // ou vous pouvez paramétrer revalidate
});

if (!response.ok) {
throw new Error(`Erreur API SNCF: ${response.status} ${response.statusText}`);
}

const data = await response.json();
const arrivals = data.arrivals || [];

return (
<section>
    <h1>Arrivées pour la gare : {decodedStopAreaId}</h1>
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