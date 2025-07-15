#!/usr/bin/env python
"""
Test script to verify wholesale parent-child functionality
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from wholesales.models import Wholesale

def test_parent_child_functionality():
    print("🧪 Testing Wholesale Parent-Child Functionality")
    print("=" * 60)
    
    # Create test data
    print("1. Creating test wholesales...")
    
    # Create parent
    parent = Wholesale.objects.create(
        name="Test Parent Wholesale",
        phone_number="081234567890",
        address="Jakarta",
        city="Jakarta",
        pic="Parent Manager"
    )
    print(f"   Created parent: {parent.name} (ID: {parent.id})")
    
    # Create child
    child = Wholesale.objects.create(
        name="Test Child Wholesale",
        phone_number="081234567891",
        address="Bandung",
        city="Bandung",
        pic="Child Manager"
    )
    print(f"   Created child: {child.name} (ID: {child.id})")
    
    # Test setting parent
    print("\n2. Setting parent relationship...")
    child.parent = parent
    child.save()
    
    # Refresh from database
    child.refresh_from_db()
    parent.refresh_from_db()
    
    print(f"   Child parent: {child.parent}")
    print(f"   Child level: {child.get_level()}")
    print(f"   Parent children count: {parent.get_children().count()}")
    print(f"   Parent is_root: {parent.is_root()}")
    print(f"   Child is_leaf: {child.is_leaf()}")
    
    # Test API serializer
    print("\n3. Testing API serializer...")
    from api.serializers import WholesaleSerializer
    
    serializer = WholesaleSerializer(child)
    data = serializer.data
    print(f"   Serialized data: {data}")
    
    # Test updating parent via serializer
    print("\n4. Testing parent update via serializer...")
    update_data = {'parent': None}  # Set to root
    serializer = WholesaleSerializer(child, data=update_data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print("   ✅ Parent updated successfully")
        
        # Verify update
        child.refresh_from_db()
        print(f"   Child parent after update: {child.parent}")
        print(f"   Child level after update: {child.get_level()}")
    else:
        print(f"   ❌ Serializer errors: {serializer.errors}")
    
    # Test setting parent back
    print("\n5. Setting parent back...")
    update_data = {'parent': parent.id}
    serializer = WholesaleSerializer(child, data=update_data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print("   ✅ Parent set back successfully")
        
        # Verify update
        child.refresh_from_db()
        print(f"   Child parent after restore: {child.parent}")
        print(f"   Child level after restore: {child.get_level()}")
    else:
        print(f"   ❌ Serializer errors: {serializer.errors}")
    
    # Cleanup
    print("\n6. Cleaning up...")
    child.delete()
    parent.delete()
    print("   ✅ Test data cleaned up")
    
    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    test_parent_child_functionality()
