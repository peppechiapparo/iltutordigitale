// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';

// URL del sito: in produzione viene da PUBLIC_SITE_URL (Cloudflare/GitHub).
const site = process.env.PUBLIC_SITE_URL ?? 'https://tutordigitale.com';

// https://astro.build/config
export default defineConfig({
  site,
  integrations: [tailwind(), sitemap(), react()],
  output: 'static',
});
