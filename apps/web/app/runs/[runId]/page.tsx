import RunDetailPage from './_client/RunDetailPage';

export async function generateStaticParams() {
  return [{ runId: 'demo' }];
}

export default function Page() {
  return <RunDetailPage />;
}
