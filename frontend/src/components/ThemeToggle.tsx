import { useEffect, useState } from "react";

/**
 * Переключатель темы (dark/light).
 * Сохраняет выбор пользователя в localStorage.
 */
const ThemeToggle = () => {
  const [theme, setTheme] = useState(
    localStorage.getItem("theme") || "dark"
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggle = () =>
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));

  return (
    <button
      onClick={toggle}
      className="px-3 py-1 rounded border dark:border-gray-700 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200"
    >
      {theme === "dark" ? "☾ Dark" : "☀ Light"}
    </button>
  );
};

export default ThemeToggle;
