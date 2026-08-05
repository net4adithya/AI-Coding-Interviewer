// prisma/prisma.config.ts
// Stub configuration file to satisfy imports expecting 'defineConfig' and 'env'.
// This mirrors the existing CommonJS configuration in prisma.config.cjs.

export const defineConfig = (config: Record<string, any>) => config;
export const env = process.env;

// You can also export the full configuration object if needed:
export const config = {
  schema: "./prisma/schema.prisma",
  datasource: {
    url: process.env.DATABASE_URL,
    provider: "postgresql",
  },
};
