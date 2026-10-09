const BotApiClient = {
  TIMEOUT_MS: 12000,
  async post(endpoint, body) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.TIMEOUT_MS);
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal
      });
      clearTimeout(timeout);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      clearTimeout(timeout);
      return null;
    }
  },
  chat(query, history = []) {
    return this.post("/api/chat", { query, conversation_history: history });
  },
  fairnessCheck(situation) {
    return this.post("/api/fairness-check", { situation });
  },
  simulateScenario(scenario) {
    return this.post("/api/simulate-scenario", { scenario });
  },
  translateText(text, direction) {
    return this.post("/api/translate", { text, direction });
  },
  getRightsCard(rights_type) {
    return this.post("/api/rights-card", { rights_type });
  },
  compareArticles(article_a, article_b) {
    return this.post("/api/compare-articles", { article_a, article_b });
  }
};

globalThis.BotApiClient = BotApiClient;
