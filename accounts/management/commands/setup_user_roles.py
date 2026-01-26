"""
Management command to set up user roles and permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Set up user roles (Admin, Accountant, Executive Secretary, Program Officer) with appropriate permissions'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Setting up user roles and permissions...'))
        
        # Define roles and their permissions
        roles = {
            'Admin': {
                'description': 'Full system access',
                'permissions': 'all'
            },
            'Council Member': {
                'description': 'Read-only access to student performance',
                'apps': ['students'],
                'permissions': ['view'],
            },
            'Data Entry': {
                'description': 'Data entry for students, families, and schools',
                'apps': ['students', 'families', 'core'],
                'permissions': ['view', 'add', 'change'],
            },
            'Accountant': {
                'description': 'Financial management and reporting - Full view access to all finance-related data',
                'apps': ['finance', 'insurance', 'students', 'families', 'core', 'reports'],
                'permissions': ['view', 'add', 'change'],
                'models': ['schoolfee', 'familyinsurance'],
                'extra_permissions': ['manage_fees', 'manage_insurance'],
            },
            'Executive Secretary': {
                'description': 'Overall coordination and reporting',
                'apps': ['students', 'families', 'core', 'finance', 'insurance', 'reports'],
                'permissions': ['view', 'add', 'change'],
                'extra_permissions': ['manage_fees', 'manage_insurance'],
            },
            'Program Officer': {
                'description': 'Student and family management',
                'apps': ['students', 'families', 'core'],
                'permissions': ['view', 'add', 'change'],
            }
        }
        
        for role_name, role_config in roles.items():
            # Create or get the group
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Role already exists: {role_name}'))
                # Clear existing permissions to reset
                group.permissions.clear()
            
            # Assign permissions
            if role_config.get('permissions') == 'all':
                # Admin gets all permissions
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(self.style.SUCCESS(f'  Assigned ALL permissions to {role_name}'))
            else:
                # Assign specific permissions based on apps
                permission_count = 0
                apps = role_config.get('apps', [])
                permission_types = role_config.get('permissions', ['view'])
                
                for app_label in apps:
                    # Get all content types for this app
                    content_types = ContentType.objects.filter(app_label=app_label)
                    
                    for content_type in content_types:
                        for perm_type in permission_types:
                            # Try to get the permission
                            codename = f'{perm_type}_{content_type.model}'
                            try:
                                permission = Permission.objects.get(
                                    codename=codename,
                                    content_type=content_type
                                )
                                group.permissions.add(permission)
                                permission_count += 1
                            except Permission.DoesNotExist:
                                pass
                
                extra_permissions = role_config.get('extra_permissions', [])
                if extra_permissions:
                    extra_perms = Permission.objects.filter(codename__in=extra_permissions)
                    if extra_perms:
                        group.permissions.add(*extra_perms)
                        permission_count += extra_perms.count()

                self.stdout.write(self.style.SUCCESS(f'  Assigned {permission_count} permissions to {role_name}'))
            
            self.stdout.write(self.style.SUCCESS(f'  Description: {role_config["description"]}\n'))
        
        self.stdout.write(self.style.SUCCESS('\nUser roles setup complete!'))
        self.stdout.write(self.style.SUCCESS('\nAvailable roles:'))
        for role_name, role_config in roles.items():
            self.stdout.write(f'  - {role_name}: {role_config["description"]}')
