import { useAppDispatch, useAppSelector } from "../app/store";
import { setLang } from "../app/slices/localeSlice";
import i18n from "../i18n";

const LanguageSwitcher = () => {
  const lang = useAppSelector((s) => s.locale.lang);
  const dispatch = useAppDispatch();

  const change = (lng: "en" | "pl" | "ru") => {
    dispatch(setLang(lng));
    i18n.changeLanguage(lng);
  };

  return (
    <div className="flex gap-2 items-center">
      <button className={`px-2 py-1 rounded ${lang === "en" ? "bg-gray-200 dark:bg-gray-700" : ""}`} onClick={() => change("en")}>EN</button>
      <button className={`px-2 py-1 rounded ${lang === "pl" ? "bg-gray-200 dark:bg-gray-700" : ""}`} onClick={() => change("pl")}>PL</button>
      <button className={`px-2 py-1 rounded ${lang === "ru" ? "bg-gray-200 dark:bg-gray-700" : ""}`} onClick={() => change("ru")}>RU</button>
    </div>
  );
};

export default LanguageSwitcher;
