from django.db import models


class Province(models.Model):
    """Rwanda Province model."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class District(models.Model):
    """Rwanda District model."""
    name = models.CharField(max_length=200)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'province']

    def __str__(self):
        return f"{self.name} - {self.province.name}"


class Sector(models.Model):
    """Rwanda Sector model."""
    name = models.CharField(max_length=200)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='sectors')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'district']

    def __str__(self):
        return f"{self.name} - {self.district.name}"


class Cell(models.Model):
    """Rwanda Cell model."""
    name = models.CharField(max_length=200)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='cells')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'sector']

    def __str__(self):
        return f"{self.name} - {self.sector.name}"


class Village(models.Model):
    """Rwanda Village model."""
    name = models.CharField(max_length=200)
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE, related_name='villages')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'cell']

    def __str__(self):
        return f"{self.name} - {self.cell.name}"


class School(models.Model):
    """School model for storing school information."""
    name = models.CharField(max_length=200)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='schools')
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.district.name if self.district else 'N/A'}"
