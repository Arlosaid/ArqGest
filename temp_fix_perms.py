import re

file_path = r'C:\Users\Alonso\Desktop\arc_manager\arc_manager\apps\projects\templates\projects\kanban_board.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón 1: Agregar condición antes de task-status-buttons d-md-none
pattern1 = r'(<!-- Botones de cambio de estado para móvil \(simplificados\) -->)\s*\n(\s+)<div class="task-status-buttons d-md-none">'
replacement1 = r'\1\n\2{% if is_org_admin or task.assigned_to and task.assigned_to.id == user.id %}\n\2<div class="task-status-buttons d-md-none">'
content = re.sub(pattern1, replacement1, content)

# Patrón 2: Agregar endif después del cierre del div de botones de estado, antes de "Botones de acción tradicionales"
pattern2 = r'({% endif %})\s*\n(\s+)</div>\s*\n\s*\n(\s+)<!-- Botones de acción tradicionales -->'
replacement2 = r'\1\n\2</div>\n\2{% endif %}\n\n\3<!-- Botones de acción tradicionales -->'
content = re.sub(pattern2, replacement2, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Archivo modificado correctamente')
print(f'Reemplazos realizados: patrón 1 y patrón 2')
