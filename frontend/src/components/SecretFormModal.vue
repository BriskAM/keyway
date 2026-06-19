<script setup>
import { ref, watch, computed } from "vue";
import api from "../api/axios";
import { X, Eye, EyeOff, Loader2, Play, CheckCircle2, XCircle } from "lucide-vue-next";

const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  editSecret: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["close", "save"]);

const isEdit = computed(() => !!props.editSecret);

const serviceName = ref("");
const secretValue = ref("");
const notes = ref("");
const tagsString = ref("");
const expiryDate = ref("");

// Healthcheck configs
const enableHealthcheck = ref(false);
const healthcheckUrl = ref("");
const healthcheckMethod = ref("GET");
const healthcheckAuthStyle = ref("bearer");
const healthcheckAuthField = ref("");

// Testing and loading states
const saving = ref(false);
const testingConnection = ref(false);
const testResult = ref(null); // { status: 'valid'|'invalid'|'error', message?: string }
const showPassword = ref(false);

const resetForm = () => {
  serviceName.value = "";
  secretValue.value = "";
  notes.value = "";
  tagsString.value = "";
  expiryDate.value = "";
  
  enableHealthcheck.value = false;
  healthcheckUrl.value = "";
  healthcheckMethod.value = "GET";
  healthcheckAuthStyle.value = "bearer";
  healthcheckAuthField.value = "";
  
  testResult.value = null;
  showPassword.value = false;
};

// Sync fields when editing
watch(
  () => props.editSecret,
  (newVal) => {
    if (newVal) {
      serviceName.value = newVal.service_name || "";
      secretValue.value = ""; // Leave blank in edit mode unless they want to overwrite
      notes.value = newVal.notes || "";
      tagsString.value = newVal.tags ? newVal.tags.join(", ") : "";
      expiryDate.value = newVal.expiry_date || "";
      
      if (newVal.healthcheck_url) {
        enableHealthcheck.value = true;
        healthcheckUrl.value = newVal.healthcheck_url || "";
        healthcheckMethod.value = newVal.healthcheck_method || "GET";
        healthcheckAuthStyle.value = newVal.healthcheck_auth_style || "bearer";
        healthcheckAuthField.value = newVal.healthcheck_auth_field || "";
      } else {
        enableHealthcheck.value = false;
        healthcheckUrl.value = "";
        healthcheckMethod.value = "GET";
        healthcheckAuthStyle.value = "bearer";
        healthcheckAuthField.value = "";
      }
    } else {
      resetForm();
    }
  },
  { immediate: true }
);

const handleClose = () => {
  resetForm();
  emit("close");
};

const handleTestConnection = async () => {
  if (!healthcheckUrl.value) {
    testResult.value = { status: "error", message: "Healthcheck URL is required for testing" };
    return;
  }
  
  // In edit mode, if secretValue is empty, we must tell the backend to use the saved encrypted value
  if (isEdit.value && !secretValue.value) {
    testResult.value = { 
      status: "error", 
      message: "Please re-type the secret value to test the connection (for security, saved keys cannot be tested without confirmation)." 
    };
    return;
  }
  
  if (!secretValue.value) {
    testResult.value = { status: "error", message: "Secret value is required for testing" };
    return;
  }

  testingConnection.value = true;
  testResult.value = null;
  
  try {
    const res = await api.post("/api/secrets/test-healthcheck", {
      healthcheck_url: healthcheckUrl.value,
      healthcheck_method: healthcheckMethod.value,
      healthcheck_auth_style: healthcheckAuthStyle.value,
      healthcheck_auth_field: healthcheckAuthField.value,
      value: secretValue.value,
    });
    
    testResult.value = {
      status: res.data.status,
      message: res.data.status === "valid" 
        ? "Connected successfully! Key is active." 
        : `Verification failed: HTTP Status ${res.data.http_status || 'Unknown'}`,
    };
  } catch (err) {
    testResult.value = {
      status: "error",
      message: err.response?.data?.error || "Could not connect to healthcheck endpoint.",
    };
  } finally {
    testingConnection.value = false;
  }
};

const handleSave = async () => {
  if (!serviceName.value) return;
  if (!isEdit.value && !secretValue.value) return;
  
  saving.value = true;
  
  const payload = {
    service_name: serviceName.value,
    notes: notes.value || null,
    tags: tagsString.value ? tagsString.value.split(",").map(t => t.trim()).filter(Boolean) : [],
    expiry_date: expiryDate.value || null,
    healthcheck_url: enableHealthcheck.value ? healthcheckUrl.value : null,
    healthcheck_method: enableHealthcheck.value ? healthcheckMethod.value : "GET",
    healthcheck_auth_style: enableHealthcheck.value ? healthcheckAuthStyle.value : "none",
    healthcheck_auth_field: enableHealthcheck.value ? healthcheckAuthField.value : null,
  };
  
  // Only append value if entered
  if (secretValue.value) {
    payload.value = secretValue.value;
  }

  try {
    emit("save", payload);
    resetForm();
  } catch (err) {
    console.error("Save error", err);
  } finally {
    saving.value = false;
  }
};
</script>

<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
  >
    <div 
      class="max-w-2xl w-full glass-panel rounded-3xl p-6 md:p-8 flex flex-col max-h-[90vh] overflow-y-auto relative animate-fade-in"
    >
      <!-- Close Button -->
      <button 
        @click="handleClose"
        class="absolute top-4 right-4 p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-colors"
      >
        <X class="h-5 w-5" />
      </button>

      <!-- Header -->
      <h2 class="text-2xl font-bold mb-6 text-zinc-100">
        {{ isEdit ? `Edit ${editSecret.service_name}` : "Add New Secret" }}
      </h2>

      <!-- Form Inputs -->
      <div class="space-y-4">
        <!-- Service Name -->
        <div>
          <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Service Name</label>
          <input 
            v-model="serviceName"
            type="text" 
            placeholder="e.g. Stripe Prod, SendGrid Key"
            class="glass-input px-4 py-3 block w-full text-sm"
          />
        </div>

        <!-- Secret Value -->
        <div>
          <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
            Secret Value
            <span v-if="isEdit" class="text-[10px] text-zinc-500 lowercase">(leave blank to keep unchanged)</span>
          </label>
          <div class="relative">
            <input 
              v-model="secretValue"
              :type="showPassword ? 'text' : 'password'"
              placeholder="e.g. sk_live_••••••••••••"
              class="glass-input pl-4 pr-10 py-3 block w-full text-sm"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <EyeOff v-if="showPassword" class="h-4 w-4" />
              <Eye v-else class="h-4 w-4" />
            </button>
          </div>
        </div>

        <!-- Notes -->
        <div>
          <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Notes</label>
          <textarea 
            v-model="notes"
            rows="2"
            placeholder="Optional context about where this key is used..."
            class="glass-input px-4 py-3 block w-full text-sm resize-none"
          ></textarea>
        </div>

        <!-- Tags and Expiry Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Tags -->
          <div>
            <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Tags</label>
            <input 
              v-model="tagsString"
              type="text" 
              placeholder="comma-separated (e.g. prod, finance)"
              class="glass-input px-4 py-3 block w-full text-sm"
            />
          </div>

          <!-- Expiry Date -->
          <div>
            <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Expiry Date</label>
            <input 
              v-model="expiryDate"
              type="date" 
              class="glass-input px-4 py-3 block w-full text-sm"
            />
          </div>
        </div>

        <!-- Collapsible Healthcheck Config -->
        <div class="border-t border-white/5 pt-4">
          <div class="flex items-center justify-between mb-4">
            <div class="flex flex-col">
              <span class="text-sm font-semibold text-zinc-300">Enable Health Check</span>
              <span class="text-xs text-zinc-500">Keyway will test this credentials status against a URL</span>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="enableHealthcheck" class="sr-only peer" />
              <div class="w-11 h-6 bg-zinc-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-zinc-400 after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-violet-600 peer-checked:after:bg-white"></div>
            </label>
          </div>

          <!-- Healthcheck Form Fields -->
          <div v-if="enableHealthcheck" class="space-y-4 p-4 rounded-2xl bg-black/40 border border-white/5 animate-fade-in">
            <!-- Healthcheck URL -->
            <div>
              <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Endpoint URL</label>
              <input 
                v-model="healthcheckUrl"
                type="url" 
                placeholder="https://api.stripe.com/v1/charges"
                class="glass-input px-4 py-3 block w-full text-sm"
              />
            </div>

            <!-- Healthcheck Method & Auth Style -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Method</label>
                <select 
                  v-model="healthcheckMethod"
                  class="glass-input px-4 py-3 block w-full text-sm bg-zinc-900"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="HEAD">HEAD</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Auth Style</label>
                <select 
                  v-model="healthcheckAuthStyle"
                  class="glass-input px-4 py-3 block w-full text-sm bg-zinc-900"
                >
                  <option value="bearer">Bearer Token</option>
                  <option value="header">Custom Header</option>
                  <option value="query_param">Query Parameter</option>
                  <option value="none">No Auth</option>
                </select>
              </div>

              <!-- Auth Field Name (Custom Header / Query Param) -->
              <div v-if="healthcheckAuthStyle === 'header' || healthcheckAuthStyle === 'query_param'">
                <label class="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Field Name</label>
                <input 
                  v-model="healthcheckAuthField"
                  type="text" 
                  :placeholder="healthcheckAuthStyle === 'header' ? 'e.g. x-api-key' : 'e.g. api_token'"
                  class="glass-input px-4 py-3 block w-full text-sm"
                />
              </div>
            </div>

            <!-- Connection Test panel -->
            <div class="border-t border-white/5 pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <button
                type="button"
                @click="handleTestConnection"
                :disabled="testingConnection"
                class="flex items-center px-4 py-2 rounded-xl text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-white/5 transition-all disabled:opacity-40"
              >
                <Loader2 v-if="testingConnection" class="h-3.5 w-3.5 mr-2 animate-spin text-violet-400" />
                <Play v-else class="h-3.5 w-3.5 mr-2 text-violet-400" />
                Test Connection
              </button>

              <!-- Connection test result banner -->
              <div 
                v-if="testResult" 
                class="flex items-center space-x-2 text-xs font-medium"
                :class="testResult.status === 'valid' ? 'text-emerald-400' : 'text-rose-400'"
              >
                <CheckCircle2 v-if="testResult.status === 'valid'" class="h-4 w-4" />
                <XCircle v-else class="h-4 w-4" />
                <span>{{ testResult.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="mt-8 flex items-center justify-end space-x-4 border-t border-white/5 pt-5">
        <button 
          @click="handleClose"
          class="px-5 py-2.5 rounded-xl text-sm font-semibold text-zinc-400 hover:text-zinc-200 hover:bg-white/5 transition-all"
        >
          Cancel
        </button>
        <button 
          @click="handleSave"
          :disabled="saving || !serviceName || (!isEdit && !secretValue)"
          class="px-6 py-2.5 rounded-xl text-sm font-semibold btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="saving" class="h-4 w-4 animate-spin" />
          <span v-else>{{ isEdit ? "Save Changes" : "Add Secret" }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
