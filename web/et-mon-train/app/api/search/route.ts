// app/api/search/route.ts
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
const { searchParams } = new URL(request.url);
const query = searchParams.get('q');

if (!query) {
return NextResponse.json({ error: 'Paramètre "q" manquant' }, { status: 400 });
}

try {
const SNCF_API_KEY = process.env.SNCF_API_KEY;
const apiUrl = `https://api.sncf.com/v1/coverage/sncf/places?q=${encodeURIComponent(query)}`;
const response = await fetch(apiUrl, {
  headers: {
    Authorization: 'Basic ' + Buffer.from(SNCF_API_KEY + ':').toString('base64'),
  },
});

if (!response.ok) {
  return NextResponse.json(
    { error: `Erreur SNCF: ${response.status} ${response.statusText}` },
    { status: response.status }
  );
}

const data = await response.json();
return NextResponse.json(data);
} catch (error: any) {
console.error(error);
return NextResponse.json({ error: error.message }, { status: 500 });
}
}