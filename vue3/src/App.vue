

<template>
<div
  style="
    margin-bottom: 30px;
    padding: 24px;
    border-radius: 10px;
  "
>
  <el-card
    style="
      text-align: center;
      background: #409EFF;
      border: none;
      color: #ffffff;
    "
  >
    <div style="font-size: 28px; font-weight: 600; letter-spacing: 1px;">
      天玑智算存储配额系统
    </div>
    <div style="margin-top: 10px; font-size: 14px; color: #c7d6e5;">
      当前集群： {{ cluster_id }}
    </div>
  </el-card>
</div>
<div style=" margin: auto; width: 70%; margin-bottom: 20px; text-align: center; font-size: 28px; font-weight: 600;
margin-bottom: 20px; border-radius: 12px;
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
background: #fff; padding: 24px 20px;
">

      <el-button type="success" round @click="set8581" style="margin-right: 10px;margin-left: 10px;" >8581</el-button>
      <el-button type="success" round @click="set9654" style="margin-right: 10px;margin-left: 10px;" >9654</el-button>
</div>
<div style="margin: auto; width: 70%;">

   <div style="margin-bottom: 20px;">
      <el-input type="primary" style="width: 300px;" placeholder="姓名" v-model="name"></el-input>
      <el-button type="primary" @click="load" style="margin-right: 10px;margin-left: 10px;" >查询</el-button>
      <el-button type="primary" @click="handleadd" style="margin-right: 10px;margin-left: 10px;" >新增</el-button>
      <el-button type="primary" @click="loadall" style="margin-right: 10px;margin-left: 10px;" >查询所有用户</el-button>
      <el-button type="primary" @click="reset" style="margin-right: 10px;margin-left: 10px;" >重置</el-button>
    </div>
    <el-table border stripe :data="tableData" style="width: 100%">
      <el-table-column prop="id" label="id" width="180" sortable />
      <el-table-column prop="name" label="姓名" width="180" sortable />
      <el-table-column prop="address" label="家目录" />
      <el-table-column prop="num" label="存储大小" sortable
      :sort-method="(a, b) => parseSize(a.num) - parseSize(b.num)"
      />
      <el-table-column prop="iphone" label="存储配额" sortable
      :sort-method="(a, b) => parseSize(a.iphone) - parseSize(b.iphone)"
      />
      <el-table-column prop="cluster_id" label="集群id" />
      <el-table-column fixed="right" label="Operations" min-width="120">
        <template #default="scope">

          <el-button link type="primary" style="margin-right: 10px;"size="small" @click="handleEdit(scope.row)">
            编辑
          </el-button>
          <el-button link type="primary" style="margin-right: 10px;"size="small" @click="remove(scope.row)"> 删除 </el-button>

        </template>
      </el-table-column>
    </el-table>
    <div style="margin: 10px;">
      <el-pagination background layout="total, sizes, prev, pager, next, jumper"
      :disabled="disabled"
      :total="total" v-model:page-size="pageSize"  v-model:current-page="pageNum" @current-change="load"
      @size-change="handleSizeChange"
      />
    </div>
    <el-dialog v-model="ruleform.dialogVisible" title="学生信息" width="30%">
      <el-form ref="formRef" :model="ruleform.form" :rules="rules"  Label-width="80px" style="padding: 20px">
        <el-form-item prop="name" label="姓名">
          <el-input v-model="ruleform.form.name" autocompLete="off" placeholder="请输入姓名"/>
        </el-form-item>
                <el-form-item prop="address" label="家目录">
          <el-input v-model="ruleform.form.address" autocompLete="off" placeholder="请输入地址"/>
        </el-form-item>
                <el-form-item prop="iphone" label="配额大小">
          <el-input v-model="ruleform.form.iphone" autocompLete="off" placeholder="请输入电话"/>
        </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="ruleform.dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </div>
    </template>
    </el-dialog>
  </div>
</template>

<style scoped></style>
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