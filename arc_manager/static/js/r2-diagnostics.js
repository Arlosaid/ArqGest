/**
 * Herramienta de diagnóstico para uploads directos a R2
 * Ejecuta esto en la consola del navegador para diagnosticar problemas de CORS
 */

const R2Diagnostics = {
    /**
     * Test de conectividad básica a R2
     */
    async testConnectivity(presignedUrl) {
        console.log('🔍 Iniciando diagnóstico de R2...\n');
        
        try {
            // Test 1: Preflight request (OPTIONS)
            console.log('Test 1: Verificando CORS preflight...');
            const optionsResponse = await fetch(presignedUrl, {
                method: 'OPTIONS',
                headers: {
                    'Access-Control-Request-Method': 'PUT',
                    'Access-Control-Request-Headers': 'content-type',
                }
            });
            
            console.log('✅ Preflight OK');
            console.log('Headers permitidos:', optionsResponse.headers.get('Access-Control-Allow-Headers'));
            console.log('Métodos permitidos:', optionsResponse.headers.get('Access-Control-Allow-Methods'));
            console.log('Origen permitido:', optionsResponse.headers.get('Access-Control-Allow-Origin'));
            
        } catch (error) {
            console.error('❌ Preflight falló:', error.message);
            console.error('💡 Esto indica que CORS no está configurado en R2');
            return false;
        }
        
        try {
            // Test 2: Upload de prueba
            console.log('\nTest 2: Upload de archivo de prueba...');
            const testBlob = new Blob(['test content'], { type: 'text/plain' });
            
            const uploadResponse = await fetch(presignedUrl, {
                method: 'PUT',
                body: testBlob,
                headers: {
                    'Content-Type': 'text/plain',
                }
            });
            
            if (uploadResponse.ok) {
                console.log('✅ Upload de prueba exitoso');
                console.log('Status:', uploadResponse.status);
                console.log('ETag:', uploadResponse.headers.get('ETag'));
                return true;
            } else {
                console.error('❌ Upload de prueba falló:', uploadResponse.status, uploadResponse.statusText);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Upload de prueba falló:', error.message);
            console.error('💡 Verifica la configuración CORS en R2');
            return false;
        }
    },
    
    /**
     * Obtener una URL presignada de prueba
     */
    async getTestPresignedUrl(projectId, phaseId) {
        try {
            const response = await fetch(`/projects/${projectId}/phases/${phaseId}/files/presigned-upload/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({
                    filename: 'test.txt',
                    content_type: 'text/plain',
                    file_size: 100
                })
            });
            
            if (!response.ok) {
                throw new Error('Error obteniendo URL presignada');
            }
            
            const data = await response.json();
            return data.url;
            
        } catch (error) {
            console.error('❌ Error obteniendo URL presignada:', error);
            return null;
        }
    },
    
    /**
     * Diagnóstico completo
     */
    async runFullDiagnostics(projectId, phaseId) {
        console.log('🔍 DIAGNÓSTICO COMPLETO DE R2\n');
        console.log('═══════════════════════════════════════\n');
        
        // Paso 1: Obtener URL presignada
        console.log('Paso 1: Obteniendo URL presignada...');
        const presignedUrl = await this.getTestPresignedUrl(projectId, phaseId);
        
        if (!presignedUrl) {
            console.error('❌ No se pudo obtener URL presignada');
            console.log('\n💡 SOLUCIÓN:');
            console.log('1. Verifica que ENABLE_STORAGES=true en variables de entorno');
            console.log('2. Verifica credenciales de R2 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)');
            console.log('3. Verifica AWS_S3_ENDPOINT_URL y AWS_STORAGE_BUCKET_NAME');
            return;
        }
        
        console.log('✅ URL presignada obtenida');
        console.log('URL:', presignedUrl);
        
        // Paso 2: Test de conectividad
        console.log('\nPaso 2: Probando conectividad y CORS...');
        const success = await this.testConnectivity(presignedUrl);
        
        // Resultados
        console.log('\n═══════════════════════════════════════');
        if (success) {
            console.log('✅ DIAGNÓSTICO EXITOSO');
            console.log('El sistema está configurado correctamente para uploads directos a R2');
        } else {
            console.log('❌ DIAGNÓSTICO FALLÓ');
            console.log('\n📖 PASOS PARA SOLUCIONAR:');
            console.log('1. Ve a Cloudflare Dashboard > R2 > Tu Bucket > Settings');
            console.log('2. Configura CORS Policy (ver docs/R2_CORS_CONFIGURATION.md)');
            console.log('3. Asegúrate de incluir tu dominio en AllowedOrigins');
            console.log('4. Asegúrate de incluir PUT en AllowedMethods');
            console.log('5. Espera 1-2 minutos y vuelve a probar');
        }
        console.log('═══════════════════════════════════════\n');
    },
    
    /**
     * Mostrar información del entorno
     */
    showEnvironmentInfo() {
        console.log('ℹ️ INFORMACIÓN DEL ENTORNO\n');
        console.log('Origen actual:', window.location.origin);
        console.log('Protocolo:', window.location.protocol);
        console.log('User Agent:', navigator.userAgent);
        console.log('\n');
    }
};

// Exportar para uso en consola
window.R2Diagnostics = R2Diagnostics;

console.log('🔧 Herramientas de diagnóstico R2 cargadas');
console.log('📖 Uso:');
console.log('  R2Diagnostics.showEnvironmentInfo()');
console.log('  R2Diagnostics.runFullDiagnostics(projectId, phaseId)');
console.log('  Ejemplo: R2Diagnostics.runFullDiagnostics(16, 26)');
