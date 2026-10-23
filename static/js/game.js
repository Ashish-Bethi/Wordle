let gameId = null;
let guessCount = 0;
let finished = true;
const board = document.getElementById("board");
const input = document.getElementById("guess-input");
const submitButton = document.getElementById("submit-guess");
const newButton = document.getElementById("new-game");
const statusEl = document.getElementById("status");
const modal = document.getElementById("result-modal");

function drawBoard() {
  board.innerHTML = "";
  for (let r = 0; r < 5; r++) {
    const row = document.createElement("div");
    row.className = "board-row";
    for (let c = 0; c < 5; c++) {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.id = `tile-${r}-${c}`;
      row.appendChild(tile);
    }
    board.appendChild(row);
  }
}
function showModal(message) {
  document.getElementById("result-message").textContent = message;
  modal.classList.remove("hidden");
  document.getElementById("modal-ok").focus();
}
function endGame() {
  finished = true;
  input.disabled = true;
  submitButton.disabled = true;
  newButton.disabled = false;
}
async function startGame() {
  statusEl.textContent = "";
  const response = await fetch("/api/games", {method:"POST", headers:{"Content-Type":"application/json", "X-CSRFToken": csrfToken()}});
  const data = await response.json();
  if (!response.ok) { statusEl.textContent = data.error || "Could not start a game."; return; }
  gameId = data.game_id;
  guessCount = 0;
  finished = false;
  drawBoard();
  input.value = "";
  input.disabled = false;
  submitButton.disabled = false;
  newButton.disabled = true;
  input.focus();
}
function csrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || getCookie("csrf_token") || "";
}
function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : "";
}
async function submitGuess() {
  if (finished || !gameId) return;
  const word = input.value;
  if (!/^[A-Z]{5}$/.test(word)) { statusEl.textContent = "Enter exactly five uppercase English letters."; return; }
  submitButton.disabled = true;
  const response = await fetch(`/api/games/${gameId}/guesses`, {
    method:"POST", headers:{"Content-Type":"application/json", "X-CSRFToken": csrfToken()},
    body:JSON.stringify({word})
  });
  const data = await response.json();
  submitButton.disabled = false;
  if (!response.ok) { statusEl.textContent = data.error || "Guess rejected."; return; }
  const row = data.guess_number - 1;
  [...word].forEach((letter, col) => {
    const tile = document.getElementById(`tile-${row}-${col}`);
    tile.textContent = letter;
    tile.classList.add(data.feedback[col]);
  });
  guessCount = data.guess_number;
  input.value = "";
  statusEl.textContent = data.status === "in_progress" ? `${5 - guessCount} guesses remaining.` : "";
  if (data.status !== "in_progress") {
    endGame();
    showModal(data.message || (data.won ? "Congratulations!" : "Better luck next time."));
  } else input.focus();
}
newButton.addEventListener("click", startGame);
submitButton.addEventListener("click", submitGuess);
input.addEventListener("keydown", e => { if (e.key === "Enter") submitGuess(); });
input.addEventListener("input", () => { input.value = input.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0,5); });
document.getElementById("modal-ok").addEventListener("click", () => modal.classList.add("hidden"));
drawBoard();
input.disabled = true;
submitButton.disabled = true;
