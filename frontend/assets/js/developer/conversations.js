"use strict";

const DeveloperConversations = (() => {
  function render(
    container,
    conversations,
    onSelect
  ) {
    if (!container) {
      return;
    }

    container.innerHTML = "";

    if (
      !Array.isArray(conversations) ||
      conversations.length === 0
    ) {
      container.innerHTML = `
        <p class="developer-empty">
          No conversations found.
        </p>
      `;

      return;
    }

    conversations.forEach(
      (conversation) => {
        const button =
          document.createElement("button");

        button.type = "button";
        button.className =
          "developer-conversation";

        button.innerHTML = `
          <strong>
            ${escapeHtml(
              conversation.title ||
                "Conversation"
            )}
          </strong>

          <span>
            ${
              conversation.message_count ||
              0
            }
            messages
          </span>

          <small>
            ${formatDate(
              conversation.updated_at
            )}
          </small>
        `;

        button.addEventListener(
          "click",
          () => {
            onSelect(
              conversation.id
            );
          }
        );

        container.appendChild(
          button
        );
      }
    );
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatDate(value) {
    if (!value) {
      return "-";
    }

    return new Date(value)
      .toLocaleString();
  }

  return {
    render,
  };
})();