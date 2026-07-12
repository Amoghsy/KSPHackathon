import React from "react";
import { Globe, Check } from "lucide-react";
import { useLanguage, Language } from "@/context/LanguageContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

export const LanguageSelector: React.FC = () => {
  const { language, setLanguage, resolvedLanguage } = useLanguage();

  const options: { value: Language; label: string }[] = [
    { value: "auto", label: "Auto Detect" },
    { value: "en", label: "English" },
    { value: "kn", label: "ಕನ್ನಡ (Kannada)" },
  ];

  const currentLabel = options.find((opt) => opt.value === language)?.label || "Language";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-9 px-3 gap-2 border-input bg-background/40 backdrop-blur-md hover:bg-accent hover:text-accent-foreground text-xs font-medium"
        >
          <Globe className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="hidden sm:inline">{currentLabel}</span>
          <span className="sm:hidden uppercase">{language === "auto" ? `AUTO (${resolvedLanguage})` : language}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40 glass-strong">
        {options.map((opt) => (
          <DropdownMenuItem
            key={opt.value}
            onClick={() => setLanguage(opt.value)}
            className="flex items-center justify-between text-xs cursor-pointer"
          >
            <span>{opt.label}</span>
            {language === opt.value && <Check className="h-3.5 w-3.5 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
