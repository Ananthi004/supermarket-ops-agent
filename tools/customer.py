from app.database import get_connection


def create_customer(name):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO customers (name, balance)
            VALUES (?, 0)
        """, (name,))

        conn.commit()

        return {
            "success": True,
            "message": f"Customer {name} created successfully."
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def get_customer_balance(name):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, balance
            FROM customers
            WHERE name = ?
        """, (name,))

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "message": "Customer not found."
            }

        return {
            "success": True,
            "customer": dict(customer)
        }

    finally:
        conn.close()


def add_credit(name, amount):
    conn = get_connection()

    try:
        if amount <= 0:
            return {
                "success": False,
                "message": "Credit amount must be greater than zero."
            }

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, balance
            FROM customers
            WHERE name = ?
        """, (name,))

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "message": "Customer not found."
            }

        new_balance = customer["balance"] + amount

        cursor.execute("""
            UPDATE customers
            SET balance = ?
            WHERE id = ?
        """, (new_balance, customer["id"]))

        conn.commit()

        return {
            "success": True,
            "message": f"₹{amount:.2f} credit added for {name}.",
            "customer": name,
            "balance": round(new_balance, 2)
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def record_payment(name, amount):
    conn = get_connection()

    try:
        if amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than zero."
            }

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, balance
            FROM customers
            WHERE name = ?
        """, (name,))

        customer = cursor.fetchone()

        if customer is None:
            return {
                "success": False,
                "message": "Customer not found."
            }

        if amount > customer["balance"]:
            return {
                "success": False,
                "message": (
                    f"Payment of ₹{amount:.2f} is greater than "
                    f"the outstanding balance of ₹{customer['balance']:.2f}."
                )
            }

        new_balance = customer["balance"] - amount

        cursor.execute("""
            UPDATE customers
            SET balance = ?
            WHERE id = ?
        """, (new_balance, customer["id"]))

        conn.commit()

        return {
            "success": True,
            "message": f"₹{amount:.2f} payment recorded for {name}.",
            "customer": name,
            "balance": round(new_balance, 2)
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()