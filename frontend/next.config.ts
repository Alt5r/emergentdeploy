import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'media.giphy.com',
      },
    ],
  },
  output: 'standalone',
  webpack: (config) => {
    // Cesium configuration
    config.module = config.module || {};
    config.module.unknownContextCritical = false;
    config.module.unknownContextRegExp = /\/cesium\/cesium\/Source\/Core\/buildModuleUrl\.js/;

    return config;
  },
};

export default nextConfig;
