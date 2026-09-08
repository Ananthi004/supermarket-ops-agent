from app.database import get_connection


def set_owner_preference(key: str, value: str) -> dict:
    """
    Save or update an owner preference.
    """

    if not key or not key.strip():
        return {
            "success": False,
            "message": "Preference key cannot be empty."
        }

    if value is None or not str(value).strip():
        return {
            "success": False,
            "message": "Preference value cannot be empty."
        }

    key = key.strip().lower()
    value = str(value).strip()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO owner_preferences (key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """,
            (key, value)
        )

        conn.commit()

        return {
            "success": True,
            "message": f"Owner preference '{key}' saved successfully.",
            "key": key,
            "value": value
        }

    except Exception as e:
        conn.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def get_owner_preference(key: str) -> dict:
    """
    Retrieve one owner preference.
    """

    if not key or not key.strip():
        return {
            "success": False,
            "message": "Preference key cannot be empty."
        }

    key = key.strip().lower()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT key, value
            FROM owner_preferences
            WHERE key = ?
            """,
            (key,)
        )

        row = cursor.fetchone()

        if not row:
            return {
                "success": False,
                "message": f"No preference found for '{key}'."
            }

        return {
            "success": True,
            "key": row["key"],
            "value": row["value"]
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()


def get_all_owner_preferences() -> dict:
    """
    Retrieve all saved owner preferences.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT key, value
            FROM owner_preferences
            ORDER BY key
            """
        )

        rows = cursor.fetchall()

        preferences = {
            row["key"]: row["value"]
            for row in rows
        }

        return {
            "success": True,
            "preferences": preferences
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        conn.close()