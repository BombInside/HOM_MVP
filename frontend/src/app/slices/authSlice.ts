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
  isAuthResolved: boolean; // Флаг для избежания гонки
};

const initialToken = localStorage.getItem("token");
 
const initialState: AuthState = {
  accessToken: initialToken,
  user: null,
  loading: false,
  error: null,
  isAuthResolved: !initialToken, // Если нет токена, считаем, что статус разрешен
};

// ИСПРАВЛЕНИЕ: Используем явную типизацию <Return, Payload, Config>
export const login = createAsyncThunk<
  // 1. Return type (Тип, который возвращает API)
  { access_token: string, user: User, token_type: string }, 
  // 2. Payload (Input) type (Тип входящих данных для thunk)
  { email: string; password: string }, 
  // 3. Config type (Тип конфигурации, включая rejectValue)
  { rejectValue: string } 
>(
  "auth/login",
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      if (data?.access_token) localStorage.setItem("token", data.access_token);
      return data;
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Login failed";
      return rejectWithValue(msg);
    }
  }
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
      state.isAuthResolved = true;
      localStorage.removeItem("token");
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (s) => {
        s.loading = true;
        s.error = null;
        s.isAuthResolved = false;
      })
      .addCase(login.fulfilled, (s, action: any) => {
        s.loading = false;
        s.error = null;
        s.accessToken = action.payload?.access_token || null;
        s.user = action.payload?.user || null;
        s.isAuthResolved = true;
      })
      .addCase(login.rejected, (s, action: any) => {
        s.loading = false;
        s.error = action.payload || "Login failed";
        s.isAuthResolved = true;
      })
      .addCase(fetchCurrentUser.fulfilled, (s, action: any) => {
        s.user = action.payload || null;
        s.isAuthResolved = true;
        if (s.accessToken == null) {
          // если пришёл user, а токена нет — ничего не делаем;
          // (обычно сюда попадём только с токеном)
        }
      })
      .addCase(fetchCurrentUser.rejected, (s) => {
        s.user = null;
        s.accessToken = null;
        s.isAuthResolved = true;
      });
  },
});

export const { logout } = slice.actions;
export default slice.reducer;

// Селекторы для роутера и других компонентов
import type { RootState } from "../store";

// Пользователь авторизован?
export const selectIsAuthenticated = (state: RootState): boolean => {
    // Подстрой это под свою реальную структуру состояния,
    // но чаще всего это что-то вроде:
    return Boolean(
        (state as any).auth?.isAuthenticated ??
        (state as any).auth?.accessToken ??
        (state as any).auth?.token
    );
};

// Роутер может уже принимать решение (auth успел инициализироваться)?
export const selectIsAuthResolved = (state: RootState): boolean => {
    // Если в слайсе есть явный флаг isAuthResolved / isLoaded — используй его.
    const authSlice: any = (state as any).auth || {};
    if (typeof authSlice.isAuthResolved === "boolean") {
        return authSlice.isAuthResolved;
    }
    if (typeof authSlice.isInitialized === "boolean") {
        return authSlice.isInitialized;
    }
    // Fallback: считаем, что как только есть любая инфа о токене — auth "разрулился"
    return Boolean(authSlice.isAuthenticated ?? authSlice.accessToken ?? authSlice.token);
};