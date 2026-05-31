import { defineCollection, z } from 'astro:content';

// Schema condiviso blog/tutorial — vedi docs/03-STRUTTURA-PROGETTO.md
const baseFields = {
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  category: z.enum(['smartphone', 'pc', 'sicurezza', 'whatsapp', 'app']),
  tags: z.array(z.string()).default([]),
  heroImage: z.string().optional(),
  youtubeId: z.string().optional(),
  // AEO: domande/risposte → FAQPage structured data (vedi docs/10-SEO-AEO.md)
  faq: z
    .array(z.object({ q: z.string(), a: z.string() }))
    .optional(),
  affiliate: z
    .array(
      z.object({
        name: z.string(),
        url: z.string(),
        price: z.string().optional(),
      }),
    )
    .optional(),
  draft: z.boolean().default(false),
};

const blog = defineCollection({ type: 'content', schema: z.object(baseFields) });
const tutorial = defineCollection({ type: 'content', schema: z.object(baseFields) });

export const collections = { blog, tutorial };
