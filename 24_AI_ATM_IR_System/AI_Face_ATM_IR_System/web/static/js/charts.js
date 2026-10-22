/**
 * Chart.js and Vis.js Network Visualization Helpers
 */

function renderBarChart(canvasId, labels, data, labelTitle = "Value", color = "#38bdf8") {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (window[canvasId + "_chart"]) {
        window[canvasId + "_chart"].destroy();
    }

    window[canvasId + "_chart"] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: labelTitle,
                data: data,
                backgroundColor: color,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });

    return window[canvasId + "_chart"];
}

function renderVisNetwork(containerId, nodesArray, edgesArray) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    const data = {
        nodes: new vis.DataSet(nodesArray),
        edges: new vis.DataSet(edgesArray)
    };

    const options = {
        nodes: {
            shape: 'dot',
            size: 16,
            font: {
                size: 12,
                color: '#f8fafc'
            },
            borderWidth: 2
        },
        edges: {
            width: 1.5,
            smooth: {
                type: 'continuous'
            },
            arrows: {
                to: { enabled: true, scaleFactor: 0.8 }
            }
        },
        physics: {
            stabilization: false,
            barnesHut: {
                gravitationalConstant: -2000,
                springConstant: 0.04,
                springLength: 120
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200
        }
    };

    return new vis.Network(container, data, options);
}
