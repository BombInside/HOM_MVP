// Redux store + полезные хуки.
// Если уже есть redux-persist — можно подключить отдельно. Здесь — минимально и надёжно.

import { configureStore } from "@reduxjs/toolkit";
import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";
import authReducer from "./slices/authSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  middleware: (getDefault) => getDefault({ serializableCheck: false }),
  devTools: true,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
