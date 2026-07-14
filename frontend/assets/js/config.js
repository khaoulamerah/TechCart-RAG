/**
 * config.js
 * ─────────────────────────────────────────────────────────
 * Rôle : centraliser TOUTE la configuration du frontend.
 *
 * Pourquoi un fichier dédié ?
 * → Si demain l'URL du backend change (dev → staging → prod,
 *   ou déploiement derrière Nginx dans docker-compose), on modifie
 *   UNE seule ligne, ici, au lieu de chercher des URLs codées en dur
 *   dans app.js / api.js / chat.js.
 * → C'est le principe "Single Source of Truth" (une seule source
 *   de vérité) : une bonne pratique fondamentale en ingénierie.
 *
 * Ce fichier ne fait AUCUNE logique, il ne fait qu'exporter des
 * constantes. Il doit être chargé en premier dans index.html.
 */

const CONFIG = {
  // Base URL de l'API FastAPI.
  // En dev local sans Docker : http://localhost:8000
  // En Docker Compose avec Nginx en reverse-proxy : /api (chemin relatif)
  API_BASE_URL: "http://localhost:8000",

  // Endpoint du chat (voir backend/api/routes/)
  CHAT_ENDPOINT: "/api/chat",

  // Nom de la clé utilisée pour stocker l'historique des
  // conversations dans le localStorage du navigateur.
  STORAGE_KEY: "techcart_conversations",

  // Délai (ms) entre chaque "tick" de l'effet machine à écrire.
  // Plus la valeur est basse, plus l'IA "tape" vite.
  TYPING_SPEED_MS: 12,

  // Nombre de caractères révélés par tick (permet d'accélérer
  // l'effet sans le rendre saccadé).
  TYPING_CHARS_PER_TICK: 2,

  // Délai avant d'afficher l'indicateur "l'assistant réfléchit..."
  THINKING_DELAY_MS: 300,

  // Timeout réseau : au-delà, on considère que le backend ne répond pas.
  REQUEST_TIMEOUT_MS: 30000,

  // Message affiché au tout premier chargement.
  WELCOME_MESSAGE:
    "Bonjour \u{1F44B} Je suis l'assistant TechCart. Demandez-moi un GPU, un CPU, ou demandez-moi de comparer deux composants — je fouille le stock en temps réel pour vous.",
};

// On fige l'objet pour éviter qu'une autre partie du code ne
// modifie accidentellement la configuration à l'exécution.
Object.freeze(CONFIG);
