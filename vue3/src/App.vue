<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <p class="page-eyebrow">生产运维 · 存储租用管理</p>
        <h1>天玑智算存储配额管理台</h1>
        <p class="page-subtitle">
          每条记录都包含存储开始日期、结束日期和剩余天数；默认按“快要到期”优先排序，已到期记录自动进入独立列表。
        </p>
      </div>
      <el-tag type="info" effect="plain" round>当前集群 {{ clusterId }}</el-tag>
    </header>

    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar-grid">
        <div class="toolbar-section">
          <span class="section-label">集群范围</span>
          <el-radio-group v-model="clusterId" size="large" @change="changeCluster">
            <el-radio-button v-for="cluster in clusters" :key="cluster" :label="cluster" :value="cluster">
              {{ cluster }}
            </el-radio-button>
          </el-radio-group>
        </div>

        <div class="toolbar-section toolbar-actions">
          <el-input
            v-model.trim="keyword"
            class="search-input"
            clearable
            placeholder="按姓名搜索，例如 liu / wang / sun"
            @keyup.enter="refreshAll"
          />
          <el-button type="primary" :loading="loading" @click="refreshAll">查询</el-button>
          <el-button :disabled="loading" @click="resetFilters">重置</el-button>
          <el-button :disabled="loading" @click="loadAllRows">查询所有用户</el-button>
        </div>
      </div>
    </el-card>

    <section class="summary-grid">
      <el-card shadow="never">
        <p class="summary-label">未到期记录</p>
        <strong>{{ total }}</strong>
        <p class="summary-note">当前分页总数，按剩余天数升序展示。</p>
      </el-card>
      <el-card shadow="never">
        <p class="summary-label">已到期记录</p>
        <strong>{{ expiredTotal }}</strong>
        <p class="summary-note">结束日期早于今天的记录会自动出现在这里。</p>
      </el-card>
      <el-card shadow="never">
        <p class="summary-label">7 天内到期</p>
        <strong>{{ soonExpiringCount }}</strong>
        <p class="summary-note">帮助你快速定位需要续期处理的记录。</p>
      </el-card>
      <el-card shadow="never">
        <p class="summary-label">最近到期</p>
        <strong class="summary-text">{{ nearestExpiryText }}</strong>
        <p class="summary-note">用于快速查看当前最接近到期的用户。</p>
      </el-card>
    </section>

    <el-card class="list-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div>
            <p class="card-eyebrow">未到期列表</p>
            <h2>租用中 / 即将到期</h2>
            <p class="card-description">默认按剩余天数从少到多排序；修改结束日期并保存后，记录会自动留在这里或移动到已到期列表。</p>
          </div>
          <div class="header-actions">
            <el-tag v-if="soonExpiringCount > 0" type="warning" effect="light" round>
              {{ soonExpiringCount }} 条记录 7 天内到期
            </el-tag>
            <el-button text @click="refreshAll">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" border stripe row-key="id" empty-text="当前无未到期记录">
        <el-table-column prop="id" label="ID" width="88" />
        <el-table-column label="姓名" min-width="180">
          <template #default="scope">
            <div class="name-cell">
              <strong>{{ scope.row.name || '未命名用户' }}</strong>
              <span>{{ scope.row.num || '0B' }} 已用 · {{ scope.row.iphone || '0B' }} 配额</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="家目录" min-width="220" show-overflow-tooltip />
        <el-table-column prop="num" label="已用容量" min-width="110" />
        <el-table-column prop="iphone" label="配额上限" min-width="110" />
        <el-table-column prop="cluster_id" label="集群" width="96" />
        <el-table-column label="开始日期" min-width="128">
          <template #default="scope">{{ formatDate(scope.row.start_date) }}</template>
        </el-table-column>
        <el-table-column label="结束日期" min-width="128">
          <template #default="scope">{{ formatDate(scope.row.end_date) }}</template>
        </el-table-column>
        <el-table-column label="剩余天数" min-width="136">
          <template #default="scope">
            <el-tag :type="remainingTagType(scope.row)" effect="light" round>
              {{ remainingDaysText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="使用率" min-width="170">
          <template #default="scope">
            <div class="usage-cell">
              <span>{{ usagePercent(scope.row) }}%</span>
              <el-progress :percentage="usageBarWidth(scope.row)" :stroke-width="8" :show-text="false" />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <div class="row-actions">
              <el-button text type="primary" @click="openEditModal(scope.row)">编辑</el-button>
              <el-button text @click="syncQuota(scope.row)">同步配额</el-button>
              <el-button text type="danger" @click="removeRow(scope.row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="card-footer">
        <span class="footer-meta">共 {{ total }} 条未到期记录</span>
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="pageSizeOptions"
          :total="total"
          @current-change="handleCurrentChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-card class="list-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div>
            <p class="card-eyebrow">已到期列表</p>
            <h2>已到期记录</h2>
            <p class="card-description">这里显示结束日期早于今天的记录。把结束日期往后延长并保存后，记录会自动回到未到期列表。</p>
          </div>
          <el-tag type="danger" effect="light" round>共 {{ expiredTotal }} 条已到期记录</el-tag>
        </div>
      </template>

      <el-table :data="expiredRows" border stripe row-key="id" empty-text="当前无已到期记录">
        <el-table-column prop="id" label="ID" width="88" />
        <el-table-column label="姓名" min-width="180">
          <template #default="scope">
            <div class="name-cell">
              <strong>{{ scope.row.name || '未命名用户' }}</strong>
              <span>{{ scope.row.num || '0B' }} 已用 · {{ scope.row.iphone || '0B' }} 配额</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="address" label="家目录" min-width="220" show-overflow-tooltip />
        <el-table-column prop="num" label="已用容量" min-width="110" />
        <el-table-column prop="iphone" label="配额上限" min-width="110" />
        <el-table-column prop="cluster_id" label="集群" width="96" />
        <el-table-column label="开始日期" min-width="128">
          <template #default="scope">{{ formatDate(scope.row.start_date) }}</template>
        </el-table-column>
        <el-table-column label="结束日期" min-width="128">
          <template #default="scope">{{ formatDate(scope.row.end_date) }}</template>
        </el-table-column>
        <el-table-column label="超期情况" min-width="136">
          <template #default="scope">
            <el-tag :type="remainingTagType(scope.row)" effect="light" round>
              {{ remainingDaysText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="使用率" min-width="170">
          <template #default="scope">
            <div class="usage-cell">
              <span>{{ usagePercent(scope.row) }}%</span>
              <el-progress :percentage="usageBarWidth(scope.row)" :stroke-width="8" :show-text="false" status="exception" />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <div class="row-actions">
              <el-button text type="primary" @click="openEditModal(scope.row)">编辑</el-button>
              <el-button text @click="syncQuota(scope.row)">同步配额</el-button>
              <el-button text type="danger" @click="removeRow(scope.row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="编辑配额记录与租用时间" width="760px" destroy-on-close @closed="resetForm">
      <el-form :model="form" label-position="top">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <el-form-item label="姓名" required>
              <el-input v-model.trim="form.name" placeholder="例如 liuyang" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="集群 ID" required>
              <el-select v-model="form.cluster_id" placeholder="请选择集群" style="width: 100%">
                <el-option v-for="cluster in clusters" :key="cluster" :label="cluster" :value="cluster" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="家目录" required>
              <el-input v-model.trim="form.address" placeholder="例如 /lustre/home/liuyang" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="已用容量">
              <el-input v-model.trim="form.num" placeholder="例如 12.6T" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="配额上限" required>
              <el-input v-model.trim="form.iphone" placeholder="例如 16T" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="开始日期" required>
              <el-date-picker
                v-model="form.start_date"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择开始日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="结束日期" required>
              <el-date-picker
                v-model="form.end_date"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-alert
              title="结束日期改到今天之后，记录会自动回到未到期列表；如果日期早于今天，则会自动进入已到期列表。"
              type="info"
              :closable="false"
              show-icon
            />
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeModal">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveRecord">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

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
// 当前未到期列表的总记录数。
const total = ref(0)
// 列表数据是否正在加载。
const loading = ref(false)
// 表单保存动作是否正在提交。
const saving = ref(false)
// 当前未到期列表的数据。
const rows = ref([])
// 当前已到期列表的数据。
const expiredRows = ref([])
// 当前已到期列表的总记录数。
const expiredTotal = ref(0)
// 编辑弹窗是否可见。
const dialogVisible = ref(false)

// 编辑表单的响应式数据对象。
const form = reactive({
  id: null,
  num: '',
  name: '',
  address: '',
  iphone: '',
  cluster_id: '8581',
  start_date: '',
  end_date: '',
})

// 分页组件里可选的每页数量；当用户点“查询所有用户”时，会自动补入一个更大的选项。
const pageSizeOptions = computed(() => {
  const options = [10, 20, 50, 100]
  if (pageSize.value > 100) {
    options.push(pageSize.value)
  }
  return [...new Set(options)].sort((a, b) => a - b)
})

// 当前未到期列表里，7 天内即将到期的记录数。
const soonExpiringCount = computed(() => rows.value.filter((row) => row.remaining_days != null && row.remaining_days >= 0 && row.remaining_days <= 7).length)
// 当前最先到期的记录摘要，方便在顶部快速查看。
const nearestExpiryText = computed(() => {
  const target = rows.value.find((row) => row.remaining_days != null)
  if (!target) return '暂无数据'
  return `${target.name || target.id} · ${target.end_date || '未设置日期'}`
})

// 创建一个新的空表单对象，用于重置编辑弹窗表单。
function createEmptyForm() {
  return {
    id: null,
    num: '',
    name: '',
    address: '',
    iphone: '',
    cluster_id: clusterId.value,
    start_date: '',
    end_date: '',
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
    start_date: form.start_date || null,
    end_date: form.end_date || null,
  }
}

// 把接口错误尽量转换成更容易阅读的提示文案。
function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  const message = error?.response?.data?.message
  if (typeof message === 'string' && message) return message
  const text = error?.message
  if (typeof text === 'string' && text) return text
  return fallback
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

// 把接口返回的日期字符串格式化成页面展示文本。
function formatDate(value) {
  return value || '未设置'
}

// 把剩余天数转换成更适合用户阅读的文本。
function remainingDaysText(row) {
  if (row?.remaining_days == null) return '未设置'
  if (row.remaining_days < 0) return `已到期 ${Math.abs(row.remaining_days)} 天`
  if (row.remaining_days === 0) return '今日到期'
  return `剩余 ${row.remaining_days} 天`
}

// 根据剩余天数返回 Element Plus 标签颜色。
function remainingTagType(row) {
  if (row?.remaining_days == null) return 'info'
  if (row.remaining_days < 0) return 'danger'
  if (row.remaining_days <= 7) return 'warning'
  return 'success'
}

// 按当前筛选条件读取未到期列表的当前页数据。
async function fetchPage() {
  const response = await axios.get(`${apiBase}/api/selectPage`, {
    params: {
      name: keyword.value,
      pagenum: pageNum.value,
      pagesize: pageSize.value,
      cluster_id: clusterId.value,
      rent_status: 'active',
    },
  })
  rows.value = response.data.students || []
  total.value = Number(response.data.total || 0)
}

// 读取已到期列表的全部数据；这里单独成表，不做分页。
async function fetchExpiredRows() {
  const response = await axios.get(`${apiBase}/api/selectAll`, {
    params: {
      name: keyword.value,
      cluster_id: clusterId.value,
      rent_status: 'expired',
    },
  })
  expiredRows.value = response.data.students || []
  expiredTotal.value = expiredRows.value.length
}

// 刷新页面需要的全部数据：未到期列表和已到期列表都会一起更新。
async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([fetchPage(), fetchExpiredRows()])
  } catch (error) {
    console.error(error)
    ElMessage.error(getErrorMessage(error, '加载数据失败，请检查后端服务与数据库。'))
  } finally {
    loading.value = false
  }
}

// 把每页数量放大到足够展示全部未到期记录，然后重新加载数据。
async function loadAllRows() {
  pageNum.value = 1
  pageSize.value = total.value > 0 ? Math.max(total.value, 100) : 100
  await refreshAll()
}

// 切换当前集群，并回到第一页重新查询。
function changeCluster(cluster) {
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
function handlePageSizeChange(size) {
  pageSize.value = size
  pageNum.value = 1
  refreshAll()
}

// 当页码变化时重新查询对应页数据。
function handleCurrentChange(page) {
  pageNum.value = page
  refreshAll()
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
    start_date: row.start_date || '',
    end_date: row.end_date || '',
  })
  dialogVisible.value = true
}

// 关闭弹窗，并顺手重置表单，避免下次打开残留旧数据。
function closeModal() {
  dialogVisible.value = false
}

// 保存当前表单：编辑时更新基础信息和租用日期；新增时提交全部字段。
async function saveRecord() {
  const payload = normalisePayload()
  if (!payload.name || !payload.address || !payload.iphone) {
    ElMessage.warning('请先补全姓名、家目录和配额上限。')
    return
  }
  if (!payload.start_date || !payload.end_date) {
    ElMessage.warning('请先选择开始日期和结束日期。')
    return
  }
  if (payload.end_date < payload.start_date) {
    ElMessage.warning('结束日期不能早于开始日期。')
    return
  }

  saving.value = true
  try {
    if (payload.id) {
      const { start_date, end_date, ...basePayload } = payload
      await axios.put(`${apiBase}/api/update`, basePayload)
      await axios.put(`${apiBase}/api/rental/${payload.id}/dates`, {
        start_date,
        end_date,
      })
      ElMessage.success('记录与租用时间已更新')
    } else {
      await axios.post(`${apiBase}/api/add`, payload)
      ElMessage.success('记录新增成功')
    }
    dialogVisible.value = false
    resetForm()
    await refreshAll()
  } catch (error) {
    console.error(error)
    ElMessage.error(getErrorMessage(error, '保存失败，请检查接口返回。'))
  } finally {
    saving.value = false
  }
}

// 删除一条记录；删除成功后根据当前页情况决定是否回退页码。
async function removeRow(row) {
  try {
    await ElMessageBox.confirm(`确认删除 ${row.name || row.id} 这条记录吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await axios.delete(`${apiBase}/api/delete/${row.id}`)
    ElMessage.success('删除成功')
    if (rows.value.length === 1 && pageNum.value > 1) {
      pageNum.value -= 1
    }
    await refreshAll()
  } catch (error) {
    console.error(error)
    ElMessage.error(getErrorMessage(error, '删除失败，请检查接口返回。'))
  }
}

// 调用后端接口，把当前记录的配额信息同步到 Lustre。
async function syncQuota(row) {
  try {
    await ElMessageBox.confirm(`确认同步 ${row.name} 的 Lustre 配额吗？`, '同步确认', {
      type: 'warning',
      confirmButtonText: '确认同步',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

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
    ElMessage.error(getErrorMessage(error, '同步配额失败，请检查后端。'))
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
  background: #f5f7fa;
  color: #1f2329;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

:global(*) {
  box-sizing: border-box;
}

:global(.el-card) {
  border-radius: 18px;
  border: 1px solid #e5e7eb;
}

:global(.el-card__header) {
  padding: 20px 24px;
}

:global(.el-card__body) {
  padding: 20px 24px;
}

:global(.el-dialog) {
  border-radius: 20px;
}

:global(.el-table th.el-table__cell) {
  background: #fafafa;
  color: #4b5563;
}

.page-shell {
  width: min(1480px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 24px 0 40px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-eyebrow,
.page-subtitle,
.card-eyebrow,
.card-description,
.summary-label,
.summary-note,
.footer-meta,
.name-cell span {
  margin: 0;
}

.page-eyebrow,
.card-eyebrow,
.summary-label {
  color: #6b7280;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.page-header h1,
.card-header h2 {
  margin: 8px 0 0;
  color: #111827;
}

.page-header h1 {
  font-size: 30px;
  line-height: 1.2;
}

.page-subtitle,
.card-description,
.summary-note {
  margin-top: 10px;
  color: #4b5563;
  line-height: 1.7;
}

.toolbar-card,
.list-card {
  margin-bottom: 20px;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: minmax(220px, auto) minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}

.toolbar-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.toolbar-actions {
  justify-content: flex-end;
}

.section-label {
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}

.search-input {
  width: min(320px, 100%);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-grid strong {
  display: block;
  margin-top: 10px;
  font-size: 30px;
  line-height: 1.1;
  color: #111827;
}

.summary-grid .summary-text {
  font-size: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.header-actions,
.dialog-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  align-content: center;
  justify-content: flex-start;
  column-gap: 12px;
  row-gap: 6px;
  min-width: 0;
}

.row-actions :deep(.el-button) {
  margin-left: 0 !important;
  padding: 0;
  height: auto;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name-cell strong {
  color: #111827;
}

.name-cell span {
  color: #6b7280;
  font-size: 12px;
}

.usage-cell {
  display: grid;
  gap: 8px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.footer-meta {
  color: #6b7280;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .page-shell {
    width: min(100vw - 16px, 100%);
    padding-top: 16px;
  }

  .page-header,
  .card-header,
  .card-footer,
  .toolbar-grid,
  .toolbar-actions {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-actions {
    justify-content: flex-start;
  }

  .search-input {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
