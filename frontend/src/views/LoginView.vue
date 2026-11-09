<template>
  <div class="login-page">
    <header class="login-nav">
      <span class="brand">MIROFISH</span>
      <LanguageSwitcher />
    </header>

    <main class="login-main">
      <form class="login-form" @submit.prevent="submit">
        <h1>{{ t('login.subtitle') }}</h1>

        <label for="username">{{ t('login.username') }}</label>
        <input id="username" v-model="username" autocomplete="username" autofocus required />

        <label for="password">{{ t('login.password') }}</label>
        <input id="password" v-model="password" type="password" autocomplete="current-password" required />

        <p v-if="error" class="login-error" role="alert">{{ error }}</p>

        <button type="submit" :disabled="submitting">
          {{ submitting ? t('login.submitting') : t('login.submit') }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { login } from '../api/auth'
import { setToken } from '../api/session'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

const submit = async () => {
  error.value = ''
  submitting.value = true
  try {
    const res = await login(username.value, password.value)
    setToken(res.data.token)
    const redirect = route.query.redirect
    // Only follow redirects inside this app
    const isLocal = typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
    await router.replace(isLocal ? redirect : '/')
  } catch (err) {
    error.value = err.response?.status === 401 ? t('login.invalid') : t('login.failed')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.login-nav {
  height: 60px;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e5e5;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  letter-spacing: 1px;
}

.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.login-form {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
}

h1 {
  margin-bottom: 28px;
  font-size: 1.75rem;
  font-weight: 600;
}

label {
  margin-bottom: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #666666;
}

input {
  margin-bottom: 20px;
  padding: 12px;
  border: 1px solid #e5e5e5;
  font: inherit;
}

input:focus {
  outline: 2px solid #ff4500;
  outline-offset: -1px;
}

.login-error {
  margin-bottom: 16px;
  color: #c2300a;
  font-size: 0.9rem;
}

button {
  padding: 14px;
  border: none;
  background: #000000;
  color: #ffffff;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background: #ff4500;
}

button:disabled {
  opacity: 0.6;
  cursor: wait;
}
</style>
