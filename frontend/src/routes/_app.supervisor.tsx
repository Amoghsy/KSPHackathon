import { createFileRoute, useNavigate, redirect } from "@tanstack/react-router";
import { requiredRoleLabel, PERMISSIONS } from "@/lib/rbac";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth";
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
  Search,
  Activity,
  AlertTriangle
} from "lucide-react";
import { apiClient } from "@/lib/api/axios";

export const Route = createFileRoute("/_app/supervisor")({
  head: () => ({ meta: [{ title: "Supervisor Console — Karnataka State Police" }] }),
  beforeLoad: () => {
    if (typeof window === "undefined") return;
    const user = useAuthStore.getState().user;
    if (user?.role !== "SUPERVISOR" && user?.role !== "ADMINISTRATOR") {
      throw redirect({
        to: "/access-restricted",
        search: {
          module: "Supervisor Console",
          required: requiredRoleLabel([PERMISSIONS.VIEW_AUDIT_LOGS]),
          from: "/supervisor",
        },
      });
    }
  },
  component: SupervisorPage,
});

const KARNATAKA_DISTRICTS = [
  "Bengaluru Urban",
  "Bengaluru Rural",
  "Mysuru",
  "Hubballi-Dharwad",
  "Belagavi",
  "Kalaburagi",
  "Ballari",
  "Shivamogga",
  "Tumakuru",
  "Udupi"
];

function SupervisorPage() {
  const currentUser = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<"requests" | "assignments">("requests");

  // State for Access Requests
  const [requests, setRequests] = useState<any[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(true);

  // State for District Assignments
  const [assignments, setAssignments] = useState<any[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(true);

  // State for User list (for assignment creator)
  const [usersList, setUsersList] = useState<any[]>([]);

  // Dialog & Form State
  const [reviewDialogRequest, setReviewDialogRequest] = useState<any | null>(null);
  const [reviewComment, setReviewComment] = useState("");
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignDistrict, setAssignDistrict] = useState(KARNATAKA_DISTRICTS[0]);
  const [isSubmittingAssign, setIsSubmittingAssign] = useState(false);

  const [reassignDialogTarget, setReassignDialogTarget] = useState<any | null>(null);
  const [reassignNewDistrict, setReassignNewDistrict] = useState(KARNATAKA_DISTRICTS[0]);
  const [isSubmittingReassign, setIsSubmittingReassign] = useState(false);

  useEffect(() => {
    if (currentUser) {
      if (currentUser.role === "SUPERVISOR") {
        loadRequests();
        loadAssignments();
      } else if (currentUser.role === "ADMINISTRATOR") {
        loadUsers();
        setRequestsLoading(false);
        setAssignmentsLoading(false);
      }
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
      // Exclude administrators and supervisors from investigators listing
      const filtered = res.data.filter((u: any) => u.role !== "ADMINISTRATOR" && u.role !== "SUPERVISOR");
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
      toast.success(`Access request successfully ${action === "approve" ? "approved" : action === "reject" ? "rejected" : "marked for more info"}.`);
      setReviewDialogRequest(null);
      setReviewComment("");
      loadRequests();
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? "Failed to submit review.";
      toast.error(msg);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignUserId) {
      toast.error("Please select a user.");
      return;
    }
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
      const msg = err.response?.data?.detail ?? "Failed to create assignment.";
      toast.error(msg);
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
      const msg = err.response?.data?.detail ?? "Failed to revoke assignment.";
      toast.error(msg);
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
      const msg = err.response?.data?.detail ?? "Failed to reassign user.";
      toast.error(msg);
    } finally {
      setIsSubmittingReassign(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6 text-white">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <PageHeader
          title="Supervisor Security Panel"
          subtitle="Review temporary investigator requests and manage district containment assignments."
        />
        <div className="flex items-center gap-3">
          <Button
            onClick={() => {
              loadRequests();
              loadAssignments();
            }}
            variant="outline"
            className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button
            onClick={() => setAssignDialogOpen(true)}
            className="bg-sky-600 hover:bg-sky-700 text-white focus:ring-sky-500"
          >
            <UserPlus className="mr-2 h-4 w-4" />
            Assign District
          </Button>
        </div>
      </div>

      {currentUser?.role === "ADMINISTRATOR" && (
        <Alert className="border-amber-900 bg-amber-950/20 text-amber-300">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Administrative View Mode Only</AlertTitle>
          <AlertDescription>
            You are logged in as an Administrator. Access request approvals and investigator containments are supervised and managed by regional Supervisors. Log in with a Supervisor account to review requests or assign scopes.
          </AlertDescription>
        </Alert>
      )}

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab("requests")}
          className={`flex items-center gap-2 border-b-2 px-6 py-3 text-sm font-medium transition-all ${
            activeTab === "requests"
              ? "border-sky-500 text-sky-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Clock className="h-4 w-4" />
          Pending Access Requests ({requests.length})
        </button>
        <button
          onClick={() => setActiveTab("assignments")}
          className={`flex items-center gap-2 border-b-2 px-6 py-3 text-sm font-medium transition-all ${
            activeTab === "assignments"
              ? "border-sky-500 text-sky-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Users className="h-4 w-4" />
          Permanent District Assignments ({assignments.length})
        </button>
      </div>

      {/* Tab Panels */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-xl">
        {activeTab === "requests" ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Pending Requests Drawer</h2>
              <span className="text-xs text-slate-400">Evaluating active ABAC conditions</span>
            </div>

            {requestsLoading ? (
              <div className="flex h-40 items-center justify-center text-slate-400">Loading pending requests...</div>
            ) : requests.length === 0 ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2 text-slate-500">
                <ShieldCheck className="h-10 w-10 text-slate-600" />
                <p>No pending temporary access requests.</p>
              </div>
            ) : (
              <div className="overflow-hidden border border-slate-800 rounded-lg">
                <Table>
                  <TableHeader className="bg-slate-950/60">
                    <TableRow className="border-slate-800 hover:bg-transparent">
                      <TableHead className="text-slate-400 font-medium">Requester ID</TableHead>
                      <TableHead className="text-slate-400 font-medium">Requested District</TableHead>
                      <TableHead className="text-slate-400 font-medium">Case ID</TableHead>
                      <TableHead className="text-slate-400 font-medium">Justification</TableHead>
                      <TableHead className="text-slate-400 font-medium">Duration</TableHead>
                      <TableHead className="text-slate-400 font-medium">Requested At</TableHead>
                      <TableHead className="text-slate-400 font-medium text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requests.map((req) => (
                      <TableRow key={req.id} className="border-slate-800 hover:bg-slate-800/20">
                        <TableCell className="font-semibold text-slate-300">User #{req.requester_id}</TableCell>
                        <TableCell className="text-sky-400 font-semibold">{req.requested_district}</TableCell>
                        <TableCell className="text-slate-300">{req.related_case_id ?? "N/A"}</TableCell>
                        <TableCell className="max-w-xs truncate text-slate-400" title={req.reason}>
                          {req.reason}
                        </TableCell>
                        <TableCell className="text-slate-300">{req.duration_hours} Hours</TableCell>
                        <TableCell className="text-slate-400 text-xs">
                          {new Date(req.requested_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              onClick={() => setReviewDialogRequest(req)}
                              size="sm"
                              className="bg-sky-600 hover:bg-sky-700 text-white"
                            >
                              Review
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
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Active District Containments</h2>
              <span className="text-xs text-slate-400">Restricting read operations to scoped boundaries</span>
            </div>

            {assignmentsLoading ? (
              <div className="flex h-40 items-center justify-center text-slate-400">Loading assignments...</div>
            ) : assignments.length === 0 ? (
              <div className="flex h-40 flex-col items-center justify-center gap-2 text-slate-500">
                <Users className="h-10 w-10 text-slate-600" />
                <p>No active district assignments found.</p>
              </div>
            ) : (
              <div className="overflow-hidden border border-slate-800 rounded-lg">
                <Table>
                  <TableHeader className="bg-slate-950/60">
                    <TableRow className="border-slate-800 hover:bg-transparent">
                      <TableHead className="text-slate-400 font-medium">Username</TableHead>
                      <TableHead className="text-slate-400 font-medium">System Role</TableHead>
                      <TableHead className="text-slate-400 font-medium">Containment District</TableHead>
                      <TableHead className="text-slate-400 font-medium">Assigned At</TableHead>
                      <TableHead className="text-slate-400 font-medium text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assignments.map((asn) => (
                      <TableRow key={asn.id} className="border-slate-800 hover:bg-slate-800/20">
                        <TableCell className="font-semibold text-slate-300">{asn.username}</TableCell>
                        <TableCell className="text-slate-400 text-xs">
                          <span className="bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full">{asn.role}</span>
                        </TableCell>
                        <TableCell className="text-sky-400 font-semibold">{asn.district}</TableCell>
                        <TableCell className="text-slate-400 text-xs">
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
                              className="border-slate-800 hover:bg-slate-800 text-slate-300"
                            >
                              Reassign
                            </Button>
                            <Button
                              onClick={() => handleRevokeAssignment(asn.id)}
                              size="sm"
                              variant="destructive"
                              className="bg-red-950/40 hover:bg-red-950/80 text-red-400 border border-red-900/60"
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
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white">Review Temporary Access Request</DialogTitle>
            <DialogDescription className="text-slate-400">
              Reviewing request from Investigator User #{reviewDialogRequest?.requester_id} for district{" "}
              <span className="text-sky-400 font-semibold">{reviewDialogRequest?.requested_district}</span>.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-slate-950/60 p-4 border border-slate-800 rounded-lg text-sm space-y-2">
              <div>
                <span className="text-slate-500 block text-xs">Justification Reason</span>
                <span className="text-slate-300 font-medium">{reviewDialogRequest?.reason}</span>
              </div>
              <div className="flex gap-6 pt-2">
                <div>
                  <span className="text-slate-500 block text-xs">Case ID</span>
                  <span className="text-slate-300 font-semibold">{reviewDialogRequest?.related_case_id ?? "None Specified"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-xs">Duration Limit</span>
                  <span className="text-slate-300 font-semibold">{reviewDialogRequest?.duration_hours} Hours</span>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="comment" className="text-slate-300">Decision Comment / Feedback</Label>
              <Textarea
                id="comment"
                placeholder="Enter review decision notes, instructions, or conditions..."
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                className="bg-slate-950 border-slate-800 text-white placeholder-slate-600 focus:ring-sky-500 min-h-[80px]"
              />
            </div>
          </div>
          <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:justify-end">
            <Button
              onClick={() => handleReviewAction("more-info")}
              disabled={isSubmittingReview}
              variant="outline"
              className="border-slate-800 hover:bg-slate-800 text-yellow-500 gap-1.5"
            >
              <HelpCircle className="h-4 w-4" />
              Need Info
            </Button>
            <Button
              onClick={() => handleReviewAction("reject")}
              disabled={isSubmittingReview}
              variant="destructive"
              className="bg-red-650 hover:bg-red-750 text-white gap-1.5"
            >
              <X className="h-4 w-4" />
              Reject
            </Button>
            <Button
              onClick={() => handleReviewAction("approve")}
              disabled={isSubmittingReview}
              className="bg-green-605 hover:bg-green-705 text-white gap-1.5"
            >
              <Check className="h-4 w-4" />
              Approve Access
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign District Dialog */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white">New Permanent District Assignment</DialogTitle>
            <DialogDescription className="text-slate-400">
              Create a database record assigning an investigator to a containment scope.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateAssignment} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="assignUser" className="text-slate-300">Select Investigator / Analyst</Label>
              <Select value={assignUserId} onValueChange={setAssignUserId}>
                <SelectTrigger className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue placeholder="Select an investigator" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  {usersList.map((u) => (
                    <SelectItem key={u.id} value={u.id.toString()}>
                      {u.username} ({u.role})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="assignDistrict" className="text-slate-300">Containment District</Label>
              <Select value={assignDistrict} onValueChange={setAssignDistrict}>
                <SelectTrigger className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue placeholder="Select district" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  {KARNATAKA_DISTRICTS.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setAssignDialogOpen(false)}
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmittingAssign}
                className="bg-sky-600 hover:bg-sky-700 text-white focus:ring-sky-500"
              >
                {isSubmittingAssign ? "Creating..." : "Create Assignment"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reassign Dialog */}
      <Dialog open={!!reassignDialogTarget} onOpenChange={(open) => !open && setReassignDialogTarget(null)}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white">Reassign District Containment</DialogTitle>
            <DialogDescription className="text-slate-400">
              Reassign investigator <span className="font-semibold text-slate-200">{reassignDialogTarget?.username}</span> from{" "}
              <span className="font-semibold text-sky-400">{reassignDialogTarget?.district}</span> to a new district scope.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleReassign} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reassignDistrict" className="text-slate-300">New Containment District</Label>
              <Select value={reassignNewDistrict} onValueChange={setReassignNewDistrict}>
                <SelectTrigger className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue placeholder="Select new district" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-white">
                  {KARNATAKA_DISTRICTS.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setReassignDialogTarget(null)}
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmittingReassign}
                className="bg-sky-600 hover:bg-sky-700 text-white focus:ring-sky-500"
              >
                {isSubmittingReassign ? "Reassigning..." : "Confirm Reassignment"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
