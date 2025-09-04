/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
import "./src/env.js";

/** @type {import("next").NextConfig} */
const nextConfig = {
  experimental: {
    externalDir: true, // allow importing from ../../packages
  },
  transpilePackages: ["@sam-chat/locations"], // transpile TS source from the package
};
export default nextConfig;
