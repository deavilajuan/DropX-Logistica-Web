document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-password-toggle]').forEach((toggle) => {
        toggle.addEventListener('click', () => {
            const input = document.getElementById(toggle.dataset.passwordToggle);
            if (!input) return;

            const showPassword = input.type === 'password';
            input.type = showPassword ? 'text' : 'password';
            toggle.textContent = showPassword ? 'Ocultar' : 'Mostrar';
            toggle.setAttribute('aria-label', showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
            toggle.setAttribute('aria-pressed', String(showPassword));
        });
    });

    // Gráficas del dashboard: usan los datos reales que manda el servidor
    const dataTag = document.getElementById('chart-data');
    if (!dataTag || typeof Chart === 'undefined') return;
    const data = JSON.parse(dataTag.textContent);

    // Paquetes creados por mes
    new Chart(document.getElementById('lineChartPaquetes'), {
        type: 'line',
        data: {
            labels: data.months,
            datasets: [{
                data: data.created,
                borderColor: '#ff5722',
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                tension: 0.35,
                pointBackgroundColor: '#ff5722',
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0, color: '#94a3b8' }, grid: { color: '#f1f5f9' } },
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
            }
        }
    });

    // Paquetes por rango de peso
    new Chart(document.getElementById('barChartPesos'), {
        type: 'bar',
        data: {
            labels: ['0-5 Kg', '5-8 Kg', '8-10 Kg', '+10 Kg'],
            datasets: [{
                data: data.weights,
                backgroundColor: ['#ffb74d', '#2dd4bf', '#f87171', '#c084fc'],
                borderRadius: 8,
                barPercentage: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { display: false },
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
            }
        }
    });

    // Entregas del mes por repartidor
    new Chart(document.getElementById('donutChartRepartidores'), {
        type: 'doughnut',
        data: {
            labels: data.couriers,
            datasets: [{
                data: data.deliveries,
                backgroundColor: ['#ff7043', '#3b82f6', '#10b981', '#ef4444'],
                borderWidth: 0,
                cutout: '72%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
});

/* ==========================================================================
   LOGÍSTICOS - MAPA LEAFLET + INTERACTIVIDAD
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    // Solo inicializar si estamos en la página de logísticos
    const mapaDiv = document.getElementById('mapaLogistico');
    if (!mapaDiv) return;

    // ----------- MAPA LEAFLET (Colombia, tiles oscuros) -----------
    const map = L.map('mapaLogistico', {
        center: [5.0, -74.0],  // Centro de Colombia
        zoom: 6,
        zoomControl: true,
        scrollWheelZoom: true,
        attributionControl: true
    });

    // Tiles oscuros (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OSM</a> © <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 18
    }).addTo(map);

    // Ciudades / Centros de Distribución
    const hubs = [
        { nombre: 'Bogotá Norte',          lat: 4.7110,  lng: -74.0721, color: '#10b981' },
        { nombre: 'Medellín Centro',       lat: 6.2442,  lng: -75.5812, color: '#10b981' },
        { nombre: 'Cali Sur',              lat: 3.4516,  lng: -76.5320, color: '#10b981' },
        { nombre: 'Barranquilla Puerto',   lat: 10.9685, lng: -74.7813, color: '#10b981' },
        { nombre: 'Bucaramanga',           lat: 7.1193,  lng: -73.1227, color: '#10b981' }
    ];

    // Crear marcadores con popup
    hubs.forEach(function (hub) {
        L.circleMarker([hub.lat, hub.lng], {
            radius: 7,
            fillColor: hub.color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(map).bindPopup(
            '<strong style="font-size:13px;">' + hub.nombre + '</strong><br>' +
            '<span style="color:#94a3b8;font-size:11px;">Centro de distribución DropX</span>'
        );
    });

    // Rutas activas (polylines entre ciudades)
    const rutas = [
        // Bogotá → Medellín
        { coords: [[4.7110, -74.0721], [5.6, -74.8], [6.2442, -75.5812]], color: '#ff5722' },
        // Bogotá → Cali
        { coords: [[4.7110, -74.0721], [3.9, -75.2], [3.4516, -76.5320]], color: '#ff5722' },
        // Bogotá → Bucaramanga
        { coords: [[4.7110, -74.0721], [5.9, -73.6], [7.1193, -73.1227]], color: '#ff5722' },
        // Medellín → Barranquilla
        { coords: [[6.2442, -75.5812], [8.5, -75.2], [10.9685, -74.7813]], color: '#ff5722' },
        // Cali → Bogotá (retorno)
        { coords: [[3.4516, -76.5320], [4.2, -75.5], [4.7110, -74.0721]], color: 'rgba(255,87,34,0.35)' }
    ];

    rutas.forEach(function (ruta) {
        L.polyline(ruta.coords, {
            color: ruta.color,
            weight: 2.5,
            opacity: 0.85,
            dashArray: '8 5',
            lineJoin: 'round'
        }).addTo(map);
    });

    // Ajustar bounds al grupo de marcadores
    const bounds = L.latLngBounds(hubs.map(function (h) { return [h.lat, h.lng]; }));
    map.fitBounds(bounds, { padding: [30, 30] });

    // ----------- SELECTOR DE FECHA -----------
    const logDateBtn = document.getElementById('logDateBtn');
    if (logDateBtn) {
        const dateSpan = document.getElementById('logCurrentDate');
        const now = new Date();
        const opciones = { day: 'numeric', month: 'long' };
        const fechaFormateada = 'Hoy, ' + now.toLocaleDateString('es-CO', opciones);
        if (dateSpan) dateSpan.textContent = fechaFormateada;
    }
});

/* Paquetes: creación, consulta y edición */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-delete-driver-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            const name = form.dataset.driverName || 'este repartidor';
            if (!window.confirm(`¿Eliminar a ${name}? Esta acción no se puede deshacer.`)) {
                event.preventDefault();
            }
        });
    });

    const modalTriggers = document.querySelectorAll('[data-open-modal]');
    const modals = document.querySelectorAll('[data-modal]');
    let activeTrigger = null;

    const closeModal = (modal) => {
        if (!modal) return;
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        if (activeTrigger) activeTrigger.focus();
    };

    const openModal = (modal, trigger) => {
        if (!modal) return;
        activeTrigger = trigger;
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
        const firstInput = modal.querySelector('input, select, button');
        if (firstInput) firstInput.focus();
    };

    modalTriggers.forEach((trigger) => {
        trigger.addEventListener('click', () => {
            openModal(document.getElementById(trigger.dataset.openModal), trigger);
        });
    });

    modals.forEach((modal) => {
        modal.querySelectorAll('[data-close-modal]').forEach((button) => {
            button.addEventListener('click', () => closeModal(modal));
        });
        modal.addEventListener('click', (event) => {
            if (event.target === modal) closeModal(modal);
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const openedModal = document.querySelector('[data-modal].open');
            if (openedModal) closeModal(openedModal);
        }
    });

    document.querySelectorAll('[data-view-package]').forEach((button) => {
        button.addEventListener('click', () => {
            const fields = {
                'detail-guide': `Guía ${button.dataset.guide}`,
                'detail-sender': button.dataset.sender,
                'detail-recipient': button.dataset.recipient,
                'detail-city': button.dataset.city,
                'detail-address': button.dataset.address,
                'detail-status': button.dataset.statusLabel,
                'detail-courier': button.dataset.courier || 'Sin asignar',
                'detail-weight': `${button.dataset.weight} kg`,
                'detail-date': button.dataset.date
            };
            Object.entries(fields).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value || '—';
            });
            openModal(document.getElementById('view-package-modal'), button);
        });
    });

    const editForm = document.getElementById('edit-package-form');
    const deleteForm = document.getElementById('delete-package-form');
    const deleteButton = document.getElementById('delete-package-button');
    document.querySelectorAll('[data-edit-package]').forEach((button) => {
        button.addEventListener('click', () => {
            if (!editForm) return;
            const values = {
                'edit-sender': button.dataset.sender,
                'edit-recipient': button.dataset.recipient,
                'edit-city': button.dataset.city,
                'edit-address': button.dataset.address,
                'edit-weight': button.dataset.weight,
                'edit-status': button.dataset.status,
                'edit-courier': button.dataset.courierId
            };
            Object.entries(values).forEach(([id, value]) => {
                const input = document.getElementById(id);
                if (input) input.value = value || '';
            });
            const guide = document.getElementById('edit-package-guide');
            if (guide) guide.textContent = `Guía ${button.dataset.guide}`;
            editForm.action = `${editForm.dataset.editUrl.replace(/\/$/, '')}/${button.dataset.id}/editar`;
            if (deleteForm) {
                deleteForm.action = `${deleteForm.dataset.deleteUrl.replace(/\/$/, '')}/${button.dataset.id}/eliminar`;
            }
            openModal(document.getElementById('edit-package-modal'), button);
        });
    });

    if (deleteButton && deleteForm) {
        deleteButton.addEventListener('click', () => {
            const guide = document.getElementById('edit-package-guide');
            const packageGuide = guide ? guide.textContent.replace(/^Guía\s*/, '') : 'este paquete';
            if (window.confirm(`¿Eliminar el paquete ${packageGuide}? Esta acción no se puede deshacer.`)) {
                deleteForm.submit();
            }
        });
    }
});