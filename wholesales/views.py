from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from retailer.models import Voucher
from .models import VoucherRedeem, Wholesale
from .serializers import (
    WholesaleSerializer, 
    WholesaleTreeSerializer, 
    WholesaleHierarchySerializer, 
    VoucherRedeemSerializer
)

class WholesaleViewSet(viewsets.ModelViewSet):
    """ViewSet for Wholesale with hierarchy support"""
    queryset = Wholesale.objects.all()
    serializer_class = WholesaleSerializer
    
    def get_queryset(self):
        """Optimize queryset with select_related for parent"""
        return Wholesale.objects.select_related('parent').prefetch_related('children')
    
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get all root wholesales (no parent)"""
        roots = self.get_queryset().filter(parent__isnull=True)
        serializer = WholesaleTreeSerializer(roots, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def leaves(self, request):
        """Get all leaf wholesales (no children)"""
        leaves = self.get_queryset().annotate(
            children_count=Count('children')
        ).filter(children_count=0)
        serializer = self.get_serializer(leaves, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get direct children of a wholesale"""
        wholesale = self.get_object()
        children = wholesale.get_children()
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get all descendants of a wholesale"""
        wholesale = self.get_object()
        descendants = wholesale.get_all_descendants()
        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get all ancestors of a wholesale"""
        wholesale = self.get_object()
        ancestors = wholesale.get_ancestors()
        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """Get full hierarchy info for a wholesale"""
        wholesale = self.get_object()
        serializer = WholesaleHierarchySerializer(wholesale)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get wholesale with full tree structure"""
        wholesale = self.get_object()
        serializer = WholesaleTreeSerializer(wholesale)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get wholesales grouped by hierarchy level"""
        level = request.query_params.get('level')
        if level is not None:
            try:
                level = int(level)
                wholesales = []
                for wholesale in self.get_queryset():
                    if wholesale.get_level() == level:
                        wholesales.append(wholesale)
                serializer = self.get_serializer(wholesales, many=True)
                return Response(serializer.data)
            except ValueError:
                return Response(
                    {'error': 'Level must be an integer'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Return all levels if no specific level requested
        levels = {}
        for wholesale in self.get_queryset():
            level = wholesale.get_level()
            if level not in levels:
                levels[level] = []
            levels[level].append(wholesale)
        
        result = {}
        for level, wholesales in levels.items():
            serializer = self.get_serializer(wholesales, many=True)
            result[f'level_{level}'] = serializer.data
        
        return Response(result)

# Halaman redeem voucher oleh wholesales
def redeem_voucher(request):
    if request.method == 'POST':
        voucher_code = request.POST.get('voucher_code')
        ws_name = request.POST.get('ws_name')
        try:
            voucher = Voucher.objects.get(code=voucher_code, redeemed=False)
            wholesaler = Wholesale.objects.get(name=ws_name)  # Asumsi user sudah login sebagai wholesaler
            voucher.redeemed = True
            voucher.save()

            # Simpan redeem data
            redeem = VoucherRedeem(voucher=voucher, wholesaler=wholesaler)
            redeem.save()
            return render(request, 'wholesales/redeem_success.html')

        except Voucher.DoesNotExist:
            return render(request, 'wholesales/redeem_failed.html')

    return render(request, 'wholesales/redeem_voucher.html')

# Laporan redeem voucher oleh wholesales
def redeem_report(request,name):
    wholesaler = Wholesale.objects.get(name=name)
    redeemed_vouchers = VoucherRedeem.objects.filter(wholesaler=wholesaler)
    return render(request, 'wholesales/redeem_report.html', {'redeemed_vouchers': redeemed_vouchers})
