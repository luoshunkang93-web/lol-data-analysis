import snowflake.connector
import getpass

# 1. Prompt for password to avoid hardcoding credentials in plain text (Security Best Practice)
user_password = getpass.getpass("Enter your Snowflake password: ")

try:
    # 2. Establish the connection to the Snowflake Cloud
    conn = snowflake.connector.connect(
        user='kksnow',             # <-- Replace with your Snowflake login username
        password=user_password,           
        account='JKNNMCM-ORC24346',       # <-- Your unique account identifier
        warehouse='LOL_WH',               # The compute engine we created
        database='LOL_CLOUD_DB',          # The database we created
        schema='PUBLIC'                   # The default schema
    )

    # 3. Create a cursor to execute SQL commands
    cursor = conn.cursor()

    # 4. Execute a simple test query to get the Snowflake version
    cursor.execute("SELECT CURRENT_VERSION()")
    snowflake_version = cursor.fetchone()[0]

    print("=" * 50)
    print(f"✅ SUCCESS! Successfully connected to Snowflake Cloud!")
    print(f"❄️ Snowflake Version: {snowflake_version}")
    print("=" * 50)

except Exception as e:
    print("❌ CONNECTION FAILED:")
    print(e)

finally:
    # 5. Always close the connection to prevent resource leaks
    if 'conn' in locals() and conn:
        conn.close()
        print("🔒 Connection closed safely.")