import RobotDetailPage from './_client/RobotDetailPage';

export async function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function Page() {
  return <RobotDetailPage />;
}
