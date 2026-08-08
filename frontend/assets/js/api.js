
const TechCartAPI = (() => {
  /**
   * @param {string} message 
   * @param {string|null} sessionId 
   * @param {string|null} conversationId 
   * @returns {Promise<{reply: string, conversationId: string, sessionId: string}>}
   * @throws {APIError} 
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

  return { sendMessage };
})();


class APIError extends Error {
  constructor(message, statusCode, kind) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode; 
    this.kind = kind; 
  }
}