from datetime import datetime
from app.database import get_connection


def get_daily_sales() -> dict:
    """
    Get today's finalized sales summary.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # -------------------------------------------------
        # SALES SUMMARY
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(*) AS bill_count,
                COALESCE(SUM(subtotal), 0) AS subtotal,
                COALESCE(SUM(gst_amount), 0) AS gst_amount,
                COALESCE(SUM(cgst_amount), 0) AS cgst_amount,
                COALESCE(SUM(sgst_amount), 0) AS sgst_amount,
                COALESCE(SUM(total_amount), 0) AS total_sales
            FROM bills
            WHERE status = 'finalized'
              AND DATE(created_at) = DATE('now', 'localtime')
        """)

        summary = cursor.fetchone()

        # -------------------------------------------------
        # SALES BY PAYMENT MODE
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                LOWER(payment_mode) AS payment_mode,
                COALESCE(SUM(total_amount), 0) AS sales_amount,
                COALESCE(SUM(payment_amount), 0) AS collected_amount
            FROM bills
            WHERE status = 'finalized'
              AND DATE(created_at) = DATE('now', 'localtime')
            GROUP BY LOWER(payment_mode)
        """)

        payment_rows = cursor.fetchall()

        payment_summary = {
            "cash": {
                "sales": 0.0,
                "collected": 0.0
            },
            "upi": {
                "sales": 0.0,
                "collected": 0.0
            },
            "card": {
                "sales": 0.0,
                "collected": 0.0
            },
            "credit": {
                "sales": 0.0,
                "collected": 0.0
            }
        }

        for row in payment_rows:
            mode = row["payment_mode"]

            if mode in payment_summary:
                payment_summary[mode]["sales"] = round(
                    row["sales_amount"], 2
                )

                payment_summary[mode]["collected"] = round(
                    row["collected_amount"], 2
                )

        # -------------------------------------------------
        # TOP PRODUCTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                product_id,
                product_name,
                SUM(quantity) AS quantity_sold,
                SUM(quantity * unit_price) AS sales_amount
            FROM bill_items
            WHERE bill_id IN (
                SELECT id
                FROM bills
                WHERE status = 'finalized'
                  AND DATE(created_at) = DATE('now', 'localtime')
            )
            GROUP BY product_id, product_name
            ORDER BY quantity_sold DESC
            LIMIT 10
        """)

        top_products = []

        for row in cursor.fetchall():
            top_products.append({
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "quantity_sold": round(row["quantity_sold"], 2),
                "sales_amount": round(row["sales_amount"], 2)
            })

        # -------------------------------------------------
        # LOW STOCK
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                unit,
                quantity,
                reorder_level
            FROM products
            WHERE quantity <= reorder_level
            ORDER BY quantity ASC
        """)

        low_stock = []

        for row in cursor.fetchall():
            low_stock.append({
                "product_id": row["id"],
                "product_name": row["name"],
                "unit": row["unit"],
                "quantity": round(row["quantity"], 2),
                "reorder_level": round(row["reorder_level"], 2)
            })

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return {
            "success": True,
            "date": datetime.now().strftime("%Y-%m-%d"),

            "bill_count": summary["bill_count"],

            "subtotal": round(summary["subtotal"], 2),

            "gst_amount": round(summary["gst_amount"], 2),

            "cgst_amount": round(summary["cgst_amount"], 2),

            "sgst_amount": round(summary["sgst_amount"], 2),

            "total_sales": round(summary["total_sales"], 2),

            "payments": payment_summary,

            "top_products": top_products,

            "low_stock_products": low_stock
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()