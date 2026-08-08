

const CONFIG = {

  API_BASE_URL: "http://localhost:8000",

  CHAT_ENDPOINT: "/chat",

  SESSION_STORAGE_KEY: "techcart_session_id",

  STORAGE_KEY: "techcart_conversations",

  TYPING_SPEED_MS: 12,

  TYPING_CHARS_PER_TICK: 2,

  THINKING_DELAY_MS: 300,

  REQUEST_TIMEOUT_MS: 30000,

  WELCOME_MESSAGE:
    "Bonjour \u{1F44B} Je suis l'assistant TechCart. Demandez-moi un GPU, un CPU, ou demandez-moi de comparer deux composants — je fouille le stock en temps réel pour vous.",
};

Object.freeze(CONFIG);