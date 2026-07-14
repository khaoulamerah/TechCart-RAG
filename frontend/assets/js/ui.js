/**
 * ui.js
 * ─────────────────────────────────────────────────────────
 * Rôle : c'est la SEULE couche qui touche au DOM (querySelector,
 * innerHTML, création d'éléments, animations CSS...).
 *
 * Pourquoi isoler ça ?
 * → chat.js décide QUOI afficher (logique), ui.js décide COMMENT
 *   l'afficher (présentation). Ça permet, par exemple, de changer
 *   complètement le design des bulles de message sans jamais
 *   toucher à la logique de conversation.
 * → Chaque fonction ici est une brique réutilisable et testable
 *   indépendamment.
 *
 * Convention : toute fonction qui LIT le DOM commence par `get`,
 * toute fonction qui ÉCRIT dans le DOM commence par `render`,
 * `add`, `show` ou `set`.
 */

const TechCartUI = (() => {
  // Cache des éléments du DOM interrogés souvent, pour éviter de
  // refaire un querySelector à chaque appel (micro-optimisation,
  // mais aussi plus lisible).
  const dom = {
    messages: document.getElementById("chat-messages"),
    form: document.getElementById("chat-form"),
    input: document.getElementById("chat-input"),
    sendBtn: document.getElementById("send-btn"),
    sidebarToggle: document.getElementById("sidebar-toggle"),
    sidebar: document.getElementById("sidebar"),
    newChatBtn: document.getElementById("new-chat-btn"),
    historyList: document.getElementById("history-list"),
    themeToggle: document.getElementById("theme-toggle"),
    scrollAnchor: document.getElementById("scroll-anchor"),
  };

  /**
   * Échappe le HTML pour empêcher toute injection de balises via
   * une question utilisateur ou une réponse du LLM.
   * Règle d'or sécurité : on n'injecte JAMAIS du texte dynamique
   * avec innerHTML sans l'avoir échappé au préalable.
   */
  function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Convertit un minimum de markdown (gras, listes, retours à la
   * ligne) en HTML. Le LLM a tendance à répondre avec du markdown
   * (ex: "**RTX 3080**"), donc on le rend lisible sans dépendre
   * d'une librairie externe (cahier des charges : pas de frameworks).
   */
  function lightMarkdownToHTML(text) {
    let safe = escapeHTML(text);
    safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }

  /**
   * Crée le squelette DOM d'une ligne de message (avatar + bulle)
   * mais NE remplit PAS encore le texte — utile pour l'effet
   * machine à écrire, où le texte arrive progressivement.
   *
   * @param {"user"|"assistant"} role
   * @returns {{row: HTMLElement, bubble: HTMLElement}}
   */
  function createMessageSkeleton(role) {
    const row = document.createElement("div");
    row.className = `message-row message-row--${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.innerHTML =
      role === "assistant" ? chipAvatarSVG() : userAvatarSVG();

    const bubbleWrap = document.createElement("div");
    bubbleWrap.className = "bubble-wrap";

    const bubble = document.createElement("div");
    bubble.className = `bubble bubble--${role}`;

    bubbleWrap.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(bubbleWrap);

    dom.messages.appendChild(row);
    scrollToBottom();

    return { row, bubble };
  }

  /**
   * Affiche un message complet d'un coup (pas d'effet typing).
   * Utilisé pour les messages utilisateur et le message d'accueil.
   */
  function renderMessage(role, text) {
    const { bubble } = createMessageSkeleton(role);
    bubble.innerHTML = lightMarkdownToHTML(text);
    return bubble;
  }

  /**
   * Affiche les 3 points animés ("l'assistant tape...") pendant
   * qu'on attend la réponse du backend.
   * @returns {HTMLElement} l'élément à retirer une fois la réponse prête
   */
  function showThinkingIndicator() {
    const { row, bubble } = createMessageSkeleton("assistant");
    row.classList.add("message-row--thinking");
    bubble.innerHTML = `
      <div class="thinking-dots" aria-label="L'assistant réfléchit">
        <span></span><span></span><span></span>
      </div>`;
    return row;
  }

  /**
   * Révèle un texte progressivement dans une bulle déjà créée,
   * pour simuler l'effet "streaming" façon ChatGPT.
   * @param {HTMLElement} bubble
   * @param {string} fullText
   * @returns {Promise<void>} résolue quand tout le texte est affiché
   */
  function typeInto(bubble, fullText) {
    return new Promise((resolve) => {
      let index = 0;
      bubble.innerHTML = "";
      const cursor = document.createElement("span");
      cursor.className = "typing-cursor";

      function tick() {
        index += CONFIG.TYPING_CHARS_PER_TICK;
        const chunk = fullText.slice(0, index);
        bubble.innerHTML = lightMarkdownToHTML(chunk);
        bubble.appendChild(cursor);
        scrollToBottom();

        if (index < fullText.length) {
          setTimeout(tick, CONFIG.TYPING_SPEED_MS);
        } else {
          cursor.remove();
          resolve();
        }
      }
      tick();
    });
  }

  /** Affiche un bandeau d'erreur inline dans le fil de discussion. */
  function renderErrorMessage(message) {
    const row = document.createElement("div");
    row.className = "message-row message-row--error";
    row.innerHTML = `
      <div class="error-banner">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L14.71 3.86a2 2 0 0 0-3.42 0Z"
            stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>${escapeHTML(message)}</span>
      </div>`;
    dom.messages.appendChild(row);
    scrollToBottom();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      dom.messages.scrollTop = dom.messages.scrollHeight;
    });
  }

  function clearMessages() {
    dom.messages.innerHTML = "";
  }

  function setSendingState(isSending) {
    dom.sendBtn.disabled = isSending;
    dom.input.disabled = isSending;
    dom.sendBtn.classList.toggle("is-loading", isSending);
  }

  function clearInput() {
    dom.input.value = "";
    dom.input.style.height = "auto";
  }

  function toggleSidebar() {
    dom.sidebar.classList.toggle("sidebar--open");
  }

  function closeSidebarOnMobile() {
    if (window.innerWidth <= 860) {
      dom.sidebar.classList.remove("sidebar--open");
    }
  }

  /** Recalcule la hauteur du textarea au fil de la saisie (auto-grow). */
  function autoGrowInput() {
    dom.input.style.height = "auto";
    dom.input.style.height = Math.min(dom.input.scrollHeight, 160) + "px";
  }

  function renderHistoryList(conversations, activeId, onSelect) {
    dom.historyList.innerHTML = "";
    conversations.forEach((conv) => {
      const item = document.createElement("button");
      item.className =
        "history-item" + (conv.id === activeId ? " history-item--active" : "");
      item.type = "button";
      item.textContent = conv.title || "Nouvelle conversation";
      item.addEventListener("click", () => onSelect(conv.id));
      dom.historyList.appendChild(item);
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  // ─── Icônes SVG inline (aucune dépendance externe) ──────────────
  function chipAvatarSVG() {
    return `<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="10" y="10" width="20" height="20" rx="3" fill="var(--accent-cyan)"/>
      <rect x="14" y="14" width="12" height="12" rx="1.5" fill="var(--bg-primary)"/>
      <g stroke="var(--accent-cyan)" stroke-width="1.6">
        <line x1="14" y1="4" x2="14" y2="10"/><line x1="20" y1="4" x2="20" y2="10"/><line x1="26" y1="4" x2="26" y2="10"/>
        <line x1="14" y1="30" x2="14" y2="36"/><line x1="20" y1="30" x2="20" y2="36"/><line x1="26" y1="30" x2="26" y2="36"/>
        <line x1="4" y1="14" x2="10" y2="14"/><line x1="4" y1="20" x2="10" y2="20"/><line x1="4" y1="26" x2="10" y2="26"/>
        <line x1="30" y1="14" x2="36" y2="14"/><line x1="30" y1="20" x2="36" y2="20"/><line x1="30" y1="26" x2="36" y2="26"/>
      </g>
    </svg>`;
  }

  function userAvatarSVG() {
    return `<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="20" fill="var(--bg-elevated)"/>
      <circle cx="20" cy="16" r="6" fill="var(--text-secondary)"/>
      <path d="M8 33c1.5-7 6-10 12-10s10.5 3 12 10" stroke="var(--text-secondary)" stroke-width="2.2" stroke-linecap="round" fill="none"/>
    </svg>`;
  }

  return {
    dom,
    renderMessage,
    showThinkingIndicator,
    typeInto,
    renderErrorMessage,
    scrollToBottom,
    clearMessages,
    setSendingState,
    clearInput,
    toggleSidebar,
    closeSidebarOnMobile,
    autoGrowInput,
    renderHistoryList,
    applyTheme,
    escapeHTML,
  };
})();
