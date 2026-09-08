from app.database import get_connection


def main():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Remove test/draft bills and their items.
        bills_to_delete = (1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16)
        placeholders = ",".join("?" for _ in bills_to_delete)

        cursor.execute(
            f"DELETE FROM bill_items WHERE bill_id IN ({placeholders})",
            bills_to_delete
        )

        cursor.execute(
            f"DELETE FROM bills WHERE id IN ({placeholders})",
            bills_to_delete
        )

        # Keep Maggi ID 1 because historical bills #10 and #11
        # may reference it.
        #
        # Make ID 1 the main demo product.
        cursor.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (10, 1)
        )

        # Remove duplicate Maggi ID 2 only if no remaining bill uses it.
        cursor.execute(
            """
            DELETE FROM products
            WHERE id = 2
              AND id NOT IN (
                  SELECT DISTINCT product_id
                  FROM bill_items
              )
            """
        )

        # Tata Salt remains ID 3.
        cursor.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (10, 3)
        )

        conn.commit()

        print("Demo database cleaned successfully.")

        print("\nPRODUCTS:")
        for row in cursor.execute(
            """
            SELECT id, name, unit, quantity,
                   reorder_level, gst_rate, hsn_code
            FROM products
            ORDER BY id
            """
        ):
            print(dict(row))

        print("\nBILLS:")
        for row in cursor.execute(
            """
            SELECT id, customer_name, total_amount,
                   payment_mode, status, created_at
            FROM bills
            ORDER BY id
            """
        ):
            print(dict(row))

        print("\nCUSTOMERS:")
        for row in cursor.execute(
            "SELECT id, name, balance FROM customers ORDER BY id"
        ):
            print(dict(row))

    except Exception as e:
        conn.rollback()
        print("Cleanup failed:", e)

    finally:
        conn.close()


if __name__ == "__main__":
    main()