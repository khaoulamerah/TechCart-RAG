document.addEventListener("DOMContentLoaded", () => {
  const dom = TechCartUI.dom;


  /*
   * ─────────────────────────────────────────────
   * SEND MESSAGE
   * ─────────────────────────────────────────────
   */

  dom.form.addEventListener(
    "submit",
    (event) => {
      event.preventDefault();

      TechCartChat.sendUserMessage(
        dom.input.value
      );
    }
  );


  /*
   * Enter = send
   * Shift + Enter = new line
   */

  dom.input.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {
        event.preventDefault();

        dom.form.requestSubmit();
      }
    }
  );


  /*
   * ─────────────────────────────────────────────
   * AUTO-GROW TEXTAREA
   * ─────────────────────────────────────────────
   */

  dom.input.addEventListener(
    "input",
    () => {
      TechCartUI.autoGrowInput();
    }
  );


  /*
   * ─────────────────────────────────────────────
   * NEW CONVERSATION
   * ─────────────────────────────────────────────
   */

  dom.newChatBtn.addEventListener(
    "click",
    () => {
      TechCartChat.startNewConversation();
    }
  );


  /*
   * ─────────────────────────────────────────────
   * MOBILE SIDEBAR
   * ─────────────────────────────────────────────
   */

  dom.sidebarToggle.addEventListener(
    "click",
    () => {
      TechCartUI.toggleSidebar();
    }
  );


  /*
   * ─────────────────────────────────────────────
   * THEME
   * ─────────────────────────────────────────────
   */

  dom.themeToggle.addEventListener(
    "click",
    () => {
      const current =
        document.documentElement
          .getAttribute("data-theme");

      const next =
        current === "light"
          ? "dark"
          : "light";

      TechCartUI.applyTheme(next);

      localStorage.setItem(
        "techcart_theme",
        next
      );
    }
  );


  const savedTheme =
    localStorage.getItem(
      "techcart_theme"
    ) || "dark";

  TechCartUI.applyTheme(
    savedTheme
  );


  TechCartChat.init();
});