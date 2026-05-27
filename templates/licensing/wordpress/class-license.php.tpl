<?php
/**
 * License client for WordPress themes/plugins — port PHP de
 * @pcreative/license-client.
 *
 * Esquema (anti-nulled): activación remota -> JWT firmado RS256 -> verificación
 * OFFLINE con la clave pública embebida (sin llamar al servidor en cada carga)
 * -> heartbeat de renovación. El binding de dominio y el watermark van dentro
 * del JWT firmado, así que no se pueden falsificar sin la clave privada.
 *
 * Uso desde el bootstrap del theme/plugin:
 *
 *   require_once __DIR__ . '/inc/class-license.php';
 *   $license = new \ThemeForge\Licensing\License('__SLUG__');
 *   if (!$license->is_active()) {
 *       add_action('admin_notices', [$license, 'render_inactive_notice']);
 *   }
 *
 * Genérico: la URL de activación, la clave pública y el issuer se inyectan al
 * generar el proyecto (de tu licensing.json). Cada usuario usa SU backend.
 */

namespace ThemeForge\Licensing;

defined('ABSPATH') || exit;

class License
{
    /** Endpoint público de activación (devuelve un JWT firmado). */
    const API_URL = '__LICENSE_API_URL__';

    /** Clave pública RS256 (PEM) para verificar los JWT offline. NO secreta. */
    const PUBLIC_KEY = "__LICENSE_PUBKEY__";

    /** Issuer esperado en el claim `iss`. */
    const ISSUER = '__LICENSE_ISSUER__';

    /** Días antes de la expiración del JWT en que se intenta renovar. */
    const RENEW_BEFORE_DAYS = 5;

    private string $product;
    private string $option_key;

    public function __construct(string $product_slug)
    {
        $this->product    = $product_slug;
        $this->option_key = "themeforge_license_{$product_slug}";
    }

    // ── Estado ────────────────────────────────────────────────────────────

    /** Verifica OFFLINE el JWT guardado. Renueva en background si caduca pronto. */
    public function is_active(): bool
    {
        $jwt = (string)($this->get_state()['jwt'] ?? '');
        if ($jwt === '') {
            return false;
        }
        $payload = $this->verify_jwt($jwt);
        if ($payload === null) {
            return false;
        }
        $exp = (int)($payload['exp'] ?? 0);
        if ($exp - time() < self::RENEW_BEFORE_DAYS * DAY_IN_SECONDS) {
            $this->maybe_schedule_heartbeat();
        }
        return true;
    }

    public function get_state(): array
    {
        $state = get_option($this->option_key, []);
        return is_array($state) ? $state : [];
    }

    public function get_key(): string
    {
        return (string)($this->get_state()['license_key'] ?? '');
    }

    /** Datos del JWT verificado (type, domain, watermark, email, exp…) o []. */
    public function info(): array
    {
        $jwt = (string)($this->get_state()['jwt'] ?? '');
        return $jwt ? ($this->verify_jwt($jwt) ?? []) : [];
    }

    // ── Activación / heartbeat ──────────────────────────────────────────────

    public function activate(string $key): array
    {
        $key = trim($key);
        $response = wp_remote_post(self::API_URL, [
            'timeout' => 15,
            'headers' => ['Content-Type' => 'application/json'],
            'body'    => wp_json_encode([
                'license_key' => $key,
                'product'     => $this->product,
                'domain'      => $this->host(),
            ]),
        ]);

        if (is_wp_error($response)) {
            return ['valid' => false, 'error' => 'License server unreachable.'];
        }

        $body = json_decode(wp_remote_retrieve_body($response), true);
        if (!is_array($body)) {
            return ['valid' => false, 'error' => 'Bad response from license server.'];
        }
        if (empty($body['valid']) || empty($body['jwt'])) {
            return ['valid' => false, 'error' => (string)($body['error'] ?? 'Invalid license.')];
        }

        // El servidor dice "valid", pero confiamos en la FIRMA, no en el flag.
        $payload = $this->verify_jwt((string)$body['jwt']);
        if ($payload === null) {
            return ['valid' => false, 'error' => 'License signature could not be verified.'];
        }

        update_option($this->option_key, [
            'jwt'            => (string)$body['jwt'],
            'license_key'    => $key,
            'last_heartbeat' => time(),
        ]);

        return ['valid' => true] + $payload;
    }

    /** Re-activa con la key guardada para renovar el JWT (lo llama wp-cron). */
    public function heartbeat(): void
    {
        $key = $this->get_key();
        if ($key !== '') {
            $this->activate($key);
        }
    }

    public function deactivate(): void
    {
        delete_option($this->option_key);
    }

    private function maybe_schedule_heartbeat(): void
    {
        $hook = "themeforge_license_heartbeat_{$this->product}";
        add_action($hook, [$this, 'heartbeat']);
        if (!wp_next_scheduled($hook)) {
            wp_schedule_single_event(time() + 60, $hook);
        }
    }

    // ── Verificación JWT offline (RS256 vía openssl) ────────────────────────

    private function verify_jwt(string $jwt): ?array
    {
        $parts = explode('.', $jwt);
        if (count($parts) !== 3) {
            return null;
        }
        [$h64, $p64, $s64] = $parts;

        $header = json_decode($this->b64url_decode($h64), true);
        if (!is_array($header) || ($header['alg'] ?? '') !== 'RS256') {
            return null;
        }
        $payload = json_decode($this->b64url_decode($p64), true);
        if (!is_array($payload)) {
            return null;
        }
        $signature = $this->b64url_decode($s64);

        // Firma
        $ok = openssl_verify("{$h64}.{$p64}", $signature, self::PUBLIC_KEY, OPENSSL_ALGO_SHA256);
        if ($ok !== 1) {
            return null;
        }
        // Claims
        if ((string)($payload['iss'] ?? '') !== self::ISSUER) {
            return null;
        }
        if ((string)($payload['aud'] ?? '') !== $this->product) {
            return null;
        }
        if ((int)($payload['exp'] ?? 0) < time()) {
            return null;
        }
        // Binding de dominio (salvo licencia extended)
        if (empty($payload['extended'])) {
            $bound = strtolower((string)($payload['domain'] ?? ''));
            if ($bound !== '' && $bound !== $this->host()) {
                return null;
            }
        }
        return $payload;
    }

    private function b64url_decode(string $s): string
    {
        $pad = strlen($s) % 4;
        if ($pad) {
            $s .= str_repeat('=', 4 - $pad);
        }
        return (string)base64_decode(strtr($s, '-_', '+/'));
    }

    // ── UI ──────────────────────────────────────────────────────────────────

    public function render_inactive_notice(): void
    {
        $url = admin_url('admin.php?page=' . $this->product . '-license');
        ?>
        <div class="notice notice-warning">
            <p><strong><?php echo esc_html($this->product); ?></strong>:
            <?php esc_html_e('license not active.', '__SLUG__'); ?>
            <a href="<?php echo esc_url($url); ?>"><?php esc_html_e('Activate your license', '__SLUG__'); ?></a>.</p>
        </div>
        <?php
    }

    private function host(): string
    {
        $h = parse_url(home_url(), PHP_URL_HOST) ?: 'localhost';
        return strtolower(preg_replace('/:\d+$/', '', (string)$h));
    }
}
