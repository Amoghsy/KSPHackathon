import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/primitives";
import { useAuthStore } from "@/stores/auth";
import { usePrefs } from "@/stores/prefs";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/settings")({
  head: () => ({ meta: [{ title: "Settings — Crime Intelligence Assistant" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const { lang, setLang, theme, toggleTheme } = usePrefs();
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Settings" subtitle="Profile, language and notification preferences." />
      <div className="space-y-6">
        <section className="rounded-xl glass p-5">
          <h2 className="text-sm font-semibold mb-4">Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Name</Label>
              <Input readOnly value={user?.name ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Role</Label>
              <Input readOnly value={user?.role ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Badge No.</Label>
              <Input readOnly value={user?.badgeNo ?? ""} />
            </div>
            <div className="space-y-1.5">
              <Label>Station</Label>
              <Input readOnly value={user?.station ?? ""} />
            </div>
          </div>
        </section>

        <section className="rounded-xl glass p-5">
          <h2 className="text-sm font-semibold mb-4">Preferences</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Language</div>
                <div className="text-xs text-muted-foreground">Interface language for labels.</div>
              </div>
              <div className="flex rounded-md border border-input overflow-hidden text-xs">
                <button
                  onClick={() => setLang("en")}
                  className={
                    "px-3 py-1.5 font-medium " +
                    (lang === "en" ? "bg-primary text-primary-foreground" : "hover:bg-accent")
                  }
                >
                  English
                </button>
                <button
                  onClick={() => setLang("kn")}
                  className={
                    "px-3 py-1.5 font-medium " +
                    (lang === "kn" ? "bg-primary text-primary-foreground" : "hover:bg-accent")
                  }
                >
                  ಕನ್ನಡ
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Dark mode</div>
                <div className="text-xs text-muted-foreground">Best for low-light control rooms.</div>
              </div>
              <Switch checked={theme === "dark"} onCheckedChange={toggleTheme} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Critical alert notifications</div>
                <div className="text-xs text-muted-foreground">Push critical alerts to this session.</div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </section>

        <div>
          <Button
            onClick={() =>
              toast.success("Preferences saved", {
                description: "Language, theme and notification settings updated.",
              })
            }
          >
            Save changes
          </Button>
          <span className="text-xs text-muted-foreground ml-3">
            Profile changes require Supervisor approval.
          </span>
        </div>
      </div>
    </div>
  );
}
