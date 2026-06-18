import { defineStore } from "pinia";
import api from "../api/axios";

export const useSecretsStore = defineStore("secrets", {
  state: () => ({
    secrets: [],
    dashboardData: {
      total_secrets: 0,
      expiring_soon: [],
      expired: [],
      invalid_keys: [],
      unchecked: [],
    },
    loading: false,
    checkingAll: false,
    error: null,
  }),

  actions: {
    async fetchSecrets() {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.get("/api/secrets");
        this.secrets = res.data;
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to load secrets";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async fetchDashboard() {
      this.loading = true;
      this.error = null;
      try {
        const res = await api.get("/api/dashboard");
        this.dashboardData = res.data;
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to load dashboard metrics";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async createSecret(payload) {
      this.error = null;
      try {
        const res = await api.post("/api/secrets", payload);
        this.secrets.unshift(res.data.secret);
        await this.fetchDashboard(); // Keep dashboard updated
        return res.data.secret;
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to create secret";
        throw err;
      }
    },

    async updateSecret(id, payload) {
      this.error = null;
      try {
        const res = await api.put(`/api/secrets/${id}`, payload);
        const idx = this.secrets.findIndex((s) => s.id === id);
        if (idx !== -1) {
          this.secrets[idx] = res.data.secret;
        }
        await this.fetchDashboard();
        return res.data.secret;
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to update secret";
        throw err;
      }
    },

    async deleteSecret(id) {
      this.error = null;
      try {
        await api.delete(`/api/secrets/${id}`);
        this.secrets = this.secrets.filter((s) => s.id !== id);
        await this.fetchDashboard();
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to delete secret";
        throw err;
      }
    },

    async revealSecret(id) {
      try {
        const res = await api.post(`/api/secrets/${id}/reveal`);
        return res.data.value;
      } catch (err) {
        const errMsg = err.response?.data?.error || "Failed to reveal secret";
        alert(errMsg); // Or handle in component UI
        throw err;
      }
    },

    async runHealthcheck(id) {
      try {
        const res = await api.post(`/api/secrets/${id}/healthcheck`);
        const idx = this.secrets.findIndex((s) => s.id === id);
        if (idx !== -1) {
          this.secrets[idx].last_check_status = res.data.status;
          this.secrets[idx].last_checked_at = res.data.last_checked_at;
        }
        await this.fetchDashboard(); // Update counts
        return res.data;
      } catch (err) {
        const errMsg = err.response?.data?.error || "Failed to execute healthcheck";
        throw new Error(errMsg);
      }
    },

    async runHealthcheckAll() {
      this.checkingAll = true;
      try {
        await api.post("/api/secrets/healthcheck-all");
        await this.fetchSecrets();
        await this.fetchDashboard();
      } catch (err) {
        this.error = err.response?.data?.error || "Failed to run batch healthcheck";
        throw err;
      } finally {
        this.checkingAll = false;
      }
    },
  },
});
