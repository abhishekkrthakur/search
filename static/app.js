document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("search-form");
  const queryInput = document.getElementById("query");
  const limitInput = document.getElementById("limit");
  const rankingSelect = document.getElementById("ranking");
  const status = document.getElementById("status");
  const resultsEl = document.getElementById("results");
  const button = document.getElementById("search-button");

  if (!form || !queryInput || !status || !resultsEl || !button) {
    return;
  }

  const renderStatus = (text, isError = false) => {
    status.textContent = text;
    status.style.color = isError ? "#f87171" : "var(--muted)";
  };

  const renderHits = (payload) => {
    const { hits = [], latency_ms = 0, total_available = 0, ranking_profile } = payload || {};
    resultsEl.innerHTML = "";

    if (!hits.length) {
      resultsEl.innerHTML = "<p class='status'>No results yet. Try a different query.</p>";
      return;
    }

    const summary = document.createElement("div");
    summary.className = "results-summary";
    summary.innerHTML = `
      <span><strong>${hits.length}</strong> shown</span>
      <span><strong>${total_available}</strong> total</span>
      <span>latency <strong>${latency_ms.toFixed(2)} ms</strong></span>
      ${ranking_profile ? `<span>ranking <strong>${ranking_profile}</strong></span>` : ""}
    `;
    resultsEl.appendChild(summary);

    hits.forEach((hit) => {
      const card = document.createElement("article");
      card.className = "hit";
      card.innerHTML = `
        <div class="meta">
          <span class="badge">relevance ${hit.relevance ?? 0}</span>
        </div>
        ${
          hit.url
            ? `<a href="${hit.url}" target="_blank" rel="noopener">${hit.url}</a>`
            : "<strong>Untitled result</strong>"
        }
        <p>${hit.snippet || "No preview available."}</p>
      `;
      resultsEl.appendChild(card);
    });
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    if (!query) {
      renderStatus("Please enter a query first.", true);
      return;
    }

    button.disabled = true;
    form.classList.add("loading");
    if (document.activeElement === queryInput) {
      queryInput.blur();
    }
    renderStatus("Searching…");
    resultsEl.innerHTML = "";

    const limitValue = limitInput ? parseInt(limitInput.value, 10) : undefined;
    const payloadBody = {
      query,
      limit: Number.isFinite(limitValue) ? limitValue : undefined,
      ranking: rankingSelect ? rankingSelect.value : undefined,
    };

    try {
      const response = await fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payloadBody),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Search failed");
      }
      renderStatus(`Showing ${payload.returned} of ${payload.total_available} results`);
      if (limitInput && typeof payload.limit === "number") {
        limitInput.value = payload.limit;
      }
      renderHits(payload);
    } catch (error) {
      console.error(error);
      renderStatus(error.message || "Something went wrong.", true);
    } finally {
      form.classList.remove("loading");
      button.disabled = false;
    }
  });
});
