"use strict";

const DeveloperApp = (() => {
  const state = {
    conversations: [],
    selectedConversation: null,
    traces: [],
    selectedTrace: null,
  };

  const elements = {};

  function initialize() {
    cacheElements();
    bindEvents();
  }

  function cacheElements() {
    elements.page =
      document.getElementById(
        "developer-page"
      );

    elements.conversations =
      document.getElementById(
        "developer-conversations"
      );

    elements.conversation =
      document.getElementById(
        "developer-conversation-detail"
      );

    elements.traces =
      document.getElementById(
        "developer-traces"
      );

    elements.trace =
      document.getElementById(
        "developer-trace-detail"
      );

    elements.error =
      document.getElementById(
        "developer-error"
      );

    elements.refresh =
      document.getElementById(
        "developer-refresh"
      );
  }

  function bindEvents() {
    if (elements.refresh) {
      elements.refresh.addEventListener(
        "click",
        () => {
          loadConversations().catch(
            showError
          );
        }
      );
    }
  }

  async function loadConversations() {
    clearError();

    setLoading(
      elements.conversations,
      "Loading conversations..."
    );

    try {
      const conversations =
        await getDeveloperConversations(
          100
        );

      state.conversations =
        Array.isArray(conversations)
          ? conversations
          : [];

      renderConversations();

    } catch (error) {
      showError(error);

      renderEmpty(
        elements.conversations,
        "Unable to load conversations."
      );
    }
  }

  async function selectConversation(
    conversationId
  ) {
    clearError();

    state.selectedConversation = null;
    state.traces = [];
    state.selectedTrace = null;

    renderConversationLoading();
    renderTraceListLoading();
    renderTraceLoading();

    try {
      const [
        conversation,
        traces,
      ] = await Promise.all([
        getDeveloperConversation(
          conversationId
        ),

        getConversationTraces(
          conversationId
        ),
      ]);

      state.selectedConversation =
        conversation;

      state.traces =
        Array.isArray(traces)
          ? traces
          : [];

      renderConversation();
      renderTraceList();

      if (state.traces.length > 0) {
        await selectTrace(
          state.traces[0].id
        );
      } else {
        renderNoTrace();
      }

    } catch (error) {
      showError(error);
    }
  }

  async function selectTrace(traceId) {
    clearError();

    renderTraceLoading();

    try {
      const trace =
        await getRAGTrace(traceId);

      state.selectedTrace = trace;

      renderTrace();

    } catch (error) {
      showError(error);
    }
  }

  function renderConversations() {
    if (!elements.conversations) {
      return;
    }

    if (
      state.conversations.length === 0
    ) {
      renderEmpty(
        elements.conversations,
        "No conversations found."
      );

      return;
    }

    elements.conversations.innerHTML = "";

    state.conversations.forEach(
      (conversation) => {
        const button =
          document.createElement("button");

        button.type = "button";

        button.className =
          "developer-conversation";

        button.dataset.id =
          conversation.id;

        button.innerHTML = `
          <span class="conversation-title">
            ${escapeHtml(
              conversation.title ||
                "Conversation"
            )}
          </span>

          <span class="conversation-meta">
            ${
              Number(
                conversation.message_count ||
                  0
              )
            } messages
          </span>

          <span class="conversation-date">
            ${formatDate(
              conversation.updated_at
            )}
          </span>
        `;

        button.addEventListener(
          "click",
          () => {
            selectConversation(
              conversation.id
            );
          }
        );

        elements.conversations.appendChild(
          button
        );
      }
    );
  }

  function renderConversation() {
    if (!elements.conversation) {
      return;
    }

    const conversation =
      state.selectedConversation;

    if (!conversation) {
      renderEmpty(
        elements.conversation,
        "Select a conversation."
      );

      return;
    }

    const messages =
      Array.isArray(
        conversation.messages
      )
        ? conversation.messages
        : [];

    elements.conversation.innerHTML = `
      <div class="developer-section-header">
        <div>
          <h2>
            ${escapeHtml(
              conversation.title ||
                "Conversation"
            )}
          </h2>

          <p>
            Conversation ID:
            <code>
              ${escapeHtml(
                conversation.id
              )}
            </code>
          </p>
        </div>

        <span class="developer-badge">
          ${messages.length} messages
        </span>
      </div>

      <div class="developer-messages">
        ${
          messages.length === 0
            ? `
              <p class="developer-empty">
                No messages.
              </p>
            `
            : messages
                .map(
                  renderMessage
                )
                .join("")
        }
      </div>
    `;
  }

  function renderMessage(message) {
    const role =
      message.role || "unknown";

    const content =
      message.content || "";

    return `
      <article
        class="developer-message
        developer-message-${escapeHtml(
          role
        )}"
      >
        <div class="developer-message-role">
          ${escapeHtml(role)}
        </div>

        <div class="developer-message-content">
          ${escapeHtml(content)}
        </div>
      </article>
    `;
  }

  function renderTraceList() {
    if (!elements.traces) {
      return;
    }

    elements.traces.innerHTML = `
      <div class="developer-section-header">
        <h2>RAG Requests</h2>

        <span class="developer-badge">
          ${state.traces.length}
        </span>
      </div>
    `;

    if (state.traces.length === 0) {
      elements.traces.innerHTML += `
        <p class="developer-empty">
          No RAG traces found.
        </p>
      `;

      return;
    }

    const list =
      document.createElement("div");

    list.className =
      "developer-trace-list";

    state.traces.forEach(
      (trace) => {
        const button =
          document.createElement("button");

        button.type = "button";

        button.className =
          "developer-trace-item";

        button.innerHTML = `
          <div>
            <strong>
              ${escapeHtml(
                trace.question ||
                  "Unknown question"
              )}
            </strong>

            <small>
              ${formatDate(
                trace.created_at
              )}
            </small>
          </div>

          <div class="trace-summary">
            <span>
              ${formatLatency(
                trace.total_latency_ms
              )}
            </span>

            <span
              class="trace-status
              trace-status-${escapeHtml(
                trace.status ||
                  "unknown"
              )}"
            >
              ${escapeHtml(
                trace.status ||
                  "unknown"
              )}
            </span>
          </div>
        `;

        button.addEventListener(
          "click",
          () => {
            selectTrace(trace.id);
          }
        );

        list.appendChild(button);
      }
    );

    elements.traces.appendChild(list);
  }

  function renderTrace() {
    if (!elements.trace) {
      return;
    }

    const trace =
      state.selectedTrace;

    if (!trace) {
      renderNoTrace();
      return;
    }

    elements.trace.innerHTML = `
      <div class="developer-section-header">
        <div>
          <h2>RAG Trace</h2>

          <p>
            ${escapeHtml(
              trace.question ||
                ""
            )}
          </p>
        </div>

        <span class="developer-badge">
          ${formatLatency(
            trace.total_latency_ms
          )}
        </span>
      </div>

      <div class="developer-tabs">
        <button
          type="button"
          class="developer-tab active"
          data-tab="overview"
        >
          Overview
        </button>

        <button
          type="button"
          class="developer-tab"
          data-tab="retrieval"
        >
          Retrieval
        </button>

        <button
          type="button"
          class="developer-tab"
          data-tab="reranking"
        >
          Reranking
        </button>

        <button
          type="button"
          class="developer-tab"
          data-tab="context"
        >
          Context
        </button>

        <button
          type="button"
          class="developer-tab"
          data-tab="llm"
        >
          LLM
        </button>
      </div>

      <div
        id="developer-tab-content"
        class="developer-tab-content"
      ></div>
    `;

    const tabs =
      elements.trace.querySelectorAll(
        ".developer-tab"
      );

    tabs.forEach((tab) => {
      tab.addEventListener(
        "click",
        () => {
          tabs.forEach(
            (item) =>
              item.classList.remove(
                "active"
              )
          );

          tab.classList.add(
            "active"
          );

          renderTab(
            tab.dataset.tab
          );
        }
      );
    });

    renderTab("overview");
  }

  function renderTab(tabName) {
    const container =
      document.getElementById(
        "developer-tab-content"
      );

    if (!container) {
      return;
    }

    switch (tabName) {
      case "overview":
        renderOverview(container);
        break;

      case "retrieval":
        renderRetrieval(container);
        break;

      case "reranking":
        renderReranking(container);
        break;

      case "context":
        renderContext(container);
        break;

      case "llm":
        renderLLM(container);
        break;

      default:
        renderOverview(container);
    }
  }

  function renderOverview(container) {
    const trace =
      state.selectedTrace;

    container.innerHTML = `
      <div class="developer-metrics">
        ${metricCard(
          "Total",
          formatLatency(
            trace.total_latency_ms
          )
        )}

        ${metricCard(
          "Retrieval",
          formatLatency(
            trace.retrieval?.latency_ms
          )
        )}

        ${metricCard(
          "Reranking",
          formatLatency(
            trace.reranking?.latency_ms
          )
        )}

        ${metricCard(
          "LLM",
          formatLatency(
            trace.llm?.latency_ms
          )
        )}
      </div>

      <div class="developer-info-grid">
        <div>
          <strong>Status</strong>
          <p>
            ${escapeHtml(
              trace.status ||
                "unknown"
            )}
          </p>
        </div>

        <div>
          <strong>Conversation</strong>
          <p>
            <code>
              ${escapeHtml(
                trace.conversation_id ||
                  ""
              )}
            </code>
          </p>
        </div>
      </div>
    `;
  }

  function renderRetrieval(container) {
    const retrieval =
      state.selectedTrace
        ?.retrieval;

    if (!retrieval) {
      renderEmpty(
        container,
        "No retrieval information recorded."
      );

      return;
    }

    container.innerHTML = `
      <div class="trace-header">
        <h3>Retrieval</h3>

        <div class="developer-info-grid">
          <div>
            <strong>Embedding model</strong>
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
              ${retrieval.top_k ?? 0}
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
      </div>

      <div class="developer-documents">
        ${
          (
            retrieval.documents || []
          )
            .map(
              (document, index) => `
                <article
                  class="developer-document"
                >
                  <div
                    class="document-header"
                  >
                    <strong>
                      #${index + 1}
                      ${escapeHtml(
                        document.chunk_id ||
                          ""
                      )}
                    </strong>
                  </div>

                  <p>
                    Document:
                    ${escapeHtml(
                      document.document ||
                        "unknown"
                    )}
                  </p>

                  <div class="score-grid">
                    ${scoreCard(
                      "Vector",
                      document.vector_score
                    )}

                    ${scoreCard(
                      "BM25",
                      document.bm25_score
                    )}

                    ${scoreCard(
                      "Hybrid",
                      document.hybrid_score
                    )}
                  </div>

                  <pre>${escapeHtml(
                    document.text ||
                      ""
                  )}</pre>
                </article>
              `
            )
            .join("")
        }
      </div>
    `;
  }

  function renderReranking(container) {
    const reranking =
      state.selectedTrace
        ?.reranking;

    if (!reranking) {
      renderEmpty(
        container,
        "No reranking information recorded."
      );

      return;
    }

    container.innerHTML = `
      <div class="trace-header">
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
              ${reranking.input_count ?? 0}
              candidates
            </p>
          </div>

          <div>
            <strong>Output</strong>
            <p>
              ${reranking.output_count ?? 0}
              documents
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
      </div>

      <div class="developer-documents">
        ${
          (
            reranking.documents || []
          )
            .map(
              (document, index) => `
                <article
                  class="developer-document"
                >
                  <div
                    class="document-header"
                  >
                    <strong>
                      #${index + 1}
                      ${escapeHtml(
                        document.chunk_id ||
                          ""
                      )}
                    </strong>
                  </div>

                  <div class="score-grid">
                    ${scoreCard(
                      "Original",
                      document.original_score
                    )}

                    ${scoreCard(
                      "Reranker",
                      document.rerank_score
                    )}
                  </div>

                  <pre>${escapeHtml(
                    document.text ||
                      ""
                  )}</pre>
                </article>
              `
            )
            .join("")
        }
      </div>
    `;
  }

  function renderContext(container) {
    const context =
      state.selectedTrace
        ?.context || [];

    container.innerHTML = `
      <h3>
        Context sent to LLM
      </h3>

      ${
        context.length === 0
          ? `
            <p class="developer-empty">
              No context recorded.
            </p>
          `
          : context
              .map(
                (item, index) => `
                  <article
                    class="developer-context"
                  >
                    <h4>
                      Chunk ${index + 1}
                    </h4>

                    <pre>${escapeHtml(
                      item
                    )}</pre>
                  </article>
                `
              )
              .join("")
      }
    `;
  }

  function renderLLM(container) {
    const llm =
      state.selectedTrace?.llm;

    if (!llm) {
      renderEmpty(
        container,
        "No LLM information recorded."
      );

      return;
    }

    container.innerHTML = `
      <div class="trace-header">
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
      </div>

      <h3>Response</h3>

      <pre class="developer-llm-response">${escapeHtml(
        llm.response || ""
      )}</pre>
    `;
  }

  function metricCard(
    label,
    value
  ) {
    return `
      <div class="developer-metric">
        <span>${label}</span>
        <strong>${value}</strong>
      </div>
    `;
  }

  function scoreCard(
    label,
    value
  ) {
    return `
      <div class="developer-score">
        <span>${label}</span>
        <strong>
          ${formatScore(value)}
        </strong>
      </div>
    `;
  }

  function renderConversationLoading() {
    if (elements.conversation) {
      setLoading(
        elements.conversation,
        "Loading conversation..."
      );
    }
  }

  function renderTraceListLoading() {
    if (elements.traces) {
      setLoading(
        elements.traces,
        "Loading RAG traces..."
      );
    }
  }

  function renderTraceLoading() {
    if (elements.trace) {
      setLoading(
        elements.trace,
        "Loading trace..."
      );
    }
  }

  function renderNoTrace() {
    if (elements.trace) {
      renderEmpty(
        elements.trace,
        "Select a RAG request."
      );
    }
  }

  function renderEmpty(
    element,
    message
  ) {
    if (!element) {
      return;
    }

    element.innerHTML = `
      <p class="developer-empty">
        ${escapeHtml(message)}
      </p>
    `;
  }

  function setLoading(
    element,
    message
  ) {
    if (!element) {
      return;
    }

    element.innerHTML = `
      <p class="developer-loading">
        ${escapeHtml(message)}
      </p>
    `;
  }

  function showError(error) {
    console.error(
      "Developer interface:",
      error
    );

    if (elements.error) {
      elements.error.textContent =
        error?.message ||
        "An unexpected error occurred.";
    }
  }

  function clearError() {
    if (elements.error) {
      elements.error.textContent = "";
    }
  }

  function formatLatency(value) {
    if (
      value === null ||
      value === undefined ||
      Number.isNaN(Number(value))
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

  function formatScore(value) {
    if (
      value === null ||
      value === undefined
    ) {
      return "-";
    }

    return Number(value).toFixed(4);
  }

  function formatDate(value) {
    if (!value) {
      return "-";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(date.getTime())
    ) {
      return "-";
    }

    return date.toLocaleString();
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
    initialize,
    loadConversations,
    selectConversation,
    selectTrace,
  };
})();

