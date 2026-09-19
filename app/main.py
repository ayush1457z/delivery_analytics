from database import get_connection
from gui.app import DeliveryAnalyticsApp




def main():
    connection = get_connection()
    cursor = connection.cursor()

    tables = [
        "customers",
        "addresses",
        "restaurants",
        "menu_items",
        "riders",
        "orders",
        "order_items",
        "deliveries",
        "payments",
        "reviews"
    ]

    print("\nDATABASE SUMMARY")
    print("-" * 30)

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        print(f"{table:<20} {count}")

    cursor.close()
    connection.close()


if __name__ == "__main__":
    app = DeliveryAnalyticsApp()
    app.mainloop()
