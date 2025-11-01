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
};

const initialState: AuthState = {
  accessToken: localStorage.getItem("token"),
  user: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  "auth/login",
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
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
      localStorage.removeItem("token");
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (s) => {
        s.loading = true;
        s.error = null;
      })
      .addCase(login.fulfilled, (s, action: any) => {
        s.loading = false;
        s.error = null;
        s.accessToken = action.payload?.access_token || null;
        s.user = action.payload?.user || null;
      })
      .addCase(login.rejected, (s, action: any) => {
        s.loading = false;
        s.error = action.payload || "Login failed";
      })
      .addCase(fetchCurrentUser.fulfilled, (s, action: any) => {
        s.user = action.payload || null;
        if (s.accessToken == null) {
          // если пришёл user, а токена нет — ничего не делаем;
          // (обычно сюда попадём только с токеном)
        }
      })
      .addCase(fetchCurrentUser.rejected, (s) => {
        s.user = null;
        s.accessToken = null;
      });
  },
});

export const { logout } = slice.actions;
export default slice.reducer;
