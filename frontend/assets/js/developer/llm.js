"use strict";

const DeveloperLLM = (() => {
  function render(
    container,
    llm
  ) {
    if (!container) {
      return;
    }

    if (!llm) {
      container.innerHTML = `
        <p class="developer-empty">
          No LLM data.
        </p>
      `;

      return;
    }

    container.innerHTML = `
      <h3>LLM</h3>

      <div class="developer-info-grid">
        <div>
          <strong>Provider</strong>
          <p>
            ${escapeHtml(
              llm.provider ||
                "unknown"
            )}
          </p>
        </div>

        <div>
          <strong>Model</strong>
          <p>
            ${escapeHtml(
              llm.model ||
                "unknown"
            )}
          </p>
        </div>

        <div>
          <strong>First token</strong>
          <p>
            ${formatLatency(
              llm.time_to_first_token_ms
            )}
          </p>
        </div>

        <div>
          <strong>Total</strong>
          <p>
            ${formatLatency(
              llm.latency_ms
            )}
          </p>
        </div>
      </div>

      <h4>Response</h4>

      <pre class="developer-llm-response">${escapeHtml(
        llm.response || ""
      )}</pre>
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