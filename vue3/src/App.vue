

<template>
  <div style="margin: auto; width: 70%;">
    <div>
      <el-button type="primary" style="margin:30px auto; text-align: center; ">数据展示</el-button>
    </div style="margin-bottom: 30px;">
    <el-input type="primary" style="width: 300px;" placeholder="姓名" v-model="name"></el-input>
    <el-button type="primary" @click="load" style="margin-right: 10px;margin-left: 10px;" >查询</el-button>
    <el-table border stripe :data="tableData" style="width: 100%">
      <el-table-column prop="id" label="Date" width="180" />
      <el-table-column prop="name" label="Name" width="180" />
      <el-table-column prop="address" label="Address" />
      <el-table-column fixed="right" label="Operations" min-width="120">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleClick">
            Detail
          </el-button>
          <el-button link type="primary" size="small" @click="handleEdit(scope.row)">
            Edit
          </el-button>
          <el-button link type="primary" size="small" @click="remove(scope.row)"> 删除 </el-button>
         
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
  </div>
</template>

<style scoped></style>
<script lang="ts" setup>
import axios from 'axios'
import { pa, ta } from 'element-plus/es/locale'
import { ref } from 'vue'
import type { ComponentSize } from 'element-plus'
import { reactive } from 'vue'
  const date = reactive({
    name: null
  })
const handleSizeChange = (val: number) => {
  pageSize.value = val
  pageNum.value = 1
  load()
}
const name = ref('')
const pageSize = ref(10)         // 当前页大小
const pageNum = ref(1)          // 当前页码
const tableData = ref([])       // 表格数据
const total = ref(0)            // 总条数
const handleEdit = (row) =>{
  console.log(row)
}
const remove = (id) =>{

}
const ip = '127.0.0.1:8000'
const load = () => {
  axios.get('http://' + ip + '/api/selectPage',{
    params: {
      name: name.value,
      pagenum: pageNum.value,
      pagesize: pageSize.value,
    }
  }).then(res => {
    console.log(res.data)
    tableData.value = res.data.students
    total.value = res.data.total
    pageSize.value = res.data.pagesize
    pageNum.value = res.data.page
  })
}
load() //
</script>

   <!-- 2 pip install tortoise-orm
   3 pip install aiomysql
   4 history
   5 cd .\vue3\
   6 ll
   7 npi i axios
   8 npm i axios -->