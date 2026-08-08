

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

  const savedTheme = localStorage.getItem("techcart_theme") || "dark";
  TechCartUI.applyTheme(savedTheme);

  // ─── Démarrage de l'application ────────────────────────────
  TechCartChat.init();
});
