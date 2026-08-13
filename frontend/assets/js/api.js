const TechCartAPI = (() => {
  /**
   * @param {string} message - le message envoyé par l'utilisateur
   * @param {string|null} sessionId - session invité à continuer, ou null pour en créer une
   * @param {string|null} conversationId - conversation MongoDB à continuer, ou null pour en créer une
   * @returns {Promise<{reply: string, conversationId: string, sessionId: string}>}
   * @throws {APIError} en cas d'échec réseau, timeout ou erreur serveur
   */
  async function sendMessage(message, sessionId = null, conversationId = null) {
    const controller = new AbortController();

    const timeoutId = setTimeout(
      () => controller.abort(),
      CONFIG.REQUEST_TIMEOUT_MS
    );

    try {
      const response = await fetch(
        `${CONFIG.API_BASE_URL}${CONFIG.CHAT_ENDPOINT}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            session_id: sessionId,
            conversation_id: conversationId,
          }),
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        const status = response.status;
        let detail = "Erreur inconnue.";
        try {
          const errBody = await response.json();
          detail = errBody.detail || detail;
        } catch (_) {
        }
        throw new APIError(
          `Le serveur a répondu avec le statut ${status}`,
          status,
          detail
        );
      }

      const data = await response.json();

      return {
        reply: data.reply ?? "",
        conversationId: data.conversation_id,
        sessionId: data.session_id,
      };
    } catch (error) {
      clearTimeout(timeoutId);

      if (error.name === "AbortError") {
        throw new APIError(
          "Le serveur met trop de temps à répondre.",
          0,
          "timeout"
        );
      }
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        "Impossible de contacter le serveur TechCart.",
        0,
        "network"
      );
    }
  }

  /**
   * @param {string} conversationId - le VRAI conversation_id backend (pas l'ID local sidebar)
   * @throws {APIError} si le serveur refuse ou est injoignable
   */
  async function deleteConversation(conversationId) {
    const response = await fetch(
      `${CONFIG.API_BASE_URL}${CONFIG.CHAT_ENDPOINT}/conversations/${conversationId}`,
      { method: "DELETE" }
    );

    if (!response.ok) {
      let detail = "Erreur inconnue.";
      try {
        const errBody = await response.json();
        detail = errBody.detail || detail;
      } catch (_) {
        /* pas de corps JSON, on garde le message par défaut */
      }
      throw new APIError(
        `Le serveur a répondu avec le statut ${response.status}`,
        response.status,
        detail
      );
    }
  }

  return { sendMessage, deleteConversation };
})();


class APIError extends Error {
  constructor(message, statusCode, kind) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode; // 0 = pas de réponse HTTP du tout
    this.kind = kind; // "network" | "timeout" | "server" | undefined
  }
}