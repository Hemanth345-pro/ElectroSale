from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path("", views.LoginView.as_view(), name="login_page"),
    path("/signup", views.SignupView.as_view(), name="signup_page"),
    path("/admin_home", views.AdminHome.as_view(), name="admin_home"),
    path("/admin_products", views.AdminProducts.as_view(), name="admin_products"),
    path("/admin_add_product", views.AdminAddProduct.as_view(), name="admin_add_product"),
    path("/admin_inventory", views.AdminInventory.as_view(), name="admin_inventory"),
    path("/admin_add_inventory", views.AdminAddInventory.as_view(), name="admin_add_inventory"),
    path('/<int:product_id>/inventory/add/', views.AdminAddInventory.as_view(), name='admin_add_inventory'),
    path("get-stock/<int:product_id>/<str:size>/", views.get_stock, name="get_stock"),

    path('get-sizes/<int:product_id>/', views.get_available_sizes, name='get_available_sizes'),
    path('get-stock/<int:product_id>/<str:size>/', views.get_stock, name='get_stock'),


    path("/admin_view_inventory/<int:product_id>/", views.AdminViewInventory.as_view(), name="admin_view_inventory"),
    path("/admin_sales", views.AdminSales.as_view(), name="admin_sales"),
    path('get-sizes/<int:product_id>/', views.get_available_sizes, name='get_sizes'),
    path('get-sizes/<int:product_id>/', views.get_available_sizes, name='get_available_sizes'),


    path("/admin_sales_history", views.AdminSalesHistory.as_view(), name="admin_sales_history"),
    path("/admin_analysis", views.AdminAnalysis.as_view(), name="admin_analysis"),

    path("/logout", views.LogoutView.as_view(), name="logout"),

    path('/export_sales_csv', views.ExportToCSV.as_view(), name='export_sales_csv'),


]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)