import RunReportPage from './_client/RunReportPage';

export async function generateStaticParams() {
  return [{ runId: 'demo' }];
}

export default function Page() {
  return <RunReportPage />;
}
