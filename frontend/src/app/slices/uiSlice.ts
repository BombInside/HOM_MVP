import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type UiState = {
  theme: "light" | "dark";
  toast?: { type: "success" | "error" | "info"; message: string } | null;
};

const preferredTheme = ((): "light" | "dark" => {
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return "light";
})();

const initialState: UiState = {
  theme: preferredTheme,
  toast: null,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<"light" | "dark">) => {
      state.theme = action.payload;
      localStorage.setItem("theme", action.payload);
      const root = document.documentElement;
      if (action.payload === "dark") root.classList.add("dark");
      else root.classList.remove("dark");
    },
    showToast: (state, action: PayloadAction<UiState["toast"]>) => {
      state.toast = action.payload || null;
    },
    clearToast: (state) => {
      state.toast = null;
    },
  },
});

export const { setTheme, showToast, clearToast } = uiSlice.actions;
export default uiSlice.reducer;
