from app.database import get_connection


def main():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (name, unit, cost_price, sell_price, mrp,
             quantity, reorder_level, gst_rate, hsn_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Maggi 70g",
            "packet",
            12.0,
            14.0,
            14.0,
            10.0,
            5.0,
            12.0,
            "TEST"
        ))

        conn.commit()

        print("Maggi 70g restored successfully.")

        print("\nCurrent products:")
        for row in cursor.execute("""
            SELECT id, name, unit, quantity,
                   cost_price, sell_price, mrp,
                   reorder_level, gst_rate, hsn_code
            FROM products
            ORDER BY id
        """):
            print(dict(row))

    except Exception as e:
        conn.rollback()
        print("Failed:", e)

    finally:
        conn.close()


if __name__ == "__main__":
    main()