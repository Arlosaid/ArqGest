// ===== ORGANIZATION MANAGEMENT - JavaScript Optimizado ===== //

// ===== MONITOR DE RENDIMIENTO (OPCIONAL - SOLO DESARROLLO) ===== //
const PERFORMANCE_MONITORING = false; // Cambiar a true para monitorear

if (PERFORMANCE_MONITORING && window.performance) {
    // Performance monitoring deshabilitado en producción
}

document.addEventListener('DOMContentLoaded', function() {
    // ===== FUNCIONES DE INICIALIZACIÓN ===== //
    initializeAnimations();
    initializeInteractions();
    initializeCounters();
});

// ===== ANIMACIONES DE ENTRADA ===== //
function initializeAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observar elementos con animaciones
    document.querySelectorAll('.info-card, .action-card').forEach(card => {
        card.style.animationPlayState = 'paused';
        observer.observe(card);
    });
}

// ===== INTERACCIONES MEJORADAS ===== //
function initializeInteractions() {
    // Efectos hover optimizados para tarjetas
    document.querySelectorAll('.info-card, .action-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Efectos para estadísticas
    document.querySelectorAll('.stat-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            const value = this.querySelector('.stat-value');
            if (value) {
                value.style.transform = 'scale(1.05)';
                value.style.color = 'var(--arc-color-primary)';
            }
        });

        item.addEventListener('mouseleave', function() {
            const value = this.querySelector('.stat-value');
            if (value) {
                value.style.transform = 'scale(1)';
                value.style.color = 'var(--arc-text-primary)';
            }
        });
    });

    // Ripple effect para botones
    document.querySelectorAll('.btn-primary-improved, .btn-secondary-trial').forEach(button => {
        button.addEventListener('click', createRippleEffect);
    });
}

// ===== EFECTO RIPPLE ===== //
function createRippleEffect(e) {
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s linear;
        left: ${x}px;
        top: ${y}px;
        width: ${size}px;
        height: ${size}px;
        pointer-events: none;
    `;
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to { transform: scale(4); opacity: 0; }
        }
    `;
    
    if (!document.querySelector('style[data-ripple]')) {
        style.setAttribute('data-ripple', 'true');
        document.head.appendChild(style);
    }
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
}

// ===== ANIMACIÓN DE CONTADORES ===== //
function initializeCounters() {
    // Solo animar elementos con la clase específica 'animate-counter'
    const counterElements = document.querySelectorAll('.trial-days');
    
    const animateCounter = (element) => {
        const originalText = element.textContent.trim();
        
        // Solo animar números puros (días de trial)
        const target = parseInt(originalText);
        if (isNaN(target) || target <= 0) return;
        
        const increment = target / 30; // Más suave
        let current = 0;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            element.textContent = Math.floor(current);
        }, 30);
    };

    // Observar cuando los contadores entren en vista
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counterElements.forEach(counter => {
        // Solo observar elementos que contengan números puros
        const text = counter.textContent.trim();
        if (!isNaN(parseInt(text))) {
            counterObserver.observe(counter);
        }
    });
}

// ===== OPTIMIZACIONES DE RENDIMIENTO ===== //

// Throttle para eventos de scroll y resize
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Preload de animaciones críticas para mejor rendimiento
function preloadAnimations() {
    const style = document.createElement('style');
    style.textContent = `
        .preload-animations * {
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-duration: 0s !important;
        }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => {
        document.body.classList.remove('preload-animations');
        style.remove();
    }, 100);
}

// Aplicar preload si es necesario
if (document.readyState === 'loading') {
    document.body.classList.add('preload-animations');
    document.addEventListener('DOMContentLoaded', preloadAnimations);
}

// ===== ACCESIBILIDAD MEJORADA ===== //
document.addEventListener('keydown', function(e) {
    // Mejorar navegación por teclado
    if (e.key === 'Tab') {
        const focusableElements = document.querySelectorAll(
            'a[href], button, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements.forEach(el => {
            el.addEventListener('focus', function() {
                this.style.outline = '2px solid var(--arc-color-primary)';
                this.style.outlineOffset = '2px';
            });
            
            el.addEventListener('blur', function() {
                this.style.outline = '';
                this.style.outlineOffset = '';
            });
        });
    }
});

// ===== REDUCIR MOVIMIENTO PARA USUARIOS CON PREFERENCIAS ===== //
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const style = document.createElement('style');
    style.textContent = `
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    `;
    document.head.appendChild(style);
} 