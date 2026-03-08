"""
迁移脚本：创建hex_tiles表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from models_sqlite import Base, HexTileORM

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'clawloom.db')}"

print(f"Database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 检查表是否存在
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")

if 'hex_tiles' not in tables:
    print("Creating hex_tiles table...")
    HexTileORM.__table__.create(engine)
    print("Done!")
else:
    print("hex_tiles table already exists")
