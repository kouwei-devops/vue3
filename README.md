# 天玑智算存储配额管理台（lustre-quota-manager）

Lustre 集群用户存储租用的内部运维工具：管理配额记录、跟踪租用到期时间，并可一键把配额同步到远端 Lustre 节点。

## 目录结构

仓库根目录：`/root/lustre-quota-manager`

- 前端：`vue3/`（Vue 3 + Element Plus + Vite）
- 后端：`python/`（FastAPI + Tortoise ORM + MySQL）
- Demo 初始化 SQL：`demo/mysql/init/001-student.sql`
- Demo 数据库编排：`docker-compose.demo.yml`
- 生产编排（参考）：`dockercompose.yaml`、`k8s-lustre-quota.yaml`

## Demo 启动过程（本地跑通前后端）

### 0. 前置条件

- Docker（用于起 MySQL）
- Node.js >= 20.19（前端构建）
- Python 3.10+（后端）

### 1. 启动 MySQL（Demo 容器）

```bash
cd /root/lustre-quota-manager
docker compose -f docker-compose.demo.yml up -d
```

会启动两个容器：

- `vue3-demo-mysql`：MySQL 8.0，监听 3306，首次启动自动执行 `demo/mysql/init/001-student.sql` 建表并插入示例数据
- `vue3-demo-adminer`：Adminer 数据库管理面板，监听 8088（http://localhost:8088，可选的，不需要可以不管）

确认数据库就绪：

```bash
docker ps --filter name=vue3-demo-mysql
# STATUS 显示 (healthy) 即可
```

### 2. 准备后端 Python 环境

后端使用仓库自带的虚拟环境 `.venv`（首次需要创建并安装依赖）：

```bash
cd /root/lustre-quota-manager
python3 -m venv .venv
.venv/bin/pip install -r python/requirements.txt
```

> 如果 `.venv` 已存在但报缺依赖，直接重跑上面 `pip install` 那行即可。

### 3. 启动后端

方式一：直接用脚本（等价于下面的命令）：

```bash
bash python/run-demo-backend.sh
```

方式二：手动启动：

```bash
cd /root/lustre-quota-manager/python
../.venv/bin/uvicorn main:app --env-file .env.demo --host 127.0.0.1 --port 8000
```

- `.env.demo` 里的关键配置：`DB_HOST=127.0.0.1`、`DEMO_MODE=1`
- DEMO_MODE=1 时：启动会自动给空租用日期的记录补示例日期；配额同步接口走模拟返回，不会真的 SSH 到集群

验证后端：

```bash
curl http://127.0.0.1:8000/openapi.json
# 返回 JSON 接口文档即成功
```

### 4. 启动前端

```bash
cd /root/lustre-quota-manager/vue3
npm install        # 首次需要
npm run dev
```

Vite 默认监听 5173 端口，浏览器打开 http://localhost:5173 即可看到页面。

- 前端请求的后端地址由 `VITE_API_BASE` 控制，默认 `http://127.0.0.1:8000`（见 `vue3/.env.local`）
- Demo 数据：集群 8581 有 6 条未到期 + 1 条已到期记录，9654 有若干条

### 5. 验证全链路

1. 页面能打开：http://localhost:5173
2. 列表有数据：未到期列表默认显示 8581 集群，按剩余天数从少到多排序
3. 切集群：顶部切换 8581 / 9654，列表跟随变化
4. 编辑记录：点"编辑"，改结束日期并保存，记录会在未到期/已到期列表间移动
5. 同步配额（Demo）：点"同步配额"，DEMO_MODE 下返回模拟结果，不会执行真实 SSH

## 当前 student 表结构

当前项目后端实际使用的表是 `student`，本地数据库中实际结构如下：

```sql
CREATE TABLE `student` (
  `id` int NOT NULL AUTO_INCREMENT,
  `num` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `iphone` varchar(255) DEFAULT NULL,
  `cluster_id` varchar(255) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 字段含义

- `id`：主键 ID
- `num`：当前已用容量，例如 `12.6T`
- `name`：用户名
- `address`：家目录或存储路径
- `iphone`：配额上限（历史字段名，当前业务含义实际上是"配额大小"）
- `cluster_id`：所属集群 ID，例如 `8581`、`9654`
- `start_date`：存储租用开始日期
- `end_date`：存储租用结束日期

## 线上旧库最少需要补的字段

如果线上目前已经有旧版 `student` 表，并且旧表里只有这些字段：

- `id`
- `num`
- `name`
- `address`
- `iphone`
- `cluster_id`

那么为了支持"租用时间 / 到期排序 / 已到期列表"功能，最少只需要新增这 2 列：

```sql
ALTER TABLE `student`
  ADD COLUMN `start_date` DATE NULL,
  ADD COLUMN `end_date` DATE NULL;
```

如果你希望逐条执行，也可以：

```sql
ALTER TABLE `student`
  ADD COLUMN `start_date` DATE NULL;

ALTER TABLE `student`
  ADD COLUMN `end_date` DATE NULL;
```

## 哪些不是数据库字段

下面这两个值虽然前端会展示、接口也会返回，但它们不是数据库列：

- `remaining_days`
- `is_expired`

它们是后端接口根据 `end_date` 动态计算出来的：

- `remaining_days`：`end_date - 今天`
- `is_expired`：`remaining_days < 0`

所以线上数据库不需要额外新增这两个字段。

## 当前接口与租用时间的关系

后端当前已支持以下租用时间相关能力：

### 1. 新增/更新记录时可带日期

接口：

- `POST /api/add`
- `PUT /api/update`

可提交字段：

- `start_date`
- `end_date`

### 2. 只更新租用日期

接口：

- `PUT /api/rental/{student_id}/dates`

请求体示例：

```json
{
  "start_date": "2026-07-09",
  "end_date": "2026-08-08"
}
```

### 3. 按租用状态查询

接口：

- `GET /api/selectPage`
- `GET /api/selectAll`

可带参数：

- `rent_status=active`：未到期
- `rent_status=expired`：已到期
- `rent_status=all`：全部

### 4. 同步 Lustre 配额

接口：

- `POST /api/lustre/quota/update`

请求体示例：

```json
{
  "cluster_id": 8581,
  "name": "liuyang",
  "address": "/lustre/home/liuyang",
  "iphone": "16T"
}
```

- DEMO_MODE=1 时返回模拟结果，不执行 SSH
- 生产模式下通过 SSH（`/app/ssh/id_rsa`）连接集群管理节点执行 `lfs setquota` 并回写
- 集群映射：8581 → node202，9654 → node120

## 检查线上表结构的 SQL

上线前可以先执行下面的语句确认线上表当前有哪些列：

```sql
DESCRIBE student;
```

或者：

```sql
SHOW COLUMNS FROM student;
```

## Demo 初始化 SQL 说明

仓库里已经提供了 demo 初始化文件：

- `demo/mysql/init/001-student.sql`

这个文件里的 `student` 建表语句已经包含：

- `start_date`
- `end_date`

所以新建 demo 库时，不需要再额外手工补这两个字段。
