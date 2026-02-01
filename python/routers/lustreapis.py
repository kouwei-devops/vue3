from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import Student
import subprocess
router = APIRouter(prefix="/api/lustre")

class LustreQuotaQuery(BaseModel):
    host: str        # 计算节点 
    user: str        # Linux 用户
    home: str        # Lustre 路径

def ssh_quota_query(host: str, user: str, home: str) -> str:
    cmd = [
        "ssh",
        f"{host}",
        f"lfs quota -u {user} {home}"
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

@router.post("/quota/query")
async def query_lustre_quota(q: LustreQuotaQuery):

    # —— 最基本的安全兜底（实验阶段也建议留着） ——
    if not q.user.isalnum():
        raise HTTPException(400, "invalid user")

    if not q.home.startswith("/"):
        raise HTTPException(400, "invalid path")

    try:
        output = ssh_quota_query(
            host=q.host,
            user=q.user,
            home=q.home
        )
    except Exception as e:
        raise HTTPException(500, str(e))

    return {
        "host": q.host,
        "user": q.user,
        "home": q.home,
        "quota_raw": output
    }