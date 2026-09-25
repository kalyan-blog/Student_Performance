function createChart(canvasId, type, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#e2e8f0' : '#475569';
    const gridColor = isDark ? '#334155' : '#e2e8f0';

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { labels: { color: textColor, font: { size: 11 } } }
        },
        scales: type !== 'pie' && type !== 'doughnut' ? {
            x: { ticks: { color: textColor, font: { size: 10 } }, grid: { color: gridColor } },
            y: { ticks: { color: textColor, font: { size: 10 } }, grid: { color: gridColor } }
        } : {}
    };

    const mergedOptions = { ...defaultOptions, ...options };
    if (options.plugins) mergedOptions.plugins = { ...defaultOptions.plugins, ...options.plugins };
    if (options.scales) mergedOptions.scales = { ...defaultOptions.scales, ...options.scales };

    charts[canvasId] = new Chart(ctx, {
        type,
        data: { labels, datasets },
        options: mergedOptions
    });
    return charts[canvasId];
}

function createBarChart(canvasId, labels, data, label = 'Value', color = '#4f46e5') {
    return createChart(canvasId, 'bar', labels, [{
        label,
        data,
        backgroundColor: Array.isArray(color) ? color : `${color}80`,
        borderColor: color,
        borderWidth: 2,
        borderRadius: 4,
    }]);
}

function createLineChart(canvasId, labels, datasets) {
    return createChart(canvasId, 'line', labels, datasets);
}

function createPieChart(canvasId, labels, data, colors = null) {
    const defaultColors = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];
    const bgColors = colors || data.map((_, i) => defaultColors[i % defaultColors.length]);
    return createChart(canvasId, 'doughnut', labels, [{
        data,
        backgroundColor: bgColors.map(c => `${c}CC`),
        borderColor: bgColors,
        borderWidth: 2,
    }]);
}

function createRadarChart(canvasId, labels, datasets) {
    return createChart(canvasId, 'radar', labels, datasets);
}

function updateChartColors() {
    Object.keys(charts).forEach(key => {
        if (charts[key] && charts[key].options) {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            const textColor = isDark ? '#e2e8f0' : '#475569';
            const gridColor = isDark ? '#334155' : '#e2e8f0';
            charts[key].options.plugins.legend.labels.color = textColor;
            if (charts[key].options.scales) {
                Object.values(charts[key].options.scales).forEach(s => {
                    s.ticks.color = textColor;
                    s.grid.color = gridColor;
                });
            }
            charts[key].update();
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('themeIcon');
    if (themeBtn) {
        const observer = new MutationObserver(() => updateChartColors());
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }
});