
const TechCartChat = (() => {
  const state = {
    conversationId: null,       // local ID, only used as a localStorage key for the sidebar
    backendConversationId: null, // real MongoDB _id, returned by the backend
    sessionId: null,             // guest session_id, returned by the backend and reused
    messages: [], // { role: "user"|"assistant", content: string }
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
      // localStorage corrompu ou indisponible (mode navigation privée
      // stricte sur certains navigateurs) : on repart d'une liste vide
      // plutôt que de faire planter l'application.
      return [];
    }
  }

  function persistCurrentConversation() {
    if (state.messages.length === 0) return;

    const conversations = loadConversations();
    const title =
      state.messages.find((m) => m.role === "user")?.content.slice(0, 40) ||
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
      localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(conversations));
    } catch (_) {
      /* quota dépassé ou navigation privée : on ignore silencieusement,
         l'app reste fonctionnelle, seul l'historique n'est pas sauvegardé */
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
      openConversation
    );
  }

  function openConversation(id) {
    const conversations = loadConversations();
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;

    state.conversationId = conv.id;
    state.backendConversationId = conv.backendConversationId ?? null;
    state.sessionId = conv.sessionId ?? null;
    state.messages = conv.messages;

    TechCartUI.clearMessages();
    state.messages.forEach((m) => TechCartUI.renderMessage(m.role, m.content));
    TechCartUI.closeSidebarOnMobile();
    renderSidebarHistory();
  }

  function startNewConversation() {
    state.conversationId = generateId();
    state.backendConversationId = null;
    state.sessionId = null;
    state.messages = [];
    TechCartUI.clearMessages();
    TechCartUI.renderMessage("assistant", CONFIG.WELCOME_MESSAGE);
    TechCartUI.closeSidebarOnMobile();
    renderSidebarHistory();
  }


  async function sendUserMessage(rawText) {
    const text = rawText.trim();
    if (!text || state.isSending) return;

    state.isSending = true;
    TechCartUI.setSendingState(true);

    TechCartUI.renderMessage("user", text);
    state.messages.push({ role: "user", content: text });
    TechCartUI.clearInput();

    // Étape 3
    const thinkingRow = TechCartUI.showThinkingIndicator();

    try {
      // Étape 4 — on envoie les VRAIS identifiants backend (session_id /
      // backendConversationId), pas l'ID local utilisé pour la sidebar.
      const { reply, conversationId, sessionId } = await TechCartAPI.sendMessage(
        text,
        state.sessionId,
        state.backendConversationId
      );

      // Le backend fait autorité : on mémorise ce qu'il renvoie pour
      // que le prochain message de cette conversation continue le
      // même fil côté Mongo (get_or_create_by_session).
      state.backendConversationId = conversationId;
      state.sessionId = sessionId;

      // Étape 5 — on retire l'indicateur et on crée une vraie bulle
      // de réponse dans laquelle on "tape" le texte.
      thinkingRow.remove();
      const bubble = TechCartUI.renderMessage("assistant", "");
      await TechCartUI.typeInto(bubble, reply || "Je n'ai pas de réponse à vous proposer pour le moment.");

      state.messages.push({ role: "assistant", content: reply });
      persistCurrentConversation();
    } catch (error) {
      // Étape 6 — gestion différenciée des erreurs réseau.
      thinkingRow.remove();
      TechCartUI.renderErrorMessage(errorToUserMessage(error));
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
    const conversations = loadConversations();
    if (conversations.length > 0) {
      openConversation(conversations.sort((a, b) => b.updatedAt - a.updatedAt)[0].id);
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