import React, { useEffect, useRef } from "react";
import { usePrefs } from "@/stores/prefs";

const domDictionary: Record<string, string> = {
  // Navigation & Headers
  "Chat Assistant": "ಚಾಟ್ ಸಹಾಯಕ",
  "Dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
  "Criminal Network": "ಅಪರಾಧಿ ಜಾಲ",
  "Financial Crime": "ಹಣಕಾಸು ಅಪರಾಧ",
  "Crime Map": "ಅಪರಾಧ ನಕ್ಷೆ",
  "Sociological Insights": "ಸಾಮಾಜಿಕ ಒಳನೋಟಗಳು",
  "Case Search": "ಪ್ರಕರಣ ಹುಡುಕಾಟ",
  "Offender Profiles": "ಅಪರಾಧಿ ವಿವರ",
  "Alerts": "ಎಚ್ಚರಿಕೆಗಳು",
  "Audit Log": "ಆಡಿಟ್ ಲಾಗ್",
  "Settings": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
  "Admin Console": "ನಿರ್ವಾಹಕ ಕನ್ಸೋಲ್",
  "Supervisor Panel": "ಮೇಲ್ವಿಚಾರಕ ಫಲಕ",
  "Collapse": "ಮಡಚು",

  // Settings page
  "Profile": "ಪ್ರೊಫೈಲ್",
  "Name": "ಹೆಸರು",
  "Role": "ಪಾತ್ರ",
  "Badge No.": "ಬ್ಯಾಡ್ಜ್ ಸಂಖ್ಯೆ",
  "Station": "ಠಾಣೆ",
  "Preferences": "ಆದ್ಯತೆಗಳು",
  "Display Language": "ಪ್ರದರ್ಶನ ಭಾಷೆ",
  "Chatbot Language": "ಚಾಟ್‌ಬಾಟ್ ಭಾಷೆ",
  "Dark mode": "ಕತ್ತಲೆ ಮೋಡ್",
  "Critical alert notifications": "ನಿರ್ಣಾಯಕ ಎಚ್ಚರಿಕೆ ಅಧಿಸೂಚನೆಗಳು",
  "Active Sessions": "ಸಕ್ರಿಯ ಸೆಷನ್‌ಗಳು",
  "Auto Detect": "ಸ್ವಯಂ ಪತ್ತೆ",
  "English": "ಇಂಗ್ಲಿಷ್",
  "ಕನ್ನಡ": "ಕನ್ನಡ",

  // Search forms
  "Search Accused": "ಅಪರಾಧಿಯನ್ನು ಹುಡುಕಿ",
  "Search FIR / Case No": "ಎಫ್‌ಐಆರ್ / ಪ್ರಕರಣ ಹುಡುಕಿ",
  "Filter District": "ಜಿಲ್ಲೆಯನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ",
  "Accused name or ID...": "ಅಪರಾಧಿಯ ಹೆಸರು ಅಥವಾ ಐಡಿ...",
  "FIR / Case number...": "ಎಫ್‌ಐಆರ್ ಅಥವಾ ಪ್ರಕರಣ ಸಂಖ್ಯೆ...",
  "Select District...": "ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ...",
  "Search": "ಹುಡುಕಿ",
  "Clear Filters": "ಫಿಲ್ಟರ್‌ಗಳನ್ನು ತೆರವುಗೊಳಿಸಿ",
  "Filter by District": "ಜಿಲ್ಲೆಯ ಮೂಲಕ ಫಿಲ್ಟರ್ ಮಾಡಿ",
  "Filter by Crime Type": "ಅಪರಾಧ ಪ್ರಕಾರದ ಮೂಲಕ ಫಿಲ್ಟರ್ ಮಾಡಿ",
  "Filter by Year": "ವರ್ಷದ ಮೂಲಕ ಫಿಲ್ಟರ್ ಮಾಡಿ",
  "Filter by Status": "ಸ್ಥಿತಿಯ ಮೂಲಕ ಫಿಲ್ಟರ್ ಮಾಡಿ",
  "Search FIR No / Accused Name...": "ಎಫ್‌ಐಆರ್ ಸಂಖ್ಯೆ / ಅಪರಾಧಿಯ ಹೆಸರು ಹುಡುಕಿ...",

  // Buttons & Actions
  "Investigate": "ತನಿಖೆ ನಡೆಸಿ",
  "Close": "ಮುಚ್ಚಿ",
  "Action": "ಕಾರ್ಯ",
  "View Details": "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
  "View Profile": "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
  "Add Offender Profile": "ಅಪರಾಧಿಯ ವಿವರವನ್ನು ಸೇರಿಸಿ",
  "Register New User": "ಹೊಸ ಬಳಕೆದಾರರನ್ನು ನೋಂದಾಯಿಸಿ",
  "Create New Alert Rule": "ಹೊಸ ಎಚ್ಚರಿಕೆ ನಿಯಮವನ್ನು ರಚಿಸಿ",

  // Table & Card Headers
  "MOST CONNECTED CRIMINAL": "ಹೆಚ್ಚು ಸಂಪರ್ಕ ಹೊಂದಿದ ಅಪರಾಧಿ",
  "CONNECTED PS": "ಸಂಪರ್ಕಿತ ಪೊಲೀಸ್ ಠಾಣೆ",
  "COMMUNITIES DETECTED": "ಪತ್ತೆಯಾದ ಅಪರಾಧಿ ಗುಂಪುಗಳು",
  "DENSITY RATIO": "ಸಾಂದ್ರತೆಯ ಅನುಪಾತ",
  "TOP REPEAT OFFENDERS (HIGH PRIORITY)": "ಟಾಪ್ ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು (ಉನ್ನತ ಆದ್ಯತೆ)",
  "TOP CRIME GANGS": "ಟಾಪ್ ಅಪರಾಧಿ ಗ್ಯಾಂಗ್‌ಗಳು",
  "None Identified": "ಯಾವುದೂ ಪತ್ತೆಯಾಗಿಲ್ಲ",
  "None": "ಯಾವುದೂ ಇಲ್ಲ",
  "Leader": "ನಾಯಕ",
  "Members": "ಸದಸ್ಯರು",
  "Recent Investigations": "ಇತ್ತೀಚಿನ ತನಿಖೆಗಳು",
  "Cases": "ಪ್ರಕರಣಗಳು",
  "Associates": "ಸಹಚರರು",
  "RISK SCORE": "ಅಪಾಯದ ಅಂಕ",
  "Total Cases Found": "ಒಟ್ಟು ಪ್ರಕರಣಗಳು ಪತ್ತೆಯಾಗಿವೆ",
  "Accused": "ಅಪರಾಧಿ",
  "Date": "ದಿನಾಂಕ",
  "Police Station": "ಪೊಲೀಸ್ ಠಾಣೆ",
  "Crime Type": "ಅಪರಾಧ ಪ್ರಕಾರ",
  "Status": "ಸ್ಥಿತಿ",
  "Offender Name": "ಅಪರಾಧಿಯ ಹೆಸರು",
  "Primary Crime Type": "ಪ್ರಾಥಮಿಕ ಅಪರಾಧ ಪ್ರಕಾರ",
  "Risk Level": "ಅಪಾಯದ ಮಟ್ಟ",
  "Co-Offending Count": "ಸಹ-ಅಪರಾಧ ಸಂಖ್ಯೆ",
  "Active Alert Rules": "ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆ ನಿಯಮಗಳು",
  "Triggered Warnings Feed": "ಪ್ರಚೋದಿತ ಎಚ್ಚರಿಕೆಗಳು",
  "Severity": "ತೀವ್ರತೆ",
  "Triggered Time": "ಪ್ರಚೋದಿತ ಸಮಯ",
  "Area": "ಪ್ರದೇಶ",
  "Rule Details": "ನಿಯಮದ ವಿವರಗಳು",
  "Triggered Count": "ಪ್ರಚೋದಿತ ಸಂಖ್ಯೆ",
  "Timestamp": "ಸಮಯದ ಮುದ್ರೆ",
  "Operator": "ನಿರ್ವಾಹಕರು",
  "Operation Type": "ಕಾರ್ಯಾಚರಣೆಯ ಪ್ರಕಾರ",
  "IP Address": "ಐಪಿ ವಿಳಾಸ",
  "Details": "ವಿವರಗಳು",
  "User Accounts": "ಬಳಕೆದಾರರ ಖಾತೆಗಳು",
  "Backend Services Status": "ಬ್ಯಾಕೆಂಡ್ ಸೇವೆಗಳ ಸ್ಥಿತಿ",
  "Logs Monitor": "ಲಾಗ್‌ಗಳ ಮಾನಿಟರ್",
  "Database Status": "ಡೇಟಾಬೇಸ್ ಸ್ಥಿತಿ",
  "Redis Status": "ರೆಡಿಸ್ ಸ್ಥಿತಿ",
  "API Server Status": "ಎಪಿಐ ಸರ್ವರ್ ಸ್ಥಿತಿ",
  "District Allocation": "ಜಿಲ್ಲಾ ಹಂಚಿಕೆ",
  "Access Requests": "ಪ್ರವೇಶ ವಿನಂತಿಗಳು",
  "Active Investigators": "ಸಕ್ರಿಯ ತನಿಖಾಧಿಕಾರಿಗಳು",
  "System Configurations": "ಸಿಸ್ಟಮ್ ಕಾನ್ಫಿಗರೇಶನ್‌ಗಳು",
  "Review Access Requests": "ಪ್ರವೇಶ ವಿನಂತಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ",
  "Configure Precinct Permissions": "ಠಾಣೆಯ ಅನುಮತಿಗಳನ್ನು ಕಾನ್ಫಿಗರ್ ಮಾಡಿ",

  // GIS Crime Map Page
  "Karnataka Crime Intelligence GIS": "ಕರ್ನಾಟಕ ಅಪರಾಧ ಗುಪ್ತಚರ ಜಿಐಎಸ್",
  "Dedicated state-level crime mapping and spatial intelligence portal.": "ರಾಜ್ಯ ಮಟ್ಟದ ಅಪರಾಧ ನಕ್ಷೆ ಮತ್ತು ಪ್ರಾದೇಶಿಕ ಮಾಹಿತಿ ಪೋರ್ಟಲ್.",
  "GIS Data": "ಜಿಐಎಸ್ ಡೇಟಾ",
  "Map Layers": "ನಕ್ಷೆಯ ಪದರಗಳು",
  "GIS FILTERS": "ಜಿಐಎಸ್ ಫಿಲ್ಟರ್‌ಗಳು",
  "Time Range": "ಸಮಯದ ವ್ಯಾಪ್ತಿ",
  "All Time": "ಎಲ್ಲಾ ಸಮಯ",
  "District Focus": "ಜಿಲ್ಲಾ ಕೇಂದ್ರ",
  "All districts": "ಎಲ್ಲಾ ಜಿಲ್ಲೆಗಳು",
  "Severity Gravity": "ಗಂಭೀರತೆಯ ಮಟ್ಟ",
  "All": "ಎಲ್ಲಾ",
  "Case Status": "ಪ್ರಕರಣದ ಸ್ಥಿತಿ",
  "All Statuses": "ಎಲ್ಲಾ ಸ್ಥಿತಿಗಳು",
  "Loading map data...": "ನಕ್ಷೆ ಡೇಟಾವನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",
  "Applying filters to all GIS layers": "ಎಲ್ಲಾ ಜಿಐಎಸ್ ಪದರಗಳಿಗೆ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಅನ್ವಯಿಸಲಾಗುತ್ತಿದೆ",
  "GIS QUERY TELEMETRY": "ಜಿಐಎಸ್ ಪ್ರಶ್ನೆ ಟೆಲಿಮೆಟ್ರಿ",
  "Crime Type:": "ಅಪರಾಧ ಪ್ರಕಾರ:",
  "Time Range:": "ಸಮಯದ ವ್ಯಾಪ್ತಿ:",
  "District:": "ಜಿಲ್ಲೆ:",
  "Severity:": "ಗಂಭೀರತೆ:",
  "Status:": "ಸ್ಥಿತಿ:",
  "ALL": "ಎಲ್ಲಾ",
  "ALL Time": "ಎಲ್ಲಾ ಸಮಯ",
  "PLOTTED DATASET STATISTICS": "ಚಿತ್ರಿಸಿದ ಡೇಟಾಸೆಟ್ ಅಂಕಿಅಂಶಗಳು",
  "Heat Points": "ಶಾಖ ಬಿಂದುಗಳು",
  "Stations": "ಠಾಣೆಗಳು",
  "Hotspots": "ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು",
  "SEVERITY MARKER SCALE": "ಗಂಭೀರತೆಯ ಗುರುತು ಪ್ರಮಾಣ",
  "Low": "ಕಡಿಮೆ",
  "Medium": "ಮಧ್ಯಮ",
  "High": "ಹೆಚ್ಚು",
  "Critical": "ನಿರ್ಣಾಯಕ",
  "All types": "ಎಲ್ಲಾ ಪ್ರಕಾರಗಳು",
  "Loading": "ಲೋಡ್ ಆಗುತ್ತಿದೆ",

  // Sociological Crime Insights Page
  "Sociological Crime Insights": "ಸಾಮಾಜಿಕ ಅಪರಾಧ ಒಳನೋಟಗಳು",
  "Demographic and socio-economic patterns across Karnataka crime records.": "ಕರ್ನಾಟಕದ ಅಪರಾಧ ದಾಖಲೆಗಳಾದ್ಯಂತ ಜನಸಂಖ್ಯಾ ಮತ್ತು ಸಾಮಾಜಿಕ-ಆರ್ಥಿಕ ಮಾದರಿಗಳು.",
  "Live demographic insights compiled from active criminal registries.": "ಸಕ್ರಿಯ ಅಪರಾಧ ರೆಜಿಸ್ಟ್ರಿಗಳಿಂದ ಸಂಗ್ರಹಿಸಲಾದ ಲೈವ್ ಜನಸಂಖ್ಯಾ ಒಳನೋಟಗಳು.",
  "Crime count by age band": "ವಯಸ್ಸಿನ ಗುಂಪಿನ ಆಧಾರದ ಮೇಲೆ ಅಪರಾಧದ ಸಂಖ್ಯೆ",
  "Accused age bands, rolling 12-month window": "ಆರೋಪಿಗಳ ವಯಸ್ಸಿನ ಗುಂಪುಗಳು, 12 ತಿಂಗಳ ಕಾಲಾವಧಿ",
  "Crime count by gender": "ಲಿಂಗದ ಆಧಾರದ ಮೇಲೆ ಅಪರಾಧದ ಸಂಖ್ಯೆ",
  "Accused gender distribution": "ಆರೋಪಿಗಳ ಲಿಂಗ ವಿತರಣೆ",
  "Female": "ಮಹಿಳೆ",
  "Male": "ಪುರುಷ",
  "Crime rate vs. socio-economic index": "ಅಪರಾಧ ದರ ಮತ್ತು ಸಾಮಾಜಿಕ-ಆರ್ಥಿಕ ಸೂಚ್ಯಂಕ",

  // Early Warning Center (Alerts Page)
  "Early Warning Center": "ಮುನ್ನೆಚ್ಚರಿಕೆ ಕೇಂದ್ರ",
  "AI-generated alerts from anomaly detection across FIR feeds.": "ಎಫ್‌ಐಆರ್ ಫೀಡ್‌ಗಳಾದ್ಯಂತ ಅಸಂಗತತೆ ಪತ್ತೆಯಿಂದ AI-ರಚಿತ ಎಚ್ಚರಿಕೆಗಳು.",
  "Warning": "ಎಚ್ಚರಿಕೆ",
  "Info": "ಮಾಹಿತಿ",
  "Advanced Monthly Crime Forecasting (ARIMA)": "ಸುಧಾರಿತ ಮಾಸಿಕ ಅಪರಾಧ ಮುನ್ಸೂಚನೆ (ARIMA)",
  "Multi-period monthly projection using AutoRegressive Integrated Moving Average (ARIMA) models.": "ಆಟೋರೆಗ್ರೆಸಿವ್ ಇಂಟಿಗ್ರೇಟೆಡ್ ಮೂವಿಂಗ್ ಆವರೇಜ್ (ARIMA) ಮಾದರಿಗಳನ್ನು ಬಳಸಿಕೊಂಡು ಮಾಸಿಕ ಯೋಜನೆ.",
  "District": "ಜಿಲ್ಲೆ",
  "Horizon": "ಮುನ್ನೋಟದ ಅವಧಿ",
  "3 Months": "೩ ತಿಂಗಳುಗಳು",
  "ARIMA/WMA Forecast": "ARIMA/WMA ಮುನ್ಸೂಚನೆ",
  "Confidence Interval": "ನಂಬಿಕೆಯ ಮಧ್ಯಂತರ",
  "Historical Trend": "ಐತಿಹಾಸಿಕ ಪ್ರವೃತ್ತಿ",
  "Forecasting Algorithm:": "ಮುನ್ಸೂಚನೆ ಅಲ್ಗಾರಿದಮ್:",
  "Model Confidence Rating:": "ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ ರೇಟಿಂಗ್:",
  "Forecast — next 4 weeks": "ಮುನ್ಸೂಚನೆ — ಮುಂದಿನ 4 ವಾರಗಳು",
  "Actual counts plus 95% forecast confidence interval.": "ನಿಜವಾದ ಸಂಖ್ಯೆಗಳು ಮತ್ತು 95% ಮುನ್ಸೂಚನೆ ನಂಬಿಕೆಯ ಮಧ್ಯಂತರ.",

  // Supervisor Security Panel Page
  "Supervisor Security Panel": "ಮೇಲ್ವಿಚಾರಕ ಭದ್ರತಾ ಫಲಕ",
  "Review temporary investigator requests and manage district containment assignments.": "ತಾತ್ಕಾಲಿಕ ತನಿಖಾಧಿಕಾರಿ ವಿನಂತಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಜಿಲ್ಲಾ ಹಂಚಿಕೆಗಳನ್ನು ನಿರ್ವಹಿಸಿ.",
  "Refresh": "ರಿಫ್ರೆಶ್",
  "Assign District": "ಜಿಲ್ಲೆಯನ್ನು ನಿಯೋಜಿಸಿ",
  "Pending Access Requests (0)": "ಬಾಕಿ ಇರುವ ಪ್ರವೇಶ ವಿನಂತಿಗಳು (೦)",
  "Permanent District Assignments (0)": "ಖಾಯಂ ಜಿಲ್ಲಾ ನಿಯೋಜನೆಗಳು (೦)",
  "Pending Requests Drawer": "ಬಾಕಿ ಇರುವ ವಿನಂತಿಗಳ ಡ್ರಾಯರ್",
  "Evaluating active ABAC conditions": "ಸಕ್ರಿಯ ABAC ಪರಿಸ್ಥಿತಿಗಳ ಮೌಲ್ಯಮಾಪನ",
  "No pending temporary access requests.": "ಯಾವುದೇ ಬಾಕಿ ಇರುವ ತಾತ್ಕಾಲಿಕ ಪ್ರವೇಶ ವಿನಂತಿಗಳಿಲ್ಲ.",
  
  // Settings details
  "Security & Access Keys": "ಭದ್ರತೆ ಮತ್ತು ಪ್ರವೇಶ ಕೀಗಳು",
  "Language & Regional": "ಭಾಷೆ ಮತ್ತು ಪ್ರಾದೇಶಿಕ",
  "Enable system-wide dark UI theme": "ಸಿಸ್ಟಮ್-ವ್ಯಾಪಿ ಡಾರ್ಕ್ ಯುಐ ಥೀಮ್ ಸಕ್ರಿಯಗೊಳಿಸಿ",
  "Critical Alerts": "ನಿರ್ಣಾಯಕ ಎಚ್ಚರಿಕೆಗಳು",
  "Receive immediate notifications for high-priority incidents": "ಉನ್ನತ ಆದ್ಯತೆಯ ಘಟನೆಗಳಿಗೆ ತಕ್ಷಣದ ಅಧಿಸೂಚನೆಗಳನ್ನು ಸ್ವೀಕರಿಸಿ",
  "Disable OTP Requirement": "ಒಟಿಪಿ ಅವಶ್ಯಕತೆಯನ್ನು ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ",
  "OTP verification will not be requested for this account.": "ಈ ಖಾತೆಗೆ ಒಟಿಪಿ ಪರಿಶೀಲನೆಯನ್ನು ವಿನಂತಿಸಲಾಗುವುದಿಲ್ಲ."
};

export const DOMTranslateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const lang = usePrefs((s) => s.lang);
  const containerRef = useRef<HTMLDivElement>(null);
  const originalTexts = useRef(new WeakMap<Node, string>());
  const originalPlaceholders = useRef(new WeakMap<Element, string>());

  useEffect(() => {
    const translate = () => {
      if (!containerRef.current) return;
      
      const walk = (node: Node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.nodeValue?.trim() || "";
          if (lang === "kn") {
            if (text && domDictionary[text]) {
              if (!originalTexts.current.has(node)) {
                originalTexts.current.set(node, node.nodeValue || "");
              }
              node.nodeValue = domDictionary[text];
            }
          } else {
            if (originalTexts.current.has(node)) {
              node.nodeValue = originalTexts.current.get(node) || "";
            }
          }
        } else {
          if (node instanceof Element) {
            const ph = node.getAttribute("placeholder");
            if (lang === "kn") {
              if (ph && domDictionary[ph]) {
                if (!originalPlaceholders.current.has(node)) {
                  originalPlaceholders.current.set(node, ph);
                }
                node.setAttribute("placeholder", domDictionary[ph]);
              }
            } else {
              if (originalPlaceholders.current.has(node)) {
                node.setAttribute("placeholder", originalPlaceholders.current.get(node) || "");
              }
            }
          }
          for (let i = 0; i < node.childNodes.length; i++) {
            walk(node.childNodes[i]);
          }
        }
      };

      walk(containerRef.current);
    };

    translate();

    if (lang === "kn") {
      const observer = new MutationObserver(() => {
        observer.disconnect();
        translate();
        if (containerRef.current) {
          observer.observe(containerRef.current, {
            childList: true,
            subtree: true,
            characterData: true,
          });
        }
      });

      if (containerRef.current) {
        observer.observe(containerRef.current, {
          childList: true,
          subtree: true,
          characterData: true,
        });
      }

      return () => observer.disconnect();
    }
  }, [lang]);

  return <div ref={containerRef} className="contents">{children}</div>;
};
