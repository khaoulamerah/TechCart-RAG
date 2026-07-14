/**
 * api.js
 * ─────────────────────────────────────────────────────────
 * Rôle : c'est la SEULE couche du frontend qui a le droit de
 * parler au réseau (fetch). Aucun autre fichier ne doit
 * contenir d'appel `fetch(...)`.
 *
 * Pourquoi isoler ça ?
 * → Separation of Concerns (séparation des responsabilités) :
 *   chat.js gère la LOGIQUE de conversation, ui.js gère
 *   l'AFFICHAGE, api.js gère le RÉSEAU. Si demain le backend
 *   passe de REST à un WebSocket ou du Server-Sent Events pour
 *   du vrai streaming, on ne touche QUE ce fichier.
 * → Testabilité : on peut remplacer TechCartAPI par un mock
 *   dans des tests unitaires sans toucher au reste du code.
 *
 * Le module est exposé sous forme d'objet global `TechCartAPI`
 * (pas d'imports ES6 ici pour rester compatible avec un simple
 * <script src="..."> sans bundler, conformément au cahier des
 * charges "Vanilla JS uniquement").
 */

const TechCartAPI = (() => {
  /**
   * Envoie une question au backend et retourne la réponse de l'IA.
   *
   * @param {string} question - la question posée par l'utilisateur
   * @param {string} conversationId - identifiant de conversation (pour historique côté backend, optionnel selon impl.)
   * @returns {Promise<{answer: string, sources?: object[]}>}
   * @throws {APIError} en cas d'échec réseau, timeout ou erreur serveur
   */
  async function sendMessage(question, conversationId = null) {
    const controller = new AbortController();

    // On protège l'appel avec un timeout : si le backend (ou le LLM
    // via Ollama, qui peut être lent) ne répond pas assez vite, on
    // préfère afficher une erreur claire plutôt que de laisser
    // l'utilisateur face à un loader infini.
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
            question,
            conversation_id: conversationId,
          }),
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        // On distingue les erreurs "attendues" (4xx : mauvaise requête)
        // des erreurs "serveur" (5xx : bug backend, LLM down, etc.)
        // pour pouvoir un jour afficher des messages différenciés.
        const status = response.status;
        let detail = "Erreur inconnue.";
        try {
          const errBody = await response.json();
          detail = errBody.detail || detail;
        } catch (_) {
          /* le corps n'était pas du JSON, on garde le message par défaut */
        }
        throw new APIError(
          `Le serveur a répondu avec le statut ${status}`,
          status,
          detail
        );
      }

      const data = await response.json();

      // NOTE POUR TOI : adapte ce mapping à la forme exacte de la
      // réponse renvoyée par ton endpoint FastAPI (backend/api/schemas).
      // On accepte ici plusieurs noms de champs possibles pour rester
      // robuste tant que le contrat d'API n'est pas figé.
      return {
        answer: data.answer ?? data.response ?? data.message ?? "",
        sources: data.sources ?? data.sql_results ?? null,
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
      // TypeError = généralement "Failed to fetch" → backend injoignable
      // (backend éteint, mauvais port, CORS bloqué, pas de réseau...)
      throw new APIError(
        "Impossible de contacter le serveur TechCart.",
        0,
        "network"
      );
    }
  }

  return { sendMessage };
})();

/**
 * Erreur métier dédiée aux appels API.
 * Avoir une classe d'erreur spécifique permet à ui.js de savoir
 * exactement QUOI afficher (message réseau vs message serveur)
 * au lieu de parser des chaînes de caractères génériques.
 */
class APIError extends Error {
  constructor(message, statusCode, kind) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode; // 0 = pas de réponse HTTP du tout
    this.kind = kind; // "network" | "timeout" | "server" | undefined
  }
}
