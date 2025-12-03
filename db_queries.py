import pypyodbc
from datetime import datetime
from flask import jsonify
import json

import pyodbc
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

DRIVER_NAME='SQL SERVER'
SERVER_NAME='APB-JBS02-113L\SQLEXPRESS'
DATABASE_NAME='inventory'

connection_string=F"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trust_Connection=yes
"""



def get_connection():
    conn = pypyodbc.connect(connection_string)
    print('my db connection ', conn)
    return conn




def get_catalog_by_supplier(user_id):
    
    # Establish connection
    conn = get_connection()

    # Create a cursor object
    cursor = conn.cursor()

    # SQL query to filter catalogs by supplier with SELECT *
    query = '''
    SELECT * 
    FROM 
        Catalog 
    WHERE 
        SupplierID = ?
    '''

    # Execute the query with the user_id as a parameter
    cursor.execute(query, (user_id,))

    # Fetch all results
    rows = cursor.fetchall()

    # Get the column names from the cursor description
    columns = [column[0] for column in cursor.description]

    # Close the connection
    conn.close()

    # Return results as a list of dictionaries with column names as keys
    result = [dict(zip(columns, row)) for row in rows]

    return result

import pyodbc

def check_order_amount_exists(user_id):
    # Establish connection
    conn = get_connection()

    # Create a cursor object
    cursor = conn.cursor()

    # SQL query to check if any record exists for the given customer
    query = '''
    SELECT COUNT(*) 
    FROM OrderAmount 
    WHERE customer_id = ?
    '''

    # Execute the query with the logged_user as a parameter
    cursor.execute(query, (user_id,))

    # Fetch the result
    exists = cursor.fetchone()[0] > 0

    # Close the connection
    conn.close()

    return exists

def get_top_ratings():
    # Establish connection
    conn = get_connection()

    # Create a cursor object
    cursor = conn.cursor()

    # SQL query to get the top 5 ratings ordered by id in descending order
    query = '''
    SELECT TOP 5 * 
    FROM accounts_rating
    ORDER BY id DESC;
    '''

    # Execute the query
    cursor.execute(query)

    # Fetch column names
    columns = [column[0] for column in cursor.description]

    # Fetch all rows
    rows = cursor.fetchall()

    # Convert rows to a list of dictionaries
    results = [dict(zip(columns, row)) for row in rows]

    # Close the connection
    conn.close()

    # Return the results
    return results



def get_latest_testimonials():
    
    # Establish connection
    conn = get_connection()

    # Create a cursor object
    cursor = conn.cursor()

    # SQL query to get the top 5 testimonials ordered by created_at in descending order
    query = '''
    SELECT TOP 5 *
    FROM accounts_testimonial
    ORDER BY created_at DESC;
    '''

    # Execute the query
    cursor.execute(query)

    # Fetch column names
    columns = [column[0] for column in cursor.description]

    # Fetch all rows
    rows = cursor.fetchall()

    # Convert rows to a list of dictionaries
    results = [dict(zip(columns, row)) for row in rows]

    # Close the connection
    conn.close()

    # Return the results
    return results


def insert_catalog(name,description, supplier_id):
    # Establish connection
    conn = get_connection()

    # Create a cursor object
    cursor = conn.cursor()

    # SQL query to insert a new row into the Catalog table
    query = '''
    INSERT INTO Catalog (Name, Description, SupplierID)
    VALUES (?, ?, ?)
    '''
    #name, is_deleted, description, catalog_file, supplier_id
    # Execute the query with parameterized values
    cursor.execute(query, (name,description, supplier_id))

    # Commit the transaction
    conn.commit()

    # Close the connection
    conn.close()

    print("Catalog entry added successfully!")


def insert_catalog_with_image(name,file,description, supplier_id):
    # Establish connection
    conn = get_connection()
    # Create a cursor object
    cursor = conn.cursor()
    try:
       
            # SQL query to insert a new row into the Catalog table
        query = '''
            INSERT INTO Catalog (Name,CatalogFile, Description, SupplierID)
            VALUES (?,?, ?, ?)
            '''
            #name, is_deleted, description, catalog_file, supplier_id
            # Execute the query with parameterized values
        cursor.execute(query, (name,file,description, supplier_id))

            # Commit the transaction
        conn.commit()
        print("succesfull")

    except Exception as e:
        print(f"Error saving image: {str(e)}")

    finally:
        # Close the database connection
        conn.close()



def save_image_to_sql_server(uploaded_file, image_name):
    """
    Saves an uploaded image to a SQL Server database as VARBINARY.
    """

    try:
        # Convert the uploaded file to binary data (Base64 decoding)
        image_data = uploaded_file.read()

        # Establish SQL Server connection
        conn = get_connection()

        # Create a cursor object
        cursor = conn.cursor()

        # SQL query to insert the image data into the database
        query = '''
        INSERT INTO Images (image_data, image_name)
        VALUES (?, ?)
        '''

        # Execute the query, passing the image binary data and name
        cursor.execute(query, (image_data, image_name))

        # Commit the transaction
        conn.commit()

        print(f"Image '{image_name}' saved successfully!")

    except Exception as e:
        print(f"Error saving image: {str(e)}")

    finally:
        # Close the database connection
        conn.close()



def get_image_from_sql_server(image_id):
    """
    Fetch the image from SQL Server by ID and return it as a ContentFile.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Query to fetch image data by ID
        query = "SELECT image_data, image_name FROM Images WHERE id = ?"
        cursor.execute(query, (image_id,))

        # Fetch the image data and name
        row = cursor.fetchone()

        if row:
            image_data = row[0]
            image_name = row[1]

            # Create a ContentFile from the binary data
            image_file = ContentFile(image_data)

            print(f"Image '{image_name}' fetched successfully!")
            return image_file

        else:
            print("Image not found.")
            return None

    except Exception as e:
        print(f"Error fetching image: {str(e)}")
        return None

    finally:
        conn.close()


def get_catalog_by_pk(pk):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get Catalog by pk
        query = '''
        SELECT *
        FROM Catalog
        WHERE SupplierID = ?  -- using 'id' for primary key
        '''
        # Execute the query with the pk value as a parameter
        cursor.execute(query, (pk,))
        
        # Fetch the result
        catalog = cursor.fetchone()

        if catalog:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert result to a dictionary with column names as keys
            catalog_data = dict(zip(columns, catalog))
            print("Catalog found:", catalog_data)
            return catalog_data
        else:
            print(f"Catalog with pk={pk} not found.")
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    finally:
        # Close the connection
        conn.close()


def get_inventory_by_supplier(supplier_id):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventory based on supplier ID
        query = '''
        SELECT inv.*
        FROM inventory inv
        INNER JOIN Catalog cat ON inv.catalog_id = cat.CatalogID
        WHERE cat.SupplierID = ?
        '''
        # Execute the query with the supplier ID as a parameter
        cursor.execute(query, (supplier_id,))
        
        # Fetch all matching results
        rows = cursor.fetchall()

        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            inventory_data = [dict(zip(columns, row)) for row in rows]
            print("Inventory found:", inventory_data)
            return inventory_data
        else:
            print(f"No inventory found for supplier_id={supplier_id}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()


def get_low_stock_inventories(low_quantity_threshold):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventories with low stock
        query = '''
        SELECT *
        FROM inventory
        WHERE quantity_in_stock <= ?
        '''
        # Execute the query with the threshold as a parameter
        cursor.execute(query, (low_quantity_threshold,))
        
        # Fetch all matching results
        rows = cursor.fetchall()

        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            low_stock_inventories = [dict(zip(columns, row)) for row in rows]
            print("Low stock inventories found:", low_stock_inventories)
            return low_stock_inventories
        else:
            print(f"No inventories found with quantity_in_stock <= {low_quantity_threshold}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()

def get_catalogs_by_supplier(user_id):
    """
    Fetch catalogs for a specific supplier from the database.

    :param user_id: ID of the supplier (user)
    :return: List of catalogs belonging to the supplier
    """
    # Establish connection
    conn = get_connection()  # Replace with your connection function
    cursor = conn.cursor()

    try:
        # SQL query to fetch catalogs for the given supplier
        query = '''
        SELECT * FROM Catalog WHERE SupplierID = ?
        '''

        # Execute the query with the supplier's user ID
        cursor.execute(query, (user_id,))

        # Fetch all results
        catalogs = cursor.fetchall()

        # Optionally, fetch column names for better result formatting
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in catalogs]

        return result

    except Exception as e:
        print(f"Error fetching catalogs: {e}")
        return []

    finally:
        # Close the connection
        conn.close()


def get_catalogs_by_id(id):
    """
    Fetch catalogs for a specific supplier from the database.

    :param user_id: ID of the supplier (user)
    :return: List of catalogs belonging to the supplier
    """
    # Establish connection
    conn = get_connection()  # Replace with your connection function
    cursor = conn.cursor()

    try:
        # SQL query to fetch catalogs for the given supplier
        query = '''
        SELECT * FROM Catalog WHERE CatalogID = ?
        '''

        # Execute the query with the supplier's user ID
        cursor.execute(query, (id,))

        # Fetch all results
        catalogs = cursor.fetchall()

        # Optionally, fetch column names for better result formatting
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in catalogs]

        return result

    except Exception as e:
        print(f"Error fetching catalogs: {e}")
        return []

    finally:
        # Close the connection
        conn.close()


def get_inventories(supplier_id):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventories with low stock
        query = '''
        SELECT *
        FROM inventory
        WHERE farmer_id=?
        '''
        # Execute the query with the threshold as a parameter
        cursor.execute(query, [supplier_id])
        
        # Fetch all matching results
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            inventories = [dict(zip(columns, row)) for row in rows]
            print("inventories found:", inventories)
            return inventories
        else:
            print(f"No inventories found  {inventories}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()


def get_inventories_by_id(id):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventories with low stock
        query = '''
        SELECT *
        FROM inventory
        WHERE id=?
        '''
        # Execute the query with the threshold as a parameter
        cursor.execute(query, [id])
        
        # Fetch all matching results
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            inventories = [dict(zip(columns, row)) for row in rows]
            print("inventories found:", inventories)
            return inventories
        else:
            print(f"No inventories found  {inventories}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()


def save_barcode_to_db(inventory_id, barcode_data):
    try:
      
        # SQL query to update the database
        query = '''
        UPDATE inventory
        SET image = ?
        WHERE id = ?
        '''

        # Execute query
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (barcode_data, inventory_id))
        conn.commit()

        print(f"Barcode saved successfully for Inventory ID: {inventory_id}")

    except Exception as e:
        print(f"Error saving barcode to the database: {e}")

    finally:
        if conn:
            conn.close()


def insert_inventory(name, cost_per_item, quantity_in_stock, quantity_sold,sales,catalog_id,farmer_id):
    # Establish a connection to the database
    conn = get_connection()
    cursor = conn.cursor()
    stock_date = datetime.now().date()
    last_sales_date=datetime.now().date()
    is_deleted=0
    try:
        # Insert data into the Inventory table
        query = '''
            INSERT INTO inventory (name, cost_per_item, quantity_in_stock, quantity_sold,sales,last_sales_date,stock_date,is_deleted,catalog_id,farmer_id)
            VALUES (?, ?, ?, ?,?,?,?,?,?,?)
        '''
        cursor.execute(query, (name, cost_per_item, quantity_in_stock, quantity_sold,sales,last_sales_date,stock_date,is_deleted,catalog_id,farmer_id))

        # Commit the transaction to the database
        conn.commit()
        print("Inventory item inserted successfully!")

    except Exception as e:
        print(f"Error inserting inventory item: {e}")
        conn.rollback()

    finally:
        # Close the database connection
        conn.close()


def get_testimonial_by_id(inventory_id):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventories with low stock
        query = '''
        SELECT * 
        FROM accounts_testimonial 
        WHERE inventory_id = ?

        '''
        # Execute the query with the threshold as a parameter
        cursor.execute(query, [inventory_id])
        
        # Fetch all matching results
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            testimonial = [dict(zip(columns, row)) for row in rows]
            
            return testimonial
        else:
            print(f"No testimonial found  {testimonial}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()

def insert_testimonial(text, rating,inventory_id,user_id,username):
    conn = get_connection()
    cursor = conn.cursor()
    created_at=datetime.now()
    try:
        query="""
                INSERT INTO accounts_testimonial (text, rating, created_at,inventory_id,user_id,username)
                VALUES (?, ?, ?,?,?,?)
            """
        cursor.execute(query,[text, rating,created_at,inventory_id,user_id,username])
                    
        conn.commit()
        print("Inventory item inserted successfully!")

    except Exception as e:
        print(f"Error inserting inventory item: {e}")
        conn.rollback()

    finally:
        # Close the database connection
        conn.close()



def update_testimonials(id, text, rating):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now()  # To record when the update happens
    
    try:
        # Update query to modify the existing testimonial record based on the testimonial_id
        query = """
            UPDATE accounts_testimonial
            SET text=?, rating=?, created_at=?
            WHERE id = ?
        """
        
        cursor.execute(query, [id,text, rating, created_at])

        conn.commit()
        print("Testimonial updated successfully!")

    except Exception as e:
        print(f"Error updating testimonial: {e}")
        conn.rollback()

    finally:
        # Close the database connection
        conn.close()


def delete_testimonials(id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Update query to modify the existing testimonial record based on the testimonial_id
        query = """
            DELETE FROM accounts_testimonial
            WHERE id = ?
        """
        
        cursor.execute(query, [id])  # Pass the ID as a parameter

        conn.commit()  # Commit the changes to the database
        return {"message":"success"}

    except Exception as e:
        # Log the error and rollback the transaction in case of failure
        print(f"Error deleting testimonial: {e}")
        conn.rollback()

    finally:
        # Ensure the database connection is closed
        conn.close()



def get_testimonial_by_its_id(id):
    # Establish connection
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL query to get inventories with low stock
        query = '''
        SELECT * 
        FROM accounts_testimonial 
        WHERE id = ?

        '''
        # Execute the query with the threshold as a parameter
        cursor.execute(query, [id])
        
        # Fetch all matching results
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            testimonial = [dict(zip(columns, row)) for row in rows]
            
            return testimonial
        else:
            print(f"No testimonial found  {testimonial}.")
            return []
        
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    finally:
        # Close the connection
        conn.close()


def delete_inventory(id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Update query to modify the existing testimonial record based on the testimonial_id
        query = """
            DELETE FROM inventory
            WHERE id = ?
        """
        
        cursor.execute(query, [id])  # Pass the ID as a parameter

        conn.commit()  # Commit the changes to the database
        return {"message":"success"}

    except Exception as e:
        # Log the error and rollback the transaction in case of failure
        print(f"Error deleting inventory: {e}")
        conn.rollback()

    finally:
        # Ensure the database connection is closed
        conn.close()


def get_inventory_by_supplier(user_id):
    # Define the connection to your SQL Server database
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQL Query to fetch inventory by supplier's user_id
    query = """
        SELECT i.*
        FROM inventory i
        JOIN Catalog c ON i.catalog_id = c.CatalogID
        WHERE i.farmer_id = ?
    """
    
    try:
        # Execute the SQL query with the supplier_user_id as a parameter
        cursor.execute(query, (user_id,))
        
        # Fetch the results
        rows = cursor.fetchall()
        if rows:
            # Get column names
            columns = [column[0] for column in cursor.description]

            # Convert results to a list of dictionaries
            inventory = [dict(zip(columns, row)) for row in rows]
           
            return inventory
        else:
            print(f"No inventory found  {inventory}.")
            return []
    except Exception as e:
        print(f"Error retrieving inventory: {e}")
        return None, None
    
    finally:
        # Close the database connection
        cursor.close()
        conn.close()


def get_inventory_by_name(searched):
    # Define the connection to your SQL Server database
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQL Query to filter inventory by name
    query = """
        SELECT * 
        FROM inventory 
        WHERE name LIKE ?
    """
    
    try:
        # Prepare the search term with wildcards
        search_term = f"%{searched}%"  # '%searched%' for SQL LIKE
        cursor.execute(query, (search_term,))
        
        # Fetch the results
        rows = cursor.fetchall()
        
        # Retrieve the column names
        columns = [column[0] for column in cursor.description]
        
        # Print or return the result (rows) and column names (columns)
        return columns, rows
    
    except Exception as e:
        print(f"Error retrieving inventory: {e}")
        return None, None
    
    finally:
        # Close the database connection
        cursor.close()
        conn.close()


def get_inventory_by_supplierid(supplier_id):
    """
    Retrieves inventory details for a given supplier.
    """
    query = """
        SELECT inventory.id, inventory.name, inventory.cost_per_item,
               inventory.quantity_in_stock, inventory.quantity_sold,
               inventory.barcode, inventory.image, inventory.catalog_id
        FROM inventory
        INNER JOIN catalog ON inventory.catalog_id = catalog.id
        WHERE catalog.SupplierID = ?;
    """
    conn = get_connection()  # Replace with your database connection logic
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, [supplier_id])
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]  # Fetch column names
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching inventory: {e}")
    finally:
        conn.close()


def update_billing_email(customer_name, email):
    """
    Updates the billing_email of invoices where the billing_name matches the given customer_name.
    """
    query = """
        UPDATE Invoice
        SET billing_email = ?
        WHERE billing_name = ?;
    """
    conn = get_connection()  # Replace with your database connection logic
    cursor = conn.cursor()

    try:
        cursor.execute(query, [email, customer_name])
        conn.commit()
        print(f"Updated billing_email to {email} for customer {customer_name}")
    except Exception as e:
        print(f"Error updating billing_email: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()


def update_cart_customer(customer_name, new_customer):
    """
    Updates the customer field in the cart table where the customer matches the given customer_name.
    """
    query = """
        UPDATE cart
        SET customer = ?
        WHERE customer = ?;
    """
    conn = get_connection()  # Replace with your database connection logic
    cursor = conn.cursor()

    try:
        cursor.execute(query, [new_customer, customer_name])
        conn.commit()
        print(f"Updated customer to {new_customer} for entries where customer was {customer_name}")
    except Exception as e:
        print(f"Error updating cart customer: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

















