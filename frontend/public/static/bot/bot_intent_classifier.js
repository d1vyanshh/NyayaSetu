const BotIntentClassifier = {
  GUIDE_SIGNALS: ["how do i", "how to", "where is", "where can i", "what is this page", "what does this do", "i don't understand", "i dont understand", "confused", "help me use", "how does this work", "what can i do here", "navigate", "show me how", "what is this feature", "getting started", "what is nyayasetu", "about nyayasetu", "faq", "common questions", "tools", "features", "best practices", "guide", "judgement predictor", "predict", "nyayadraft", "draft", "pdf summariser", "pdf summarizer", "summarise", "summarizer", "document intelligence", "template", "templates", "ai tools", "legal tools", "get advice", "domain", "what documents", "ocr", "example", "what does it predict", "translator", "legal translator", "translate", "plain english", "rights card", "know my rights", "generate rights card", "fairness check", "fairness checker", "unfair", "violation", "scenario simulator", "simulate", "scenario", "amendments", "amendment", "compare articles", "comparator", "compare article", "article compare", "compare"],
  LEGAL_SIGNALS: ["right", "arrested", "detention", "fired", "terminated", "dismiss", "evict", "salary", "wages", "police", "landlord", "tenant", "court", "bail", "section", "article", "act", "law", "legal", "charge", "warrant", "notice", "complaint", "compensation", "fir", "harassment", "discrimination", "consumer", "refund", "defective", "overtime", "provident fund", "pf", "gratuity", "case"],
  classify(text) {
    const t = String(text || "").toLowerCase();
    const isGuide = this.GUIDE_SIGNALS.some(s => t.includes(s));
    const isLegal = this.LEGAL_SIGNALS.some(s => t.includes(s));
    if (isGuide) return "guide";
    if (isLegal) return "legal";
    if (t.length < 15) return "ambiguous";
    return "guide";
  },
  detectFeature(text) {
    const t = String(text || "").toLowerCase();
    for (const [key, val] of Object.entries(NS_KNOWLEDGE)) {
      if (val.trigger_phrases && val.trigger_phrases.some(p => t.includes(p))) return key;
    }
    return null;
  },
  detectLegalTopic(text) {
    const t = String(text || "").toLowerCase();
    const topicMap = [
      { topic: "arrest", keys: ["arrest", "detain", "custody", "lock up", "jail"] },
      { topic: "termination", keys: ["fired", "terminat", "dismiss", "sacked", "laid off", "notice period", "retrench"] },
      { topic: "landlord", keys: ["landlord", "tenant", "rent", "evict", "deposit", "house owner"] },
      { topic: "wages", keys: ["salary", "wages", "pay", "overtime", "not paid", "payment", "minimum wage"] },
      { topic: "police", keys: ["police", "fir", "cop", "constable", "officer", "station"] },
      { topic: "consumer", keys: ["consumer", "product", "refund", "defect", "shopkeeper", "seller", "ecommerce"] },
      { topic: "discrimination", keys: ["discriminat", "religion", "caste", "gender", "harass"] },
      { topic: "constitution", keys: ["article", "constitution", "fundamental right", "amendment"] },
      { topic: "bail", keys: ["bail", "bailable", "anticipatory"] }
    ];
    const hit = topicMap.find(({ keys }) => keys.some(k => t.includes(k)));
    return hit ? hit.topic : null;
  }
};

globalThis.BotIntentClassifier = BotIntentClassifier;
