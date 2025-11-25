import re

file_path = r'C:\Users\Alonso\Desktop\arc_manager\arc_manager\apps\projects\templates\projects\kanban_board.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar todas las condiciones para hacerlas más explícitas
# Cambiar: {% if is_org_admin or task.assigned_to and task.assigned_to.id == user.id %}
# Por: {% if is_org_admin or task.assigned_to.id|default:0 == user.id %}

old_pattern = r'{% if is_org_admin or task\.assigned_to and task\.assigned_to\.id == user\.id %}'
new_pattern = r'{% if is_org_admin or task.assigned_to.id|default:0 == user.id %}'

content = re.sub(old_pattern, new_pattern, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Archivo modificado correctamente')
print(f'Condiciones de permisos actualizadas para ser más explícitas')
