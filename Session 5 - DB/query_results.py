import psycopg2


connection = psycopg2.connect(host="localhost", database="portfolio_sim", user="postgres", password="")
cursor = connection.cursor()

cursor.execute("SELECT * FROM portfolio_results")
print(cursor.fetchall())
