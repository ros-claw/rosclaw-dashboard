/** @type {import('next').NextConfig} */
const isStaticExport = process.env.DASHBOARD_STATIC_EXPORT === '1';

const nextConfig = {
  output: isStaticExport ? 'export' : 'standalone',
  distDir: isStaticExport ? '../api/src/rosclaw_dashboard/static' : '.next',
  allowedDevOrigins: ['127.0.0.1'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8001/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
