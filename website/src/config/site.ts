const configuredDownloadUrl = import.meta.env.PUBLIC_DOWNLOAD_URL?.trim();

export const site = {
  name: 'HoN Reborn RU',
  title: 'HoN Reborn на русском — русификатор HoN Reborn',
  description:
    'Русская локализация HoN Reborn. Скачайте русификатор и запускайте игру на русском языке.',
  canonicalUrl: 'https://honreborn.ru',
  downloadUrl: configuredDownloadUrl || null,
} as const;
