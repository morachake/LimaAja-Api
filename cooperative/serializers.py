from rest_framework import serializers
from .models import Farmer, Product, ProduceType, ProduceVariant, CooperativeProduce

class FarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ['id', 'name', 'phone_number', 'location', 'created_at']
        read_only_fields = ['id', 'created_at']

class FarmerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ['id', 'name', 'phone_number', 'location', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'category', 'image']
        read_only_fields = ['id']

# New serializers for produce management
class ProduceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduceType
        fields = ['id', 'name', 'description', 'category', 'base_price', 'image']

class ProduceVariantSerializer(serializers.ModelSerializer):
    produce_type_name = serializers.CharField(source='produce_type.name', read_only=True)
    
    class Meta:
        model = ProduceVariant
        fields = ['id', 'produce_type', 'produce_type_name', 'grade', 'price_multiplier']

class CooperativeProduceSerializer(serializers.ModelSerializer):
    produce_type_name = serializers.CharField(source='produce_type.name', read_only=True)
    variant_grade = serializers.CharField(source='variant.grade', read_only=True)
    category = serializers.CharField(source='produce_type.category', read_only=True)
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = CooperativeProduce
        fields = ['id', 'cooperative', 'produce_type', 'produce_type_name', 
                  'variant', 'variant_grade', 'quantity', 'province', 
                  'created_at', 'updated_at', 'category', 'price']
        read_only_fields = ['cooperative']
    
    def get_price(self, obj):
        # Calculate the price based on base price and variant multiplier
        return obj.produce_type.base_price * obj.variant.price_multiplier

