from django.contrib import admin
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import ProjectFile
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class ProjectFileResource(resources.ModelResource):
    """Recurso para exportar información de archivos (sin los archivos en sí)."""
    class Meta:
        model = ProjectFile
        fields = ('id', 'filename', 'extension', 'size_bytes', 'phase__name', 
                 'phase__project__name', 'uploaded_by__email', 'uploaded_at')
        export_order = fields


@admin.register(ProjectFile)
class ProjectFileAdmin(ImportExportModelAdmin):
    """Administración avanzada de archivos de proyecto."""
    resource_class = ProjectFileResource
    list_display = ("get_filename_display", "get_extension_display", "get_size_display", 
                   "get_phase_link", "get_project_link", "get_uploaded_by_info", "uploaded_at")
    list_filter = ("ext_upper", "uploaded_at", "phase__project__organization__name")
    search_fields = ("file", "uploaded_by__first_name", "uploaded_by__last_name", 
                    "phase__name", "phase__project__name", "phase__project__organization__name")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)
    readonly_fields = ("uploaded_at", "filename", "extension", "size_bytes", "get_download_link",
                      "get_phase_link", "get_project_link", "get_size_display")
    actions = ["calculate_storage_usage", "mark_for_review"]
    
    fieldsets = (
        ("Información del Archivo", {
            'fields': ('get_download_link', 'filename', 'extension', 'get_size_display')
        }),
        ("Ubicación en el Proyecto", {
            'fields': ('phase', 'get_phase_link', 'get_project_link'),
            'description': 'Fase y proyecto donde está almacenado el archivo.'
        }),
        ("Información de Subida", {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'phase__project__organization', 'uploaded_by'
        )

    def get_filename_display(self, obj):
        """Mostrar nombre del archivo con icono según extensión."""
        # Iconos según extensión
        ext_icons = {
            'PDF': '📄',
            'DOC': '📝', 'DOCX': '📝',
            'XLS': '📊', 'XLSX': '📊',
            'PPT': '📊', 'PPTX': '📊',
            'JPG': '🖼️', 'JPEG': '🖼️', 'PNG': '🖼️', 'GIF': '🖼️',
            'ZIP': '🗜️', 'RAR': '🗜️',
            'TXT': '📄',
            'DWG': '📐', 'DXF': '📐',
        }
        
        icon = ext_icons.get(obj.ext_upper, '📎')
        return format_html(
            '{} <strong>{}</strong>',
            icon, obj.filename
        )
    get_filename_display.short_description = 'Archivo'
    get_filename_display.admin_order_field = 'file'

    def get_extension_display(self, obj):
        """Mostrar extensión con color."""
        ext_colors = {
            'PDF': '#FF5722',
            'DOC': '#2196F3', 'DOCX': '#2196F3',
            'XLS': '#4CAF50', 'XLSX': '#4CAF50',
            'JPG': '#9C27B0', 'JPEG': '#9C27B0', 'PNG': '#9C27B0', 'GIF': '#9C27B0',
            'ZIP': '#FF9800', 'RAR': '#FF9800',
            'DWG': '#607D8B', 'DXF': '#607D8B',
        }
        
        color = ext_colors.get(obj.ext_upper, '#666')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.ext_upper
        )
    get_extension_display.short_description = 'Tipo'
    get_extension_display.admin_order_field = 'ext_upper'

    def get_size_display(self, obj):
        """Mostrar tamaño formateado."""
        size = filesizeformat(obj.size_bytes or 0)
        if obj.size_bytes:
            if obj.size_bytes > 10 * 1024 * 1024:  # > 10MB
                color = '#F44336'  # Rojo
            elif obj.size_bytes > 1 * 1024 * 1024:  # > 1MB
                color = '#FF9800'  # Naranja
            else:
                color = '#4CAF50'  # Verde
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, size
            )
        return size
    get_size_display.short_description = 'Tamaño'
    get_size_display.admin_order_field = 'size_bytes'

    def get_phase_link(self, obj):
        """Enlace a la fase."""
        if obj.phase:
            phase_url = reverse('admin:projects_phase_change', args=[obj.phase.pk])
            return format_html('<a href="{}">{}</a>', phase_url, obj.phase.name)
        return format_html('<span style="color: #999;">Sin fase</span>')
    get_phase_link.short_description = 'Fase'
    get_phase_link.admin_order_field = 'phase__name'

    def get_project_link(self, obj):
        """Enlace al proyecto."""
        if obj.phase and obj.phase.project:
            project_url = reverse('admin:projects_project_change', args=[obj.phase.project.pk])
            return format_html('<a href="{}">{}</a>', project_url, obj.phase.project.name)
        return format_html('<span style="color: #999;">Sin proyecto</span>')
    get_project_link.short_description = 'Proyecto'
    get_project_link.admin_order_field = 'phase__project__name'

    def get_uploaded_by_info(self, obj):
        """Información del usuario que subió el archivo."""
        if obj.uploaded_by:
            user_url = reverse('admin:accounts_user_change', args=[obj.uploaded_by.pk])
            return format_html(
                '<a href="{}" style="text-decoration: none;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</a>',
                user_url,
                obj.uploaded_by.get_full_name() or obj.uploaded_by.email,
                obj.uploaded_by.email
            )
        return format_html('<span style="color: #999;">Usuario desconocido</span>')
    get_uploaded_by_info.short_description = 'Subido por'
    get_uploaded_by_info.admin_order_field = 'uploaded_by__first_name'

    def get_download_link(self, obj):
        """Link de descarga del archivo."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button">⬇️ Descargar archivo</a>',
                obj.file.url
            )
        return 'Archivo no disponible'
    get_download_link.short_description = 'Descarga'

    def calculate_storage_usage(self, request, queryset):
        """Calcular uso de almacenamiento de archivos seleccionados."""
        total_size = queryset.aggregate(total=Sum('size_bytes'))['total'] or 0
        total_files = queryset.count()
        
        size_formatted = filesizeformat(total_size)
        
        self.message_user(
            request,
            f"📊 Uso de almacenamiento: {size_formatted} en {total_files} archivo(s) seleccionado(s).",
            messages.INFO
        )
    calculate_storage_usage.short_description = "📊 Calcular uso de almacenamiento"

    def mark_for_review(self, request, queryset):
        """Marcar archivos para revisión."""
        file_count = queryset.count()
        self.message_user(
            request,
            f"🔍 Se marcaron {file_count} archivo(s) para revisión. "
            "Funcionalidad de revisión próximamente.",
            messages.INFO
        )
    mark_for_review.short_description = "🔍 Marcar para revisión"

    # Métodos heredados para compatibilidad
    def filename_display(self, obj):
        return obj.filename

    def extension(self, obj):
        return obj.extension

    def size_h(self, obj):
        return filesizeformat(obj.size_bytes or 0)

