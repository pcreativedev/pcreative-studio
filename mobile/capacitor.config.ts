import type { CapacitorConfig } from '@capacitor/cli';

/**
 * App nativa que envuelve la PWA de Pcreative Studio (webui/mobile).
 * La URL del gateway + token los mete el usuario en la pantalla de config
 * (se guardan en localStorage), así que NO se hardcodean aquí.
 *
 * `www/` se genera con `npm run sync-web` (copia webui/mobile + el shim remoto).
 */
const config: CapacitorConfig = {
  appId: 'dev.pcreative.themeforge',
  appName: 'Pcreative Studio',
  webDir: 'www',
  plugins: {
    PushNotifications: { presentationOptions: ['badge', 'sound', 'alert'] },
    SplashScreen: { launchShowDuration: 800, backgroundColor: '#0b0e14' },
  },
  // Para desarrollo con live-reload contra la PWA servida en tu portátil:
  // server: { url: 'http://100.x.x.x:8080/mobile/', cleartext: true },
};

export default config;
