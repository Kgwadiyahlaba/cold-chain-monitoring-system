// dashboard/script.js
const API_ROOT = window.location.origin + "/api";

let tempChart, humChart;

async function fetchHistory() {
  const res = await fetch(API_ROOT + "/history");
  return await res.json();
}

async function fetchDevices() {
  const res = await fetch(API_ROOT + "/devices");
  return await res.json();
}

async function fetchChain() {
  const res = await fetch(API_ROOT + "/blockchain/alerts");
  if (res.status === 200) return await res.json();
  return [];
}

function buildCharts(history) {
  const temps = history.map(h => ({x: h.timestamp, y: h.temperature_c}));
  const hums = history.map(h => ({x: h.timestamp, y: h.humidity_percent}));

  const tempCtx = document.getElementById("tempChart").getContext("2d");
  const humCtx = document.getElementById("humChart").getContext("2d");

  if (tempChart) tempChart.destroy();
  if (humChart) humChart.destroy();

  tempChart = new Chart(tempCtx, {
    type: 'line',
    data: {datasets: [{label:'Temperature (°C)', data: temps, tension:0.2}]},
    options: { parsing: {xAxisKey: 'x', yAxisKey: 'y'}, scales: { x: { type:'time', time:{tooltipFormat:'HH:mm:ss'} } } }
  });

  humChart = new Chart(humCtx, {
    type: 'line',
    data: {datasets: [{label:'Humidity (%)', data: hums, tension:0.2}]},
    options: { parsing: {xAxisKey: 'x', yAxisKey: 'y'}, scales: { x: { type:'time', time:{tooltipFormat:'HH:mm:ss'} } } }
  });
}

function buildDeviceTable(devices) {
  const tbody = document.querySelector("#deviceTable tbody");
  tbody.innerHTML = "";
  devices.forEach(d => {
    const r = d.latest || {};
    const alertClass = (r.temperature_c > 8 || r.temperature_c < -5 || r.door_state === "open") ? "alert" : "";
    const txLink = r.tx_hash ? `<a href="https://sepolia.etherscan.io/tx/${r.tx_hash}" target="_blank" class="link">tx</a>` : "";
    tbody.innerHTML += `<tr>
      <td>${d.device_id}</td>
      <td class="${alertClass}">${r.temperature_c ?? ""}</td>
      <td>${r.humidity_percent ?? ""}</td>
      <td>${r.battery_voltage ?? ""}</td>
      <td>${r.door_state ?? ""}</td>
      <td>${txLink}</td>
    </tr>`;
  });
}

async function refreshAll() {
  const history = await fetchHistory();
  buildCharts(history);

  const devices = await fetchDevices();
  buildDeviceTable(devices);

  const chain = await fetchChain();
  const chainDiv = document.getElementById("chainList");
  chainDiv.innerHTML = "";
  chain.forEach(a => {
    const txLink = a.tx_hash ? `https://sepolia.etherscan.io/tx/${a.tx_hash}` : "";
    chainDiv.innerHTML += `<div style="background:#fff;padding:8px;border-radius:6px;margin-bottom:6px">
      <strong>${a.alert_type}</strong> — ${a.device_id} @ ${a.timestamp} ${txLink ? `<a class="link" href="${txLink}" target="_blank">[tx]</a>` : ""}
      <div style="font-size:12px;color:#555">hash: ${a.data_hash || a.dataHash || ""}</div>
    </div>`;
  });
}

// AI handler
document.getElementById("askBtn").addEventListener("click", async () => {
  const q = document.getElementById("aiQuestion").value;
  if (!q) return;
  const res = await fetch(API_ROOT + "/ai", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({question:q})});
  const j = await res.json();
  document.getElementById("aiAnswer").innerText = j.answer || JSON.stringify(j);
});

refreshAll();
setInterval(refreshAll, 5000); // every 5s
