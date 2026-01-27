from fastapi import FastAPI
from pydantic import BaseModel
import json
import uvicorn
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_ORM_CONFIG
from models import Student

from routers import stuapis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(stuapis.router)
## 注册
register_tortoise(app, config=TORTOISE_ORM_CONFIG,add_exception_handlers=True)


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
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)