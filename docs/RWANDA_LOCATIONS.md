# Rwanda Location Hierarchy Guide

This guide explains how to use the Rwanda administrative location structure (Province → District → Sector → Cell → Village) in your application.

## Database Structure

The location hierarchy is stored in 5 connected models:

- **Province** - Highest level (5 provinces + Kigali city)
- **District** - Within provinces (30+ districts)
- **Sector** - Within districts
- **Cell** - Within sectors
- **Village** - Smallest unit within cells

## Models

Located in `core/models.py`:

```python
Province
  ├── District
  │   ├── Sector
  │   │   ├── Cell
  │   │   │   └── Village
```

## API Endpoints

### 1. Get All Provinces
```
GET /core/api/locations/provinces/

Response:
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Kigali", "code": "KGL"},
    {"id": 2, "name": "Northern Province", "code": "NRP"},
    ...
  ]
}
```

### 2. Get Districts by Province
```
GET /core/api/locations/districts/{province_id}/

Response:
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Gasabo", "code": "GSB"},
    {"id": 2, "name": "Kicukiro", "code": "KCK"},
    ...
  ]
}
```

### 3. Get Sectors by District
```
GET /core/api/locations/sectors/{district_id}/

Response:
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Remera", "code": "REM"},
    {"id": 2, "name": "Kacyiru", "code": "KCY"},
    ...
  ]
}
```

### 4. Get Cells by Sector
```
GET /core/api/locations/cells/{sector_id}/

Response:
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Remera", "code": "REM"},
    {"id": 2, "name": "Gisozi", "code": "GSZ"},
    ...
  ]
}
```

### 5. Get Villages by Cell
```
GET /core/api/locations/villages/{cell_id}/

Response:
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Remera Village", "code": "REM-V1"},
    {"id": 2, "name": "Remera Central", "code": "REM-V2"},
    ...
  ]
}
```

### 6. Get Complete Location Tree
```
GET /core/api/locations/tree/

Returns the entire nested hierarchy as a single JSON response.
Use for loading complete structure in frontend applications.

Response:
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Kigali",
      "code": "KGL",
      "districts": [
        {
          "id": 1,
          "name": "Gasabo",
          "code": "GSB",
          "sectors": [
            {
              "id": 1,
              "name": "Remera",
              "code": "REM",
              "cells": [
                {
                  "id": 1,
                  "name": "Remera",
                  "code": "REM",
                  "villages": [
                    {
                      "id": 1,
                      "name": "Remera Village",
                      "code": "REM-V1"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 7. Search Locations
```
GET /core/api/locations/search/?q={query}&level={optional_level}

Parameters:
- q: Search query (minimum 2 characters)
- level: Optional level to search ('province', 'district', 'sector', 'cell', 'village')
         If omitted, searches all levels

Response:
{
  "status": "success",
  "data": {
    "provinces": [...],
    "districts": [...],
    "sectors": [...],
    "cells": [...],
    "villages": [...]
  }
}

Examples:
- Search all locations for "Kigali": /core/api/locations/search/?q=Kigali
- Search only districts: /core/api/locations/search/?q=Kigali&level=district
```

## Loading Initial Data

The Rwanda location data is provided as a JSON fixture:

```bash
python manage.py loaddata core/fixtures/rwanda_locations.json
```

This loads:
- All 5 provinces
- 30 districts across provinces
- Sample sectors, cells, and villages for Gasabo district

To extend with more data, edit the fixture file and add more entries.

### Sync full government dataset

To load the full official Rwanda location dataset and regenerate the fixture file:

```bash
python manage.py sync_rwanda_locations
```

This command downloads the public dataset from `jnkindi/rwanda-locations-json`,
replaces existing location records, and rewrites
`core/fixtures/rwanda_locations.json`.

If you want to keep existing records and only add missing ones:

```bash
python manage.py sync_rwanda_locations --keep-existing
```

## Frontend Implementation

### Using JavaScript Manager (Cascading Dropdowns)

```html
<!-- Include the script -->
<script src="{% static 'js/rwanda-location-manager.js' %}"></script>

<!-- Your form with location selects -->
<form>
  <select id="id_province" name="province"></select>
  <select id="id_district" name="district"></select>
  <select id="id_sector" name="sector"></select>
  <select id="id_cell" name="cell"></select>
  <select id="id_village" name="village"></select>
</form>

<!-- Initialize the manager -->
<script>
  const locationManager = new RwandaLocationManager({
    apiBaseUrl: '/core/api/locations',
    provinceSelector: '#id_province',
    districtSelector: '#id_district',
    sectorSelector: '#id_sector',
    cellSelector: '#id_cell',
    villageSelector: '#id_village'
  });
  
  // Get selected location
  const location = locationManager.getSelectedLocation();
  console.log(location);
  // Output: { province_id: 1, district_id: 2, sector_id: 3, cell_id: 4, village_id: 5 }
  
  // Set location programmatically
  await locationManager.setLocation(1, 2, 3, 4, 5);
</script>
```

### Using with Django Forms

In your form template:

```django
{% extends "base.html" %}
{% load static %}

{% block content %}
<form method="post">
  {% csrf_token %}
  
  {{ form.head_of_family }}
  {{ form.phone_number }}
  
  {{ form.province }}
  {{ form.district }}
  {{ form.sector }}
  {{ form.cell }}
  {{ form.village }}
  
  <button type="submit">Save</button>
</form>

<script src="{% static 'js/rwanda-location-manager.js' %}"></script>
<script>
  const locationManager = new RwandaLocationManager();
</script>
{% endblock %}
```

### Using HTMX for Dynamic Updates

```html
<select id="id_province" 
        name="province"
        hx-get="/core/api/locations/districts/{{ object.province.id }}/"
        hx-target="#id_district"
        hx-trigger="change"
        hx-swap="innerHTML">
  <option value="">Select Province</option>
</select>

<select id="id_district" name="district">
  <option value="">Select District</option>
</select>
```

## Python Usage

### In Views

```python
from core.models import Province, District, Sector, Cell, Village

# Get a province's districts
province = Province.objects.get(name="Kigali")
districts = province.districts.all()

# Get a district's sectors
district = District.objects.get(name="Gasabo")
sectors = district.sectors.all()

# Get a sector's cells
sector = Sector.objects.get(name="Remera")
cells = sector.cells.all()

# Get a cell's villages
cell = Cell.objects.get(name="Remera")
villages = cell.villages.all()
```

### In Admin

```python
from django.contrib import admin
from .models import Province, District, Sector, Cell, Village

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'code']
    list_filter = ['province']
    search_fields = ['name', 'code']

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'code']
    list_filter = ['district__province', 'district']
    search_fields = ['name', 'code']

@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ['name', 'sector', 'code']
    list_filter = ['sector__district__province', 'sector__district']
    search_fields = ['name', 'code']

@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'cell', 'code']
    list_filter = ['cell__sector__district__province', 'cell__sector__district']
    search_fields = ['name', 'code']
```

## In Django Models

When creating models that reference locations:

```python
from core.models import Province, District, Sector, Cell, Village

class Family(models.Model):
    head_of_family = models.CharField(max_length=200)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True)
    cell = models.ForeignKey(Cell, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True)
```

## In Django Forms

```python
from django import forms
from core.models import Province, District, Sector, Cell, Village

class LocationForm(forms.Form):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        empty_label="Select Province",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        empty_label="Select District",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sector = forms.ModelChoiceField(
        queryset=Sector.objects.none(),
        empty_label="Select Sector",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    cell = forms.ModelChoiceField(
        queryset=Cell.objects.none(),
        empty_label="Select Cell",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    village = forms.ModelChoiceField(
        queryset=Village.objects.none(),
        empty_label="Select Village",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
```

## Querying Examples

### Get all families in a specific location

```python
from families.models import Family

# All families in Kigali
families = Family.objects.filter(province__name="Kigali")

# All families in Gasabo district
families = Family.objects.filter(district__name="Gasabo")

# All families in Remera sector
families = Family.objects.filter(sector__name="Remera")

# All families in a specific cell
families = Family.objects.filter(cell__name="Remera")
```

### Get location summary for a model

```python
from families.models import Family
from django.db.models import Count

# Count families by province
summary = Family.objects.values('province__name').annotate(count=Count('id'))

# Count families by district
summary = Family.objects.values('district__name').annotate(count=Count('id'))
```

## JSON Export

To export location data as JSON:

```bash
python manage.py dumpdata core.Province core.District core.Sector core.Cell core.Village --indent 2 > locations.json
```

To import from an external JSON file:

```bash
python manage.py loaddata locations.json
```

## Adding More Data

Edit `core/fixtures/rwanda_locations.json` and add more entries:

```json
{
  "model": "core.village",
  "pk": 100,
  "fields": {
    "name": "New Village",
    "cell": 1,
    "code": "NV-001"
  }
}
```

Then reload:

```bash
python manage.py loaddata core/fixtures/rwanda_locations.json
```

## Performance Tips

1. **Use select_related() for Foreign Keys:**
   ```python
   villages = Village.objects.select_related('cell', 'cell__sector', 'cell__sector__district')
   ```

2. **Use prefetch_related() for Reverse Relations:**
   ```python
   provinces = Province.objects.prefetch_related('districts__sectors__cells__villages')
   ```

3. **Use the full location tree API if loading all at once:**
   ```javascript
   fetch('/core/api/locations/tree/')
   ```

4. **Cache location data in frontend if frequently accessed:**
   ```javascript
   // Store in localStorage for offline access
   localStorage.setItem('locations', JSON.stringify(locationsData));
   ```
