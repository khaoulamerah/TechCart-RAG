const TechCartChat = (() => {
  const state = {
    conversationId: null,
    backendConversationId: null,
    sessionId: null,
    messages: [],
    isSending: false,
  };


  function generateId() {
    return `conv_${Date.now()}_${Math.random()
      .toString(36)
      .slice(2, 8)}`;
  }


  function loadConversations() {
    try {
      const raw = localStorage.getItem(
        CONFIG.STORAGE_KEY
      );

      return raw ? JSON.parse(raw) : [];
    } catch (_) {
      return [];
    }
  }


  function persistCurrentConversation() {
    if (state.messages.length === 0) {
      return;
    }

    const conversations = loadConversations();

    const firstUserMessage = state.messages.find(
      (message) => message.role === "user"
    );

    const title =
      firstUserMessage?.content?.slice(0, 40) ||
      "Nouvelle conversation";

    const existingIndex =
      conversations.findIndex(
        (conversation) =>
          conversation.id === state.conversationId
      );

    const record = {
      id: state.conversationId,

      backendConversationId:
        state.backendConversationId,

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
      (conversation) =>
        conversation.id === id
    );

    if (index === -1) {
      return;
    }

    conversations[index].title =
      newTitle;

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

    const conversation =
      conversations.find(
        (item) => item.id === id
      );

    if (!conversation) {
      return;
    }

    if (conversation.backendConversationId) {
      try {
        await TechCartAPI.deleteConversation(
          conversation.backendConversationId
        );
      } catch (error) {
        console.error(
          "Backend conversation deletion failed:",
          error
        );
      }
    }

    const remaining =
      conversations.filter(
        (item) => item.id !== id
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

    const conversation =
      conversations.find(
        (item) => item.id === id
      );

    if (!conversation) {
      return;
    }

    state.conversationId =
      conversation.id;

    state.backendConversationId =
      conversation.backendConversationId ??
      null;

    state.sessionId =
      conversation.sessionId ??
      null;

    state.messages =
      conversation.messages || [];

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
    state.conversationId =
      generateId();

    state.backendConversationId =
      null;

    state.sessionId =
      null;

    state.messages = [];

    TechCartUI.clearMessages();

    TechCartUI.renderMessage(
      "assistant",
      CONFIG.WELCOME_MESSAGE
    );

    TechCartUI.closeSidebarOnMobile();

    renderSidebarHistory();
  }


  /**
   * Send a user message and display the Ollama response
   * token-by-token.
   */
  async function sendUserMessage(rawText) {
    const text = rawText.trim();

    if (!text || state.isSending) {
      return;
    }

    state.isSending = true;

    TechCartUI.setSendingState(true);

    /*
     * 1. Display user message immediately.
     */
    TechCartUI.renderMessage(
      "user",
      text
    );

    state.messages.push({
      role: "user",
      content: text,
    });

    TechCartUI.clearInput();


    /*
     * 2. Show "thinking" indicator.
     */
    const thinkingRow =
      TechCartUI.showThinkingIndicator();


    /*
     * 3. Create the assistant bubble BEFORE
     *    the first token arrives.
     */
    const assistantBubble =
      TechCartUI.renderMessage(
        "assistant",
        ""
      );


    /*
     * Add a streaming state.
     */
    TechCartUI.startStreamingMessage(
      assistantBubble
    );


    let fullReply = "";

    try {
      /*
       * 4. Start real streaming.
       */
      const result =
        await TechCartAPI.streamMessage(
          text,

          state.sessionId,

          state.backendConversationId,

          /*
           * Called for EVERY token.
           */
          (chunk) => {
            /*
             * Remove "thinking..." when the
             * first real token arrives.
             */
            if (thinkingRow) {
              thinkingRow.remove();
            }

            fullReply += chunk;

            /*
             * Immediately display the token.
             */
            TechCartUI.appendToMessage(
              assistantBubble,
              chunk
            );
          },

          /*
           * Called when backend sends "done".
           */
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


      /*
       * 5. Use the final metadata returned by
       *    streamMessage().
       */
      state.backendConversationId =
        result.conversationId ??
        state.backendConversationId;

      state.sessionId =
        result.sessionId ??
        state.sessionId;

      fullReply =
        result.reply || fullReply;


      /*
       * 6. Finish streaming UI.
       */
      TechCartUI.finishStreamingMessage(
        assistantBubble
      );


      /*
       * 7. Save the complete assistant response.
       */
      if (fullReply) {
        state.messages.push({
          role: "assistant",
          content: fullReply,
        });
      }

      persistCurrentConversation();

    } catch (error) {
      console.error(
        "Chat streaming failed:",
        error
      );

      if (thinkingRow) {
        thinkingRow.remove();
      }

      /*
       * Remove the unfinished assistant bubble
       * if no content was received.
       */
      if (!fullReply) {
        assistantBubble
          ?.closest(".message-row")
          ?.remove();
      } else {
        TechCartUI.finishStreamingMessage(
          assistantBubble
        );
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
      return (
        "Impossible de joindre le serveur TechCart. " +
        "Vérifiez que le backend est démarré."
      );
    }

    if (error?.kind === "timeout") {
      return (
        "Le serveur met trop de temps à répondre. " +
        "Réessayez dans quelques instants."
      );
    }

    if (error?.kind === "stream") {
      return (
        "Le serveur n'a pas retourné un flux de réponse valide."
      );
    }

    if (error?.kind === "server") {
      return (
        error.detail ||
        error.message ||
        "Le serveur a rencontré une erreur."
      );
    }

    return (
      "Une erreur est survenue. Veuillez réessayer."
    );
  }


  function init() {
    const conversations =
      loadConversations();

    if (conversations.length > 0) {
      const latest =
        conversations.sort(
          (a, b) =>
            b.updatedAt - a.updatedAt
        )[0];

      openConversation(latest.id);
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