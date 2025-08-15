/**
 * DEMO DEL SISTEMA DE NOTIFICACIONES
 * Archivo temporal para probar las notificaciones - se puede eliminar después
 */

// Función para probar todas las notificaciones
function testNotifications() {
    if (!window.notifications) {
        console.error('Sistema de notificaciones no disponible');
        return;
    }

    // Notificación de éxito
    setTimeout(() => {
        window.notifications.success('¡Operación completada exitosamente!', {
            title: 'Éxito',
            duration: 4000
        });
    }, 500);

    // Notificación de información
    setTimeout(() => {
        window.notifications.info('Nueva actualización disponible en el sistema', {
            title: 'Información',
            duration: 5000
        });
    }, 1500);

    // Notificación de advertencia
    setTimeout(() => {
        window.notifications.warning('Tu suscripción expirará en 7 días', {
            title: 'Advertencia',
            duration: 6000
        });
    }, 2500);

    // Notificación de error
    setTimeout(() => {
        window.notifications.error('No se pudo conectar con el servidor', {
            title: 'Error',
            duration: 7000
        });
    }, 3500);

    // Notificación persistente
    setTimeout(() => {
        window.notifications.info('Esta notificación no se cierra automáticamente', {
            title: 'Persistente',
            persistent: true
        });
    }, 4500);
}

// Función para probar duplicados
function testDuplicates() {
    if (!window.notifications) {
        console.error('Sistema de notificaciones no disponible');
        return;
    }
    
    // Intentar crear duplicados
    window.notifications.success('Tarea creada exitosamente');
    setTimeout(() => {
        window.notifications.success('Tarea creada correctamente'); // Similar, debería ser bloqueada
    }, 500);
    
    setTimeout(() => {
        window.notifications.success('Usuario eliminado correctamente');
    }, 1000);
    
    setTimeout(() => {
        window.notifications.success('Usuario eliminado exitosamente'); // Similar, debería ser bloqueada
    }, 1500);
}

// Función para probar notificaciones de suscripción
function testSubscriptionNotifications() {
    if (!window.notifications) {
        console.error('Sistema de notificaciones no disponible');
        return;
    }
    
    // Simular diferentes escenarios
    setTimeout(() => {
        window.notifications.warning('Tu suscripción expira en 3 días. ¡Renueva ahora para evitar interrupciones!', {
            title: 'Renovación Necesaria',
            duration: 8000,
            onClick: () => console.log('Redirigir a renovación')
        });
    }, 500);
    
    setTimeout(() => {
        window.notifications.warning('Solo puedes agregar 1 usuario más. Considera actualizar tu plan.', {
            title: 'Límite de Usuarios',
            duration: 7000,
            onClick: () => console.log('Redirigir a upgrade')
        });
    }, 2000);
    
    setTimeout(() => {
        window.notifications.error('Tu suscripción ha expirado. Renueva inmediatamente para evitar la suspensión.', {
            title: 'Suscripción Expirada',
            persistent: true,
            onClick: () => console.log('Redirigir a renovación urgente')
        });
    }, 4000);
}

// Función para limpiar todas las notificaciones
function clearAllNotifications() {
    if (window.notifications) {
        window.notifications.clear();
    }
}

// Agregar botones de prueba al DOM cuando esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Solo agregar en desarrollo
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const testContainer = document.createElement('div');
        testContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 10001;
            display: flex;
            gap: 10px;
            flex-direction: column;
        `;

        const testButton = document.createElement('button');
        testButton.textContent = 'Probar Notificaciones';
        testButton.style.cssText = `
            padding: 8px 16px;
            background: #4285f4;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        testButton.onclick = testNotifications;

        const duplicatesButton = document.createElement('button');
        duplicatesButton.textContent = 'Probar Duplicados';
        duplicatesButton.style.cssText = `
            padding: 8px 16px;
            background: #f59e0b;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        duplicatesButton.onclick = testDuplicates;

        const subscriptionButton = document.createElement('button');
        subscriptionButton.textContent = 'Notif. Suscripción';
        subscriptionButton.style.cssText = `
            padding: 8px 16px;
            background: #8b5cf6;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        subscriptionButton.onclick = testSubscriptionNotifications;

        const historyButton = document.createElement('button');
        historyButton.textContent = 'Limpiar Historial';
        historyButton.style.cssText = `
            padding: 8px 16px;
            background: #6b7280;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        historyButton.onclick = clearNotificationHistory;

        const clearButton = document.createElement('button');
        clearButton.textContent = 'Limpiar Todo';
        clearButton.style.cssText = `
            padding: 8px 16px;
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        clearButton.onclick = clearAllNotifications;

        testContainer.appendChild(testButton);
        testContainer.appendChild(duplicatesButton);
        testContainer.appendChild(subscriptionButton);
        testContainer.appendChild(historyButton);
        testContainer.appendChild(clearButton);
        document.body.appendChild(testContainer);
    }
});

// Exponer funciones globalmente para consola
window.testNotifications = testNotifications;
window.testDuplicates = testDuplicates;
window.testSubscriptionNotifications = testSubscriptionNotifications;
window.clearAllNotifications = clearAllNotifications;
