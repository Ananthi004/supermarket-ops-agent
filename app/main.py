from .database import init_database


def main():
    print("Starting Supermarket Ops Agent...")

    init_database()

    print("Supermarket Ops Agent started successfully.")


if __name__ == "__main__":
    main()