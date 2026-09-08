from app.database import get_connection


def calculate_gst(base_amount: float, gst_rate: float) -> dict:
    """Calculate GST, CGST and SGST."""

    gst_amount = round(base_amount * gst_rate / 100, 2)

    cgst_amount = round(gst_amount / 2, 2)
    sgst_amount = round(gst_amount - cgst_amount, 2)

    return {
        "gst_amount": gst_amount,
        "cgst_amount": cgst_amount,
        "sgst_amount": sgst_amount,
    }


def create_bill(customer_name: str = None) -> dict:
    """Create a new draft bill."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bills (
                customer_name,
                subtotal,
                gst_amount,
                total_amount,
                payment_mode,
                payment_reference,
                status,
                cgst_amount,
                sgst_amount,
                payment_amount
            )
            VALUES (?, 0, 0, 0, NULL, NULL, 'draft', 0, 0, 0)
            """,
            (customer_name,),
        )

        bill_id = cursor.lastrowid

        conn.commit()

        return {
            "success": True,
            "message": f"Bill #{bill_id} created successfully.",
            "bill_id": bill_id,
            "status": "draft",
            "customer_name": customer_name,
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def add_bill_item(
    bill_id: int,
    product_id: int,
    quantity: float,
) -> dict:
    """
    Add an item to a draft bill.

    Stock is checked but not deducted.
    Stock is deducted only when the bill is finalized.
    """

    if quantity <= 0:
        return {
            "success": False,
            "message": "Quantity must be greater than 0.",
        }

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Check bill
        cursor.execute(
            """
            SELECT id, status
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        if bill["status"] != "draft":
            return {
                "success": False,
                "message": f"Bill #{bill_id} is already finalized.",
            }

        # Get product
        cursor.execute(
            """
            SELECT
                id,
                name,
                unit,
                sell_price,
                gst_rate,
                quantity
            FROM products
            WHERE id = ?
            """,
            (product_id,),
        )

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": f"Product ID {product_id} not found.",
            }

        # Check stock
        if product["quantity"] < quantity:
            return {
                "success": False,
                "message": (
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {product['quantity']} "
                    f"{product['unit']}."
                ),
            }

        # Calculate line amount
        base_amount = round(
            product["sell_price"] * quantity,
            2,
        )

        gst = calculate_gst(
            base_amount,
            product["gst_rate"],
        )

        line_total = round(
            base_amount + gst["gst_amount"],
            2,
        )

        cursor.execute(
            """
            INSERT INTO bill_items (
                bill_id,
                product_id,
                product_name,
                quantity,
                unit_price,
                gst_rate,
                gst_amount,
                line_total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bill_id,
                product["id"],
                product["name"],
                quantity,
                product["sell_price"],
                product["gst_rate"],
                gst["gst_amount"],
                line_total,
            ),
        )

        _recalculate_bill_totals(
            cursor,
            bill_id,
        )

        conn.commit()

        return {
            "success": True,
            "message": (
                f"{quantity} {product['unit']} of "
                f"{product['name']} added to Bill #{bill_id}."
            ),
            "bill_id": bill_id,
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "line_total": line_total,
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def get_bill(bill_id: int) -> dict:
    """Get complete bill details."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                customer_name,
                subtotal,
                gst_amount,
                cgst_amount,
                sgst_amount,
                total_amount,
                payment_mode,
                payment_reference,
                payment_amount,
                status,
                created_at
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        cursor.execute(
            """
            SELECT
                id,
                bill_id,
                product_id,
                product_name,
                quantity,
                unit_price,
                gst_rate,
                gst_amount,
                line_total
            FROM bill_items
            WHERE bill_id = ?
            ORDER BY id
            """,
            (bill_id,),
        )

        items = []

        for row in cursor.fetchall():
            items.append(
                {
                    "id": row["id"],
                    "bill_id": row["bill_id"],
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "quantity": row["quantity"],
                    "unit_price": round(row["unit_price"], 2),
                    "gst_rate": row["gst_rate"],
                    "gst_amount": round(row["gst_amount"], 2),
                    "line_total": round(row["line_total"], 2),
                }
            )

        return {
            "success": True,
            "bill": {
                "id": bill["id"],
                "customer_name": bill["customer_name"],
                "subtotal": round(bill["subtotal"], 2),
                "gst_amount": round(bill["gst_amount"], 2),
                "cgst_amount": round(bill["cgst_amount"], 2),
                "sgst_amount": round(bill["sgst_amount"], 2),
                "total_amount": round(bill["total_amount"], 2),
                "payment_mode": bill["payment_mode"],
                "payment_reference": bill["payment_reference"],
                "payment_amount": round(
                    bill["payment_amount"] or 0,
                    2,
                ),
                "status": bill["status"],
                "created_at": bill["created_at"],
                "items": items,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def update_bill_item(
    bill_item_id: int,
    quantity: float,
    bill_id: int = None,
) -> dict:
    """
    Update a bill item's quantity.

    bill_id is optional for backward compatibility.
    If omitted, it is automatically obtained from bill_item_id.
    """

    if quantity <= 0:
        return {
            "success": False,
            "message": "Quantity must be greater than 0.",
        }

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # If bill_id wasn't supplied, find it from the item.
        if bill_id is None:
            cursor.execute(
                """
                SELECT bill_id
                FROM bill_items
                WHERE id = ?
                """,
                (bill_item_id,),
            )

            item_bill = cursor.fetchone()

            if not item_bill:
                return {
                    "success": False,
                    "message": (
                        f"Bill item #{bill_item_id} not found."
                    ),
                }

            bill_id = item_bill["bill_id"]

        # Check bill
        cursor.execute(
            """
            SELECT id, status
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        if bill["status"] != "draft":
            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} is already finalized "
                    "and cannot be edited."
                ),
            }

        # Get bill item
        cursor.execute(
            """
            SELECT
                id,
                product_id,
                product_name
            FROM bill_items
            WHERE id = ?
              AND bill_id = ?
            """,
            (bill_item_id, bill_id),
        )

        item = cursor.fetchone()

        if not item:
            return {
                "success": False,
                "message": (
                    f"Bill item #{bill_item_id} "
                    f"not found in Bill #{bill_id}."
                ),
            }

        # Get product
        cursor.execute(
            """
            SELECT
                id,
                name,
                unit,
                sell_price,
                gst_rate,
                quantity
            FROM products
            WHERE id = ?
            """,
            (item["product_id"],),
        )

        product = cursor.fetchone()

        if not product:
            return {
                "success": False,
                "message": (
                    f"Product ID {item['product_id']} "
                    "no longer exists."
                ),
            }

        if product["quantity"] < quantity:
            return {
                "success": False,
                "message": (
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {product['quantity']} "
                    f"{product['unit']}."
                ),
            }

        # Recalculate
        base_amount = round(
            product["sell_price"] * quantity,
            2,
        )

        gst = calculate_gst(
            base_amount,
            product["gst_rate"],
        )

        line_total = round(
            base_amount + gst["gst_amount"],
            2,
        )

        cursor.execute(
            """
            UPDATE bill_items
            SET quantity = ?,
                unit_price = ?,
                gst_rate = ?,
                gst_amount = ?,
                line_total = ?
            WHERE id = ?
              AND bill_id = ?
            """,
            (
                quantity,
                product["sell_price"],
                product["gst_rate"],
                gst["gst_amount"],
                line_total,
                bill_item_id,
                bill_id,
            ),
        )

        _recalculate_bill_totals(
            cursor,
            bill_id,
        )

        conn.commit()

        return {
            "success": True,
            "message": (
                f"Bill item #{bill_item_id} updated "
                f"to quantity {quantity}."
            ),
            "bill_id": bill_id,
            "bill_item_id": bill_item_id,
            "quantity": quantity,
            "line_total": line_total,
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def remove_bill_item(
    bill_item_id: int,
    bill_id: int = None,
) -> dict:
    """
    Remove a bill item.

    bill_id is optional for backward compatibility.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Find bill_id automatically if not supplied.
        if bill_id is None:
            cursor.execute(
                """
                SELECT bill_id
                FROM bill_items
                WHERE id = ?
                """,
                (bill_item_id,),
            )

            item_bill = cursor.fetchone()

            if not item_bill:
                return {
                    "success": False,
                    "message": (
                        f"Bill item #{bill_item_id} not found."
                    ),
                }

            bill_id = item_bill["bill_id"]

        # Check bill
        cursor.execute(
            """
            SELECT id, status
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        if bill["status"] != "draft":
            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} is already finalized "
                    "and cannot be edited."
                ),
            }

        # Get item
        cursor.execute(
            """
            SELECT id, product_name
            FROM bill_items
            WHERE id = ?
              AND bill_id = ?
            """,
            (bill_item_id, bill_id),
        )

        item = cursor.fetchone()

        if not item:
            return {
                "success": False,
                "message": (
                    f"Bill item #{bill_item_id} "
                    f"not found in Bill #{bill_id}."
                ),
            }

        cursor.execute(
            """
            DELETE FROM bill_items
            WHERE id = ?
              AND bill_id = ?
            """,
            (bill_item_id, bill_id),
        )

        _recalculate_bill_totals(
            cursor,
            bill_id,
        )

        conn.commit()

        return {
            "success": True,
            "message": (
                f"{item['product_name']} removed "
                f"from Bill #{bill_id}."
            ),
            "bill_id": bill_id,
            "bill_item_id": bill_item_id,
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def finalize_bill(
    bill_id: int,
    payment_mode: str,
    payment_amount: float = None,
    payment_reference: str = "",
) -> dict:
    """
    Finalize a normal bill.

    payment_amount is optional for backward compatibility.
    If omitted, the bill total is treated as the received amount.

    Supports:
        cash
        upi
        card

    Uses transaction + atomic stock deduction +
    conditional draft -> finalized update.
    """

    payment_mode = payment_mode.strip().lower()

    allowed_modes = {
        "cash",
        "upi",
        "card",
    }

    if payment_mode not in allowed_modes:
        return {
            "success": False,
            "message": (
                "Invalid payment mode. "
                "Use cash, upi or card."
            ),
        }

    conn = get_connection()

    try:
        conn.execute("BEGIN")

        cursor = conn.cursor()

        # Get bill
        cursor.execute(
            """
            SELECT
                id,
                customer_name,
                subtotal,
                gst_amount,
                cgst_amount,
                sgst_amount,
                total_amount,
                status
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            conn.rollback()

            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        # Idempotency protection
        if bill["status"] != "draft":
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} has already been finalized. "
                    "It cannot be finalized again."
                ),
            }

        # Get items
        cursor.execute(
            """
            SELECT
                id,
                product_id,
                product_name,
                quantity,
                unit_price,
                gst_rate,
                gst_amount,
                line_total
            FROM bill_items
            WHERE bill_id = ?
            ORDER BY id
            """,
            (bill_id,),
        )

        items = cursor.fetchall()

        if not items:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} has no items."
                ),
            }

        total_amount = round(
            bill["total_amount"],
            2,
        )

        # Backward compatibility:
        # If payment amount isn't provided,
        # assume exact payment.
        if payment_amount is None:
            payment_amount = total_amount

        payment_amount = float(payment_amount)

        if payment_amount <= 0:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    "Payment amount must be greater than 0."
                ),
            }

        # Check payment
        if payment_amount < total_amount:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Insufficient payment. "
                    f"Bill total is ₹{total_amount:.2f}, "
                    f"but payment received is "
                    f"₹{payment_amount:.2f}."
                ),
            }

        change = round(
            payment_amount - total_amount,
            2,
        )

        # Check stock
        for item in items:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    unit,
                    quantity
                FROM products
                WHERE id = ?
                """,
                (item["product_id"],),
            )

            product = cursor.fetchone()

            if not product:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Product ID {item['product_id']} "
                        "not found."
                    ),
                }

            if product["quantity"] < item["quantity"]:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for "
                        f"{product['name']}. "
                        f"Available: {product['quantity']} "
                        f"{product['unit']}, "
                        f"required: {item['quantity']}."
                    ),
                }

        # Atomic stock deduction
        for item in items:

            cursor.execute(
                """
                UPDATE products
                SET quantity = quantity - ?
                WHERE id = ?
                  AND quantity >= ?
                """,
                (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"],
                ),
            )

            if cursor.rowcount != 1:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Stock changed while finalizing "
                        "the bill. Please check stock and "
                        "try again."
                    ),
                }

        # Important:
        # Only draft bills can transition to finalized.
        cursor.execute(
            """
            UPDATE bills
            SET payment_mode = ?,
                payment_amount = ?,
                payment_reference = ?,
                status = 'finalized'
            WHERE id = ?
              AND status = 'draft'
            """,
            (
                payment_mode,
                payment_amount,
                payment_reference,
                bill_id,
            ),
        )

        # If another process finalized it first,
        # this update affects zero rows.
        if cursor.rowcount == 0:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    "Bill could not be finalized. "
                    "It may have already been finalized."
                ),
            }

        conn.commit()

        return {
            "success": True,
            "message": (
                f"Bill #{bill_id} finalized successfully."
            ),
            "bill_id": bill_id,
            "payment_mode": payment_mode,
            "payment_amount": round(payment_amount, 2),
            "bill_total": total_amount,
            "change": change,
            "status": "finalized",
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def finalize_credit_bill(
    bill_id: int,
) -> dict:
    """
    Finalize a bill as credit / Khata.

    Customer balance is increased by bill total.
    """

    conn = get_connection()

    try:
        conn.execute("BEGIN")

        cursor = conn.cursor()

        # Get bill
        cursor.execute(
            """
            SELECT
                id,
                customer_name,
                subtotal,
                gst_amount,
                cgst_amount,
                sgst_amount,
                total_amount,
                status
            FROM bills
            WHERE id = ?
            """,
            (bill_id,),
        )

        bill = cursor.fetchone()

        if not bill:
            conn.rollback()

            return {
                "success": False,
                "message": f"Bill #{bill_id} not found.",
            }

        if bill["status"] != "draft":
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} has already been finalized."
                ),
            }

        customer_name = bill["customer_name"]

        if not customer_name:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    "Credit bill requires a customer name."
                ),
            }

        # Find customer
        cursor.execute(
            """
            SELECT
                id,
                name,
                balance
            FROM customers
            WHERE LOWER(name) = LOWER(?)
            """,
            (customer_name,),
        )

        customer = cursor.fetchone()

        if not customer:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Customer '{customer_name}' "
                    "does not exist. Create the customer "
                    "before using credit billing."
                ),
            }

        # Get items
        cursor.execute(
            """
            SELECT
                id,
                product_id,
                product_name,
                quantity
            FROM bill_items
            WHERE bill_id = ?
            ORDER BY id
            """,
            (bill_id,),
        )

        items = cursor.fetchall()

        if not items:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} has no items."
                ),
            }

        # Check stock
        for item in items:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    unit,
                    quantity
                FROM products
                WHERE id = ?
                """,
                (item["product_id"],),
            )

            product = cursor.fetchone()

            if not product:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Product ID {item['product_id']} "
                        "not found."
                    ),
                }

            if product["quantity"] < item["quantity"]:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for "
                        f"{product['name']}. "
                        f"Available: {product['quantity']} "
                        f"{product['unit']}, "
                        f"required: {item['quantity']}."
                    ),
                }

        # Deduct stock atomically
        for item in items:

            cursor.execute(
                """
                UPDATE products
                SET quantity = quantity - ?
                WHERE id = ?
                  AND quantity >= ?
                """,
                (
                    item["quantity"],
                    item["product_id"],
                    item["quantity"],
                ),
            )

            if cursor.rowcount != 1:
                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Stock changed while finalizing "
                        "the credit bill. Please check "
                        "stock and try again."
                    ),
                }

        bill_total = round(
            bill["total_amount"],
            2,
        )

        old_balance = round(
            customer["balance"] or 0,
            2,
        )

        new_balance = round(
            old_balance + bill_total,
            2,
        )

        # Update customer balance
        cursor.execute(
            """
            UPDATE customers
            SET balance = ?
            WHERE id = ?
            """,
            (
                new_balance,
                customer["id"],
            ),
        )

        # Finalize only if still draft
        cursor.execute(
            """
            UPDATE bills
            SET payment_mode = ?,
                payment_amount = ?,
                payment_reference = ?,
                status = 'finalized'
            WHERE id = ?
              AND status = 'draft'
            """,
            (
                "credit",
                0,
                "KHATA",
                bill_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.rollback()

            return {
                "success": False,
                "message": (
                    "Credit bill could not be finalized. "
                    "It may have already been finalized."
                ),
            }

        conn.commit()

        return {
            "success": True,
            "message": (
                f"Credit Bill #{bill_id} finalized successfully."
            ),
            "bill_id": bill_id,
            "customer_name": customer["name"],
            "bill_total": bill_total,
            "previous_balance": old_balance,
            "new_balance": new_balance,
            "payment_mode": "credit",
            "status": "finalized",
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e),
        }

    finally:
        conn.close()


def _recalculate_bill_totals(
    cursor,
    bill_id: int,
) -> None:
    """Recalculate bill subtotal, GST, CGST, SGST and total."""

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(quantity * unit_price), 0) AS subtotal,
            COALESCE(SUM(gst_amount), 0) AS gst_amount
        FROM bill_items
        WHERE bill_id = ?
        """,
        (bill_id,),
    )

    totals = cursor.fetchone()

    subtotal = round(
        totals["subtotal"],
        2,
    )

    gst_amount = round(
        totals["gst_amount"],
        2,
    )

    cgst_amount = round(
        gst_amount / 2,
        2,
    )

    sgst_amount = round(
        gst_amount - cgst_amount,
        2,
    )

    total_amount = round(
        subtotal + gst_amount,
        2,
    )

    cursor.execute(
        """
        UPDATE bills
        SET subtotal = ?,
            gst_amount = ?,
            cgst_amount = ?,
            sgst_amount = ?,
            total_amount = ?
        WHERE id = ?
        """,
        (
            subtotal,
            gst_amount,
            cgst_amount,
            sgst_amount,
            total_amount,
            bill_id,
        ),
    )