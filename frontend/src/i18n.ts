import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import ru from "./locales/ru.json";
import en from "./locales/en.json";
import pl from "./locales/pl.json";

/**
 * Инициализация i18next без зависимости от Redux.
 * Автоматически определяет язык браузера и fallback = en.
 */
i18next.use(initReactI18next).init({
  lng: navigator.language.startsWith("ru")
    ? "ru"
    : navigator.language.startsWith("pl")
    ? "pl"
    : "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  resources: {
    en: { translation: en },
    ru: { translation: ru },
    pl: { translation: pl },
  },
});

export default i18next;
