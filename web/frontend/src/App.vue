<template>
  <section v-if="!authed" class="auth card">
    <div class="header">
      <h1>题练通 Web</h1>
      <p>登录后导入题库并开始多人在线刷题。</p>
    </div>
    <input class="input" v-model="loginForm.username" placeholder="用户名" />
    <input class="input" v-model="loginForm.password" placeholder="密码" type="password" />
    <div class="row">
      <button class="primary" @click="login">登录</button>
      <button class="secondary" @click="register">注册</button>
    </div>
    <div v-if="error" class="alert error">{{ error }}</div>
  </section>

  <div v-else class="app">
    <aside class="sidebar">
      <div>
        <div class="brand">题练通</div>
        <div class="muted">多人刷题平台</div>
      </div>
      <nav class="nav">
        <button :class="{active: page==='banks'}" @click="page='banks'; loadBanks()">题库</button>
        <button :class="{active: page==='import'}" @click="page='import'">导入题库</button>
        <button :class="{active: page==='wrong'}" @click="page='wrong'; loadWrong()">错题本</button>
        <button :class="{active: page==='favorites'}" @click="page='favorites'; loadFavorites()">收藏</button>
        <button :class="{active: page==='stats'}" @click="page='stats'; loadStats()">学习记录</button>
        <button v-if="me?.is_admin" :class="{active: page==='admin'}" @click="page='admin'; loadAdmin()">后台管理</button>
      </nav>
      <button class="secondary" @click="doLogout">退出登录</button>
    </aside>

    <main class="main">
      <section v-if="page==='banks'">
        <div class="header"><h1>题库</h1><p>管理在线题库，继续练习或导入新的 Excel 题库。</p></div>
        <div class="grid">
          <article class="card" v-for="bank in banks" :key="bank.id">
            <h3>{{ bank.name }}</h3>
            <p class="muted">{{ bank.category || '未分类' }} · {{ bank.question_count }} 题</p>
            <p>进度 {{ bank.progress }}% · 正确率 {{ bank.accuracy }}% · 错题 {{ bank.wrong_count }}</p>
            <div class="row">
              <button class="primary" @click="startPractice(bank.id, '顺序刷题')">继续练习</button>
              <button class="secondary" @click="startPractice(bank.id, '随机刷题')">随机练习</button>
              <button class="secondary" @click="startPractice(bank.id, '背题模式')">背题模式</button>
            </div>
          </article>
        </div>
        <div v-if="!banks.length" class="card">暂无题库，请先导入 Excel 题库。</div>
      </section>

      <section v-if="page==='import'">
        <div class="header"><h1>导入题库</h1><p>上传标准 Excel 模板，预览校验结果后保存为在线题库。</p></div>
        <div class="card">
          <input type="file" accept=".xlsx" @change="onFile" />
          <button class="primary" @click="previewImport" :disabled="!selectedFile">上传并预览</button>
          <div v-if="importResult" class="alert success">
            共读取 {{ importResult.total_count }} 题，成功 {{ importResult.valid_count }} 题，问题 {{ importResult.error_count }} 题。
          </div>
          <div v-if="importResult?.errors?.length" class="alert error">
            <div v-for="item in importResult.errors.slice(0, 8)" :key="item">{{ item }}</div>
          </div>
        </div>
        <div v-if="importResult" class="card">
          <h3>保存题库</h3>
          <input class="input" v-model="bankMeta.name" placeholder="题库名称" />
          <input class="input" v-model="bankMeta.category" placeholder="分类" />
          <input class="input" v-model="bankMeta.description" placeholder="说明" />
          <label><input type="checkbox" v-model="bankMeta.is_public" /> 公开给其他用户练习</label>
          <button class="primary" @click="confirmImport">确认导入正确题目</button>
        </div>
      </section>

      <section v-if="page==='practice'" class="practice">
        <div class="header"><h1>{{ practiceMode }}</h1><p>{{ currentIndex + 1 }} / {{ questions.length }}</p></div>
        <article v-if="currentQuestion" class="card">
          <p class="muted">{{ currentQuestion.question_type }} · {{ currentQuestion.chapter_name }} · {{ currentQuestion.difficulty || '未填写' }}</p>
          <h2>{{ currentIndex + 1 }}. {{ currentQuestion.question_text }}</h2>
          <button
            v-for="(value, key) in currentQuestion.options"
            :key="key"
            class="option"
            :class="optionClass(String(key))"
            @click="selectOption(String(key))"
          >{{ key }}. {{ value }}</button>
          <input v-if="currentQuestion.question_type === '填空题'" class="input" v-model="blankAnswer" placeholder="请输入答案" />
          <div class="row">
            <button class="secondary" @click="prevQuestion">上一题</button>
            <button class="secondary" @click="nextQuestion">下一题</button>
            <button class="secondary" @click="toggleFavorite(currentQuestion.id)">{{ currentQuestion.is_favorite ? '已收藏' : '收藏' }}</button>
            <button v-if="practiceMode !== '背题模式'" class="primary" @click="submitAnswer">提交答案</button>
          </div>
          <div v-if="answerResult" class="alert" :class="answerResult.is_correct ? 'success' : 'error'">
            <strong>{{ answerResult.is_correct ? '回答正确' : '回答错误' }}</strong><br />
            你的答案：{{ selectedAnswer || blankAnswer }}<br />
            正确答案：{{ answerResult.correct_answer }}<br />
            解析：{{ answerResult.analysis || '暂无解析' }}
          </div>
        </article>
      </section>

      <section v-if="page==='wrong'">
        <div class="header"><h1>错题本</h1><p>集中复习做错的题目。</p></div>
        <article class="card" v-for="item in wrong" :key="item.question_id">
          <h3>{{ item.question_text }}</h3>
          <p class="muted">{{ item.bank_name }} · 错误 {{ item.wrong_count }} 次 · {{ item.mastery_status }}</p>
        </article>
      </section>

      <section v-if="page==='favorites'">
        <div class="header"><h1>收藏</h1><p>查看收藏题目。</p></div>
        <article class="card" v-for="item in favorites" :key="item.question_id">
          <h3>{{ item.question_text }}</h3>
          <p class="muted">{{ item.bank_name }}</p>
        </article>
      </section>

      <section v-if="page==='stats'">
        <div class="header"><h1>学习记录</h1><p>查看你的在线练习统计。</p></div>
        <div class="grid">
          <div class="card stat"><strong>{{ stats.total || 0 }}</strong><span>累计做题</span></div>
          <div class="card stat"><strong>{{ stats.correct || 0 }}</strong><span>正确题数</span></div>
          <div class="card stat"><strong>{{ stats.wrong || 0 }}</strong><span>错误题数</span></div>
          <div class="card stat"><strong>{{ stats.accuracy || 0 }}%</strong><span>总体正确率</span></div>
        </div>
      </section>

      <section v-if="page==='admin'">
        <div class="header"><h1>后台管理</h1><p>查看平台注册用户、题库和学习情况。</p></div>
        <div class="grid">
          <div class="card stat"><strong>{{ adminStats.user_count || 0 }}</strong><span>用户总数</span></div>
          <div class="card stat"><strong>{{ adminStats.bank_count || 0 }}</strong><span>题库总数</span></div>
          <div class="card stat"><strong>{{ adminStats.question_count || 0 }}</strong><span>题目总数</span></div>
          <div class="card stat"><strong>{{ adminStats.answer_count || 0 }}</strong><span>答题记录</span></div>
        </div>
        <div class="card">
          <h3>用户情况</h3>
          <table class="table">
            <thead>
              <tr>
                <th>用户</th><th>角色</th><th>题库</th><th>题目</th><th>做题</th><th>正确率</th><th>错题</th><th>注册时间</th><th>最近登录</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in adminStats.users || []" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.is_admin ? '管理员' : '用户' }}</td>
                <td>{{ user.bank_count }}</td>
                <td>{{ user.question_count }}</td>
                <td>{{ user.answer_count }}</td>
                <td>{{ user.accuracy }}%</td>
                <td>{{ user.wrong_count }}</td>
                <td>{{ formatTime(user.created_at) }}</td>
                <td>{{ formatTime(user.last_login_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <div v-if="error" class="alert error">{{ error }}</div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, logout, setToken, token } from './api'

const authed = ref(Boolean(token()))
const page = ref('banks')
const error = ref('')
const loginForm = reactive({ username: '', password: '' })
const me = ref<any>(null)
const banks = ref<any[]>([])
const selectedFile = ref<File | null>(null)
const importResult = ref<any>(null)
const bankMeta = reactive({ name: '', category: '', description: '', is_public: false })
const questions = ref<any[]>([])
const currentIndex = ref(0)
const practiceMode = ref('顺序刷题')
const selected = ref<string[]>([])
const blankAnswer = ref('')
const answerResult = ref<any>(null)
const wrong = ref<any[]>([])
const favorites = ref<any[]>([])
const stats = ref<any>({})
const adminStats = ref<any>({})

const currentQuestion = computed(() => questions.value[currentIndex.value])
const selectedAnswer = computed(() => currentQuestion.value?.question_type === '多选题' ? [...selected.value].sort().join('') : selected.value[0] || '')

async function run(fn: () => Promise<void>) {
  error.value = ''
  try { await fn() } catch (e: any) { error.value = e.message }
}
async function loadMe() { me.value = await api('/auth/me') }
async function afterAuth() { authed.value = true; await loadMe(); await loadBanks() }
async function login() { await run(async () => { const data = await api('/auth/login', { method: 'POST', body: new URLSearchParams({ username: loginForm.username, password: loginForm.password }) }); setToken(data.access_token); await afterAuth() }) }
async function register() { await run(async () => { const data = await api('/auth/register', { method: 'POST', body: JSON.stringify(loginForm) }); setToken(data.access_token); await afterAuth() }) }
function doLogout() { logout(); authed.value = false; me.value = null }
async function loadBanks() { await run(async () => { banks.value = await api('/banks') }) }
function onFile(event: Event) { selectedFile.value = (event.target as HTMLInputElement).files?.[0] || null }
async function previewImport() { await run(async () => { const form = new FormData(); form.append('file', selectedFile.value!); importResult.value = await api('/banks/import/preview', { method: 'POST', body: form }); bankMeta.name = selectedFile.value?.name.replace(/\.xlsx$/i, '') || '' }) }
async function confirmImport() { await run(async () => { await api('/banks/import/confirm', { method: 'POST', body: JSON.stringify({ ...bankMeta, questions: importResult.value.questions }) }); importResult.value = null; page.value = 'banks'; await loadBanks() }) }
async function startPractice(bankId: number, mode: string) { await run(async () => { practiceMode.value = mode; questions.value = await api(`/banks/${bankId}/questions?mode=${encodeURIComponent(mode)}&limit=50`); currentIndex.value = 0; resetAnswer(); page.value = 'practice' }) }
function selectOption(key: string) { if (!currentQuestion.value || answerResult.value) return; if (currentQuestion.value.question_type === '多选题') selected.value = selected.value.includes(key) ? selected.value.filter(x => x !== key) : [...selected.value, key]; else selected.value = [key] }
function optionClass(key: string) { if (!answerResult.value) return { selected: selected.value.includes(key) }; if (answerResult.value.correct_answer.includes(key)) return 'correct'; if (selected.value.includes(key)) return 'wrong'; return '' }
function resetAnswer() { selected.value = []; blankAnswer.value = ''; answerResult.value = null }
function prevQuestion() { currentIndex.value = Math.max(0, currentIndex.value - 1); resetAnswer() }
function nextQuestion() { currentIndex.value = Math.min(questions.value.length - 1, currentIndex.value + 1); resetAnswer() }
async function submitAnswer() { await run(async () => { answerResult.value = await api('/practice/answer', { method: 'POST', body: JSON.stringify({ question_id: currentQuestion.value.id, user_answer: currentQuestion.value.question_type === '填空题' ? blankAnswer.value : selectedAnswer.value, practice_mode: practiceMode.value }) }) }) }
async function toggleFavorite(questionId: number) { await run(async () => { const data = await api(`/practice/questions/${questionId}/favorite`, { method: 'POST' }); currentQuestion.value.is_favorite = data.is_favorite }) }
async function loadWrong() { await run(async () => { wrong.value = await api('/practice/wrong') }) }
async function loadFavorites() { await run(async () => { favorites.value = await api('/practice/favorites') }) }
async function loadStats() { await run(async () => { stats.value = await api('/stats/overview') }) }
async function loadAdmin() { await run(async () => { adminStats.value = await api('/admin/overview') }) }
function formatTime(value: string | null) { return value ? new Date(value).toLocaleString() : '暂无' }

onMounted(() => { if (authed.value) afterAuth() })
</script>
