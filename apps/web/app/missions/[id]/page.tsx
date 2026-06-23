import MissionTracePage from './_client/MissionTracePage';

export async function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function Page() {
  return <MissionTracePage />;
}
