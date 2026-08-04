
from tortoise import Model, fields


# Student 模型对应数据库里的 student 表。
class Student(Model):

    # 主键 ID。
    id = fields.IntField(pk=True,)   
    # 已用容量。
    num = fields.CharField(max_length=255, null=True)
    # 用户名。
    name = fields.CharField(max_length=255, null=True)
    # 家目录或路径地址。
    address = fields.CharField(max_length=255, null=True)
    # 配额上限；字段名沿用历史命名 iphone。
    iphone = fields.CharField(max_length=255, null=True)
    # 所属集群 ID。
    cluster_id = fields.CharField(max_length=255, null=True)
    class Meta:

        table = "student"