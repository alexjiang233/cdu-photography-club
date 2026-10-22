import type { NextConfig } from 'next';
const config: NextConfig = {
  output: 'standalone',
  devIndicators: false,
  skipTrailingSlashRedirect: true,
  async redirects() {
    return [
      { source: '/field-journal', destination: '/', permanent: true },
      { source: '/field-journal/:path*', destination: '/:path*', permanent: true },
      { source: '/events', destination: '/activities', permanent: true },
      { source: '/events/:id', destination: '/activities/:id', permanent: true },
      { source: '/join', destination: '/about', permanent: true },
    ];
  },
  async rewrites() {
    const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      { source: '/api/:path*/', destination: `${backend}/api/:path*/` },
      { source: '/admin/:path*/', destination: `${backend}/admin/:path*/` },
      { source: '/static/:path*', destination: `${backend}/static/:path*` },
    ];
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ];
  },
};
export default config;
