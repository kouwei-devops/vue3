<template>
  <div class="page-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>
          <p class="brand-title">Tianji Quota Console</p>
          <p class="brand-subtitle">Vercel-inspired storage quota operations panel</p>
        </div>
      </div>
      <div class="top-actions">
        <button class="ghost-button" type="button" @click="refreshAll" :disabled="loading">刷新</button>
        <button class="primary-button" type="button" @click="openCreateModal">新增记录</button>
      </div>
    </header>

    <main class="content-grid">
      <section class="hero-card panel-card">
        <span class="eyebrow">Operate / Monitor · storage quota management</span>
        <h1>让你的配额后台像一个现代产品控制台。</h1>
        <p class="hero-copy">
          我按你现有后端接口来组织页面：集群切换、分页查询、新增、更新、删除、以及 Lustre 配额同步都保留，
          但页面信息结构、层级、留白和交互关系改成更贴近 Vercel 风格的白底控制台。
        </p>
        <div class="hero-badges">
          <span class="badge">GET /api/selectPage</span>
          <span class="badge">POST /api/add</span>
          <span class="badge">PUT /api/update</span>
          <span class="badge">DELETE /api/delete/:id</span>
          <span class="badge">POST /api/lustre/quota/update</span>
        </div>
      </section>

      <section class="panel-card side-card">
        <div class="side-card-header">
          <div>
            <p class="eyebrow">Runtime</p>
            <h2>当前接入</h2>
          </div>
          <span class="status-dot" :class="loading ? 'is-loading' : 'is-ready'"></span>
        </div>
        <dl class="runtime-list">
          <div>
            <dt>API Base</dt>
            <dd>{{ apiBase }}</dd>
          </div>
          <div>
            <dt>Cluster</dt>
            <dd>{{ clusterId }}</dd>
          </div>
          <div>
            <dt>Records</dt>
            <dd>{{ total }}</dd>
          </div>
          <div>
            <dt>Search</dt>
            <dd>{{ keyword || '—' }}</dd>
          </div>
        </dl>
        <p class="runtime-footnote">
          Demo 数据库跑起来后，这里会直接展示真实 API 返回的数据，不再走纯静态样板。
        </p>
      </section>

      <section class="toolbar-card panel-card full-width">
        <div class="cluster-switcher">
          <button
            v-for="cluster in clusters"
            :key="cluster"
            type="button"
            class="cluster-pill"
            :class="{ active: clusterId === cluster }"
            @click="changeCluster(cluster)"
          >
            {{ cluster }}
          </button>
        </div>

        <label class="search-field">
          <span class="sr-only">搜索姓名</span>
          <input v-model.trim="keyword" type="text" placeholder="按姓名搜索，例如 liu / wang / sun" @keyup.enter="refreshAll" />
        </label>

        <div class="toolbar-actions">
          <button class="ghost-button" type="button" @click="refreshAll" :disabled="loading">查询</button>
          <button class="ghost-button" type="button" @click="resetFilters" :disabled="loading">重置</button>
          <button class="ghost-button" type="button" @click="loadAllRows" :disabled="loading">查询所有用户</button>
          <button class="primary-button" type="button" @click="openCreateModal">新增</button>
        </div>
      </section>

      <section class="stats-grid full-width">
        <article class="panel-card stat-card">
          <span class="stat-label">Records</span>
          <strong>{{ total }}</strong>
          <p>当前集群与过滤条件下的用户记录总数。</p>
        </article>
        <article class="panel-card stat-card">
          <span class="stat-label">Used Capacity</span>
          <strong>{{ formatBytes(totalUsedBytes) }}</strong>
          <p>基于当前查询结果聚合的已用容量。</p>
        </article>
        <article class="panel-card stat-card">
          <span class="stat-label">Total Quota</span>
          <strong>{{ formatBytes(totalQuotaBytes) }}</strong>
          <p>当前查询结果聚合的总配额上限。</p>
        </article>
        <article class="panel-card stat-card">
          <span class="stat-label">High Risk</span>
          <strong>{{ highRiskCount }}</strong>
          <p>使用率超过 80% 的账号数量。</p>
        </article>
      </section>

      <section class="panel-card table-card full-width">
        <div class="table-header">
          <div>
            <span class="eyebrow">Storage records</span>
            <h2>配额记录</h2>
            <p>保留你原来的业务动作，但把表格作为主角，让查询、编辑、同步、删除更有层级。</p>
          </div>
          <div class="table-header-actions">
            <button class="ghost-button" type="button" @click="refreshAll" :disabled="loading">刷新列表</button>
          </div>
        </div>

        <div v-if="loading" class="table-state">正在加载数据…</div>
        <div v-else-if="rows.length === 0" class="table-state empty-state">
          <h3>当前没有数据</h3>
          <p>你可以切换集群、重置筛选，或先新增一条示例记录。</p>
        </div>
        <div v-else class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>姓名</th>
                <th>家目录</th>
                <th>已用容量</th>
                <th>配额上限</th>
                <th>集群</th>
                <th>使用率</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.id">
                <td>{{ row.id }}</td>
                <td>
                  <div class="name-cell">
                    <strong>{{ row.name || '未命名用户' }}</strong>
                    <small>{{ row.num || '0B' }} used · {{ row.iphone || '0B' }} quota</small>
                  </div>
                </td>
                <td><code>{{ row.address || '—' }}</code></td>
                <td>{{ row.num || '—' }}</td>
                <td>{{ row.iphone || '—' }}</td>
                <td><span class="cluster-tag">{{ row.cluster_id || '—' }}</span></td>
                <td>
                  <div class="usage-cell">
                    <span>{{ usagePercent(row) }}%</span>
                    <div class="progress-track">
                      <div class="progress-bar" :style="{ width: `${usageBarWidth(row)}%` }"></div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="row-actions">
                    <button class="text-button" type="button" @click="openEditModal(row)">编辑</button>
                    <button class="text-button" type="button" @click="syncQuota(row)">同步配额</button>
                    <button class="text-button danger" type="button" @click="removeRow(row)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination-bar">
          <div class="pagination-meta">
            <span>第 {{ pageNum }} / {{ totalPages }} 页</span>
            <span>共 {{ total }} 条</span>
          </div>
          <div class="pagination-actions">
            <label class="page-size-field">
              <span>每页</span>
              <select v-model.number="pageSize" @change="handlePageSizeChange">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </label>
            <button class="ghost-button" type="button" @click="goPrevPage" :disabled="pageNum <= 1 || loading">上一页</button>
            <button class="ghost-button" type="button" @click="goNextPage" :disabled="pageNum >= totalPages || loading">下一页</button>
          </div>
        </div>
      </section>
    </main>

    <div v-if="dialogVisible" class="modal-backdrop" @click.self="closeModal">
      <section class="modal-card">
        <div class="modal-header">
          <div>
            <span class="eyebrow">{{ form.id ? 'Edit record' : 'Create record' }}</span>
            <h3>{{ form.id ? '编辑配额记录' : '新增配额记录' }}</h3>
          </div>
          <button class="icon-button" type="button" @click="closeModal">×</button>
        </div>

        <form class="modal-form" @submit.prevent="saveRecord">
          <label>
            <span>姓名</span>
            <input v-model.trim="form.name" type="text" placeholder="例如 liuyang" required />
          </label>
          <label>
            <span>家目录</span>
            <input v-model.trim="form.address" type="text" placeholder="例如 /lustre/home/liuyang" required />
          </label>
          <label>
            <span>已用容量</span>
            <input v-model.trim="form.num" type="text" placeholder="例如 12.6T" />
          </label>
          <label>
            <span>配额上限</span>
            <input v-model.trim="form.iphone" type="text" placeholder="例如 16T" required />
          </label>
          <label>
            <span>集群 ID</span>
            <select v-model="form.cluster_id">
              <option v-for="cluster in clusters" :key="cluster" :value="cluster">{{ cluster }}</option>
            </select>
          </label>

          <div class="modal-actions">
            <button class="ghost-button" type="button" @click="closeModal">取消</button>
            <button class="primary-button" type="submit" :disabled="saving">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiBase = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '')
const clusters = ['8581', '9654']

const clusterId = ref('8581')
const keyword = ref('')
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const summaryRows = ref([])
const dialogVisible = ref(false)

const form = reactive({
  id: null,
  num: '',
  name: '',
  address: '',
  iphone: '',
  cluster_id: '8581',
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value) || 1))
const totalUsedBytes = computed(() => summaryRows.value.reduce((sum, row) => sum + parseSize(row.num), 0))
const totalQuotaBytes = computed(() => summaryRows.value.reduce((sum, row) => sum + parseSize(row.iphone), 0))
const highRiskCount = computed(() => summaryRows.value.filter((row) => usagePercent(row) >= 80).length)

function createEmptyForm() {
  return {
    id: null,
    num: '',
    name: '',
    address: '',
    iphone: '',
    cluster_id: clusterId.value,
  }
}

function resetForm() {
  Object.assign(form, createEmptyForm())
}

function normalisePayload() {
  return {
    ...(form.id ? { id: Number(form.id) } : {}),
    num: form.num || '',
    name: form.name || '',
    address: form.address || '',
    iphone: form.iphone || '',
    cluster_id: Number(form.cluster_id || clusterId.value),
  }
}

function parseSize(value) {
  if (!value) return 0
  const text = String(value).trim()
  const match = text.match(/^(\d+(?:\.\d+)?)\s*([kmgtp]?)(?:i?b)?$/i)
  if (!match) return Number(text) || 0
  const number = Number(match[1])
  const unit = match[2].toUpperCase()
  const powerMap = { '': 0, K: 1, M: 2, G: 3, T: 4, P: 5 }
  return number * 1024 ** (powerMap[unit] ?? 0)
}

function formatBytes(bytes) {
  if (!bytes) return '0B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value >= 100 ? value.toFixed(0) : value.toFixed(1)}${units[unitIndex]}`
}

function usagePercent(row) {
  const used = parseSize(row?.num)
  const quota = parseSize(row?.iphone)
  if (!quota) return 0
  return Math.round((used / quota) * 100)
}

function usageBarWidth(row) {
  return Math.min(100, usagePercent(row))
}

async function fetchPage() {
  const response = await axios.get(`${apiBase}/api/selectPage`, {
    params: {
      name: keyword.value,
      pagenum: pageNum.value,
      pagesize: pageSize.value,
      cluster_id: clusterId.value,
    },
  })
  rows.value = response.data.students || []
  total.value = Number(response.data.total || 0)
}

async function fetchSummaryRows() {
  const summaryPageSize = Math.max(total.value || pageSize.value, pageSize.value, 100)
  const response = await axios.get(`${apiBase}/api/selectPage`, {
    params: {
      name: keyword.value,
      pagenum: 1,
      pagesize: summaryPageSize,
      cluster_id: clusterId.value,
    },
  })
  summaryRows.value = response.data.students || []
}

async function refreshAll() {
  loading.value = true
  try {
    await fetchPage()
    await fetchSummaryRows()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载数据失败，请检查后端服务与数据库。')
  } finally {
    loading.value = false
  }
}

async function loadAllRows() {
  if (total.value > 0) {
    pageNum.value = 1
    pageSize.value = Math.max(total.value, 100)
  } else {
    pageNum.value = 1
    pageSize.value = 100
  }
  await refreshAll()
}

function changeCluster(cluster) {
  if (clusterId.value === cluster) return
  clusterId.value = cluster
  pageNum.value = 1
  form.cluster_id = cluster
  refreshAll()
}

function resetFilters() {
  keyword.value = ''
  pageNum.value = 1
  pageSize.value = 10
  refreshAll()
}

function handlePageSizeChange() {
  pageNum.value = 1
  refreshAll()
}

function goPrevPage() {
  if (pageNum.value <= 1) return
  pageNum.value -= 1
  refreshAll()
}

function goNextPage() {
  if (pageNum.value >= totalPages.value) return
  pageNum.value += 1
  refreshAll()
}

function openCreateModal() {
  resetForm()
  dialogVisible.value = true
}

function openEditModal(row) {
  Object.assign(form, {
    id: row.id,
    num: row.num || '',
    name: row.name || '',
    address: row.address || '',
    iphone: row.iphone || '',
    cluster_id: String(row.cluster_id || clusterId.value),
  })
  dialogVisible.value = true
}

function closeModal() {
  dialogVisible.value = false
  resetForm()
}

async function saveRecord() {
  saving.value = true
  try {
    const payload = normalisePayload()
    if (payload.id) {
      await axios.put(`${apiBase}/api/update`, payload)
      ElMessage.success('记录更新成功')
    } else {
      await axios.post(`${apiBase}/api/add`, payload)
      ElMessage.success('记录新增成功')
    }
    closeModal()
    await refreshAll()
  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败，请检查接口返回。')
  } finally {
    saving.value = false
  }
}

async function removeRow(row) {
  if (!window.confirm(`确认删除 ${row.name || row.id} 这条记录吗？`)) return
  try {
    await axios.delete(`${apiBase}/api/delete/${row.id}`)
    ElMessage.success('删除成功')
    if (rows.value.length === 1 && pageNum.value > 1) {
      pageNum.value -= 1
    }
    await refreshAll()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除失败，请检查接口返回。')
  }
}

async function syncQuota(row) {
  if (!window.confirm(`确认同步 ${row.name} 的 Lustre 配额吗？`)) return
  try {
    const response = await axios.post(`${apiBase}/api/lustre/quota/update`, {
      cluster_id: Number(row.cluster_id || clusterId.value),
      name: row.name,
      address: row.address,
      iphone: row.iphone,
    })
    ElMessage.success(response.data?.result || '配额同步请求已提交')
  } catch (error) {
    console.error(error)
    ElMessage.error('同步配额失败，请检查后端。')
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
:global(body) {
  margin: 0;
  background:
    radial-gradient(circle at top, rgba(10, 114, 239, 0.08), transparent 30%),
    linear-gradient(180deg, #f7f9fc 0%, #ffffff 28%);
  color: #171717;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

:global(*) {
  box-sizing: border-box;
}

button,
input,
select,
textarea {
  font: inherit;
}

.page-shell {
  width: min(1320px, calc(100vw - 40px));
  margin: 0 auto;
  padding: 24px 0 40px;
}

.topbar,
.panel-card,
.modal-card {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  box-shadow:
    rgba(0, 0, 0, 0.08) 0 0 0 1px,
    rgba(0, 0, 0, 0.04) 0 2px 2px,
    rgba(0, 0, 0, 0.04) 0 18px 40px -28px,
    #fafafa 0 0 0 1px inset;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 22px;
  margin-bottom: 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(180deg, #171717, #4d4d4d);
}

.brand-title,
.brand-subtitle,
.hero-copy,
.runtime-footnote,
.eyebrow,
.table-header p,
.stat-card p,
.table-state p,
.name-cell small,
.pagination-meta,
.runtime-list dt,
.runtime-list dd {
  margin: 0;
}

.brand-title {
  font-size: 15px;
  font-weight: 600;
}

.brand-subtitle {
  font-size: 13px;
  color: #666666;
  margin-top: 4px;
}

.top-actions,
.toolbar-actions,
.table-header-actions,
.pagination-actions,
.row-actions,
.hero-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  gap: 20px;
}

.full-width {
  grid-column: 1 / -1;
}

.panel-card {
  padding: 24px;
}

.hero-card h1 {
  margin: 12px 0 0;
  font-size: clamp(38px, 5vw, 60px);
  line-height: 1.02;
  letter-spacing: -2.4px;
  font-weight: 700;
}

.hero-copy {
  margin-top: 16px;
  max-width: 62ch;
  color: #4d4d4d;
  font-size: 17px;
  line-height: 1.76;
}

.eyebrow {
  color: #666666;
  font-size: 12px;
  letter-spacing: 0.02em;
}

.badge,
.cluster-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #edf5ff;
  color: #0068d6;
  font-size: 12px;
  font-weight: 500;
}

.side-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.side-card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.side-card h2,
.table-header h2,
.modal-header h3 {
  margin: 8px 0 0;
  font-size: 28px;
  line-height: 1.08;
  letter-spacing: -1px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 6px;
}

.status-dot.is-ready {
  background: #0ea56b;
  box-shadow: 0 0 0 6px rgba(14, 165, 107, 0.14);
}

.status-dot.is-loading {
  background: #0a72ef;
  box-shadow: 0 0 0 6px rgba(10, 114, 239, 0.14);
}

.runtime-list {
  display: grid;
  gap: 14px;
}

.runtime-list div {
  display: grid;
  gap: 6px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.runtime-list div:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.runtime-list dt {
  font-size: 12px;
  color: #666666;
}

.runtime-list dd {
  font-size: 14px;
  color: #171717;
  word-break: break-all;
}

.runtime-footnote,
.table-header p,
.stat-card p,
.table-state p,
.empty-state p {
  color: #4d4d4d;
  line-height: 1.7;
}

.toolbar-card {
  display: grid;
  grid-template-columns: auto minmax(240px, 1fr) auto;
  gap: 14px;
  align-items: center;
}

.cluster-switcher {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cluster-pill,
.ghost-button,
.primary-button,
.text-button,
.icon-button,
.page-size-field select {
  border: none;
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.cluster-pill,
.ghost-button,
.primary-button,
.page-size-field,
.icon-button {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 12px;
  font-size: 14px;
}

.cluster-pill,
.ghost-button,
.page-size-field,
.search-field input,
.modal-form input,
.modal-form select,
.page-size-field select {
  background: #ffffff;
  box-shadow: rgba(0, 0, 0, 0.08) 0 0 0 1px, #fafafa 0 0 0 1px inset;
  color: #171717;
}

.cluster-pill.active,
.primary-button {
  background: #171717;
  color: #ffffff;
  box-shadow: none;
}

.ghost-button:hover,
.primary-button:hover,
.cluster-pill:hover,
.text-button:hover,
.icon-button:hover {
  transform: translateY(-1px);
}

.ghost-button:disabled,
.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.search-field input,
.modal-form input,
.modal-form select {
  width: 100%;
  min-height: 44px;
  border: none;
  border-radius: 14px;
  padding: 0 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.stat-card {
  display: grid;
  gap: 10px;
}

.stat-label {
  color: #666666;
  font-size: 12px;
}

.stat-card strong {
  font-size: clamp(28px, 4vw, 40px);
  letter-spacing: -1.2px;
}

.table-card {
  display: grid;
  gap: 18px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-end;
}

.table-state {
  min-height: 200px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  text-align: center;
  background: linear-gradient(180deg, #fafbfd 0%, #ffffff 100%);
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.06);
}

.table-state h3 {
  margin: 0 0 10px;
  font-size: 24px;
  letter-spacing: -0.6px;
}

.table-wrapper {
  overflow-x: auto;
}

.table-wrapper table {
  width: 100%;
  border-collapse: collapse;
}

.table-wrapper th,
.table-wrapper td {
  text-align: left;
  padding: 14px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  vertical-align: middle;
}

.table-wrapper th {
  color: #666666;
  font-size: 12px;
  font-weight: 600;
}

.table-wrapper td {
  font-size: 14px;
}

.name-cell {
  display: grid;
  gap: 4px;
}

.name-cell strong {
  font-size: 14px;
}

.name-cell small,
code {
  color: #666666;
}

code {
  font-family: 'Geist Mono', 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
}

.usage-cell {
  display: grid;
  gap: 8px;
  min-width: 120px;
}

.progress-track {
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #efefef;
}

.progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #0a72ef, #de1d8d);
}

.row-actions {
  gap: 12px;
}

.text-button {
  padding: 0;
  background: transparent;
  color: #0072f5;
  font-size: 13px;
}

.text-button.danger {
  color: #e5484d;
}

.pagination-bar {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.pagination-meta {
  display: flex;
  gap: 16px;
  color: #666666;
  font-size: 13px;
}

.page-size-field {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding-right: 10px;
}

.page-size-field span {
  color: #666666;
  font-size: 13px;
}

.page-size-field select {
  min-height: 34px;
  padding: 0 10px;
  border-radius: 10px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.28);
  display: grid;
  place-items: center;
  padding: 24px;
  z-index: 1000;
}

.modal-card {
  width: min(560px, 100%);
  padding: 22px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.icon-button {
  min-width: 40px;
  min-height: 40px;
  background: #ffffff;
  box-shadow: rgba(0, 0, 0, 0.08) 0 0 0 1px;
  font-size: 22px;
  line-height: 1;
}

.modal-form {
  display: grid;
  gap: 16px;
}

.modal-form label {
  display: grid;
  gap: 8px;
}

.modal-form label span {
  font-size: 13px;
  color: #4d4d4d;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 6px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1080px) {
  .content-grid,
  .stats-grid,
  .toolbar-card {
    grid-template-columns: 1fr;
  }

  .table-header,
  .pagination-bar,
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
