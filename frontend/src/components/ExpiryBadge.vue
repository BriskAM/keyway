<script setup>
import { computed } from "vue";
import { Calendar, AlertCircle, Clock } from "lucide-vue-next";

const props = defineProps({
  expiryDate: {
    type: String,
    default: null,
  },
});

const expiryInfo = computed(() => {
  if (!props.expiryDate) {
    return {
      style: "bg-zinc-500/10 border-zinc-500/10 text-zinc-500",
      text: "No Expiry",
      icon: Clock,
    };
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const expiry = new Date(props.expiryDate);
  expiry.setHours(0, 0, 0, 0);

  const diffTime = expiry.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return {
      style: "bg-red-500/10 border-red-500/20 text-red-400 font-semibold",
      text: `Expired ${Math.abs(diffDays)}d ago`,
      icon: AlertCircle,
    };
  } else if (diffDays === 0) {
    return {
      style: "bg-amber-500/10 border-amber-500/20 text-amber-400 font-semibold",
      text: "Expires Today",
      icon: AlertCircle,
    };
  } else if (diffDays === 1) {
    return {
      style: "bg-amber-500/10 border-amber-500/20 text-amber-400",
      text: "Expires Tomorrow",
      icon: AlertCircle,
    };
  } else if (diffDays <= 7) {
    return {
      style: "bg-amber-500/10 border-amber-500/20 text-amber-400",
      text: `Expires in ${diffDays}d`,
      icon: AlertCircle,
    };
  } else {
    // Format date nicely
    const options = { year: "numeric", month: "short", day: "numeric" };
    const formattedDate = expiry.toLocaleDateString(undefined, options);
    return {
      style: "bg-emerald-500/10 border-emerald-500/10 text-emerald-400",
      text: `Expires ${formattedDate}`,
      icon: Calendar,
    };
  }
});
</script>

<template>
  <div 
    class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors duration-300"
    :class="expiryInfo.style"
  >
    <component :is="expiryInfo.icon" class="h-3 w-3" />
    <span>{{ expiryInfo.text }}</span>
  </div>
</template>
