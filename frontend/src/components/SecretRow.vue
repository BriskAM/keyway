<script setup>
import { ref, onUnmounted } from "vue";
import { useSecretsStore } from "../stores/secrets";
import HealthBadge from "./HealthBadge.vue";
import ExpiryBadge from "./ExpiryBadge.vue";
import { 
  Eye, EyeOff, Clipboard, Check, RefreshCw, 
  Trash2, Edit3, Loader2, KeyRound 
} from "@lucide/vue";

const props = defineProps({
  secret: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["edit", "delete"]);

const secretsStore = useSecretsStore();
const revealedValue = ref(null);
const countdown = ref(0);
const copied = ref(false);
const checkingHealth = ref(false);
let countdownInterval = null;

const startCountdown = () => {
  countdown.value = 10;
  clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      maskSecret();
    }
  }, 1000);
};

const maskSecret = () => {
  revealedValue.value = null;
  countdown.value = 0;
  clearInterval(countdownInterval);
};

const handleReveal = async () => {
  if (revealedValue.value) {
    maskSecret();
    return;
  }
  
  try {
    const rawVal = await secretsStore.revealSecret(props.secret.id);
    revealedValue.value = rawVal;
    startCountdown();
  } catch (err) {
    console.error("Reveal error", err);
  }
};

const handleCopy = async () => {
  try {
    let copyText = revealedValue.value;
    if (!copyText) {
      // Fetch silently if not revealed
      copyText = await secretsStore.revealSecret(props.secret.id);
    }
    
    await navigator.clipboard.writeText(copyText);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error("Clipboard copy failed", err);
  }
};

const handleHealthcheck = async () => {
  checkingHealth.value = true;
  try {
    await secretsStore.runHealthcheck(props.secret.id);
  } catch (err) {
    alert(err.message);
  } finally {
    checkingHealth.value = false;
  }
};

onUnmounted(() => {
  clearInterval(countdownInterval);
});
</script>

<template>
  <div 
    class="glass-panel rounded-2xl p-5 border border-white/5 bg-zinc-900/40 hover:bg-zinc-900/60 transition-all duration-300 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in relative overflow-hidden"
  >
    <!-- Left Area: Service & Metadata -->
    <div class="flex-grow space-y-2 max-w-full md:max-w-[50%]">
      <div class="flex items-center space-x-2">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-800 text-zinc-400">
          <KeyRound class="h-4 w-4" />
        </div>
        <h3 class="font-bold text-lg text-zinc-100 truncate">{{ secret.service_name }}</h3>
      </div>
      
      <!-- Notes -->
      <p v-if="secret.notes" class="text-xs text-zinc-400 line-clamp-2">{{ secret.notes }}</p>
      
      <!-- Tags -->
      <div v-if="secret.tags && secret.tags.length > 0" class="flex flex-wrap gap-1.5 pt-1">
        <span 
          v-for="tag in secret.tags" 
          :key="tag" 
          class="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/20"
        >
          {{ tag }}
        </span>
      </div>
    </div>

    <!-- Center Area: Secret Value Container -->
    <div class="flex items-center space-x-2 md:justify-center flex-grow">
      <div class="glass-card rounded-xl px-4 py-2.5 flex items-center justify-between space-x-3 w-full md:max-w-[280px]">
        <span 
          class="font-mono-key truncate select-all"
          :class="revealedValue ? 'text-violet-300 font-medium' : 'text-zinc-500'"
        >
          {{ revealedValue || secret.masked_value }}
        </span>
        
        <!-- Countdown Pill -->
        <span 
          v-if="countdown > 0"
          class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-violet-600 text-white animate-pulse"
        >
          {{ countdown }}s
        </span>
      </div>
    </div>

    <!-- Right Area: Status and Actions -->
    <div class="flex flex-wrap items-center gap-3 justify-end md:flex-nowrap">
      <!-- Status Badges -->
      <div class="flex flex-row items-center gap-2">
        <ExpiryBadge :expiry-date="secret.expiry_date" />
        <HealthBadge 
          v-if="secret.healthcheck_url" 
          :status="secret.last_check_status" 
          :last-checked="secret.last_checked_at" 
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-1.5 border-l border-white/10 pl-3">
        <!-- Reveal/Mask Toggle -->
        <button
          @click="handleReveal"
          class="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all"
          :title="revealedValue ? 'Mask Secret' : 'Reveal Secret'"
        >
          <EyeOff v-if="revealedValue" class="h-4 w-4 text-violet-400" />
          <Eye v-else class="h-4 w-4" />
        </button>

        <!-- Copy Clipboard -->
        <button
          @click="handleCopy"
          class="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all relative"
          :class="{ 'text-emerald-400': copied }"
          title="Copy Value"
        >
          <Check v-if="copied" class="h-4 w-4" />
          <Clipboard v-else class="h-4 w-4" />
        </button>

        <!-- Trigger Health Check -->
        <button
          v-if="secret.healthcheck_url"
          @click="handleHealthcheck"
          :disabled="checkingHealth"
          class="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all disabled:opacity-40"
          title="Verify Key Health"
        >
          <Loader2 v-if="checkingHealth" class="h-4 w-4 animate-spin text-violet-400" />
          <RefreshCw v-else class="h-4 w-4" />
        </button>

        <!-- Edit Button -->
        <button
          @click="emit('edit')"
          class="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all"
          title="Edit Details"
        >
          <Edit3 class="h-4 w-4" />
        </button>

        <!-- Delete Button -->
        <button
          @click="emit('delete')"
          class="p-2 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
          title="Delete Secret"
        >
          <Trash2 class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
</template>
