import axios from "axios";

const instance = axios.create({
  // Fallback to localhost:5000 if VITE_API_BASE_URL is not set
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000",
  withCredentials: true, // Required for Flask session cookies
  headers: {
    "Content-Type": "application/json",
  },
});

export default instance;
