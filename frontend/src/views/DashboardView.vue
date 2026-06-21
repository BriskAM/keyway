<script setup>
import { onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useSecretsStore } from "../stores/secrets";
import { 
  AlertOctagon, AlertTriangle, XOctagon, HelpCircle, 
  ArrowRight, KeyRound, ExternalLink, CalendarDays, RefreshCw 
} from "@lucide/vue";

const secretsStore = useSecretsStore();
const router = useRouter();

onMounted(async () => {
  await secretsStore.fetchDashboard();
});

const cards = computed(() => {
  const data = secretsStore.dashboardData;
  return [
    {
      id: "expired",
      title: "Expired Keys",
      count: data.expired ? data.expired.length : 0,
      description: "Keys that have passed their expiration date.",
      color: "from-red-500/20 border-red-500/20 text-red-400 hover:border-red-500/40 hover:shadow-red-500/10",
      dot: "bg-red-400",
      icon: XOctagon,
      items: data.expired || [],
    },
    {
      id: "expiring_soon",
      title: "Expiring Soon",
      count: data.expiring_soon ? data.expiring_soon.length : 0,
      description: "Keys expiring within the next 7 days.",
      color: "from-amber-500/20 border-amber-500/20 text-amber-400 hover:border-amber-500/40 hover:shadow-amber-500/10",
      dot: "bg-amber-400",
      icon: AlertTriangle,
      items: data.expiring_soon || [],
    },
    {
      id: "invalid",
      title: "Invalid Keys",
      count: data.invalid_keys ? data.invalid_keys.length : 0,
      description: "Keys that failed the healthcheck request.",
      color: "from-rose-500/20 border-rose-500/20 text-rose-400 hover:border-rose-500/40 hover:shadow-rose-500/10",
      dot: "bg-rose-400",
      icon: AlertOctagon,
      items: data.invalid_keys || [],
    },
    {
      id: "unchecked",
      title: "Unchecked Health",
      count: data.unchecked ? data.unchecked.length : 0,
      description: "Keys with health URL but never checked.",
      color: "from-zinc-500/20 border-zinc-500/20 text-zinc-400 hover:border-zinc-500/40 hover:shadow-zinc-500/10",
      dot: "bg-zinc-400",
      icon: HelpCircle,
      items: data.unchecked || [],
    },
  ];
});

const navigateToFilteredVault = (filterId) => {
  router.push({ name: "vault", query: { filter: filterId } });
};

const hasUrgentIssues = computed(() => {
  const data = secretsStore.dashboardData;
  return (
    (data.expired?.length || 0) > 0 ||
    (data.expiring_soon?.length || 0) > 0 ||
    (data.invalid_keys?.length || 0) > 0
  );
});
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-zinc-100 flex items-center space-x-2">
        <LayoutDashboard class="h-8 w-8 text-violet-500" />
        <span>Vault Health Dashboard</span>
      </h1>
      <p class="text-sm text-zinc-400 mt-1">
        Overview of secrets requiring validation, renewal, or security check actions.
      </p>
    </div>

    <!-- Summary Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="card in cards"
        :key="card.id"
        @click="navigateToFilteredVault(card.id)"
        class="glass-panel p-6 rounded-3xl cursor-pointer bg-gradient-to-b to-zinc-900/40 border transition-all duration-300 flex flex-col justify-between group relative overflow-hidden h-48"
        :class="card.color"
      >
        <!-- Card background subtle glow -->
        <div class="absolute -top-12 -right-12 w-24 h-24 rounded-full bg-white/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 filter blur-xl"></div>
        
        <div>
          <!-- Header and Icon -->
          <div class="flex items-center justify-between">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-inherit border border-white/5">
              <component :is="card.icon" class="h-5 w-5" />
            </div>
            <span class="text-3xl font-black tracking-tight">{{ card.count }}</span>
          </div>
          
          <h3 class="text-lg font-bold mt-4 text-zinc-100">{{ card.title }}</h3>
          <p class="text-xs text-zinc-500 mt-1 leading-relaxed">{{ card.description }}</p>
        </div>

        <div class="flex items-center text-xs font-semibold mt-4 text-inherit group-hover:translate-x-0.5 transition-transform duration-200">
          <span>Inspect Keys</span>
          <ArrowRight class="h-3.5 w-3.5 ml-1.5" />
        </div>
      </div>
    </div>

    <!-- Urgent Action Lists Section -->
    <div class="space-y-6">
      <h2 class="text-xl font-bold text-zinc-200 flex items-center space-x-2">
        <CalendarDays class="h-5 w-5 text-violet-400" />
        <span>Urgent Action Required</span>
      </h2>

      <!-- Safe State -->
      <div 
        v-if="!hasUrgentIssues"
        class="glass-panel rounded-3xl p-10 text-center border border-white/5 max-w-lg mx-auto flex flex-col items-center justify-center space-y-4"
      >
        <div class="h-16 w-16 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
          <CheckCircle2 class="h-8 w-8" />
        </div>
        <div>
          <h3 class="text-lg font-bold text-zinc-200">Your Vault is Secure</h3>
          <p class="text-sm text-zinc-500 mt-1">
            No keys are expired, expiring this week, or showing invalid connection status!
          </p>
        </div>
        <button
          @click="$router.push({ name: 'vault' })"
          class="px-5 py-2.5 rounded-xl text-xs font-semibold btn-primary"
        >
          View All Secrets
        </button>
      </div>

      <!-- Action Items Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Expired / Expiring soon list panel -->
        <div 
          v-if="secretsStore.dashboardData.expired?.length || secretsStore.dashboardData.expiring_soon?.length"
          class="glass-panel rounded-3xl p-6 border border-white/5 bg-zinc-900/20"
        >
          <div class="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
            <h3 class="font-bold text-base text-zinc-300">Expiration Warnings</h3>
            <button 
              @click="navigateToFilteredVault('expired')"
              class="text-xs text-violet-400 hover:text-violet-300 flex items-center font-semibold"
            >
              <span>Manage</span>
              <ExternalLink class="h-3 w-3 ml-1" />
            </button>
          </div>

          <div class="space-y-3 max-h-[300px] overflow-y-auto pr-1">
            <!-- Expired -->
            <div 
              v-for="sec in secretsStore.dashboardData.expired" 
              :key="sec.id" 
              class="flex items-center justify-between p-3 rounded-xl bg-red-500/5 border border-red-500/15"
            >
              <div class="flex items-center space-x-2.5 truncate">
                <KeyRound class="h-4 w-4 text-red-400 flex-shrink-0" />
                <span class="text-sm text-zinc-200 font-semibold truncate">{{ sec.service_name }}</span>
              </div>
              <span class="text-xs text-red-400 bg-red-500/10 px-2.5 py-0.5 rounded-full font-bold">Expired</span>
            </div>

            <!-- Expiring Soon -->
            <div 
              v-for="sec in secretsStore.dashboardData.expiring_soon" 
              :key="sec.id" 
              class="flex items-center justify-between p-3 rounded-xl bg-amber-500/5 border border-amber-500/15"
            >
              <div class="flex items-center space-x-2.5 truncate">
                <KeyRound class="h-4 w-4 text-amber-400 flex-shrink-0" />
                <span class="text-sm text-zinc-200 font-semibold truncate">{{ sec.service_name }}</span>
              </div>
              <span class="text-xs text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full font-medium">Expires Soon</span>
            </div>
          </div>
        </div>

        <!-- Invalid health status list panel -->
        <div 
          v-if="secretsStore.dashboardData.invalid_keys?.length"
          class="glass-panel rounded-3xl p-6 border border-white/5 bg-zinc-900/20"
        >
          <div class="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
            <h3 class="font-bold text-base text-zinc-300">Invalid Connection Status</h3>
            <button 
              @click="navigateToFilteredVault('invalid')"
              class="text-xs text-violet-400 hover:text-violet-300 flex items-center font-semibold"
            >
              <span>Verify</span>
              <ExternalLink class="h-3 w-3 ml-1" />
            </button>
          </div>

          <div class="space-y-3 max-h-[300px] overflow-y-auto pr-1">
            <div 
              v-for="sec in secretsStore.dashboardData.invalid_keys" 
              :key="sec.id" 
              class="flex items-center justify-between p-3 rounded-xl bg-rose-500/5 border border-rose-500/15"
            >
              <div class="flex items-center space-x-2.5 truncate">
                <RefreshCw class="h-4 w-4 text-rose-400 flex-shrink-0 animate-pulse" />
                <div class="flex flex-col truncate">
                  <span class="text-sm text-zinc-200 font-semibold truncate">{{ sec.service_name }}</span>
                  <span class="text-[10px] text-zinc-500 truncate">{{ sec.healthcheck_url }}</span>
                </div>
              </div>
              <span class="text-xs text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full font-bold">Failed Check</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
