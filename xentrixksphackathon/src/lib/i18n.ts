import { usePrefs } from "@/stores/prefs";

const en = {
  // sidebar
  chat: "Chat Assistant",
  dashboard: "Dashboard",
  network: "Criminal Network",
  financial: "Financial Crime",
  map: "Crime Map",
  sociological: "Sociological Insights",
  cases: "Case Search",
  offenders: "Offender Profiles",
  alerts: "Alerts",
  audit: "Audit Log",
  settings: "Settings",
  collapse: "Collapse",
  brandLine1: "Karnataka SCRB",
  brandLine2: "Crime Intelligence",

  // topbar
  signIn: "Sign In",
  signOut: "Sign Out",
  search: "Search cases, FIRs, offenders, districts…",

  // chat page
  chatTitle: "Chat Assistant",
  chatBadge: "Explainable NL → SQL",
  chatSubtitle:
    "Natural-language queries against the Karnataka SCRB crime records database.",
  history: "History",
  exportPdf: "Export PDF",
  send: "Send",
  askPlaceholder: "Ask about FIRs, offenders, districts, or trends…",
  analysing: "Assistant is analysing the request…",
  explainabilityNote:
    "Responses include the generated SQL and row count for explainability. Every query is audited.",
  translationNote:
    "Response translation requires backend integration — UI labels only for now.",
  historyTitle: "Conversation history",
  showReasoning: "Show reasoning",
  voiceUnsupported: "Voice input not supported in this browser",

  // suggestion chips
  s1: "Show robbery cases in Bengaluru last 6 months",
  s2: "Which accused have 3+ FIRs?",
  s3: "Show network around Accused A12",
  s4: "Crime trend for cybercrime this year",
  s5: "Total open cases this month?",
};

const kn: typeof en = {
  chat: "ಚಾಟ್ ಸಹಾಯಕ",
  dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
  network: "ಅಪರಾಧಿ ಜಾಲ",
  financial: "ಆರ್ಥಿಕ ಅಪರಾಧ",
  map: "ಅಪರಾಧ ನಕ್ಷೆ",
  sociological: "ಸಾಮಾಜಿಕ ಒಳನೋಟಗಳು",
  cases: "ಪ್ರಕರಣ ಹುಡುಕಾಟ",
  offenders: "ಅಪರಾಧಿ ವಿವರ",
  alerts: "ಎಚ್ಚರಿಕೆಗಳು",
  audit: "ಆಡಿಟ್ ಲಾಗ್",
  settings: "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
  collapse: "ಮಡಚು",
  brandLine1: "ಕರ್ನಾಟಕ SCRB",
  brandLine2: "ಅಪರಾಧ ಗುಪ್ತಚರ",

  signIn: "ಪ್ರವೇಶಿಸಿ",
  signOut: "ನಿರ್ಗಮನ",
  search: "ಪ್ರಕರಣ, ಎಫ್‌ಐಆರ್, ಅಪರಾಧಿ, ಜಿಲ್ಲೆ ಹುಡುಕಿ…",

  chatTitle: "ಚಾಟ್ ಸಹಾಯಕ",
  chatBadge: "ವಿವರಿಸಬಹುದಾದ NL → SQL",
  chatSubtitle:
    "ಕರ್ನಾಟಕ SCRB ಅಪರಾಧ ದಾಖಲೆಗಳ ಡೇಟಾಬೇಸ್ ವಿರುದ್ಧ ಸ್ವಾಭಾವಿಕ-ಭಾಷಾ ಪ್ರಶ್ನೆಗಳು.",
  history: "ಇತಿಹಾಸ",
  exportPdf: "PDF ರಫ್ತು",
  send: "ಕಳುಹಿಸಿ",
  askPlaceholder: "ಎಫ್‌ಐಆರ್, ಅಪರಾಧಿ, ಜಿಲ್ಲೆ ಅಥವಾ ಪ್ರವೃತ್ತಿಗಳ ಬಗ್ಗೆ ಕೇಳಿ…",
  analysing: "ಸಹಾಯಕ ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ…",
  explainabilityNote:
    "ಪ್ರತಿ ಪ್ರತಿಕ್ರಿಯೆಯು ರಚಿಸಲಾದ SQL ಮತ್ತು ಸಾಲುಗಳ ಎಣಿಕೆಯನ್ನು ಒಳಗೊಂಡಿದೆ. ಎಲ್ಲಾ ಪ್ರಶ್ನೆಗಳು ಆಡಿಟ್ ಆಗಿವೆ.",
  translationNote:
    "ಪ್ರತಿಕ್ರಿಯೆ ಅನುವಾದವು ಬ್ಯಾಕೆಂಡ್ ಸಂಯೋಜನೆಗೆ ಅಗತ್ಯವಿದೆ — ಇದೀಗ UI ಲೇಬಲ್‌ಗಳು ಮಾತ್ರ.",
  historyTitle: "ಸಂಭಾಷಣೆ ಇತಿಹಾಸ",
  showReasoning: "ತಾರ್ಕಿಕತೆ ತೋರಿಸಿ",
  voiceUnsupported: "ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ",

  s1: "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳೆದ 6 ತಿಂಗಳಲ್ಲಿ ದರೋಡೆ ಪ್ರಕರಣಗಳನ್ನು ತೋರಿಸಿ",
  s2: "ಯಾವ ಅಪರಾಧಿಗಳಿಗೆ 3+ ಎಫ್‌ಐಆರ್‌ಗಳಿವೆ?",
  s3: "ಅಪರಾಧಿ A12 ಸುತ್ತಲಿನ ಜಾಲವನ್ನು ತೋರಿಸಿ",
  s4: "ಈ ವರ್ಷ ಸೈಬರ್ ಅಪರಾಧದ ಪ್ರವೃತ್ತಿ",
  s5: "ಈ ತಿಂಗಳ ಒಟ್ಟು ತೆರೆದ ಪ್ರಕರಣಗಳು?",
};

export type DictKey = keyof typeof en;

export function useT() {
  const lang = usePrefs((s) => s.lang);
  const dict = lang === "kn" ? kn : en;
  return (k: DictKey) => dict[k];
}
