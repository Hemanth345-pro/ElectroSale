from django.contrib import admin
from app import models

admin.site.register(models.Product)
# admin.site.register(models.Size)
admin.site.register(models.Size)
admin.site.register(models.Sale)
admin.site.register(models.ProductInventory)

# Register your models here.
