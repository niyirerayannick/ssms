"""
API views for Rwanda administrative structure.
Returns JSON data for hierarchical location selection.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Province, District, Sector, Cell, Village
from .utils import encode_id

@require_http_methods(["GET"])
def get_provinces(request):
    """Get all provinces as JSON."""
    provinces = Province.objects.all()
    data = [{
        'id': encode_id(p.id),
        'name': p.name,
        'code': p.code
    } for p in provinces]
    return JsonResponse({
        'status': 'success',
        'data': data
    })


@require_http_methods(["GET"])
def get_districts(request, province_id):
    """Get districts for a specific province."""
    districts = District.objects.filter(province_id=province_id)
    data = [{
        'id': encode_id(d.id),
        'name': d.name,
        'code': d.code
    } for d in districts]
    return JsonResponse({
        'status': 'success',
        'data': data
    })


@require_http_methods(["GET"])
def get_sectors(request, district_id):
    """Get sectors for a specific district."""
    sectors = Sector.objects.filter(district_id=district_id)
    data = [{
        'id': encode_id(s.id),
        'name': s.name,
        'code': s.code
    } for s in sectors]
    return JsonResponse({
        'status': 'success',
        'data': data
    })


@require_http_methods(["GET"])
def get_cells(request, sector_id):
    """Get cells for a specific sector."""
    cells = Cell.objects.filter(sector_id=sector_id)
    data = [{
        'id': encode_id(c.id),
        'name': c.name,
        'code': c.code
    } for c in cells]
    return JsonResponse({
        'status': 'success',
        'data': data
    })


@require_http_methods(["GET"])
def get_villages(request, cell_id):
    """Get villages for a specific cell."""
    villages = Village.objects.filter(cell_id=cell_id)
    data = [{
        'id': encode_id(v.id),
        'name': v.name,
        'code': v.code
    } for v in villages]
    return JsonResponse({
        'status': 'success',
        'data': data
    })


@require_http_methods(["GET"])
def get_full_location_tree(request):
    """
    Get complete Rwanda location hierarchy as nested JSON.
    Useful for frontend autocomplete/selection components.
    """
    provinces = Province.objects.prefetch_related(
        'districts__sectors__cells__villages'
    )
    
    result = []
    for province in provinces:
        province_data = {
            'id': encode_id(province.id),
            'name': province.name,
            'code': province.code,
            'districts': []
        }
        
        for district in province.districts.all():
            district_data = {
                'id': encode_id(district.id),
                'name': district.name,
                'code': district.code,
                'sectors': []
            }
            
            for sector in district.sectors.all():
                sector_data = {
                    'id': encode_id(sector.id),
                    'name': sector.name,
                    'code': sector.code,
                    'cells': []
                }
                
                for cell in sector.cells.all():
                    cell_data = {
                        'id': encode_id(cell.id),
                        'name': cell.name,
                        'code': cell.code,
                        'villages': []
                    }
                    
                    for village in cell.villages.all():
                        village_data = {
                            'id': encode_id(village.id),
                            'name': village.name,
                            'code': village.code
                        }
                        cell_data['villages'].append(village_data)
                    
                    sector_data['cells'].append(cell_data)
                
                district_data['sectors'].append(sector_data)
            
            province_data['districts'].append(district_data)
        
        result.append(province_data)
    
    return JsonResponse({
        'status': 'success',
        'data': result
    })


@require_http_methods(["GET"])
def search_locations(request):
    """
    Search across all location levels.
    Query parameters:
    - q: search query string
    - level: 'province', 'district', 'sector', 'cell', 'village' (optional)
    """
    query = request.GET.get('q', '').strip()
    level = request.GET.get('level', '')
    
    if not query or len(query) < 2:
        return JsonResponse({
            'status': 'error',
            'message': 'Query must be at least 2 characters'
        }, status=400)
    
    results = {
        'provinces': [],
        'districts': [],
        'sectors': [],
        'cells': [],
        'villages': []
    }
    
    if not level or level == 'province':
        results['provinces'] = [{
            'id': encode_id(p.id),
            'name': p.name,
            'code': p.code
        } for p in Province.objects.filter(name__icontains=query)]
    
    if not level or level == 'district':
        results['districts'] = [{
            'id': encode_id(d.id),
            'name': d.name,
            'code': d.code,
            'province__name': d.province.name if d.province else None
        } for d in District.objects.filter(name__icontains=query).select_related('province')]
    
    if not level or level == 'sector':
        results['sectors'] = [{
            'id': encode_id(s.id),
            'name': s.name,
            'code': s.code,
            'district__name': s.district.name,
            'district__province__name': s.district.province.name if s.district.province else None
        } for s in Sector.objects.filter(name__icontains=query).select_related('district', 'district__province')]
    
    if not level or level == 'cell':
        results['cells'] = [{
            'id': encode_id(c.id),
            'name': c.name,
            'code': c.code,
            'sector__name': c.sector.name,
            'sector__district__name': c.sector.district.name
        } for c in Cell.objects.filter(name__icontains=query).select_related('sector', 'sector__district')]
    
    if not level or level == 'village':
        results['villages'] = [{
            'id': encode_id(v.id),
            'name': v.name,
            'code': v.code,
            'cell__name': v.cell.name,
            'cell__sector__name': v.cell.sector.name
        } for v in Village.objects.filter(name__icontains=query).select_related('cell', 'cell__sector')]
    
    return JsonResponse({
        'status': 'success',
        'data': results
    })
