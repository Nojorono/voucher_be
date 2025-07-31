

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from retailer.models import RetailerPhoto, Retailer, Voucher
from .models import VoucherLimit, VoucherProject, VoucherRetailerDiscount
from .twilio import send_whatsapp_voucher  # Impor fungsi kirim WhatsApp

# Fungsi untuk verifikasi foto oleh kantor dan mengirimkan voucher
def verify_photo(request, retailer_id):
    # Get the retailer details
    retailer = get_object_or_404(Retailer, id=retailer_id)

    # Ambil semua foto untuk retailer berdasarkan retailer_id
    photos = RetailerPhoto.objects.all().filter(retailer_id=retailer_id)
    
    # Jika ada foto yang tidak ditemukan
    if not photos.exists():
        return redirect('office:office_verification_report')  # Jika tidak ada foto, redirect ke laporan

    if request.method == 'POST':
        # Tentukan status verifikasi berdasarkan pilihan
        is_verified = request.POST.get('is_verified') == 'True'
        
        # Update status verifikasi untuk setiap foto
        for photo in photos:
            photo.is_verified = is_verified
            photo.save()

        # Setelah verifikasi, redirect ke laporan verifikasi
        if is_verified:
            # Kirim voucher melalui WhatsApp jika disetujui
            # send_whatsapp_voucher(photos[0].retailer.id)  # Kirim voucher untuk retailer pertama
            return redirect('office:office_verification_report')

    context = {
        'retailer': retailer,
        'photos': photos,
    }

    return render(request, 'office/verify_photo.html', context)

# Fungsi untuk menampilkan laporan foto yang belum diverifikasi oleh Office
def office_verification_report(request):
    # Get all retailers
    retailers = Retailer.objects.all()
    
    # Get photos that are not verified and group them by retailer
    photos_to_verify = RetailerPhoto.objects.filter(is_verified=False).values('retailer').annotate(total=Count('id'))
    
    # Create a dictionary to hold the retailer and their unverified photos
    retailer_photos = {}
    for retailer in retailers:
        retailer_photos[retailer] = RetailerPhoto.objects.filter(retailer=retailer, is_verified=False)
    
    context = {
        'retailer_photos': retailer_photos,
        'photos_to_verify': photos_to_verify,
    }
    return render(request, 'office/verification_report.html', context)


# ================================
# VOUCHER PROJECT VIEWS
# ================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def voucher_project_list(request):
    """List all voucher projects or create new one"""
    if request.method == 'GET':
        projects = VoucherProject.objects.all().order_by('-created_at')
        project_list = []
        
        for project in projects:
            project_data = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'periode_start': project.periode_start.isoformat() if project.periode_start else None,
                'periode_end': project.periode_end.isoformat() if project.periode_end else None,
                'is_active': project.is_active,
                'created_at': project.created_at.isoformat(),
                'created_by': project.created_by,
                'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                'updated_by': project.updated_by,
            }
            project_list.append(project_data)
        
        return JsonResponse({
            'success': True,
            'data': project_list,
            'total': len(project_list)
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create new voucher project
            project = VoucherProject.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                periode_start=data.get('periode_start'),
                periode_end=data.get('periode_end'),
                is_active=data.get('is_active', True),
                created_by=data.get('created_by'),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher project created successfully',
                'data': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'is_active': project.is_active,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating voucher project: {str(e)}'
            }, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def voucher_project_detail(request, project_id):
    """Get, update, or delete specific voucher project"""
    try:
        project = get_object_or_404(VoucherProject, id=project_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'periode_start': project.periode_start.isoformat() if project.periode_start else None,
                    'periode_end': project.periode_end.isoformat() if project.periode_end else None,
                    'is_active': project.is_active,
                    'created_at': project.created_at.isoformat(),
                    'created_by': project.created_by,
                    'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                    'updated_by': project.updated_by,
                }
            })
        
        elif request.method == 'PUT':
            data = json.loads(request.body)
            
            # Update project fields
            project.name = data.get('name', project.name)
            project.description = data.get('description', project.description)
            project.periode_start = data.get('periode_start', project.periode_start)
            project.periode_end = data.get('periode_end', project.periode_end)

            # Update expired_at pada semua Voucher yang terkait dengan project ini
            Voucher.objects.filter(project=project).update(expired_at=project.periode_end)
            project.is_active = data.get('is_active', project.is_active)
            project.updated_by = data.get('updated_by')
            project.updated_at = timezone.now()
            project.save()
            
            return JsonResponse({
                            'success': True,
                            'message': 'Voucher project updated successfully',
                            'data': {
                                'id': project.id,
                                'name': project.name,
                                'is_active': project.is_active,
                            }
                        })
                    
        elif request.method == 'DELETE':
            project_name = project.name
            project.is_active = False
            project.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Voucher project "{project_name}" deactivated (soft deleted) successfully'
            })    
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)


# ================================
# VOUCHER LIMIT VIEWS
# ================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def voucher_limit_list(request):
    """List all voucher limits or create new one"""
    if request.method == 'GET':
        limits = VoucherLimit.objects.select_related('voucher_project').all().order_by('-created_at')
        limit_list = []
        
        for limit in limits:
            limit_data = {
                'id': limit.id,
                'description': limit.description,
                'limit': limit.limit,
                'current_count': limit.current_count,
                'remaining': limit.limit - limit.current_count,
                'percentage_used': (limit.current_count / limit.limit * 100) if limit.limit > 0 else 0,
                'voucher_project': {
                    'id': limit.voucher_project.id,
                    'name': limit.voucher_project.name,
                } if limit.voucher_project else None,
                'created_at': limit.created_at.isoformat(),
            }
            limit_list.append(limit_data)
        
        return JsonResponse({
            'success': True,
            'data': limit_list,
            'total': len(limit_list)
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get voucher project if provided
            voucher_project = None
            if data.get('voucher_project_id'):
                voucher_project = get_object_or_404(VoucherProject, id=data.get('voucher_project_id'))
            
            # Create new voucher limit
            limit = VoucherLimit.objects.create(
                description=data.get('description'),
                limit=data.get('limit', 0),
                current_count=data.get('current_count', 0),
                voucher_project=voucher_project,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher limit created successfully',
                'data': {
                    'id': limit.id,
                    'description': limit.description,
                    'limit': limit.limit,
                    'current_count': limit.current_count,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating voucher limit: {str(e)}'
            }, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def voucher_limit_detail(request, limit_id):
    """Get, update, or delete specific voucher limit"""
    try:
        limit = get_object_or_404(VoucherLimit, id=limit_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': limit.id,
                    'description': limit.description,
                    'limit': limit.limit,
                    'current_count': limit.current_count,
                    'remaining': limit.limit - limit.current_count,
                    'voucher_project': {
                        'id': limit.voucher_project.id,
                        'name': limit.voucher_project.name,
                    } if limit.voucher_project else None,
                    'created_at': limit.created_at.isoformat(),
                }
            })
        
        elif request.method == 'PUT':
            data = json.loads(request.body)
            
            # Update limit fields
            limit.description = data.get('description', limit.description)
            limit.limit = data.get('limit', limit.limit)
            limit.current_count = data.get('current_count', limit.current_count)
            
            # Update voucher project if provided
            if data.get('voucher_project_id'):
                limit.voucher_project = get_object_or_404(VoucherProject, id=data.get('voucher_project_id'))
            
            limit.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher limit updated successfully',
                'data': {
                    'id': limit.id,
                    'description': limit.description,
                    'limit': limit.limit,
                    'current_count': limit.current_count,
                }
            })
        
        elif request.method == 'DELETE':
            description = limit.description
            limit.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Voucher limit "{description}" deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def voucher_limit_increment(request, limit_id):
    """Increment current count for voucher limit"""
    try:
        limit = get_object_or_404(VoucherLimit, id=limit_id)
        data = json.loads(request.body)
        increment = data.get('increment', 1)
        
        # Check if increment would exceed limit
        new_count = limit.current_count + increment
        if new_count > limit.limit:
            return JsonResponse({
                'success': False,
                'message': f'Cannot increment. Would exceed limit of {limit.limit}'
            }, status=400)
        
        limit.current_count = new_count
        limit.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Voucher count incremented by {increment}',
            'data': {
                'id': limit.id,
                'current_count': limit.current_count,
                'remaining': limit.limit - limit.current_count,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)


# ================================
# VOUCHER RETAILER DISCOUNT VIEWS
# ================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def voucher_discount_list(request):
    """List all voucher discounts or create new one"""
    if request.method == 'GET':
        discounts = VoucherRetailerDiscount.objects.select_related('voucher_project').all().order_by('-created_at')
        discount_list = []
        
        for discount in discounts:
            discount_data = {
                'id': discount.id,
                'discount_amount': float(discount.discount_amount),
                'discount_percentage': float(discount.discount_percentage),
                'agen_fee': float(discount.agen_fee) if discount.agen_fee else None,
                'voucher_project': {
                    'id': discount.voucher_project.id,
                    'name': discount.voucher_project.name,
                } if discount.voucher_project else None,
                'created_at': discount.created_at.isoformat(),
                'created_by': discount.created_by,
                'updated_at': discount.updated_at.isoformat() if discount.updated_at else None,
                'updated_by': discount.updated_by,
            }
            discount_list.append(discount_data)
        
        return JsonResponse({
            'success': True,
            'data': discount_list,
            'total': len(discount_list)
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get voucher project if provided
            voucher_project = None
            if data.get('voucher_project_id'):
                voucher_project = get_object_or_404(VoucherProject, id=data.get('voucher_project_id'))
            
            # Create new voucher discount
            discount = VoucherRetailerDiscount.objects.create(
                discount_amount=data.get('discount_amount', 0),
                discount_percentage=data.get('discount_percentage', 0),
                agen_fee=data.get('agen_fee'),
                voucher_project=voucher_project,
                created_by=data.get('created_by'),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher discount created successfully',
                'data': {
                    'id': discount.id,
                    'discount_amount': float(discount.discount_amount),
                    'discount_percentage': float(discount.discount_percentage),
                    'agen_fee': float(discount.agen_fee) if discount.agen_fee else None,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating voucher discount: {str(e)}'
            }, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def voucher_discount_detail(request, discount_id):
    """Get, update, or delete specific voucher discount"""
    try:
        discount = get_object_or_404(VoucherRetailerDiscount, id=discount_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': discount.id,
                    'discount_amount': float(discount.discount_amount),
                    'discount_percentage': float(discount.discount_percentage),
                    'agen_fee': float(discount.agen_fee) if discount.agen_fee else None,
                    'voucher_project': {
                        'id': discount.voucher_project.id,
                        'name': discount.voucher_project.name,
                    } if discount.voucher_project else None,
                    'created_at': discount.created_at.isoformat(),
                    'created_by': discount.created_by,
                    'updated_at': discount.updated_at.isoformat() if discount.updated_at else None,
                    'updated_by': discount.updated_by,
                }
            })
        
        elif request.method == 'PUT':
            data = json.loads(request.body)
            
            # Update discount fields
            discount.discount_amount = data.get('discount_amount', discount.discount_amount)
            discount.discount_percentage = data.get('discount_percentage', discount.discount_percentage)
            discount.agen_fee = data.get('agen_fee', discount.agen_fee)
            discount.updated_by = data.get('updated_by')
            discount.updated_at = timezone.now()
            
            # Update voucher project if provided
            if data.get('voucher_project_id'):
                discount.voucher_project = get_object_or_404(VoucherProject, id=data.get('voucher_project_id'))
            
            discount.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher discount updated successfully',
                'data': {
                    'id': discount.id,
                    'discount_amount': float(discount.discount_amount),
                    'discount_percentage': float(discount.discount_percentage),
                    'agen_fee': float(discount.agen_fee) if discount.agen_fee else None,
                }
            })
        
        elif request.method == 'DELETE':
            discount.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Voucher discount deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)


# ================================
# UTILITY VIEWS
# ================================

@csrf_exempt
@require_http_methods(["GET"])
def voucher_project_active_list(request):
    """Get only active voucher projects"""
    projects = VoucherProject.objects.filter(is_active=True).order_by('name')
    project_list = []
    
    for project in projects:
        project_data = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'periode_start': project.periode_start.isoformat() if project.periode_start else None,
            'periode_end': project.periode_end.isoformat() if project.periode_end else None,
        }
        project_list.append(project_data)
    
    return JsonResponse({
        'success': True,
        'data': project_list,
        'total': len(project_list)
    })


@csrf_exempt
@require_http_methods(["GET"])
def voucher_summary(request):
    """Get summary of voucher limits and projects"""
    total_projects = VoucherProject.objects.count()
    active_projects = VoucherProject.objects.filter(is_active=True).count()
    total_limits = VoucherLimit.objects.count()
    
    # Calculate total voucher usage
    limits = VoucherLimit.objects.all()
    total_allocated = sum(limit.limit for limit in limits)
    total_used = sum(limit.current_count for limit in limits)
    total_remaining = total_allocated - total_used
    
    return JsonResponse({
        'success': True,
        'data': {
            'projects': {
                'total': total_projects,
                'active': active_projects,
                'inactive': total_projects - active_projects,
            },
            'vouchers': {
                'total_allocated': total_allocated,
                'total_used': total_used,
                'total_remaining': total_remaining,
                'usage_percentage': (total_used / total_allocated * 100) if total_allocated > 0 else 0,
            },
            'limits_count': total_limits,
        }
    })
