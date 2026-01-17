from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import District, Sector, Cell, Village, Province


@require_http_methods(["GET"])
def get_districts(request):
    """Get districts for a given province."""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse({'error': 'province_id required'}, status=400)
    
    districts = District.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse({'districts': list(districts)})


@require_http_methods(["GET"])
def get_sectors(request):
    """Get sectors for a given district."""
    district_id = request.GET.get('district_id')
    if not district_id:
        return JsonResponse({'error': 'district_id required'}, status=400)
    
    sectors = Sector.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse({'sectors': list(sectors)})


@require_http_methods(["GET"])
def get_cells(request):
    """Get cells for a given sector."""
    sector_id = request.GET.get('sector_id')
    if not sector_id:
        return JsonResponse({'error': 'sector_id required'}, status=400)
    
    cells = Cell.objects.filter(sector_id=sector_id).values('id', 'name')
    return JsonResponse({'cells': list(cells)})


@require_http_methods(["GET"])
def get_villages(request):
    """Get villages for a given cell."""
    cell_id = request.GET.get('cell_id')
    if not cell_id:
        return JsonResponse({'error': 'cell_id required'}, status=400)
    
    villages = Village.objects.filter(cell_id=cell_id).values('id', 'name')
    return JsonResponse({'villages': list(villages)})
