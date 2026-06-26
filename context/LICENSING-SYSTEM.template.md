# Sistema de licencias propio (template)

Plantilla pública. Stub neutro.

Pcreative Studio soporta opcionalmente integrar cada theme generado con un
sistema de licencias del autor (verificación remota de purchase code,
setup wizard, panel admin). El módulo
`licensing_scaffold.py`* implementa este patrón para el sistema del
autor original; tú puedes:

  · **Usarlo tal cual** si te montas un endpoint público de verificación
    compatible.
  · **Adaptarlo** a tu propio servicio (Lemon Squeezy, Polar, Paddle,
    Gumroad License API, etc.) reescribiendo el endpoint del wrapper.
  · **Desactivarlo** (checkbox "🔑 Activar sistema de licencias" OFF en la UI).

Si quieres que el agente IA del proyecto entienda TU sistema concreto
(URL del endpoint, formato de keys, tipos de licencia, slugs en uso,
panel admin), crea tu versión privada en:

    ~/.config/themeforge/context-private/LICENSING-SYSTEM.md

Pcreative Studio la priorizará. Tu versión privada va a quedar fuera del repo
público (`.gitignore`).

*nota: el módulo se llama `licensing_scaffold.py` y los templates
viven en `templates/licensing/`. Si forkeas y prefieres tu propio
naming, son nombres aislados — solo hay que renombrar el módulo + dir
y actualizar los imports.

## Qué debería contener tu versión privada

1. URL pública del endpoint de verify (`https://midominio.com/api/license/verify`).
2. URL admin / Bearer token (NO el token en sí — el token va en `.env`
   o config, no en este MD).
3. Formato de las purchase keys.
4. Tabla de tipos: `regular`, `pro`, `extended`, `developer` con
   `max_domains` por tipo.
5. Lista de slugs de productos en uso (uno por línea).
6. Patrón estándar de integración en cada theme.

**No metas secrets reales en esta plantilla pública.** Los secrets van
solo en tu versión privada.
