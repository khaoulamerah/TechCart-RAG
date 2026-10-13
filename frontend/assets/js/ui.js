const TechCartUI = (() => {
  // ─────────────────────────────────────────────────────────────
  // DOM REFERENCES
  // ─────────────────────────────────────────────────────────────

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

  let toastTimer = null;

  // ─────────────────────────────────────────────────────────────
  // SECURITY / TEXT FORMATTING
  // ─────────────────────────────────────────────────────────────

  function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
  }

  /**
   * Very small Markdown renderer.
   *
   * Currently supports:
   * - **bold**
   * - new lines
   *
   * IMPORTANT:
   * The input is escaped before HTML formatting is applied.
   * This prevents streamed LLM content from injecting HTML/JS.
   */
  function lightMarkdownToHTML(text) {
    let safe = escapeHTML(text);

    // Bold: **text**
    safe = safe.replace(
      /\*\*(.+?)\*\*/g,
      "<strong>$1</strong>"
    );

    // New lines
    safe = safe.replace(/\n/g, "<br>");

    return safe;
  }

  // ─────────────────────────────────────────────────────────────
  // MESSAGE CREATION
  // ─────────────────────────────────────────────────────────────

  /**
   * Creates the basic structure of a chat message.
   *
   * Returns:
   * {
   *   row: HTMLElement,
   *   bubble: HTMLElement
   * }
   */
  function createMessageSkeleton(role) {
    const row = document.createElement("div");

    row.className =
      `message-row message-row--${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";

    avatar.innerHTML =
      role === "assistant"
        ? chipAvatarSVG()
        : userAvatarSVG();

    const bubbleWrap = document.createElement("div");
    bubbleWrap.className = "bubble-wrap";

    const bubble = document.createElement("div");

    bubble.className =
      `bubble bubble--${role}`;

    bubbleWrap.appendChild(bubble);

    row.appendChild(avatar);
    row.appendChild(bubbleWrap);

    dom.messages.appendChild(row);

    scrollToBottom();

    return {
      row,
      bubble,
    };
  }

  /**
   * Render a complete message.
   */
  function renderMessage(role, text) {
    const { bubble } = createMessageSkeleton(role);

    const content = text ?? "";

    bubble.dataset.rawText = content;

    bubble.innerHTML =
      lightMarkdownToHTML(content);

    return bubble;
  }

  // ─────────────────────────────────────────────────────────────
  // STREAMING
  // ─────────────────────────────────────────────────────────────

  /**
   * Marks a freshly-created assistant bubble as "streaming" — shows
   * the blinking cursor immediately, before the first token arrives.
   * Called once per message, right after renderMessage("assistant", "").
   */
  function startStreamingMessage(bubble) {
    if (!bubble) {
      return;
    }

    bubble.dataset.rawText = bubble.dataset.rawText || "";

    const cursor = document.createElement("span");
    cursor.className = "typing-cursor";
    cursor.setAttribute("aria-hidden", "true");
    bubble.appendChild(cursor);
  }

  /**
   * Append a streamed chunk to an assistant message.
   *
   * This function is called by chat.js for every chunk received
   * from the backend.
   *
   * Example:
   *
   * chunk 1 -> "Hello"
   * chunk 2 -> " world"
   * chunk 3 -> "!"
   *
   * Result:
   *
   * "Hello world!"
   */
  function appendToMessage(bubble, chunk) {
    if (!bubble || !chunk) {
      return;
    }

    // Keep the complete raw response in the DOM element.
    const currentText =
      bubble.dataset.rawText || "";

    const newText =
      currentText + chunk;

    bubble.dataset.rawText = newText;

    // Re-render the message safely.
    bubble.innerHTML =
      lightMarkdownToHTML(newText);

    // Add a small streaming cursor.
    const cursor =
      document.createElement("span");

    cursor.className = "typing-cursor";
    cursor.setAttribute(
      "aria-hidden",
      "true"
    );

    bubble.appendChild(cursor);

    scrollToBottom();
  }

  /**
   * Remove the streaming cursor.
   *
   * Called when the response has finished.
   */
  function finishStreamingMessage(bubble) {
    if (!bubble) {
      return;
    }

    bubble
      .querySelectorAll(".typing-cursor")
      .forEach((cursor) => {
        cursor.remove();
      });

    const finalText =
      bubble.dataset.rawText || "";

    bubble.innerHTML =
      lightMarkdownToHTML(finalText);

    scrollToBottom();
  }

  // ─────────────────────────────────────────────────────────────
  // THINKING INDICATOR
  // ─────────────────────────────────────────────────────────────

  function showThinkingIndicator() {
    const { row, bubble } =
      createMessageSkeleton("assistant");

    row.classList.add(
      "message-row--thinking"
    );

    bubble.innerHTML = `
      <div class="thinking-indicator">
        <div class="thinking-dots" aria-hidden="true">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span class="thinking-status">
          Analyse de votre demande…
        </span>
      </div>
    `;

    return row;
  }

  function updateThinkingIndicator(row, message) {
    if (!row || !message) {
      return;
    }

    const status = row.querySelector(".thinking-status");

    if (status) {
      status.textContent = message;
    }
  }

  // ─────────────────────────────────────────────────────────────
  // LEGACY TYPEWRITER
  // ─────────────────────────────────────────────────────────────

  /**
   * Kept for compatibility with the previous non-streaming
   * implementation.
   *
   * Your current streaming chat.js does NOT need this function.
   */
  function typeInto(bubble, fullText) {
    return new Promise((resolve) => {
      if (!bubble) {
        resolve();
        return;
      }

      let index = 0;

      bubble.innerHTML = "";

      const cursor =
        document.createElement("span");

      cursor.className =
        "typing-cursor";

      function tick() {
        index +=
          CONFIG.TYPING_CHARS_PER_TICK;

        const chunk =
          fullText.slice(0, index);

        bubble.innerHTML =
          lightMarkdownToHTML(chunk);

        bubble.appendChild(cursor);

        scrollToBottom();

        if (index < fullText.length) {
          setTimeout(
            tick,
            CONFIG.TYPING_SPEED_MS
          );
        } else {
          cursor.remove();
          resolve();
        }
      }

      tick();
    });
  }

  // ─────────────────────────────────────────────────────────────
  // ERROR MESSAGE
  // ─────────────────────────────────────────────────────────────

  function renderErrorMessage(message) {
    const row =
      document.createElement("div");

    row.className =
      "message-row message-row--error";

    row.innerHTML = `
      <div class="error-banner">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M12 9v4m0 4h.01
               M10.29 3.86 1.82 18
               a2 2 0 0 0 1.71 3
               h16.94
               a2 2 0 0 0 1.71-3
               L14.71 3.86
               a2 2 0 0 0-3.42 0Z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <span>
          ${escapeHTML(message)}
        </span>
      </div>
    `;

    dom.messages.appendChild(row);

    scrollToBottom();
  }

  // ─────────────────────────────────────────────────────────────
  // SCROLLING
  // ─────────────────────────────────────────────────────────────

  function scrollToBottom() {
    requestAnimationFrame(() => {
      if (!dom.messages) {
        return;
      }

      dom.messages.scrollTop =
        dom.messages.scrollHeight;
    });
  }

  // ─────────────────────────────────────────────────────────────
  // CLEAR CHAT
  // ─────────────────────────────────────────────────────────────

  function clearMessages() {
    if (!dom.messages) {
      return;
    }

    dom.messages.innerHTML = "";
  }

  // ─────────────────────────────────────────────────────────────
  // SENDING STATE
  // ─────────────────────────────────────────────────────────────

  function setSendingState(isSending) {
    if (dom.sendBtn) {
      dom.sendBtn.disabled = isSending;

      dom.sendBtn.classList.toggle(
        "is-loading",
        isSending
      );

      dom.sendBtn.setAttribute(
        "aria-busy",
        String(isSending)
      );
    }

    if (dom.input) {
      dom.input.disabled = isSending;
    }
  }

  // ─────────────────────────────────────────────────────────────
  // INPUT
  // ─────────────────────────────────────────────────────────────

  function clearInput() {
    if (!dom.input) {
      return;
    }

    dom.input.value = "";
    dom.input.style.height = "auto";
  }

  function autoGrowInput() {
    if (!dom.input) {
      return;
    }

    dom.input.style.height = "auto";

    dom.input.style.height =
      Math.min(
        dom.input.scrollHeight,
        160
      ) + "px";
  }

  // ─────────────────────────────────────────────────────────────
  // SIDEBAR
  // ─────────────────────────────────────────────────────────────

  function toggleSidebar() {
    if (!dom.sidebar) {
      return;
    }

    dom.sidebar.classList.toggle(
      "sidebar--open"
    );
  }

  function closeSidebarOnMobile() {
    if (
      !dom.sidebar ||
      window.innerWidth > 860
    ) {
      return;
    }

    dom.sidebar.classList.remove(
      "sidebar--open"
    );
  }

  // ─────────────────────────────────────────────────────────────
  // CONVERSATION HISTORY
  // ─────────────────────────────────────────────────────────────

  function renderHistoryList(conversations, activeId, handlers = {}) {
    if (!dom.historyList) {
      return;
    }

    const {
      onSelect = () => {},
      onRename = () => {},
      onDelete = () => {},
      onPin = () => {},
      onShare = () => {},
    } = handlers;

    closeAllDropdowns();
    dom.historyList.replaceChildren();

    if (!Array.isArray(conversations) || conversations.length === 0) {
      const empty = document.createElement("p");
      empty.className = "history-empty-state";
      empty.textContent = "Your conversations will appear here.";
      dom.historyList.appendChild(empty);
      return;
    }

    conversations.forEach((conv, index) => {
      const item = document.createElement("div");
      item.className = "history-item";
      if (conv.id === activeId) {
        item.classList.add("history-item--active");
      }
      if (conv.isPinned) {
        item.classList.add("history-item--pinned");
      }

      // Open conversation by clicking its title.
      const titleBtn = document.createElement("button");
      titleBtn.type = "button";
      titleBtn.className = "history-item-title";
      titleBtn.title = conv.title || "New chat";
      titleBtn.addEventListener("click", () => onSelect(conv.id));

      if (conv.isPinned) {
        const pinIndicator = document.createElement("span");
        pinIndicator.className = "history-item-pin-indicator";
        pinIndicator.innerHTML = historyActionIconSVG("pin");
        pinIndicator.setAttribute("aria-hidden", "true");
        titleBtn.appendChild(pinIndicator);
      }

      const titleText = document.createElement("span");
      titleText.className = "history-item-title-text";
      titleText.textContent = conv.title || "New chat";
      titleBtn.appendChild(titleText);

      // Three-dot menu button.
      const menuBtn = document.createElement("button");
      menuBtn.type = "button";
      menuBtn.className = "history-item-menu-btn";
      menuBtn.setAttribute("aria-label", `Options for ${conv.title || "New chat"}`);
      menuBtn.setAttribute("aria-haspopup", "menu");
      menuBtn.setAttribute("aria-expanded", "false");
      menuBtn.innerHTML = kebabIconSVG();

      // Dropdown is kept hidden until its matching three-dot button is clicked.
      const dropdown = document.createElement("div");
      dropdown.className = "history-item-dropdown";
      dropdown.hidden = true;
      dropdown.setAttribute("role", "menu");
      dropdown.setAttribute("aria-label", `Actions for ${conv.title || "New chat"}`);
      dropdown.id = `history-menu-${String(conv.id || index).replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      menuBtn.setAttribute("aria-controls", dropdown.id);

      const makeAction = ({ label, icon, className = "", onClick }) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `history-item-dropdown-action ${className}`.trim();
        button.setAttribute("role", "menuitem");
        button.innerHTML = `${historyActionIconSVG(icon)}<span></span>`;
        button.querySelector("span").textContent = label;
        button.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          closeAllDropdowns();
          onClick();
        });
        return button;
      };

      dropdown.appendChild(makeAction({
        label: "Rename",
        icon: "rename",
        onClick: () => beginRename(item, titleBtn, conv, onRename),
      }));

      dropdown.appendChild(makeAction({
        label: conv.isPinned ? "Unpin" : "Pin",
        icon: "pin",
        onClick: () => onPin(conv.id),
      }));

      dropdown.appendChild(makeAction({
        label: "Share",
        icon: "share",
        onClick: () => onShare(conv.id),
      }));

      const separator = document.createElement("div");
      separator.className = "history-item-dropdown-separator";
      separator.setAttribute("role", "separator");
      dropdown.appendChild(separator);

      dropdown.appendChild(makeAction({
        label: "Delete",
        icon: "delete",
        className: "history-item-dropdown-btn--danger",
        onClick: () => onDelete(conv.id),
      }));

      menuBtn.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const wasOpen = !dropdown.hidden;
        closeAllDropdowns();
        if (wasOpen) {
          return;
        }

        dropdown.hidden = false;
        menuBtn.setAttribute("aria-expanded", "true");
        positionHistoryDropdown(dropdown, menuBtn);
      });

      item.append(titleBtn, menuBtn, dropdown);
      dom.historyList.appendChild(item);
    });
  }

  function positionHistoryDropdown(dropdown, trigger) {
    // Position the menu against the viewport so it is not clipped by the
    // scrollable history list, including for conversations near the bottom.
    const triggerRect = trigger.getBoundingClientRect();
    const viewportPadding = 8;
    const menuWidth = Math.max(dropdown.offsetWidth, 184);
    const menuHeight = dropdown.offsetHeight;

    let left = triggerRect.right - menuWidth;
    left = Math.max(
      viewportPadding,
      Math.min(left, window.innerWidth - menuWidth - viewportPadding)
    );

    let top = triggerRect.bottom + 4;
    if (top + menuHeight > window.innerHeight - viewportPadding) {
      top = triggerRect.top - menuHeight - 4;
    }
    top = Math.max(
      viewportPadding,
      Math.min(top, window.innerHeight - menuHeight - viewportPadding)
    );

    dropdown.style.left = `${left}px`;
    dropdown.style.top = `${top}px`;
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".history-item-dropdown").forEach((dropdown) => {
      dropdown.hidden = true;
      dropdown.style.left = "";
      dropdown.style.top = "";
      const item = dropdown.closest(".history-item");
      const trigger = item?.querySelector(".history-item-menu-btn");
      trigger?.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", closeAllDropdowns);
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }

    const openMenu = document.querySelector(
      ".history-item-dropdown:not([hidden])"
    );
    if (!openMenu) {
      return;
    }

    const trigger = openMenu
      .closest(".history-item")
      ?.querySelector(".history-item-menu-btn");
    closeAllDropdowns();
    trigger?.focus();
  });
  window.addEventListener("resize", closeAllDropdowns);
  dom.historyList?.addEventListener("scroll", closeAllDropdowns);

  // ─────────────────────────────────────────────────────────────
  // RENAME CONVERSATION
  // ─────────────────────────────────────────────────────────────

  function beginRename(item, titleBtn, conv, onRename) {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "history-item-rename-input";
    input.value = conv.title || "";
    input.maxLength = 60;
    input.setAttribute("aria-label", "Conversation name");

    titleBtn.replaceWith(input);
    input.focus();
    input.select();

    let settled = false;

    function commit() {
      if (settled) {
        return;
      }
      settled = true;
      const newTitle = input.value.trim() || "New chat";
      onRename(conv.id, newTitle);
    }

    function cancel() {
      if (settled) {
        return;
      }
      settled = true;
      input.replaceWith(titleBtn);
    }

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        commit();
      } else if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      }
    });
    input.addEventListener("blur", commit);
    input.addEventListener("click", (event) => event.stopPropagation());
  }

  // Small non-blocking feedback for pin/share actions.
  function showToast(message, type = "success") {
    let toast = document.getElementById("techcart-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "techcart-toast";
      toast.className = "app-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }

    if (toastTimer) {
      clearTimeout(toastTimer);
    }

    toast.className = `app-toast app-toast--${type}`;
    toast.textContent = message;
    toast.hidden = false;
    toastTimer = setTimeout(() => {
      toast.hidden = true;
    }, 2800);
  }

  // ─────────────────────────────────────────────────────────────
  // THEME
  // ─────────────────────────────────────────────────────────────

  function applyTheme(theme) {
    const validTheme =
      theme === "light"
        ? "light"
        : "dark";

    document.documentElement
      .setAttribute(
        "data-theme",
        validTheme
      );
  }

  // ─────────────────────────────────────────────────────────────
  // SVG ICONS
  // ─────────────────────────────────────────────────────────────

  function kebabIconSVG() {
    return `
      <svg
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        aria-hidden="true"
      >
        <circle
          cx="12"
          cy="5"
          r="1.6"
          fill="currentColor"
        />
        <circle
          cx="12"
          cy="12"
          r="1.6"
          fill="currentColor"
        />
        <circle
          cx="12"
          cy="19"
          r="1.6"
          fill="currentColor"
        />
      </svg>
    `;
  }

  function historyActionIconSVG(name) {
    const icons = {
      rename: `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z"/>
        </svg>`,
      pin: `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="m16 3 5 5-4 1-4 4v5l-2-2-2 2v-5l4-4 1-4Z"/><path d="m5 19 5-5"/>
        </svg>`,
      share: `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.7 10.7 6.6-4.4M8.7 13.3l6.6 4.4"/>
        </svg>`,
      delete: `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v5M14 11v5"/>
        </svg>`,
    };

    return icons[name] || "";
  }

  function chipAvatarSVG() {
    return `
      <svg
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <rect
          x="10"
          y="10"
          width="20"
          height="20"
          rx="3"
          fill="var(--accent-cyan)"
        />

        <rect
          x="14"
          y="14"
          width="12"
          height="12"
          rx="1.5"
          fill="var(--bg-primary)"
        />

        <g
          stroke="var(--accent-cyan)"
          stroke-width="1.6"
        >
          <line x1="14" y1="4" x2="14" y2="10"/>
          <line x1="20" y1="4" x2="20" y2="10"/>
          <line x1="26" y1="4" x2="26" y2="10"/>

          <line x1="14" y1="30" x2="14" y2="36"/>
          <line x1="20" y1="30" x2="20" y2="36"/>
          <line x1="26" y1="30" x2="26" y2="36"/>

          <line x1="4" y1="14" x2="10" y2="14"/>
          <line x1="4" y1="20" x2="10" y2="20"/>
          <line x1="4" y1="26" x2="10" y2="26"/>

          <line x1="30" y1="14" x2="36" y2="14"/>
          <line x1="30" y1="20" x2="36" y2="20"/>
          <line x1="30" y1="26" x2="36" y2="26"/>
        </g>
      </svg>
    `;
  }

  function userAvatarSVG() {
    return `
      <svg
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          cx="20"
          cy="20"
          r="20"
          fill="var(--bg-elevated)"
        />

        <circle
          cx="20"
          cy="16"
          r="6"
          fill="var(--text-secondary)"
        />

        <path
          d="M8 33
             c1.5-7 6-10 12-10
             s10.5 3 12 10"
          stroke="var(--text-secondary)"
          stroke-width="2.2"
          stroke-linecap="round"
          fill="none"
        />
      </svg>
    `;
  }

  // ─────────────────────────────────────────────────────────────
  // PUBLIC API
  // ─────────────────────────────────────────────────────────────

  return {
    dom,

    // Messages
    renderMessage,
    showThinkingIndicator,
    updateThinkingIndicator,
    startStreamingMessage,
    appendToMessage,
    finishStreamingMessage,
    typeInto,
    renderErrorMessage,

    // Utility
    scrollToBottom,
    clearMessages,
    setSendingState,
    clearInput,

    // Sidebar
    toggleSidebar,
    closeSidebarOnMobile,

    // Input
    autoGrowInput,

    // History
    renderHistoryList,
    showToast,

    // Theme
    applyTheme,

    // Security
    escapeHTML,
  };
})();