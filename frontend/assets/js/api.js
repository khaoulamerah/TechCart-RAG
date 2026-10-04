const TechCartAPI = (() => {
  /**
   * Stream a chat response from the backend using Server-Sent Events
   * transported through the Fetch API ReadableStream.
   *
   * Backend expected format:
   *
   * event: token
   * data: {"type":"token","content":" hello"}
   *
   * event: done
   * data: {
   *   "type":"done",
   *   "conversation_id":"...",
   *   "session_id":"..."
   * }
   *
   * event: error
   * data: {"type":"error","message":"..."}
   *
   * @param {string} message
   * @param {string|null} sessionId
   * @param {string|null} conversationId
   * @param {(content: string) => void} onToken
   * @param {(metadata: object) => void} onDone
   * @returns {Promise<{
   *   reply: string,
   *   conversationId: string|null,
   *   sessionId: string|null
   * }>}
   */
  async function streamMessage(
    message,
    sessionId = null,
    conversationId = null,
    onToken = () => {},
    onDone = () => {}
  ) {
    const controller = new AbortController();

    let timeoutId = null;

    const resetTimeout = () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        controller.abort();
      }, CONFIG.STREAM_TIMEOUT_MS);
    };

    try {
      resetTimeout();

      const response = await fetch(
        `${CONFIG.API_BASE_URL}${CONFIG.CHAT_ENDPOINT}`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },

          body: JSON.stringify({
            message,
            session_id: sessionId,
            conversation_id: conversationId,
          }),

          signal: controller.signal,
        }
      );

      if (!response.ok) {
        const status = response.status;

        let detail = "Erreur inconnue.";

        try {
          const errorBody = await response.json();

          detail =
            errorBody.detail ||
            errorBody.message ||
            detail;
        } catch (_) {
          // Response was not JSON.
        }

        throw new APIError(
          `Le serveur a répondu avec le statut ${status}.`,
          status,
          "server",
          detail
        );
      }

      /*
       * The browser must receive a streaming body.
       */
      if (!response.body) {
        throw new APIError(
          "Le navigateur ne supporte pas le streaming de réponse.",
          0,
          "stream"
        );
      }

      const contentType =
        response.headers.get("content-type") || "";

      if (!contentType.includes("text/event-stream")) {
        throw new APIError(
          "Le serveur n'a pas retourné une réponse SSE.",
          response.status,
          "stream"
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      let fullReply = "";

      let resultConversationId = conversationId;
      let resultSessionId = sessionId;

      let doneReceived = false;

      while (true) {
        resetTimeout();

        const { value, done } = await reader.read();

        resetTimeout();

        if (done) {
          break;
        }
        buffer += decoder.decode(value, {
          stream: true,
        });

        /*
         * Normalize CRLF to LF.
         */
        buffer = buffer.replace(/\r\n/g, "\n");


        const events = buffer.split("\n\n");

        /*
         * Keep the incomplete event for the next network chunk.
         */
        buffer = events.pop() || "";

        for (const eventBlock of events) {
          const event = parseSSEEvent(eventBlock);

          if (!event) {
            continue;
          }

          const { type, data } = event;

          /*
           * TOKEN
           */
          if (type === "token") {
            const content = data?.content ?? "";

            if (content) {
              fullReply += content;

              /*
               * Immediately update the UI.
               */
              onToken(content);
            }

            continue;
          }

          if (type === "metadata") {
            resultConversationId =
              data?.conversation_id ??
              resultConversationId;

            resultSessionId =
              data?.session_id ??
              resultSessionId;

            continue;
          }

          /*
           * DONE
           */
          if (type === "done") {
            resultConversationId =
              data?.conversation_id ??
              resultConversationId;

            resultSessionId =
              data?.session_id ??
              resultSessionId;

            doneReceived = true;

            onDone({
              reply: fullReply,
              conversationId: resultConversationId,
              sessionId: resultSessionId,
            });

            continue;
          }

          /*
           * ERROR
           */
          if (type === "error") {
            throw new APIError(
              data?.message ||
                data?.detail ||
                "Le serveur a rencontré une erreur.",
              500,
              "server"
            );
          }
        }
      }

      /*
       * Flush the final UTF-8 bytes.
       */
      buffer += decoder.decode();

      if (buffer.trim()) {
        const event = parseSSEEvent(buffer);

        if (event) {
          const { type, data } = event;

          if (type === "token") {
            const content = data?.content ?? "";

            if (content) {
              fullReply += content;
              onToken(content);
            }
          }

          if (type === "metadata") {
            resultConversationId =
              data?.conversation_id ??
              resultConversationId;

            resultSessionId =
              data?.session_id ??
              resultSessionId;
          }

          if (type === "done") {
            resultConversationId =
              data?.conversation_id ??
              resultConversationId;

            resultSessionId =
              data?.session_id ??
              resultSessionId;

            doneReceived = true;

            onDone({
              reply: fullReply,
              conversationId: resultConversationId,
              sessionId: resultSessionId,
            });
          }

          if (type === "error") {
            throw new APIError(
              data?.message ||
                data?.detail ||
                "Le serveur a rencontré une erreur.",
              500,
              "server"
            );
          }
        }
      }

      if (!doneReceived && fullReply) {
        onDone({
          reply: fullReply,
          conversationId: resultConversationId,
          sessionId: resultSessionId,
        });
      }

      return {
        reply: fullReply,
        conversationId: resultConversationId,
        sessionId: resultSessionId,
      };
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new APIError(
          "Le serveur met trop de temps à répondre.",
          0,
          "timeout"
        );
      }

      if (error instanceof APIError) {
        throw error;
      }

      console.error(
        "TechCart streaming error:",
        error
      );

      throw new APIError(
        "Impossible de contacter le serveur TechCart.",
        0,
        "network"
      );
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  }

  /**
   * Parse one SSE event block.
   *
   * IMPORTANT:
   * We must preserve spaces in "data:" because Ollama tokens
   * frequently contain leading spaces.
   */
  function parseSSEEvent(eventBlock) {
    if (!eventBlock || !eventBlock.trim()) {
      return null;
    }

    const lines = eventBlock.split(/\r?\n/);

    let eventType = "message";
    const dataLines = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventType = line
          .slice("event:".length)
          .trim();
      } else if (line.startsWith("data:")) {
        /*
         * Remove only the optional single space after "data:".
         *
         * DO NOT use .trim() here.
         *
         * Example:
         *
         * data: {"content":" hello"}
         *
         * must preserve " hello".
         */
        let value = line.slice("data:".length);

        if (value.startsWith(" ")) {
          value = value.slice(1);
        }

        dataLines.push(value);
      }
    }

    if (dataLines.length === 0) {
      return null;
    }

    const dataText = dataLines.join("\n");

    let data;

    try {
      data = JSON.parse(dataText);
    } catch (_) {
      /*
       * Support plain-text SSE data too.
       */
      data = {
        content: dataText,
      };
    }

    return {
      type: eventType,
      data,
    };
  }

  /**
   * Delete a conversation.
   *
   * @param {string} conversationId
   */
  async function deleteConversation(conversationId) {
    const controller = new AbortController();

    const timeoutId = setTimeout(
      () => controller.abort(),
      CONFIG.REQUEST_TIMEOUT_MS
    );

    try {
      const response = await fetch(
        `${CONFIG.API_BASE_URL}${CONFIG.CHAT_ENDPOINT}/conversations/${conversationId}`,
        {
          method: "DELETE",
          signal: controller.signal,
        }
      );

      if (!response.ok) {
        let detail = "Erreur inconnue.";

        try {
          const errorBody = await response.json();

          detail =
            errorBody.detail ||
            errorBody.message ||
            detail;
        } catch (_) {
          // No JSON body.
        }

        throw new APIError(
          `Le serveur a répondu avec le statut ${response.status}.`,
          response.status,
          "server",
          detail
        );
      }
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new APIError(
          "La suppression a pris trop de temps.",
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
    } finally {
      clearTimeout(timeoutId);
    }
  }

  return {
    streamMessage,
    deleteConversation,
  };
})();


class APIError extends Error {
  constructor(
    message,
    statusCode = 0,
    kind = undefined,
    detail = undefined
  ) {
    super(message);

    this.name = "APIError";
    this.statusCode = statusCode;
    this.kind = kind;
    this.detail = detail;
  }
}




// ============================================================
// Developer / Observability API
// ============================================================

async function getDeveloperConversations(
  limit = 100
) {
  const response = await fetch(
    `${API_BASE_URL}/developer/conversations?limit=${limit}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load conversations (${response.status})`
    );
  }

  return response.json();
}


async function getDeveloperConversation(
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/developer/conversations/${encodeURIComponent(
      conversationId
    )}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load conversation (${response.status})`
    );
  }

  return response.json();
}


async function getConversationTraces(
  conversationId
) {
  const response = await fetch(
    `${API_BASE_URL}/developer/conversations/${encodeURIComponent(
      conversationId
    )}/traces`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load RAG traces (${response.status})`
    );
  }

  return response.json();
}


async function getRAGTrace(traceId) {
  const response = await fetch(
    `${API_BASE_URL}/developer/traces/${encodeURIComponent(
      traceId
    )}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load RAG trace (${response.status})`
    );
  }

  return response.json();
}