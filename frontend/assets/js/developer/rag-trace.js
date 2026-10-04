"use strict";

const DeveloperRAGTrace = (() => {
  function render(
    container,
    trace
  ) {
    if (!container) {
      return;
    }

    if (!trace) {
      container.innerHTML = `
        <p class="developer-empty">
          No trace selected.
        </p>
      `;

      return;
    }

    container.innerHTML = `
      <div class="developer-section-header">
        <div>
          <h2>RAG Trace</h2>

          <p>
            ${escapeHtml(
              trace.question
            )}
          </p>
        </div>

        <strong>
          ${formatLatency(
            trace.total_latency_ms
          )}
        </strong>
      </div>
    `;
  }

  function formatLatency(value) {
    if (
      value === null ||
      value === undefined
    ) {
      return "-";
    }

    const number = Number(value);

    if (number >= 1000) {
      return `${(
        number / 1000
      ).toFixed(2)} s`;
    }

    return `${number.toFixed(1)} ms`;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  return {
    render,
  };
})();