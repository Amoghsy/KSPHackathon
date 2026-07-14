// src/config/constants.ts — Shared static constants for the frontend application.
// Extracted from mock files to serve as permanent filter/option configurations.

export const DISTRICTS = [
  "Bengaluru Urban",
  "Bengaluru Rural",
  "Mysuru",
  "Mangaluru",
  "Belagavi",
  "Kalaburagi",
  "Hubballi-Dharwad",
  "Tumakuru",
  "Shivamogga",
  "Ballari",
  "Vijayapura",
  "Udupi",
  "Chitradurga",
  "Hassan",
] as const;

export const CRIME_HEADS = [
  "Theft",
  "Robbery",
  "Cyber Fraud",
  "Murder",
  "Assault",
  "Kidnapping",
  "Vehicle Theft",
  "Drug Trafficking",
  "Financial Fraud",
  "Human Trafficking",
] as const;

export const STATUSES = [
  "Under Investigation",
  "Charge Sheeted",
  "Closed",
  "Undetected",
] as const;

export const GRAVITY = ["Low", "Medium", "High", "Grievous"] as const;

export type ForecastCrime = "Robbery" | "Theft" | "Cybercrime" | "Assault";
