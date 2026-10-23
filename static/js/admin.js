const dateInput = document.getElementById("report-date");
const today = new Date();
dateInput.value = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0,10);
async function getJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}
document.getElementById("load-daily").addEventListener("click", async () => {
  const out = document.getElementById("daily-results");
  out.textContent = "Loading…";
  try {
    const d = await getJson(`/admin/api/daily?date=${encodeURIComponent(dateInput.value)}`);
    out.innerHTML = "";
    const items = [
      ["Unique players", d.unique_players],
      ["Games started", d.games_started],
      ["Games won", d.games_won],
      ["Exact correct submissions", d.exact_correct_submissions]
    ];
    items.forEach(([label, value]) => {
      const div = document.createElement("div"); div.className = "metric";
      const title = document.createElement("span"); title.textContent = label;
      const strong = document.createElement("strong"); strong.textContent = value;
      div.append(title, strong); out.appendChild(div);
    });
  } catch (e) { out.textContent = e.message; }
});
async function loadPlayers() {
  const select = document.getElementById("player-select");
  try {
    const data = await getJson("/admin/api/users");
    select.innerHTML = '<option value="">Choose a player</option>';
    data.users.forEach(user => {
      const option = document.createElement("option");
      option.value = user.id; option.textContent = user.username; select.appendChild(option);
    });
  } catch (e) { select.innerHTML = `<option>${e.message}</option>`; }
}
document.getElementById("load-user").addEventListener("click", async () => {
  const select = document.getElementById("player-select");
  const out = document.getElementById("user-results");
  if (!select.value) { out.textContent = "Choose a player first."; return; }
  out.textContent = "Loading…";
  try {
    const d = await getJson(`/admin/api/user-report?user_id=${encodeURIComponent(select.value)}`);
    out.innerHTML = "";
    const table = document.createElement("table");
    table.innerHTML = "<thead><tr><th>Date</th><th>Games started</th><th>Games won</th><th>Exact correct submissions</th><th>Guesses submitted</th></tr></thead>";
    const tbody = document.createElement("tbody");
    d.days.forEach(day => {
      const tr = document.createElement("tr");
      [day.date, day.games_started, day.games_won, day.exact_correct_submissions, day.guesses_submitted].forEach(value => {
        const td = document.createElement("td"); td.textContent = value; tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody); out.appendChild(table);
    if (!d.days.length) out.textContent = "No games found for this player.";
  } catch (e) { out.textContent = e.message; }
});
loadPlayers();
document.getElementById("load-daily").click();
