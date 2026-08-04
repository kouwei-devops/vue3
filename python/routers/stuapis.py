
import json
from fastapi import APIRouter
from pydantic import BaseModel
from models import Student
import paramiko

# 统一声明本组接口的公共前缀。
router = APIRouter(prefix="/api")

# 定义前端提交记录时使用的请求体结构。
class StudentModel(BaseModel):
    id: int | None = None
    num: str | None = None
    name: str | None = None
    address: str | None = None
    iphone: str | None = None
    cluster_id: int | None = None

# 按姓名模糊查询全部记录，不做分页。
@router.get("/selectAll")
async def select_all_student(name:str=''):
    students = await Student.filter(name__contains=name)
    return {"students": students}
#     pip install tortoise-orm
#     pip install aiomysql
# 新增一条记录；如果主键已存在，则本函数不会重复创建。
@router.post("/add")
async def add_student(student_model: StudentModel):
    stu_id = await Student.get_or_none(id=student_model.id)
    if stu_id is None:
        stu_dic = student_model.model_dump(exclude_none=True)
        stu_json = json.dumps(stu_dic, ensure_ascii=False)  # 中文不转义
        print("JSON格式：", stu_json)
        resp = await Student.create(**stu_dic)
        
        return {"message": "Student added successfully"}

# 根据前端传入的 id 更新一条已有记录。
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

# 按主键删除一条记录。
@router.delete("/delete/{student_id}")
async def delete_student(student_id: int):  # 从URL路径获取
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}
    
    await Student.filter(id=student_id).delete()
    return {"message": "Student deleted successfully"} 

# 根据 id 执行“存在则更新，不存在则新增”的保存逻辑。
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



# 按姓名与集群筛选记录，并返回分页结果与总数。
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

# 显式导出路由对象，便于外部模块导入。
__all__ = ["router"]