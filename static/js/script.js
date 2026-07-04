document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".progress-ring").forEach((ring) => {
        const value = Number(ring.dataset.progress || 0);
        ring.style.setProperty("--value", `${Math.max(0, Math.min(100, value))}%`);
    });

    const chart = document.getElementById("adminChart");
    if (chart && window.Chart) {
        new Chart(chart, {
            type: "doughnut",
            data: {
                labels: ["Users", "Completions", "Logs", "SQL", "XSS", "Brute Force"],
                datasets: [{
                    data: [
                        Number(chart.dataset.users || 0),
                        Number(chart.dataset.completed || 0),
                        Number(chart.dataset.logs || 0),
                        Number(chart.dataset.sql || 0),
                        Number(chart.dataset.xss || 0),
                        Number(chart.dataset.bruteforce || 0)
                    ],
                    backgroundColor: ["#42d9ff", "#65f0a2", "#ff637d", "#ffd166", "#b18cff", "#ff9f6e"],
                    borderColor: "#071017",
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#e8f6ff" } } }
            }
        });
    }

    document.querySelectorAll("textarea[name='passwords']").forEach((box) => {
        box.addEventListener("input", () => {
            const lines = box.value.split(/\r?\n/).filter(Boolean).length;
            box.title = `${lines} guesses queued`;
        });
    });
});
