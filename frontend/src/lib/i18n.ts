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
  admin: "Admin Console",
  supervisor: "Supervisor Panel",
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
  chatSubtitle: "Natural-language queries against the Karnataka SCRB crime records database.",
  history: "History",
  exportPdf: "Export PDF",
  send: "Send",
  askPlaceholder: "Ask about FIRs, offenders, districts, or trends…",
  analysing: "Assistant is analysing the request…",
  historyTitle: "Conversation history",
  showReasoning: "Show reasoning",
  voiceUnsupported: "Voice input not supported in this browser",

  // self-introduction (spoken on page load, ~10 seconds)
  introGreeting:
    "Namaskara. I am the Karnataka SCRB Crime Intelligence Assistant, powered by advanced AI. " +
    "I can help you query police records, analyze suspect networks, explore crime trends, " +
    "and generate detailed case reports — all in natural language. " +
    "Just type or speak your question and I will respond instantly. How can I assist you today?",

  // suggestion chips
  s1: "Show robbery cases in Bengaluru",
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
  admin: "ನಿರ್ವಾಹಕ ಕನ್ಸೋಲ್",
  supervisor: "ಮೇಲ್ವಿಚಾರಕ ಫಲಕ",
  collapse: "ಮಡಚು",
  brandLine1: "ಕರ್ನಾಟಕ SCRB",
  brandLine2: "ಅಪರಾಧ ಗುಪ್ತಚರ",

  signIn: "ಪ್ರವೇಶಿಸಿ",
  signOut: "ನಿರ್ಗಮನ",
  search: "ಪ್ರಕರಣ, ಎಫ್‌ಐಆರ್, ಅಪರಾಧಿ, ಜಿಲ್ಲೆ ಹುಡುಕಿ…",

  chatTitle: "ಚಾಟ್ ಸಹಾಯಕ",
  chatBadge: "ವಿವರಿಸಬಹುದಾದ NL → SQL",
  chatSubtitle: "ಕರ್ನಾಟಕ SCRB ಅಪರಾಧ ದಾಖಲೆಗಳ ಡೇಟಾಬೇಸ್ ವಿರುದ್ಧ ಸ್ವಾಭಾವಿಕ-ಭಾಷಾ ಪ್ರಶ್ನೆಗಳು.",
  history: "ಇತಿಹಾಸ",
  exportPdf: "PDF ರಫ್ತು",
  send: "ಕಳುಹಿಸಿ",
  askPlaceholder: "ಎಫ್‌ಐಆರ್, ಅಪರಾಧಿ, ಜಿಲ್ಲೆ ಅಥವಾ ಪ್ರವೃತ್ತಿಗಳ ಬಗ್ಗೆ ಕೇಳಿ…",
  analysing: "ಸಹಾಯಕ ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ…",
  historyTitle: "ಸಂಭಾಷಣೆ ಇತಿಹಾಸ",
  showReasoning: "ತಾರ್ಕಿಕತೆ ತೋರಿಸಿ",
  voiceUnsupported: "ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ",

  // self-introduction (spoken on page load, ~10 seconds)
  introGreeting:
    "ನಮಸ್ಕಾರ. ನಾನು ಕರ್ನಾಟಕ SCRB ಅಪರಾಧ ಗುಪ್ತಚರ ಸಹಾಯಕ. " +
    "ನಾನು ನಿಮಗೆ ಪೊಲೀಸ್ ದಾಖಲೆಗಳನ್ನು ಪ್ರಶ್ನಿಸಲು, " +
    "ಅಪರಾಧಿ ಜಾಲಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲು, " +
    "ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳನ್ನು ಅನ್ವೇಷಿಸಲು " +
    "ಮತ್ತು ವಿವರವಾದ ಪ್ರಕರಣ ವರದಿಗಳನ್ನು ರಚಿಸಲು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. " +
    "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಮಾತನಾಡಿ. ನಾನು ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧನಾಗಿದ್ದೇನೆ.",

  s1: "ಬೆಂಗಳೂರಿನಲ್ಲಿ ದರೋಡೆ ಪ್ರಕರಣಗಳನ್ನು ತೋರಿಸಿ",
  s2: "ಯಾವ ಅಪರಾಧಿಗಳಿಗೆ 3+ ಎಫ್‌ಐಆರ್‌ಗಳಿವೆ?",
  s3: "ಅಪರಾಧಿ B3 ಸುತ್ತಲಿನ ಜಾಲವನ್ನು ತೋರಿಸಿ",
  s4: "ಈ ವರ್ಷ ಸೈಬರ್ ಅಪರಾಧದ ಪ್ರವೃತ್ತಿ",
  s5: "ಈ ತಿಂಗಳ ಒಟ್ಟು ತೆರೆದ ಪ್ರಕರಣಗಳು?",
};

export type DictKey = keyof typeof en;

export function useT() {
  const lang = usePrefs((s) => s.lang);
  const dict = lang === "kn" ? kn : en;
  return (k: DictKey) => dict[k];
}

// Page Title & Subtitle translations
const headerTranslations: Record<string, Record<string, string>> = {
  en: {
    // Dashboard
    "Dashboard": "Dashboard",
    
    // Settings
    "Settings": "Settings",
    "Profile, security and notification preferences.": "Profile, security and notification preferences.",

    // Network
    "Criminal Intelligence Network": "Criminal Intelligence Network",
    "Workspace for co-offending links, Modularity gang clustering, and visual tracing.": "Workspace for co-offending links, Modularity gang clustering, and visual tracing.",

    // Financial
    "Financial Crime & Transaction Intelligence": "Financial Crime & Transaction Intelligence",
    "Discover money laundering networks, circular round-tripping, and shared account anomalies.": "Discover money laundering networks, circular round-tripping, and shared account anomalies.",

    // Map
    "Geospatial Crime Hotspots": "Geospatial Crime Hotspots",
    "State-level spatial intelligence dashboard mapping offence hubs, station locations, and division metrics.": "State-level spatial intelligence dashboard mapping offence hubs, station locations, and division metrics.",

    // Sociological
    "Sociological Insights & Crime Analytics": "Sociological Insights & Crime Analytics",
    "Examine regional crime occurrences filtered by demographic indicators, educational indexes, and poverty stats.": "Examine regional crime occurrences filtered by demographic indicators, educational indexes, and poverty stats.",

    // Cases
    "Crime Case Search Registry": "Crime Case Search Registry",
    "Query, filter, and inspect detailed First Information Reports (FIRs) across Karnataka SCRB database.": "Query, filter, and inspect detailed First Information Reports (FIRs) across Karnataka SCRB database.",

    // Offenders
    "Offender Registry & Profiles": "Offender Registry & Profiles",
    "Manage repeat suspects, history sheeters, gang members, and profiles with detailed co-offending indices.": "Manage repeat suspects, history sheeters, gang members, and profiles with detailed co-offending indices.",

    // Alerts
    "Intelligence Alerts & Pattern Warnings": "Intelligence Alerts & Pattern Warnings",
    "Automated triggers identifying serial offenders, crime waves, and anomalies in recent crime reports.": "Automated triggers identifying serial offenders, crime waves, and anomalies in recent crime reports.",

    // Audit
    "System Audit Log & Event Log": "System Audit Log & Event Log",
    "Tamper-evident logs recording administrative operations, search queries, access controls, and logins.": "Tamper-evident logs recording administrative operations, search queries, access controls, and logins.",

    // Supervisor
    "Supervisor Control Center": "Supervisor Control Center",
    "Assign district permissions, review access requests, audit active investigators, and manage system status.": "Assign district permissions, review access requests, audit active investigators, and manage system status.",

    // Admin
    "Platform Administration Portal": "Platform Administration Portal",
    "System settings, backend service configurations, logs monitoring, and complete user profile management.": "System settings, backend service configurations, logs monitoring, and complete user profile management.",

    // General UI labels
    "Search Accused": "Search Accused",
    "Search FIR / Case No": "Search FIR / Case No",
    "Filter District": "Filter District",
    "Accused name or ID...": "Accused name or ID...",
    "FIR / Case number...": "FIR / Case number...",
    "Select District...": "Select District...",
    "Search": "Search",
    "MOST CONNECTED CRIMINAL": "MOST CONNECTED CRIMINAL",
    "CONNECTED PS": "CONNECTED PS",
    "COMMUNITIES DETECTED": "COMMUNITIES DETECTED",
    "DENSITY RATIO": "DENSITY RATIO",
    "TOP REPEAT OFFENDERS (HIGH PRIORITY)": "TOP REPEAT OFFENDERS (HIGH PRIORITY)",
    "TOP CRIME GANGS": "TOP CRIME GANGS",
    "None Identified": "None Identified",
    "None": "None",
    "3 gang clusters": "3 gang clusters",
    "Target Configurator (Investigation Mode)": "Target Configurator (Investigation Mode)",
    "Min Link Weight": "Min Link Weight",
    "Close": "Close",
    "Investigate": "Investigate",
    "Gang": "Gang",
    "Leader": "Leader",
    "Members": "Members",
    "Recent Investigations": "Recent Investigations",
    "Cases": "Cases",
    "Associates": "Associates",
    "RISK SCORE": "RISK SCORE",

    // Role-based dashboard titles & subtitles
    "Investigator Command Center": "Investigator Command Center",
    "Active cases, local incident feeds, repeat offenders, and precinct map intelligence.": "Active cases, local incident feeds, repeat offenders, and precinct map intelligence.",
    "Senior Investigator Command Center": "Senior Investigator Command Center",
    "Cross-district tracking, gang networks, financial crime patterns, and tactical analytics.": "Cross-district tracking, gang networks, financial crime patterns, and tactical analytics.",
    "Crime Intelligence Analyst Hub": "Crime Intelligence Analyst Hub",
    "Spatial intelligence, predictive trends, hot-spot clusters, and demographic distributions.": "Spatial intelligence, predictive trends, hot-spot clusters, and demographic distributions.",
    "Precinct supervisor Dashboard": "Precinct supervisor Dashboard",
    "Resource allocation, personnel performance, compliance audit logs, and regional alerts.": "Resource allocation, personnel performance, compliance audit logs, and regional alerts.",
    "State Policy & Analytics Executive Dashboard": "State Policy & Analytics Executive Dashboard",
    "State-wide statistics, growth comparisons, year-over-year forecasting, and budget analytics.": "State-wide statistics, growth comparisons, year-over-year forecasting, and budget analytics.",
    "System Administration & Health Console": "System Administration & Health Console",
    "Full-spectrum visibility over users, roles, system health diagnostics, and audit logs.": "Full-spectrum visibility over users, roles, system health diagnostics, and audit logs.",

    // Dashboard specific labels
    "Workspace module": "Workspace module",
    "logged in as": "logged in as",
    "Officer": "Officer",
    "My Cases": "My Cases",
    "Assigned District": "Assigned District",
    "Recent FIRs": "Recent FIRs",
    "My Investigations": "My Investigations",
    "Repeat Offenders": "Repeat Offenders",
    "Crime Map": "Crime Map",
    "Gang Detection": "Gang Detection",
    "Financial Crime": "Financial Crime",
    "Pattern Intelligence": "Pattern Intelligence",
    "Crime Trends": "Crime Trends",
    "Forecasts": "Forecasts",
    "Heatmaps": "Heatmaps",
    "District Ranking": "District Ranking",
    "Crime Statistics": "Crime Statistics",
    "All Investigations": "All Investigations",
    "Officer Performance": "Officer Performance",
    "Audit Dashboard": "Audit Dashboard",
    "Network": "Network",
    "Reports": "Reports",
    "State Trends": "State Trends",
    "District Comparison": "District Comparison",
    "Crime Growth": "Crime Growth",
    "Budget Analytics": "Budget Analytics",
    "Everything": "Everything",
    "Users": "Users",
    "Roles": "Roles",
    "Permissions": "Permissions",
    "Audit": "Audit",
    "System Health": "System Health",

    // Panel strings
    "Crime-type trend — last 12 months": "Crime-type trend — last 12 months",
    "Monthly FIR counts by major crime categories": "Monthly FIR counts by major crime categories",
    "Operational case status": "Operational case status",
    "Active state-wide status distribution": "Active state-wide status distribution",
    "Top districts by case volume": "Top districts by case volume",
    "Active case volume comparison": "Active case volume comparison",
    "Intelligence anomalies & alerts": "Intelligence anomalies & alerts",
    "Early warnings generated by ML pattern models": "Early warnings generated by ML pattern models",
    "System compliance audit logs": "System compliance audit logs",
    "Recent administrative action audits": "Recent administrative action audits",
    "System audit trail is active and monitoring platform interactions.": "System audit trail is active and monitoring platform interactions.",
    "Audit Compliance Level 1": "Audit Compliance Level 1",
    "All data exports, role modifications, and PII views are registered.": "All data exports, role modifications, and PII views are registered.",
    "SECURE AUDIT CHANNEL": "SECURE AUDIT CHANNEL",
  },
  kn: {
    // Dashboard
    "Dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ನಿಯಂತ್ರಣ ಫಲಕ",

    // Settings
    "Settings": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು (Settings)",
    "Profile, security and notification preferences.": "ಬಳಕೆದಾರರ ಪ್ರೊಫೈಲ್, ಭದ್ರತೆ ಮತ್ತು ಅಧಿಸೂಚನೆಗಳ ಸೆಟ್ಟಿಂಗ್ ಆದ್ಯತೆಗಳು.",

    // Network
    "Criminal Intelligence Network": "ಅಪರಾಧ ಗುಪ್ತಚರ ಜಾಲ ವಿಶ್ಲೇಷಣೆ",
    "Workspace for co-offending links, Modularity gang clustering, and visual tracing.": "ಸಹ-ಅಪರಾಧ ಲಿಂಕ್‌ಗಳು, ಗ್ಯಾಂಗ್ ಕ್ಲಸ್ಟರಿಂಗ್ ಮತ್ತು ಜಾಲ ಪತ್ತೆಹಚ್ಚುವಿಕೆ ವಿಶ್ಲೇಷಣೆ.",

    // Financial
    "Financial Crime & Transaction Intelligence": "ಹಣಕಾಸು ಅಪರಾಧ ಮತ್ತು ವಹಿವಾಟು ಗುಪ್ತಚರ ವಿಶ್ಲೇಷಣೆ",
    "Discover money laundering networks, circular round-tripping, and shared account anomalies.": "ಹಣ ವರ್ಗಾವಣೆ ಜಾಲಗಳು, ಸುತ್ತೋಲೆಯ ವಹಿವಾಟುಗಳು ಮತ್ತು ಹಂಚಿಕೆಯ ಖಾತೆ ಅಸಂಗತತೆಗಳನ್ನು ಪತ್ತೆಹಚ್ಚಿ.",

    // Map
    "Geospatial Crime Hotspots": "ಭೂವ್ಯೋಮ ಅಪರಾಧ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು",
    "State-level spatial intelligence dashboard mapping offence hubs, station locations, and division metrics.": "ಅಪರಾಧ ಕೇಂದ್ರಗಳು, ಠಾಣೆಗಳ ಸ್ಥಳಗಳು ಮತ್ತು ವಿಭಾಗೀಯ ಮೆಟ್ರಿಕ್ಸ್‌ನ ರಾಜ್ಯ ಮಟ್ಟದ ನಕ್ಷೆ ವಿಶ್ಲೇಷಣೆ.",

    // Sociological
    "Sociological Insights & Crime Analytics": "ಸಾಮಾಜಿಕ ಒಳನೋಟಗಳು ಮತ್ತು ಅಪರಾಧ ವಿಶ್ಲೇಷಣೆ",
    "Examine regional crime occurrences filtered by demographic indicators, educational indexes, and poverty stats.": "ಜನಸंಖ್ಯಾ ಸೂಚಕಗಳು, ಶೈಕ್ಷಣಿಕ ಸೂಚ್ಯಂಕಗಳು ಮತ್ತು ಬಡತನದ ವಿವರಗಳೊಂದಿಗೆ ಪ್ರಾದೇಶಿಕ ಅಪರಾಧ ಘಟನೆಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ.",

    // Cases
    "Crime Case Search Registry": "ಅಪರಾಧ ಪ್ರಕರಣಗಳ ಹುಡುಕಾಟ ನೋಂದಾವಣೆ",
    "Query, filter, and inspect detailed First Information Reports (FIRs) across Karnataka SCRB database.": "ಕರ್ನಾಟಕ SCRB ಡೇಟಾಬೇಸ್‌ನಿಂದ ವಿವರವಾದ ಎಫ್‌ಐಆರ್ ದಾಖಲೆಗಳನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ ಮತ್ತು ಪರಿಶೀಲಿಸಿ.",

    // Offenders
    "Offender Registry & Profiles": "ಅಪರಾಧಿಗಳ ನೋಂದಾವಣೆ ಮತ್ತು ವಿವರಗಳು",
    "Manage repeat suspects, history sheeters, gang members, and profiles with detailed co-offending indices.": "ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು, ಹಿಸ್ಟರಿ ಶೀಟರ್‌ಗಳು, ಗ್ಯಾಂಗ್ ಸದಸ್ಯರು ಮತ್ತು ವಿವರವಾದ ಸಹ-ಅಪರಾಧ ಸೂಚ್ಯಂಕಗಳನ್ನು ನಿರ್ವಹಿಸಿ.",

    // Alerts
    "Intelligence Alerts & Pattern Warnings": "ಗುಪ್ತಚರ ಎಚ್ಚರಿಕೆಗಳು ಮತ್ತು ಅಪರಾಧ ಮಾದರಿಗಳ ಎಚ್ಚರಿಕೆ",
    "Automated triggers identifying serial offenders, crime waves, and anomalies in recent crime reports.": "ಸರಣಿ ಅಪರಾಧಿಗಳು, ಅಪರಾಧ ಅಲೆಗಳು ಮತ್ತು ಅಸಂಗತತೆಗಳನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗುರುತಿಸುವ ವ್ಯವಸ್ಥೆ.",

    // Audit
    "System Audit Log & Event Log": "ಸಿಸ್ಟಮ್ ಆಡಿಟ್ ಲಾಗ್ ಮತ್ತು ಘಟನೆಗಳ ದಾಖಲೆ",
    "Tamper-evident logs recording administrative operations, search queries, access controls, and logins.": "ಆಡಳಿತಾತ್ಮಕ ಕಾರ್ಯಾಚರಣೆಗಳು, ಹುಡುಕಾಟ ಪ್ರಶ್ನೆಗಳು ಮತ್ತು ಭದ್ರತಾ ಲಾಗ್‌ಗಳ ವಿವರಗಳು.",

    // Supervisor
    "Supervisor Control Center": "ಮೇಲ್ವಿಚಾರಕರ ನಿಯಂತ್ರಣ ಕೇಂದ್ರ",
    "Assign district permissions, review access requests, audit active investigators, and manage system status.": "ಜಿಲ್ಲೆಯ ಅನುಮತಿಗಳನ್ನು ನಿಯೋಜಿಸಿ, ಪ್ರವೇಶ ವಿನಂತಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಸಿಸ್ಟಮ್ ಸ್ಥಿತಿಯನ್ನು ನಿರ್ವಹಿಸಿ.",

    // Admin
    "Platform Administration Portal": "ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಆಡಳಿತ ಪೋರ್ಟಲ್",
    "System settings, backend service configurations, logs monitoring, and complete user profile management.": "Sistem ಸೆಟ್ಟಿಂಗ್‌ಗಳು, ಬ್ಯಾಕೆಂಡ್ ಸೇವೆಗಳು, ಲಾಗ್‌ಗಳ ಮಾನಿಟರಿಂಗ್ ಮತ್ತು ಬಳಕೆದಾರರ ವಿವರ ನಿರ್ವಹಣೆ.",

    // General UI labels
    "Search Accused": "ಅಪರಾಧಿಯನ್ನು ಹುಡುಕಿ",
    "Search FIR / Case No": "ಎಫ್‌ಐಆರ್ / ಪ್ರಕರಣ ಹುಡುಕಿ",
    "Filter District": "ಜಿಲ್ಲೆಯನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ",
    "Accused name or ID...": "ಅಪರಾಧಿಯ ಹೆಸರು ಅಥವಾ ಐಡಿ...",
    "FIR / Case number...": "ಎಫ್‌ಐಆರ್ ಅಥವಾ ಪ್ರಕರಣ ಸಂಖ್ಯೆ...",
    "Select District...": "ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ...",
    "Search": "ಹುಡುಕಿ",
    "MOST CONNECTED CRIMINAL": "ಹೆಚ್ಚು ಸಂಪರ್ಕ ಹೊಂದಿದ ಅಪರಾಧಿ",
    "CONNECTED PS": "ಸಂಪರ್ಕಿತ ಪೊಲೀಸ್ ಠಾಣೆ",
    "COMMUNITIES DETECTED": "ಪತ್ತೆಯಾದ ಅಪರಾಧಿ ಗುಂಪುಗಳು",
    "DENSITY RATIO": "ಸಾಂದ್ರತೆಯ ಅನುಪಾತ",
    "TOP REPEAT OFFENDERS (HIGH PRIORITY)": "ಟಾಪ್ ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು (ಉನ್ನತ ಆದ್ಯತೆ)",
    "TOP CRIME GANGS": "ಟಾಪ್ ಅಪರಾಧಿ ಗ್ಯಾಂಗ್‌ಗಳು",
    "None Identified": "ಯಾವುದೂ ಪತ್ತೆಯಾಗಿಲ್ಲ",
    "None": "ಯಾವುದೂ ಇಲ್ಲ",
    "3 gang clusters": "೩ ಗ್ಯಾಂಗ್ ಕ್ಲಸ್ಟರ್‌ಗಳು",
    "Target Configurator (Investigation Mode)": "ಟಾರ್ಗೆಟ್ ಕಾನ್ಫಿಗರೇಟರ್ (ತನಿಖಾ ಮೋಡ್)",
    "Min Link Weight": "ಕನಿಷ್ಠ ಲಿಂಕ್ ತೂಕ",
    "Close": "ಮುಚ್ಚಿ",
    "Investigate": "ತನಿಖೆ ನಡೆಸಿ",
    "Gang": "ಗ್ಯಾಂಗ್",
    "Leader": "ನಾಯಕ",
    "Members": "ಸದಸ್ಯರು",
    "Recent Investigations": "ಇತ್ತೀಚಿನ ತನಿಖೆಗಳು",
    "Cases": "ಪ್ರಕರಣಗಳು",
    "Associates": "ಸಹಚರರು",
    "RISK SCORE": "ಅಪಾಯದ ಅಂಕ",

    // Role-based dashboard titles & subtitles
    "Investigator Command Center": "ತನಿಖಾಧಿಕಾರಿ ನಿಯಂತ್ರಣ ಕೇಂದ್ರ",
    "Active cases, local incident feeds, repeat offenders, and precinct map intelligence.": "ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳು, ಸ್ಥಳೀಯ ಘಟನೆಗಳು, ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು ಮತ್ತು ನಕ್ಷೆ ಮಾಹಿತಿಯ ವಿಶ್ಲೇಷಣೆ.",
    "Senior Investigator Command Center": "ಹಿರಿಯ ತನಿಖಾಧಿಕಾರಿ ನಿಯಂತ್ರಣ ಕೇಂದ್ರ",
    "Cross-district tracking, gang networks, financial crime patterns, and tactical analytics.": "ಅಂತರ-ಜಿಲ್ಲಾ ಟ್ರ್ಯಾಕಿಂಗ್, ಗ್ಯಾಂಗ್ ಜಾಲಗಳು, ಹಣಕಾಸು ಅಪರಾಧ ಮತ್ತು ಯುದ್ಧತಂತ್ರದ ವಿಶ್ಲೇಷಣೆ.",
    "Crime Intelligence Analyst Hub": "ಅಪರಾಧ ಗುಪ್ತಚರ ವಿಶ್ಲೇಷಕರ ಹಬ್",
    "Spatial intelligence, predictive trends, hot-spot clusters, and demographic distributions.": "ಪ್ರಾದೇಶಿಕ ಬುದ್ಧಿಮತ್ತೆ, ಮುನ್ಸೂಚನೆಯ ಪ್ರವೃತ್ತಿಗಳು, ಹಾಟ್-ಸ್ಪಾಟ್ ಕ್ಲಸ್ಟರ್‌ಗಳು ಮತ್ತು ಜನಸಂಖ್ಯಾ ವಿವರಗಳು.",
    "Precinct supervisor Dashboard": "ಠಾಣಾ ಮೇಲ್ವಿಚಾರಕರ ನಿಯಂತ್ರಣ ಫಲಕ",
    "Resource allocation, personnel performance, compliance audit logs, and regional alerts.": "ಸಂಪನ್ಮೂಲ ಹಂಚಿಕೆ, ಸಿಬ್ಬಂದಿ ಕಾರ್ಯಕ್ಷಮತೆ, ಅನುಸರಣೆ ಆಡಿಟ್ ಲಾಗ್‌ಗಳು ಮತ್ತು ಪ್ರಾದೇಶಿಕ ಎಚ್ಚರಿಕೆಗಳು.",
    "State Policy & Analytics Executive Dashboard": "ರಾಜ್ಯ ನೀತಿ ಮತ್ತು ವಿಶ್ಲೇಷಣಾ ಕಾರ್ಯನಿರ್ವಾಹಕ ನಿಯಂತ್ರಣ ಫಲಕ",
    "State-wide statistics, growth comparisons, year-over-year forecasting, and budget analytics.": "ರಾಜ್ಯವ್ಯಾಪಿ ಅಂಕಿಅಂಶಗಳು, ಹೋಲಿಕೆಗಳು, ಮುನ್ಸೂಚನೆಗಳು ಮತ್ತು ಬಜೆಟ್ ವಿಶ್ಲೇಷಣೆ.",
    "System Administration & Health Console": "ಸಿಸ್ಟಮ್ ಆಡಳಿತ ಮತ್ತು ಆರೋಗ್ಯ ಕನ್ಸೋಲ್",
    "Full-spectrum visibility over users, roles, system health diagnostics, and audit logs.": "ಬಳಕೆದಾರರು, ಪಾತ್ರಗಳು, ಸಿಸ್ಟಮ್ ಆರೋಗ್ಯ ಮತ್ತು ಆಡಿಟ್ ಲಾಗ್‌ಗಳ ಸಂಪೂರ್ಣ ವಿವರಣೆ.",

    // Dashboard specific labels
    "Workspace module": "ಕಾರ್ಯಕ್ಷೇತ್ರದ ಮಾಡ್ಯೂಲ್",
    "logged in as": "ಲಾಗಿನ್ ಆಗಿರುವ ಬಳಕೆದಾರ",
    "Officer": "ಅಧಿಕಾರಿ",
    "My Cases": "ನನ್ನ ಪ್ರಕರಣಗಳು",
    "Assigned District": "ನಿಯೋಜಿತ ಜಿಲ್ಲೆ",
    "Recent FIRs": "ಇತ್ತೀಚಿನ ಎಫ್‌ಐಆರ್‌ಗಳು",
    "My Investigations": "ನನ್ನ ತನಿಖೆಗಳು",
    "Repeat Offenders": "ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು",
    "Crime Map": "ಅಪರಾಧ ನಕ್ಷೆ",
    "Gang Detection": "ಗ್ಯಾಂಗ್ ಪತ್ತೆಹಚ್ಚುವಿಕೆ",
    "Financial Crime": "ಹಣಕಾಸು ಅಪರಾಧ",
    "Pattern Intelligence": "ಮಾದರಿ ಗುಪ್ತಚರ",
    "Crime Trends": "ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು",
    "Forecasts": "ಮುನ್ಸೂಚನೆಗಳು",
    "Heatmaps": "ಶಾಖದ ನಕ್ಷೆಗಳು",
    "District Ranking": "ಜಿಲ್ಲಾ ಶ್ರೇಯಾಂಕ",
    "Crime Statistics": "ಅಪರಾಧ ಅಂಕಿಅಂಶಗಳು",
    "All Investigations": "ಎಲ್ಲಾ ತನಿಖೆಗಳು",
    "Officer Performance": "ಅಧಿಕಾರಿಯ ಕಾರ್ಯಕ್ಷಮತೆ",
    "Audit Dashboard": "ಆಡಿಟ್ ನಿಯಂತ್ರಣ ಫಲಕ",
    "Network": "ಜಾಲ ವಿಶ್ಲೇಷಣೆ",
    "Reports": "ವರದಿಗಳು",
    "State Trends": "ರಾಜ್ಯದ ಪ್ರವೃತ್ತಿಗಳು",
    "District Comparison": "ಜಿಲ್ಲಾ ಹೋಲಿಕೆ",
    "Crime Growth": "ಅಪರಾಧದ ಬೆಳವಣಿಗೆ",
    "Budget Analytics": "ಬಜೆಟ್ ವಿಶ್ಲೇಷಣೆ",
    "Everything": "ಎಲ್ಲವೂ",
    "Users": "ಬಳಕೆದಾರರು",
    "Roles": "ಪಾತ್ರಗಳು",
    "Permissions": "ಅನುಮತಿಗಳು",
    "Audit": "ಆಡಿಟ್",
    "System Health": "ಸಿಸ್ಟಮ್ ಆರೋಗ್ಯ",

    // Panel strings
    "Crime-type trend — last 12 months": "ಅಪರಾಧ ಪ್ರಕಾರದ ಪ್ರವೃತ್ತಿ — ಕಳೆದ 12 ತಿಂಗಳು",
    "Monthly FIR counts by major crime categories": "ಪ್ರಮುಖ ಅಪರಾಧ ಪ್ರಕಾರಗಳ ಮಾಸಿಕ ಎಫ್‌ಐಆರ್ ಸಂಖ್ಯೆ",
    "Operational case status": "ಕಾರ್ಯಾಚರಣೆಯ ಪ್ರಕರಣದ ಸ್ಥಿತಿ",
    "Active state-wide status distribution": "ರಾಜ್ಯವ್ಯಾಪಿ ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳ ಸ್ಥಿತಿ",
    "Top districts by case volume": "ಅತಿ ಹೆಚ್ಚು ಪ್ರಕರಣಗಳನ್ನು ಹೊಂದಿರುವ ಜಿಲ್ಲೆಗಳು",
    "Active case volume comparison": "ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳ ಸಂಖ್ಯೆಯ ಹೋಲಿಕೆ",
    "Intelligence anomalies & alerts": "ಗುಪ್ತಚರ ಅಸಂಗತತೆಗಳು ಮತ್ತು ಎಚ್ಚರಿಕೆಗಳು",
    "Early warnings generated by ML pattern models": "ML ಮಾದರಿಗಳಿಂದ ರಚಿಸಲಾದ ಆರಂಭಿಕ ಎಚ್ಚರಿಕೆಗಳು",
    "System compliance audit logs": "ಸಿಸ್ಟಮ್ ಅನುಸರಣೆ ಆಡಿಟ್ ಲಾಗ್‌ಗಳು",
    "Recent administrative action audits": "ಇತ್ತೀಚಿನ ಆಡಳಿತಾತ್ಮಕ ಆಡಿಟ್ ಲಾಗ್‌ಗಳು",
    "System audit trail is active and monitoring platform interactions.": "ಸಿಸ್ಟಮ್ ಆಡಿಟ್ ಸಕ್ರಿಯವಾಗಿದೆ ಮತ್ತು ಪ್ಲಾಟ್‌ಫಾರ್ಮ್ ಸಂವಹನಗಳನ್ನು ಮೇಲ್ವಿಚಾರಣೆ ಮಾಡುತ್ತಿದೆ.",
    "Audit Compliance Level 1": "ಆಡಿಟ್ ಅನುಸರಣೆ ಮಟ್ಟ 1",
    "All data exports, role modifications, and PII views are registered.": "ಎಲ್ಲಾ ಡೇಟಾ ರಫ್ತುಗಳು, ಪಾತ್ರಗಳ ಬದಲಾವಣೆಗಳು ಮತ್ತು ವೈಯಕ್ತಿಕ ವಿವರ ವೀಕ್ಷಣೆಗಳನ್ನು ನೋಂದಾಯಿಸಲಾಗಿದೆ.",
    "SECURE AUDIT CHANNEL": "ಸುರಕ್ಷಿತ ಆಡಿಟ್ ಚಾನಲ್",
  }
};

export function useTranslateHeader() {
  const lang = usePrefs((s) => s.lang);
  return (text: string) => {
    return headerTranslations[lang]?.[text] ?? text;
  };
}
