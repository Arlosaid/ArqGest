from django.contrib import admin
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import ProjectFile


class FileSizeFilter(admin.SimpleListFilter):
    """Filtro por tamaño de archivo."""
    title = 'Tamaño'
    parameter_name = 'size_range'

    def lookups(self, request, model_admin):
        return (
            ('small', '< 1 MB'),
            ('medium', '1-10 MB'),
            ('large', '> 10 MB'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'small':
            return queryset.filter(size_bytes__lt=1024*1024)
        if self.value() == 'medium':
            return queryset.filter(size_bytes__gte=1024*1024, size_bytes__lt=10*1024*1024)
        if self.value() == 'large':
            return queryset.filter(size_bytes__gte=10*1024*1024)


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    """Administración simple y optimizada de archivos de proyecto."""
    
    # Vista principal simplificada
    list_display = ('get_file_info', 'get_location', 'get_size_display', 'uploaded_at', 'get_actions')
    
    # Filtros simples pero efectivos
    list_filter = (
        ('phase__project__organization', admin.RelatedOnlyFieldListFilter),
        ('phase__project', admin.RelatedOnlyFieldListFilter),
        ('ext_upper', admin.ChoicesFieldListFilter),
        FileSizeFilter,
        ('uploaded_at', admin.DateFieldListFilter),
    )
    
    # Búsqueda optimizada
    search_fields = ('file', 'phase__project__name', 'phase__project__organization__name', 'phase__name')
    
    # Orden lógico
    ordering = ('-uploaded_at',)
    
    # Campos de solo lectura
    readonly_fields = ('uploaded_at', 'filename', 'extension', 'size_bytes')
    
    # Acciones útiles
    actions = ['calculate_storage', 'export_file_list']
    
    # Paginación eficiente
    list_per_page = 25
    
    # CSS simple
    class Media:
        css = {
            'all': ('css/admin_files_simple.css',)
        }
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'phase__project__organization', 'uploaded_by', 'phase__project', 'phase'
        )
    
    def get_file_info(self, obj):
        """Información del archivo con icono y descarga."""
        # Iconos simples por tipo
        icons = {
            'PDF': '📄', 'DOC': '📝', 'DOCX': '📝', 'XLS': '📊', 'XLSX': '📊',
            'JPG': '🖼️', 'PNG': '🖼️', 'GIF': '🖼️', 'ZIP': '🗜️', 'DWG': '📐'
        }
        icon = icons.get(obj.ext_upper, '📎')
        
        if obj.file:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="font-size: 18px;">{}</span>'
                '<div>'
                '<strong><a href="{}" target="_blank" style="text-decoration: none; color: #0073aa;">{}</a></strong><br>'
                '<small style="color: #666; background: #f0f0f0; padding: 2px 5px; border-radius: 3px;">{}</small>'
                '</div>'
                '</div>',
                icon, obj.file.url, obj.filename, obj.ext_upper
            )
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<span style="font-size: 18px;">🚫</span>'
            '<div><strong>{}</strong><br><small style="color: #666;">{}</small></div>'
            '</div>',
            obj.filename, obj.ext_upper
        )
    get_file_info.short_description = 'Archivo'
    get_file_info.admin_order_field = 'file'
    
    def get_location(self, obj):
        """Ubicación jerárquica simple."""
        if obj.phase and obj.phase.project and obj.phase.project.organization:
            return format_html(
                '<div style="font-size: 12px; line-height: 1.4;">'
                '<div style="color: #0073aa; font-weight: bold;">🏢 {}</div>'
                '<div style="color: #666; margin-left: 10px;">📁 {}</div>'
                '<div style="color: #999; margin-left: 20px;">📋 {}</div>'
                '</div>',
                obj.phase.project.organization.name,
                obj.phase.project.name,
                obj.phase.name
            )
        return format_html('<span style="color: #999;">Sin ubicación</span>')
    get_location.short_description = 'Ubicación'
    get_location.admin_order_field = 'phase__project__organization__name'
    
    def get_size_display(self, obj):
        """Tamaño con color."""
        size = filesizeformat(obj.size_bytes or 0)
        if obj.size_bytes:
            if obj.size_bytes > 10 * 1024 * 1024:  # > 10MB
                color = '#d63384'
            elif obj.size_bytes > 1 * 1024 * 1024:  # > 1MB
                color = '#fd7e14'
            else:
                color = '#198754'
            
            return format_html(
                '<span style="color: {}; font-weight: 600; font-size: 13px;">{}</span>',
                color, size
            )
        return size
    get_size_display.short_description = 'Tamaño'
    get_size_display.admin_order_field = 'size_bytes'
    
    def get_actions(self, obj):
        """Acciones rápidas."""
        actions = []
        
        # Verificar que obj es una instancia de ProjectFile
        if hasattr(obj, 'file') and obj.file:
            actions.append(format_html(
                '<a href="{}" target="_blank" title="Descargar" style="color: #198754; text-decoration: none; margin-right: 8px;">⬇️</a>',
                obj.file.url
            ))
        
        if hasattr(obj, 'pk'):
            actions.append(format_html(
                '<a href="{}" title="Editar" style="color: #0073aa; text-decoration: none; margin-right: 8px;">✏️</a>',
                reverse('admin:files_projectfile_change', args=[obj.pk])
            ))
        
        if hasattr(obj, 'uploaded_by') and obj.uploaded_by:
            actions.append(format_html(
                '<span title="Subido por {}" style="color: #666;">👤</span>',
                obj.uploaded_by.get_full_name() or obj.uploaded_by.email
            ))
        
        return format_html(''.join(actions))
    get_actions.short_description = 'Acciones'
    
    def calculate_storage(self, request, queryset):
        """Calcular uso de almacenamiento."""
        total_size = queryset.aggregate(total=Sum('size_bytes'))['total'] or 0
        total_files = queryset.count()
        
        # Estadísticas por organización
        orgs = {}
        for file_obj in queryset.select_related('phase__project__organization'):
            if file_obj.phase and file_obj.phase.project and file_obj.phase.project.organization:
                org_name = file_obj.phase.project.organization.name
                if org_name not in orgs:
                    orgs[org_name] = {'size': 0, 'count': 0}
                orgs[org_name]['size'] += file_obj.size_bytes or 0
                orgs[org_name]['count'] += 1
        
        message = f"📊 RESUMEN DE ALMACENAMIENTO\n"
        message += f"Total: {filesizeformat(total_size)} en {total_files} archivos\n\n"
        
        if orgs:
            message += "Por organización:\n"
            for org_name, data in sorted(orgs.items()):
                message += f"• {org_name}: {filesizeformat(data['size'])} ({data['count']} archivos)\n"
        
        self.message_user(request, message, messages.INFO)
    calculate_storage.short_description = "📊 Calcular almacenamiento"
    
    def export_file_list(self, request, queryset):
        """Exportar lista de archivos seleccionados."""
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="archivos_{timestamp}.csv"'
        
        # Escribir BOM para UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'Archivo', 'Extensión', 'Tamaño', 'Organización', 
            'Proyecto', 'Fase', 'Usuario', 'Fecha Subida'
        ])
        
        for file_obj in queryset.select_related('phase__project__organization', 'uploaded_by'):
            org = file_obj.phase.project.organization.name if file_obj.phase and file_obj.phase.project and file_obj.phase.project.organization else 'Sin organización'
            project = file_obj.phase.project.name if file_obj.phase and file_obj.phase.project else 'Sin proyecto'
            phase = file_obj.phase.name if file_obj.phase else 'Sin fase'
            user = file_obj.uploaded_by.get_full_name() or file_obj.uploaded_by.email if file_obj.uploaded_by else 'Usuario desconocido'
            
            writer.writerow([
                file_obj.filename,
                file_obj.ext_upper,
                filesizeformat(file_obj.size_bytes or 0),
                org,
                project,
                phase,
                user,
                file_obj.uploaded_at.strftime('%d/%m/%Y %H:%M')
            ])
        
        # Mensaje de confirmación
        count = queryset.count()
        self.message_user(
            request, 
            f"📋 Se exportaron {count} archivo{'s' if count != 1 else ''} exitosamente",
            messages.SUCCESS
        )
        return response
    export_file_list.short_description = "📋 Exportar lista (.csv)"