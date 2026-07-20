import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient } from "@/lib/api/axios";
import { toast } from "sonner";

export function AccessRequestModal() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [district, setDistrict] = React.useState("");
  const [caseId, setCaseId] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [duration, setDuration] = React.useState("24");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  React.useEffect(() => {
    const handleUnauthorized = (e: Event) => {
      const customEvent = e as CustomEvent<{
        district_id?: string;
        can_request_access?: boolean;
        message?: string;
      }>;
      const detail = customEvent.detail;

      // Only show the modal when the backend explicitly says the user CAN request access.
      // SUPERVISOR, ANALYST, POLICY_MAKER never get can_request_access=true — they
      // should never see this modal. Only INVESTIGATOR and SENIOR_INVESTIGATOR can.
      if (detail?.can_request_access === true && detail?.district_id) {
        setDistrict(detail.district_id);
        setIsOpen(true);
      }
    };

    window.addEventListener("district-not-authorized", handleUnauthorized);
    return () => {
      window.removeEventListener("district-not-authorized", handleUnauthorized);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      toast.error("Please provide a justification reason.");
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post("/security/access-requests", {
        requested_district: district,
        related_case_id: caseId ? parseInt(caseId) : null,
        reason: reason,
        duration_hours: parseInt(duration),
      });
      toast.success(`Temporary access request for ${district} submitted successfully.`);
      setIsOpen(false);
      setReason("");
      setCaseId("");
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? "Failed to submit access request.";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[425px] bg-slate-900 border-slate-800 text-white">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold tracking-tight text-white">Temporary Access Request</DialogTitle>
          <DialogDescription className="text-slate-400">
            You do not have access to data in <span className="font-semibold text-sky-400">{district}</span>.
            Submit a temporary access request to your supervisor.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="district" className="text-slate-300">Target District</Label>
            <Input
              id="district"
              value={district}
              disabled
              className="bg-slate-950 border-slate-800 text-slate-400 cursor-not-allowed"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="caseId" className="text-slate-300">Related Case ID (Optional)</Label>
            <Input
              id="caseId"
              type="number"
              placeholder="e.g. 1023"
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              className="bg-slate-950 border-slate-800 text-white placeholder-slate-600 focus:ring-sky-500"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="duration" className="text-slate-300">Requested Duration</Label>
            <Select value={duration} onValueChange={setDuration}>
              <SelectTrigger className="bg-slate-950 border-slate-800 text-white">
                <SelectValue placeholder="Select duration" />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800 text-white">
                <SelectItem value="2">2 Hours</SelectItem>
                <SelectItem value="6">6 Hours</SelectItem>
                <SelectItem value="12">12 Hours</SelectItem>
                <SelectItem value="24">24 Hours (1 Day)</SelectItem>
                <SelectItem value="48">48 Hours (2 Days)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="reason" className="text-slate-300">Justification / Investigation Reason</Label>
            <Textarea
              id="reason"
              placeholder="Provide a brief explanation for why you need temporary access to this district's cases..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="bg-slate-950 border-slate-800 text-white placeholder-slate-600 focus:ring-sky-500 min-h-[80px]"
            />
          </div>
          <DialogFooter className="pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-sky-600 hover:bg-sky-700 text-white focus:ring-sky-500"
            >
              {isSubmitting ? "Submitting..." : "Submit Request"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
