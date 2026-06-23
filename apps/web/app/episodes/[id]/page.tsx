import EpisodePage from './_client/EpisodePage';

export async function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function Page() {
  return <EpisodePage />;
}
