// frontend/src/app/slices/authSlice.ts

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../api";

type User = {
  email?: string;
  roles?: string[];
  is_admin?: boolean;
};

type AuthState = {
  accessToken: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthResolved: boolean; // <--- ДОБАВЛЕНО
};

const initialToken = localStorage.getItem("token"); // <--- ИЗМЕНЕНО
 
const initialState: AuthState = {
  accessToken: initialToken,
  user: null,
  loading: false,
  error: null,
  isAuthResolved: !initialToken, // <--- ИЗМЕНЕНО: Если нет токена, считаем, что статус уже разрешен. Если есть, ждем fetchCurrentUser.
};

export const login = createAsyncThunk(
// ...
);

export const fetchCurrentUser = createAsyncThunk("auth/me", async (_, { rejectWithValue }) => {
  try {
    const { data } = await api.get("/auth/me");
    return data;
  } catch (err) {
    localStorage.removeItem("token");
    return rejectWithValue("Unauthorized");
  }
});

const slice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout(state) {
      state.accessToken = null;
      state.user = null;
      state.error = null;
      state.loading = false;
      state.isAuthResolved = true; // <--- ИЗМЕНЕНО: Выход - это разрешенное состояние.
      localStorage.removeItem("token");
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (s) => {
        s.loading = true;
        s.error = null;
        s.isAuthResolved = false; // <--- ИЗМЕНЕНО: Логин - неразрешенное состояние
      })
      .addCase(login.fulfilled, (s, action: any) => {
        s.loading = false;
        s.error = null;
        s.accessToken = action.payload?.access_token || null;
        s.user = action.payload?.user || null;
        s.isAuthResolved = true; // <--- ИЗМЕНЕНО: Успех - разрешенное состояние
      })
      .addCase(login.rejected, (s, action: any) => {
        s.loading = false;
        s.error = action.payload || "Login failed";
        s.isAuthResolved = true; // <--- ИЗМЕНЕНО: Провал - разрешенное состояние
      })
      .addCase(fetchCurrentUser.fulfilled, (s, action: any) => {
        s.user = action.payload || null;
        s.isAuthResolved = true; // <--- ИЗМЕНЕНО: Успешно загружено - разрешенное состояние
        if (s.accessToken == null) {
          // ...
        }
      })
      .addCase(fetchCurrentUser.rejected, (s) => {
        s.user = null;
        s.accessToken = null;
        s.isAuthResolved = true; // <--- ИЗМЕНЕНО: Ошибка токена - разрешенное состояние
      });
  },
});

export const { logout } = slice.actions;
export default slice.reducer;