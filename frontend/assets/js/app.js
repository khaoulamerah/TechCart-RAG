document.addEventListener("DOMContentLoaded", () => {
  const dom = TechCartUI.dom;

  const chatPage = document.getElementById("chat-page");
  const developerPage = document.getElementById("developer-page");
  const developerOpen = document.getElementById("developer-open");
  const developerBack = document.getElementById("developer-back");

  function showChatPage(updateUrl = true) {
    chatPage?.classList.add("active");
    developerPage?.classList.remove("active");

    if (
      updateUrl &&
      (
        window.location.pathname === "/developer" ||
        window.location.hash === "#developer"
      )
    ) {
      history.replaceState(null, "", "/");
    }
  }

  function showDeveloperPage(updateUrl = true) {
    chatPage?.classList.remove("active");
    developerPage?.classList.add("active");

    if (updateUrl && window.location.pathname !== "/developer") {
      history.replaceState(null, "", "/developer");
    }

    DeveloperApp.loadConversations().catch(console.error);
  }

  function routeFromUrl() {
    if (window.location.pathname === "/developer") {
      showDeveloperPage(false);
    } else {
      showChatPage(false);
    }
  }

  dom.form?.addEventListener("submit", (event) => {
    event.preventDefault();
    TechCartChat.sendUserMessage(dom.input.value);
  });

  dom.input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      dom.form.requestSubmit();
    }
  });

  dom.input?.addEventListener("input", () => {
    TechCartUI.autoGrowInput();
  });

  dom.newChatBtn?.addEventListener("click", () => {
    showChatPage();
    TechCartChat.startNewConversation();
  });

  dom.sidebarToggle?.addEventListener("click", () => {
    TechCartUI.toggleSidebar();
  });

  dom.themeToggle?.addEventListener("click", () => {
    const current =
      document.documentElement.getAttribute("data-theme");

    const next =
      current === "light"
        ? "dark"
        : "light";

    TechCartUI.applyTheme(next);
    localStorage.setItem("techcart_theme", next);
  });

  developerOpen?.addEventListener("click", () => {
    showDeveloperPage();
  });

  developerBack?.addEventListener("click", () => {
    showChatPage();
  });

  window.addEventListener("popstate", routeFromUrl);

  const savedTheme =
    localStorage.getItem("techcart_theme") || "dark";

  TechCartUI.applyTheme(savedTheme);

  DeveloperApp.initialize();
  TechCartChat.init();

  /*
   * Root URL "/" always opens the user chat.
   * Developer mode is available explicitly through
   * the Developer button or /developer.
   */
  routeFromUrl();
});
