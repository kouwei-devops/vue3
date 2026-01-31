
from tortoise import Model, fields


class Student(Model):

    id = fields.IntField(pk=True,)   
    num = fields.CharField(max_length=255, null=True)
    name = fields.CharField(max_length=255, null=True)
    address = fields.CharField(max_length=255, null=True)
    iphone = fields.CharField(max_length=255, null=True)
    cluster_id = fields.CharField(max_length=255, null=True)
    class Meta:

        table = "student"