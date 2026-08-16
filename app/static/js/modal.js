/* One modal controller for the whole site.

   Any element with [data-modal-open="id"] opens that modal; any element with
   [data-modal-close] inside one closes it. Overlay click and Escape also
   close. No per-page wiring required. */

const modal = {
    open(id) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.add('active');
        el.querySelector('input, select, textarea, button')?.focus();
    },

    close(el) {
        (typeof el === 'string' ? document.getElementById(el) : el)?.classList.remove('active');
    },

    closeAll() {
        document.querySelectorAll('.modal-overlay.active').forEach((m) => m.classList.remove('active'));
    },

    /** Shared confirmation dialog. Replaces every ad-hoc confirm modal. */
    confirm(message, onConfirm) {
        const el = document.getElementById('confirmModal');
        if (!el) return onConfirm();

        el.querySelector('[data-confirm-message]').textContent = message;

        const button = el.querySelector('[data-confirm-accept]');
        const fresh = button.cloneNode(true); // drop previous listeners
        button.replaceWith(fresh);
        fresh.addEventListener('click', () => {
            modal.close(el);
            onConfirm();
        });

        modal.open('confirmModal');
        fresh.focus();
    },
};

document.addEventListener('click', (e) => {
    const opener = e.target.closest('[data-modal-open]');
    if (opener) {
        e.preventDefault();
        modal.open(opener.dataset.modalOpen);
        return;
    }
    if (e.target.closest('[data-modal-close]') || e.target.classList.contains('modal-overlay')) {
        modal.close(e.target.closest('.modal-overlay'));
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') modal.closeAll();
});

window.modal = modal;
