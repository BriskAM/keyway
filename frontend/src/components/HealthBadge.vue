<script setup>
import { computed } from "vue";
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle } from "@lucide/vue";

const props = defineProps({
  status: {
    type: String,
    default: "unchecked",
  },
  lastChecked: {
    type: String,
    default: null,
  },
});

const formattedTime = computed(() => {
  if (!props.lastChecked) return "Never checked";
  try {
    const d = new Date(props.lastChecked);
    return d.toLocaleString();
  } catch (e) {
    return props.lastChecked;
  }
});

const config = computed(() => {
  switch (props.status) {
    case "valid":
      return {
        bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
        dot: "bg-emerald-400 shadow-emerald-400/50",
        icon: CheckCircle2,
        label: "Valid",
      };
    case "invalid":
      return {
        bg: "bg-rose-500/10 border-rose-500/20 text-rose-400",
        dot: "bg-rose-400 shadow-rose-400/50",
        icon: XCircle,
        label: "Invalid",
      };
    case "error":
      return {
        bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
        dot: "bg-amber-400 shadow-amber-400/50",
        icon: AlertTriangle,
        label: "Error",
      };
    default:
      return {
        bg: "bg-zinc-500/10 border-zinc-500/20 text-zinc-400",
        dot: "bg-zinc-400 shadow-zinc-400/50",
        icon: HelpCircle,
        label: "Unchecked",
      };
  }
});
</script>

<template>
  <div 
    class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border relative group cursor-help transition-all duration-300"
    :class="config.bg"
  >
    <span class="relative flex h-2 w-2">
      <span 
        class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
        :class="status === 'unchecked' ? '' : config.dot"
      ></span>
      <span class="relative inline-flex rounded-full h-2 w-2" :class="config.dot"></span>
    </span>
    <span>{{ config.label }}</span>
    
    <!-- Hover Tooltip -->
    <div 
      class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block z-50 bg-zinc-900 border border-white/10 text-zinc-300 text-[10px] px-2.5 py-1.5 rounded-lg shadow-xl whitespace-nowrap"
    >
      Checked: {{ formattedTime }}
    </div>
  </div>
</template>
