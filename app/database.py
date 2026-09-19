import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        port=3307,
        password="",
        database="delivery_analytics"
    )

    return connection