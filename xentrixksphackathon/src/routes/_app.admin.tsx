import { createFileRoute, useNavigate, redirect } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAuthStore, type Role } from "@/stores/auth";
import { PageHeader } from "@/components/app/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  Activity
} from "lucide-react";
import { listUsers, createUser, deleteUser, getAdminStats } from "@/lib/api/services";
import type { UserResponse } from "@/lib/api/types";
import { Skeleton } from "@/components/ui/skeleton";


export const Route = createFileRoute("/_app/admin")({
  head: () => ({ meta: [{ title: "Admin Console — Crime Intelligence Assistant" }] }),
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    if (user?.role !== "Admin") {
      throw redirect({ to: "/" });
    }
  },
  component: AdminPage,
});

const ROLES: Role[] = ["Investigator", "Analyst", "Supervisor", "Policymaker", "Admin"];

function AdminPage() {
  const currentUser = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Form State
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("Investigator");
  const [creating, setCreating] = useState(false);
  
  // Dashboard stats
  const [stats, setStats] = useState<any>({
    activeUsers: 1,
    investigationsToday: 4,
    mostViewedDistrict: "Mysuru",
    mostUsedFeature: "Chat Assistant",
    averageQueryTime: 28.5,
    totalReportsGenerated: 2
  });
  const [statsLoading, setStatsLoading] = useState(true);
  
  // Deleting State
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    if (currentUser && currentUser.role !== "Admin") {
      toast.error("Access denied", {
        description: "You do not have permission to view the Admin Console.",
      });
      navigate({ to: "/" });
    } else {
      loadUsers();
      loadStats();
    }
  }, [currentUser, navigate]);

  async function loadStats() {
    setStatsLoading(true);
    try {
      const data = await getAdminStats();
      if (data) {
        setStats(data);
      }
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
      setUsers(data);
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Failed to fetch user list.";
      toast.error("Error", { description: msg });
    } finally {
      setUsers((prev) => (Array.isArray(prev) ? prev : []));
      setLoading(false);
    }
  }

  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast.warning("Missing Fields", { description: "Please enter both username and password." });
      return;
    }
    
    setCreating(true);
    try {
      await createUser({
        username: username.trim(),
        password: password.trim(),
        role: role,
      });
      toast.success("User Created", { 
        description: `Successfully added ${username} as a ${role}.` 
      });
      setUsername("");
      setPassword("");
      setRole("Investigator");
      await loadUsers();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Failed to create user.";
      toast.error("Error", { description: msg });
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteUser(userId: number, uName: string) {
    setDeletingId(userId);
    try {
      await deleteUser(userId);
      toast.success("User Deleted", {
        description: `Successfully removed user account '${uName}'.`
      });
      setDeleteConfirmId(null);
      await loadUsers();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Failed to delete user.";
      toast.error("Error", { description: msg });
    } finally {
      setDeletingId(null);
    }
  }

  if (!currentUser || currentUser.role !== "Admin") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
        <div className="p-4 rounded-full bg-destructive/10 text-destructive mb-4 animate-bounce">
          <ShieldAlert className="h-12 w-12" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Access Restricted</h1>
        <p className="text-muted-foreground mt-2 max-w-md">
          Only registered System Administrators with valid security credentials can access the Admin Console.
        </p>
        <Button onClick={() => navigate({ to: "/" })} className="mt-6">
          Return to Console
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      <PageHeader 
        title="Admin Console" 
        subtitle="Manage SCRB security keys, user accounts, and database roles."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Registration Form */}
        <div className="lg:col-span-1 space-y-6">
          <section 
            className="rounded-xl glass-strong p-6 relative overflow-hidden"
            style={{
              boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.3)",
              border: "1px solid rgba(255, 255, 255, 0.05)"
            }}
          >
            {/* Ambient accent blob inside the card */}
            <div className="absolute -right-16 -top-16 h-32 w-32 bg-primary/10 rounded-full blur-2xl pointer-events-none" />
            
            <div className="flex items-center gap-2 mb-4">
              <UserPlus className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Register User</h2>
            </div>
            <p className="text-xs text-muted-foreground mb-6">
              Create database-backed credentials for authorized law enforcement personnel.
            </p>

            <form onSubmit={handleAddUser} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="reg-u">Username / Badge No.</Label>
                <Input
                  id="reg-u"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. insp_karan"
                  disabled={creating}
                  className="bg-background/40"
                  autoComplete="off"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-p">Secure Password</Label>
                <Input
                  id="reg-p"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={creating}
                  className="bg-background/40"
                  autoComplete="new-password"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg-r">System Role</Label>
                <Select 
                  value={role} 
                  onValueChange={(v) => setRole(v as Role)} 
                  disabled={creating}
                >
                  <SelectTrigger id="reg-r" className="bg-background/40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" className="w-full mt-2" disabled={creating}>
                {creating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Registering…
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Create Account
                  </>
                )}
              </Button>
            </form>
          </section>

          {/* System Info Callout */}
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex gap-3 text-xs text-primary-foreground/90">
            <Lock className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block mb-1">Security Audit Enforcement</span>
              Every action in the Admin Console is recorded and linked to your badge credentials. Cryptographic keys are rotated every 24 hours.
            </div>
          </div>
        </div>

        {/* Registered Users List */}
        <div className="lg:col-span-2">
          <section 
            className="rounded-xl glass p-6 h-full"
            style={{
              boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.2)",
              border: "1px solid rgba(255, 255, 255, 0.05)"
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">Registered Personnel</h2>
              </div>
              <span className="text-xs text-muted-foreground font-mono bg-muted/40 px-2.5 py-1 rounded-md">
                Total: {users.length} Users
              </span>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center min-h-[250px] space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-xs text-muted-foreground">Retrieving secure user list...</p>
              </div>
            ) : users.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[250px] text-center border-2 border-dashed border-muted/20 rounded-lg p-6">
                <Users className="h-10 w-10 text-muted-foreground/40 mb-3" />
                <p className="text-sm font-semibold">No registered users found</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                  Create database-backed user accounts using the registration panel.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-border/60">
                <Table>
                  <TableHeader className="bg-muted/40">
                    <TableRow>
                      <TableHead className="w-16 text-center">ID</TableHead>
                      <TableHead>Username / Badge No.</TableHead>
                      <TableHead className="w-40">System Role</TableHead>
                      <TableHead className="w-32 text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => {
                      const isAdmin = u.role === "Admin";
                      const isSelf = u.username === currentUser.username;
                      
                      return (
                        <TableRow key={u.id} className="hover:bg-muted/25 transition-colors">
                          <TableCell className="text-center font-mono text-xs text-muted-foreground">
                            {u.id}
                          </TableCell>
                          <TableCell className="font-medium text-foreground">
                            <div className="flex items-center gap-2">
                              {isAdmin ? (
                                <Shield className="h-3.5 w-3.5 text-primary shrink-0" />
                              ) : (
                                <Lock className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
                              )}
                              <span>{u.username}</span>
                              {isSelf && (
                                <span className="text-[10px] bg-primary/20 text-primary-foreground/90 px-1.5 py-0.5 rounded font-medium">
                                  You
                                </span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span 
                              className={`text-[11px] px-2 py-0.5 rounded-full font-medium inline-block ${
                                isAdmin 
                                  ? "bg-primary/10 text-primary border border-primary/20" 
                                  : u.role === "Supervisor"
                                  ? "bg-warning/10 text-warning border border-warning/20"
                                  : "bg-muted/60 text-muted-foreground border border-border"
                              }`}
                            >
                              {u.role}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            {deleteConfirmId === u.id ? (
                              <div className="flex items-center justify-end gap-1.5 animate-fade-in">
                                <span className="text-[10px] text-destructive font-medium mr-1 select-none">
                                  Confirm?
                                </span>
                                <Button
                                  size="icon"
                                  variant="destructive"
                                  className="h-7 w-7"
                                  disabled={deletingId !== null}
                                  onClick={() => handleDeleteUser(u.id, u.username)}
                                >
                                  {deletingId === u.id ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  ) : (
                                    <CheckCircle2 className="h-3.5 w-3.5" />
                                  )}
                                </Button>
                                <Button
                                  size="icon"
                                  variant="outline"
                                  className="h-7 w-7 bg-background/50 hover:bg-background"
                                  disabled={deletingId !== null}
                                  onClick={() => setDeleteConfirmId(null)}
                                >
                                  <AlertCircle className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            ) : (
                              <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                disabled={isSelf}
                                title={isSelf ? "You cannot delete your own account" : "Delete User"}
                                onClick={() => setDeleteConfirmId(u.id)}
                              >
                                <Trash2 className="h-4 w-4" />
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
          </section>
        </div>
      </div>

      {/* User Activity Dashboard */}
      <section 
        className="rounded-xl glass p-6 mt-6 bg-card"
        style={{
          boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.2)",
          border: "1px solid rgba(255, 255, 255, 0.05)"
        }}
      >
        <div className="flex items-center gap-2 mb-6">
          <Activity className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">User Activity Dashboard</h2>
        </div>
        
        {statsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Active Users Today</span>
              <span className="text-3xl font-bold text-primary mt-2">{stats.activeUsers}</span>
            </div>
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Investigations Today</span>
              <span className="text-3xl font-bold text-green-500 mt-2">{stats.investigationsToday}</span>
            </div>
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Most Viewed District</span>
              <span className="text-xl font-bold text-amber-500 mt-2">{stats.mostViewedDistrict}</span>
            </div>
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Most Used Feature</span>
              <span className="text-xl font-bold text-blue-500 mt-2 truncate">{stats.mostUsedFeature}</span>
            </div>
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Avg Query Time</span>
              <span className="text-3xl font-bold text-purple-400 mt-2 font-mono">{stats.averageQueryTime} ms</span>
            </div>
            <div className="p-4 rounded-xl bg-muted/30 border border-border/60 flex flex-col justify-between">
              <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Reports Generated</span>
              <span className="text-3xl font-bold text-teal-400 mt-2">{stats.totalReportsGenerated}</span>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
