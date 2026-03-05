import { useTranslation } from "react-i18next";

export default function LangSwitcher({ className = "" }: { className?: string }) {
  const { i18n } = useTranslation();
  const current = i18n.language;

  function toggle(lng: string) {
    i18n.changeLanguage(lng);
    localStorage.setItem("lang", lng);
  }

  return (
    <div className={`flex items-center gap-1 text-sm font-medium ${className}`}>
      <button
        onClick={() => toggle("de")}
        className={current === "de" ? "font-bold underline" : "opacity-50 hover:opacity-80"}
      >
        DE
      </button>
      <span className="opacity-30">|</span>
      <button
        onClick={() => toggle("en")}
        className={current === "en" ? "font-bold underline" : "opacity-50 hover:opacity-80"}
      >
        EN
      </button>
    </div>
  );
}
