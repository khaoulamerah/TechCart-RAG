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

      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
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
      "New chat";

    const existingIndex =
      conversations.findIndex(
        (conversation) =>
          conversation.id === state.conversationId
      );

    const existingConversation =
      existingIndex >= 0 ? conversations[existingIndex] : null;

    const record = {
      ...(existingConversation || {}),
      id: state.conversationId,
      backendConversationId:
        state.backendConversationId ??
        existingConversation?.backendConversationId ??
        null,
      sessionId:
        state.sessionId ?? existingConversation?.sessionId ?? null,
      // Keep a user-defined title when new messages are added.
      title: existingConversation?.isTitleCustom
        ? existingConversation.title
        : title,
      isTitleCustom: existingConversation?.isTitleCustom ?? false,
      isPinned: existingConversation?.isPinned ?? false,
      createdAt: existingConversation?.createdAt ?? Date.now(),
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
    const conversations = sortConversations(loadConversations());

    TechCartUI.renderHistoryList(
      conversations,
      state.conversationId,
      {
        onSelect: openConversation,
        onRename: renameConversation,
        onDelete: deleteConversationById,
        onPin: pinConversation,
        onShare: shareConversation,
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

    conversations[index].title = newTitle;
    conversations[index].isTitleCustom = true;
    conversations[index].updatedAt = Date.now();

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

    const confirmed = window.confirm(
      `Delete "${conversation.title || "New chat"}"? This action cannot be undone.`
    );
    if (!confirmed) {
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
      const next = sortConversations(remaining)[0];

      if (next) {
        openConversation(next.id);
      } else {
        startNewConversation();
      }
    } else {
      renderSidebarHistory();
    }
  }


  function sortConversations(conversations) {
    return [...conversations].sort((a, b) => {
      const pinOrder = Number(Boolean(b.isPinned)) - Number(Boolean(a.isPinned));
      if (pinOrder !== 0) {
        return pinOrder;
      }
      return (b.updatedAt || b.createdAt || 0) -
        (a.updatedAt || a.createdAt || 0);
    });
  }

  function pinConversation(id) {
    const conversations = loadConversations();
    const conversation = conversations.find((item) => item.id === id);
    if (!conversation) {
      return;
    }

    conversation.isPinned = !conversation.isPinned;

    try {
      localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(conversations));
    } catch (error) {
      console.error("Unable to save pinned conversation:", error);
      TechCartUI.showToast("Could not update the pinned state.", "error");
      return;
    }

    renderSidebarHistory();
    TechCartUI.showToast(
      conversation.isPinned ? "Conversation pinned." : "Conversation unpinned."
    );
  }

  async function shareConversation(id) {
    const conversation = loadConversations().find((item) => item.id === id);
    if (!conversation) {
      TechCartUI.showToast("Conversation not found.", "error");
      return;
    }

    const title = conversation.title || "TechCart conversation";
    const transcript = (conversation.messages || [])
      .map((message) => {
        const speaker = message.role === "user" ? "You" : "TechCart";
        return `${speaker}:\n${message.content || ""}`;
      })
      .join("\n\n");
    const shareText = `${title}\n\n${transcript}`.trim();

    if (!transcript) {
      TechCartUI.showToast("There are no messages to share yet.", "error");
      return;
    }

    // Native share is available on some browsers/devices. It shares the
    // conversation transcript, not a public URL to a hosted conversation.
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title, text: shareText });
        TechCartUI.showToast("Conversation shared.");
        return;
      } catch (error) {
        if (error?.name === "AbortError") {
          return; // The user cancelled the share sheet.
        }
        console.warn("Native sharing failed; trying clipboard:", error);
      }
    }

    try {
      await copyTextToClipboard(shareText);
      TechCartUI.showToast("Conversation copied to clipboard.");
    } catch (error) {
      console.error("Unable to share conversation:", error);
      TechCartUI.showToast(
        "Unable to share this conversation in this browser.",
        "error"
      );
    }
  }

  async function copyTextToClipboard(text) {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (_) {
        // Try the legacy fallback if clipboard permissions are unavailable.
      }
    }

    // Fallback for browsers without the Clipboard API or clipboard permission.
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    textarea.style.pointerEvents = "none";
    document.body.appendChild(textarea);
    textarea.select();

    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) {
      throw new Error("Clipboard copy was not successful.");
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
          },

          /*
           * Progress events keep the user informed while retrieval,
           * reranking or the first LLM token is taking time.
           */
          (status) => {
            TechCartUI.updateThinkingIndicator(
              thinkingRow,
              status
            );
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