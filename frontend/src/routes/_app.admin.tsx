import { createFileRoute, useNavigate, redirect } from "@tanstack/react-router";
import { requiredRoleLabel, PERMISSIONS } from "@/lib/rbac";
import { useEffect, useState } from "react";
import { useAuthStore, type Role } from "@/stores/auth";
import { PageHeader } from "@/components/app/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  ShieldAlert,
  UserPlus,
  Trash2,
  Shield,
  Users,
  Lock,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Activity,
  MapPin,
  X,
  Plus,
  Key,
  Database,
  Cpu,
  BarChart3,
  Clock,
  TrendingUp,
  Monitor,
  Smartphone,
  Tablet,
  Wifi,
  Globe,
  RefreshCw,
} from "lucide-react";
import {
  listUsers,
  createUser,
  deleteUser,
  getAdminStats,
  listSupervisorAssignments,
  assignSupervisorDistrict,
  revokeSupervisorAssignment,
} from "@/lib/api/services";
import { apiGet, apiDelete, apiPost, apiPatch } from "@/lib/api/axios";
import type { UserResponse, DistrictAssignmentRecord } from "@/lib/api/types";

export const Route = createFileRoute("/_app/admin")({
  head: () => ({ meta: [{ title: "Admin Console — Crime Intelligence Assistant" }] }),
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    if (user?.role !== "ADMINISTRATOR") {
      throw redirect({
        to: "/access-restricted",
        search: {
          module: "Admin Console",
          required: requiredRoleLabel([PERMISSIONS.MANAGE_USERS]),
          from: "/admin",
        },
      });
    }
  },
  component: AdminPage,
});

const ROLES: Role[] = ["INVESTIGATOR", "ANALYST", "SUPERVISOR", "POLICY_MAKER", "ADMINISTRATOR"];

const ROLE_META: Record<string, { color: string; label: string }> = {
  ADMINISTRATOR:      { color: "bg-primary/15 text-primary border-primary/30", label: "Administrator" },
  SUPERVISOR:         { color: "bg-amber-500/15 text-amber-400 border-amber-400/30", label: "Supervisor" },
  SENIOR_INVESTIGATOR:{ color: "bg-chart-2/15 text-chart-2 border-chart-2/30", label: "Sr. Investigator" },
  INVESTIGATOR:       { color: "bg-success/15 text-success border-success/30", label: "Investigator" },
  ANALYST:            { color: "bg-info/15 text-info border-info/30", label: "Analyst" },
  POLICY_MAKER:       { color: "bg-muted/40 text-muted-foreground border-border", label: "Policy Maker" },
};

const KARNATAKA_DISTRICTS = [
  "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
  "Bidar", "Chamarajanagara", "Chikkaballapura", "Chikkamagaluru", "Chitradurga",
  "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan",
  "Haveri", "Hubballi-Dharwad", "Kalaburagi", "Kodagu", "Kolar",
  "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara",
  "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura",
  "Yadgir",
];

function AdminPage() {
  const currentUser = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Create user form state
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<Role>("INVESTIGATOR");
  const [creating, setCreating] = useState(false);

  // Active sessions monitoring and account activation status toggles
  const [selectedUserForSessions, setSelectedUserForSessions] = useState<any | null>(null);
  const [userSessions, setUserSessions] = useState<any[]>([]);
  const [loadingUserSessions, setLoadingUserSessions] = useState(false);
  const [revokingUserSessionId, setRevokingUserSessionId] = useState<string | null>(null);
  const [statusChangingId, setStatusChangingId] = useState<number | null>(null);

  // Dashboard stats
  const [stats, setStats] = useState<any>({
    activeUsers: 0,
    investigationsToday: 0,
    mostViewedDistrict: "—",
    mostUsedFeature: "—",
    averageQueryTime: 0,
    totalReportsGenerated: 0,
  });
  const [statsLoading, setStatsLoading] = useState(true);

  // Delete state
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Supervisor district assignment state
  const [assignments, setAssignments] = useState<DistrictAssignmentRecord[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(true);
  const [selectedSupervisorId, setSelectedSupervisorId] = useState<string>("");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("");
  const [assigning, setAssigning] = useState(false);
  const [revokingId, setRevokingId] = useState<number | null>(null);

  useEffect(() => {
    if (!currentUser) {
      navigate({ to: "/login" });
      return;
    }
    if (currentUser.role !== "ADMINISTRATOR") {
      toast.error("Access denied", {
        description: "You do not have permission to view the Admin Console.",
      });
      navigate({ to: "/" });
    } else {
      loadUsers();
      loadStats();
      loadAssignments();
    }
  }, [currentUser, navigate]);

  async function loadStats() {
    setStatsLoading(true);
    try {
      const data = await getAdminStats();
      if (data) setStats(data);
    } catch (err) {
      console.error("Failed to load admin stats:", err);
    } finally {
      setStatsLoading(false);
    }
  }

  async function loadUsers() {
    setLoading(true);
    try {
      const data = await listUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err: any) {
      toast.error("Error", { description: err?.response?.data?.detail ?? "Failed to fetch user list." });
    } finally {
      setLoading(false);
    }
  }

  async function loadAssignments() {
    setAssignmentsLoading(true);
    try {
      const data = await listSupervisorAssignments();
      setAssignments(Array.isArray(data) ? data.filter((a) => a.role === "SUPERVISOR") : []);
    } catch (err: any) {
      console.error("loadAssignments error:", err?.response?.data?.detail ?? err);
      setAssignments([]);
    } finally {
      setAssignmentsLoading(false);
    }
  }

  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !email.trim() || !employeeId.trim()) {
      toast.warning("Missing Fields", { description: "Please fill in username, email, and employee ID." });
      return;
    }
    setCreating(true);
    try {
      await createUser({
        username: username.trim(),
        email: email.trim().toLowerCase(),
        employee_id: employeeId.trim(),
        full_name: fullName.trim(),
        role,
      });
      toast.success("Account Created", { description: `Activation email sent to ${email.trim()}.` });
      setUsername("");
      setEmail("");
      setEmployeeId("");
      setFullName("");
      setRole("INVESTIGATOR");
      await loadUsers();
    } catch (err: any) {
      toast.error("Error", { description: err?.response?.data?.detail ?? "Failed to create user." });
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteUser(userId: number, uName: string) {
    setDeletingId(userId);
    try {
      await deleteUser(userId);
      toast.success("User Deleted", { description: `Removed account '${uName}'.` });
      setDeleteConfirmId(null);
      await loadUsers();
    } catch (err: any) {
      toast.error("Error", { description: err?.response?.data?.detail ?? "Failed to delete user." });
    } finally {
      setDeletingId(null);
    }
  }

  async function loadUserSessions(userId: number) {
    setLoadingUserSessions(true);
    try {
      const data = await apiGet<any[]>(`/admin/users/${userId}/sessions`);
      setUserSessions(data);
    } catch {
      toast.error("Failed to load user active sessions.");
    } finally {
      setLoadingUserSessions(false);
    }
  }

  async function handleRevokeUserSession(userId: number, sessionId: string) {
    setRevokingUserSessionId(sessionId);
    try {
      await apiDelete(`/admin/users/${userId}/sessions/${sessionId}`);
      toast.success("Session terminated successfully.");
      setUserSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    } catch {
      toast.error("Failed to terminate user session.");
    } finally {
      setRevokingUserSessionId(null);
    }
  }

  async function handleRevokeAllUserSessions(userId: number) {
    setLoadingUserSessions(true);
    try {
      await apiPost(`/admin/users/${userId}/logout-all`, {});
      toast.success("All active sessions terminated for this user.");
      await loadUserSessions(userId);
    } catch {
      toast.error("Failed to terminate sessions.");
    } finally {
      setLoadingUserSessions(false);
    }
  }

  async function handleToggleUserStatus(userId: number, currentStatus: string) {
    setStatusChangingId(userId);
    const nextStatus = currentStatus === "ACTIVE" ? "DISABLED" : "ACTIVE";
    try {
      await apiPatch(`/users/${userId}/status`, { status: nextStatus });
      toast.success(`User status updated to ${nextStatus}.`);
      await loadUsers();
    } catch (err: any) {
      toast.error("Failed to change user status.", {
        description: err?.response?.data?.detail ?? "Request failed.",
      });
    } finally {
      setStatusChangingId(null);
    }
  }

  async function handleAssignDistrict() {
    if (!selectedSupervisorId || !selectedDistrict) {
      toast.warning("Incomplete", { description: "Please select both a supervisor and a district." });
      return;
    }
    setAssigning(true);
    try {
      await assignSupervisorDistrict(parseInt(selectedSupervisorId), selectedDistrict);
      toast.success("District Assigned", { description: `'${selectedDistrict}' assigned successfully.` });
      setSelectedSupervisorId("");
      setSelectedDistrict("");
      await loadAssignments();
    } catch (err: any) {
      toast.error("Error", { description: err?.response?.data?.detail ?? "Failed to assign district." });
    } finally {
      setAssigning(false);
    }
  }

  async function handleRevokeAssignment(assignmentId: number, uname: string, district: string) {
    setRevokingId(assignmentId);
    try {
      await revokeSupervisorAssignment(assignmentId);
      toast.success("Assignment Revoked", { description: `Removed '${district}' from ${uname}.` });
      await loadAssignments();
    } catch (err: any) {
      toast.error("Error", { description: err?.response?.data?.detail ?? "Failed to revoke assignment." });
    } finally {
      setRevokingId(null);
    }
  }

  if (!currentUser || currentUser.role !== "ADMINISTRATOR") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
        <div className="p-5 rounded-full bg-destructive/10 text-destructive mb-5 animate-bounce">
          <ShieldAlert className="h-12 w-12" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Access Restricted</h1>
        <p className="text-muted-foreground mt-2 max-w-md text-sm">
          Only registered System Administrators can access the Admin Console.
        </p>
        <Button onClick={() => navigate({ to: "/" })} className="mt-6">
          Return to Console
        </Button>
      </div>
    );
  }

  const supervisors = users.filter((u) => u.role === "SUPERVISOR");

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="System Admin Console"
        subtitle="Manage SCRB users, district assignments, and platform security settings."
      />

      {/* ── Section 1: Stats Row ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { icon: Users, label: "Active Users", value: stats.activeUsers, color: "text-primary" },
          { icon: Database, label: "Investigations Today", value: stats.investigationsToday, color: "text-success" },
          { icon: MapPin, label: "Top District", value: stats.mostViewedDistrict, color: "text-amber-400", isText: true },
          { icon: Cpu, label: "Top Feature", value: stats.mostUsedFeature, color: "text-info", isText: true },
          { icon: Clock, label: "Avg Query Time", value: `${stats.averageQueryTime} ms`, color: "text-chart-2", isText: true },
          { icon: BarChart3, label: "Reports Generated", value: stats.totalReportsGenerated, color: "text-chart-3" },
        ].map(({ icon: Icon, label, value, color, isText }) => (
          <div
            key={label}
            className="glass rounded-xl p-4 flex flex-col justify-between min-h-[90px] hover:scale-[1.02] transition-transform duration-200"
          >
            <div className="flex items-center gap-1.5 mb-2">
              <Icon className={`h-3.5 w-3.5 ${color}`} />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
            </div>
            {statsLoading ? (
              <Skeleton className="h-7 w-16 mt-1" />
            ) : (
              <span className={`font-bold mt-auto truncate ${isText ? "text-base" : "text-2xl"} ${color}`}>
                {value}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* ── Section 2: Register User + User Table ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Register Form */}
        <div className="lg:col-span-1">
          <div className="glass-strong rounded-2xl p-6 relative overflow-hidden h-full">
            {/* Ambient blob */}
            <div className="absolute -right-12 -top-12 h-28 w-28 bg-primary/8 rounded-full blur-2xl pointer-events-none" />
            <div className="absolute -left-8 -bottom-8 h-24 w-24 bg-chart-2/8 rounded-full blur-2xl pointer-events-none" />

            <div className="flex items-center gap-2.5 mb-1">
              <div className="p-1.5 rounded-lg bg-primary/10">
                <UserPlus className="h-4 w-4 text-primary" />
              </div>
              <h2 className="text-base font-semibold">Register Personnel</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-6">
              Create database-backed credentials for authorised law enforcement officers.
            </p>

            <form onSubmit={handleAddUser} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="reg-u" className="text-xs font-medium">Full Name</Label>
                <Input
                  id="reg-fn"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Karan Singh"
                  disabled={creating}
                  className="bg-background/30 border-border/50 text-sm h-9"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-u" className="text-xs font-medium">Username / Badge No.</Label>
                <Input
                  id="reg-u"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. insp_karan"
                  disabled={creating}
                  className="bg-background/30 border-border/50 text-sm h-9"
                  autoComplete="off"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-email" className="text-xs font-medium">Government Email</Label>
                <Input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@ksp.gov.in"
                  disabled={creating}
                  className="bg-background/30 border-border/50 text-sm h-9"
                  autoComplete="off"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-emp" className="text-xs font-medium">Employee ID</Label>
                <Input
                  id="reg-emp"
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  placeholder="e.g. KSP-10045"
                  disabled={creating}
                  className="bg-background/30 border-border/50 text-sm h-9"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-r" className="text-xs font-medium">System Role</Label>
                <Select value={role} onValueChange={(v) => setRole(v as Role)} disabled={creating}>
                  <SelectTrigger id="reg-r" className="bg-background/30 border-border/50 h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r} className="text-sm">
                        {ROLE_META[r]?.label ?? r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" className="w-full mt-2 gap-2 h-9 text-sm" disabled={creating || !username.trim() || !email.trim() || !employeeId.trim()}>
                {creating ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Sending Invitation…</>
                ) : (
                  <><UserPlus className="h-3.5 w-3.5" /> Create & Send Activation Email</>
                )}
              </Button>
            </form>

            {/* Security callout */}
            <div className="mt-6 rounded-xl border border-primary/20 bg-primary/5 p-3.5 flex gap-2.5">
              <Lock className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-semibold text-primary block mb-0.5">Security Audit Enforcement</span>
                <span className="text-[11px] text-muted-foreground leading-relaxed">
                  All admin actions are cryptographically logged and linked to your badge credentials.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Registered Users Table */}
        <div className="lg:col-span-2">
          <div className="glass rounded-2xl p-6 h-full">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg bg-muted/50">
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
                <h2 className="text-base font-semibold">Registered Personnel</h2>
              </div>
              <Badge variant="secondary" className="text-[10px] font-mono tabular-nums">
                {users.length} accounts
              </Badge>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center min-h-[240px] gap-3">
                <Loader2 className="h-7 w-7 animate-spin text-primary" />
                <p className="text-xs text-muted-foreground">Retrieving secure user list…</p>
              </div>
            ) : users.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[240px] text-center border-2 border-dashed border-muted/30 rounded-xl p-6">
                <Users className="h-10 w-10 text-muted-foreground/30 mb-3" />
                <p className="text-sm font-medium">No registered users found</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                  Create user accounts using the registration panel on the left.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-border/50">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/30 hover:bg-muted/30">
                      <TableHead className="w-12 text-center text-[11px]">ID</TableHead>
                      <TableHead className="text-[11px]">Username / Email</TableHead>
                      <TableHead className="text-[11px] w-28">Role</TableHead>
                      <TableHead className="text-[11px] w-24">Sessions</TableHead>
                      <TableHead className="text-[11px] w-24">Status</TableHead>
                      <TableHead className="text-[11px] w-24 text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => {
                      const isAdmin = u.role === "ADMINISTRATOR";
                      const isSelf = u.username === currentUser.username;
                      const meta = ROLE_META[u.role] ?? ROLE_META.INVESTIGATOR;

                      return (
                        <TableRow key={u.id} className="hover:bg-muted/20 transition-colors">
                          <TableCell className="text-center font-mono text-[11px] text-muted-foreground">
                            {u.id}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {isAdmin ? (
                                <Shield className="h-3.5 w-3.5 text-primary shrink-0" />
                              ) : (
                                <Lock className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
                              )}
                              <div className="flex flex-col">
                                <span className="text-sm font-medium">{u.username}</span>
                                <span className="text-[10px] text-muted-foreground">{u.email}</span>
                              </div>
                              {isSelf && (
                                <span className="text-[10px] bg-primary/15 text-primary px-1.5 py-0.5 rounded-md font-semibold">
                                  You
                                </span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium border inline-block ${meta.color}`}>
                              {meta.label}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-[10px] gap-1 px-2"
                              onClick={() => {
                                setSelectedUserForSessions(u);
                                loadUserSessions(u.id);
                              }}
                            >
                              <Activity className="h-3 w-3 text-sky-400" />
                              Sessions
                            </Button>
                          </TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant={u.account_status === "ACTIVE" ? "ghost" : "destructive"}
                              disabled={isSelf || statusChangingId === u.id}
                              className="h-7 text-[10px] px-2 font-semibold"
                              onClick={() => handleToggleUserStatus(u.id, u.account_status)}
                            >
                              {statusChangingId === u.id ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                              ) : (
                                u.account_status || "ACTIVE"
                              )}
                            </Button>
                          </TableCell>
                          <TableCell className="text-right">
                            {deleteConfirmId === u.id ? (
                              <div className="flex items-center justify-end gap-1.5">
                                <span className="text-[10px] text-destructive font-medium">Confirm?</span>
                                <Button
                                  size="icon"
                                  variant="destructive"
                                  className="h-7 w-7"
                                  disabled={deletingId !== null}
                                  onClick={() => handleDeleteUser(u.id, u.username)}
                                >
                                  {deletingId === u.id ? (
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  ) : (
                                    <CheckCircle2 className="h-3 w-3" />
                                  )}
                                </Button>
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="h-7 w-7"
                                  disabled={deletingId !== null}
                                  onClick={() => setDeleteConfirmId(null)}
                                >
                                  <AlertCircle className="h-3 w-3" />
                                </Button>
                              </div>
                            ) : (
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-7 w-7 text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10"
                                disabled={isSelf}
                                title={isSelf ? "Cannot delete your own account" : "Delete user"}
                                onClick={() => setDeleteConfirmId(u.id)}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Section 3: Supervisor District Assignments ─────────────────── */}
      <div className="glass rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute -right-20 -top-20 h-48 w-48 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center gap-2.5 mb-1">
          <div className="p-1.5 rounded-lg bg-amber-500/10">
            <MapPin className="h-4 w-4 text-amber-400" />
          </div>
          <h2 className="text-base font-semibold">Supervisor District Assignments</h2>
          <Badge
            variant="outline"
            className="ml-auto text-[10px] font-mono border-amber-400/30 text-amber-400 bg-amber-500/10"
          >
            {assignments.length} active
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mb-6">
          Assign supervisors to Karnataka districts. Supervisors can only view case data and manage investigators within their assigned jurisdictions.
        </p>

        {/* Assignment form */}
        <div className="flex flex-wrap gap-3 items-end p-4 rounded-xl bg-muted/15 border border-border/40 mb-6">
          <div className="flex-1 min-w-[180px] space-y-1.5">
            <Label htmlFor="sup-select" className="text-xs font-medium">Supervisor</Label>
            <Select value={selectedSupervisorId} onValueChange={setSelectedSupervisorId} disabled={assigning}>
              <SelectTrigger id="sup-select" className="bg-background/30 border-border/50 h-9 text-sm">
                <SelectValue placeholder={supervisors.length === 0 ? "No supervisors found" : "Select supervisor…"} />
              </SelectTrigger>
              <SelectContent>
                {supervisors.length === 0 ? (
                  <div className="px-3 py-2 text-xs text-muted-foreground">No supervisor accounts exist yet.</div>
                ) : (
                  supervisors.map((u) => (
                    <SelectItem key={u.id} value={String(u.id)} className="text-sm">
                      <span className="font-medium">{u.username}</span>
                      <span className="text-muted-foreground ml-2 text-[11px]">#{u.id}</span>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>

          <div className="flex-1 min-w-[200px] space-y-1.5">
            <Label htmlFor="dist-select" className="text-xs font-medium">District</Label>
            <Select value={selectedDistrict} onValueChange={setSelectedDistrict} disabled={assigning}>
              <SelectTrigger id="dist-select" className="bg-background/30 border-border/50 h-9 text-sm">
                <SelectValue placeholder="Select district…" />
              </SelectTrigger>
              <SelectContent className="max-h-64">
                <SelectItem value="All" className="text-sm font-semibold text-primary">All Districts (State-wide)</SelectItem>
                {KARNATAKA_DISTRICTS.map((d) => (
                  <SelectItem key={d} value={d} className="text-sm">{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            id="btn-assign-district"
            onClick={handleAssignDistrict}
            disabled={assigning || !selectedSupervisorId || !selectedDistrict}
            className="gap-2 h-9 text-sm shrink-0"
          >
            {assigning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
            Assign District
          </Button>
        </div>

        {/* Assignments table */}
        {assignmentsLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-11 rounded-lg" />
            ))}
          </div>
        ) : assignments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed border-muted/20 rounded-xl">
            <MapPin className="h-8 w-8 text-muted-foreground/25 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No supervisor districts assigned</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Use the form above to assign a jurisdiction to a supervisor.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border/50">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/30 hover:bg-muted/30">
                  <TableHead className="text-[11px]">Supervisor</TableHead>
                  <TableHead className="text-[11px]">District</TableHead>
                  <TableHead className="text-[11px] hidden sm:table-cell">Assigned</TableHead>
                  <TableHead className="text-[11px] w-16 text-right">Revoke</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assignments.map((a) => (
                  <TableRow key={a.id} className="hover:bg-muted/20 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Shield className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                        <span className="text-sm font-medium">{a.username}</span>
                        <span className="text-[10px] font-mono text-muted-foreground/60">#{a.user_id}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                        <span className="text-sm">{a.district}</span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-xs text-muted-foreground font-mono">
                      {new Date(a.assigned_at).toLocaleDateString("en-IN", {
                        day: "numeric", month: "short", year: "numeric",
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-7 w-7 text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleRevokeAssignment(a.id, a.username, a.district)}
                        disabled={revokingId === a.id}
                        title={`Revoke ${a.district} from ${a.username}`}
                      >
                        {revokingId === a.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <X className="h-3.5 w-3.5" />
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* ── Section 4: Activity Dashboard ─────────────────────────────── */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="p-1.5 rounded-lg bg-chart-2/10">
            <Activity className="h-4 w-4 text-chart-2" />
          </div>
          <h2 className="text-base font-semibold">Platform Activity</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Security Summary */}
          <div className="rounded-xl bg-muted/20 border border-border/40 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Key className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold text-foreground">Security Summary</span>
            </div>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>Total Accounts</span>
                <span className="font-semibold text-foreground tabular-nums">{users.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Supervisors</span>
                <span className="font-semibold text-amber-400 tabular-nums">{users.filter((u) => u.role === "SUPERVISOR").length}</span>
              </div>
              <div className="flex justify-between">
                <span>Investigators</span>
                <span className="font-semibold text-success tabular-nums">{users.filter((u) => u.role === "INVESTIGATOR" || u.role === "SENIOR_INVESTIGATOR").length}</span>
              </div>
              <div className="flex justify-between">
                <span>District Scopes</span>
                <span className="font-semibold text-info tabular-nums">{assignments.length}</span>
              </div>
            </div>
          </div>

          {/* Audit Status */}
          <div className="rounded-xl bg-muted/20 border border-border/40 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="h-4 w-4 text-success" />
              <span className="text-xs font-semibold text-foreground">Audit Compliance</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success animate-pulse shrink-0" />
                <span className="text-xs text-muted-foreground">Audit trail active</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success shrink-0" />
                <span className="text-xs text-muted-foreground">All PII access logged</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success shrink-0" />
                <span className="text-xs text-muted-foreground">Role mutations recorded</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success shrink-0" />
                <span className="text-xs text-muted-foreground">District boundary enforcement</span>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="rounded-xl bg-muted/20 border border-border/40 p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-4 w-4 text-chart-3" />
              <span className="text-xs font-semibold text-foreground">Platform Metrics</span>
            </div>
            {statsLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-4 w-full" />)}
              </div>
            ) : (
              <div className="space-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Queries Today</span>
                  <span className="font-semibold text-foreground tabular-nums">{stats.investigationsToday}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Response</span>
                  <span className="font-semibold text-chart-2 tabular-nums">{stats.averageQueryTime} ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Most Active District</span>
                  <span className="font-semibold text-amber-400 truncate ml-2 max-w-[100px] text-right">{stats.mostViewedDistrict}</span>
                </div>
                <div className="flex justify-between">
                  <span>Reports Generated</span>
                  <span className="font-semibold text-chart-3 tabular-nums">{stats.totalReportsGenerated}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Active Sessions Manager Modal ────────────────────────────── */}
      {selectedUserForSessions && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="glass-strong rounded-2xl w-full max-w-2xl overflow-hidden border border-white/10 shadow-2xl flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-white/15 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-sky-500/15">
                  <Activity className="h-5 w-5 text-sky-400" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">
                    Manage Sessions — {selectedUserForSessions.username}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {selectedUserForSessions.email} · Account Status:{" "}
                    <span className={selectedUserForSessions.account_status === "ACTIVE" ? "text-success font-medium" : "text-destructive font-medium"}>
                      {selectedUserForSessions.account_status || "ACTIVE"}
                    </span>
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-white"
                onClick={() => setSelectedUserForSessions(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              <div className="flex justify-between items-center bg-white/5 rounded-xl p-4 gap-4">
                <div>
                  <span className="text-sm font-semibold text-white block">Forced Sign-out (All Devices)</span>
                  <span className="text-xs text-muted-foreground">
                    Instantly terminate all active sessions for this user.
                  </span>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={loadingUserSessions || userSessions.length === 0}
                  onClick={() => handleRevokeAllUserSessions(selectedUserForSessions.id)}
                >
                  Terminate All Sessions
                </Button>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Active Connections ({userSessions.length})
                </h4>

                {loadingUserSessions && userSessions.length === 0 ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-sky-400" />
                  </div>
                ) : userSessions.length === 0 ? (
                  <div className="text-center py-8 text-sm text-muted-foreground border border-dashed border-white/10 rounded-xl">
                    No active sessions found for this user.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {userSessions.map((s) => (
                      <div
                        key={s.session_id}
                        className="flex items-center gap-3 rounded-lg bg-white/5 p-3.5 border border-white/5 hover:border-white/10 transition-colors"
                      >
                        <div className="flex-shrink-0 h-9 w-9 rounded-lg bg-white/5 flex items-center justify-center">
                          {s.device_type === "Mobile" ? (
                            <Smartphone className="h-4.5 w-4.5 text-muted-foreground" />
                          ) : s.device_type === "Tablet" ? (
                            <Tablet className="h-4.5 w-4.5 text-muted-foreground" />
                          ) : (
                            <Monitor className="h-4.5 w-4.5 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white">
                              {s.os} · {s.browser}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 mt-1 flex-wrap text-[11px] text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Wifi className="h-3 w-3" />
                              {s.ip_address}
                            </span>
                            <span>•</span>
                            <span>Active {new Date(s.last_activity_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={revokingUserSessionId === s.session_id}
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={() => handleRevokeUserSession(selectedUserForSessions.id, s.session_id)}
                        >
                          {revokingUserSessionId === s.session_id ? (
                            <Loader2 className="h-4.5 w-4.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/15 bg-white/5 flex justify-end">
              <Button onClick={() => setSelectedUserForSessions(null)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
