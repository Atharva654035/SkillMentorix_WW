from django.db import models
import mysql.connector
# Create your models here.

conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="spartans@123",
        database="SkillMentorix"
    )

def run_query(query, params=None, fetchone=False, fetchall=False):

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())

    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()

    conn.commit()

    cursor.close()
    conn.close()
    return result
