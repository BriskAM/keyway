import { defineStore } from "pinia";
import api from "../api/axios";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    isAuthenticated: false,
    hasKey: false,
    loading: false,
    error: null,
  }),

  actions: {
    async checkAuth() {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.get("/api/auth/me");
        if (res.data.authenticated) {
          this.user = res.data.user;
          this.isAuthenticated = true;
          this.hasKey = res.data.has_key || false;
        } else {
          this.resetState();
        }
      } catch (err) {
        this.resetState();
        this.error = err.response?.data?.error || "Session check failed";
      } finally {
        this.loading = false;
      }
    },

    async login(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.post("/api/auth/login", { email, password });
        this.user = res.data.user;
        this.isAuthenticated = true;
        this.hasKey = true;
        return true;
      } catch (err) {
        this.error = err.response?.data?.error || "Login failed. Check credentials.";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async signup(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.post("/api/auth/signup", { email, password });
        this.user = res.data.user;
        this.isAuthenticated = true;
        this.hasKey = true;
        return true;
      } catch (err) {
        this.error = err.response?.data?.error || "Signup failed. Try a different email.";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      this.loading = true;
      try {
        await api.post("/api/auth/logout");
      } catch (err) {
        console.error("Logout request error", err);
      } finally {
        this.resetState();
        this.loading = false;
      }
    },

    resetState() {
      this.user = null;
      this.isAuthenticated = false;
      this.hasKey = false;
    },
  },
});
