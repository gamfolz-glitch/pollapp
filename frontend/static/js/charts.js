/**
 * JavaScript для работы с диаграммами Chart.js
 */

document.addEventListener("DOMContentLoaded", function () {
  if (typeof Chart === "undefined") {
    console.warn("Chart.js не загружен");
    return;
  }

  const baseColors = [
    { bg: "rgba(99, 102, 241, 0.8)", border: "rgba(99, 102, 241, 1)" },   // indigo
    { bg: "rgba(139, 92, 246, 0.8)", border: "rgba(139, 92, 246, 1)" },  // purple
    { bg: "rgba(16, 185, 129, 0.8)", border: "rgba(16, 185, 129, 1)" },  // green
    { bg: "rgba(245, 158, 11, 0.8)", border: "rgba(245, 158, 11, 1)" },  // amber
    { bg: "rgba(239, 68, 68, 0.8)", border: "rgba(239, 68, 68, 1)" },    // red
    { bg: "rgba(59, 130, 246, 0.8)", border: "rgba(59, 130, 246, 1)" },  // blue
    { bg: "rgba(236, 72, 153, 0.8)", border: "rgba(236, 72, 153, 1)" },  // pink
    { bg: "rgba(34, 197, 94, 0.8)", border: "rgba(34, 197, 94, 1)" },    // emerald
    { bg: "rgba(14, 165, 233, 0.8)", border: "rgba(14, 165, 233, 1)" },  // sky
    { bg: "rgba(244, 114, 182, 0.8)", border: "rgba(244, 114, 182, 1)" }, // rose
    { bg: "rgba(251, 191, 36, 0.8)", border: "rgba(251, 191, 36, 1)" },  // yellow
    { bg: "rgba(79, 70, 229, 0.8)", border: "rgba(79, 70, 229, 1)" },    // indigo deep
    { bg: "rgba(67, 56, 202, 0.8)", border: "rgba(67, 56, 202, 1)" },    // violet deep
    { bg: "rgba(15, 118, 110, 0.8)", border: "rgba(15, 118, 110, 1)" },  // teal
    { bg: "rgba(94, 234, 212, 0.8)", border: "rgba(94, 234, 212, 1)" },  // teal light
    { bg: "rgba(148, 163, 184, 0.8)", border: "rgba(148, 163, 184, 1)" }, // slate
  ];

  function normalizePercents(values) {
    const total = values.reduce((a, b) => a + b, 0);
    if (total === 0) return values.map(() => 0);
    
    let raw = values.map((v) => (v / total) * 100);
    let rounded = raw.map((v) => Math.round(v));
    let diff = 100 - rounded.reduce((a, b) => a + b, 0);
    
    while (diff !== 0) {
      for (let i = 0; i < rounded.length && diff !== 0; i++) {
        if (diff > 0) {
          rounded[i] += 1;
          diff -= 1;
        } else if (rounded[i] > 0) {
          rounded[i] -= 1;
          diff += 1;
        }
      }
    }
    return rounded;
  }

  function initChart(canvas) {
    const labels = JSON.parse(canvas.dataset.labels || "[]").filter((l) => l && l.trim() !== "");
    const valuesRaw = JSON.parse(canvas.dataset.values || "[]");
    const values = valuesRaw.slice(0, labels.length).map((v) => (Number.isFinite(Number(v)) ? Number(v) : 0));
    const percents = normalizePercents(values);
    const kind = canvas.dataset.kind || "SINGLE";

    if (labels.length === 0 || values.length === 0) {
      canvas.style.display = 'none';
      return;
    }

    const backgroundColor = [];
    const borderColor = [];
    for (let i = 0; i < labels.length; i++) {
      const color = baseColors[i % baseColors.length];
      backgroundColor.push(color.bg);
      borderColor.push(color.border);
    }

    const chartType = kind === "SINGLE" ? "doughnut" : "bar";

    new Chart(canvas, {
      type: chartType,
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: backgroundColor,
            borderColor: borderColor,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                const label = context.label || "";
                const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                const percent = percents[context.dataIndex];
                return `${label}: ${value} (${percent}%)`;
              },
            },
          },
        },
        ...(kind === "SINGLE"
          ? { cutout: "60%" }
          : {
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: { stepSize: 1, precision: 0 },
                  title: { display: true, text: "Количество голосов" },
                },
                x: {
                  title: { display: true, text: "Варианты ответа" },
                },
              },
            }),
      },
    });

    // Применяем цвета к элементам деталей
    const detailItems = canvas.closest('.card, .bg-white').querySelectorAll('li[data-choice-color]');
    detailItems.forEach((item, index) => {
      const color = baseColors[index % baseColors.length].border;
      const meta = item.querySelector('[class*="font-semibold"], .choice-meta');
      if (meta) meta.style.color = color;
    });
  }

  // Инициализация всех диаграмм
  document.querySelectorAll('[data-chart="stats"]').forEach(initChart);
});

