/**
 * Real-time chart for Biologic data visualization
 */

// Configuration
const config = {
    websocketUrl: `ws://${window.location.hostname}:8765/ws`,
    reconnectInterval: 2000, // ms
    maxPoints: 1000, // Maximum number of points to display
    updateRateWindow: 10, // Number of seconds to calculate update rate
};

// State variables
let socket = null;
let chartData = {};
let techniques = new Set();
let currentTechnique = null;
let lastUpdateTime = Date.now();
let pointsReceived = 0;
let updateRates = [];
let reconnectTimeout = null;

// DOM elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const techniqueName = document.getElementById('technique-name');
const latestData = document.getElementById('latest-data');
const dataPoints = document.getElementById('data-points');
const updateRate = document.getElementById('update-rate');
const chartElement = document.getElementById('chart');

// Initialize the chart with empty data
function initializeChart() {
    // Create an empty trace to start with
    const emptyTrace = {
        x: [],
        y: [],
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Initializing...'
    };

    const layout = {
        title: 'Biologic Real-time Data',
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            orientation: 'h'
        },
        xaxis: {
            title: 'X',
            showgrid: true,
            zeroline: true,
            range: [-1, 1]  // Set initial range
        },
        yaxis: {
            title: 'Y',
            showgrid: true,
            zeroline: true,
            range: [-1, 1]  // Set initial range
        },
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50,
            pad: 4
        },
        autosize: true
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    console.log('Initializing chart...');
    Plotly.newPlot(chartElement, [emptyTrace], layout, config);
}

// Connect to WebSocket server
function connectWebSocket() {
    if (socket) {
        socket.close();
    }

    updateConnectionStatus('connecting');

    socket = new WebSocket(config.websocketUrl);

    socket.onopen = function() {
        console.log('WebSocket connection established');
        updateConnectionStatus('connected');

        // Clear any reconnect timeout
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }
    };

    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    socket.onclose = function() {
        console.log('WebSocket connection closed');
        updateConnectionStatus('disconnected');

        // Schedule reconnect
        if (!reconnectTimeout) {
            reconnectTimeout = setTimeout(connectWebSocket, config.reconnectInterval);
        }
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus('disconnected');

        // Close socket and reconnect
        socket.close();
    };
}

// Update connection status UI
function updateConnectionStatus(status) {
    statusIndicator.className = 'status-indicator ' + status;

    switch (status) {
        case 'connected':
            statusText.textContent = 'Connected';
            break;
        case 'disconnected':
            statusText.textContent = 'Disconnected';
            break;
        case 'connecting':
            statusText.textContent = 'Connecting...';
            break;
    }
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(data) {
    // Handle different message types
    switch (data.type) {
        case 'connection_established':
            console.log('Connection established:', data.message);
            break;

        case 'data_point':
            handleDataPoint(data);
            break;

        case 'technique_change':
            handleTechniqueChange(data);
            break;

        case 'acknowledgement':
            // Just log acknowledgements
            console.log('Server acknowledged message');
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

// Handle new data point
function handleDataPoint(data) {
    const technique = data.technique;
    const x = data.x;
    const y = data.y;

    console.log(`Received data point: technique=${technique}, x=${x}, y=${y}`);

    // Initialize technique data if it doesn't exist
    if (!chartData[technique]) {
        console.log(`Creating new trace for technique: ${technique}`);
        chartData[technique] = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: technique,
            marker: {
                size: 6
            },
            line: {
                width: 2
            }
        };
        techniques.add(technique);
    }

    // Add new data point
    chartData[technique].x.push(x);
    chartData[technique].y.push(y);

    // Limit number of points
    if (chartData[technique].x.length > config.maxPoints) {
        chartData[technique].x.shift();
        chartData[technique].y.shift();
    }

    // Update current technique if needed
    if (currentTechnique !== technique) {
        currentTechnique = technique;
        techniqueName.textContent = technique;
    }

    // Update latest data display
    latestData.textContent = `X: ${x.toFixed(4)}, Y: ${y.toFixed(4)}`;

    // Update chart - use Plotly.extendTraces for incremental updates
    if (chartData[technique].x.length > 1) {
        try {
            // Find the index of this technique's trace
            const traces = Object.keys(chartData);
            const traceIndex = traces.indexOf(technique);

            if (traceIndex !== -1) {
                // Extend the trace with the new point
                Plotly.extendTraces(chartElement, {
                    x: [[x]],
                    y: [[y]]
                }, [traceIndex]);

                // Occasionally do a full redraw to ensure everything is in sync
                if (chartData[technique].x.length % 20 === 0) {
                    updateChart();
                }
            } else {
                // Fallback to full redraw if we can't find the trace
                updateChart();
            }
        } catch (error) {
            console.error('Error updating chart:', error);
            // Fallback to full redraw
            updateChart();
        }
    } else {
        // First point, do a full redraw
        updateChart();
    }

    // Update statistics
    updateStatistics();
}

// Handle technique change
function handleTechniqueChange(data) {
    currentTechnique = data.technique;
    techniqueName.textContent = currentTechnique;

    // Update chart title
    const update = {
        title: `${currentTechnique} Data`
    };

    Plotly.relayout(chartElement, update);
}

// Update the chart with new data
function updateChart() {
    // Convert chart data to array of traces
    const traces = Object.values(chartData);

    // Check if we have data to plot
    if (traces.length > 0 && traces[0].x.length > 0) {
        console.log(`Updating chart with ${traces.length} traces. First trace has ${traces[0].x.length} points.`);

        // Update the chart
        Plotly.react(chartElement, traces);

        // Make sure axes are properly scaled
        Plotly.relayout(chartElement, {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    } else {
        console.log('No data to plot yet');
    }
}

// Update statistics
function updateStatistics() {
    // Count total points
    let totalPoints = 0;
    for (const technique in chartData) {
        totalPoints += chartData[technique].x.length;
    }

    dataPoints.textContent = `Total points: ${totalPoints}`;

    // Calculate update rate
    const now = Date.now();
    const elapsed = (now - lastUpdateTime) / 1000; // seconds

    pointsReceived++;

    // Update rate calculation every second
    if (elapsed >= 1) {
        const rate = pointsReceived / elapsed;
        updateRates.push(rate);

        // Keep only the last N update rates
        if (updateRates.length > config.updateRateWindow) {
            updateRates.shift();
        }

        // Calculate average update rate
        const avgRate = updateRates.reduce((sum, rate) => sum + rate, 0) / updateRates.length;

        // Update display
        updateRate.textContent = `Update rate: ${avgRate.toFixed(2)} pts/sec`;

        // Reset counters
        lastUpdateTime = now;
        pointsReceived = 0;
    }
}

// Initialize the application
function initialize() {
    initializeChart();
    connectWebSocket();

    // Handle window resize
    window.addEventListener('resize', function() {
        Plotly.relayout(chartElement, {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    });
}

// Start the application when the page loads
document.addEventListener('DOMContentLoaded', initialize);
