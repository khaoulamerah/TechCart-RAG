const CONFIG = {
  // The browser talks to Nginx. Nginx forwards /api/* to FastAPI.
  API_BASE_URL: "/api",
  CHAT_ENDPOINT: "/chat",

  STORAGE_KEY: "techcart_conversations",
  SESSION_STORAGE_KEY: "techcart_session_id",

  // Normal CRUD requests.
  REQUEST_TIMEOUT_MS: 30000,

  // Maximum inactivity between SSE chunks.
  // The backend now emits progress/keep-alive events during long RAG steps.
  STREAM_TIMEOUT_MS: 60000,

  WELCOME_MESSAGE:
    "Hello 👋 I'm the TechCart assistant. " +
    "Ask me about a GPU or CPU, or ask a question " +
    "about TechCart store policies.",
};

Object.freeze(CONFIG);
