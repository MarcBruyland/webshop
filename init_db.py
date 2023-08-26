import sqlite3

connection = sqlite3.connect('instance/webshop.db')  # file path

# create a cursor object from the cursor class
cur = connection.cursor()

cur.execute('''
   CREATE TABLE User(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       name TEXT NOT NULL, 
       email TEXT NOT NULL, 
       password TEXT NOT NULL,    
       token TEXT NULL,    
       token_expiration_date TEXT NULL,
       address TEXT not NULL
   )''')

cur.execute('''
   CREATE TABLE Product(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       name TEXT NOT NULL,
       description TEXT NULL,
       price FLOAT NOT NULL, 
       picture TEXT NOT NULL, 
       id_price_prod TEXT NOT NULL,
       id_price_test TEXT NOT NULL
   )''')

# status Order: initiated, paid, completed
# status OrderLine: initiated, shipped, delivered
# status OrderEvent: initiated, paid, shipped, delivered, completed


cur.execute('''
   CREATE TABLE ShopOrder(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       id_user INTEGER NOT NULL,
       shipping_address TEXT NULL,
       status TEXT NOT NULL
   )''')

cur.execute('''
   CREATE TABLE OrderLine(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
       id_order INTEGER NOT NULL,
       seq_nr_order_line INTEGER NOT NULL,
       id_product INTEGER NOT NULL,
       quantity INTEGER NOT NULL,
       status TEXT NOT NULL
   )''')

cur.execute('''
   CREATE TABLE OrderEvent(
       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
       date TEXT NOT NULL, 
       id_order INTEGER NOT NULL,
       id_order_line INTEGER NULL,
       comment TEXT NULL,
       status TEXT NOT NULL
   )''')

cur.execute('''
   INSERT INTO Product (name, description, price, picture, id_price_prod, id_price_test)
          VALUES( "ball", "Soccer ball." , 4.99, "ball.jpg", "price_1NgxRAGEFG1czw226XsXIOyx", "price_1NhJFUGEFG1czw22THKNjN0E")                                                              
   ''')

cur.execute('''
   INSERT INTO Product (name, description, price, picture, id_price_prod, id_price_test)
          VALUES( "doll", "Doll that can talk and cry." , 5.25, "doll.jpg", "price_1NhJJKGEFG1czw22Y0Xrlo3N", "price_1NhJKXGEFG1czw222EaydIVK")
   ''')

cur.execute('''
   INSERT INTO Product (name, description, price, picture, id_price_prod, id_price_test)
          VALUES( "car", "Police car" , 6.15, "car.jpg", "price_1NhJM6GEFG1czw22vEzfqSCg", "price_1NhJNBGEFG1czw22vxYBieDw")
   ''')


# cur.execute('''
#     INSERT INTO ShopOrder (id_user, shipping_address, status) VALUES (1, "Arendlaan 33, 8440 Westende-Bad", "created")
#   ''')

print("\nDatabase created successfully!!!")
# committing our connection
connection.commit()

# close our connection
connection.close()
