const configuredDownloadUrl = import.meta.env.PUBLIC_DOWNLOAD_URL?.trim();
const latestSetupUrl =
  'https://github.com/jlambo12/HoN-Reborn-Ru/releases/download/v0.1.0-beta.19/HoNRebornRU-Setup.exe';

export const site = {
  name: 'HoN Reborn RU',
  title: 'HoN Reborn на русском — русификатор HoN Reborn',
  description:
    'Русская локализация HoN Reborn. Скачайте русификатор и запускайте игру на русском языке.',
  canonicalUrl: 'https://honreborn.ru',
  downloadUrl: configuredDownloadUrl || latestSetupUrl,
} as const;
