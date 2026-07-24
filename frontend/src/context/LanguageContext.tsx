import React, { createContext, useContext, useEffect, useState } from "react";

export type Language = "auto" | "en" | "kn";
export type ResolvedLanguage = "en" | "kn";
export type RecognitionLanguage = "en-IN" | "kn-IN";

interface LanguageContextProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  resolvedLanguage: ResolvedLanguage;
  recognitionLanguage: RecognitionLanguage;
}

const LanguageContext = createContext<LanguageContextProps | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>("auto");

  // Initialize from Local Storage on mount (client-side only)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("scrb-response-lang") as Language;
      if (saved && ["auto", "en", "kn"].includes(saved)) {
        setLanguageState(saved);
      }
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("scrb-response-lang", lang);
    }
  };

  // Resolve active language
  const [resolvedLanguage, setResolvedLanguage] = useState<ResolvedLanguage>("en");

  useEffect(() => {
    let resolved: ResolvedLanguage = "en";
    if (language === "auto") {
      if (typeof navigator !== "undefined") {
        const browserLang = navigator.language || "";
        if (browserLang.toLowerCase().startsWith("kn")) {
          resolved = "kn";
        }
      }
    } else {
      resolved = language;
    }
    setResolvedLanguage(resolved);
  }, [language]);

  const recognitionLanguage: RecognitionLanguage = resolvedLanguage === "kn" ? "kn-IN" : "en-IN";

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        resolvedLanguage,
        recognitionLanguage,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
