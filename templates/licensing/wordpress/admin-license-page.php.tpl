<?php
/**
 * License admin settings page for WordPress plugins/themes.
 *
 * Usage from the plugin/theme bootstrap:
 *
 *   require_once __DIR__ . '/inc/class-license.php';
 *   require_once __DIR__ . '/inc/admin-license-page.php';
 *   add_action('admin_menu', function () {
 *       $license = new \ThemeForge\Licensing\License('__SLUG__');
 *       licensing_register_admin_page($license, '__PROJECT__');
 *   });
 */

defined('ABSPATH') || exit;

function licensing_register_admin_page(\ThemeForge\Licensing\License $license, string $product_name): void
{
    add_menu_page(
        $product_name . ' License',
        $product_name,
        'manage_options',
        '__SLUG__-license',
        function () use ($license, $product_name) {
            licensing_render_admin_page($license, $product_name);
        },
        'dashicons-admin-network',
        80
    );
}

function licensing_render_admin_page(\ThemeForge\Licensing\License $license, string $product_name): void
{
    if (!current_user_can('manage_options')) {
        wp_die('Forbidden');
    }

    $notice = '';
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && check_admin_referer('licensing_save')) {
        $key = sanitize_text_field($_POST['license_key'] ?? '');
        $action = sanitize_text_field($_POST['action_type'] ?? 'activate');

        if ($action === 'deactivate') {
            $license->deactivate();
            $notice = 'License deactivated.';
        } elseif ($key) {
            $res = $license->activate($key);
            $notice = $res['valid'] ? 'License activated.' : ('Error: ' . ($res['error'] ?? 'Unknown'));
        }
    }

    $active = $license->is_active();
    $info = $active ? $license->info() : [];
    $current_key = $license->get_key();
    ?>
    <div class="wrap">
        <h1><?php echo esc_html($product_name); ?> — License</h1>
        <?php if ($notice): ?>
            <div class="notice notice-info"><p><?php echo esc_html($notice); ?></p></div>
        <?php endif; ?>

        <form method="post">
            <?php wp_nonce_field('licensing_save'); ?>
            <table class="form-table">
                <tr>
                    <th>Status</th>
                    <td>
                        <?php if ($active): ?>
                            <span style="color:#0a0">✓ Active</span>
                            (<?php echo esc_html((string)($info['type'] ?? '—')); ?><?php
                                echo !empty($info['extended'])
                                    ? ' · all domains'
                                    : ' · ' . esc_html((string)($info['domain'] ?? '')); ?><?php
                                if (!empty($info['exp'])) {
                                    echo ' · expires ' . esc_html(date_i18n(get_option('date_format'), (int)$info['exp']));
                                } ?>)
                        <?php else: ?>
                            <span style="color:#c00">✗ Inactive</span>
                        <?php endif; ?>
                    </td>
                </tr>
                <tr>
                    <th><label for="license_key">License key</label></th>
                    <td>
                        <input type="text" id="license_key" name="license_key" class="regular-text"
                               value="<?php echo esc_attr($current_key); ?>"
                               placeholder="XXXX-XXXX-XXXX-XXXX">
                    </td>
                </tr>
            </table>
            <p class="submit">
                <button type="submit" name="action_type" value="activate" class="button button-primary">
                    <?php echo $active ? 'Update license' : 'Activate'; ?>
                </button>
                <?php if ($active): ?>
                    <button type="submit" name="action_type" value="deactivate" class="button">
                        Deactivate
                    </button>
                <?php endif; ?>
            </p>
        </form>
    </div>
    <?php
}
