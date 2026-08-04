<template>
  <div class="page-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark"></div>
        <div>
          <p class="brand-title">天玑智算存储配额管理台</p>
          <p class="brand-subtitle">生产运维 · 存储配额查询、维护与同步</p>
        </div>
      </div>
      <div class="top-actions">
        <button class="ghost-button" type="button" @click="refreshAll" :disabled="loading">刷新</button>
      </div>
    </header>

    <main class="content-grid">
      <!-- 筛选与集群切换区：先确定范围，再执行查询。 -->
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
        </div>
      </section>

      <!-- 主表格区：配额记录的查看、编辑、同步和删除都在这里。 -->
      <section class="panel-card table-card full-width">
        <div class="table-header">
          <div>
            <span class="eyebrow">配额台账</span>
            <h2>配额记录</h2>
            <p>按集群维度维护用户配额信息，支持筛选查询、容量核对与配额同步。</p>
          </div>
          <div class="table-header-actions">
            <button class="ghost-button" type="button" @click="refreshAll" :disabled="loading">刷新列表</button>
          </div>
        </div>

        <div v-if="loading" class="table-state">正在加载数据…</div>
        <div v-else-if="rows.length === 0" class="table-state empty-state">
          <h3>当前无匹配记录</h3>
          <p>可切换集群或调整筛选条件后重新查询。</p>
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
                    <small>{{ row.num || '0B' }} 已用 · {{ row.iphone || '0B' }} 配额</small>
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
            <span class="eyebrow">{{ form.id ? '编辑记录' : '新增记录' }}</span>
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

// 后端接口基础地址，优先读取环境变量，未配置时默认指向本机 8000 端口。
const apiBase = (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000').replace(/\/$/, '')
// 当前页面允许切换的集群列表。
const clusters = ['8581', '9654']

// 当前选中的集群 ID。
const clusterId = ref('8581')
// 顶部搜索框中的姓名关键字。
const keyword = ref('')
// 当前页码。
const pageNum = ref(1)
// 当前每页显示的记录数。
const pageSize = ref(10)
// 当前筛选条件下的总记录数。
const total = ref(0)
// 列表数据是否正在加载。
const loading = ref(false)
// 表单保存动作是否正在提交。
const saving = ref(false)
// 当前表格页展示的数据。
const rows = ref([])
// 用于汇总统计的完整数据集合。
const summaryRows = ref([])
// 编辑/新增弹窗是否可见。
const dialogVisible = ref(false)

// 弹窗表单的响应式数据对象。
const form = reactive({
  id: null,
  num: '',
  name: '',
  address: '',
  iphone: '',
  cluster_id: '8581',
})

// 根据总数和每页条数计算总页数，至少为 1。
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value) || 1))
// 汇总所有记录的已用容量总和，单位为字节。
const totalUsedBytes = computed(() => summaryRows.value.reduce((sum, row) => sum + parseSize(row.num), 0))
// 汇总所有记录的配额上限总和，单位为字节。
const totalQuotaBytes = computed(() => summaryRows.value.reduce((sum, row) => sum + parseSize(row.iphone), 0))
// 统计使用率达到或超过 80% 的记录数量。
const highRiskCount = computed(() => summaryRows.value.filter((row) => usagePercent(row) >= 80).length)

// 创建一个新的空表单对象，用于新增记录或重置弹窗表单。
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

// 用空表单对象覆盖当前表单，恢复为初始状态。
function resetForm() {
  Object.assign(form, createEmptyForm())
}

// 把前端表单数据整理成后端接口需要的提交格式。
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

// 把类似 12T、256G 这样的容量字符串转换成字节数，便于后续计算。
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

// 把字节数转换回更适合展示的容量字符串，例如 1024 -> 1.0KB。
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

// 计算当前记录的容量使用率百分比。
function usagePercent(row) {
  const used = parseSize(row?.num)
  const quota = parseSize(row?.iphone)
  if (!quota) return 0
  return Math.round((used / quota) * 100)
}

// 计算进度条宽度，最大不超过 100%。
function usageBarWidth(row) {
  return Math.min(100, usagePercent(row))
}

// 按当前筛选条件读取当前页的数据列表。
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

// 读取汇总计算需要的数据，用于统计总容量和高风险条目数。
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

// 刷新页面需要的全部数据：先拿分页列表，再拿汇总数据。
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

// 把每页数量放大到足够展示全部记录，然后重新加载数据。
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

// 切换当前集群，并回到第一页重新查询。
function changeCluster(cluster) {
  if (clusterId.value === cluster) return
  clusterId.value = cluster
  pageNum.value = 1
  form.cluster_id = cluster
  refreshAll()
}

// 清空搜索条件并恢复默认分页设置。
function resetFilters() {
  keyword.value = ''
  pageNum.value = 1
  pageSize.value = 10
  refreshAll()
}

// 当每页条数变化时，回到第一页并重新查询。
function handlePageSizeChange() {
  pageNum.value = 1
  refreshAll()
}

// 切换到上一页。
function goPrevPage() {
  if (pageNum.value <= 1) return
  pageNum.value -= 1
  refreshAll()
}

// 切换到下一页。
function goNextPage() {
  if (pageNum.value >= totalPages.value) return
  pageNum.value += 1
  refreshAll()
}

// 打开新增记录弹窗，并先清空表单内容。
function openCreateModal() {
  resetForm()
  dialogVisible.value = true
}

// 打开编辑弹窗，并把当前行数据回填到表单中。
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

// 关闭弹窗，并顺手重置表单，避免下次打开残留旧数据。
function closeModal() {
  dialogVisible.value = false
  resetForm()
}

// 保存当前表单：有 id 时更新记录，没有 id 时新增记录。
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

// 删除一条记录；删除成功后根据当前页情况决定是否回退页码。
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

// 调用后端接口，把当前记录的配额信息同步到 Lustre。
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

// 页面首次挂载时自动加载数据。
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
