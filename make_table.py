# 데이터베이스를 생성하고 테이블을 생성하는 코드입니다.

import sqlite3

# 데이터베이스 연결 (없으면 자동 생성)
conn = sqlite3.connect("CAR.db")

# 커서 생성
cursor = conn.cursor()

# 테이블 생성 쿼리
create_table_query = """
CREATE TABLE IF NOT EXISTS DATA (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_number TEXT NOT NULL,
    phone_number TEXT,
    address TEXT
);
"""

# 테이블 생성
cursor.execute(create_table_query)

# 변경사항 저장
conn.commit()

# 연결 종료
conn.close()
