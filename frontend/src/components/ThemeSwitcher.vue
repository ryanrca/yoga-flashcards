<template>
  <q-btn-dropdown
    flat
    dense
    no-caps
    icon="palette"
    :label="$q.screen.gt.sm ? currentLabel : ''"
    aria-label="Change theme"
    content-class="user-dropdown-menu"
  >
    <q-list style="min-width: 240px;">
      <q-item
        v-for="option in themes"
        :key="option.id"
        v-close-popup
        clickable
        :active="option.id === theme"
        @click="setTheme(option.id)"
      >
        <q-item-section>
          <q-item-label>{{ option.label }}</q-item-label>
          <q-item-label caption>{{ option.blurb }}</q-item-label>
        </q-item-section>
        <q-item-section v-if="option.id === theme" side>
          <q-icon name="check" color="primary" />
        </q-item-section>
      </q-item>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'src/composables/useTheme'

const { theme, themes, setTheme } = useTheme()

const currentLabel = computed(
  () => themes.find((t) => t.id === theme.value)?.label || ''
)
</script>
