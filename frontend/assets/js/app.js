/**
 * app.js
 * ─────────────────────────────────────────────────────────
 * Rôle : le point d'entrée de l'application. C'est le SEUL fichier
 * qui attache des écouteurs d'événements aux éléments du DOM
 * (submit, click, input, keydown...).
 *
 * Pourquoi un point d'entrée unique ?
 * → Si tu ouvres ce fichier dans 6 mois, tu vois d'un coup d'œil
 *   TOUT ce qui déclenche une action dans l'app, sans avoir à
 *   fouiller dans chat.js ou ui.js. C'est la "table des matières"
 *   comportementale de l'application.
 * → Ordre de chargement obligatoire dans index.html :
 *   config.js → api.js → ui.js → chat.js → app.js
 *   (chaque fichier dépend des précédents via les objets globaux
 *   CONFIG, TechCartAPI, TechCartUI, TechCartChat).
 */

document.addEventListener("DOMContentLoaded", () => {
  const dom = TechCartUI.dom;

  // ─── Envoi d'un message ────────────────────────────────────
  dom.form.addEventListener("submit", (event) => {
    event.preventDefault();
    TechCartChat.sendUserMessage(dom.input.value);
  });

  // Entrée = envoyer, Maj+Entrée = nouvelle ligne (convention ChatGPT/Slack)
  dom.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      dom.form.requestSubmit();
    }
  });

  // Auto-agrandissement du textarea pendant la saisie
  dom.input.addEventListener("input", () => {
    TechCartUI.autoGrowInput();
  });

  // ─── Nouvelle conversation ─────────────────────────────────
  dom.newChatBtn.addEventListener("click", () => {
    TechCartChat.startNewConversation();
  });

  // ─── Sidebar (mobile) ──────────────────────────────────────
  dom.sidebarToggle.addEventListener("click", () => {
    TechCartUI.toggleSidebar();
  });

  // ─── Dark / Light mode ─────────────────────────────────────
  dom.themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    TechCartUI.applyTheme(next);
    localStorage.setItem("techcart_theme", next);
  });

  // Restaure le thème choisi précédemment (par défaut : dark, cohérent
  // avec l'identité visuelle "atelier électronique" de TechCart).
  const savedTheme = localStorage.getItem("techcart_theme") || "dark";
  TechCartUI.applyTheme(savedTheme);

  // ─── Démarrage de l'application ────────────────────────────
  TechCartChat.init();
});
