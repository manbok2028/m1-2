const API = (window.APP_CONFIG?.API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const $ = (selector) => document.querySelector(selector);
let records = [];

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json", ...options.headers }, ...options });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "요청 처리에 실패했습니다.");
  return payload;
}

function formatValue(value, unit = "") { return `${Number(value).toFixed(3).replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1")}${unit}`; }
function escapeHtml(text) { const box = document.createElement("div"); box.textContent = text; return box.innerHTML; }

function renderSummary(summary) {
  $("#summary-content").innerHTML = [
    ["관측값", `${summary.count}건`], ["핵심 지표", summary.primary_indicator],
    ["최신값", formatValue(summary.metrics.latest_value, summary.primary_unit)], ["최근 추세", summary.trend],
  ].map(([label, value]) => `<div class="metric"><span>${label}</span><b>${escapeHtml(value)}</b></div>`).join("");
}

function addMessage(role, content, loading = false) {
  const label = role === "user" ? "나" : "체납리셋 Signal AI";
  const article = document.createElement("article");
  article.className = `message ${role}${loading ? " loading" : ""}`;
  article.innerHTML = `<strong>${label}</strong><p>${escapeHtml(content)}</p>`;
  $("#chat-messages").append(article);
  $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
  return article;
}

function renderRecords() {
  const recent = records.filter((record) => record.indicator === "household_delinquency_rate").slice(-30);
  $("#data-list").innerHTML = records.slice().reverse().slice(0, 15).map((record) => `
    <tr><td>${record.date}</td><td>${escapeHtml(record.indicator)}</td><td>${formatValue(record.value, record.unit)}</td><td>${escapeHtml(record.source)}</td><td>${escapeHtml(record.memo)}</td>
    <td><div class="row-actions"><button class="small-button" data-edit="${record.id}">수정</button><button class="small-button delete" data-delete="${record.id}">삭제</button></div></td></tr>`).join("");
  document.querySelectorAll("[data-edit]").forEach((button) => button.addEventListener("click", () => editRecord(button.dataset.edit)));
  document.querySelectorAll("[data-delete]").forEach((button) => button.addEventListener("click", () => deleteRecord(button.dataset.delete)));
  drawChart(recent);
}

function drawChart(items) {
  const canvas = $("#trend-chart"); const context = canvas.getContext("2d"); const { width, height } = canvas;
  context.clearRect(0, 0, width, height); if (!items.length) return;
  const values = items.map((item) => Number(item.value)); const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1;
  const ink = getComputedStyle(document.body).getPropertyValue("--accent"); const line = getComputedStyle(document.body).getPropertyValue("--line");
  context.strokeStyle = line; context.lineWidth = 1; [45, 120, 195].forEach((y) => { context.beginPath(); context.moveTo(35, y); context.lineTo(width - 15, y); context.stroke(); });
  context.strokeStyle = ink; context.lineWidth = 3; context.beginPath();
  values.forEach((value, index) => { const x = 35 + index * ((width - 50) / Math.max(values.length - 1, 1)); const y = 205 - ((value - min) / range) * 150; index ? context.lineTo(x, y) : context.moveTo(x, y); }); context.stroke();
  context.fillStyle = getComputedStyle(document.body).getPropertyValue("--muted"); context.font = "12px Arial"; context.fillText(`${min.toFixed(1)}h`, 0, 208); context.fillText(`${max.toFixed(1)}h`, 0, 45);
}

async function loadData() {
  records = await request("/api/data"); renderRecords();
  const summary = await request("/api/data/summary"); renderSummary(summary);
}

async function loadConversations() {
  const conversations = await request("/api/conversations"); $("#conversation-count").textContent = `${conversations.length}개`;
  $("#conversation-list").innerHTML = conversations.length ? conversations.map((item) => `<button class="conversation-item" data-conversation="${item.id}"><b>${escapeHtml(item.title)}</b><span>${item.messages.length}개 메시지 · ${String(item.created_at || "").slice(0, 10)}</span></button>`).join("") : "<p>저장된 대화가 없습니다.</p>";
  document.querySelectorAll("[data-conversation]").forEach((button) => button.addEventListener("click", () => loadConversation(button.dataset.conversation)));
}

async function loadConversation(id) {
  const conversation = await request(`/api/conversations/${id}`);
  $("#loaded-conversation").innerHTML = `<h3>${escapeHtml(conversation.title)}</h3>`;
  conversation.messages.forEach((message) => { const article = document.createElement("article"); article.className = `message ${message.role}`; article.innerHTML = `<strong>${message.role === "user" ? "나" : "체납리셋 Signal AI"}</strong><p>${escapeHtml(message.content)}</p>`; $("#loaded-conversation").append(article); });
}

function editRecord(id) {
  const record = records.find((item) => item.id === id); if (!record) return;
  $("#record-id").value = record.id; $("#record-date").value = record.date; $("#record-indicator").value = record.indicator; $("#record-value").value = record.value; $("#record-unit").value = record.unit; $("#record-source").value = record.source; $("#record-memo").value = record.memo;
  $("#record-submit").textContent = "기록 수정"; $("#record-cancel").hidden = false; $("#data").scrollIntoView({ behavior: "smooth" });
}

async function deleteRecord(id) {
  if (!confirm("이 지표 관측값을 삭제할까요?")) return;
  try { await request(`/api/data/${id}`, { method: "DELETE" }); await loadData(); } catch (error) { $("#data-error").textContent = error.message; }
}

function resetRecordForm() { $("#data-form").reset(); $("#record-id").value = ""; $("#record-submit").textContent = "기록 추가"; $("#record-cancel").hidden = true; }
function exportCsv() { const rows = [["date", "indicator", "value", "unit", "source", "memo"], ...records.map((item) => [item.date, item.indicator, item.value, item.unit, item.source, item.memo])]; const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n"); const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" })); link.download = "tax-reset-macro-signals.csv"; link.click(); URL.revokeObjectURL(link.href); }

$("#chat-form").addEventListener("submit", async (event) => { event.preventDefault(); const question = $("#question").value.trim(); if (!question) return; $("#chat-error").textContent = ""; addMessage("user", question); $("#question").value = ""; const loading = addMessage("assistant", "거시경제 지표를 요약해 답변을 만드는 중…", true); try { const response = await request("/api/chat", { method: "POST", body: JSON.stringify({ question }) }); loading.remove(); const toolNotice = response.tools_used?.length ? `\n\n[이번 답변에서 조회한 내부 도구: ${response.tools_used.join(", ")}]` : ""; addMessage("assistant", `${response.answer}${toolNotice}`); renderSummary(response.summary); await loadConversations(); } catch (error) { loading.remove(); $("#chat-error").textContent = `답변을 가져오지 못했습니다: ${error.message}`; } });
$("#data-form").addEventListener("submit", async (event) => { event.preventDefault(); const id = $("#record-id").value; const payload = { date: $("#record-date").value, indicator: $("#record-indicator").value, value: Number($("#record-value").value), unit: $("#record-unit").value.trim(), source: $("#record-source").value.trim(), memo: $("#record-memo").value.trim() }; try { await request(id ? `/api/data/${id}` : "/api/data", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) }); resetRecordForm(); await loadData(); } catch (error) { $("#data-error").textContent = error.message; } });
$("#record-cancel").addEventListener("click", resetRecordForm); $("#export-csv").addEventListener("click", exportCsv);
$("#theme-toggle").addEventListener("click", () => { document.body.classList.toggle("dark"); localStorage.setItem("tax-reset-theme", document.body.classList.contains("dark") ? "dark" : "light"); drawChart(records.filter((record) => record.indicator === "household_delinquency_rate").slice(-30)); });
if (localStorage.getItem("tax-reset-theme") === "dark") document.body.classList.add("dark");
Promise.all([loadData(), loadConversations()]).then(() => { $("#connection-status").textContent = "데이터와 연결되었습니다"; }).catch((error) => { $("#connection-status").textContent = "서버 연결을 확인하세요"; $("#chat-error").textContent = error.message; });
