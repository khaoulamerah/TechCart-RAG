const TechCartChat = (() => {
  const state = {
    conversationId: null,
    backendConversationId: null,
    sessionId: null,
    messages: [],
    isSending: false,
  };

  function generateId() {
    return `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function loadConversations() {
    try {
      const raw = localStorage.getItem(CONFIG.STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (_) {
      return [];
    }
  }

  function persistCurrentConversation() {
    if (state.messages.length === 0) return;

    const conversations = loadConversations();

    const title =
      state.messages
        .find((m) => m.role === "user")
        ?.content.slice(0, 40) ||
      "Nouvelle conversation";

    const existingIndex = conversations.findIndex(
      (c) => c.id === state.conversationId
    );

    const record = {
      id: state.conversationId,
      backendConversationId: state.backendConversationId,
      sessionId: state.sessionId,
      title,
      messages: state.messages,
      updatedAt: Date.now(),
    };

    if (existingIndex >= 0) {
      conversations[existingIndex] = record;
    } else {
      conversations.unshift(record);
    }

    try {
      localStorage.setItem(
        CONFIG.STORAGE_KEY,
        JSON.stringify(conversations)
      );
    } catch (_) {
      // Ignore localStorage errors.
    }

    renderSidebarHistory();
  }

  function renderSidebarHistory() {
    const conversations = loadConversations().sort(
      (a, b) => b.updatedAt - a.updatedAt
    );

    TechCartUI.renderHistoryList(
      conversations,
      state.conversationId,
      {
        onSelect: openConversation,
        onRename: renameConversation,
        onDelete: deleteConversationById,
      }
    );
  }

  function renameConversation(id, newTitle) {
    const conversations = loadConversations();

    const index = conversations.findIndex(
      (c) => c.id === id
    );

    if (index === -1) return;

    conversations[index].title = newTitle;

    try {
      localStorage.setItem(
        CONFIG.STORAGE_KEY,
        JSON.stringify(conversations)
      );
    } catch (_) {
      // Ignore localStorage errors.
    }

    renderSidebarHistory();
  }

  async function deleteConversationById(id) {
    const conversations = loadConversations();

    const conv = conversations.find(
      (c) => c.id === id
    );

    if (!conv) return;

    if (conv.backendConversationId) {
      try {
        await TechCartAPI.deleteConversation(
          conv.backendConversationId
        );
      } catch (_) {
        // Backend deletion failure should not prevent
        // local conversation deletion.
      }
    }

    const remaining = conversations.filter(
      (c) => c.id !== id
    );

    try {
      localStorage.setItem(
        CONFIG.STORAGE_KEY,
        JSON.stringify(remaining)
      );
    } catch (_) {
      // Ignore localStorage errors.
    }

    if (state.conversationId === id) {
      const next = remaining.sort(
        (a, b) => b.updatedAt - a.updatedAt
      )[0];

      if (next) {
        openConversation(next.id);
      } else {
        startNewConversation();
      }
    } else {
      renderSidebarHistory();
    }
  }

  function openConversation(id) {
    const conversations = loadConversations();

    const conv = conversations.find(
      (c) => c.id === id
    );

    if (!conv) return;

    state.conversationId = conv.id;
    state.backendConversationId =
      conv.backendConversationId ?? null;
    state.sessionId =
      conv.sessionId ?? null;
    state.messages = conv.messages || [];

    TechCartUI.clearMessages();

    state.messages.forEach((message) => {
      TechCartUI.renderMessage(
        message.role,
        message.content
      );
    });

    TechCartUI.closeSidebarOnMobile();

    renderSidebarHistory();
  }

  function startNewConversation() {
    state.conversationId = generateId();
    state.backendConversationId = null;
    state.sessionId = null;
    state.messages = [];

    TechCartUI.clearMessages();

    TechCartUI.renderMessage(
      "assistant",
      CONFIG.WELCOME_MESSAGE
    );

    TechCartUI.closeSidebarOnMobile();

    renderSidebarHistory();
  }

  async function sendUserMessage(rawText) {
    const text = rawText.trim();

    if (!text || state.isSending) {
      return;
    }

    state.isSending = true;
    TechCartUI.setSendingState(true);

    // ─────────────────────────────────────────────
    // 1. Display user message immediately
    // ─────────────────────────────────────────────

    TechCartUI.renderMessage("user", text);

    state.messages.push({
      role: "user",
      content: text,
    });

    TechCartUI.clearInput();

    // ─────────────────────────────────────────────
    // 2. Display thinking indicator
    // ─────────────────────────────────────────────

    const thinkingRow =
      TechCartUI.showThinkingIndicator();

    try {
      // ───────────────────────────────────────────
      // 3. Create empty assistant bubble
      // ───────────────────────────────────────────

      const bubble =
        TechCartUI.renderMessage(
          "assistant",
          ""
        );

      let fullReply = "";

      // ───────────────────────────────────────────
      // 4. Start backend streaming
      // ───────────────────────────────────────────

      await TechCartAPI.streamMessage(
        text,
        state.sessionId,
        state.backendConversationId,

        // Called for every received chunk
        (chunk) => {
          // Remove thinking indicator when
          // the first real token arrives.
          if (thinkingRow) {
            thinkingRow.remove();
          }

          fullReply += chunk;

          // Display chunk immediately.
          TechCartUI.appendToMessage(
            bubble,
            chunk
          );
        },

        // Called when backend sends metadata
        (metadata) => {
          if (metadata.conversationId) {
            state.backendConversationId =
              metadata.conversationId;
          }

          if (metadata.sessionId) {
            state.sessionId =
              metadata.sessionId;
          }
        }
      );

      // ───────────────────────────────────────────
      // 5. Save complete assistant response
      // ───────────────────────────────────────────

      state.messages.push({
        role: "assistant",
        content: fullReply,
      });

      persistCurrentConversation();

    } catch (error) {
      if (thinkingRow) {
        thinkingRow.remove();
      }

      TechCartUI.renderErrorMessage(
        errorToUserMessage(error)
      );

    } finally {
      state.isSending = false;
      TechCartUI.setSendingState(false);
    }
  }

  function errorToUserMessage(error) {
    if (error?.kind === "network") {
      return "Impossible de joindre le serveur TechCart. Vérifiez que le backend est démarré.";
    }

    if (error?.kind === "timeout") {
      return "Le serveur met trop de temps à répondre. Réessayez dans quelques instants.";
    }

    return "Une erreur est survenue. Veuillez réessayer.";
  }

  function init() {
    const conversations =
      loadConversations();

    if (conversations.length > 0) {
      openConversation(
        conversations.sort(
          (a, b) => b.updatedAt - a.updatedAt
        )[0].id
      );
    } else {
      startNewConversation();
    }
  }

  return {
    init,
    sendUserMessage,
    startNewConversation,
  };
})();