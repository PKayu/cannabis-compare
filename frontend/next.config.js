/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Standalone output is required by frontend/Dockerfile (copies only necessary
  // files into the runtime image) but breaks Vercel, which expects its own
  // build output format and silently serves nothing if given a standalone build.
  // Vercel sets VERCEL=1 during its builds, so only apply this for Docker.
  ...(process.env.VERCEL ? {} : { output: 'standalone' }),
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // unsafe-eval needed by Next.js dev
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https:",
              "font-src 'self'",
              "connect-src 'self' https://*.supabase.co https://*.supabase.io " +
                (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'),
              "frame-ancestors 'none'",
            ].join('; '),
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
