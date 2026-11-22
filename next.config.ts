import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  outputFileTracingIncludes: {
    "/api/analyze": ["./decision_engine/**/*.py", "./examples/problems.json"],
  },
};

export default nextConfig;
