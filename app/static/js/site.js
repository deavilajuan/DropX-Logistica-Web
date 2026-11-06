// Comportamiento del sitio público: menú en móvil y ventana del video institucional.
const burger = document.getElementById('burger');
const mobileMenu = document.getElementById('mobileMenu');
if (burger && mobileMenu) {
    burger.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
}

// Video institucional: se abre en una ventana ([data-overlay]) y se pausa al cerrarla
const overlay = document.getElementById('videoOverlay');
const video = document.getElementById('institutionalVideo');
if (overlay && video) {
    const open = () => {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
        video.play().catch(() => {});  // si el navegador bloquea la reproducción, queda el botón de play
    };
    const close = () => {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
        video.pause();
    };
    document.getElementById('playBtn').addEventListener('click', open);
    overlay.addEventListener('click', (e) => { if (e.target === overlay || e.target.closest('[data-close]')) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
}
