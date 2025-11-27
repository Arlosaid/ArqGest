/**
 * 🔧 Configuración Global del Sistema
 * 
 * Este archivo centraliza todas las configuraciones de límites de archivos.
 * Para cambiar el límite de tamaño de archivo, edita MAX_FILE_SIZE_MB.
 */

// Get settings injected from Django template
const serverConfig = window.SERVER_UPLOAD_CONFIG || {};

window.FILE_UPLOAD_CONFIG = {
    // Tamaño máximo de archivo en MB (Use server config or default)
    MAX_FILE_SIZE_MB: serverConfig.MAX_FILE_SIZE_MB || 1500,              // Límite para desktop/tablet
    MAX_FILE_SIZE_MOBILE_MB: 50,       // Límite para móviles (puedes reducirlo si quieres)
    
    // Storage externo (R2/S3) - cambiar a true para habilitar uploads directos
    ENABLE_STORAGES: false,
    
    // Extensiones permitidas (Use server config or default)
    // Si el servidor envía una lista vacía, usamos la lista por defecto para evitar inconsistencias
    ALLOWED_EXTENSIONS: (serverConfig.ALLOWED_EXTENSIONS && serverConfig.ALLOWED_EXTENSIONS.length > 0) 
        ? serverConfig.ALLOWED_EXTENSIONS 
        : [
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