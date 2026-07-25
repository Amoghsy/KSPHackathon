import { createFileRoute, useNavigate, redirect } from "@tanstack/react-router";
import { requiredRoleLabel, PERMISSIONS } from "@/lib/rbac";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth";
import { PageHeader } from "@/components/app/primitives";
import { Button } from "@/components/ui/button";
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Users,
  ShieldCheck,
  Clock,
  UserMinus,
  UserPlus,
  Check,
  X,
  HelpCircle,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/lib/api/axios";

export const Route = createFileRoute("/_app/supervisor")({
  head: () => ({ meta: [{ title: "Supervisor Console — Karnataka State Police" }] }),
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    const isAuthorized = user?.role === "SUPERVISOR";
    if (!isAuthorized) {
      throw redirect({
        to: "/access-restricted",
        search: {
          module: "Supervisor Panel",
          required: requiredRoleLabel([PERMISSIONS.ASSIGN_DISTRICTS]),
          from: "/supervisor",
        },
      });
    }
  },
  component: SupervisorPage,
});

const KARNATAKA_DISTRICTS = [
  "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
  "Bidar", "Chamarajanagara", "Chikkaballapura", "Chikkamagaluru", "Chitradurga",
  "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan",
  "Haveri", "Hubballi-Dharwad", "Kalaburagi", "Kodagu", "Kolar",
  "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara",
  "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura",
  "Yadgir",
];

function SupervisorPage() {
  const currentUser = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"requests" | "assignments">("requests");

  const [requests, setRequests] = useState<any[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(true);

  const [assignments, setAssignments] = useState<any[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(true);

  const [usersList, setUsersList] = useState<any[]>([]);

  const [reviewDialogRequest, setReviewDialogRequest] = useState<any | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const [supervisorDistricts, setSupervisorDistricts] = useState<string[]>([]);

  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignDistrict, setAssignDistrict] = useState("");
  const [isSubmittingAssign, setIsSubmittingAssign] = useState(false);

  const [reassignDialogTarget, setReassignDialogTarget] = useState<any | null>(null);
  const [reassignNewDistrict, setReassignNewDistrict] = useState("");
  const [isSubmittingReassign, setIsSubmittingReassign] = useState(false);

  const loadSupervisorDistricts = async () => {
    if (!currentUser) return;
    try {
      const res = await apiClient.get<any[]>(`/security/district-assignments/user/${currentUser.id}`);
      const dists = res.data.map((d: any) => d.district);
      const isStateWide = dists.some((d: string) => d === "All" || d === "__ALL__");
      const finalDists = isStateWide ? ["All", ...KARNATAKA_DISTRICTS] : dists;
      setSupervisorDistricts(finalDists);
      if (finalDists.length > 0) {
        setAssignDistrict(finalDists[0]);
        setReassignNewDistrict(finalDists[0]);
      }
    } catch (err) {
      console.error("Failed to load supervisor districts:", err);
    }
  };

  useEffect(() => {
    if (currentUser && currentUser.role === "SUPERVISOR") {
      loadRequests();
      loadAssignments();
      loadSupervisorDistricts();
    }
  }, [currentUser]);

  const loadRequests = async () => {
    setRequestsLoading(true);
    try {
      const res = await apiClient.get<any[]>("/security/access-requests/pending");
      setRequests(res.data);
    } catch (err) {
      console.error("Failed to load requests:", err);
      toast.error("Failed to load pending access requests.");
    } finally {
      setRequestsLoading(false);
    }
  };

  const loadAssignments = async () => {
    setAssignmentsLoading(true);
    try {
      const res = await apiClient.get<any[]>("/security/district-assignments/investigators");
      setAssignments(res.data);
    } catch (err) {
      console.error("Failed to load assignments:", err);
      toast.error("Failed to load district assignments.");
    } finally {
      setAssignmentsLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const res = await apiClient.get<any[]>("/users/");
      const filtered = res.data.filter((u: any) => {
        const r = String(u.role).toUpperCase();
        return r !== "ADMINISTRATOR" && r !== "SUPERVISOR" && r !== "ADMIN";
      });
      setUsersList(filtered);
    } catch (err) {
      console.error("Failed to load users:", err);
    }
  };

  const handleReviewAction = async (action: "approve" | "reject" | "more-info") => {
    if (!reviewDialogRequest) return;
    setIsSubmittingReview(true);
    try {
      await apiClient.post(`/security/access-requests/${reviewDialogRequest.id}/${action}`, {
        review_comment: reviewComment,
      });
      toast.success(
        `Access request ${action === "approve" ? "approved" : action === "reject" ? "rejected" : "marked for more info"}.`
      );
      setReviewDialogRequest(null);
      setReviewComment("");
      loadRequests();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Failed to submit review.");
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignUserId) { toast.error("Please select a user."); return; }
    setIsSubmittingAssign(true);
    try {
      await apiClient.post("/security/district-assignments", {
        user_id: parseInt(assignUserId),
        district: assignDistrict,
      });
      toast.success("District assignment created successfully.");
      setAssignDialogOpen(false);
      setAssignUserId("");
      loadAssignments();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Failed to create assignment.");
    } finally {
      setIsSubmittingAssign(false);
    }
  };

  const handleRevokeAssignment = async (id: number) => {
    if (!confirm("Are you sure you want to revoke this district assignment?")) return;
    try {
      await apiClient.delete(`/security/district-assignments/${id}`);
      toast.success("District assignment revoked successfully.");
      loadAssignments();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Failed to revoke assignment.");
    }
  };

  const handleReassign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reassignDialogTarget) return;
    setIsSubmittingReassign(true);
    try {
      await apiClient.post(`/security/district-assignments/${reassignDialogTarget.id}/reassign`, {
        new_district: reassignNewDistrict,
      });
      toast.success("User reassigned successfully.");
      setReassignDialogTarget(null);
      loadAssignments();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Failed to reassign user.");
    } finally {
      setIsSubmittingReassign(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      <PageHeader
        title="Supervisor Security Panel"
        subtitle="Review temporary investigator requests and manage district containment assignments."
        actions={
          <div className="flex items-center gap-3">
            <Button
              onClick={() => { loadRequests(); loadAssignments(); }}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button
              onClick={() => { loadUsers(); setAssignDialogOpen(true); }}
              size="sm"
            >
              <UserPlus className="mr-2 h-4 w-4" />
              Assign District
            </Button>
          </div>
        }
      />

      {/* Tabs Navigation */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab("requests")}
          className={`-mb-[1px] flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-all ${
            activeTab === "requests"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          <Clock className="h-4 w-4" />
          Pending Access Requests ({requests.length})
        </button>
        <button
          onClick={() => setActiveTab("assignments")}
          className={`-mb-[1px] flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-all ${
            activeTab === "assignments"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
          }`}
        >
          <Users className="h-4 w-4" />
          Permanent District Assignments ({assignments.length})
        </button>
      </div>

      {/* Tab Panels */}
      <div className="rounded-xl glass p-6">
        {activeTab === "requests" ? (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-foreground">Pending Requests Drawer</h2>
              <span className="text-xs text-muted-foreground">Evaluating active ABAC conditions</span>
            </div>

            {requestsLoading ? (
              <div className="flex h-40 items-center justify-center text-muted-foreground text-sm">
                Loading pending requests…
              </div>
            ) : requests.length === 0 ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2 text-muted-foreground">
                <ShieldCheck className="h-10 w-10 opacity-30" />
                <p className="text-sm">No pending temporary access requests.</p>
              </div>
            ) : (
              <div className="overflow-hidden border border-border rounded-lg">
                <Table>
                  <TableHeader className="bg-muted/60">
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="font-medium">Requester ID</TableHead>
                      <TableHead className="font-medium">Requested District</TableHead>
                      <TableHead className="font-medium">Case ID</TableHead>
                      <TableHead className="font-medium">Justification</TableHead>
                      <TableHead className="font-medium">Duration</TableHead>
                      <TableHead className="font-medium">Requested At</TableHead>
                      <TableHead className="font-medium text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requests.map((req) => (
                      <TableRow key={req.id} className="border-border hover:bg-accent/40">
                        <TableCell className="font-semibold">User #{req.requester_id}</TableCell>
                        <TableCell className="text-primary font-semibold">{req.requested_district}</TableCell>
                        <TableCell>{req.related_case_id ?? "N/A"}</TableCell>
                        <TableCell className="max-w-xs truncate text-muted-foreground" title={req.reason}>
                          {req.reason}
                        </TableCell>
                        <TableCell>{req.duration_hours} Hours</TableCell>
                        <TableCell className="text-muted-foreground text-xs">
                          {new Date(req.requested_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            onClick={() => setReviewDialogRequest(req)}
                            size="sm"
                            variant="outline"
                          >
                            Review
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-foreground">Active District Containments</h2>
              <span className="text-xs text-muted-foreground">Restricting read operations to scoped boundaries</span>
            </div>

            {assignmentsLoading ? (
              <div className="flex h-40 items-center justify-center text-muted-foreground text-sm">
                Loading assignments…
              </div>
            ) : assignments.length === 0 ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2 text-muted-foreground">
                <Users className="h-10 w-10 opacity-30" />
                <p className="text-sm">No active district assignments found.</p>
              </div>
            ) : (
              <div className="overflow-hidden border border-border rounded-lg">
                <Table>
                  <TableHeader className="bg-muted/60">
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="font-medium">Username</TableHead>
                      <TableHead className="font-medium">System Role</TableHead>
                      <TableHead className="font-medium">Containment District</TableHead>
                      <TableHead className="font-medium">Assigned At</TableHead>
                      <TableHead className="font-medium text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assignments.map((asn) => (
                      <TableRow key={asn.id} className="border-border hover:bg-accent/40">
                        <TableCell className="font-semibold">{asn.username}</TableCell>
                        <TableCell>
                          <span className="bg-muted text-muted-foreground px-2.5 py-1 rounded-full text-xs font-medium">
                            {asn.role}
                          </span>
                        </TableCell>
                        <TableCell className="text-primary font-semibold">{asn.district}</TableCell>
                        <TableCell className="text-muted-foreground text-xs">
                          {new Date(asn.assigned_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              onClick={() => {
                                setReassignDialogTarget(asn);
                                setReassignNewDistrict(asn.district);
                              }}
                              size="sm"
                              variant="outline"
                            >
                              Reassign
                            </Button>
                            <Button
                              onClick={() => handleRevokeAssignment(asn.id)}
                              size="sm"
                              variant="destructive"
                            >
                              <UserMinus className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Review Access Request Dialog */}
      <Dialog open={!!reviewDialogRequest} onOpenChange={(open) => !open && setReviewDialogRequest(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Temporary Access Request</DialogTitle>
            <DialogDescription>
              Reviewing request from User #{reviewDialogRequest?.requester_id} for district{" "}
              <span className="text-primary font-semibold">{reviewDialogRequest?.requested_district}</span>.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="bg-muted/60 p-4 border border-border rounded-lg text-sm space-y-2">
              <div>
                <span className="text-muted-foreground block text-xs mb-0.5">Justification Reason</span>
                <span className="font-medium">{reviewDialogRequest?.reason}</span>
              </div>
              <div className="flex gap-6 pt-2">
                <div>
                  <span className="text-muted-foreground block text-xs mb-0.5">Case ID</span>
                  <span className="font-semibold">{reviewDialogRequest?.related_case_id ?? "None Specified"}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-xs mb-0.5">Duration Limit</span>
                  <span className="font-semibold">{reviewDialogRequest?.duration_hours} Hours</span>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="comment">Decision Comment / Feedback</Label>
              <Textarea
                id="comment"
                placeholder="Enter review decision notes, instructions, or conditions…"
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </div>
          <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:justify-end">
            <Button
              onClick={() => handleReviewAction("more-info")}
              disabled={isSubmittingReview}
              variant="outline"
              className="gap-1.5"
            >
              <HelpCircle className="h-4 w-4" />
              Need Info
            </Button>
            <Button
              onClick={() => handleReviewAction("reject")}
              disabled={isSubmittingReview}
              variant="destructive"
              className="gap-1.5"
            >
              <X className="h-4 w-4" />
              Reject
            </Button>
            <Button
              onClick={() => handleReviewAction("approve")}
              disabled={isSubmittingReview}
              className="gap-1.5"
            >
              <Check className="h-4 w-4" />
              Approve Access
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign District Dialog */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Permanent District Assignment</DialogTitle>
            <DialogDescription>
              Create a database record assigning an investigator to a containment scope.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateAssignment} className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="assignUser">Select Investigator / Analyst</Label>
              <Select value={assignUserId} onValueChange={setAssignUserId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select an investigator" />
                </SelectTrigger>
                <SelectContent>
                  {usersList.map((u) => (
                    <SelectItem key={u.id} value={u.id.toString()}>
                      {u.username} ({u.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="assignDistrict">Containment District</Label>
              <Select value={assignDistrict} onValueChange={setAssignDistrict}>
                <SelectTrigger>
                  <SelectValue placeholder="Select district" />
                </SelectTrigger>
                <SelectContent>
                  {supervisorDistricts.map((d: string) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setAssignDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmittingAssign}>
                {isSubmittingAssign ? "Creating…" : "Create Assignment"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
 
      {/* Reassign Dialog */}
      <Dialog open={!!reassignDialogTarget} onOpenChange={(open) => !open && setReassignDialogTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reassign District Containment</DialogTitle>
            <DialogDescription>
              Reassign <span className="font-semibold">{reassignDialogTarget?.username}</span> from{" "}
              <span className="font-semibold text-primary">{reassignDialogTarget?.district}</span> to a new scope.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleReassign} className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="reassignDistrict">New Containment District</Label>
              <Select value={reassignNewDistrict} onValueChange={setReassignNewDistrict}>
                <SelectTrigger>
                  <SelectValue placeholder="Select new district" />
                </SelectTrigger>
                <SelectContent>
                  {supervisorDistricts.map((d: string) => (
                    <SelectItem key={d} value={d}>{d}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setReassignDialogTarget(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmittingReassign}>
                {isSubmittingReassign ? "Reassigning…" : "Confirm Reassignment"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
