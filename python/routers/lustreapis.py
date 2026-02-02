from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import Student
import subprocess
import re
router = APIRouter(prefix="/api/lustre")
import logging
CLUSTER_HOST_MAP = {
    8581: "node202",
    9654: "node120",
}


class LustreQuotaQuery(BaseModel):
    cluster_id: int
    name: str        # Linux 用户
    address: str        # Lustre 路径
    iphone: str      # 存储大小

def ssh_quota_update(host: str, name: str, address: str, iphone: str) -> str:
    cmd = [
        "ssh",
        "-i", "/app/ssh/id_rsa",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-T",
        host,
        (
            f"nohup lfs setquota -u {name} -b {iphone} -B {iphone} {address} "
            f"&& bash /root/app/vue3/lustre_one_user.sh {name} {address} "
            f"> /tmp/lustre_quota_{name}.log 2>&1 &"
        )
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        text=True
    )

    # 提交即返回
    return "submitted"


@router.post("/quota/update")
async def update_lustre_quota(q: LustreQuotaQuery):

    # —— cluster_id 校验 + 映射 ——
    host = CLUSTER_HOST_MAP.get(q.cluster_id)
    if not host:
        raise HTTPException(400, f"invalid cluster_id: {q.cluster_id}")
    # —— 基本安全校验 ——
    if not q.name.isalnum():
        raise HTTPException(400, "invalid user")

    if not q.address.startswith("/"):
        raise HTTPException(400, "invalid path")

    # size 只允许数字+KMGT
    # if not re.fullmatch(r"\d+(K|M|G|T)", q.iphone, re.IGNORECASE):
    #     raise HTTPException(400, "invalid size")

    try:
        output = ssh_quota_update(
            host=host,
            name=q.name,
            address=q.address,
            iphone=q.iphone
        )
    except Exception as e:
        raise HTTPException(500, str(e))

    return {
        "host": host,
        "name": q.name,
        "address": q.address,
        "iphone": q.iphone,
        "result": "quota updated",
        "stdout": output
    }