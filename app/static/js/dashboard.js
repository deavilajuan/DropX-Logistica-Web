// Gráficas del dashboard con Chart.js. Los datos llegan en el JSON de la página.
const data = JSON.parse(document.getElementById('chart-data').textContent);

// Colores del diseño (variables CSS que genera Tailwind a partir de input.css)
const css = getComputedStyle(document.documentElement);
const color = (name) => css.getPropertyValue(name).trim();
const accent = color('--color-accent');
const muted = color('--color-muted');
const line = color('--color-line');

Chart.defaults.font.family = css.getPropertyValue('--font-sans');
Chart.defaults.color = muted;

// Ventana que aparece al pasar el cursor (o tocar) sobre un punto o barra
const tooltip = {
    backgroundColor: color('--color-ink'),
    titleColor: '#fff',
    bodyColor: '#fff',
    padding: 10,
    cornerRadius: 10,
    displayColors: true,
    boxPadding: 4,
};

// ---- Paquetes creados: este año contra el año anterior ----
const areaCanvas = document.getElementById('areaChart');
const gradient = areaCanvas.getContext('2d').createLinearGradient(0, 0, 0, 250);
gradient.addColorStop(0, 'rgba(255, 87, 34, 0.28)');
gradient.addColorStop(1, 'rgba(255, 87, 34, 0)');

new Chart(areaCanvas, {
    type: 'line',
    data: {
        labels: data.months,
        datasets: [
            {
                label: 'Este año',
                data: data.created,
                borderColor: accent,
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: accent,
                pointHoverBorderWidth: 3,
            },
            {
                label: 'Año anterior',
                data: data.previous,
                borderColor: muted,
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        // El mensaje muestra los dos años del mismo mes aunque el cursor no esté sobre el punto
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { display: false }, tooltip: tooltip },
        scales: {
            x: { grid: { display: false }, border: { display: false } },
            y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: line, borderDash: [3, 5] }, border: { display: false } },
        },
    },
});

// ---- Paquetes por rango de peso ----
new Chart(document.getElementById('weightChart'), {
    type: 'bar',
    data: {
        labels: ['0–5 kg', '5–8 kg', '8–10 kg', '+10 kg'],
        datasets: [{
            label: 'Paquetes',
            data: data.weights,
            backgroundColor: [accent, color('--color-peach'), color('--color-peach'), color('--color-peach')],
            hoverBackgroundColor: accent,
            borderRadius: 10,
            borderSkipped: false,
            maxBarThickness: 40,
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: tooltip },
        scales: {
            x: { grid: { display: false }, border: { display: false } },
            y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: line, borderDash: [3, 5] }, border: { display: false } },
        },
    },
});
