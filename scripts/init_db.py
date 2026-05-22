#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database initialization and connection waiter for PhreakBot."""

import os
import sys
import time
import psycopg2


def main():
    # Read environment variables matching those used by PhreakBot
    db_host = os.environ.get("DB_HOST", "postgres")
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_user = os.environ.get("DB_USER", "phreakbot")
    db_password = os.environ.get("DB_PASSWORD", "phreakbot")
    db_name = os.environ.get("DB_NAME", "phreakbot")

    print(f"Connecting to database '{db_name}' at {db_host}:{db_port} as user '{db_user}'...")

    # Wait for PostgreSQL to start up and accept connections
    conn = None
    retries = 30
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                dbname=db_name,
                connect_timeout=3
            )
            print("Successfully connected to the database!")
            break
        except Exception as e:
            print(f"Database connection failed: {e}. Retrying in 2 seconds ({retries} retries left)...")
            retries -= 1
            time.sleep(2)

    if not conn:
        print("Error: Could not connect to PostgreSQL database after several attempts.", file=sys.stderr)
        sys.exit(1)

    try:
        cur = conn.cursor()
        # Check if the database schema is already initialized
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'phreakbot_users')")
        table_exists = cur.fetchone()[0]

        if table_exists:
            print("Database schema already exists. Skipping initialization.")
        else:
            print("Database schema does not exist. Creating schema...")
            # We look for the schema file
            schema_paths = ["/app/dbschema.psql", "dbschema.psql"]
            schema_path = None
            for path in schema_paths:
                if os.path.exists(path):
                    schema_path = path
                    break

            if not schema_path:
                print("Error: dbschema.psql schema file not found!", file=sys.stderr)
                sys.exit(1)

            print(f"Loading schema from: {schema_path}")
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            cur.execute(schema_sql)
            conn.commit()
            print("Database schema created successfully!")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during database initialization: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
