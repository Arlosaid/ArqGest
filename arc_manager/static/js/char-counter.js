/**
 * Character Counter
 * Muestra contadores de caracteres para campos de texto con límites
 * con feedback visual progresivo según UX best practices
 */

class CharCounter {
    constructor(element) {
        this.input = element;
        this.maxLength = parseInt(this.input.getAttribute('data-max-length')) || 100;
        this.init();
    }

    init() {
        // Crear el elemento contador
        this.counter = this.createCounter();
        
        // Insertar el contador después del input
        this.insertCounter();
        
        // Event listeners
        this.input.addEventListener('input', () => this.updateCounter());
        this.input.addEventListener('focus', () => this.showCounter());
        this.input.addEventListener('blur', () => this.hideCounterIfEmpty());
        
        // Actualización inicial
        this.updateCounter();
    }

    createCounter() {
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.setAttribute('aria-live', 'polite');
        counter.style.opacity = '0';
        return counter;
    }

    insertCounter() {
        // Buscar el contenedor más apropiado
        const formGroup = this.input.closest('.form-group, .mb-3, .field-wrapper');
        
        if (formGroup) {
            formGroup.appendChild(this.counter);
        } else {
            this.input.parentNode.insertBefore(this.counter, this.input.nextSibling);
        }
    }

    updateCounter() {
        const currentLength = this.input.value.length;
        const remaining = this.maxLength - currentLength;
        const percentage = (currentLength / this.maxLength) * 100;
        
        // Actualizar texto
        if (remaining >= 0) {
            this.counter.textContent = `${currentLength} / ${this.maxLength} caracteres`;
        } else {
            this.counter.textContent = `Excedido por ${Math.abs(remaining)} caracteres`;
        }
        
        // Actualizar clases según el porcentaje
        this.counter.className = 'char-counter';
        
        if (percentage >= 100) {
            this.counter.classList.add('char-counter--error');
        } else if (percentage >= 90) {
            this.counter.classList.add('char-counter--warning');
        } else if (percentage >= 75) {
            this.counter.classList.add('char-counter--info');
        } else {
            this.counter.classList.add('char-counter--normal');
        }
        
        // Mostrar si hay contenido
        if (currentLength > 0 || document.activeElement === this.input) {
            this.showCounter();
        }
    }

    showCounter() {
        this.counter.style.opacity = '1';
        this.counter.style.visibility = 'visible';
    }

    hideCounterIfEmpty() {
        if (this.input.value.length === 0) {
            this.counter.style.opacity = '0';
            setTimeout(() => {
                if (this.counter.style.opacity === '0') {
                    this.counter.style.visibility = 'hidden';
                }
            }, 200);
        }
    }
}

/**
 * Inicialización automática de contadores
 */
function initCharCounters() {
    const elements = document.querySelectorAll('[data-char-counter="true"]');
    
    elements.forEach(element => {
        // Evitar inicializar múltiples veces
        if (!element.hasAttribute('data-char-counter-initialized')) {
            new CharCounter(element);
            element.setAttribute('data-char-counter-initialized', 'true');
        }
    });
}

/**
 * Inicializar al cargar el DOM
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCharCounters);
} else {
    initCharCounters();
}

/**
 * Función global para reinicializar contadores (útil para contenido dinámico)
 */
window.reinitCharCounters = initCharCounters;

/**
 * Observador de mutaciones para contadores en contenido dinámico (modales, AJAX, etc.)
 */
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.addedNodes.length) {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    // Buscar inputs con data-char-counter en el nodo agregado
                    const inputs = node.querySelectorAll ? node.querySelectorAll('[data-char-counter="true"]') : [];
                    inputs.forEach(input => {
                        if (!input.hasAttribute('data-char-counter-initialized')) {
                            new CharCounter(input);
                            input.setAttribute('data-char-counter-initialized', 'true');
                        }
                    });
                    
                    // Si el nodo mismo es un input con contador
                    if (node.matches && node.matches('[data-char-counter="true"]')) {
                        if (!node.hasAttribute('data-char-counter-initialized')) {
                            new CharCounter(node);
                            node.setAttribute('data-char-counter-initialized', 'true');
                        }
                    }
                }
            });
        }
    });
});

// Observar el documento completo para contenido dinámico
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Exportar para uso en módulos si es necesario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CharCounter;
}

