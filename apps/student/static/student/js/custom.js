document.addEventListener("DOMContentLoaded", function () {

    const canvas = document.getElementById("studentBarChart");
    if (!canvas) return;

    if (typeof Chart === "undefined") {
        console.error("Chart.js not loaded");
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: ["HTML", "CSS", "JavaScript", "Django"],
            datasets: [{
                label: "Progress (%)",
                data: [90, 80, 65, 50],
                backgroundColor: [
                    "#22c55e",
                    "#3b82f6",
                    "#8b5cf6",
                    "#f59e0b"
                ],
                borderRadius: 10,
                barThickness: 28
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Subjects"
                    },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: "Progress (%)"
                    },
                    ticks: {
                        callback: value => value + "%"
                    }
                }
            }
        }
    });

});
