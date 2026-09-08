from app.database import get_connection

def add_product(
    name,
    unit,
    cost_price,
    sell_price,
    mrp,
    quantity,
    reorder_level,
    gst_rate,
    hsn_code
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (name, unit, cost_price, sell_price, mrp,
             quantity, reorder_level, gst_rate, hsn_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            unit,
            cost_price,
            sell_price,
            mrp,
            quantity,
            reorder_level,
            gst_rate,
            hsn_code
        ))

        conn.commit()

        return {
            "success": True,
            "message": f"{name} added successfully."
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def receive_stock(product_id, quantity):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE products
            SET quantity = quantity + ?
            WHERE id = ?
        """, (quantity, product_id))

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Product not found."
            }

        conn.commit()

        return {
            "success": True,
            "message": f"{quantity} units of stock received."
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def get_stock(product_name):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, unit, quantity,
                   cost_price, sell_price, mrp,
                   reorder_level, gst_rate, hsn_code
            FROM products
            WHERE name LIKE ?
        """, (f"%{product_name}%",))

        products = cursor.fetchall()

        if not products:
            return {
                "success": False,
                "message": "Product not found."
            }

        result = []

        for product in products:
            result.append(dict(product))

        return {
            "success": True,
            "products": result
        }

    finally:
        conn.close()


def get_low_stock():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, unit, quantity, reorder_level
            FROM products
            WHERE quantity <= reorder_level
        """)

        products = cursor.fetchall()

        return {
            "success": True,
            "products": [dict(product) for product in products]
        }

    finally:
        conn.close()
def sell_stock(product_id, quantity):
    """Sell stock only when enough quantity is available."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Check current stock
        cursor.execute(
            "SELECT name, quantity FROM products WHERE id = ?",
            (product_id,)
        )

        product = cursor.fetchone()

        if product is None:
            return {
                "success": False,
                "message": "Product not found."
            }

        # Overselling protection
        if product["quantity"] < quantity:
            return {
                "success": False,
                "message": (
                    f"Cannot sell {quantity} units of {product['name']}. "
                    f"Only {product['quantity']} units are available."
                )
            }

        # Reduce stock
        cursor.execute(
            """
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ? AND quantity >= ?
            """,
            (quantity, product_id, quantity)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return {
                "success": False,
                "message": "Sale failed because stock is insufficient."
            }

        conn.commit()

        return {
            "success": True,
            "message": (
                f"Sold {quantity} units of {product['name']}. "
                f"Remaining stock: {product['quantity'] - quantity}"
            )
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()