"use strict";

const DeveloperRetrieval = (() => {
  function render(
    container,
    retrieval
  ) {
    if (!container) {
      return;
    }

    if (!retrieval) {
      container.innerHTML = `
        <p class="developer-empty">
          No retrieval data.
        </p>
      `;

      return;
    }

    const documents =
      retrieval.documents || [];

    container.innerHTML = `
      <h3>Retrieval</h3>

      <div class="developer-info-grid">
        <div>
          <strong>Embedding</strong>
          <p>
            ${escapeHtml(
              retrieval.embedding_model ||
                "unknown"
            )}
          </p>
        </div>

        <div>
          <strong>Top K</strong>
          <p>
            ${retrieval.top_k || 0}
          </p>
        </div>

        <div>
          <strong>Latency</strong>
          <p>
            ${formatLatency(
              retrieval.latency_ms
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

                <p>
                  Document:
                  ${escapeHtml(
                    document.document ||
                      "unknown"
                  )}
                </p>

                <div class="score-grid">
                  ${score(
                    "Vector",
                    document.vector_score
                  )}

                  ${score(
                    "BM25",
                    document.bm25_score
                  )}

                  ${score(
                    "Hybrid",
                    document.hybrid_score
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