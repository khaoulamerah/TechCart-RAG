/**
 * chat.js
 * ─────────────────────────────────────────────────────────
 * Rôle : le "cerveau" du frontend. Il ne touche jamais directement
 * au DOM (c'est le rôle de ui.js) ni au réseau (c'est le rôle de
 * api.js). Il ORCHESTRE les deux et gère l'ÉTAT de la conversation.
 *
 * Pourquoi séparer l'état ici ?
 * → C'est le même principe qu'un store Redux/Pinia, mais fait à la
 *   main : une seule fonction (sendUserMessage) décrit tout le
 *   cycle de vie d'un message, ce qui rend le flux facile à suivre
 *   et à déboguer.
 * → En gardant l'état en mémoire (`state`) plutôt que dispersé dans
 *   le DOM, on peut le sérialiser tel quel dans localStorage pour
 *   l'historique des conversations.
 */

const TechCartChat = (() => {
  const state = {
    conversationId: null,
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
    state.messages = conv.messages;

    TechCartUI.clearMessages();
    state.messages.forEach((m) => TechCartUI.renderMessage(m.role, m.content));
    TechCartUI.closeSidebarOnMobile();
    renderSidebarHistory();
  }

  function startNewConversation() {
    state.conversationId = generateId();
    state.messages = [];
    TechCartUI.clearMessages();
    TechCartUI.renderMessage("assistant", CONFIG.WELCOME_MESSAGE);
    TechCartUI.closeSidebarOnMobile();
    renderSidebarHistory();
  }

  /**
   * Cycle de vie complet de l'envoi d'un message :
   * 1. Valider la saisie
   * 2. Afficher le message utilisateur immédiatement (optimistic UI)
   * 3. Afficher l'indicateur "réflexion"
   * 4. Appeler le backend
   * 5. Remplacer l'indicateur par la réponse (avec effet machine à écrire)
   * 6. Gérer les erreurs à chaque étape critique
   */
  async function sendUserMessage(rawText) {
    const text = rawText.trim();
    if (!text || state.isSending) return;

    state.isSending = true;
    TechCartUI.setSendingState(true);

    // Étape 2 — affichage immédiat du message utilisateur.
    // On n'attend pas la réponse du serveur pour l'afficher : c'est
    // ce qu'on appelle une "optimistic UI", ça rend l'app plus réactive.
    TechCartUI.renderMessage("user", text);
    state.messages.push({ role: "user", content: text });
    TechCartUI.clearInput();

    // Étape 3
    const thinkingRow = TechCartUI.showThinkingIndicator();

    try {
      // Étape 4
      const { answer } = await TechCartAPI.sendMessage(
        text,
        state.conversationId
      );

      // Étape 5 — on retire l'indicateur et on crée une vraie bulle
      // de réponse dans laquelle on "tape" le texte.
      thinkingRow.remove();
      const bubble = TechCartUI.renderMessage("assistant", "");
      await TechCartUI.typeInto(bubble, answer || "Je n'ai pas de réponse à vous proposer pour le moment.");

      state.messages.push({ role: "assistant", content: answer });
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
