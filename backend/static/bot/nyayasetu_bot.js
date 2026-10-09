const NyayaSetuBot = {
  isOpen: false,
  currentMode: "guide",
  conversationHistory: [],
  init() {
    this.bindEvents();
    const hasSession = this.loadSession();
    if (!hasSession) {
      this.checkFirstVisit();
    }
    this.setupPageContextTriggers();
  },
  loadSession() {
    const html = sessionStorage.getItem("ns_chat_html");
    if (html) {
      const box = document.getElementById("ns-msgs");
      if (box) {
        box.innerHTML = html;
        box.scrollTop = box.scrollHeight;
      }
      const history = sessionStorage.getItem("ns_chat_history");
      if (history) this.conversationHistory = JSON.parse(history);
      return true;
    }
    return false;
  },
  saveHistory() {
    sessionStorage.setItem("ns_chat_history", JSON.stringify(this.conversationHistory));
  },
  open() {
    document.getElementById("ns-window").style.display = "flex";
    this.isOpen = true;
    document.getElementById("ns-badge").style.display = "none";
    document.getElementById("ns-toggle").classList.remove("ns-pulse");
  },
  close() {
    document.getElementById("ns-window").style.display = "none";
    this.isOpen = false;
  },
  toggle() {
    this.isOpen ? this.close() : this.open();
  },
  bindEvents() {
    document.getElementById("ns-toggle").addEventListener("click", () => this.toggle());
    document.getElementById("ns-close").addEventListener("click", () => this.close());
    document.getElementById("ns-send").addEventListener("click", () => this.handleSend());
    document.getElementById("ns-input").addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); this.handleSend(); }
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") this.close();
    });
  },
  async handleSend(text) {
    const input = document.getElementById("ns-input");
    const msg = String(text || input.value || "").trim();
    if (!msg) return;
    input.value = "";
    BotUI.addMessage("user", BotUI.escape(msg));
    this.conversationHistory.push({ role: "user", content: msg });
    this.saveHistory();
    BotUI.showTyping();
    const intent = BotIntentClassifier.classify(msg);
    const feature = BotIntentClassifier.detectFeature(msg);
    const topic = BotIntentClassifier.detectLegalTopic(msg);
    this.setMode(intent === "legal" ? "legal" : "guide");
    await new Promise(r => setTimeout(r, 800));
    BotUI.removeTyping();
    if (intent === "guide" && feature) {
      this.respondWithFeatureGuide(feature);
    } else if (intent === "guide" && !feature) {
      this.respondWithFeatureGuide("general");
    } else if (intent === "ambiguous") {
      this.respondWithClarification();
    } else {
      await this.respondWithLegalAnswer(msg, topic);
    }
  },
  setMode(mode) {
    this.currentMode = mode;
    const label = document.getElementById("ns-mode-label");
    if (mode === "legal") {
      label.textContent = "Legal Assistant";
      label.className = "ns-mode ns-mode-legal";
    } else {
      label.textContent = "Site Guide";
      label.className = "ns-mode ns-mode-guide";
    }
  },
  respondWithFeatureGuide(featureKey) {
    BotUI.renderFeatureCard(featureKey);
  },
  respondWithClarification() {
    BotUI.addMessage("bot", "I can help in two ways. Which do you need?", { chips: ["Answer my legal question", "Help me use a NyayaSetu feature", "Show me all features"] });
  },
  async respondWithLegalAnswer(query) {
    const data = await BotApiClient.chat(query, this.conversationHistory.slice(-6));
    if (!data) {
      BotUI.addMessage("bot", "I'm having trouble reaching the server. You can use the tools directly from the navigation menu, or try again in a moment.", { chips: ["Try again", "Show me all features", "Which tool should I use?"] });
      return;
    }
    this.conversationHistory.push({ role: "assistant", content: data.answer });
    this.saveHistory();
    BotUI.renderLegalAnswer(data);
    if (data.feature_hint && data.feature_hint_message) {
      setTimeout(() => BotUI.addMessage("bot", `💡 ${BotUI.escape(data.feature_hint_message)}`, { chips: (data.quick_actions || []).map(a => a.label) }), 400);
    }
  },
  checkFirstVisit() {
    if (!localStorage.getItem("ns_visited")) {
      localStorage.setItem("ns_visited", "1");
      setTimeout(() => {
        this.open();
        BotUI.addMessage("bot", "Namaste! Welcome to <strong>NyayaSetu</strong> - your bridge to justice.<br><br>I can answer <strong>legal questions</strong> grounded in Indian law, or help you <strong>navigate this platform</strong>. What do you need today?", { chips: ["What can NyayaSetu do?", "I have a legal situation", "How do I use this site?"] });
      }, 2000);
    }
  },
  setupPageContextTriggers() {
    const path = window.location.pathname;
    const proactiveMessages = {
      "/fairness-check": { delay: 8000, msg: "Not sure how to describe your situation? Try: <em>My employer has not paid me for 2 months.</em> I can also explain your results after the check.", chips: ["Show me an example", "What counts as a violation?"] },
      "/simulate": { delay: 6000, msg: "Describe what happened to you in plain English - for example: <em>I was fired without notice after 3 years.</em> I will walk you through your legal options.", chips: ["Try: fired without notice", "Try: landlord harassment"] },
      "/translate": { delay: 7000, msg: "Paste any legal notice, contract clause, or court document and I will translate it into plain English.", chips: ["What can I translate?", "Show me an example"] },
      "/amendments": { delay: 8000, msg: "Try searching for a specific article like <em>Article 21</em> to see its full amendment history. Or browse the full timeline below.", chips: ["Show Article 21 history", "How many amendments has India had?"] },
      "/rights-card": { delay: 6000, msg: "Not sure which rights card to generate? Tell me your situation and I will suggest the right category.", chips: ["I was arrested", "I have a workplace issue", "I have a consumer complaint"] },
      "/ai-legal-tools": { delay: 7000, msg: "This page contains Fairness Check, Rights Cards, Scenario Simulator, Legal Translator, Amendments, and Article Compare. Tell me what you are trying to do.", chips: ["Which tool should I use?", "I have a legal situation"] }
    };
    const trigger = proactiveMessages[path];
    if (trigger) {
      setTimeout(() => {
        if (!this.isOpen) {
          document.getElementById("ns-badge").style.display = "block";
          document.getElementById("ns-toggle").classList.add("ns-pulse");
        } else {
          BotUI.addMessage("bot", trigger.msg, { chips: trigger.chips });
        }
      }, trigger.delay);
    }
  }
};

globalThis.NyayaSetuBot = NyayaSetuBot;

document.addEventListener("DOMContentLoaded", () => NyayaSetuBot.init());
