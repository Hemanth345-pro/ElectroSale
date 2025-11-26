from django.db import models
from django.utils import timezone



class Size(models.Model):
    SIZE_CHOICES = [
        ('Apple', 'Apple'),
        ('LG', 'LG'),
        ('Samsong', 'Samsong'),
        ('Vivo', 'Vivo'),
        ('Oppo', 'Oppo'),
    ]
    size = models.CharField(max_length=15, choices=SIZE_CHOICES, unique=True)

    def __str__(self):
        return dict(self.SIZE_CHOICES).get(self.size, self.size)



class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    

class Sale(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    sale_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.customer_name} - {self.product.name} ({self.size})"


class ProductInventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size} : {self.stock}"


