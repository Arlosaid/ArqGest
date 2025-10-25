/**
 * 🔧 Configuración Global del Sistema
 * 
 * Este archivo centraliza todas las configuraciones de límites de archivos.
 * Para cambiar el límite de tamaño de archivo, edita MAX_FILE_SIZE_MB.
 */

window.FILE_UPLOAD_CONFIG = {
    // Tamaño máximo de archivo en MB
    MAX_FILE_SIZE_MB: 1500,              // Límite para desktop/tablet
    MAX_FILE_SIZE_MOBILE_MB: 50,       // Límite para móviles (puedes reducirlo si quieres)
    
    // Extensiones permitidas
    ALLOWED_EXTENSIONS: [
        'PDF', 'JPG', 'JPEG', 'PNG', 'GIF', 'TIFF', 
        'DWG', 'DXF', 'RVT', 'SKP', 
        'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 
        'ZIP', 'RAR', 'TXT', 'MD'
    ],
    
    // Configuración de chunks para uploads grandes
    CHUNK_SIZE_MB: 5,
    MAX_RETRIES: 3,
    
    // Configuración para móviles
    MOBILE_CHUNK_SIZE_MB: 1,
    MOBILE_MAX_CONCURRENT: 1,
    DESKTOP_MAX_CONCURRENT: 2,
};