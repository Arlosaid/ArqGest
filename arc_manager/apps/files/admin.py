from django.contrib import admin
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import ProjectFile
from core.structured_logging import log_info, log_error


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
            'PDF': 'PDF', 'DOC': 'DOC', 'DOCX': 'DOCX', 'XLS': 'XLS', 'XLSX': 'XLSX',
            'JPG': 'IMG', 'PNG': 'IMG', 'GIF': 'IMG', 'ZIP': 'ZIP', 'DWG': 'DWG'
        }
        icon = icons.get(obj.ext_upper, 'FILE')
        
        if obj.file:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="font-size: 12px; font-weight: bold; background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">{}</span>'
                '<div>'
                '<strong><a href="{}" target="_blank" style="text-decoration: none; color: #0073aa;">{}</a></strong><br>'
                '<small style="color: #666; background: #f0f0f0; padding: 2px 5px; border-radius: 3px;">{}</small>'
                '</div>'
                '</div>',
                icon, obj.file.url, obj.filename, obj.ext_upper
            )
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<span style="font-size: 12px; font-weight: bold; color: #999;">ERR</span>'
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
                '<div style="color: #0073aa; font-weight: bold;">ORG: {}</div>'
                '<div style="color: #666; margin-left: 10px;">PROJ: {}</div>'
                '<div style="color: #999; margin-left: 20px;">FASE: {}</div>'
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
                '<span title="Subido por {}" style="color: #666;">USER</span>',
                obj.uploaded_by.get_full_name() or obj.uploaded_by.email
            ))
        
        return format_html(''.join(actions))
    get_actions.short_description = 'Acciones'
    
    def save_model(self, request, obj, form, change):
        """Hook para guardar el modelo con logging estructurado."""
        try:
            if change:
                # Es una actualización - capturar cambios
                changes = []
                
                tracked_fields = {
                    'phase': 'Fase',
                    'file': 'Archivo'
                }
                
                try:
                    original = ProjectFile.objects.get(pk=obj.pk)
                    
                    for field_name, field_label in tracked_fields.items():
                        old_value = getattr(original, field_name)
                        new_value = getattr(obj, field_name)
                        
                        if old_value != new_value:
                            # Formatear valores para logging
                            if field_name == 'phase':
                                old_val = f"{old_value.name} (Proyecto: {old_value.project.name})" if old_value else 'Sin fase'
                                new_val = f"{new_value.name} (Proyecto: {new_value.project.name})" if new_value else 'Sin fase'
                            elif field_name == 'file':
                                old_val = str(old_value.name) if old_value else 'Sin archivo'
                                new_val = str(new_value.name) if new_value else 'Sin archivo'
                            else:
                                old_val = str(old_value) if old_value else ''
                                new_val = str(new_value) if new_value else ''
                            
                            changes.append({
                                'field': field_name,
                                'field_label': field_label,
                                'old': old_val,
                                'new': new_val
                            })
                except ProjectFile.DoesNotExist:
                    change = False
            
            # Guardar el objeto
            super().save_model(request, obj, form, change)
            
            # Logging estructurado
            if change and changes:
                log_info(
                    event='FILE_UPDATED',
                    message=f"Archivo '{obj.filename}' actualizado con {len(changes)} cambio(s)",
                    logger_name='apps.files',
                    file_id=obj.id,
                    filename=obj.filename,
                    file_extension=obj.ext_upper,
                    file_size_bytes=obj.size_bytes,
                    phase_id=obj.phase.id if obj.phase else None,
                    phase_name=obj.phase.name if obj.phase else 'Sin fase',
                    project_id=obj.phase.project.id if obj.phase and obj.phase.project else None,
                    project_name=obj.phase.project.name if obj.phase and obj.phase.project else 'Sin proyecto',
                    changes=changes,
                    updated_by=request.user.email if request.user else 'Sistema'
                )
                
                # Mensaje para el admin
                changes_text = ', '.join([f"{c['field_label']}" for c in changes])
                messages.success(
                    request,
                    f"Archivo '{obj.filename}' actualizado exitosamente. Cambios: {changes_text}"
                )
            elif not change:
                # Creación de archivo
                log_info(
                    event='FILE_UPLOADED',
                    message=f"Archivo '{obj.filename}' subido exitosamente",
                    logger_name='apps.files',
                    file_id=obj.id,
                    filename=obj.filename,
                    file_extension=obj.ext_upper,
                    file_size_bytes=obj.size_bytes,
                    phase_id=obj.phase.id if obj.phase else None,
                    phase_name=obj.phase.name if obj.phase else 'Sin fase',
                    project_id=obj.phase.project.id if obj.phase and obj.phase.project else None,
                    project_name=obj.phase.project.name if obj.phase and obj.phase.project else 'Sin proyecto',
                    uploaded_by=request.user.email if request.user else 'Sistema'
                )
        
        except Exception as e:
            log_error(
                event='FILE_SAVE_FAILED',
                error_code='FILE001',
                error_message=str(e),
                logger_name='apps.files',
                filename=getattr(obj, 'filename', 'Desconocido'),
                action='create' if not change else 'update',
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            messages.error(
                request,
                f"Error al {'subir' if not change else 'actualizar'} el archivo: {str(e)}"
            )
            
            raise
    
    def calculate_storage(self, request, queryset):
        """Calcular uso de almacenamiento con manejo de errores."""
        try:
            total_size = queryset.aggregate(total=Sum('size_bytes'))['total'] or 0
            total_files = queryset.count()
            
            # Estadísticas por organización
            orgs = {}
            for file_obj in queryset.select_related('phase__project__organization'):
                try:
                    if file_obj.phase and file_obj.phase.project and file_obj.phase.project.organization:
                        org_name = file_obj.phase.project.organization.name
                        if org_name not in orgs:
                            orgs[org_name] = {'size': 0, 'count': 0}
                        orgs[org_name]['size'] += file_obj.size_bytes or 0
                        orgs[org_name]['count'] += 1
                except Exception as e:
                    # Log error pero continúa procesando
                    log_error(
                        event='STORAGE_CALCULATION_FILE_ERROR',
                        error_code='FILE_STORAGE_001',
                        error_message=f"Error procesando archivo {file_obj.id}: {str(e)}",
                        logger_name='apps.files',
                        file_id=file_obj.id,
                        performed_by=request.user.email if request.user else 'Sistema'
                    )
            
            message = f"RESUMEN DE ALMACENAMIENTO\n"
            message += f"Total: {filesizeformat(total_size)} en {total_files} archivos\n\n"
            
            if orgs:
                message += "Por organización:\n"
                for org_name, data in sorted(orgs.items()):
                    message += f"• {org_name}: {filesizeformat(data['size'])} ({data['count']} archivos)\n"
            
            # Log de la operación
            log_info(
                event='STORAGE_CALCULATED',
                message=f"Cálculo de almacenamiento completado: {filesizeformat(total_size)} en {total_files} archivos",
                logger_name='apps.files',
                total_size_bytes=total_size,
                total_files=total_files,
                organizations_count=len(orgs),
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(request, message, messages.INFO)
            
        except Exception as e:
            log_error(
                event='STORAGE_CALCULATION_FAILED',
                error_code='FILE_STORAGE_002',
                error_message=str(e),
                logger_name='apps.files',
                file_count=queryset.count(),
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al calcular almacenamiento: {str(e)}",
                messages.ERROR
            )
    calculate_storage.short_description = "Calcular almacenamiento"
    
    def export_file_list(self, request, queryset):
        """Exportar lista de archivos seleccionados con manejo de errores."""
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        try:
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
            
            exported_count = 0
            error_count = 0
            
            for file_obj in queryset.select_related('phase__project__organization', 'uploaded_by'):
                try:
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
                    exported_count += 1
                    
                except Exception as e:
                    error_count += 1
                    # Log error pero continúa exportando
                    log_error(
                        event='FILE_EXPORT_ROW_ERROR',
                        error_code='FILE_EXPORT_001',
                        error_message=f"Error exportando archivo {file_obj.id}: {str(e)}",
                        logger_name='apps.files',
                        file_id=file_obj.id,
                        filename=getattr(file_obj, 'filename', 'Desconocido'),
                        performed_by=request.user.email if request.user else 'Sistema'
                    )
            
            # Log de la operación exitosa
            log_info(
                event='FILES_EXPORTED',
                message=f"Exportación CSV completada: {exported_count} archivos exportados",
                logger_name='apps.files',
                exported_count=exported_count,
                error_count=error_count,
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            # Mensaje de confirmación
            if error_count > 0:
                self.message_user(
                    request, 
                    f"Se exportaron {exported_count} archivo(s). {error_count} tuvieron errores y se omitieron.",
                    messages.WARNING
                )
            else:
                self.message_user(
                    request, 
                    f"Se exportaron {exported_count} archivo{'s' if exported_count != 1 else ''} exitosamente",
                    messages.SUCCESS
                )
            
            return response
            
        except Exception as e:
            log_error(
                event='FILE_EXPORT_FAILED',
                error_code='FILE_EXPORT_002',
                error_message=str(e),
                logger_name='apps.files',
                file_count=queryset.count(),
                performed_by=request.user.email if request.user else 'Sistema'
            )
            
            self.message_user(
                request,
                f"Error al exportar archivos: {str(e)}",
                messages.ERROR
            )
            
            # Retornar None hace que Django maneje el error apropiadamente
            return None
    export_file_list.short_description = "Exportar lista (.csv)"