// app/departures/[stopAreaId]/page.tsx

interface DeparturesPageProps {
params: {
    stopAreaId: string;
};
}

export default async function DeparturesPage({ params }: DeparturesPageProps) {
const { stopAreaId } = params;
const SNCF_API_KEY = process.env.SNCF_API_KEY;

const url = `https://api.sncf.com/v1/coverage/sncf/${stopAreaId}/departures?count=10`;
const response = await fetch(url, {
    headers: {
    Authorization: 'Basic ' + Buffer.from(SNCF_API_KEY + ':').toString('base64'),
    },
    cache: 'no-store',
});

if (!response.ok) {
    throw new Error(`Erreur API SNCF: ${response.status} ${response.statusText}`);
}

const data = await response.json();
const departures = data.departures || [];

return (
    <section>
    <h1>Départs pour la gare : {stopAreaId}</h1>
    <ul>
        {departures.map((dep: any) => {
        const { id } = dep;
        const train = dep.display_informations.headsign;
        const direction = dep.display_informations.direction;
        const departureTime = dep.stop_date_time.departure_date_time;

        return (
            <li key={id}>
            <strong>Train {train}</strong> → {direction} <br />
            Départ prévu : {departureTime}
            </li>
        );
        })}
    </ul>
    </section>
);
}  