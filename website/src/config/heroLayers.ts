export interface HeroImageLayer {
  name: string;
  src: string;
  depth: number;
  position?: string;
}

/**
 * Only files that actually exist belong in this array, so the page never emits
 * requests for unfinished artwork. Add future transparent layers here as they
 * arrive; HeroParallax renders them in array order.
 */
export const heroImageLayers: HeroImageLayer[] = [
  {
    name: 'caldavar',
    src: '/hero/caldavar-official.webp',
    depth: 0.7,
    position: 'center 52%',
  },
];

/** Planned filenames for the final multi-layer Caldavar composition. */
export const plannedHeroLayers = [
  'sky.webp',
  'mountains.webp',
  'base.webp',
  'ruins.webp',
  'foreground.webp',
  'fog-back.webp',
  'fog-front.webp',
  'legion-glow.webp',
  'hellbourne-glow.webp',
  'particles.webp',
] as const;
