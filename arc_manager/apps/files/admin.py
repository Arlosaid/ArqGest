from django.contrib import admin
from django.db.models import Sum
from django.template.defaultfilters import filesizeformat
from .models import ProjectFile


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ("filename_display", "extension", "size_h", "phase", "uploaded_by", "uploaded_at")
    list_filter = ("ext_upper", "uploaded_at")
    search_fields = ("file", "uploaded_by__first_name", "uploaded_by__last_name", "phase__project__name")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)

    def filename_display(self, obj):
        return obj.filename

    def extension(self, obj):
        return obj.extension

    def size_h(self, obj):
        return filesizeformat(obj.size_bytes or 0)

