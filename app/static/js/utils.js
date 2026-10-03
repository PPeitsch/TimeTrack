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
