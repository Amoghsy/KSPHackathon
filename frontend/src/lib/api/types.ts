// src/lib/api/types.ts — Shared TypeScript types matching the FastAPI response schemas.

// ─── Auth ───────────────────────────────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

/** Step 1 response — contains OTP challenge, NOT a token */
export interface LoginOTPResponse {
  otp_required: boolean;
  challenge_id: string;
  expires_in: number;
  message: string;
}

/** Step 2 response — full session response after OTP verification */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  session_id: string;
  username: string;
  role: string;
  refresh_token?: string;
  user: {
    id: string;
    name: string;
    username: string;
    role: string;
    badgeNo: string;
    station: string;
  };
}

/** Active device session */
export interface DeviceSession {
  session_id: string;
  device_name: string;
  browser: string;
  os: string;
  device_type: string;
  ip_address: string;
  created_at: string;
  last_activity_at: string;
  is_current: boolean;
}

// ─── Chat ───────────────────────────────────────────────────────────────────

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
  response_language?: string | null;
}

export interface ChatRow {
  [key: string]: string | number | boolean | null;
}

export interface ChatResponse {
  status: "success" | "error";
  question?: string;
  generated_sql?: string;
  rows?: ChatRow[];
  columns?: string[];
  row_count?: number;
  execution_time_ms?: number;
  confidence?: number;
  summary?: string;
  agent?: string;
  request_id?: string;
  conversation_id?: string;
  resolved_question?: string;
  error?: string;
  error_type?: string;
  explain?: {
    sql?: string;
    sources?: string;
    algorithms?: string;
    confidence?: number;
    execution_time?: string;
    summary?: string;
  };
}

// ─── Conversations ──────────────────────────────────────────────────────────

export interface ResolvedEntities {
  last_case?: string | null;
  last_accused?: string | null;
  last_victim?: string | null;
  last_station?: string | null;
  last_district?: string | null;
  last_crime_type?: string | null;
  last_date_range?: string | null;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  generated_sql?: string | null;
  resolved_entities?: ResolvedEntities | null;
}

export interface ConversationSession {
  conversation_id: string;
  user_id?: number | null;
  created_at: number;
  updated_at: number;
  last_question?: string | null;
  last_generated_sql?: string | null;
  conversation_history: ConversationMessage[];
  resolved_entities: ResolvedEntities;
  preferred_language: string;
}

// ─── Dashboard ──────────────────────────────────────────────────────────────

export interface DashboardKPI {
  label: string;
  value: number;
  delta?: number;
}

export interface DashboardMonthlyTrend {
  month: string;
  [crime: string]: number | string;
}

export interface DashboardDistrictCount {
  district: string;
  cases: number;
}

export interface DashboardStatusBreakdown {
  name: string;
  value: number;
}

export interface DashboardResponse {
  kpis: DashboardKPI[];
  monthlyTrend: DashboardMonthlyTrend[];
  districtCounts: DashboardDistrictCount[];
  statusBreakdown: DashboardStatusBreakdown[];
}

// ─── Cases / FIRs ───────────────────────────────────────────────────────────

export interface Case {
  case_master_id: number;
  crime_no: string;
  case_no?: string | null;
  crime_registered_date: string;
  police_station_id?: number | null;
  incident_from_date?: string | null;
  incident_to_date?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  brief_facts?: string | null;
}

export interface CasesResponse {
  cases: Case[];
  count: number;
}

// ─── Accused / Offenders ────────────────────────────────────────────────────

export interface Accused {
  accused_master_id: number;
  case_master_id?: number | null;
  accused_name?: string | null;
  age_year?: number | null;
  gender_id?: string | null;
  person_id?: number | null;
}

export interface AccusedResponse {
  accused: Accused[];
  count: number;
}

// ─── Administrative Users ───────────────────────────────────────────────────

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  full_name?: string;
  employee_id?: string;
  account_status: string;
}

export interface UserCreatePayload {
  username: string;
  email: string;
  employee_id: string;
  role: string;
  full_name?: string;
  password?: string;
  districts?: string;
}

// ─── District Assignments ────────────────────────────────────────────────────

export interface DistrictAssignmentRecord {
  id: number;
  user_id: number;
  username: string;
  role: string;
  district: string;
  assigned_at: string;
}
