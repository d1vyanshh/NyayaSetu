const NS_ICON = `<svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true"><path d="M7 20h12M13 6v14M7 11l6-5 6 5" stroke="#f0d080" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="7" cy="16" r="3" stroke="#c9a84c" stroke-width="1.5"/><circle cx="19" cy="16" r="3" stroke="#c9a84c" stroke-width="1.5"/></svg>`;

const BotUI = {
  escape(text) {
    return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  },
  addMessage(role, content, options = {}) {
    const box = document.getElementById("ns-msgs");
    if (!box) return;
    const row = document.createElement("div");
    row.className = `ns-msg-row ns-${role}`;
    const bubble = document.createElement("div");
    bubble.className = "ns-bubble";
    bubble.innerHTML = content;
    if (role === "bot") {
      const avatar = document.createElement("div");
      avatar.className = "ns-avatar";
      avatar.innerHTML = NS_ICON;
      row.appendChild(avatar);
    }
    row.appendChild(bubble);
    box.appendChild(row);
    if (options.confidence !== undefined) bubble.insertAdjacentHTML("beforeend", this.renderConfidenceBadge(options.confidence));
    if (options.source) bubble.insertAdjacentHTML("beforeend", this.renderSourceBlock(options.source.label, options.source.text));
    if (options.chips?.length) box.insertAdjacentHTML("beforeend", this.renderChips(options.chips));
    box.scrollTop = box.scrollHeight;
    this.saveToSession();
  },
  showTyping() {
    if (document.getElementById("ns-typing")) return;
    const box = document.getElementById("ns-msgs");
    box.insertAdjacentHTML("beforeend", `<div id="ns-typing" class="ns-msg-row ns-bot"><div class="ns-avatar">${NS_ICON}</div><div class="ns-typing"><span></span><span></span><span></span></div></div>`);
    box.scrollTop = box.scrollHeight;
    this.saveToSession();
  },
  removeTyping() {
    document.getElementById("ns-typing")?.remove();
    this.saveToSession();
  },
  saveToSession() {
    const box = document.getElementById("ns-msgs");
    if (box) sessionStorage.setItem("ns_chat_html", box.innerHTML);
  },
  renderConfidenceBadge(score) {
    const n = Number(score || 0);
    const cls = n >= 0.75 ? "high" : n >= 0.45 ? "med" : "low";
    const text = n >= 0.75 ? "High confidence" : n >= 0.45 ? "Moderate" : "Low - verify with a lawyer";
    return `<div class="ns-confidence ns-${cls}">● ${text}</div>`;
  },
  renderSourceBlock(source_text, chunk_preview) {
    const id = `ns-src-${Math.random().toString(36).slice(2)}`;
    return `<div class="ns-source" onclick="document.getElementById('${id}').classList.toggle('ns-open')"><strong>Sources</strong><div class="ns-source-label">${this.escape(source_text || "Retrieved legal corpus")}</div><div id="${id}" class="ns-source-text">${this.escape(chunk_preview || "")}</div></div>`;
  },
  renderChips(chips) {
    return `<div class="ns-chips">${chips.map(c => `<button type="button" class="ns-chip" onclick="NyayaSetuBot.handleSend('${this.escape(String(c)).replace(/'/g, "\\'")}')">${this.escape(c)}</button>`).join("")}</div>`;
  },
  renderFeatureCard(feature_key) {
    const k = NS_KNOWLEDGE[feature_key] || NS_KNOWLEDGE.general;
    const steps = (k.how_to_use || []).map((s, i) => `<div class="ns-step"><span class="ns-step-num">${i + 1}</span><span>${this.escape(s)}</span></div>`).join("");
    const tools = (k.tools_summary || []).map(t => `<div class="ns-step"><span><strong>${this.escape(t.name)}:</strong> ${this.escape(t.use)}</span></div>`).join("");
    const faqs = (k.faqs || []).map(f => `<div class="ns-step"><span><strong>Q: ${this.escape(f.q)}</strong><br>A: ${this.escape(f.a)}</span></div>`).join("");
    const bullets = (k.bullets || []).map(b => `<div class="ns-step"><span>• ${this.escape(b)}</span></div>`).join("");
    const summary = k.what_it_does || k.overview || "";
    const nav = k.nav ? `<button class="ns-nav-btn" onclick="window.location.href='${k.nav}'">Open feature</button>` : "";
    let blocks = "";
    if (steps) blocks += `<div class="ns-steps-block">${steps}</div>`;
    if (tools) blocks += `<div class="ns-steps-block">${tools}</div>`;
    if (faqs) blocks += `<div class="ns-steps-block">${faqs}</div>`;
    if (bullets) blocks += `<div class="ns-steps-block">${bullets}</div>`;
    this.addMessage("bot", `<strong>${this.escape(k.title)}</strong><br><span class="ns-muted-text">${this.escape(summary)}</span>${blocks}${nav}`, { chips: k.chips || [] });
  },
  renderLegalAnswer(data) {
    const answer = data.answer || data.data?.answer || data.data?.simulation?.summary || "I found grounded legal information from NyayaSetu.";
    const points = data.data?.legal_points || data.data?.simulation?.rights_involved || data.data?.possible_violations?.map(v => `${v.right}: ${v.why_applicable}`) || [];
    const pointHtml = points.length ? `<ul>${points.slice(0, 5).map(p => `<li>${this.escape(p)}</li>`).join("")}</ul>` : "";
    const chunk = data.explainability?.retrieved_chunks?.[0] || {};
    const chips = (data.quick_actions || []).map(a => a.label).slice(0, 3);
    if (!chips.length) chips.push("Simulate this scenario", "Generate rights card", "Which tool should I use?");
    this.addMessage("bot", `<p>${this.escape(answer)}</p>${pointHtml}`, {
      confidence: data.confidence,
      source: { label: chunk.source_file, text: chunk.text },
      chips
    });
    if (data.warnings?.length) {
      this.addMessage("bot", "⚠ Some information could not be verified against the legal corpus. Please confirm with a qualified lawyer before taking action.");
    }
  },
  renderViolationsCard(violations) {
    const html = (violations || []).map(v => `<div class="ns-mini-card"><strong>${this.escape(v.right)}</strong><br><span>${this.escape(v.act)}</span><p>${this.escape(v.why_applicable)}</p>${this.renderConfidenceBadge(v.confidence)}</div>`).join("");
    this.addMessage("bot", html || "No clear violations were identified from the retrieved corpus.");
  },
  renderSimulationCard(simulation) {
    const steps = (simulation?.legal_walkthrough || []).map(s => `<div class="ns-step"><span class="ns-step-num">${s.step}</span><span><strong>${this.escape(s.title)}</strong><br>${this.escape(s.detail)}</span></div>`).join("");
    this.addMessage("bot", `<strong>${this.escape(simulation?.summary || "Scenario simulation")}</strong><div class="ns-steps-block">${steps}</div>`);
  }
};

globalThis.BotUI = BotUI;
