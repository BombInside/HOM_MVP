import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../app/store";
import { setTheme } from "../app/slices/uiSlice";

const ThemeToggle = () => {
  const theme = useAppSelector((s) => s.ui.theme);
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(setTheme(theme));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = () => dispatch(setTheme(theme === "dark" ? "light" : "dark"));

  return <button className="px-3 py-1 rounded border" onClick={toggle}>{theme === "dark" ? "☾ Dark" : "☀ Light"}</button>;
};

export default ThemeToggle;
