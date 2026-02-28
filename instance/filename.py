import sqlite3

# Connect to the database file
conn = sqlite3.connect("events.db")  # replace with your .db file path
cursor = conn.cursor()

# List all tables in the database
print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print("-", table[0])

print("\nContents of each table:\n")

# Loop through each table and display its contents
for table in tables:
    table_name = table[0]
    print(f"Table: {table_name}")
    
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [info[1] for info in cursor.fetchall()]
    print("Columns:", columns)
    
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("(No data)")
    
    print("-" * 40)

# Close connection
conn.close()