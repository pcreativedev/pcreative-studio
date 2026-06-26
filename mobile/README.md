# Pcreative Studio Móvil — app nativa (Capacitor)

Envuelve la PWA de `webui/mobile` en una app nativa Android/iOS. Aporta sobre la
PWA: **push notifications fiables** (FCM/APNs), splash, e instalación como app.
La cámara para el OCR de cartas ya funciona vía WebView (`<input capture>`), no
necesita plugin.

> El motor (scaffold, agentes, Docker) **no** va en el móvil: la app es un
> cliente del **gateway** (`api_gateway.py`) corriendo en tu VPS/portátil.
> Recomendado acceder por **Tailscale**.

## Requisitos
- Node 20+, y **Android Studio** (Android) y/o **Xcode** (iOS).
- El gateway corriendo: `uvicorn api_gateway:app --host 0.0.0.0 --port 8765`.

## Build Android
```bash
cd mobile
npm install
npm run add:android          # genera www/ + crea el proyecto android/
# Firebase: crea un proyecto, baja google-services.json → android/app/
npm run android              # sync + abre Android Studio → Run
```

## Build iOS
```bash
cd mobile
npm install
npm run add:ios
# APNs: configura el certificado/clave de push en tu cuenta de Apple Developer
npm run ios                  # sync + abre Xcode → Run
```

## Push "build terminado" (FCM)
1. **Servidor:** descarga el *service account* JSON de tu proyecto Firebase y
   ponlo en `~/.config/themeforge/fcm-service-account.json` (o exporta
   `GOOGLE_APPLICATION_CREDENTIALS`). Comprueba: `GET /push/status`.
2. **App:** al abrir, `native.js` pide permiso, registra el token y lo manda a
   `POST /push/register`.
3. **Probar:** `POST /push/test` → debería llegarte una push.
4. La entrega real de "build terminado" se enganchará cuando los builds corran
   en el servidor (Fase 3): `push_service.send("Pcreative Studio", "Build terminado ✅")`.

## Desarrollo rápido (live-reload)
En `capacitor.config.ts` descomenta `server.url` apuntando a la PWA servida en tu
portátil (`python -m http.server 8080` desde `webui/`), y la app cargará en vivo
sin reempaquetar.

## Estructura
- `www/` — generado por `npm run sync-web` (copia `webui/mobile` + el shim
  `webui/remote/tfbridge-remote.js` + `native.js`). **No se commitea.**
- `native.js` — registro de push (solo activo en nativo).
- `capacitor.config.ts` — appId `dev.pcreative.themeforge`, webDir `www`.
