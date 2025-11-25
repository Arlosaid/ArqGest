import re

# Ruta al archivo
file_path = r'c:\Users\Alonso\Desktop\arc_manager\arc_manager\apps\projects\templates\projects\kanban_board.html'

# Leer el contenido
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar las tarjetas kanban
# Agregar clase condicional: my-task si es del usuario, other-user-task si no lo es
pattern = r'(<div class="kanban-card" data-task-id="{{ task\.id }}" draggable="[^"]*" data-assigned-to-id="{{ task\.assigned_to\.id\|default:0 }}")'
replacement = r'\1 class="{% if is_org_admin or task.assigned_to.id|default:0 == user.id %}my-task{% else %}other-user-task{% endif %}"'

# Nota: Necesitamos modificar para que sea class="kanban-card {% if ... %}"
pattern = r'<div class="kanban-card" data-task-id="{{ task\.id }}"'
replacement = r'<div class="kanban-card {% if is_org_admin or task.assigned_to.id|default:0 == user.id %}my-task{% else %}other-user-task{% endif %}" data-task-id="{{ task.id }}"'

content = re.sub(pattern, replacement, content)

# Guardar los cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Clases de UX agregadas a las tarjetas del kanban')
print('- my-task: Tareas del usuario (destacadas, interactivas)')
print('- other-user-task: Tareas de otros (atenuadas, solo vista)')
