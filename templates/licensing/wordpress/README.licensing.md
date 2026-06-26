# License integration — WordPress (plugin/theme)

Este proyecto trae preconfigurada la integración con el sistema de
sistema de licencias en **__LICENSE_HOST_BARE__**.

## Archivos generados

- `inc/class-license.php` — clase verificadora de licencias (llama a
  `__LICENSE_API_URL__`).
- `inc/admin-license-page.php` — página de admin para introducir/
  activar/desactivar la clave.

## Cómo cablearlo

En el archivo principal del plugin o `functions.php` del theme:

```php
require_once __DIR__ . '/inc/class-license.php';
require_once __DIR__ . '/inc/admin-license-page.php';

$license = new \Pcreative Studio\Licensing\License('__SLUG__');

add_action('admin_menu', function () use ($license) {
    licensing_register_admin_page($license, '__PROJECT__');
});

if (!$license->is_active() && is_admin()) {
    add_action('admin_notices', [$license, 'render_inactive_notice']);
}
```

## Slug

Este theme/plugin se identifica con el slug **`__SLUG__`** en la API
de licencias. Asegúrate de que aparece en el catálogo de productos de
tu panel admin antes de generar el ZIP de distribución.

## Documentación canónica

Ver `context/LICENSING-SYSTEM.md` para el modelo completo.
