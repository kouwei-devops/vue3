# vue3 存储配额管理项目说明

这个仓库目前是一个前后端同仓库项目：

- 前端目录：`/root/vue3/vue3`
- 后端目录：`/root/vue3/python`
- Demo 初始化 SQL：`/root/vue3/demo/mysql/init/001-student.sql`

说明：`/root/vue3/vue3/README.md` 仍然保留的是 Vite 默认说明；本文件用于补充当前项目自己的运行和数据库结构信息。

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
- `iphone`：配额上限（历史字段名，当前业务含义实际上是“配额大小”）
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

那么为了支持“租用时间 / 到期排序 / 已到期列表”功能，最少只需要新增这 2 列：

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
