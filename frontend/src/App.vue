<script setup>
import { RouterView, RouterLink, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";
import { Key, LayoutDashboard, Database, LogOut, ShieldAlert } from "@lucide/vue";

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = async () => {
  await authStore.logout();
  router.push({ name: "login" });
};
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Header Navigation -->
    <header 
      v-if="authStore.isAuthenticated" 
      class="sticky top-0 z-40 w-full border-b border-white/10 bg-black/60 backdrop-blur-md transition-all duration-300"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo and Title -->
        <div class="flex items-center space-x-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600/10 border border-violet-500/20 text-violet-400">
            <Key class="h-5 w-5" />
          </div>
          <span class="text-xl font-bold tracking-tight text-gradient">Keyway</span>
        </div>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <RouterLink
            :to="{ name: 'dashboard' }"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="$route.name === 'dashboard' ? 'bg-white/5 text-violet-400 border border-white/5' : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'"
          >
            <div class="flex items-center space-x-2">
              <LayoutDashboard class="h-4 w-4" />
              <span>Dashboard</span>
            </div>
          </RouterLink>
          <RouterLink
            :to="{ name: 'vault' }"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="$route.name === 'vault' ? 'bg-white/5 text-violet-400 border border-white/5' : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'"
          >
            <div class="flex items-center space-x-2">
              <Database class="h-4 w-4" />
              <span>Vault</span>
            </div>
          </RouterLink>
        </nav>

        <!-- User Controls -->
        <div class="flex items-center space-x-4">
          <div class="hidden sm:flex flex-col text-right">
            <span class="text-xs text-zinc-500 font-medium">Logged in as</span>
            <span class="text-sm text-zinc-300 font-semibold max-w-[180px] truncate">{{ authStore.user?.email }}</span>
          </div>
          
          <button
            @click="handleLogout"
            class="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium text-zinc-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all duration-200"
            title="Log Out"
          >
            <LogOut class="h-4 w-4" />
            <span class="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Session Warning if encryption key is missing -->
      <div 
        v-if="authStore.isAuthenticated && !authStore.hasKey" 
        class="mb-6 p-4 rounded-xl border border-amber-500/20 bg-amber-500/10 text-amber-300 flex items-start space-x-3"
      >
        <ShieldAlert class="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div>
          <h4 class="font-semibold text-sm">Session Decryption Key Missing</h4>
          <p class="text-xs text-amber-400/90 mt-1">
            Your encryption key could not be recovered. This happens if the server restarted or your session expired. 
            Please log out and log back in to restore full encryption and decryption.
          </p>
        </div>
      </div>

      <RouterView />
    </main>

    <!-- Simple Footer -->
    <footer class="border-t border-white/5 py-6 bg-black/20 text-center text-xs text-zinc-600">
      <p>© 2026 Keyway. All values are encrypted at rest using PBKDF2-HMAC key derivation.</p>
    </footer>
  </div>
</template>

<style>
/* Additional grid layouts for premium responsive spacing */
.flex-grow {
  animation: fadeIn 0.3s ease-out;
}
</style>
