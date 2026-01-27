

<template>
  <div style="margin: auto; width: 70%;">
    <div>
      <el-button type="primary" style="margin:30px auto; text-align: center; ">数据展示</el-button>
    </div style="margin-bottom: 30px;">
    <el-input type="primary" style="width: 300px;" placeholder="姓名" v-model="date.name"></el-input>
    <el-button type="primary" @click="handleSearch" style="margin-right: 10px;margin-left: 10px;" >查询</el-button>
    <el-table border stripe :data="tableData" style="width: 100%">
      <el-table-column prop="date" label="Date" width="180" />
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
    <div style="margin: 10px;marg">
      <el-pagination background layout="prev, pager, next, total" :total="4" v-model:page-size="pageSize"/>
    </div>
  </div>
</template>

<style scoped></style>
<script lang="ts" setup>
import axios from 'axios'
import { pa } from 'element-plus/es/locale'
import { ref } from 'vue'
  import { reactive } from 'vue'
  const date = reactive({
    name: null
  })
  const pageSize = ref(1)
  const pageNum = ref(1)
  const tableData = ref([])
  const handleEdit = (row) =>{
    console.log(row)
  }
  const remove = (id) =>{

  }
  const ip = '127.0.0.1:8000'
  const load = () => {
    axios.get('http://' + ip + '/api/selectAll',{
      params:{
        pageNum: pageNum,
        pageSize: pageSize,

      }
    }).then(res => {
      console.log(res)
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