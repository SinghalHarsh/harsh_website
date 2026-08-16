/* Tooltips that work with both mouse and touch.

   The previous per-page implementations bound only mouseenter/mousemove, so
   heatmap tooltips were unreachable on phones. Any [data-tooltip] element is
   handled here: hover on pointer devices, tap on touch devices. */

const el = document.createElement('div');
el.className = 'tooltip';
el.setAttribute('role', 'tooltip');
document.body.appendChild(el);

let hideTimer = null;

function show(target, x, y) {
    const text = target.dataset.tooltip;
    if (!text) return;

    clearTimeout(hideTimer);
    el.textContent = text;
    el.classList.add('active');

    // Keep the bubble inside the viewport.
    const box = el.getBoundingClientRect();
    const left = Math.min(Math.max(x - box.width / 2, 8), window.innerWidth - box.width - 8);
    const top = y - box.height - 12;
    el.style.left = `${left}px`;
    el.style.top = `${top < 8 ? y + 20 : top}px`;
}

function hide() {
    el.classList.remove('active');
}

document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (target) show(target, e.clientX, e.clientY);
});

document.addEventListener('mousemove', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (target) show(target, e.clientX, e.clientY);
    else if (el.classList.contains('active')) hide();
});

document.addEventListener('mouseout', (e) => {
    if (e.target.closest('[data-tooltip]')) hide();
});

// Touch: tap to reveal, auto-dismiss.
document.addEventListener('touchstart', (e) => {
    const target = e.target.closest('[data-tooltip]');
    if (!target) return hide();
    const touch = e.touches[0];
    show(target, touch.clientX, touch.clientY);
    hideTimer = setTimeout(hide, 2000);
}, { passive: true });

window.addEventListener('scroll', hide, { passive: true });
