from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from .models import Catalog, Inventory, SalesData, Subscriber, Rating, Testimonial, Distributor
from orders.models import OrderAmount
from django.shortcuts import get_object_or_404
from .forms import InventoryUpdateForm, AddInventoryForm, SubscriptionForm, BulkEmailForm, CatalogForm, InventoryForm, uploadCatalogForm, DistributorForm, TestimonialForm, SearchForm
from django.conf import settings
from django_pandas.io import read_frame
import pandas as pd
import plotly
import base64
import mimetypes
import plotly.express as px
import uuid
# import openpyxl
from django.core.files import File
# from openpyxl_image_loader import SheetImageLoader
import zipfile
import os
import json
from django.core.mail import send_mail
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile
from barcode.codex import Code128
import csv
from django.core.files.storage import default_storage
from PIL import Image
from matplotlib import pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import requests
import logging
from accounts import views as accounts_views
from user.models import Profile
from user.forms import RegisterForm
import barcode
from barcode.writer import ImageWriter
from db_queries import (
    check_order_amount_exists,
    get_top_ratings,
    get_latest_testimonials,
    insert_catalog,
    insert_catalog_with_image,
    get_catalog_by_pk,
    get_inventory_by_supplier,
    get_low_stock_inventories,
    get_catalogs_by_supplier,
    get_catalogs_by_id,
    get_inventories,
    get_inventories_by_id,
    save_barcode_to_db,
    insert_inventory,
    get_testimonial_by_id,
    insert_testimonial,
    get_testimonial_by_its_id,
    update_testimonials,
    delete_testimonials,
    delete_inventory,
    get_inventory_by_name,
    get_inventory_by_supplierid
)
logging.basicConfig(level=logging.INFO)

LOW_QUANTITY = getattr(settings, 'LOW_QUANTITY', 5)
def index(request):
    user_param = request.GET.get('user')
    
    # user=request.session['user']
    # if 'user_id' in user:
        # logged_user=user
    user_id = user_param
    api_endpoint = 'https://society-ed02.onrender.com/stemuserprofiles'
    url = f"{api_endpoint}/{user_id}"
   
    try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP errors

            user = response.json()
            user.pop('role',None)
            print("user ",user)
            if user:
                if isinstance(user, dict) and 'avatar' in user:
                    user['avatar']=decode_base64_to_image(user['avatar'])
        
                request.session['user']=user
            
    except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
    logged_user = request.session['user']
    print("logged user ",logged_user)
    if "role" not in logged_user:
        form = RegisterForm()
        if form.is_valid():
            role=form.data['role']
            print("role ",role)
        return render(request, 'users/register.html', {'form': form})

    request.session['old_username'] = logged_user['first_name'] +" "+ logged_user['last_name']
   
    # Retrieve cart count for the logged-in user
    if check_order_amount_exists(logged_user['user_id']):   # OrderAmount.objects.filter(customer=logged_user).exists():
        cart_record = check_order_amount_exists(logged_user['user_id']) #get_object_or_404(OrderAmount, customer=logged_user)
        request.session['cart_count'] = cart_record
    else:
        request.session['cart_count'] = 0

    # Retrieve latest ratings and testimonials
    latest_ratings = get_top_ratings() #Rating.objects.all().order_by('-id')[:5]
    latest_testimonials = get_latest_testimonials()   #Testimonial.objects.all().order_by('-created_at')[:5]

    context = {
        'latest_ratings': latest_ratings,
        'latest_testimonials': latest_testimonials,
    }

    return render(request, 'accounts/index.html', context)



def catalog_list(request):
    user=request.session['user']
    catalogs = get_catalogs_by_supplier(user['user_id']) #Catalog.objects.filter(supplier=user)
    return render(request, 'accounts/catalog_list.html', {'catalogs': catalogs})


def catalog_create(request):
    user=request.session['user']
    if request.method == 'POST':
        form = CatalogForm(request.POST)
        if form.is_valid():
            print("form data ",form.data['name'])
            name=form.data['name']
            description=form.data['description']
            supplier_id=user['user_id']
            insert_catalog(name, description, supplier_id)
            #catalog = form.save(commit=False)
            #catalog.supplier = user  #Assign the current user as the supplier
            #catalog.save()
            return redirect('catalog_list')
    else:
        form = CatalogForm()
    return render(request, 'accounts/catalog_create.html', {'form': form})


def upload_catalog(request):
    user=request.session['user']
    if request.method == 'POST':
       
            name = request.POST.get('name')
            description = request.POST.get('description')
            catalog_file = request.FILES.get('catalog_file')
            supplier_id=user['user_id']
            insert_catalog_with_image(name,catalog_file, description, supplier_id)
            #catalog = form.save(commit=False)
            #catalog.supplier = request.user  #Assign the current user as the supplier
            #catalog.save()
            return redirect('extract_catalog_data',pk=supplier_id)
    else:
        form = uploadCatalogForm()
    return render(request, 'accounts/upload_catalog.html', {'form': form})


def extract_catalog_data (request, pk):
    uploaded_catalog = get_catalog_by_pk(pk) #get_object_or_404(Catalog, pk=pk)
    
    file = uploaded_catalog['catalogfile']
    
    catalog_data = pd.read_excel(file)

    # Edit catalog data
    for index, row in catalog_data.iterrows():

        #Fetch images for each product
        image_name = row['image']
        stored_images = 'media/images'
        image_names = os.listdir(stored_images)

        for name in image_names:
            if image_name in name:
                image_path = os.path.join(stored_images, name).replace('\\', '/')
                catalog_data.at[index, 'image'] = image_path
                print("Image found:", image_path) 
    print(catalog_data)

    for index, product in catalog_data.iterrows():       
        #Save to the Inventory
        inventory_data = Inventory(
            catalog = uploaded_catalog,
            name=product['name'],
            cost_per_item=product['cost_per_item'],
            quantity_in_stock=product['quantity_in_stock']
        )
        inventory_data.sales = inventory_data.cost_per_item * inventory_data.quantity_sold
        
        #fetch and upload the images
        print(type(product['image']))
        with open(product['image'], 'rb') as image:
            image_file = File(image)
            inventory_data.image.save(product['image'],image_file, save=True)

        # Generate barcode and save it to the new inventory item
        barcode_data = str(inventory_data.pk) + " " + inventory_data.name  # Barcode data
        code128 = Code128(barcode_data, writer=ImageWriter())
        barcode_image = code128.render()

        # Convert the barcode image to PNG format
        image_io = BytesIO()
        barcode_image.save(image_io, format='PNG')
        barcode_image_file = ContentFile(image_io.getvalue())
        inventory_data.barcode.save(f'barcode_{barcode_data}.png', barcode_image_file, save=False)
        inventory_data.save()
    
    messages.success(request, "Products successfully saved in the inventory")
    return redirect('catalog_list')


def inventory_list(request):
    user=request.session['user']
    
    inventories = get_inventory_by_supplier(user['user_id'])#Inventory.objects.filter(catalog__supplier=user['user_id'])
    
    # Check for low stock items
    low_stock_inventory = get_low_stock_inventories(LOW_QUANTITY)#inventories.filter(quantity_in_stock__lte=LOW_QUANTITY)
   
    if low_stock_inventory:
        # Display a message for each low stock item
        for item in low_stock_inventory:
            messages.warning(request, f"Low stock alert: {item['name']} - quantity in stock: {item['quantity_in_stock']}")

    paginator = Paginator(inventories, 10)  # Show 10 items per page

    page = request.GET.get('page')
    try:
        inventories = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        inventories = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        inventories = paginator.page(paginator.num_pages)
    print("inventories ",inventories)
    return render(request, 'accounts/inventory_list.html', {'inventories': inventories})


def create_inventory(request):
    user=request.session['user']
    from decimal import Decimal,ROUND_DOWN
    from io import BytesIO
    import barcode 
    catalogs=get_catalogs_by_supplier(user['user_id'])
    if request.method == 'POST':
            item_id=request.POST.get('catalog')
            name=request.POST.get('item')
            cost_per_item=request.POST.get('cost_per_item')
            quantity_in_stock=request.POST.get('quantity_in_stock')
            quantity_sold=request.POST.get('quantity_sold')
            image=request.POST.get('image')
            catalog_name=get_catalogs_by_id(item_id)
            
            sales = Decimal(cost_per_item).quantize(Decimal('0.00'), rounding=ROUND_DOWN) * int(quantity_sold)
            
            insert_inventory(name,cost_per_item,quantity_in_stock, quantity_sold,sales,item_id,user['user_id'])
           
            inventory = get_inventories(user['user_id'])
           
            inventory=inventory[0]
            # Generate barcode and save it to the new inventory item
            barcode_data = str(inventory['id']) + " " + inventory['name']  # Barcode data\
            
            
            code128 = Code128(barcode_data, writer=ImageWriter())
            barcode_image = code128.render()
            
            barcode_image_file = BytesIO()
            barcode_image.save(barcode_image_file, format='PNG')
            # Reset the file pointer to the beginning
            barcode_image_file.seek(0)

            binary_image_data = barcode_image_file.read()
            save_barcode_to_db(inventory['id'],binary_image_data)

            messages.success(request, "Successfully Added Product")
            return redirect('inventory_list')
    else:
        
        
        print("catalog ",catalogs)
    return render(request, 'accounts/create_inventory.html', {'catalogs': catalogs})



def add_product(request):
    if request.method == "POST":
        updateForm = AddInventoryForm(request.POST, request.FILES, request.user)
        if updateForm.is_valid():
            new_inventory = updateForm.save(commit=False)
            new_inventory.sales = float(
                updateForm.data['cost_per_item']) * float(updateForm.data['quantity_sold'])

            # Generate barcode and save it to the new inventory item
            # You can modify this based on your barcode data
            barcode_data = new_inventory.name + \
                " " + str(new_inventory.cost_per_item)
            code128 = Code128(barcode_data, writer=ImageWriter())
            image = code128.render()

            # Convert the barcode image to PNG format
            image_io = BytesIO()
            image.save(image_io, format='PNG')
            image_file = ContentFile(image_io.getvalue())
            new_inventory.barcode.save(
                f'barcode_{barcode_data}.png', image_file, save=False)

            new_inventory.save()

            messages.success(request, "Successfully Added Product")
            return redirect('stock')  # You can adjust the redirect URL

    else:
        updateForm = AddInventoryForm(request.user)

    return render(request, 'accounts/inventory_add.html')


def per_product(request, pk):
    inventory = get_inventories_by_id(pk)
    
    output=inventory[0]
    
    context={
        'name':output['name'],
    'quantity_in_stock':output['quantity_in_stock'],
    'quantity_sold':output['quantity_sold'],
    'cost_per_item':output['cost_per_item'],
    'sales':output['sales'],
    'stock_date':inventory[0]['stock_date'],
    'last_sales_date':inventory[0]['last_sales_date'],
    'barcode_data':inventory[0]['barcode'],
    'id':output['id']}
    return render(request, "accounts/per_product.html",context=context)


def each_product(request, pk):
    user=request.session['user']
    
    inventory = get_inventories_by_id(pk)
    testimonials = get_testimonial_by_id(inventory[0]['id'])  #Testimonial.objects.filter(inventory=inventory)
     

    return render(request, "accounts/each_product.html", {'inventory':inventory[0], 'testimonials':testimonials,"user":user})  
    

def write_review(request, pk):
    inventory = get_inventories_by_id(pk) #get_object_or_404(Inventory, pk=pk)
    user=request.session['user']
   
    if request.method == 'POST':
            text=request.POST.get('text')
            rating=request.POST.get('rating')
            username=user['first_name']+ ' '+user['last_name']
            insert_testimonial(text, rating,pk,user['user_id'],username)
            messages.success(request, 'Thank you for your review!')
            return redirect('each_product', pk=pk)  # Redirect to the product detail page
    ratings = [1, 2, 3, 4, 5]

    return render(request, 'accounts/write_review.html', {'ratings':ratings,'inventory': inventory[0]})


def delete_testimonial(request, pk):
   
    # Delete the testimonial using the helper function
    message = delete_testimonials(pk)  # delete_testimonials should return a relevant message or success status
    
    # Check if the deletion was successful
    if message:  # Adjust condition based on your delete_testimonials function's return behavior
        messages.success(request, 'Testimonial deleted successfully.')
    else:
        messages.error(request, 'Failed to delete the testimonial.')

    # Redirect to the desired page
    return redirect('each_product', pk=pk)

def update_testimonial(request, pk):
 
    testimonial = get_testimonial_by_its_id(pk) #get_object_or_404(Testimonial, pk=pk)
   
    new_id=testimonial[0]['inventory_id']
   
    if request.method == 'POST':
        text=request.POST.get('text')
        rating=request.POST.get('rating')
        # testimonial_id, text, rating, inventory_id, user_id, username
        update_testimonials(pk,text, rating)
       
        messages.success(request, 'Thank you for your review!')
        return redirect('each_product', pk=new_id)  
    else:
        messages.error(request, 'You are not authorized to update this testimonial.')
    ratings = [1, 2, 3, 4, 5]
    data={
        'text':testimonial[0]['text'],
        'rating':testimonial[0]['rating'],
        'id':pk
    }
    return render(request, 'accounts/update_testimonial.html',{'ratings':ratings,'data':data})


def products(request):
    catalogs = Catalog.objects.filter(is_deleted=False)  # Fetch all non-deleted catalogs
    context = {
        "title": "Products",
        "catalogs": catalogs
    }
    return render(request, 'orders/products.html', context=context)


def update(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)
    if request.method == "POST":
        updateForm = InventoryUpdateForm(request.POST, request.FILES, instance=inventory)
        if updateForm.is_valid():
            inventory = updateForm.save(commit=False)
            inventory.sales = inventory.cost_per_item * inventory.quantity_sold
            inventory.save()
            messages.success(request, "Update Successful")
            return redirect(reverse('per_product', kwargs={'pk': pk}))
    else:
        updateForm = InventoryUpdateForm(instance=inventory)

    return render(request, 'accounts/inventory_update.html', {'form': updateForm})


def delete(request, pk):
    inventory = delete_inventory(pk) #get_object_or_404(Inventory, pk=pk)
     # Check if the deletion was successful
    if inventory:  # Adjust condition based on your delete_testimonials function's return behavior
        messages.success(request, 'Inventory deleted successfully.')
    else:
        messages.error(request, 'Failed to delete the testimonial.')

    return redirect('inventory_list')


def add_product(request):
    if request.method == "POST":
        updateForm = AddInventoryForm(request.POST, request.FILES)
        if updateForm.is_valid():
            new_inventory = updateForm.save(commit=False)
            new_inventory.sales = new_inventory.cost_per_item * new_inventory.quantity_sold
            new_inventory.save()
            messages.success(request, "Successfully Added Product")
            return redirect('stock')  # You can adjust the redirect URL
    else:
        updateForm = AddInventoryForm()

    return render(request, 'accounts/inventory_add.html', {'form': updateForm})



def dashboard(request):
    user=request.session['user']
    # Get all inventory items
    inventories = get_inventory_by_supplier(user['user_id'])#Inventory.objects.filter(catalog__supplier=supplier['user_id'])
    
    # Check if the inventories are empty
    if not inventories:
        # Handle case where inventory is empty
        context = {
            "message": "No data available for dashboard."
        }
        return render(request, "accounts/empty_dashboard.html", context=context)

    # Convert Inventory queryset to DataFrame
    df = read_frame(inventories)

   

    # sales graph
    sales_graph_df = df.groupby(by="last_sales_date", as_index=False, sort=False)['sales'].sum()
    sales_graph = px.line(sales_graph_df, x=sales_graph_df.last_sales_date, y=sales_graph_df.sales, title="Sales Trend")
    sales_graph = json.dumps(sales_graph, cls=plotly.utils.PlotlyJSONEncoder)

    # best performing product
    df['quantity_sold'] = df['quantity_sold'].astype(int)
    best_performing_product_df = df.groupby(by="name").sum().sort_values(by="quantity_sold")
    colors = px.colors.qualitative.Set3[:len(best_performing_product_df)]
    best_performing_product = px.bar(best_performing_product_df,
                                     x=best_performing_product_df.index,
                                     y=best_performing_product_df.quantity_sold,
                                     color=best_performing_product_df.index,
                                     title="Best Performing Product")
    best_performing_product = json.dumps(best_performing_product, cls=plotly.utils.PlotlyJSONEncoder)

    # best performing product in sales
    sales_graph_df_per_product_df = df.groupby(by="name", as_index=False, sort=False)['sales'].sum()
    best_performing_product_per_product = px.pie(sales_graph_df_per_product_df,
                                                 names="name",
                                                 values="sales",
                                                 title="Product Performance By Sales",
                                                 color_discrete_sequence=px.colors.qualitative.Bold)
    best_performing_product_per_product = json.dumps(best_performing_product_per_product, cls=plotly.utils.PlotlyJSONEncoder)

    # Most Product In Stock
    most_product_in_stock_df = df.groupby(by="name").sum().sort_values(by="quantity_in_stock")
    most_product_in_stock = px.pie(most_product_in_stock_df,
                                   names=most_product_in_stock_df.index,
                                   values=most_product_in_stock_df.quantity_in_stock,
                                   title="Most Product In Stock")
    most_product_in_stock = json.dumps(most_product_in_stock, cls=plotly.utils.PlotlyJSONEncoder)

    context = {
        "sales_graph": sales_graph,
        "best_performing_product": best_performing_product,
        "most_product_in_stock": most_product_in_stock,
        "best_performing_product_per_product": best_performing_product_per_product
    }

    return render(request, "accounts/dashboard.html", context=context)



def marketing(request):
    context = {}
    return render(request, 'accounts/marketing.html', context)



def about(request):
    context = {}
    return render(request, 'accounts/about.html', context)

# Search for something

def search(request):
    if request.method == "POST":
        searched = request.POST['searched']
        inventories = get_inventory_by_name(searched) #Inventory.objects.filter(name__contains=searched)

        return render(request, 'accounts/search.html', {'searched': searched, 'inventories': inventories})
    else:
        return render(request, 'accounts/search.html', {})



def generate_sales_report(request):
    supplier = request.user
    user=request.session['user']
    # Get all inventory items
    inventories = get_inventory_by_supplier(user['user_id'])#Inventory.objects.filter(catalog__supplier=supplier)

    # Create a response object with CSV content
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write header row
    writer.writerow(['Product', 'Total Sales',
                    'Quantity Sold', 'Last Sale Date'])

    # Loop through each inventory item and write sales data
    for inventory in inventories:
        writer.writerow([inventory['name'], inventory['sales'],
                        inventory['quantity_sold'], inventory['last_sales_date']])

     # Update or create SalesData entries
        SalesData.objects.update_or_create(
            product=inventory,
            date=inventory['last_sales_date'],
            defaults={'quantity_sold': inventory['quantity_sold']}
        )

    return response


def analyze_sales_data(request):
    supplier = request.user
    user=request.session['user']
    # Get all inventory items
    inventories = get_inventory_by_supplierid(user['user_id']) #Inventory.objects.filter(catalog__supplier=supplier)

    # Check if the inventories are empty
    if not inventories:
        # Handle case where inventory is empty
        context = {
            "message": "No data available to forecast."
        }
        return render(request, "accounts/empty_forecast.html", context=context)

    sales_df = pd.DataFrame(
        list(inventories.values('last_sales_date', 'sales')))
    sales_df['last_sales_date'] = pd.to_datetime(sales_df['last_sales_date'])

    # Convert 'sales' column to numeric, handling errors by setting them to NaN
    sales_df['sales'] = pd.to_numeric(sales_df['sales'], errors='coerce')

    # Drop rows with NaN values in the 'sales' column
    sales_df = sales_df.dropna(subset=['sales'])

    # Continue with the time series analysis
    df = sales_df.set_index('last_sales_date')
    df_weekly = df.resample('W').sum()  # Resample weekly instead of monthly

    # Perform time series analysis
    model = ARIMA(df_weekly['sales'], order=(1, 1, 1))
    results = model.fit()

    # Generate future dates for forecasting
    future_dates = pd.date_range(
        start=df_weekly.index[-1], periods=7, freq='W-MON')[1:]  # Forecast for a week

    # Get forecasted values and their index
    forecast = results.get_forecast(steps=7)
    forecast_values = forecast.predicted_mean
    forecast_index = pd.date_range(
        start=df_weekly.index[-1], periods=8, freq='W-MON')[1:]

    # Create a DataFrame for the forecast data
    forecast_df = pd.DataFrame(
        {'Date': forecast_index, 'Forecast': forecast_values})

    # Create product_forecasts within the view function
    product_forecasts = []
    for inventory in inventories:  # Iterate through your inventory data
        product_forecasts.append({
            'name': inventory.name,
            'data': [
                {'Date': date, 'Forecast': value} for date, value in zip(forecast_df['Date'], forecast_df['Forecast'])
            ]
        })

    context = {'product_forecasts': product_forecasts}

    # Pass the forecast data to the template
    return render(request, 'accounts/analyze_sales_data.html', context)


def subscription(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                subscriber, created = Subscriber.objects.get_or_create(email=email)
                if created:
                    # Send confirmation email
                    send_subscription_confirmation_email(email)
                messages.success(request, "You have successfully subscribed!")
                return HttpResponseRedirect(reverse('subscription_confirmation'))
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
    else:
        form = SubscriptionForm()
    return render(request, 'accounts/subscription.html', {'form': form})


def send_subscription_confirmation_email(email):
    subject = 'Subscription Confirmation'
    message = 'Thank you for subscribing to FarmFresh! You will receive updates and promotions in your inbox.'
    sender_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, sender_email, recipient_list)



def send_bulk_emails(request):
    if request.method == 'POST':
        form = BulkEmailForm(request.POST, request.FILES)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            file = request.FILES.get('file')
            recipients = []

            # Filter subscribers based on recipient type
            if recipient_type == 'all':
                subscribers = Subscriber.objects.all()
            elif recipient_type == 'active':
                subscribers = Subscriber.objects.filter(is_active=True)
            elif recipient_type == 'inactive':
                subscribers = Subscriber.objects.filter(is_active=False)
            else:
                # Handle invalid recipient type
                return HttpResponseRedirect(reverse('send_bulk_emails'))

            # Get email addresses of selected recipients
            recipients = [subscriber.email for subscriber in subscribers]

            # Send bulk emails only if recipients exist
            if recipients:
                # Send emails
                for recipient in recipients:
                    email = EmailMultiAlternatives(subject, message, settings.EMAIL_HOST_USER, [recipient])
                    if file:
                        email.attach(file.name, file.read(), file.content_type)
                    email.send()

                return render(request, 'accounts/success.html')  # Render a success page or redirect as needed
    else:
        form = BulkEmailForm()

    # Retrieve the list of subscribers and pass it to the template
    subscribers = Subscriber.objects.all()
    context = {
        'form': form,
        'subscribers': subscribers,
    }

    return render(request, 'accounts/bulk_email.html', context)


def rate(request):
    catalogs = Catalog.objects.filter(is_deleted=False)  # Fetch all non-deleted catalogs
    context = {
        "title": "Products",
        "catalogs": catalogs
    }
    return render(request, 'accounts/rate.html', context)



def rate_inventory(request, inventory_id):
    if request.method == 'POST':
        inventory = Inventory.objects.get(id=inventory_id)
        user = request.user
        rating = request.POST.get('rating')
        Rating.objects.create(inventory=inventory, user=user, rating=rating)
        messages.success(request, 'Thank you for rating!')
    return redirect('rate')  # Redirect to the rate page


def distributor(request):
    if request.method == 'POST':
        form = DistributorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Distributor details saved successfully')
            return redirect('distributor')
    else:
        form = DistributorForm()
    return render(request, 'accounts/distributor.html', {'form': form})


def distributor_list(request):
    distributors = Distributor.objects.all()  # Retrieve all distributors from the database
    return render(request, 'accounts/distributor_list.html', {'distributors': distributors})


def extract_city_from_address(address):
    if address:
        parts = address.split(',')
        return parts[2].strip() if len(parts) > 2 else ''
    return ''


def nearby_suppliers(request):
    if 'q' in request.GET:
        query = request.GET.get('q')
        
        profiles = Profile.objects.filter(is_supplier=True)
        suggestions = []

        for profile in profiles:
            city = extract_city_from_address(profile.address)
            if query.lower() in city.lower():
                supplier_info = {'city': city, 'username': profile.user.username}
                # Check if the supplier has a catalog
                catalog = Catalog.objects.filter(supplier=profile.user).first()
                if catalog:
                    supplier_info['catalog_name'] = catalog.name
                    supplier_info['pk'] = catalog.pk
                suggestions.append(supplier_info)

        return JsonResponse(suggestions, safe=False)
    return render(request, 'users/nearby_suppliers.html')


def each_catalog(request, catalog_id):
    catalog = get_object_or_404(Catalog, pk=catalog_id)
    my_products = Catalog.objects.filter(is_deleted=False, supplier=request.user)
    
    context = {
        'title': 'Products',
        'catalog': catalog,
        'catalogs': my_products
    }
    
    return render(request, 'accounts/each_catalog.html', context)
    

def convert_file_to_base64(uploaded_file):
    """
    Convert the uploaded file (InMemoryUploadedFile) to a Base64 encoded string.
    """
    try:
        # Read the content of the uploaded file
        file_content = uploaded_file.read()

        # Encode the file content to Base64
        base64_string = base64.b64encode(file_content).decode('utf-8')

        return base64_string

    except Exception as e:
        print(f"Error converting file to Base64: {e}")
        return None


def decode_base64_to_image(base64_string):
    """
    Convert a Base64 string back to an image.
    """
    try:
        # Decode the Base64 string
        imgdata = base64.b64decode(base64_string)

        # Create an in-memory file from the decoded data
        image_file = ContentFile(imgdata)

        # Verify image validity (optional)
        try:
            Image.open(image_file)  # This will attempt to open the image
        except IOError:
            raise ValueError("Invalid image data.")

        return image_file

    except Exception as e:
        raise ValueError(f"Error decoding Base64 image: {e}")

def handle_uploaded_file(uploaded_file):
    # Step 1: Convert the uploaded file to Base64 string
    base64_string = convert_file_to_base64(uploaded_file)
    
    if base64_string:
        # Step 2: Decode the Base64 string to an image
        image_file = decode_base64_to_image(base64_string)
        print("Image successfully decoded.")
        return image_file
    else:
        print("Error in file conversion.")
        return None







def analytics_tracker(request):
    """
    Render the Analytics Tracker dashboard. This page currently uses placeholder
    data rendered by Chart.js and Leaflet. Hook real data sources later.
    """
    return render(request, 'accounts/analytics_tracker.html')

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    request.session.flush()  # Clear session data
    messages.success(request, "You have been logged out.")
    from django.http import HttpResponseRedirect
    return HttpResponseRedirect('https://society-ed02.onrender.com')







