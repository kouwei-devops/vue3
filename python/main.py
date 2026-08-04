from fastapi import FastAPI
from pydantic import BaseModel
import json
import uvicorn
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_ORM_CONFIG
from models import Student

from routers import stuapis 
from routers import lustreapis
from fastapi.middleware.cors import CORSMiddleware

# 创建 FastAPI 应用实例，作为整个后端服务的入口。
app = FastAPI()
# 注册 Lustre 配额相关接口。
app.include_router(lustreapis.router)
# 注册学生/配额记录的增删改查接口。
app.include_router(stuapis.router)
# 注册 Tortoise ORM，让应用启动时自动连接数据库并加载模型。
register_tortoise(app, config=TORTOISE_ORM_CONFIG,add_exception_handlers=True)


# 配置跨域访问，允许前端页面直接调用本后端接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



## 客户端JSON → FastAPI自动验证 → Pydantic模型 → 字典转换 > 数据库插入
# ✅ Tortoise ORM 的数据库操作方法：
# await Student.create(**data)- 插入
# await Student.get(id=1)- 查询单条
# await Student.filter(name="张三")- 查询多条
# await Student.filter(id=1).update(**data)- 更新
# await Student.filter(id=1).delete()- 删除
# 这是一个简单的示例接口，用来验证服务是否能正常响应请求。
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# 允许直接用 `python main.py` 启动开发服务。
if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)