

<template>
  <!-- 顶部标题 -->
  <div class="header-wrap">
    <el-card class="header-card">
      <div class="header-title">天玑智算存储配额系统</div>
      <div class="header-sub">当前集群：{{ cluster_id }}</div>
    </el-card>
  </div>

  <!-- 集群切换 -->
  <div class="cluster-switch">
    <el-button type="success" round @click="set8581">8581</el-button>
    <el-button type="success" round @click="set9654">9654</el-button>
  </div>

  <!-- 主体内容 -->
  <div class="content">
    <!-- 查询区 -->
    <div class="toolbar">
      <el-input
        style="width: 260px"
        placeholder="姓名"
        v-model="name"
      />
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="primary" @click="handleadd">新增</el-button>
      <el-button type="primary" @click="loadall">查询所有用户</el-button>
      <el-button @click="reset">重置</el-button>
    </div>

    <!-- 表格 -->
    <el-table border stripe :data="tableData">
      <!-- 原表格列不动 -->
      <el-table-column prop="id" label="id" width="180" sortable />
      <el-table-column prop="name" label="姓名" width="180" sortable />
      <el-table-column prop="address" label="家目录" />
      <el-table-column
        prop="num"
        label="存储大小"
        sortable
        :sort-method="(a, b) => parseSize(a.num) - parseSize(b.num)"
      />
      <el-table-column
        prop="iphone"
        label="存储配额"
        sortable
        :sort-method="(a, b) => parseSize(a.iphone) - parseSize(b.iphone)"
      />
      <el-table-column prop="cluster_id" label="集群id" />
      <el-table-column fixed="right" label="操作" min-width="120">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleEdit(scope.row)">
            编辑
          </el-button>
          <el-button link type="danger" size="small" @click="remove(scope.row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        v-model:page-size="pageSize"
        v-model:current-page="pageNum"
        @current-change="load"
        @size-change="handleSizeChange"
      />
    </div>
  </div>

  <!-- 弹窗：原样保留 -->
  <!-- el-dialog 原代码不动 -->
</template>

<style scoped>
/* 页面整体居中 */
.header-wrap {
  width: 100%;
  margin-bottom: 24px;
}

.header-card {
  text-align: center;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border: none;
  color: #fff;
  padding: 20px 0;
}

.header-title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 1px;
}

.header-sub {
  margin-top: 8px;
  font-size: 14px;
  color: #e3effa;
}

/* 集群切换 */
.cluster-switch {
  width: 70%;
  margin: 0 auto 24px;
  padding: 20px;
  text-align: center;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.cluster-switch .el-button {
  margin: 0 12px;
}

/* 主体内容 */
.content {
  width: 70%;
  margin: 0 auto;
}

/* 查询工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

/* 分页 */
.pagination {
  margin-top: 16px;
  text-align: right;
}
</style>

<script lang="ts" setup>
import axios from 'axios'
import { da, pa, ru, ta, tr } from 'element-plus/es/locale'
import { ref } from 'vue'
import type { ComponentSize } from 'element-plus'
import { reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/* 分页大小改变时触发 */
const handleSizeChange = (val: number) => {
  pageSize.value = val,     // 更新每页条数
  pageNum.value = 1        // 页码重置为第一页
  load()                   // 重新加载数据
}
const ruleform = reactive({

  dialogVisible: false,
  form: {
    id : null,
    num: '',
    name: '',
    address : '',
    iphone : '',
  }
})

/* 表单、弹窗、校验规则 */
const rules = reactive({
  name: [
    { required: true, message: '姓名不能为空', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度为 2-20 个字符', trigger: 'blur' }
  ],
  address: [
    { required: true, message: '地址不能为空', trigger: 'blur' },
    { min: 5, message: '地址不能少于 5 个字符', trigger: 'blur' }
  ],
  num: [
    { required: true, message: '手机号不能为空', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号',
      trigger: 'blur'
    }
  ]
})

/* 查询条件：姓名 */
const cluster_id = ref("8581")
const id = ref('')
const name = ref('')
const num = ref('')
const iphone = ref()
const formRef = ref()
/* 分页相关变量 */
const pageSize = ref(10)         // 每页条数
const pageNum = ref(1)           // 当前页码
const tableData = ref([])        // 表格数据
const total = ref(0)             // 总记录数

/* 编辑按钮点击事件 */
const handleEdit = (row) => {
  ruleform.form = JSON.parse(JSON.stringify(row))
  ruleform.dialogVisible = true

}

/* 删除按钮点击事件（未实现） */
const remove = (row) => {
  axios.delete('http://' + ip + '/api/delete/' + row.id).then(res => {
    ElMessageBox.confirm(
      '是否确认删除？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      // 用户点击了确定按钮
      if (res.status == 200) {
        console.log(res.data)
        ElMessage.success('删除成功')
        load()
    }else{
      ElMessage.error('删除失败')
    }
    }).catch(() => {
      // 用户点击了取消按钮或关闭了对话框
    });

  })
}

/* 后端服务地址 */
const ip = '10.82.4.120:8000'

/* 新增按钮：打开弹窗并清空表单 */
const handleadd = () => {
  ruleform.dialogVisible = true
  ruleform.form = {}
}
const add = () => {
  axios.post('http://' + ip + '/api/add', ruleform.form).then(res => {
    console.log(res.data)
      ruleform.dialogVisible = false
      load()
  })
}

const updating = ref(false)
const update = async () => {
  if (updating.value) return
  updating.value = true

  try {
    const res = await axios.post(
      'http://' + ip + '/api/lustre/quota/update',
      { ...ruleform.form }   // 解构，避免 reactive 副作用
    )

    if (res.status === 200) {
      ElMessage.success('更新成功')
      ruleform.dialogVisible = false
      await load()           // 等数据刷新完
    } else {
      ElMessage.error('更新失败')
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('请求失败')
  } finally {
    updating.value = false
  }
}

/* 保存按钮：提交表单 */
const save = async () => {
  const valid = await formRef.value.validate() // 直接 await 校验
  if (!valid) return

  if (ruleform.form.id) {
    await update()
  } else {
    ElMessage.error('表单校验不通过')
  }

}

const load = async () => {
  const res = await axios.get('http://' + ip + '/api/selectPage', {
    params: {
      name: name.value,
      num: num.value,
      pagenum: pageNum.value,
      pagesize: pageSize.value,
      cluster_id: cluster_id.value,
    }
  })
  console.log(res.data)
  tableData.value = res.data.students
  id.value = res.data.id
  num.value = res.data.num
  total.value = res.data.total
  pageSize.value = res.data.pagesize
  pageNum.value = res.data.page
  iphone.value = res.data.iphone
}
const loadall = async () => {
  const res = await axios.get('http://' + ip + '/api/selectPage', {
    params: {
      name: name.value,
      num: num.value,
      pagenum: pageNum.value,
      pagesize: pageSize.value,
      cluster_id: cluster_id.value,
    }
  })
  console.log(res.data)
  tableData.value = res.data.students
  id.value = res.data.id
  num.value = res.data.num
  total.value = res.data.total
  pageSize.value = 9999999
  pageNum.value = res.data.page
  iphone.value = res.data.iphone
  load()
}

const parseSize = (size) => {
  if (!size) return 0

  const s = size.toString().trim()
  const value = parseFloat(s)
  if (isNaN(value)) return 0

  const unit = s.slice(-1).toUpperCase()

  switch (unit) {
    case 'T':
      return value * 1024 ** 4
    case 'G':
      return value * 1024 ** 3
    case 'M':
      return value * 1024 ** 2
    case 'K':
      return value * 1024
    default:
      return value // 已经是字节
  }
}
const reset = () => {

  pageSize.value = 10
  pageNum.value = 1

  load()

}
const set8581 = () => {
  cluster_id.value = "8581"
  ElMessage.success('已切换到集群8581')
  load()
}
const set9654 = () => {
  cluster_id.value = "9654"
  ElMessage.success('已切换到集群9654')
  load()
}

load()
</script>


   <!-- 2 pip install tortoise-orm
   3 pip install aiomysql
   4 history
   5 cd .\vue3\
   6 ll
   7 npi i axios
   8 npm i axios -->