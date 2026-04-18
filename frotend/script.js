/* DHgate Scraper – Frontend Script */

const API_BASE = "http://localhost:8000";

let lastQuery = "";
let lastPages = 1;

// ── DOM refs ────────────────────────────────────────────────────
const searchInput  = document.getElementById("searchInput");
const pagesSelect  = document.getElementById("pagesSelect");
const searchBtn    = document.getElementById("searchBtn");
const statusBar    = document.getElementById("statusBar");
const resultsSection = document.getElementById("resultsSection");
const resultsBody  = document.getElementById("resultsBody");
const resultCount  = document.getElementById("resultCount");
const emptyState   = document.getElementById("emptyState");
const errorState   = document.getElementById("errorState");
const errorMsg     = document.getElementById("errorMsg");

// ── Enter key ───────────────────────────────────────────────────
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

// ── Main search ─────────────────────────────────────────────────
async function runSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    showStatus("Por favor insere um termo de pesquisa.", "warning");
    return;
  }

  lastQuery = query;
  lastPages = parseInt(pagesSelect.value, 10);

  setLoading(true);
  hideAll();
  showStatus(`<span class="spinner"></span>A pesquisar "<strong>${escHtml(query)}</strong>"…`, "loading");

  try {
    const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(query)}&pages=${lastPages}`);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Erro HTTP ${res.status}`);
    }

    const data = await res.json();

    if (!data.products || data.products.length === 0) {
      showEmpty();
      showStatus("Nenhum produto encontrado.", "warning");
      return;
    }

    renderTable(data.products);
    resultCount.textContent = `${data.total} produto(s) encontrado(s) para "${query}"`;
    resultsSection.classList.remove("hidden");
    showStatus(`✅ ${data.total} produtos encontrados!`, "success");

  } catch (err) {
    showError(err.message);
    showStatus(`❌ ${err.message}`, "warning");
  } finally {
    setLoading(false);
  }
}

// ── Render table ─────────────────────────────────────────────────
function renderTable(products) {
  resultsBody.innerHTML = products.map(p => `
    <tr>
      <td>
        ${p.image
          ? `<img src="${escHtml(p.image)}" alt="produto" loading="lazy" onerror="this.src='https://via.placeholder.com/60?text=N%2FA'; this.classList.add('placeholder')">`
          : `<img src="https://via.placeholder.com/60?text=N%2FA" class="placeholder" alt="sem imagem">`
        }
      </td>
      <td class="name-cell">${escHtml(p.name)}</td>
      <td class="price-cell">${escHtml(p.price)}</td>
      <td class="rating-cell">${escHtml(p.rating)}</td>
      <td class="seller-cell">${escHtml(p.seller)}</td>
      <td>${escHtml(p.orders)}</td>
      <td>
        ${p.link && p.link !== "N/A"
          ? `<a href="${escHtml(p.link)}" target="_blank" rel="noopener noreferrer">Ver produto ↗</a>`
          : "N/A"
        }
      </td>
    </tr>
  `).join("");
}

// ── Export Excel ─────────────────────────────────────────────────
async function exportExcel() {
  if (!lastQuery) {
    alert("Faz uma pesquisa primeiro.");
    return;
  }

  showStatus(`<span class="spinner"></span>A gerar ficheiro Excel…`, "loading");

  try {
    const res = await fetch(
      `${API_BASE}/export/excel?query=${encodeURIComponent(lastQuery)}&pages=${lastPages}`
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Erro HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `dhgate_${lastQuery.replace(/\s+/g, "_")}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);

    showStatus("✅ Excel exportado com sucesso!", "success");
  } catch (err) {
    showStatus(`❌ ${err.message}`, "warning");
  }
}

// ── Copy table ───────────────────────────────────────────────────
function copyTable() {
  const rows = [...document.querySelectorAll("#resultsTable tr")];
  const tsv = rows.map(row =>
    [...row.querySelectorAll("th, td")]
      .filter((_, i) => i !== 0) // skip image column
      .map(cell => cell.innerText.trim())
      .join("\t")
  ).join("\n");

  navigator.clipboard.writeText(tsv)
    .then(() => showStatus("✅ Tabela copiada para a área de transferência!", "success"))
    .catch(() => showStatus("❌ Não foi possível copiar.", "warning"));
}

// ── UI helpers ───────────────────────────────────────────────────
function setLoading(on) {
  searchBtn.disabled = on;
  searchBtn.textContent = on ? "⏳ A pesquisar…" : "🔍 Pesquisar";
}

function hideAll() {
  resultsSection.classList.add("hidden");
  emptyState.classList.add("hidden");
  errorState.classList.add("hidden");
}

function showEmpty() {
  emptyState.classList.remove("hidden");
}

function showError(msg) {
  errorMsg.textContent = `❌ ${msg}`;
  errorState.classList.remove("hidden");
}

function showStatus(html, type = "") {
  statusBar.innerHTML = html;
  statusBar.className = `status-bar ${type}`;
  statusBar.classList.remove("hidden");
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
