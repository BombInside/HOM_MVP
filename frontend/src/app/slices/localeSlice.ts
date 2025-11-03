import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type LocaleState = {
  lang: "en" | "pl" | "ru";
};

const preferred = ((): "en" | "pl" | "ru" => {
  const stored = localStorage.getItem("lang");
  if (stored === "pl" || stored === "ru" || stored === "en") return stored;
  return "en";
})();

const initialState: LocaleState = {
  lang: preferred,
};

const localeSlice = createSlice({
  name: "locale",
  initialState,
  reducers: {
    setLang: (state, action: PayloadAction<"en" | "pl" | "ru">) => {
      state.lang = action.payload;
      localStorage.setItem("lang", action.payload);
    },
  },
});

export const { setLang } = localeSlice.actions;
export default localeSlice.reducer;
