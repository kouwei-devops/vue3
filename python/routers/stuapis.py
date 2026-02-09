
import json
from fastapi import APIRouter
from pydantic import BaseModel
from models import Student
import paramiko
router = APIRouter(prefix="/api")

class StudentModel(BaseModel):
    id: int | None = None
    num: str | None = None
    name: str | None = None
    address: str | None = None
    iphone: str | None = None
    cluster_id: int | None = None

@router.get("/selectAll")
async def select_all_student(name:str=''):
    students = await Student.filter(name__contains=name)
    return {"students": students}
#     pip install tortoise-orm
#     pip install aiomysql
@router.post("/add")
async def add_student(student_model: StudentModel):
    stu_id = await Student.get_or_none(id=student_model.id)
    if stu_id is None:
        stu_dic = student_model.model_dump(exclude_none=True)
        stu_json = json.dumps(stu_dic, ensure_ascii=False)  # 中文不转义
        print("JSON格式：", stu_json)
        resp = await Student.create(**stu_dic)
        
        return {"message": "Student added successfully"}

@router.put("/update")
async def update_student(student_model: StudentModel):      ##从前端获取数据 写入到pydantic模型中
    stu_dic = student_model.model_dump(exclude_none=True) ##将 Pydantic 模型实例转换为标准的 Python 字典
    stu_name = json.dumps(stu_dic, ensure_ascii=False)  # 字典格式化成json
    print(stu_name) 
    student_id = stu_dic['id']  ##  从字典中获取id
    student = await Student.get_or_none(id=student_id) ## 从数据库查询id
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}
    update_data = stu_dic.copy() ## 复制字典
    update_data.pop('id', None) ## 删除id字段
    resp = await Student.filter(id=student_id).update(**update_data)  ##  Tortoise ORM 操作数据库
    return {"message": "Student updated successfully"}

@router.delete("/delete/{student_id}")
async def delete_student(student_id: int):  # 从URL路径获取
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}
    
    await Student.filter(id=student_id).delete()
    return {"message": "Student deleted successfully"} 

@router.put("/resave")
async def save_student(student_model: StudentModel):
    stu_dic = student_model.model_dump(exclude_none=True)
    student_id = stu_dic.get("id")

    if not student_id:
        return {"error": "id is required"}

    student = await Student.get_or_none(id=student_id)

    if student is None:
        # 不存在 → 新增
        await Student.create(**stu_dic)
        return {"action": "insert", "message": "Student added successfully"}
    else:
        # 已存在 → 更新
        update_data = stu_dic.copy()
        update_data.pop("id", None)
        await Student.filter(id=student_id).update(**update_data)
        return {"action": "update", "message": "Student updated successfully"}



@router.get("/selectPage")
async def select_page_student(name: str = '',pagenum: int = 1, pagesize: int = 10, cluster_id: int = ''):
    offset = (pagenum - 1) * pagesize
    total = await Student.filter(name__contains=name, cluster_id=cluster_id).count()
    json1 = json.dumps(total, ensure_ascii=False)
    print("总记录数：", json1)
    total_pages = (total + pagesize - 1) // pagesize
    students = await Student.filter(name__contains=name, cluster_id=cluster_id).offset(offset).limit(pagesize).order_by('-id')
    return {
            "students": students,
            "total": total,  # ✅ 返回总记录数
            "page": pagenum,
            "pagesize": pagesize,
        }

## 导出router
__all__ = ["router"]