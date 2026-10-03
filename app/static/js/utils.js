// Shared helpers loaded on every page (see base.html).

function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, function(match) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[match];
    });
}

// Send the CSRF token (rendered in a <meta> tag by base.html) on every
// same-origin request that changes state.
(function() {
    const originalFetch = window.fetch.bind(window);
    const SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS'];

    window.fetch = function(resource, options = {}) {
        const method = (options.method || 'GET').toUpperCase();
        const url = new URL(resource instanceof Request ? resource.url : resource, window.location.href);
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (!SAFE_METHODS.includes(method) && url.origin === window.location.origin && meta) {
            const headers = new Headers(options.headers || {});
            headers.set('X-CSRFToken', meta.content);
            options = { ...options, headers };
        }
        return originalFetch(resource, options).then(response => {
            if (response.status === 401 && url.origin === window.location.origin) {
                window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
            }
            return response;
        });
    };
})();

// Small non-blocking notification (replaces alert()).
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast align-items-center border-0 text-bg-${type === 'error' ? 'danger' : type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.innerHTML = `<div class="d-flex"><div class="toast-body">${escapeHTML(message)}</div>` +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>';
    container.appendChild(toast);
    const instance = new bootstrap.Toast(toast, { delay: 3500 });
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
    instance.show();
}

// Local YYYY-MM-DD (toISOString() would shift the day in UTC+ timezones).
function isoDate(d) {
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function formatHours(hours) {
    const sign = hours < 0 ? '-' : '';
    const minutes = Math.round(Math.abs(hours) * 60);
    return `${sign}${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}`;
}

// Inline SVG icon from the sprite (same as the icon() Jinja macro).
function icon(name, cls = '') {
    return `<svg class="icon ${cls}" aria-hidden="true" focusable="false"><use href="/static/img/icons.svg#${name}"></use></svg>`;
}

// Light/dark toggle; the initial theme is applied inline in base.html.
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;
    const root = document.documentElement;
    const sync = () => {
        const dark = root.getAttribute('data-bs-theme') === 'dark';
        toggle.setAttribute('aria-label', dark ? toggle.dataset.labelLight : toggle.dataset.labelDark);
        toggle.title = toggle.getAttribute('aria-label');
    };
    toggle.addEventListener('click', () => {
        const next = root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-bs-theme', next);
        try { localStorage.setItem('theme', next); } catch (e) { /* storage unavailable */ }
        sync();
    });
    sync();
});
