import re

# Ruta al archivo
file_path = r'c:\Users\Alonso\Desktop\arc_manager\arc_manager\apps\projects\templates\projects\kanban_board.html'

# Leer el contenido
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Cambiar draggable para permitir drag&drop a admins O usuarios asignados
# Agregar data-assigned-to-id a cada tarjeta
pattern1 = r'(<div class="kanban-card" data-task-id="{{ task\.id }}" draggable="){% if is_org_admin %}true{% else %}false{% endif %}(")'
replacement1 = r'\1{% if is_org_admin or task.assigned_to.id|default:0 == user.id %}true{% else %}false{% endif %}\2 data-assigned-to-id="{{ task.assigned_to.id|default:0 }}"'
content = re.sub(pattern1, replacement1, content)

# 2. Cambiar condición de botón editar para SOLO admins
pattern2 = r'{% if is_org_admin or task\.assigned_to\.id\|default:0 == user\.id %}\s*<button class="btn btn-outline-primary" onclick="openTaskModal\(\'edit\', {{ task\.pk }}\)"'
replacement2 = r'{% if is_org_admin %}\n                        <button class="btn btn-outline-primary" onclick="openTaskModal(\'edit\', {{ task.pk }})"'
content = re.sub(pattern2, replacement2, content)

# Guardar los cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Archivo actualizado correctamente')
print('- Drag&drop permitido para admins y usuarios asignados')
print('- Botón editar solo para admins')
print('- Agregado data-assigned-to-id a las tarjetas')
