<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="psychedelic-header">
      <q-toolbar>
        <q-toolbar-title class="psychedelic-title">
          <div class="row items-center no-wrap">
            <q-icon name="self_improvement" size="md" class="q-mr-sm glow-icon" />
            <div class="text-h4 neon-glow" style="font-family: 'Cinzel Decorative', serif; font-weight: 900;">
              YOGA FLASHCARDS
            </div>
          </div>
        </q-toolbar-title>

        <q-space />

        <!-- Auth buttons when not logged in -->
        <div class="row q-gutter-md items-center">
          <q-btn
            flat
            label="SIGN UP"
            to="/register"
            class="yoga-btn-secondary auth-btn"
            style="font-weight: 700; letter-spacing: 1.5px; padding: 8px 24px;"
          />
          <q-btn
            unelevated
            label="LOGIN"
            to="/login"
            class="yoga-btn-primary auth-btn"
            style="font-weight: 700; letter-spacing: 1.5px; padding: 8px 24px;"
          />
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
// No drawer logic needed
</script>

<style scoped lang="scss">
.psychedelic-header {
  background: linear-gradient(135deg,
    rgba(26, 11, 46, 0.98) 0%,
    rgba(74, 20, 140, 0.95) 100%
  );
  backdrop-filter: blur(20px);
  border-bottom: 2px solid rgba(255, 107, 53, 0.5);
  box-shadow:
    0 4px 30px rgba(255, 107, 53, 0.4),
    0 0 60px rgba(155, 77, 202, 0.3);
}

.psychedelic-title {
  font-weight: 900;
  letter-spacing: 3px;
}

.glow-icon {
  filter: drop-shadow(0 0 8px currentColor);
  transition: all 0.3s ease;

  &:hover {
    filter: drop-shadow(0 0 15px currentColor) drop-shadow(0 0 25px currentColor);
    transform: scale(1.2);
  }
}

.auth-btn {
  border-radius: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
  }
}
</style>
