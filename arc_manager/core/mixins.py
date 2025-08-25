from typing import Optional


class PageSizeMixin:
	"""Mixin para habilitar paginación configurable por query param en ListView.

	- Usa `?page_size=` con valores permitidos para cambiar tamaño de página.
	- Expone datos útiles de paginación en el contexto.
	"""

	# Tamaño por defecto y límites aceptados
	paginate_by: int = 12
	allowed_page_sizes = (6, 12, 24, 48, 100)
	max_page_size: int = 100

	def get_paginate_by(self, queryset) -> Optional[int]:  # type: ignore[override]
		try:
			page_size_param = self.request.GET.get('page_size')
			if page_size_param is None:
				return getattr(self, 'paginate_by', None)
			size = int(page_size_param)
			if size in self.allowed_page_sizes:
				return size
			# Cap por seguridad si viene algo fuera de catálogo
			return min(max(size, 1), self.max_page_size)
		except Exception:
			return getattr(self, 'paginate_by', None)

	def get_context_data(self, **kwargs):  # type: ignore[override]
		context = super().get_context_data(**kwargs)
		page_obj = context.get('page_obj')
		if page_obj is not None:
			context.setdefault('page_size', page_obj.paginator.per_page)
			context.setdefault('total_count', page_obj.paginator.count)
			context.setdefault('page_number', page_obj.number)
			context.setdefault('num_pages', page_obj.paginator.num_pages)
			context.setdefault('has_next', page_obj.has_next())
			context.setdefault('has_previous', page_obj.has_previous())
		return context


# Middleware simple de performance (latencia de request)
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time, logging
        logger = logging.getLogger('apps')
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if elapsed_ms > 2000:
            logger.warning(f"Slow request {request.path} took {elapsed_ms:.1f}ms")
        return response


