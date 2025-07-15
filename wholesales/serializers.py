from rest_framework import serializers
from .models import Wholesale, VoucherRedeem

class WholesaleSerializer(serializers.ModelSerializer):
    """Basic wholesale serializer"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    is_root = serializers.SerializerMethodField()
    is_leaf = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'pic', 'city',
            'is_active', 'created_at', 'updated_at', 'parent', 'parent_name',
            'children_count', 'level', 'is_root', 'is_leaf'
        ]
        
    def get_children_count(self, obj):
        """Get count of direct children"""
        return obj.get_children().count()
        
    def get_level(self, obj):
        """Get hierarchy level"""
        return obj.get_level()
        
    def get_is_root(self, obj):
        """Check if is root"""
        return obj.is_root()
        
    def get_is_leaf(self, obj):
        """Check if is leaf"""
        return obj.is_leaf()

class WholesaleTreeSerializer(serializers.ModelSerializer):
    """Serializer for wholesale with full hierarchy tree"""
    children = serializers.SerializerMethodField()
    ancestors = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'pic', 'city',
            'is_active', 'created_at', 'updated_at', 'parent',
            'children', 'ancestors', 'level'
        ]
        
    def get_children(self, obj):
        """Get all direct children"""
        children = obj.get_children()
        return WholesaleTreeSerializer(children, many=True, context=self.context).data
        
    def get_ancestors(self, obj):
        """Get all ancestors"""
        ancestors = obj.get_ancestors()
        return WholesaleSerializer(ancestors, many=True, context=self.context).data
        
    def get_level(self, obj):
        """Get hierarchy level"""
        return obj.get_level()

class WholesaleHierarchySerializer(serializers.ModelSerializer):
    """Serializer for wholesale hierarchy operations"""
    children = serializers.SerializerMethodField()
    all_descendants = serializers.SerializerMethodField()
    ancestors = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    is_root = serializers.SerializerMethodField()
    is_leaf = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'pic', 'city',
            'is_active', 'created_at', 'updated_at', 'parent',
            'children', 'all_descendants', 'ancestors', 'level',
            'is_root', 'is_leaf'
        ]
        
    def get_children(self, obj):
        """Get direct children"""
        return WholesaleSerializer(obj.get_children(), many=True, context=self.context).data
        
    def get_all_descendants(self, obj):
        """Get all descendants"""
        return WholesaleSerializer(obj.get_all_descendants(), many=True, context=self.context).data
        
    def get_ancestors(self, obj):
        """Get all ancestors"""
        return WholesaleSerializer(obj.get_ancestors(), many=True, context=self.context).data
        
    def get_level(self, obj):
        """Get hierarchy level"""
        return obj.get_level()
        
    def get_is_root(self, obj):
        """Check if is root"""
        return obj.is_root()
        
    def get_is_leaf(self, obj):
        """Check if is leaf"""
        return obj.is_leaf()

class VoucherRedeemSerializer(serializers.ModelSerializer):
    """Voucher redeem serializer with wholesale hierarchy info"""
    wholesale_name = serializers.CharField(source='wholesale.name', read_only=True)
    wholesale_level = serializers.SerializerMethodField()
    wholesale_parent = serializers.CharField(source='wholesale.parent.name', read_only=True)
    
    class Meta:
        model = VoucherRedeem
        fields = '__all__'
        
    def get_wholesale_level(self, obj):
        """Get wholesale hierarchy level"""
        if obj.wholesale:
            return obj.wholesale.get_level()
        return 0
