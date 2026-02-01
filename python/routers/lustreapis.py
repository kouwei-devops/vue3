from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import Student
import subprocess
import re
router = APIRouter(prefix="/api/lustre")

class LustreQuotaQuery(BaseModel):
    host: str        # 计算节点
    user: str        # Linux 用户
    home: str        # Lustre 路径
    size: str      # 存储大小

def ssh_quota_update(host: str, user: str, home: str ,size:str) -> str:
    cmd = [
        "ssh",
        "-i", "/app/ssh/id_rsa",          # 指定私钥
        "-o", "StrictHostKeyChecking=no",# （可选）首次免确认
        host,
        f"lfs setquota -u {user} -b {size} -B {size} {home} "
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout

@router.post("/quota/update")
async def update_lustre_quota(q: LustreQuotaQuery):

    # —— 基本安全校验 ——
    if not q.user.isalnum():
        raise HTTPException(400, "invalid user")

    if not q.home.startswith("/"):
        raise HTTPException(400, "invalid path")

    # size 只允许数字+KMGT
    if not re.fullmatch(r"\d+(K|M|G|T)", q.size, re.IGNORECASE):
        raise HTTPException(400, "invalid size")

    try:
        output = ssh_quota_update(
            host=q.host,
            user=q.user,
            home=q.home,
            size=q.size
        )
    except Exception as e:
        raise HTTPException(500, str(e))

    return {
        "host": q.host,
        "user": q.user,
        "home": q.home,
        "size": q.size,
        "result": "quota updated",
        "stdout": output
    }