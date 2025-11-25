import re

# Ruta al archivo
file_path = r'c:\Users\Alonso\Desktop\arc_manager\arc_manager\apps\projects\templates\projects\kanban_board.html'

# Leer el contenido
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar las comillas escapadas innecesariamente
content = content.replace("onclick=\"openTaskModal(\\'edit\\', {{ task.pk }})\"", 
                         "onclick=\"openTaskModal('edit', {{ task.pk }})\"")

# Guardar los cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Formato de botones corregido')
