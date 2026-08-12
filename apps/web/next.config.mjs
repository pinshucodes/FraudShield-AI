/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'http://127.0.0.1:8000/api/v1'}/:path*`, // Proxy to FastAPI backend
      },
    ]
  },
};

export default nextConfig;
