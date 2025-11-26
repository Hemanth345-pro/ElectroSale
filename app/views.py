from django.shortcuts import render,get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from app.forms import UserRegistrationForm
from .models import Product, Sale, Size, ProductInventory
from django.http import JsonResponse
from django.utils.dateparse import parse_date
import plotly.express as px
import pandas as pd
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import json
from django.http import JsonResponse
from django.conf import settings
import requests


def send_sns_email(subject, message,name, product, email, phone):
    SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:292424520944:sns-x22183744"
    
    full_message = f"""Enquiry details:\n
        Customer Name: {name}\n
        Product: {product}\n
        Email: {email}\n
        Phone: {phone}\n
        Message: {message}\n
    """

    try:
        # Use the correct region (eu-west-2)
        sns_client = boto3.client("sns", region_name="us-east-1",)  
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=full_message,
            Subject=subject
        )
        
        print(f"Email sent successfully! Message ID: {response['MessageId']}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def s3_upload(file, object_name=None):
    bucket_name = "x22183744-cpp-bucket"
    if object_name is None:
        object_name = file.name

    s3_client = boto3.client('s3', region_name="us-east-1")
    
    try:
        s3_client.upload_fileobj(file, bucket_name, object_name)
        return True
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


#---------------------------------------------------------------------------------

class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        return redirect("login_page")

class LoginView(View):
    def get(self, request, *args, **kwargs):
        return render(request, template_name="login.html")

    def post(self, request, *args, **kwargs):
        user_obj = authenticate(
            request,
            username=request.POST.get("email-username"),
            password=request.POST.get("password"),
        )

        if not user_obj:
            return render(
                request,
                template_name="login.html",
                context={"error": "Invalid Credentials"},
            )

        if user_obj and user_obj.is_staff and user_obj.is_active:
            login(request, user_obj)
            return redirect("admin_home")
        elif user_obj and user_obj.is_active:
            login(request, user_obj)
            return redirect("admin_home")
        return redirect("login_page")


class SignupView(View):
    def get(self, request, *args, **kwargs):
        form = UserRegistrationForm()
        return render(request, "signup.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect("login_page")
        return render(request, "signup.html", {"form": form})


class AdminHome(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        sales = Sale.objects.all()
        inventory = ProductInventory.objects.all()

        total_sales = sum(sale.total_price for sale in sales)
        total_inventory = sum(item.stock for item in inventory)
        total_products = products.count()

        print("DEBUG:", total_products, total_sales, total_inventory)

        return render(request, template_name="admin_home.html", context={"total_products": total_products, "total_sales": total_sales, "total_inventory": total_inventory,})

    def post(self, request, *args, **kwargs):
        return render(request,template_name="admin_home.html")


class AdminProducts(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        return render(request, template_name="admin_products.html", context={"products": products})

    def post(self, request, *args, **kwargs):
        edit = request.POST.get("edit")
        delete = request.POST.get("delete")
        view = request.POST.get("view")

        if delete:
            if delete:
                try:
                    product = Product.objects.get(id=delete)
                    product.delete()
                    return redirect("admin_products")
                except Product.DoesNotExist:
                    return render(request, template_name="admin_products.html", context={"error": "Product not found"})
                
        if edit:
            try:
                product = Product.objects.get(id=edit)
                return render(request, template_name="admin_add_product.html", context={"product": product})
            except Product.DoesNotExist:
                return render(request, template_name="admin_products.html", context={"error": "Product not found"})
            
        if view:
            try:
                product = Product.objects.get(id=view)
                return render(request, "admin_view_product.html", context={"product":product})
            except Product.DoesNotExist:
                return render(request, template_name="admin_products.html")

        return render(request,template_name="admin_products.html")
    

class AdminAddProduct(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        sizes = Size.objects.all()
        return render(request, template_name="admin_add_product.html", context={"sizes": sizes})

    def post(self, request, *args, **kwargs):
        product_name = request.POST.get("product_name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        image = request.FILES.get("image")
        product_id = request.POST.get("product_id")

        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                product.name = product_name
                product.description = description
                product.price = price
                if image:
                    product.image = image
                product.save()
                s3_upload(image, object_name=f"products/{product.image}")
                return redirect("admin_products")
            except Product.DoesNotExist:
                return render(request, template_name="admin_add_product.html", context={"error": "Product not found"})

        if product_name and description and price and image:
            product = Product(
                name=product_name,
                description=description,
                price=price,
                image=image,
            )
            product.save()
            s3_upload(image, object_name=f"products/{product.image}")  
            return redirect("admin_products")

        sizes = Size.objects.all()
        return render(request, template_name="admin_add_product.html", context={"sizes": sizes})



class AdminEditProducts(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        return render(request, template_name="admin_products.html", context={"products": products})

    def post(self, request, *args, **kwargs):
        return render(request,template_name="admin_products.html")

    
class AdminInventory(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        inventory = ProductInventory.objects.all()
        return render(request, template_name="admin_inventory.html", context={"products": products,"inventory": inventory})

    def post(self, request, *args, **kwargs):
        return render(request,template_name="admin_inventory.html")


class AdminAddInventory(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, product_id, *args, **kwargs):
            product = get_object_or_404(Product, id=product_id)
            sizes = Size.objects.all()
            return render(request, "admin_add_inventory.html", {"product": product, "sizes": sizes})

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get("product_id")
        size_value = request.POST.get("size")
        stock = request.POST.get("quantity")

        if product_id and size_value and stock:
            try:
                product = Product.objects.get(pk=product_id)
                size_obj = Size.objects.get(size=size_value)
            except (Product.DoesNotExist, Size.DoesNotExist):
                return render(request, template_name="admin_add_inventory.html", context={"error": "Invalid product or size"})

            inventory_item, created = ProductInventory.objects.get_or_create(
                product=product,
                size=size_obj,
                defaults={'stock': stock}
            )
            if not created:
                inventory_item.stock += int(stock)
                inventory_item.save()

            return redirect("admin_inventory")

        return render(request,template_name="admin_add_inventory.html")


def get_stock(request, product_id, size):
    try:
        product = Product.objects.get(id=product_id)
        size_obj = Size.objects.get(size=size)
        inventory = ProductInventory.objects.get(product=product, size=size_obj)
        return JsonResponse({"stock": inventory.stock})
    except (Product.DoesNotExist, Size.DoesNotExist, ProductInventory.DoesNotExist):
        return JsonResponse({"stock": 0})


class AdminViewInventory(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, product_id, *args, **kwargs):
        product = get_object_or_404(Product, id=product_id)
        sizes = Size.objects.all()
        inventory_items = ProductInventory.objects.filter(product=product)
        return render(request, "admin_view_product_inventory.html",context={"inventory_items": inventory_items})

    def post(self, request, *args, **kwargs):
        return render(request,template_name="admin_view_product_inventory.html")


def get_available_sizes(request, product_id):
    inventory_qs = (
        ProductInventory.objects
        .filter(product_id=product_id, stock__gt=0)
        .select_related("size")
    )
    size_codes = sorted({inv.size.size for inv in inventory_qs})
    return JsonResponse(size_codes, safe=False)


class AdminSales(LoginRequiredMixin, View):
    login_url = '/'
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        return render(request, "admin_sales.html", {"products": products})

    def post(self, request, *args, **kwargs):
        customer_name = request.POST.get("customer_name")
        customer_phone = request.POST.get("customer_phone")
        product_id = request.POST.get("product")
        size_value = request.POST.get("size")
        quantity = request.POST.get("quantity")

        total_price = 0.00
        products = Product.objects.all()  

        if customer_name and customer_phone and product_id and size_value and quantity:
            try:
                quantity = int(quantity)
                product = Product.objects.get(pk=product_id)
                size_obj = Size.objects.get(size=size_value)

                inventory = ProductInventory.objects.get(product=product, size=size_obj)

                if inventory.stock < quantity:
                    return render(request, "admin_sales.html", {
                        "products": products,
                        "error": f"Only {inventory.stock} items left in stock for size {size_obj}."
                    })

                total_price = product.price * quantity

                sale = Sale(
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    product=product,
                    size=size_obj,
                    quantity=quantity,
                    total_price=total_price,
                )
                sale.save()
                inventory.stock -= quantity
                inventory.save()

                send_sns_email(
                    subject="New Sale Notification",
                    message=f"Sale of {quantity} {product.name} in size {size_value} for {total_price} by {customer_name}.",
                    name=customer_name,
                    product=product.name,
                    email=customer_name,
                    phone=customer_phone
                )

                return redirect("admin_sales")

            except ProductInventory.DoesNotExist:
                return render(request, "admin_sales.html", {
                    "products": products,
                    "error": "Inventory record not found for selected product and size."
                })
            except (Product.DoesNotExist, Size.DoesNotExist):
                return render(request, "admin_sales.html", {
                    "products": products,
                    "error": "Invalid product or size selected."
                })
            except ValueError:
                return render(request, "admin_sales.html", {
                    "products": products,
                    "error": "Invalid quantity."
                })
        else:
            return render(request, "admin_sales.html", {
                "products": products,
                "error": "Please fill in all fields."
            })


class AdminSalesHistory(LoginRequiredMixin, View):
    login_url = '/'
    def post(self, request, *args, **kwargs):
        return render(request,template_name="admin_sales_history.html")

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        sales = Sale.objects.all()
        if start_date:
            sales = sales.filter(sale_date__date__gte=parse_date(start_date))
        if end_date:
            sales = sales.filter(sale_date__date__lte=parse_date(end_date))
        return render(request, "admin_sales_history.html", {"sales": sales})

from django.contrib import messages


# class ExportToCSV(LoginRequiredMixin, View):
#     login_url = '/'

#     def get(self, request, *args, **kwargs):
#         sales = Sale.objects.all()
#         sales_data = list(sales.values('id', 'product__name', 'quantity', 'total_price', 'sale_date'))

#         payload = {
#             'sales': [
#                 {
#                     'id': s['id'],
#                     'product': s['product__name'],
#                     'quantity': s['quantity'],
#                     'total_price': float(s['total_price']),
#                     'sale_date': s['sale_date'].strftime('%Y-%m-%d')
#                 } for s in sales_data
#             ]
#         }

#         api_gateway_url = "https://ij536t0z4k.execute-api.us-east-1.amazonaws.com/stage1/x22183744-lambda"
#         response = requests.post(api_gateway_url, json=payload)
#         print("api gateway hit")

#         if response.status_code == 200:
#             result = response.json()
#             body_data = json.loads(result['body'])
#             file_url = body_data.get('file_url')
#             print(f"---------> File URL: {file_url}")
#             messages.success(request, ' Sales export completed successfully. Download link sent via email.')
#         else:
#             messages.error(request, ' Failed to export sales CSV.')

#         #  Redirect back to sales history regardless of success
#         return redirect('admin_sales_history')




import json
import requests
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from app.models import Sale


class ExportToCSV(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, *args, **kwargs):

        # Get all sales
        sales = Sale.objects.all()
        sales_data = list(sales.values(
            'id', 
            'product__name', 
            'quantity', 
            'total_price', 
            'sale_date'
        ))

        # Build payload for Lambda
        payload = {
            'sales': [
                {
                    'id': s['id'],
                    'product': s['product__name'],
                    'quantity': s['quantity'],
                    'total_price': float(s['total_price']),
                    'sale_date': s['sale_date'].strftime('%Y-%m-%d')
                }
                for s in sales_data
            ]
        }

        api_gateway_url = (
            "https://ij536t0z4k.execute-api.us-east-1.amazonaws.com/"
            "stage1/x22183744-lambda"
        )

        # IMPORTANT: Add content-type header
        headers = {"Content-Type": "application/json"}

        # Call API Gateway → Lambda
        response = requests.post(api_gateway_url, json=payload, headers=headers)

        print("API Gateway hit → Status:", response.status_code)

        if response.status_code == 200:
            try:
                # DIRECT JSON from Lambda (NO need result["body"])
                response_json = response.json()
                print("Lambda Response:", response_json)

                download_url = response_json.get("download_url")

                if download_url:
                    print("Download URL:", download_url)
                    messages.success(
                        request,
                        "Sales export completed successfully. "
                        "Check your email for download link."
                    )
                else:
                    messages.error(request, "Export completed but no URL returned.")

            except Exception as e:
                print("JSON parsing error →", e)
                messages.error(request, "Error reading Lambda response.")

        else:
            print("API Error →", response.text)
            messages.error(request, "Failed to export sales CSV.")

        return redirect('admin_sales_history')



from bar_graph_lib.bar_plot import generate_bar_graph
import pandas as pd
import plotly.express as px

class AdminAnalysis(LoginRequiredMixin, View):
    login_url = '/'

    # ---------- GET METHOD ----------
    def get(self, request, *args, **kwargs):

        # Sales Data
        sales_by_product = (
            Sale.objects.values('product__name')
            .annotate(total_sales=Sum('total_price'))
            .order_by('-total_sales')
        )

        sales_bar = generate_bar_graph(
            sales_by_product,
            'product__name',
            'total_sales',
            'Sales by Product'
        )

        # Inventory Data
        inventory_by_product = (
            ProductInventory.objects.values('product__name')
            .annotate(total_stock=Sum('stock'))
            .order_by('-total_stock')
        )

        inventory_bar = generate_bar_graph(
            inventory_by_product,
            'product__name',
            'total_stock',
            'Inventory by Product'
        )

        return render(request, "admin_analysis.html", {
            "sales_bar": sales_bar,
            "inventory_bar": inventory_bar
        })

    # ---------- POST METHOD ----------
    def post(self, request, *args, **kwargs):
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        start = parse_date(start_date)
        end = parse_date(end_date)

        if start and end:
            sales_query = Sale.objects.filter(sale_date__range=[start, end])
        else:
            sales_query = Sale.objects.all()

        return self.render_analysis(request, sales_query)

    # ---------- REUSABLE METHOD ----------
    def render_analysis(self, request, sales_query):

        # Sales Bar Chart
        sales_by_product = (
            sales_query.values('product__name')
            .annotate(total_sales=Sum('total_price'))
            .order_by('-total_sales')
        )

        sales_bar = generate_bar_graph(
            sales_by_product,
            'product__name',
            'total_sales',
            'Sales by Product'
        )

        # Inventory Bar Chart
        inventory_by_product = (
            ProductInventory.objects.values('product__name')
            .annotate(total_stock=Sum('stock'))
            .order_by('-total_stock')
        )

        inventory_bar = generate_bar_graph(
            inventory_by_product,
            'product__name',
            'total_stock',
            'Inventory by Product'
        )

        return render(request, "admin_analysis.html", {
            "sales_bar": sales_bar,
            "inventory_bar": inventory_bar
        })
