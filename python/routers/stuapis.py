
import json
from fastapi import APIRouter
from pydantic import BaseModel
from models import Student

router = APIRouter(prefix="/api")

class StudentModel(BaseModel):
    id: int | None = None
    num: str | None = None
    name: str | None = None
    address: str | None = None
    iphone: str | None = None

@router.get("/selectAll")
async def select_all_student(name:str=''):
    students = await Student.filter(name__contains=name)
    return {"students": students}
#     pip install tortoise-orm
#     pip install aiomysql
@router.post("/add")
async def add_student(student_model: StudentModel):
    stu_name = await Student.get_or_none(name=student_model.name)
    if stu_name is None:
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

@router.delete("/{student_id}")
async def delete_student(student_id: int):  # 从URL路径获取
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}
    
    await Student.filter(id=student_id).delete()
    return {"message": "Student deleted successfully"} 

@router.get("/selectPage")
async def select_page_student(name: str = '',page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    total = await Student.filter(name__contains=name).count()
    total_pages = (total + page_size - 1) // page_size
    students = await Student.filter(name__contains=name).offset(offset).limit(page_size).order_by('-id')

    return {
            "students": students,
            "total": total,  # ✅ 返回总记录数
            "page": page,
            "pagesize": page_size,
        }
## 导出router
__all__ = ["router"]