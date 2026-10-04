"use strict";

const DeveloperReranking = (() => {
  function render(
    container,
    reranking
  ) {
    if (!container) {
      return;
    }

    if (!reranking) {
      container.innerHTML = `
        <p class="developer-empty">
          No reranking data.
        </p>
      `;

      return;
    }

    const documents =
      reranking.documents || [];

    container.innerHTML = `
      <h3>Reranking</h3>

      <div class="developer-info-grid">
        <div>
          <strong>Model</strong>
          <p>
            ${escapeHtml(
              reranking.model ||
                "unknown"
            )}
          </p>
        </div>

        <div>
          <strong>Input</strong>
          <p>
            ${reranking.input_count || 0}
          </p>
        </div>

        <div>
          <strong>Output</strong>
          <p>
            ${reranking.output_count || 0}
          </p>
        </div>

        <div>
          <strong>Latency</strong>
          <p>
            ${formatLatency(
              reranking.latency_ms
            )}
          </p>
        </div>
      </div>

      <div class="developer-documents">
        ${documents
          .map(
            (document, index) => `
              <article
                class="developer-document"
              >
                <h4>
                  #${index + 1}
                  ${escapeHtml(
                    document.chunk_id
                  )}
                </h4>

                <div class="score-grid">
                  ${score(
                    "Original",
                    document.original_score
                  )}

                  ${score(
                    "Reranker",
                    document.rerank_score
                  )}
                </div>

                <pre>${escapeHtml(
                  document.text
                )}</pre>
              </article>
            `
          )
          .join("")}
      </div>
    `;
  }

  function score(
    label,
    value
  ) {
    return `
      <div class="developer-score">
        <span>${label}</span>
        <strong>
          ${
            value === null ||
            value === undefined
              ? "-"
              : Number(value).toFixed(4)
          }
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

    return `${Number(value).toFixed(
      1
    )} ms`;
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