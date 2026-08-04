# config.py - Tortoise-ORM配置文件
import os


# 读取整数类型环境变量；如果为空或格式错误，就回退到默认值。
def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# Tortoise ORM 的数据库连接与模型注册配置。
TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": os.getenv("DB_HOST", "testmysql"),
                "port": _int_env("DB_PORT", 3306),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", "1234"),
                "database": os.getenv("DB_NAME", "fastapi"),
                "charset": os.getenv("DB_CHARSET", "utf8mb4"),
            },
        }
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": os.getenv("APP_TIMEZONE", "Asia/Shanghai"),
}