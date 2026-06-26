<?php
/**
 * Updater de theme gateado por licencia (anti-nulled).
 *
 * Engancha el sistema de updates de WordPress para servir actualizaciones SOLO
 * a copias con licencia válida. El paquete se descarga de TU servidor con
 * verificación online + watermark por comprador — una copia nulled no recibe
 * updates (el mayor disuasor real, según EDD/Freemius).
 *
 * Bootstrap (functions.php), después de class-license.php:
 *
 *   $license = new \Pcreative Studio\Licensing\License('__SLUG__');
 *   $theme   = wp_get_theme(get_template());
 *   (new \Pcreative Studio\Licensing\Updater('__SLUG__', $theme->get('Version'), $license))->register();
 *
 * Genérico: el host del API se inyecta de licensing.json. Cada usuario, su backend.
 */

namespace Pcreative Studio\Licensing;

defined('ABSPATH') || exit;

class Updater
{
    /** Endpoint de comprobación de versión (gateado por licencia). */
    const UPDATE_API = '__LICENSE_HOST__/api/update';

    /** Endpoint de descarga del ZIP (valida licencia + inyecta watermark). */
    const DOWNLOAD_API = '__LICENSE_HOST__/api/download';

    /** Cache del check remoto (segundos). */
    const CACHE_TTL = 6 * HOUR_IN_SECONDS;

    private string $product;
    private string $version;
    private string $stylesheet;
    private License $license;

    public function __construct(string $product_slug, string $version, License $license)
    {
        $this->product    = $product_slug;
        $this->version    = $version;
        $this->stylesheet = get_template();
        $this->license    = $license;
    }

    public function register(): void
    {
        add_filter('pre_set_site_transient_update_themes', [$this, 'inject_update']);
        add_filter('themes_api', [$this, 'theme_info'], 20, 3);
        add_action('switch_theme', [$this, 'flush']);
    }

    /** Inyecta la actualización en el transient de WP si hay una versión nueva. */
    public function inject_update($transient)
    {
        if (empty($transient->checked)) {
            return $transient;
        }
        $remote = $this->remote();
        if ($remote && !empty($remote['version']) && version_compare($remote['version'], $this->version, '>')) {
            $transient->response[$this->stylesheet] = [
                'theme'       => $this->stylesheet,
                'new_version' => $remote['version'],
                'url'         => $remote['details_url'] ?? '',
                // Paquete gateado: WP descarga este ZIP (valida licencia + watermark).
                'package'     => $this->package_url(),
                'requires'    => $remote['requires'] ?? '',
                'requires_php'=> $remote['requires_php'] ?? '',
            ];
        }
        return $transient;
    }

    /** Changelog / detalles en la vista "ver detalles". */
    public function theme_info($result, $action, $args)
    {
        if ($action !== 'theme_information' || empty($args->slug) || $args->slug !== $this->stylesheet) {
            return $result;
        }
        $remote = $this->remote();
        if (!$remote) {
            return $result;
        }
        return (object) [
            'name'     => wp_get_theme($this->stylesheet)->get('Name'),
            'slug'     => $this->stylesheet,
            'version'  => $remote['version'] ?? $this->version,
            'sections' => ['changelog' => $remote['changelog'] ?? ''],
        ];
    }

    public function flush(): void
    {
        delete_transient($this->cache_key());
    }

    /** Consulta el servidor de updates. SIN licencia -> sin updates (anti-null). */
    private function remote(): ?array
    {
        $cached = get_transient($this->cache_key());
        if (is_array($cached)) {
            return $cached;
        }
        $key = $this->license->get_key();
        if ($key === '') {
            return null;
        }
        $url = add_query_arg([
            'product' => $this->product,
            'version' => $this->version,
            'key'     => $key,
            'domain'  => $this->host(),
        ], self::UPDATE_API);

        $response = wp_remote_get($url, ['timeout' => 15, 'headers' => ['Accept' => 'application/json']]);
        if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
            return null;
        }
        $data = json_decode(wp_remote_retrieve_body($response), true);
        if (!is_array($data) || empty($data['version'])) {
            return null;
        }
        set_transient($this->cache_key(), $data, self::CACHE_TTL);
        return $data;
    }

    private function package_url(): string
    {
        return add_query_arg([
            'key'     => $this->license->get_key(),
            'product' => $this->product,
            'domain'  => $this->host(),
        ], self::DOWNLOAD_API);
    }

    private function cache_key(): string
    {
        return 'themeforge_update_' . $this->product;
    }

    private function host(): string
    {
        $h = parse_url(home_url(), PHP_URL_HOST) ?: 'localhost';
        return strtolower(preg_replace('/:\d+$/', '', (string)$h));
    }
}
