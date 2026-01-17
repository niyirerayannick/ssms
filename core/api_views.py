"""
API views for Rwanda administrative structure.
Returns JSON data for hierarchical location selection.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Province, District, Sector, Cell, Village


@require_http_methods(["GET"])
def get_provinces(request):
    """Get all provinces as JSON."""
    provinces = Province.objects.all().values('id', 'name', 'code')
    return JsonResponse({
        'status': 'success',
        'data': list(provinces)
    })


@require_http_methods(["GET"])
def get_districts(request, province_id):
    """Get districts for a specific province."""
    districts = District.objects.filter(
        province_id=province_id
    ).values('id', 'name', 'code')
    return JsonResponse({
        'status': 'success',
        'data': list(districts)
    })


@require_http_methods(["GET"])
def get_sectors(request, district_id):
    """Get sectors for a specific district."""
    sectors = Sector.objects.filter(
        district_id=district_id
    ).values('id', 'name', 'code')
    return JsonResponse({
        'status': 'success',
        'data': list(sectors)
    })


@require_http_methods(["GET"])
def get_cells(request, sector_id):
    """Get cells for a specific sector."""
    cells = Cell.objects.filter(
        sector_id=sector_id
    ).values('id', 'name', 'code')
    return JsonResponse({
        'status': 'success',
        'data': list(cells)
    })


@require_http_methods(["GET"])
def get_villages(request, cell_id):
    """Get villages for a specific cell."""
    villages = Village.objects.filter(
        cell_id=cell_id
    ).values('id', 'name', 'code')
    return JsonResponse({
        'status': 'success',
        'data': list(villages)
    })


@require_http_methods(["GET"])
def get_full_location_tree(request):
    """
    Get complete Rwanda location hierarchy as nested JSON.
    Useful for frontend autocomplete/selection components.
    """
    provinces = Province.objects.prefetch_related(
        'districts__sectors__cells__villages'
    ).values('id', 'name', 'code')
    
    result = []
    for province in provinces:
        province_data = {
            'id': province['id'],
            'name': province['name'],
            'code': province['code'],
            'districts': []
        }
        
        districts = District.objects.filter(
            province_id=province['id']
        ).prefetch_related('sectors__cells__villages')
        
        for district in districts:
            district_data = {
                'id': district.id,
                'name': district.name,
                'code': district.code,
                'sectors': []
            }
            
            for sector in district.sectors.all():
                sector_data = {
                    'id': sector.id,
                    'name': sector.name,
                    'code': sector.code,
                    'cells': []
                }
                
                for cell in sector.cells.all():
                    cell_data = {
                        'id': cell.id,
                        'name': cell.name,
                        'code': cell.code,
                        'villages': []
                    }
                    
                    for village in cell.villages.all():
                        village_data = {
                            'id': village.id,
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
        results['provinces'] = list(
            Province.objects.filter(name__icontains=query).values('id', 'name', 'code')
        )
    
    if not level or level == 'district':
        results['districts'] = list(
            District.objects.filter(name__icontains=query).select_related('province').values(
                'id', 'name', 'code', 'province__name'
            )
        )
    
    if not level or level == 'sector':
        results['sectors'] = list(
            Sector.objects.filter(name__icontains=query).select_related(
                'district', 'district__province'
            ).values('id', 'name', 'code', 'district__name', 'district__province__name')
        )
    
    if not level or level == 'cell':
        results['cells'] = list(
            Cell.objects.filter(name__icontains=query).select_related(
                'sector', 'sector__district', 'sector__district__province'
            ).values('id', 'name', 'code', 'sector__name', 'sector__district__name')
        )
    
    if not level or level == 'village':
        results['villages'] = list(
            Village.objects.filter(name__icontains=query).select_related(
                'cell', 'cell__sector', 'cell__sector__district'
            ).values('id', 'name', 'code', 'cell__name', 'cell__sector__name')
        )
    
    return JsonResponse({
        'status': 'success',
        'data': results
    })
