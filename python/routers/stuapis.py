import json
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models import Student


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
    start_date: date | None = None
    end_date: date | None = None


# 定义“只更新租用时间”时使用的请求体结构。
class StudentRentalDateModel(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


# 计算一条记录距离结束日期还剩多少天；已到期时返回负数。
def remaining_days(student: Student) -> int | None:
    if not student.end_date:
        return None
    return (student.end_date - date.today()).days


# 判断记录是否已经过期。
def is_expired(student: Student) -> bool:
    days = remaining_days(student)
    return days is not None and days < 0


# 把 ORM 模型转换成前端更容易直接使用的字典结构。
def serialize_student(student: Student) -> dict:
    days = remaining_days(student)
    return {
        "id": student.id,
        "num": student.num,
        "name": student.name,
        "address": student.address,
        "iphone": student.iphone,
        "cluster_id": student.cluster_id,
        "start_date": student.start_date.isoformat() if student.start_date else None,
        "end_date": student.end_date.isoformat() if student.end_date else None,
        "remaining_days": days,
        "is_expired": days is not None and days < 0,
    }


# 校验开始日期和结束日期的先后顺序，避免出现结束日期早于开始日期。
def validate_rental_dates(start_date: date | None, end_date: date | None):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(400, "end_date must be greater than or equal to start_date")


# 按租用状态筛选记录：active=未到期，expired=已到期，all=全部。
def filter_students_by_rent_status(students: list[Student], rent_status: str) -> list[Student]:
    if rent_status == "expired":
        return [student for student in students if is_expired(student)]
    if rent_status == "all":
        return students
    return [student for student in students if not is_expired(student)]


# 按“剩余天数”排序；未设置结束日期的记录排在未到期列表末尾。
def sort_students_by_rent_status(students: list[Student], rent_status: str) -> list[Student]:
    def active_key(student: Student):
        days = remaining_days(student)
        return (
            days is None,
            days if days is not None else 10**9,
            student.end_date or date.max,
            -student.id,
        )

    def expired_key(student: Student):
        days = remaining_days(student)
        return (
            days is None,
            abs(days) if days is not None else 10**9,
            student.end_date or date.max,
            -student.id,
        )

    if rent_status == "expired":
        return sorted(students, key=expired_key)
    if rent_status == "all":
        active_students = sorted([student for student in students if not is_expired(student)], key=active_key)
        expired_students = sorted([student for student in students if is_expired(student)], key=expired_key)
        return [*active_students, *expired_students]
    return sorted(students, key=active_key)


# 根据姓名、集群和租用状态读取记录集合。
async def load_students(name: str = "", cluster_id: int | str | None = "", rent_status: str = "active") -> list[Student]:
    queryset = Student.all()
    if name:
        queryset = queryset.filter(name__contains=name)
    if cluster_id not in ("", None):
        queryset = queryset.filter(cluster_id=str(cluster_id))

    students = await queryset.all()
    filtered_students = filter_students_by_rent_status(students, rent_status)
    return sort_students_by_rent_status(filtered_students, rent_status)


# 按姓名模糊查询全部记录，不做分页。
@router.get("/selectAll")
async def select_all_student(name: str = "", cluster_id: int | str | None = "", rent_status: str = "all"):
    students = await load_students(name=name, cluster_id=cluster_id, rent_status=rent_status)
    return {"students": [serialize_student(student) for student in students]}


# 新增一条记录；如果主键已存在，则本函数不会重复创建。
@router.post("/add")
async def add_student(student_model: StudentModel):
    validate_rental_dates(student_model.start_date, student_model.end_date)
    stu_id = await Student.get_or_none(id=student_model.id)
    if stu_id is None:
        stu_dic = student_model.model_dump(exclude_none=True)
        stu_json = json.dumps(stu_dic, ensure_ascii=False, default=str)
        print("JSON格式：", stu_json)
        await Student.create(**stu_dic)
        return {"message": "Student added successfully"}
    return {"error": f"ID为 {student_model.id} 的记录已存在"}


# 根据前端传入的 id 更新一条已有记录。
@router.put("/update")
async def update_student(student_model: StudentModel):
    validate_rental_dates(student_model.start_date, student_model.end_date)
    stu_dic = student_model.model_dump(exclude_none=True)
    stu_name = json.dumps(stu_dic, ensure_ascii=False, default=str)
    print(stu_name)
    student_id = stu_dic["id"]
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}
    update_data = stu_dic.copy()
    update_data.pop("id", None)
    await Student.filter(id=student_id).update(**update_data)
    return {"message": "Student updated successfully"}


# 按主键删除一条记录。
@router.delete("/delete/{student_id}")
async def delete_student(student_id: int):
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}

    await Student.filter(id=student_id).delete()
    return {"message": "Student deleted successfully"}


# 根据 id 执行“存在则更新，不存在则新增”的保存逻辑。
@router.put("/resave")
async def save_student(student_model: StudentModel):
    validate_rental_dates(student_model.start_date, student_model.end_date)
    stu_dic = student_model.model_dump(exclude_none=True)
    student_id = stu_dic.get("id")

    if not student_id:
        return {"error": "id is required"}

    student = await Student.get_or_none(id=student_id)

    if student is None:
        await Student.create(**stu_dic)
        return {"action": "insert", "message": "Student added successfully"}

    update_data = stu_dic.copy()
    update_data.pop("id", None)
    await Student.filter(id=student_id).update(**update_data)
    return {"action": "update", "message": "Student updated successfully"}


# 只更新一条记录的租用开始日期和结束日期。
@router.put("/rental/{student_id}/dates")
async def update_student_rental_dates(student_id: int, rental_model: StudentRentalDateModel):
    validate_rental_dates(rental_model.start_date, rental_model.end_date)
    student = await Student.get_or_none(id=student_id)
    if student is None:
        return {"error": f"ID为 {student_id} 的学生不存在"}

    update_data = rental_model.model_dump(exclude_none=True)
    await Student.filter(id=student_id).update(**update_data)
    refreshed_student = await Student.get(id=student_id)
    return {
        "message": "Rental dates updated successfully",
        "student": serialize_student(refreshed_student),
    }


# 按姓名、集群和租用状态筛选记录，并返回分页结果与总数。
@router.get("/selectPage")
async def select_page_student(
    name: str = "",
    pagenum: int = 1,
    pagesize: int = 10,
    cluster_id: int | str | None = "",
    rent_status: str = "active",
):
    students = await load_students(name=name, cluster_id=cluster_id, rent_status=rent_status)
    total = len(students)
    offset = max(pagenum - 1, 0) * pagesize
    paged_students = students[offset: offset + pagesize]
    print("总记录数：", json.dumps(total, ensure_ascii=False))
    return {
        "students": [serialize_student(student) for student in paged_students],
        "total": total,
        "page": pagenum,
        "pagesize": pagesize,
    }


# 显式导出路由对象，便于外部模块导入。
__all__ = ["router"]
