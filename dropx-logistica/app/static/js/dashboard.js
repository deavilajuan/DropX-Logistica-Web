document.addEventListener('DOMContentLoaded', () => {

    // 1. Leer datos reales inyectados en los atributos del body desde SQLite
    const body = document.body;
    let pesosBD = [150, 240, 200, 120];

    try {
        const rawPesos = body.getAttribute('data-pesos');
        if (rawPesos) {
            const parsed = JSON.parse(rawPesos);
            if (Array.isArray(parsed) && parsed.some(v => v > 0)) {
                pesosBD = parsed;
            }
        }
    } catch (e) {
        console.warn('Usando pesos de respaldo');
    }

    const kpisBD = {
        recibidos: body.getAttribute('data-recibidos') || '265',
        transito: body.getAttribute('data-transito') || '3,71',
        entregados: body.getAttribute('data-entregados') || '156',
        pendientes: body.getAttribute('data-pendientes') || '2,318'
    };

    // 2. Diccionario de periodos: "Este mes" usa datos reales; los demás simulan histórico
    const datosPorPeriodo = {
        este_mes: {
            kpis: kpisBD,
            lineaEsteMes: [8000, 10000, 3000, 14000, 14000, 7000, 9500],
            lineaMesPasado: [4000, 11000, 9000, 14500, 5000, 6000, 13000],
            pesos: pesosBD,
            dona: [52.1, 22.8, 13.9, 11.2],
            donaLabels: ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        },
        mes_pasado: {
            kpis: { recibidos: '210', transito: '2,89', entregados: '180', pendientes: '1,950' },
            lineaEsteMes: [6000, 9000, 5000, 11000, 10000, 8500, 8000],
            lineaMesPasado: [3500, 8000, 7000, 12000, 6000, 7500, 9000],
            pesos: [110, 190, 160, 95],
            dona: [45.0, 30.0, 15.0, 10.0],
            donaLabels: ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        },
        ultimos_3_meses: {
            kpis: { recibidos: '780', transito: '9,40', entregados: '512', pendientes: '6,100' },
            lineaEsteMes: [12000, 18000, 15000, 22000, 25000, 19000, 24000],
            lineaMesPasado: [10000, 14000, 13000, 19000, 18000, 16000, 21000],
            pesos: [420, 680, 550, 310],
            dona: [50.0, 25.0, 15.0, 10.0],
            donaLabels: ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        },
        ultimos_6_meses: {
            kpis: { recibidos: '1,540', transito: '18,2', entregados: '1,230', pendientes: '9,800' },
            lineaEsteMes: [18000, 24000, 21000, 32000, 35000, 28000, 36000],
            lineaMesPasado: [15000, 20000, 18000, 26000, 27000, 22000, 30000],
            pesos: [950, 1450, 1180, 720],
            dona: [49.0, 26.0, 14.5, 10.5],
            donaLabels: ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        },
        ultimo_ano: {
            kpis: { recibidos: '3,200', transito: '41,5', entregados: '2,890', pendientes: '15,400' },
            lineaEsteMes: [25000, 32000, 28000, 45000, 48000, 39000, 52000],
            lineaMesPasado: [20000, 27000, 24000, 38000, 41000, 35000, 44000],
            pesos: [1800, 2900, 2200, 1400],
            dona: [48.5, 26.5, 14.0, 11.0],
            donaLabels: ['José Carlos', 'Alberto Luis', 'César Gaviria', 'Otros']
        }
    };

    // 3. Inicializar Gráfica de Líneas (Paquetes totales)
    let chartLinea = null;
    const ctxLine = document.getElementById('lineChartPaquetes');
    if (ctxLine) {
        chartLinea = new Chart(ctxLine, {
            type: 'line',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul'],
                datasets: [
                    {
                        label: 'Este mes',
                        data: datosPorPeriodo.este_mes.lineaEsteMes,
                        borderColor: '#ff5722',
                        backgroundColor: 'transparent',
                        borderWidth: 2.5,
                        tension: 0.35,
                        pointBackgroundColor: '#ff5722',
                        pointRadius: 3
                    },
                    {
                        label: 'Mes pasado',
                        data: datosPorPeriodo.este_mes.lineaMesPasado,
                        borderColor: '#60a5fa',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.35,
                        pointBackgroundColor: '#60a5fa',
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: v => v >= 1000 ? (v / 1000) + 'K' : v,
                            color: '#94a3b8'
                        },
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // 4. Inicializar Gráfica de Barras (Pesos reales)
    let chartBarras = null;
    const ctxBar = document.getElementById('barChartPesos');
    if (ctxBar) {
        chartBarras = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: ['0-5 Kg', '5-8 Kg', '8-10 Kg', '+10 Kg'],
                datasets: [{
                    data: datosPorPeriodo.este_mes.pesos,
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
    }

    // 5. Inicializar Gráfica de Dona (Repartidores)
    let chartDona = null;
    const ctxDonut = document.getElementById('donutChartRepartidores');
    if (ctxDonut) {
        chartDona = new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: datosPorPeriodo.este_mes.donaLabels,
                datasets: [{
                    data: datosPorPeriodo.este_mes.dona,
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
    }

    // 6. Evento del Selector de Periodos (Dropdown Este mes, Mes pasado...)
    const selectFiltro = document.getElementById('filtroMes');
    if (selectFiltro) {
        selectFiltro.addEventListener('change', (e) => {
            const periodo = e.target.value;
            const data = datosPorPeriodo[periodo] || datosPorPeriodo.este_mes;

            // Actualizar números de los KPIs superiores
            const kpiRecibidos = document.querySelector('.kpi-orange h2');
            const kpiTransito = document.querySelector('.kpi-blue h2');
            const kpiEntregados = document.querySelector('.kpi-green h2');
            const kpiPendientes = document.querySelector('.kpi-red h2');

            if (kpiRecibidos) kpiRecibidos.textContent = data.kpis.recibidos;
            if (kpiTransito) kpiTransito.textContent = data.kpis.transito;
            if (kpiEntregados) kpiEntregados.textContent = data.kpis.entregados;
            if (kpiPendientes) kpiPendientes.textContent = data.kpis.pendientes;

            // Actualizar Gráfica de Líneas con animación
            if (chartLinea) {
                chartLinea.data.datasets[0].data = data.lineaEsteMes;
                chartLinea.data.datasets[1].data = data.lineaMesPasado;
                chartLinea.update();
            }

            // Actualizar Gráfica de Barras
            if (chartBarras) {
                chartBarras.data.datasets[0].data = data.pesos;
                chartBarras.update();
            }

            // Actualizar Gráfica de Dona
            if (chartDona) {
                chartDona.data.datasets[0].data = data.dona;
                chartDona.data.labels = data.donaLabels;
                chartDona.update();
            }
        });
    }

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