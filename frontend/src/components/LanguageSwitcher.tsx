import { useState } from "react";
import i18n from "../i18n";

/**
 * Простое переключение языка (RU/EN/PL) без Redux.
 * Использует i18next напрямую.
 */
const LanguageSwitcher = () => {
  const [lang, setLang] = useState(i18n.language || "ru");

  const change = (lng: "en" | "pl" | "ru") => {
    setLang(lng);
    i18n.changeLanguage(lng);
  };

  return (
    <div className="flex gap-2 items-center">
      {["en", "pl", "ru"].map((lng) => (
        <button
          key={lng}
          onClick={() => change(lng as "en" | "pl" | "ru")}
          className={`px-2 py-1 rounded ${
            lang === lng ? "bg-gray-200 dark:bg-gray-700 font-semibold" : ""
          }`}
        >
          {lng.toUpperCase()}
        </button>
      ))}
    </div>
  );
};

export default LanguageSwitcher;
