
    




from orders.models import OrderAmount
from accounts.models import Rating, Testimonial

def check_order_amount_exists(user_id):
    """
    Check if any OrderAmount exists for the given customer (user_id).
    """
    return OrderAmount.objects.filter(customer_id=user_id).exists()

def get_top_ratings():
    """
    Get the top 5 ratings ordered by id in descending order.
    """
    ratings = Rating.objects.order_by('-id')[:5]
    return list(ratings.values())



def get_latest_testimonials():
    """
    Get the latest 5 testimonials ordered by created_at in descending order.
    """
    testimonials = Testimonial.objects.order_by('-created_at')[:5]
    return list(testimonials.values())



from accounts.models import Catalog, Testimonial, Inventory

def insert_catalog(name, description, supplier_id):
    """
    Insert a new catalog using Django ORM.
    """
    Catalog.objects.create(name=name, description=description, supplier_id=supplier_id)
    print("Catalog entry added successfully!")


def insert_catalog_with_image(name, file, description, supplier_id):
    """
    Insert a new catalog with an image using Django ORM.
    """
    try:
        Catalog.objects.create(name=name, catalog_file=file, description=description, supplier_id=supplier_id)
        print("successful")
    except Exception as e:
        print(f"Error saving image: {str(e)}")



def save_image_to_db(uploaded_file, image_name):
    """
    Saves an uploaded image to the database using Django ORM.
    """
    from accounts.models import Image
    try:
        image_data = uploaded_file.read()
        Image.objects.create(image_data=image_data, image_name=image_name)
        print(f"Image '{image_name}' saved successfully!")
    except Exception as e:
        print(f"Error saving image: {str(e)}")



def get_image_by_id(image_id):
    """
    Fetch the image from the database by ID using Django ORM.
    """
    from accounts.models import Image
    try:
        image = Image.objects.filter(id=image_id).first()
        if image:
            print(f"Image '{image.image_name}' fetched successfully!")
            return image
        else:
            print("Image not found.")
            return None
    except Exception as e:
        print(f"Error fetching image: {str(e)}")
        return None


def get_catalog_by_pk(pk):
    """
    Get a catalog by its primary key using Django ORM.
    """
    catalog = Catalog.objects.filter(pk=pk).first()
    if catalog:
        print("Catalog found:", catalog)
        return catalog
    else:
        print(f"Catalog with pk={pk} not found.")
        return None


def get_inventory_by_supplier(supplier_id):
    """
    Get inventory items for a supplier using Django ORM.
    """
    inventory = Inventory.objects.filter(catalog__supplier_id=supplier_id)
    if inventory.exists():
        print("Inventory found:", list(inventory.values()))
        return list(inventory.values())
    else:
        print(f"No inventory found for supplier_id={supplier_id}.")
        return []


def get_low_stock_inventories(low_quantity_threshold):
    """
    Get inventories with low stock using Django ORM.
    """
    low_stock = Inventory.objects.filter(quantity_in_stock__lte=low_quantity_threshold)
    if low_stock.exists():
        print("Low stock inventories found:", list(low_stock.values()))
        return list(low_stock.values())
    else:
        print(f"No inventories found with quantity_in_stock <= {low_quantity_threshold}.")
        return []

def get_catalogs_by_supplier(user_id):
    """
    Fetch catalogs for a specific supplier using Django ORM.
    """
    catalogs = Catalog.objects.filter(supplier_id=user_id)
    return list(catalogs.values())


def get_catalogs_by_id(id):
    """
    Fetch catalogs by CatalogID using Django ORM.
    """
    catalogs = Catalog.objects.filter(pk=id)
    return list(catalogs.values())


def get_inventories(supplier_id):
    """
    Get inventories for a farmer (supplier) using Django ORM.
    """
    inventories = Inventory.objects.filter(farmer_id=supplier_id)
    if inventories.exists():
        print("inventories found:", list(inventories.values()))
        return list(inventories.values())
    else:
        print(f"No inventories found for supplier_id={supplier_id}.")
        return []


def get_inventories_by_id(id):
    """
    Get inventories by inventory id using Django ORM.
    """
    inventories = Inventory.objects.filter(id=id)
    if inventories.exists():
        print("inventories found:", list(inventories.values()))
        return list(inventories.values())
    else:
        print(f"No inventories found for id={id}.")
        return []


def save_barcode_to_db(inventory_id, barcode_data):
    """
    Update the image field of an inventory item using Django ORM.
    """
    try:
        inventory = Inventory.objects.get(id=inventory_id)
        inventory.image = barcode_data
        inventory.save()
        print(f"Barcode saved successfully for Inventory ID: {inventory_id}")
    except Exception as e:
        print(f"Error saving barcode to the database: {e}")


from datetime import datetime
def insert_inventory(name, cost_per_item, quantity_in_stock, quantity_sold, sales, catalog_id, farmer_id):
    """
    Insert a new inventory item using Django ORM.
    """
    stock_date = datetime.now().date()
    last_sales_date = datetime.now().date()
    is_deleted = 0
    try:
        Inventory.objects.create(
            name=name,
            cost_per_item=cost_per_item,
            quantity_in_stock=quantity_in_stock,
            quantity_sold=quantity_sold,
            sales=sales,
            last_sales_date=last_sales_date,
            stock_date=stock_date,
            is_deleted=is_deleted,
            catalog_id=catalog_id,
            farmer_id=farmer_id
        )
        print("Inventory item inserted successfully!")
    except Exception as e:
        print(f"Error inserting inventory item: {e}")


def get_testimonial_by_id(inventory_id):
    """
    Get testimonials by inventory_id using Django ORM.
    """
    testimonials = Testimonial.objects.filter(inventory_id=inventory_id)
    if testimonials.exists():
        return list(testimonials.values())
    else:
        print(f"No testimonial found for inventory_id={inventory_id}.")
        return []

def insert_testimonial(text, rating, inventory_id, user_id, username):
    """
    Insert a new testimonial using Django ORM.
    """
    created_at = datetime.now()
    try:
        Testimonial.objects.create(
            text=text,
            rating=rating,
            created_at=created_at,
            inventory_id=inventory_id,
            user_id=user_id,
            username=username
        )
        print("Testimonial inserted successfully!")
    except Exception as e:
        print(f"Error inserting testimonial: {e}")



def update_testimonials(id, text, rating):
    """
    Update a testimonial using Django ORM.
    """
    created_at = datetime.now()
    try:
        testimonial = Testimonial.objects.get(id=id)
        testimonial.text = text
        testimonial.rating = rating
        testimonial.created_at = created_at
        testimonial.save()
        print("Testimonial updated successfully!")
    except Exception as e:
        print(f"Error updating testimonial: {e}")


def delete_testimonials(id):
    """
    Delete a testimonial using Django ORM.
    """
    try:
        testimonial = Testimonial.objects.get(id=id)
        testimonial.delete()
        return {"message": "success"}
    except Exception as e:
        print(f"Error deleting testimonial: {e}")
        return {"message": "error"}



def get_testimonial_by_its_id(id):
    """
    Get testimonial by its id using Django ORM.
    """
    testimonials = Testimonial.objects.filter(id=id)
    if testimonials.exists():
        return list(testimonials.values())
    else:
        print(f"No testimonial found for id={id}.")
        return []


def delete_inventory(id):
    """
    Delete an inventory item using Django ORM.
    """
    try:
        inventory = Inventory.objects.get(id=id)
        inventory.delete()
        return {"message": "success"}
    except Exception as e:
        print(f"Error deleting inventory: {e}")
        return {"message": "error"}


def get_inventory_by_supplier(user_id):
    """
    Get inventory by supplier's user_id using Django ORM.
    """
    inventory = Inventory.objects.filter(farmer_id=user_id)
    if inventory.exists():
        return list(inventory.values())
    else:
        print(f"No inventory found for user_id={user_id}.")
        return []


def get_inventory_by_name(searched):
    """
    Filter inventory by name using Django ORM.
    """
    inventory = Inventory.objects.filter(name__icontains=searched)
    if inventory.exists():
        return list(inventory.values())
    else:
        print(f"No inventory found for name containing '{searched}'.")
        return []


def get_inventory_by_supplierid(supplier_id):
    """
    Retrieves inventory details for a given supplier using Django ORM.
    """
    inventory = Inventory.objects.filter(catalog__supplier_id=supplier_id)
    if inventory.exists():
        return list(inventory.values())
    else:
        print(f"No inventory found for supplier_id={supplier_id}.")
        return []


def update_billing_email(customer_name, email):
    """
    Updates the billing_email of invoices where the billing_name matches the given customer_name using Django ORM.
    """
    from orders.models import Invoice
    try:
        Invoice.objects.filter(billing_name=customer_name).update(billing_email=email)
        print(f"Updated billing_email to {email} for customer {customer_name}")
    except Exception as e:
        print(f"Error updating billing_email: {e}")


def update_cart_customer(customer_name, new_customer):
    """
    Updates the customer field in the cart table where the customer matches the given customer_name using Django ORM.
    """
    from orders.models import Cart
    try:
        Cart.objects.filter(customer=customer_name).update(customer=new_customer)
        print(f"Updated customer to {new_customer} for entries where customer was {customer_name}")
    except Exception as e:
        print(f"Error updating cart customer: {e}")

















