import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from routers import lustreapis
from routers import stuapis
from settings import TORTOISE_ORM_CONFIG


# 创建 FastAPI 应用实例，作为整个后端服务的入口。
app = FastAPI()
# 注册 Lustre 配额相关接口。
app.include_router(lustreapis.router)
# 注册学生/配额记录的增删改查接口。
app.include_router(stuapis.router)
# 注册 Tortoise ORM，让应用启动时自动连接数据库并加载模型。
register_tortoise(app, config=TORTOISE_ORM_CONFIG, add_exception_handlers=True)


@app.on_event("startup")
async def ensure_student_rental_columns():
    """为现有 student 表补齐租用日期列；demo 模式下顺手补示例日期。"""
    connection = Tortoise.get_connection("default")

    has_start_date = await connection.execute_query_dict("SHOW COLUMNS FROM student LIKE 'start_date'")
    if not has_start_date:
        await connection.execute_script("ALTER TABLE student ADD COLUMN start_date DATE NULL;")

    has_end_date = await connection.execute_query_dict("SHOW COLUMNS FROM student LIKE 'end_date'")
    if not has_end_date:
        await connection.execute_script("ALTER TABLE student ADD COLUMN end_date DATE NULL;")

    if os.getenv("DEMO_MODE", "0") == "1":
        await connection.execute_script(
            """
            UPDATE student
            SET end_date = COALESCE(
                end_date,
                CASE id
                    WHEN 1001 THEN DATE_ADD(CURDATE(), INTERVAL 18 DAY)
                    WHEN 1002 THEN DATE_ADD(CURDATE(), INTERVAL 35 DAY)
                    WHEN 1003 THEN DATE_ADD(CURDATE(), INTERVAL 10 DAY)
                    WHEN 1004 THEN DATE_SUB(CURDATE(), INTERVAL 5 DAY)
                    WHEN 1005 THEN DATE_ADD(CURDATE(), INTERVAL 5 DAY)
                    WHEN 1006 THEN DATE_ADD(CURDATE(), INTERVAL 3 DAY)
                    WHEN 2001 THEN DATE_ADD(CURDATE(), INTERVAL 22 DAY)
                    WHEN 2002 THEN DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                    WHEN 2003 THEN DATE_SUB(CURDATE(), INTERVAL 12 DAY)
                    WHEN 2004 THEN DATE_SUB(CURDATE(), INTERVAL 1 DAY)
                    WHEN 2005 THEN DATE_SUB(CURDATE(), INTERVAL 3 DAY)
                    WHEN 2006 THEN DATE_ADD(CURDATE(), INTERVAL 1 DAY)
                    WHEN 2007 THEN DATE_ADD(CURDATE(), INTERVAL 14 DAY)
                    ELSE DATE_ADD(CURDATE(), INTERVAL 14 DAY)
                END
            )
            WHERE end_date IS NULL;

            UPDATE student
            SET start_date = COALESCE(start_date, DATE_SUB(end_date, INTERVAL 30 DAY))
            WHERE start_date IS NULL AND end_date IS NOT NULL;
            """
        )


# 配置跨域访问，允许前端页面直接调用本后端接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 这是一个简单的示例接口，用来验证服务是否能正常响应请求。
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


# 允许直接用 `python main.py` 启动开发服务。
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
