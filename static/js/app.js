let chart;
const $ = (id) => document.getElementById(id);
function fmtValue(value, unit='') { return value === undefined || value === null ? `— <small>${unit}</small>` : `${value} <small>${unit}</small>`; }
function timeLabel(value) {
  try { return new Date(value).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}); }
  catch { return value; }
}
function summarizeMeasurements(m) {
  return Object.entries(m).map(([k,v]) => `${k.replaceAll('_',' ')}: ${v}`).join(' · ');
}
async function refreshDashboard() {
  try {
    const [health, ready, history] = await Promise.all([
      fetch('/health'), fetch('/ready'), fetch('/api/v1/measurements?limit=20')
    ]);
    if (!health.ok || !ready.ok || !history.ok) throw new Error('API unavailable');
    const readyData = await ready.json(), historyData = await history.json();
    $('apiStatus').textContent = 'Connected · healthy';
    $('readyStatus').textContent = 'Health endpoint responding';
    $('readyTag').textContent = 'HEALTHY';
    $('modelStatus').textContent = readyData.heart_model_available ? 'Artifact loaded' : 'Train and register a model to enable estimates';
    $('modelTag').textContent = readyData.heart_model_available ? 'AVAILABLE' : 'UNTRAINED';
    $('modelTag').className = readyData.heart_model_available ? 'status-tag green-tag' : 'status-tag';
    renderHistory(historyData.items || []);
  } catch (err) {
    $('apiStatus').textContent = 'Connection issue';
    $('readyStatus').textContent = 'Could not reach API';
    $('readyTag').textContent = 'OFFLINE';
    $('readyTag').className = 'status-tag';
    $('formResult').textContent = 'Could not load dashboard data. Check that the Flask service is running.';
    $('formResult').className = 'form-result result-warn';
  }
}
function renderHistory(items) {
  const body = $('historyBody');
  if (!items.length) {
    body.innerHTML = '<tr><td colspan="3" class="empty-row">No records yet. Add a demo measurement.</td></tr>';
    $('chartEmpty').style.display = 'grid';
    $('heartRate').innerHTML = fmtValue(null, 'bpm');
    $('spo2').innerHTML = fmtValue(null, '%');
    $('temperature').innerHTML = fmtValue(null, '°C');
    $('flagCount').innerHTML = fmtValue(0, 'active');
    drawChart([], []);
    return;
  }
  const latest = items[0].measurements || {};
  $('heartRate').innerHTML = fmtValue(latest.heart_rate_bpm, 'bpm');
  $('spo2').innerHTML = fmtValue(latest.spo2_percent, '%');
  $('temperature').innerHTML = fmtValue(latest.temperature_c, '°C');
  const totalFlags = items.reduce((n, item) => n + (item.flags || []).length, 0);
  $('flagCount').innerHTML = fmtValue(totalFlags, 'in records');
  $('flagCaption').textContent = 'Flags are not diagnoses';
  body.innerHTML = items.slice(0,7).map(item => {
    const measurements = summarizeMeasurements(item.measurements || {});
    const flags = (item.flags || []).length;
    return `<tr><td>${timeLabel(item.created_at)}</td><td title="${escapeHtml(measurements)}">${escapeHtml(measurements || '—').slice(0,66)}</td><td><span class="flag-badge ${flags ? 'warn' : ''}">${flags ? flags + ' flag(s)' : 'No flags'}</span></td></tr>`;
  }).join('');
  const chartItems = [...items].reverse().filter(item => item.measurements && item.measurements.heart_rate_bpm !== undefined);
  $('chartEmpty').style.display = chartItems.length ? 'none' : 'grid';
  drawChart(chartItems.map(item => timeLabel(item.created_at)), chartItems.map(item => item.measurements.heart_rate_bpm));
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function drawChart(labels, values) {
  if (typeof Chart === 'undefined') return;
  const canvas = $('historyChart');
  if (chart) chart.destroy();
  chart = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets: [{ label:'Heart rate (bpm)', data:values, borderColor:'#10b7a2', backgroundColor:'rgba(16,183,162,.10)', fill:true, tension:.35, borderWidth:2, pointRadius:3, pointBackgroundColor:'#fff', pointBorderWidth:2 }] },
    options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{
      x:{grid:{display:false},ticks:{color:'#9aa4b5',font:{size:9},maxTicksLimit:5}},
      y:{grid:{color:'#eef1f6'},ticks:{color:'#9aa4b5',font:{size:9}},border:{display:false}}
    }}
  });
}
$('measurementForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const measurementForm = event.currentTarget;
  const form = new FormData(measurementForm), payload = {};
  for (const [key, raw] of form.entries()) if (raw.trim() !== '') payload[key] = Number(raw);
  if (!Object.keys(payload).length) {
    $('formResult').textContent = 'Enter at least one measurement.';
    $('formResult').className = 'form-result result-warn';
    return;
  }
  const btn = $('submitBtn'); btn.disabled = true; btn.textContent = 'Saving…';
  try {
    const response = await fetch('/api/v1/measurements/check', {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not save measurement');
    $('formResult').className = `form-result ${data.flags.length ? 'result-warn' : 'result-ok'}`;
    $('formResult').textContent = data.flags.length
      ? `Saved. ${data.flags.map(flag => `${flag.field}: ${flag.message}`).join(' ')}`
      : 'Measurement saved. No configured screening flags were raised. This is not confirmation that the reading is medically normal.';
    measurementForm.reset();
    await refreshDashboard();
  } catch (error) {
    $('formResult').textContent = error.message;
    $('formResult').className = 'form-result result-warn';
  } finally {
    btn.disabled = false; btn.innerHTML = 'Save measurement <span>→</span>';
  }
});
$('refreshBtn').addEventListener('click', refreshDashboard);
refreshDashboard();

const heartModelForm = $('heartModelForm');
heartModelForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {};
  for (const [key, raw] of new FormData(heartModelForm).entries()) {
    if (raw.trim() !== '') payload[key] = Number(raw);
  }
  const btn = $('heartModelBtn');
  btn.disabled = true;
  btn.textContent = 'Running model…';
  $('heartModelResult').textContent = '';
  try {
    const response = await fetch('/api/v1/models/heart-risk', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Model inference failed');
    const result = data.result || {};
    const score = result.estimated_positive_class_score;
    $('heartModelResult').className = 'form-result result-warn';
    $('heartModelResult').textContent =
      `Demo model output class: ${result.model_output_class}. ` +
      (score === null || score === undefined ? '' : `Model score: ${(score * 100).toFixed(1)}%. `) +
      'This is an educational model output only—not a diagnosis or clinical probability.';
  } catch (error) {
    $('heartModelResult').className = 'form-result result-warn';
    $('heartModelResult').textContent = error.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Run demo inference <span>→</span>';
  }
});
