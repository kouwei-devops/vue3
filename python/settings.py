# config.py - Tortoise-ORM配置文件
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

# 数据库配置字典
TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": {
            # MySQL配置（根据您的表结构推荐）
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": "testmysql",      # 数据库主机
                "port": 3306,            # 数据库端口
                "user": "root",          # 用户名
                "password": "1234",  # 密码
                "database": "fastapi",# 数据库名
                "charset": "utf8mb4",    # 字符集.
            },
        }
    },
    "apps": {
        "models": {
            "models": [
                "models",      # 学生模型文件路径       # 数据库迁移工具（可选）
            ],
            "default_connection": "default",
        }
    },
    "use_tz": False,                    # 是否使用时区
    "timezone": "Asia/Shanghai",        # 时区设置
}