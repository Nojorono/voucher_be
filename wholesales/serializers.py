from rest_framework import serializers
from .models import Wholesale, VoucherRedeem

class WholesaleSerializer(serializers.ModelSerializer):
    """Basic wholesale serializer"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    is_root = serializers.SerializerMethodField()
    is_leaf = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'pic', 'city',
            'is_active', 'created_at', 'updated_at', 'parent', 'parent_name', 'project', 'project_name',
            'children_count', 'level', 'is_root', 'is_leaf'
        ]
        ref_name = 'WholesaleHierarchy'
        
    def get_children_count(self, obj):
        """Get count of direct children that are active"""
        return obj.get_children(active_only=True).count()
        
    def get_level(self, obj):
        """Get hierarchy level"""
        return obj.get_level()
        
    def get_is_root(self, obj):
        """Check if is root"""
        return obj.is_root()
        
    def get_is_leaf(self, obj):
        """Check if is leaf (has no active children)"""
        return obj.is_leaf(active_only=True)

class WholesaleTreeSerializer(serializers.ModelSerializer):
    """Serializer for wholesale with full hierarchy tree"""
    children = serializers.SerializerMethodField()
    ancestors = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    
    class Meta:
        model = Wholesale
        fields = [
            'id', 'name', 'phone_number', 'address', 'pic', 'city',
            'is_active', 'created_at', 'updated_at', 'parent', 'project',
            'children', 'ancestors', 'level'
        ]
        ref_name = 'WholesaleTree'
        
    def get_children(self, obj):
        """Get all direct active children"""
        children = obj.get_children(active_only=True)
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
            'is_active', 'created_at', 'updated_at', 'parent', 'project',
            'children', 'all_descendants', 'ancestors', 'level',
            'is_root', 'is_leaf'
        ]
        ref_name = 'WholesaleHierarchyDetail'
        
    def get_children(self, obj):
        """Get direct children"""
        return WholesaleSerializer(obj.get_children(active_only=True), many=True, context=self.context).data
        
    def get_all_descendants(self, obj):
        """Get all descendants"""
        return WholesaleSerializer(obj.get_all_descendants(active_only=True), many=True, context=self.context).data
        
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
        """Check if is leaf (has no active children)"""
        return obj.is_leaf(active_only=True)

class VoucherRedeemSerializer(serializers.ModelSerializer):
    """Voucher redeem serializer with wholesale hierarchy info"""
    wholesale_name = serializers.CharField(source='wholesale.name', read_only=True)
    wholesale_level = serializers.SerializerMethodField()
    wholesale_parent = serializers.CharField(source='wholesale.parent.name', read_only=True)
    
    class Meta:
        model = VoucherRedeem
        fields = '__all__'
        ref_name = 'WholesaleVoucherRedeem'
        
    def get_wholesale_level(self, obj):
        """Get wholesale hierarchy level"""
        if obj.wholesale:
            return obj.wholesale.get_level()
        return 0
