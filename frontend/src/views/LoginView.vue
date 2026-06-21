<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { Key, Mail, Lock, Eye, EyeOff, Loader2, ArrowRight } from "@lucide/vue";

const authStore = useAuthStore();
const router = useRouter();

const isLogin = ref(true);
const email = ref("");
const password = ref("");
const showPassword = ref(false);
const errorMsg = ref("");
const formLoading = ref(false);

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  errorMsg.value = "";
};

const togglePassword = () => {
  showPassword.value = !showPassword.value;
};

const handleSubmit = async () => {
  if (!email.value || !password.value) {
    errorMsg.value = "Please fill in all fields.";
    return;
  }
  
  errorMsg.value = "";
  formLoading.value = true;
  
  try {
    if (isLogin.value) {
      await authStore.login(email.value, password.value);
    } else {
      await authStore.signup(email.value, password.value);
    }
    router.push({ name: "vault" });
  } catch (err) {
    errorMsg.value = authStore.error || "Authentication failed. Please check inputs.";
  } finally {
    formLoading.value = false;
  }
};
</script>

<template>
  <div class="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 glass-panel p-8 rounded-3xl animate-fade-in relative overflow-hidden">
      <!-- Ambient Glow behind Card -->
      <div class="absolute -top-10 -right-10 w-40 h-40 bg-violet-600/20 rounded-full filter blur-3xl -z-10"></div>
      <div class="absolute -bottom-10 -left-10 w-40 h-40 bg-indigo-600/20 rounded-full filter blur-3xl -z-10"></div>

      <!-- Card Header -->
      <div class="text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-lg shadow-violet-500/20">
          <Key class="h-6 w-6" />
        </div>
        <h2 class="mt-6 text-3xl font-extrabold tracking-tight">
          {{ isLogin ? "Welcome back" : "Create your vault" }}
        </h2>
        <p class="mt-2 text-sm text-zinc-400">
          {{ isLogin ? "Access your encrypted keys and tokens" : "Get started with self-hosted secrets tracking" }}
        </p>
      </div>

      <!-- Form -->
      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <!-- Error alert -->
        <div 
          v-if="errorMsg" 
          class="p-3 rounded-lg border border-red-500/20 bg-red-500/10 text-red-400 text-sm text-center font-medium"
        >
          {{ errorMsg }}
        </div>

        <div class="space-y-4">
          <!-- Email Input -->
          <div>
            <label for="email-address" class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Email address</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                <Mail class="h-4 w-4" />
              </div>
              <input
                id="email-address"
                name="email"
                type="email"
                autocomplete="email"
                required
                v-model="email"
                placeholder="developer@keyway.dev"
                class="glass-input pl-10 pr-4 py-3 block w-full text-sm placeholder-zinc-600"
              />
            </div>
          </div>

          <!-- Password Input -->
          <div>
            <label for="password" class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Password</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
                <Lock class="h-4 w-4" />
              </div>
              <input
                id="password"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                v-model="password"
                placeholder="••••••••••••"
                class="glass-input pl-10 pr-10 py-3 block w-full text-sm placeholder-zinc-600"
              />
              <button
                type="button"
                @click="togglePassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div>
          <button
            type="submit"
            :disabled="formLoading"
            class="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl text-sm font-semibold btn-primary focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <Loader2 v-if="formLoading" class="mr-2 h-4 w-4 animate-spin" />
            <span v-else class="flex items-center">
              {{ isLogin ? "Unlock Vault" : "Create Vault" }}
              <ArrowRight class="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </button>
        </div>
      </form>

      <!-- Toggle mode links -->
      <div class="text-center pt-2">
        <button
          type="button"
          @click="toggleMode"
          class="text-sm font-medium text-violet-400 hover:text-violet-300 transition-colors"
        >
          {{ isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in" }}
        </button>
      </div>
    </div>
  </div>
</template>
