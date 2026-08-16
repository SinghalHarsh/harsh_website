/* Single fetch wrapper for every AJAX call on the site. */

const AJAX_HEADER = { 'X-Requested-With': 'XMLHttpRequest' };

async function request(url, options = {}) {
    const response = await fetch(url, { ...options, headers: { ...AJAX_HEADER, ...options.headers } });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    const type = response.headers.get('content-type') || '';
    return type.includes('application/json') ? response.json() : response.text();
}

window.api = {
    get: (url) => request(url),

    /** POST form-encoded data — matches the Flask routes' request.form. */
    post: (url, data = {}) => request(url, {
        method: 'POST',
        body: new URLSearchParams(data),
    }),

    /** POST JSON — for routes reading request.get_json(). */
    postJson: (url, data = {}) => request(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    }),
};
