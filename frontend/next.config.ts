import type { NextConfig } from "next";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  outputFileTracingRoot: dirname(fileURLToPath(import.meta.url)),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
