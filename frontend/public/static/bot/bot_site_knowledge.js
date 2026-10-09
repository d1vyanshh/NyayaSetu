const NS_KNOWLEDGE = {
  fairness_checker: {
    trigger_phrases: ["am i being treated fairly", "check my rights", "rights violation", "treated unfairly", "is this legal", "can they do this", "fairness check"],
    title: "Fairness Checker",
    what_it_does: "Detects possible legal rights violations in your situation. Tells you which rights may have been violated, which acts and sections apply, and what to do next.",
    how_to_use: ["Click 'Fairness Check' in the top navigation", "Describe your situation in plain English - be as specific as possible", "Example: 'My employer has not paid me for 2 months and threatened to fire me if I complain'", "Click 'Check My Rights'", "Review the violations detected, applicable acts, and suggested next steps"],
    example_queries: ["My landlord entered my home without notice", "Police held me for 3 days without informing my family", "I was denied a job because of my religion"],
    chips: ["Try Fairness Checker ->", "Show me an example situation", "What counts as a rights violation?"],
    nav: "/ai-legal-tools"
  },
  rights_card: {
    trigger_phrases: ["rights card", "know my rights", "what are my rights", "arrest rights", "employment rights", "consumer rights", "tenant rights", "education rights", "printable rights"],
    title: "Rights Card Generator",
    what_it_does: "Generates a structured, printable Know Your Rights card. Choose a category and get a legally grounded card listing your rights, the law behind each right, and what authorities cannot do to you.",
    how_to_use: ["Click 'Rights Cards' in the top navigation", "Select a category: Arrest, Employment, Consumer, Tenant, or Education", "Click 'Generate My Rights Card'", "Each right shows its legal basis (act + section)", "Use the Print button to save or share the card"],
    categories: {
      arrest_rights: "Rights during police arrest and detention - Articles 20, 21, 22",
      employment_rights: "Workplace rights - Industrial Disputes Act, Payment of Wages Act, Shops & Establishments Act",
      consumer_rights: "Consumer protection rights - Consumer Protection Act 2019",
      tenant_rights: "Tenant and housing rights - Rent Control Acts, Transfer of Property Act",
      education_rights: "Right to Education - Article 21A, RTE Act 2009"
    },
    chips: ["Generate Arrest Rights Card", "Generate Employment Rights Card", "What does each category include?"],
    nav: "/ai-legal-tools"
  },
  scenario_simulator: {
    trigger_phrases: ["scenario", "simulate", "fired", "evicted", "step by step", "legal walkthrough", "what happens if", "notice period", "terminated", "dismissed", "wrongful", "what should i do"],
    title: "Scenario Simulator",
    what_it_does: "Describe any legal situation in plain English and get a complete step-by-step legal walkthrough - which laws apply, what the other party cannot legally do, what evidence to preserve, and what remedies are available.",
    how_to_use: ["Click 'Simulate Scenario' in the top navigation", "Describe what happened - e.g. 'I was fired without notice after 4 years at my company'", "Click 'Simulate'", "Review each step of the walkthrough, your rights, and how to proceed"],
    example_queries: ["I was fired without notice", "My landlord is refusing to return my security deposit", "A shopkeeper sold me a defective product and refuses a refund", "My employer is forcing me to work overtime without extra pay"],
    chips: ["Simulate: fired without notice", "Simulate: landlord deposit dispute", "What evidence should I gather?"],
    nav: "/ai-legal-tools"
  },
  translator: {
    trigger_phrases: ["translate", "legal translator", "legal jargon", "plain english", "what does this mean", "legal notice", "contract", "decode", "understand this document", "layman", "simple words", "legal language", "confusing document", "what does it say"],
    title: "Legal Translator",
    what_it_does: "Converts legal jargon into plain English, or plain English into precise legal terminology. Paste any legal notice, contract clause, or court document and get an accurate explanation with every legal term defined.",
    how_to_use: ["Click 'Legal Translator' in the top navigation", "Choose direction: 'Legal -> Plain English' or 'Plain English -> Legal'", "Paste or type the text you want translated", "Click 'Translate'", "Each legal term is explained with its source act and section"],
    example_queries: ["What does 'suo motu cognizance' mean?", "Translate this clause: 'The party of the first part shall hereinafter...'", "Translate to legal: 'My boss fired me without telling me why'"],
    chips: ["Translate a legal notice", "What does suo motu mean?", "Translate plain English to legal terms"],
    nav: "/ai-legal-tools"
  },
  amendment_tracker: {
    trigger_phrases: ["amendment", "constitution changed", "article amended", "how many times amended", "constitutional history", "amendment timeline", "42nd amendment", "44th amendment", "when was article changed", "constitutional amendment"],
    title: "Amendment Tracker",
    what_it_does: "Shows the complete history of how the Indian Constitution has been amended - 106 amendments so far. Search by article number to see every amendment that affected it, with summaries of what changed and why.",
    how_to_use: ["Click 'Amendment Tracker' in the navigation", "Browse the full timeline of all constitutional amendments", "Or search for a specific article - e.g. type '21' to see all amendments affecting Article 21", "Click any amendment card to read a detailed summary"],
    example_queries: ["Which amendments affected Article 21?", "What did the 44th Amendment change?", "When was the right to education added to the Constitution?"],
    chips: ["Show Article 21 amendment history", "What did the 44th Amendment do?", "How many amendments has India had?"],
    nav: "/ai-legal-tools"
  },
  article_comparator: {
    trigger_phrases: ["compare article", "difference between article", "article 14 and 21", "similar articles", "conflict between", "article 19", "how are they related", "article 32", "article 226"],
    title: "Article Comparison Tool",
    what_it_does: "Compare any two articles of the Indian Constitution side by side - similarities, differences, legal conflicts, how they relate to each other, and landmark cases where courts interpreted them together.",
    how_to_use: ["Click 'Compare Articles' in the navigation", "Enter the first article number (e.g. 14)", "Enter the second article number (e.g. 21)", "Click 'Compare'", "Review similarities, differences, conflicts, and the relationship between them"],
    popular_comparisons: [{ a: "14", b: "21", label: "Equality vs Right to Life" }, { a: "19", b: "21", label: "Freedom of Speech vs Personal Liberty" }, { a: "32", b: "226", label: "Supreme Court vs High Court remedies" }],
    chips: ["Compare Article 14 and 21", "Compare Article 19 and 21", "Compare Article 32 and 226"],
    nav: "/ai-legal-tools"
  },
  judgement_predictor: {
    trigger_phrases: ["judgement predictor", "predict judgement", "predict case", "likely outcome", "what is the outcome", "case predictor", "predict"],
    title: "Judgement Predictor",
    what_it_does: "Understand how similar cases have usually ended. Paste your case facts and NyayaSetu compares them with past judgments to estimate whether your matter looks likely to succeed, partly succeed, or face difficulty. It provides similar court decisions, a plain-language outcome, and practical next steps.",
    how_to_use: ["Click 'Judgement Predictor' in the top navigation", "Describe the dispute (e.g. 'I bought a washing machine under warranty. It failed within four months...')", "Click 'Predict Judgement'", "Review the predicted outcome, similar cases, and practical steps"],
    bullets: ["Example 1: I bought a defective product and the company ignores me", "Example 2: My employer fired me without notice"],
    chips: ["What does it predict?", "Show me an example"],
    nav: "/judgement-prediction"
  },
  judgement_predictor_what: {
    trigger_phrases: ["what does it predict", "what does judgement predictor do", "predict what"],
    title: "What it Predicts",
    what_it_does: "The Judgement Predictor analyzes your case facts against thousands of historical Indian court judgements. It predicts the likely outcome (Success, Partial Success, or Difficulty), provides similar past cases, and suggests practical next steps.",
    chips: ["Show me an example", "How to use Judgement Predictor"],
    nav: "/judgement-prediction"
  },
  judgement_predictor_example: {
    trigger_phrases: ["show me an example", "example situation", "give me an example", "example"],
    title: "Example Scenarios",
    what_it_does: "Here are some examples of what you can type into the predictor:",
    bullets: [
      "Consumer Issue: 'I bought a defective refrigerator and the company is ignoring my emails.'",
      "Employment Issue: 'My employer fired me without any prior notice.'",
      "Property Issue: 'My landlord is trying to evict me without returning my deposit.'"
    ],
    chips: ["What does it predict?", "How to use Judgement Predictor"],
    nav: "/judgement-prediction"
  },
  nyayadraft: {
    trigger_phrases: ["nyayadraft", "draft document", "legal template", "create document", "generate document", "docx", "draft"],
    title: "NyayaDraft",
    what_it_does: "Helps you create customized legal documents by filling placeholders in legal templates and downloading them as editable DOCX drafts.",
    how_to_use: ["Click 'NyayaDraft' in the top navigation", "Choose a legal template from the dropdown or upload a PDF", "Fill each placeholder with case or party details", "Click 'Preview' to see the completed document", "Click 'Download .docx' to get the editable draft"],
    faqs: [
      { q: "What templates are available?", a: "We currently offer templates for Affidavit, Consultancy Agreement, Experience Letter, Internship Agreement, NDA, NOC, Offer Letter, Partnership Deed, Power Of Attorney, Rent Agreement, Service Agreement, and Vendor Agreement." }
    ],
    chips: ["What templates are available?", "How to use NyayaDraft"],
    nav: "/nyayadraft"
  },
  nyayadraft_templates: {
    trigger_phrases: ["template", "templates", "what templates", "list of templates", "available templates"],
    title: "NyayaDraft Templates",
    what_it_does: "NyayaDraft currently offers the following legal document templates for you to fill and download:",
    bullets: [
      "Affidavit",
      "Consultancy Agreement",
      "Experience Letter",
      "Internship Agreement",
      "NDA (Non-Disclosure Agreement)",
      "NOC (No Objection Certificate)",
      "Offer Letter",
      "Partnership Deed",
      "Power Of Attorney",
      "Rent Agreement",
      "Service Agreement",
      "Vendor Agreement"
    ],
    chips: ["How to use NyayaDraft", "What is NyayaDraft?"],
    nav: "/nyayadraft"
  },
  pdf_summariser: {
    trigger_phrases: ["pdf summariser", "pdf summarizer", "summarise pdf", "summarize pdf", "document intelligence", "scan document", "upload pdf", "extract clause", "read contract", "summariser", "summarizer"],
    title: "PDF Summariser",
    what_it_does: "Upload a PDF, DOCX, or scanned image to extract every clause, date, party, and alert in an exhaustive legal report.",
    how_to_use: ["Click 'PDF Summariser' in the top navigation", "Click 'Choose File' to select a document (PDF, DOCX, or image)", "Click 'Summarize File'", "Review the extracted report sections, including OCR and document analysis"],
    chips: ["What documents can I upload?", "How does OCR work?"],
    nav: "/pdf-summariser"
  },
  pdf_summariser_docs: {
    trigger_phrases: ["what documents can i upload", "supported documents", "file formats", "what can i upload", "what documents"],
    title: "Supported Documents",
    what_it_does: "The PDF Summariser supports multiple document formats for extraction:",
    bullets: [
      "PDF files (standard text PDFs)",
      "DOCX (Word documents including paragraphs, tables, and headings)",
      "Scanned Images (using OCR for images and handwriting)"
    ],
    chips: ["How does OCR work?", "How to use PDF Summariser"],
    nav: "/pdf-summariser"
  },
  pdf_summariser_ocr: {
    trigger_phrases: ["how does ocr work", "what is ocr", "handwriting", "scanned document", "ocr"],
    title: "How OCR Works",
    what_it_does: "OCR (Optical Character Recognition) allows the summariser to read text from images. If you upload a scanned PDF, an image file, or even a handwritten document, the OCR engine will scan and extract the text before summarizing it.",
    chips: ["What documents can I upload?", "How to use PDF Summariser"],
    nav: "/pdf-summariser"
  },
  general: {
    trigger_phrases: ["how does this work", "what can you do", "help", "confused", "getting started", "tour", "show me around", "what is this page"],
    title: "Getting Started",
    overview: "Welcome to NyayaSetu! Here is what I can help you with:",
    tools_summary: [
      { name: "Legal Questions", use: "Ask any legal question in plain English" },
      { name: "Site Guide", use: "Ask me how to use tools or navigate the site" }
    ],
    chips: ["About NyayaSetu", "Tools of NyayaSetu", "How to use correctly", "Common Questions"]
  },
  about_nyayasetu: {
    trigger_phrases: ["what is nyayasetu", "about nyayasetu", "info about nyaysetu", "nyayasetu project", "who made nyayasetu", "purpose of nyayasetu"],
    title: "About NyayaSetu",
    overview: "NyayaSetu is an AI-powered legal assistance platform designed to bridge the gap between Indian citizens and the legal system.",
    faqs: [
      { q: "Who is it for?", a: "Indian citizens looking to understand their legal rights and options." },
      { q: "Is it a substitute for a lawyer?", a: "No, NyayaSetu provides informational guidance, not formal legal advice." },
      { q: "What domains does it cover?", a: "Constitutional law, consumer protection, tenant rights, employment, and more." }
    ],
    chips: ["Tools of NyayaSetu", "How to use correctly", "Common Questions"]
  },
  how_to_use_correctly: {
    trigger_phrases: ["how to use nyayasetu correctly", "guide to use nyayasetu", "how to use nyayasetu", "nyayasetu site guide", "how to use the site", "best practices"],
    title: "How to Use NyayaSetu Correctly",
    overview: "To get the best and most accurate results from NyayaSetu, follow these guidelines:",
    how_to_use: [
      "Be specific: Provide details like dates, amounts, and actions taken.",
      "Use plain English: You don't need to use legal jargon.",
      "Provide context: State the relationship (e.g., 'my landlord', 'my employer').",
      "Verify with a lawyer: Always confirm AI-generated advice with a qualified legal professional before taking formal action."
    ],
    chips: ["Common Questions", "Tools of NyayaSetu"]
  },
  common_questions: {
    trigger_phrases: ["common questions", "faq", "frequently asked questions", "clear common qns", "common queries"],
    title: "Common Questions (FAQ)",
    overview: "Here are some common questions about using NyayaSetu:",
    faqs: [
      { q: "Is my data safe?", a: "Yes, your queries are processed securely." },
      { q: "Can NyayaSetu represent me in court?", a: "No, NyayaSetu cannot provide legal representation." },
      { q: "How accurate is the information?", a: "It is grounded in the Indian Constitution and key acts, but AI can sometimes make mistakes. Always verify." }
    ],
    chips: ["How to use correctly", "About NyayaSetu"]
  },
  nyayasetu_tools: {
    trigger_phrases: ["tools of nyayasetu", "what tools", "nyayasetu features", "show me tools", "list tools", "site features", "ai tools", "legal tools", "ai legal tools"],
    title: "AI Tools of NyayaSetu",
    overview: "NyayaSetu provides specialized AI legal tools to help you navigate the legal system:",
    tools_summary: [
      { name: "Judgement Predictor", use: "Predicts the likely outcome of your dispute" },
      { name: "NyayaDraft", use: "Create customized legal documents from templates" },
      { name: "PDF Summariser", use: "Extract clauses, dates, and parties from documents" },
      { name: "Fairness Checker", use: "Detect possible rights violations" },
      { name: "Rights Card Generator", use: "Get printable rights for specific scenarios" },
      { name: "Scenario Simulator", use: "Step-by-step walkthrough of legal options" },
      { name: "Legal Translator", use: "Convert legal jargon to plain English" },
      { name: "Amendment Tracker", use: "Explore constitutional changes" },
      { name: "Article Comparator", use: "Compare constitutional articles side-by-side" }
    ],
    chips: ["How to use correctly", "About NyayaSetu"],
    nav: "/ai-legal-tools"
  },
  get_advice: {
    trigger_phrases: ["get advice", "legal advice", "ask question", "legal situation", "domain", "auto-detect domain", "how to ask"],
    title: "Get Advice",
    what_it_does: "Turn a legal problem into a court-ready action plan. You can ask any legal question in plain English, and NyayaSetu will retrieve relevant laws and give you a structured brief.",
    how_to_use: ["Click 'Get Advice' in the navigation", "Optionally select a specific legal domain (like Labour, Family, or Constitutional Law), or leave it as 'Auto-detect Domain'", "Describe your situation in the text box", "Click 'Ask' to get your action plan"],
    faqs: [
      { q: "What domains are available?", a: "Constitutional Law, Labour & Employment, Family & Divorce, Property & Tenant, Consumer Protection, and Business Compliance." }
    ],
    chips: ["About NyayaSetu", "How to use correctly"],
    nav: "/legal-advice"
  },
  translator: {
    trigger_phrases: ["translator", "legal translator", "translate", "plain english"],
    title: "Legal Translator",
    what_it_does: "The Legal Translator converts complex legal jargon, court notices, or contracts into plain, easy-to-understand English.",
    how_to_use: ["Navigate to 'AI Tools' then select 'Legal Translator'", "Paste your legal text into the box", "Click Translate"],
    chips: ["Fairness Checker", "AI Tools"],
    nav: "/ai-legal-tools"
  },
  rights_card: {
    trigger_phrases: ["rights card", "know my rights", "generate rights card"],
    title: "Rights Card",
    what_it_does: "Generates a concise, printable summary of your fundamental and legal rights for specific situations like unlawful arrest, workplace discrimination, or consumer fraud.",
    how_to_use: ["Navigate to AI Tools > Rights Card", "Select your legal situation", "Get a printable summary of your rights"],
    chips: ["Fairness Checker", "AI Tools"],
    nav: "/ai-legal-tools"
  },
  fairness_check: {
    trigger_phrases: ["fairness check", "fairness checker", "unfair", "violation"],
    title: "Fairness Checker",
    what_it_does: "Analyzes your situation to detect potential rights violations. It checks your facts against Indian law to tell you if you are being treated unfairly and what legal protections apply.",
    how_to_use: ["Navigate to AI Tools > Fairness Checker", "Describe what happened to you", "Review the rights violation analysis"],
    chips: ["Scenario Simulator", "Rights Card"],
    nav: "/ai-legal-tools"
  },
  scenario_simulator: {
    trigger_phrases: ["scenario simulator", "simulate scenario", "simulate this scenario", "what happens if", "simulate", "scenario"],
    title: "Scenario Simulator",
    what_it_does: "Provides a step-by-step procedural walkthrough for legal situations. It tells you what evidence to preserve, what the opposite party cannot legally do, and how to proceed.",
    how_to_use: ["Navigate to AI Tools > Scenario Simulator", "Describe your issue", "Follow the step-by-step guide"],
    chips: ["Fairness Checker", "AI Tools"],
    nav: "/ai-legal-tools"
  },
  amendments: {
    trigger_phrases: ["amendments", "amendment tracker", "article history"],
    title: "Amendment Tracker",
    what_it_does: "Tracks changes to the Constitution of India over time. You can see how specific Articles (like Article 21) have been amended and read the historical text.",
    chips: ["Compare Articles", "AI Tools"],
    nav: "/ai-legal-tools"
  },
  compare_articles: {
    trigger_phrases: ["compare articles", "article comparator", "difference between", "compare"],
    title: "Article Comparator",
    what_it_does: "Allows you to select two Constitutional Articles (e.g., Article 14 and Article 21) and compares them side-by-side to explain their differences and how they interact.",
    chips: ["Amendment Tracker", "AI Tools"],
    nav: "/ai-legal-tools"
  },
  compare_14_21: {
    trigger_phrases: ["compare article 14 and 21", "article 14 and 21"],
    title: "Article 14 vs Article 21",
    what_it_does: "Here is an example comparison from the Article Comparator:",
    bullets: [
      "Article 14: Guarantees equality before the law and equal protection of laws.",
      "Article 21: Protects life and personal liberty, which cannot be deprived except by procedure established by law.",
      "Intersection: A procedure under Article 21 must be fair, just, and reasonable, which is the core test of Article 14."
    ],
    chips: ["AI Tools", "Compare Article 19 and 21"],
    nav: "/ai-legal-tools"
  },
  compare_19_21: {
    trigger_phrases: ["compare article 19 and 21", "article 19 and 21"],
    title: "Article 19 vs Article 21",
    what_it_does: "Here is an example comparison from the Article Comparator:",
    bullets: [
      "Article 19: Provides six freedoms (speech, assembly, etc.) subject to reasonable restrictions.",
      "Article 21: A broad right to life and liberty.",
      "Intersection: Laws restricting Article 19 freedoms must also pass the test of Article 21's 'procedure established by law'."
    ],
    chips: ["AI Tools", "Compare Article 32 and 226"],
    nav: "/ai-legal-tools"
  },
  compare_32_226: {
    trigger_phrases: ["compare article 32 and 226", "article 32 and 226"],
    title: "Article 32 vs Article 226",
    what_it_does: "Here is an example comparison from the Article Comparator:",
    bullets: [
      "Article 32: The right to move the Supreme Court directly for fundamental rights violations.",
      "Article 226: Gives High Courts the power to issue writs for fundamental rights AND other legal rights.",
      "Intersection: Article 226 has a wider scope since it covers non-fundamental rights, whereas Article 32 is exclusively for fundamental rights."
    ],
    chips: ["AI Tools", "Compare Article 14 and 21"],
    nav: "/ai-legal-tools"
  }
};

globalThis.NS_KNOWLEDGE = NS_KNOWLEDGE;
