<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useSecretsStore } from "../stores/secrets";
import SecretRow from "../components/SecretRow.vue";
import SecretFormModal from "../components/SecretFormModal.vue";
import { 
  Search, Plus, RefreshCw, Loader2, Database, 
  HelpCircle, Tag, Filter, X 
} from "lucide-vue-next";

const route = useRoute();
const secretsStore = useSecretsStore();

const searchQuery = ref("");
const selectedTag = ref("");
const selectedFilter = ref("all"); // 'all', 'expired', 'expiring_soon', 'invalid', 'unchecked'

// Modal controls
const showModal = ref(false);
const editingSecret = ref(null);

onMounted(async () => {
  await secretsStore.fetchSecrets();
  
  // Set initial filter based on router query parameters (from Dashboard cards click-through)
  if (route.query.filter) {
    selectedFilter.value = route.query.filter;
  }
});

// Extract all unique tags across secrets for the filter dropdown
const allTags = computed(() => {
  const tagsSet = new Set();
  secretsStore.secrets.forEach((s) => {
    if (s.tags && Array.isArray(s.tags)) {
      s.tags.forEach((tag) => {
        if (tag.trim()) tagsSet.add(tag.trim());
      });
    }
  });
  return Array.from(tagsSet).sort();
});

// Filters implementation
const filteredSecrets = computed(() => {
  let list = secretsStore.secrets;
  
  // 1. Text Search Filter (Service name or Notes)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(
      (s) => 
        s.service_name.toLowerCase().includes(q) || 
        (s.notes && s.notes.toLowerCase().includes(q))
    );
  }
  
  // 2. Tag Filter
  if (selectedTag.value) {
    list = list.filter((s) => s.tags && s.tags.includes(selectedTag.value));
  }
  
  // 3. Status Filters (Expiry / Health)
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (selectedFilter.value === "expired") {
    list = list.filter((s) => {
      if (!s.expiry_date) return false;
      const exp = new Date(s.expiry_date);
      exp.setHours(0, 0, 0, 0);
      return exp.getTime() - today.getTime() < 0;
    });
  } else if (selectedFilter.value === "expiring_soon") {
    list = list.filter((s) => {
      if (!s.expiry_date) return false;
      const exp = new Date(s.expiry_date);
      exp.setHours(0, 0, 0, 0);
      const diffDays = Math.ceil((exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
      return diffDays >= 0 && diffDays <= 7;
    });
  } else if (selectedFilter.value === "invalid") {
    list = list.filter((s) => s.last_check_status === "invalid");
  } else if (selectedFilter.value === "unchecked") {
    list = list.filter((s) => s.healthcheck_url && s.last_check_status === "unchecked");
  }
  
  return list;
});

const handleAddClick = () => {
  editingSecret.value = null;
  showModal.value = true;
};

const handleEditClick = (secret) => {
  editingSecret.value = secret;
  showModal.value = true;
};

const handleDeleteClick = async (secret) => {
  if (confirm(`Are you sure you want to delete the secret for "${secret.service_name}"?`)) {
    try {
      await secretsStore.deleteSecret(secret.id);
    } catch (err) {
      alert("Failed to delete secret.");
    }
  }
};

const handleSaveSecret = async (payload) => {
  try {
    if (editingSecret.value) {
      await secretsStore.updateSecret(editingSecret.value.id, payload);
    } else {
      await secretsStore.createSecret(payload);
    }
    showModal.value = false;
    await secretsStore.fetchSecrets(); // Reload to get fresh masked keys
  } catch (err) {
    alert(err.message || "Failed to save secret.");
  }
};

const handleCheckAll = async () => {
  if (confirm("Run healthchecks for all keys? This might take a few seconds.")) {
    try {
      await secretsStore.runHealthcheckAll();
    } catch (err) {
      alert("Batch healthcheck failed.");
    }
  }
};

const clearFilters = () => {
  searchQuery.value = "";
  selectedTag.value = "";
  selectedFilter.value = "all";
};
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Top Action Bar Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight text-zinc-100 flex items-center space-x-2">
          <Database class="h-8 w-8 text-violet-500" />
          <span>Secrets Vault</span>
        </h1>
        <p class="text-sm text-zinc-400 mt-1">Manage, mask, copy, and run health connection checks on keys.</p>
      </div>

      <div class="flex items-center space-x-3">
        <!-- Check All Button -->
        <button
          @click="handleCheckAll"
          :disabled="secretsStore.checkingAll"
          class="flex items-center px-4 py-2.5 rounded-xl text-sm font-semibold bg-zinc-900 border border-white/5 hover:bg-zinc-800 text-zinc-300 transition-all disabled:opacity-50"
        >
          <Loader2 v-if="secretsStore.checkingAll" class="h-4 w-4 mr-2 animate-spin text-violet-400" />
          <RefreshCw v-else class="h-4 w-4 mr-2" />
          <span>Check All Health</span>
        </button>

        <!-- Add Secret Button -->
        <button
          @click="handleAddClick"
          class="flex items-center px-5 py-2.5 rounded-xl text-sm font-semibold btn-primary"
        >
          <Plus class="h-4 w-4 mr-1.5" />
          <span>Add Secret</span>
        </button>
      </div>
    </div>

    <!-- Search and Filters Panel -->
    <div class="glass-panel rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
      <!-- Search Input -->
      <div class="relative w-full md:flex-grow">
        <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-500">
          <Search class="h-4 w-4" />
        </div>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by service name or notes..."
          class="glass-input pl-10 pr-4 py-2.5 block w-full text-sm placeholder-zinc-500"
        />
      </div>

      <!-- Filters Row -->
      <div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
        <!-- Tag Filter -->
        <div class="flex items-center space-x-1.5 w-full sm:w-auto">
          <Tag class="h-4 w-4 text-zinc-500 flex-shrink-0" />
          <select
            v-model="selectedTag"
            class="glass-input px-3 py-2 text-xs bg-zinc-900 w-full sm:w-40"
          >
            <option value="">All Tags</option>
            <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div class="flex items-center space-x-1.5 w-full sm:w-auto">
          <Filter class="h-4 w-4 text-zinc-500 flex-shrink-0" />
          <select
            v-model="selectedFilter"
            class="glass-input px-3 py-2 text-xs bg-zinc-900 w-full sm:w-44"
          >
            <option value="all">All Statuses</option>
            <option value="expired">Expired Keys</option>
            <option value="expiring_soon">Expiring Soon (≤ 7d)</option>
            <option value="invalid">Invalid Health Status</option>
            <option value="unchecked">Unchecked Health</option>
          </select>
        </div>

        <!-- Clear Filters (if active) -->
        <button
          v-if="searchQuery || selectedTag || selectedFilter !== 'all'"
          @click="clearFilters"
          class="flex items-center text-xs text-red-400 hover:text-red-300 font-semibold px-2 py-2 rounded-lg hover:bg-red-500/10 transition-colors"
        >
          <X class="h-3 w-3 mr-1" />
          Clear
        </button>
      </div>
    </div>

    <!-- Secrets List Container -->
    <div class="space-y-4">
      <!-- Loading State Skeleton -->
      <div v-if="secretsStore.loading && secretsStore.secrets.length === 0" class="space-y-4">
        <div 
          v-for="i in 3" 
          :key="i"
          class="h-24 w-full rounded-2xl bg-zinc-900/30 border border-white/5 animate-pulse flex items-center justify-between px-6"
        >
          <div class="space-y-2 w-1/3">
            <div class="h-4 bg-zinc-800 rounded w-3/4"></div>
            <div class="h-3 bg-zinc-800 rounded w-1/2"></div>
          </div>
          <div class="h-10 bg-zinc-800 rounded w-1/4"></div>
          <div class="h-8 bg-zinc-800 rounded w-1/6"></div>
        </div>
      </div>

      <!-- Active List -->
      <div v-else-if="filteredSecrets.length > 0" class="space-y-3.5">
        <SecretRow
          v-for="secret in filteredSecrets"
          :key="secret.id"
          :secret="secret"
          @edit="handleEditClick(secret)"
          @delete="handleDeleteClick(secret)"
        />
      </div>

      <!-- Empty State -->
      <div 
        v-else 
        class="glass-panel rounded-3xl p-12 text-center border border-white/5 flex flex-col items-center justify-center space-y-4 max-w-lg mx-auto"
      >
        <div class="h-16 w-16 rounded-2xl bg-zinc-800/50 flex items-center justify-center text-zinc-500">
          <HelpCircle class="h-8 w-8" />
        </div>
        <div class="space-y-1">
          <h3 class="text-lg font-bold text-zinc-200">No Secrets Found</h3>
          <p class="text-sm text-zinc-500">
            {{ secretsStore.secrets.length === 0 ? "You haven't stored any secrets in this vault yet." : "No secrets match your active search filter settings." }}
          </p>
        </div>
        <button
          v-if="secretsStore.secrets.length > 0"
          @click="clearFilters"
          class="px-4 py-2 rounded-xl text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
        >
          Reset Filters
        </button>
        <button
          v-else
          @click="handleAddClick"
          class="px-5 py-2.5 rounded-xl text-xs font-semibold btn-primary"
        >
          Store Your First Secret
        </button>
      </div>
    </div>

    <!-- Modal Form Component -->
    <SecretFormModal
      :show="showModal"
      :edit-secret="editingSecret"
      @close="showModal = false"
      @save="handleSaveSecret"
    />
  </div>
</template>
