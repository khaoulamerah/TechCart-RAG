const CONFIG = {
  /*
   * Browser:
   *
   * http://localhost:3000
   *
   * API:
   *
   * http://localhost:3000/api
   *
   * Nginx forwards:
   *
   * /api/* → backend:8000/*
   */

  API_BASE_URL: "/api",

  CHAT_ENDPOINT: "/chat",

  SESSION_STORAGE_KEY:
    "techcart_session_id",

  STORAGE_KEY:
    "techcart_conversations",

  /*
   * Normal API requests.
   */
  REQUEST_TIMEOUT_MS: 30000,

  /*
   * Maximum inactivity period while
   * receiving the streaming response.
   *
   * This is NOT supposed to compensate for
   * model cold-start anymore because models
   * are warmed during backend startup.
   */
  STREAM_TIMEOUT_MS: 180000,

  TYPING_SPEED_MS: 12,

  TYPING_CHARS_PER_TICK: 2,

  THINKING_DELAY_MS: 300,

  WELCOME_MESSAGE:
    "Bonjour 👋 Je suis l'assistant TechCart. " +
    "Demandez-moi un GPU, un CPU, ou posez-moi " +
    "une question concernant les politiques " +
    "de TechCart.",
};

Object.freeze(CONFIG);