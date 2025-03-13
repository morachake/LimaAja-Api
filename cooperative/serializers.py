from rest_framework import serializers
from .models import Farmer, Product

class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ['id', 'name', 'phone_number', 'address', 'joining_date', 'is_active']

class ProductSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'farmer', 'farmer_name', 'created_at', 'updated_at']

class FarmerDetailSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Farmer
        fields = ['id', 'name', 'phone_number', 'address', 'joining_date', 'is_active', 'products']

