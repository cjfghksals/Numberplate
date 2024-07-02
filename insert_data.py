# 데이터베이스에 값을 입력하고, 출력하는 코드입니다.

import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("CAR.db")
cursor = conn.cursor()


# 데이터 삽입 예제
def insert_data(car_number, phone_number, address):
    insert_query = """
    INSERT INTO DATA (car_number, phone_number, address)
    VALUES (?, ?, ?)
    """
    cursor.execute(insert_query, (car_number, phone_number, address))
    conn.commit()
    print(f"Inserted: {car_number}, {phone_number}, {address}")


# 데이터 조회 예제
def select_data():
    select_query = """
    SELECT * FROM DATA
    """
    cursor.execute(select_query)
    rows = cursor.fetchall()
    for row in rows:
        print(row)


# 데이터 삽입
# insert_data("154러7070", "010-1234-5678", "301호")
# insert_data("120서6041", "010-4387-2398", "1602호")


# 데이터 조회
print("데이터 조회 결과:")
select_data()

# 연결 종료
conn.close()
