/**
 * =============================================================================
 * MONALYTICS - JAVASCRIPT PRINCIPAL
 * =============================================================================
 * Autor: Antonio Siqueira - Monalisa Research
 * Descrição: Scripts para funcionalidades interativas do Monalytics
 * =============================================================================
 */

// =========================== VARIÁVEIS GLOBAIS ===========================
const header = document.getElementById('header');
const menuToggle = document.getElementById('menuToggle');
const navMenu = document.getElementById('navMenu');
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('section[id]');

// =========================== MENU MOBILE TOGGLE ===========================
/**
 * Toggle do menu mobile
 * Adiciona/remove classe 'active' no menu
 */
if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        menuToggle.classList.toggle('active');
        
        // Animação do botão hamburger
        const spans = menuToggle.querySelectorAll('span');
        spans.forEach((span, index) => {
            if (menuToggle.classList.contains('active')) {
                if (index === 0) span.style.transform = 'rotate(45deg) translate(5px, 5px)';
                if (index === 1) span.style.opacity = '0';
                if (index === 2) span.style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                span.style.transform = '';
                span.style.opacity = '';
            }
        });
        
        // Previne scroll do body quando menu está aberto
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });
    
    // Fecha o menu ao clicar em um link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
                
                // Reset animação hamburger
                const spans = menuToggle.querySelectorAll('span');
                spans.forEach(span => {
                    span.style.transform = '';
                    span.style.opacity = '';
                });
            }
        });
    });
    
    // Fecha menu ao clicar fora
    document.addEventListener('click', (e) => {
        if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
            if (navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
                
                const spans = menuToggle.querySelectorAll('span');
                spans.forEach(span => {
                    span.style.transform = '';
                    span.style.opacity = '';
                });
            }
        }
    });
}

// =========================== HEADER SCROLL EFFECT ===========================
/**
 * Adiciona classe 'scrolled' ao header quando usuário rola a página
 * Melhora a visibilidade do header
 */
function handleHeaderScroll() {
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
}

window.addEventListener('scroll', handleHeaderScroll);

// =========================== ACTIVE MENU LINK ===========================
/**
 * Atualiza o link ativo do menu baseado na seção visível
 * Usa Intersection Observer para melhor performance
 */
function updateActiveLink() {
    const scrollPosition = window.scrollY + 100;
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        const sectionId = section.getAttribute('id');
        
        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${sectionId}`) {
                    link.classList.add('active');
                }
            });
        }
    });
}

window.addEventListener('scroll', updateActiveLink);

// =========================== SMOOTH SCROLL ===========================
/**
 * Scroll suave para links âncora
 * Melhora a experiência de navegação
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            const headerHeight = header.offsetHeight;
            const targetPosition = targetElement.offsetTop - headerHeight;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// =========================== SCROLL ANIMATIONS ===========================
/**
 * Intersection Observer para animações ao scroll
 * Elementos aparecem quando entram no viewport
 */
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observa elementos com animação
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.stat-card, .feature-item');
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// =========================== STATS COUNTER ANIMATION ===========================
/**
 * Animação de contagem para números estatísticos
 * Ativa quando elemento entra no viewport
 */
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Observa números para animar
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            const statNumber = entry.target.querySelector('.stat-number');
            if (statNumber) {
                const text = statNumber.textContent;
                const number = parseInt(text.replace(/\D/g, ''));
                
                if (!isNaN(number)) {
                    entry.target.classList.add('counted');
                    statNumber.textContent = '0';
                    setTimeout(() => {
                        animateCounter(statNumber, number);
                    }, 200);
                }
            }
        }
    });
}, { threshold: 0.5 });

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.stat-card').forEach(card => {
        statsObserver.observe(card);
    });
});

// =========================== RESIZE HANDLER ===========================
/**
 * Gerencia mudanças no tamanho da janela
 * Fecha menu mobile se viewport aumentar
 */
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (window.innerWidth > 768 && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            menuToggle.classList.remove('active');
            document.body.style.overflow = '';
            
            // Reset animação hamburger
            const spans = menuToggle.querySelectorAll('span');
            spans.forEach(span => {
                span.style.transform = '';
                span.style.opacity = '';
            });
        }
    }, 250);
});

// =========================== PERFORMANCE OPTIMIZATION ===========================
/**
 * Lazy loading para imagens
 * Carrega imagens apenas quando necessário
 */
if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.src = img.dataset.src;
    });
} else {
    // Fallback para navegadores antigos
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// =========================== CONSOLE INFO ===========================
/**
 * Informações do desenvolvedor no console
 */
console.log(
    '%c🚀 Monalytics - Monalisa Research',
    'color: #0066cc; font-size: 20px; font-weight: bold;'
);
console.log(
    '%c💡 Desenvolvido por Antonio Siqueira',
    'color: #00b4d8; font-size: 14px;'
);
console.log(
    '%c📊 Análise Quantitativa Avançada',
    'color: #666; font-size: 12px;'
);

// =========================== ERROR HANDLING ===========================
/**
 * Captura erros globais e loga para debug
 */
window.addEventListener('error', (event) => {
    console.error('❌ Erro capturado:', {
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        error: event.error
    });
});

// =========================== PAGE LOAD COMPLETE ===========================
/**
 * Executado quando a página termina de carregar
 */
window.addEventListener('load', () => {
    console.log('✅ Monalytics carregado com sucesso!');
    
    // Remove loader se existir
    const loader = document.querySelector('.loader');
    if (loader) {
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 300);
    }
    
    // Inicializa active link
    updateActiveLink();
});

// =========================== EXPORT PARA MÓDULOS (FUTURO) ===========================
// Caso precise usar como módulo no futuro
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        handleHeaderScroll,
        updateActiveLink,
        animateCounter
    };
}

/**
 * =============================================================================
 * MONALYTICS - CARROSSEL DE DESTAQUES DO MERCADO
 * =============================================================================
 * Autor: Antonio Siqueira - Monalisa Research
 * Descrição: Carrossel responsivo com dados do IBOVESPA, Indicadores e Notícias
 * =============================================================================
 */

// =========================== VARIÁVEIS GLOBAIS ===========================
const GITHUB_API_BASE = 'https://api.github.com/repos/Antoniosiqueiracnpi-t/Projeto_Monalytics/contents';
const GITHUB_BRANCHES = ['master', 'main'];

const DATA_PATHS = {
    bolsa: 'balancos/IBOV/monitor_diario.json',
    indicadores: 'balancos/INDICADORES/indicadores_economicos.json',
    noticias: 'balancos/feed_noticias.json'
};

let currentSlide = 0;
const totalSlides = 3;
let autoPlayInterval = null;
const AUTO_PLAY_DELAY = 8000; // 8 segundos

// =========================== CAROUSEL NAVIGATION ===========================

/**
 * Inicializa o carrossel e seus controles
 */
function initCarousel() {
    const prevBtn = document.getElementById('prevSlide');
    const nextBtn = document.getElementById('nextSlide');
    const indicators = document.querySelectorAll('.indicator');
    
    // Botões de navegação
    if (prevBtn) prevBtn.addEventListener('click', () => navigateSlide('prev'));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateSlide('next'));
    
    // Indicadores
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => goToSlide(index));
    });
    
    // Suporte a touch/swipe em mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    const carouselContainer = document.querySelector('.carousel-container');
    
    if (carouselContainer) {
        carouselContainer.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        carouselContainer.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });
    }
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                navigateSlide('next');
            } else {
                navigateSlide('prev');
            }
        }
    }
    
    // Iniciar auto-play
    startAutoPlay();
    
    // Pausar auto-play ao interagir
    carouselContainer?.addEventListener('mouseenter', stopAutoPlay);
    carouselContainer?.addEventListener('mouseleave', startAutoPlay);
}

/**
 * Navega para o próximo/anterior slide
 */
function navigateSlide(direction) {
    if (direction === 'next') {
        currentSlide = (currentSlide + 1) % totalSlides;
    } else {
        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    }
    
    updateCarousel();
    resetAutoPlay();
}

/**
 * Vai diretamente para um slide específico
 */
function goToSlide(index) {
    currentSlide = index;
    updateCarousel();
    resetAutoPlay();
}

/**
 * Atualiza a posição do carrossel
 */
function updateCarousel() {
    const track = document.querySelector('.carousel-track');
    const slides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.indicator');
    
    if (track) {
        track.style.transform = `translateX(-${currentSlide * 100}%)`;
    }
    
    // Atualiza classes active
    slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === currentSlide);
    });
    
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlide);
    });
}

/**
 * Inicia auto-play do carrossel
 */
function startAutoPlay() {
    stopAutoPlay();
    autoPlayInterval = setInterval(() => {
        navigateSlide('next');
    }, AUTO_PLAY_DELAY);
}

/**
 * Para o auto-play
 */
function stopAutoPlay() {
    if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
        autoPlayInterval = null;
    }
}

/**
 * Reseta o auto-play (para e inicia novamente)
 */
function resetAutoPlay() {
    startAutoPlay();
}

// =========================== DATA LOADING ===========================

/**
 * Carrega todos os dados
 */
async function loadAllData() {
    await Promise.all([
        loadBolsaData(),
        loadIndicadoresData(),
        loadNoticiasData()
    ]);
}

// ================================================================
// MONALYTICS - SISTEMA DE CARREGAMENTO SEGURO DE DADOS
// Versão: 2.0 - Máxima Segurança
// Autor: Antonio Siqueira - Monalisa Research
// ================================================================

console.log('🔒 Monalytics - Sistema Seguro v2.0');
console.log('💡 Desenvolvido por Antonio Siqueira');
console.log('📊 Análise Quantitativa Avançada');

// ================================================================
// CONFIGURAÇÕES DE SEGURANÇA
// ================================================================

const SECURITY_CONFIG = {
    // Rate Limiting - Máximo de requisições por minuto
    MAX_REQUESTS_PER_MINUTE: 20,
    
    // Timeout de requisição (ms)
    REQUEST_TIMEOUT: 10000, // 10 segundos
    
    // Tentativas de retry
    MAX_RETRIES: 3,
    
    // Delay entre retries (ms)
    RETRY_DELAY: 1000,
    
    // Validar origem das requisições
    VALIDATE_ORIGIN: true,
    
    // Domínios permitidos (seu site)
    ALLOWED_DOMAINS: [
        'newmonalytics.netlify.app', 
        'localhost',
        '127.0.0.1'
    ],
    
    // Cache de dados em memória (ms)
    CACHE_DURATION: 30000, // 30 segundos
    
    // Validar estrutura dos JSONs
    VALIDATE_DATA_STRUCTURE: true
};

// ================================================================
// CONFIGURAÇÃO DE DADOS
// ================================================================

const DATA_CONFIG = {
    GITHUB_RAW: 'https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics',
    BRANCH: 'main', // ou 'master'
    
    PATHS: {
        bolsa: '/balancos/IBOV/monitor_diario.json',
        indicadores: '/balancos/INDICADORES/indicadores_economicos.json',
        noticias: '/balancos/feed_noticias.json'
    },
    
    // Estrutura esperada para validação
    EXPECTED_STRUCTURE: {
        bolsa: ['ultima_atualizacao', 'total_acoes', 'estatisticas', 'top_5_altas', 'top_5_baixas'],
        indicadores: ['ultima_atualizacao', 'indicadores'],
        noticias: ['meta', 'feed']
    }
};

// ================================================================
// SISTEMA DE RATE LIMITING
// ================================================================

class RateLimiter {
    constructor() {
        this.requests = new Map();
        this.blocked = new Set();
    }
    
    // Verifica se requisição é permitida
    isAllowed(key) {
        // Se já está bloqueado
        if (this.blocked.has(key)) {
            const blockTime = this.blocked.get(key);
            const now = Date.now();
            
            // Desbloqueia após 1 minuto
            if (now - blockTime > 60000) {
                this.blocked.delete(key);
            } else {
                console.warn(`🚫 IP/Sessão bloqueado temporariamente: ${key}`);
                return false;
            }
        }
        
        const now = Date.now();
        const requestLog = this.requests.get(key) || [];
        
        // Remove requisições antigas (>1 minuto)
        const recentRequests = requestLog.filter(time => now - time < 60000);
        
        // Verifica limite
        if (recentRequests.length >= SECURITY_CONFIG.MAX_REQUESTS_PER_MINUTE) {
            console.error(`⛔ Rate limit excedido para ${key}. Bloqueando por 1 minuto.`);
            this.blocked.set(key, now);
            
            // Alerta de possível ataque
            this.logSuspiciousActivity(key, recentRequests.length);
            return false;
        }
        
        // Adiciona nova requisição
        recentRequests.push(now);
        this.requests.set(key, recentRequests);
        
        return true;
    }
    
    // Gera identificador único para sessão
    getSessionId() {
        if (!sessionStorage.getItem('monalytics_session_id')) {
            sessionStorage.setItem('monalytics_session_id', this.generateId());
        }
        return sessionStorage.getItem('monalytics_session_id');
    }
    
    generateId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    logSuspiciousActivity(key, requestCount) {
        console.error(`🚨 ATIVIDADE SUSPEITA DETECTADA:`);
        console.error(`   - Identificador: ${key}`);
        console.error(`   - Requisições: ${requestCount} em 1 minuto`);
        console.error(`   - Timestamp: ${new Date().toISOString()}`);
        console.error(`   - User Agent: ${navigator.userAgent}`);
        
        // Aqui você pode enviar para um sistema de monitoramento
        // sendToMonitoring({ key, requestCount, timestamp: Date.now() });
    }
}

const rateLimiter = new RateLimiter();

// ================================================================
// SISTEMA DE CACHE
// ================================================================

class DataCache {
    constructor() {
        this.cache = new Map();
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    get(key) {
        const cached = this.cache.get(key);
        
        if (!cached) return null;
        
        const age = Date.now() - cached.timestamp;
        
        // Cache expirado
        if (age > SECURITY_CONFIG.CACHE_DURATION) {
            this.cache.delete(key);
            return null;
        }
        
        console.log(`💾 Cache hit para ${key} (idade: ${Math.round(age/1000)}s)`);
        return cached.data;
    }
    
    clear() {
        this.cache.clear();
    }
}

const dataCache = new DataCache();

// ================================================================
// VALIDADORES DE SEGURANÇA
// ================================================================

class SecurityValidator {
    // Valida origem da requisição
    static validateOrigin() {
        if (!SECURITY_CONFIG.VALIDATE_ORIGIN) return true;
        
        const currentHost = window.location.hostname;
        
        const isAllowed = SECURITY_CONFIG.ALLOWED_DOMAINS.some(domain => 
            currentHost.includes(domain)
        );
        
        if (!isAllowed) {
            console.error(`🚫 Origem não autorizada: ${currentHost}`);
            console.error(`   Domínios permitidos:`, SECURITY_CONFIG.ALLOWED_DOMAINS);
        }
        
        return isAllowed;
    }
    
    // Valida estrutura do JSON
    static validateDataStructure(dataType, data) {
        if (!SECURITY_CONFIG.VALIDATE_DATA_STRUCTURE) return true;
        
        const expectedKeys = DATA_CONFIG.EXPECTED_STRUCTURE[dataType];
        
        if (!expectedKeys) {
            console.warn(`⚠️ Estrutura não definida para ${dataType}`);
            return true;
        }
        
        const hasAllKeys = expectedKeys.every(key => key in data);
        
        if (!hasAllKeys) {
            console.error(`❌ Estrutura inválida para ${dataType}`);
            console.error(`   Esperado:`, expectedKeys);
            console.error(`   Recebido:`, Object.keys(data));
            return false;
        }
        
        return true;
    }
    
    // Sanitiza dados de entrada
    static sanitizeData(data) {
        // Remove propriedades potencialmente perigosas
        const dangerous = ['__proto__', 'constructor', 'prototype'];
        
        const sanitized = JSON.parse(JSON.stringify(data, (key, value) => {
            if (dangerous.includes(key)) {
                console.warn(`🛡️ Propriedade perigosa removida: ${key}`);
                return undefined;
            }
            return value;
        }));
        
        return sanitized;
    }
}

// ================================================================
// FUNÇÃO PRINCIPAL DE CARREGAMENTO
// ================================================================

async function fetchJSON(dataType) {
    try {
        // 1. VALIDAÇÃO DE ORIGEM
        if (!SecurityValidator.validateOrigin()) {
            throw new Error('Origem não autorizada');
        }
        
        // 2. RATE LIMITING
        const sessionId = rateLimiter.getSessionId();
        if (!rateLimiter.isAllowed(sessionId)) {
            throw new Error('Rate limit excedido');
        }
        
        // 3. VERIFICAR CACHE
        const cached = dataCache.get(dataType);
        if (cached) {
            return cached;
        }
        
        // 4. BUSCAR DADOS COM RETRY
        const data = await fetchWithRetry(dataType);
        
        if (!data) {
            throw new Error('Falha ao carregar dados');
        }
        
        // 5. VALIDAR ESTRUTURA
        if (!SecurityValidator.validateDataStructure(dataType, data)) {
            throw new Error('Estrutura de dados inválida');
        }
        
        // 6. SANITIZAR DADOS
        const sanitizedData = SecurityValidator.sanitizeData(data);
        
        // 7. ARMAZENAR EM CACHE
        dataCache.set(dataType, sanitizedData);
        
        console.log(`✅ ${dataType.toUpperCase()} carregado com sucesso`);
        
        return sanitizedData;
        
    } catch (error) {
        console.error(`❌ Erro ao carregar ${dataType}:`, error.message);
        
        // Tenta retornar cache antigo em caso de erro
        const oldCache = dataCache.cache.get(dataType);
        if (oldCache) {
            console.warn(`⚠️ Usando cache antigo para ${dataType}`);
            return oldCache.data;
        }
        
        return null;
    }
}

// ================================================================
// FUNÇÃO DE FETCH COM RETRY E TIMEOUT
// ================================================================

async function fetchWithRetry(dataType, attempt = 1) {
    const path = DATA_CONFIG.PATHS[dataType];
    
    // Cache buster para forçar atualização
    const cacheBuster = `?t=${Date.now()}&v=${attempt}`;
    const url = `${DATA_CONFIG.GITHUB_RAW}/${DATA_CONFIG.BRANCH}${path}${cacheBuster}`;
    
    console.log(`📡 [${dataType}] Tentativa ${attempt}/${SECURITY_CONFIG.MAX_RETRIES}: ${url}`);
    
    try {
        // Cria AbortController para timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), SECURITY_CONFIG.REQUEST_TIMEOUT);
        
        const response = await fetch(url, {
          signal: controller.signal,
          cache: 'no-store',
          mode: 'cors',
          credentials: 'omit'
        });

        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Verifica Content-Type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.warn(`⚠️ Content-Type inesperado: ${contentType}`);
            
            // Tenta parsear mesmo assim
            const text = await response.text();
            
            // Se retornou HTML (404)
            if (text.includes('<!DOCTYPE') || text.includes('<html')) {
                throw new Error('Arquivo não encontrado (404 HTML)');
            }
            
            // Tenta parsear como JSON
            return JSON.parse(text);
        }
        
        const data = await response.json();
        
        // Validação básica
        if (!data || typeof data !== 'object') {
            throw new Error('Dados inválidos recebidos');
        }
        
        return data;
        
    } catch (error) {
        console.error(`⚠️ [${dataType}] Tentativa ${attempt} falhou:`, error.message);
        
        // Se não foi a última tentativa, retry
        if (attempt < SECURITY_CONFIG.MAX_RETRIES) {
            await sleep(SECURITY_CONFIG.RETRY_DELAY * attempt); // Backoff exponencial
            return fetchWithRetry(dataType, attempt + 1);
        }
        
        throw error;
    }
}

// ================================================================
// FUNÇÕES AUXILIARES
// ================================================================

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Limpa cache periodicamente (a cada 5 minutos)
setInterval(() => {
    console.log('🧹 Limpando cache antigo...');
    dataCache.clear();
}, 5 * 60 * 1000);

// ================================================================
// MONITORAMENTO E LOGS
// ================================================================

class MonitoringSystem {
    static logMetrics() {
        const metrics = {
            timestamp: new Date().toISOString(),
            cacheSize: dataCache.cache.size,
            rateLimitBlocked: rateLimiter.blocked.size,
            sessionId: rateLimiter.getSessionId()
        };
        
        console.log('📊 Métricas do sistema:', metrics);
        return metrics;
    }
}

// Log de métricas a cada 2 minutos (opcional)
if (window.location.hostname !== 'localhost') {
    setInterval(() => {
        MonitoringSystem.logMetrics();
    }, 2 * 60 * 1000);
}

// ================================================================
// EXPORTAR FUNÇÕES GLOBALMENTE
// ================================================================

window.MonalyticsSecure = {
    fetchJSON,
    clearCache: () => dataCache.clear(),
    getMetrics: () => MonitoringSystem.logMetrics(),
    config: SECURITY_CONFIG
};

console.log('✅ Sistema de segurança inicializado');
console.log('📌 Funções disponíveis: window.MonalyticsSecure');

// =========================== SLIDE 1: DESTAQUES DA BOLSA ===========================

/**
 * Carrega e renderiza dados da bolsa
 */
async function loadBolsaData() {
    const data = await fetchJSON('bolsa');
    
    if (!data) {
        showError('bolsaLoading', 'Erro ao carregar dados da bolsa');
        return;
    }
    
    renderBolsaData(data);
}

/**
 * Renderiza dados da bolsa
 */
function renderBolsaData(data) {
    // Esconde loading
    document.getElementById('bolsaLoading').style.display = 'none';
    
    // Mostra conteúdo
    document.getElementById('statsOverview').style.display = 'grid';
    document.getElementById('bolsaTabs').style.display = 'flex';
    document.getElementById('bolsaFooter').style.display = 'flex';
    
    // Estatísticas gerais
    const stats = data.estatisticas || {};
    document.getElementById('variacaoMedia').textContent = formatPercentage(stats.variacao_media);
    document.getElementById('acoesAlta').textContent = stats.acoes_em_alta || 0;
    document.getElementById('acoesBaixa').textContent = stats.acoes_em_baixa || 0;
    
    // Aplica cor à variação média
    const variacaoEl = document.getElementById('variacaoMedia');
    if (stats.variacao_media > 0) {
        variacaoEl.classList.add('positive');
    } else if (stats.variacao_media < 0) {
        variacaoEl.classList.add('negative');
    }
    
    // Renderiza listas
    renderStocksList('listAltas', data.top_5_altas || [], 'alta');
    renderStocksList('listBaixas', data.top_5_baixas || [], 'baixa');
    renderStocksList('listVolumes', data.top_5_volumes || [], 'volume');
    
    // Timestamp
    const timestamp = new Date(data.ultima_atualizacao);
    document.getElementById('bolsaTimestamp').textContent = formatTimestamp(timestamp);
    
    // Inicializa tabs
    initTabs();
}

/**
 * Renderiza lista de ações
 */
function renderStocksList(containerId, stocks, type) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = stocks.map(stock => {
        const variation = stock.variacao_pct || 0;
        const variationClass = variation >= 0 ? 'positive' : 'negative';
        const variationSign = variation >= 0 ? '+' : '';
        
        return `
            <div class="stock-item">
                <span class="stock-ticker">${stock.ticker}</span>
                <span class="stock-price">R$ ${formatCurrency(stock.preco_atual)}</span>
                <span class="stock-variation ${variationClass}">
                    ${variationSign}${variation.toFixed(2)}%
                </span>
                <span class="stock-volume">${formatVolume(stock.volume)}</span>
            </div>
        `;
    }).join('');
}

/**
 * Inicializa sistema de tabs
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Remove active de todos
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            
            // Adiciona active no clicado
            btn.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        });
    });
}

// =========================== SLIDE 2: INDICADORES ECONÔMICOS ===========================

/**
 * Carrega e renderiza indicadores econômicos
 */
async function loadIndicadoresData() {
    const data = await fetchJSON('indicadores');
    
    if (!data) {
        showError('indicadoresLoading', 'Erro ao carregar indicadores');
        return;
    }
    
    renderIndicadoresData(data);
}

/**
 * Renderiza indicadores econômicos
 */
function renderIndicadoresData(data) {
    // Esconde loading
    document.getElementById('indicadoresLoading').style.display = 'none';
    
    // Mostra conteúdo
    document.getElementById('indicadoresGrid').style.display = 'grid';
    document.getElementById('indicadoresFooter').style.display = 'flex';
    
    const ind = data.indicadores || {};
    
    // SELIC
    if (ind.selic) {
        document.getElementById('selicValor').textContent = ind.selic.formato || '-';
    }
    
    // CDI
    if (ind.cdi) {
        document.getElementById('cdiValor').textContent = ind.cdi.formato || '-';
    }
    
    // IPCA
    if (ind.ipca) {
        document.getElementById('ipcaValor').textContent = ind.ipca.formato_acumulado || '-';
        document.getElementById('ipcaMes').textContent = `Referência: ${formatMonth(ind.ipca.mes_referencia)}`;
    }
    
    // DÓLAR
    if (ind.dolar && !ind.dolar.erro) {
        document.getElementById('dolarValor').textContent = ind.dolar.formato || '-';
        document.getElementById('dolarData').textContent = `Data: ${formatDate(ind.dolar.data_referencia)}`;
    } else {
        document.getElementById('dolarValor').textContent = 'N/D';
        document.getElementById('dolarData').textContent = 'Dados indisponíveis';
    }
    
    // Timestamp
    const timestamp = new Date(data.ultima_atualizacao);
    document.getElementById('indicadoresTimestamp').textContent = formatTimestamp(timestamp);
}

// =========================== SLIDE 3: COMUNICADOS DO MERCADO ===========================

/**
 * Carrega e renderiza notícias/comunicados
 */
async function loadNoticiasData() {
    const data = await fetchJSON('noticias');
    
    if (!data) {
        showError('noticiasLoading', 'Erro ao carregar comunicados');
        return;
    }
    
    renderNoticiasData(data);
}

/**
 * Renderiza comunicados do mercado
 */
function renderNoticiasData(data) {
    // Esconde loading
    document.getElementById('noticiasLoading').style.display = 'none';
    
    // Mostra conteúdo
    document.getElementById('comunicadosList').style.display = 'flex';
    document.getElementById('noticiasFooter').style.display = 'flex';
    
    // Filtra e ordena notícias por prioridade
    const feed = data.feed || [];
    const top5 = selectTopNews(feed, 5);
    
    // Renderiza lista
    const container = document.getElementById('comunicadosList');
    if (!container) return;
    
    container.innerHTML = top5.map(item => {
        const categoria = normalizarCategoria(item.noticia.categoria);
        const badgeClass = getCategoryBadgeClass(categoria);
        
        return `
            <div class="news-item">
                <span class="news-badge ${badgeClass}">${categoria}</span>
                <div class="news-content">
                    <div class="news-header">
                        <span class="news-ticker">${item.empresa.ticker}</span>
                        <span class="news-date">${formatDate(item.data)} ${item.hora}</span>
                    </div>
                    <div class="news-title">${item.noticia.headline}</div>
                    <div class="news-company">${item.empresa.nome}</div>
                    <a href="${item.noticia.url}" target="_blank" class="news-link">
                        Ver comunicado completo <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
        `;
    }).join('');
    
    // Timestamp
    const timestamp = new Date(data.meta.ultima_atualizacao);
    document.getElementById('noticiasTimestamp').textContent = formatTimestamp(timestamp);
}

/**
 * Seleciona top N notícias priorizando categoria
 */
function selectTopNews(feed, limit = 5) {
    // Prioridades de categoria (menor = maior prioridade)
    const priorities = {
        'Fato Relevante': 1,
        'Dividendos': 2,
        'Resultados': 3,
        'Aviso': 4,
        'Outros': 5,
        'Governança': 6
    };
    
    // Ordena por: prioridade da categoria > data > hora
    const sorted = [...feed].sort((a, b) => {
        const prioA = priorities[a.noticia.categoria] || 99;
        const prioB = priorities[b.noticia.categoria] || 99;
        
        if (prioA !== prioB) return prioA - prioB;
        
        // Se mesma prioridade, ordena por data (mais recente primeiro)
        const dateCompare = b.data.localeCompare(a.data);
        if (dateCompare !== 0) return dateCompare;
        
        // Se mesma data, ordena por hora
        return b.hora.localeCompare(a.hora);
    });
    
    return sorted.slice(0, limit);
}

/**
 * Normaliza nome da categoria
 */
function normalizarCategoria(categoria) {
    const map = {
        'Fato Relevante': 'Fato Relevante',
        'Dividendos': 'Dividendos',
        'Resultados': 'Resultados',
        'Aviso': 'Aviso',
        'Governança': 'Governança',
        'Outros': 'Outros'
    };
    
    return map[categoria] || categoria;
}

/**
 * Retorna classe CSS para badge da categoria
 */
function getCategoryBadgeClass(categoria) {
    const map = {
        'Fato Relevante': 'fato-relevante',
        'Dividendos': 'dividendos',
        'Resultados': 'resultados',
        'Aviso': 'aviso',
        'Governança': 'governanca',
        'Outros': 'outros'
    };
    
    return map[categoria] || 'outros';
}

// =========================== UTILITY FUNCTIONS ===========================

/**
 * Formata porcentagem
 */
function formatPercentage(value) {
    if (value == null) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

/**
 * Formata moeda
 */
function formatCurrency(value) {
    if (value == null) return '-';
    return value.toFixed(2);
}

/**
 * Formata volume (milhões)
 */
function formatVolume(value) {
    if (value == null) return '-';
    
    if (value >= 1000000) {
        return `${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
    }
    
    return value.toLocaleString('pt-BR');
}

/**
 * Formata timestamp
 */
function formatTimestamp(date) {
    if (!date || isNaN(date)) return '-';
    
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Formata data
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    
    const date = new Date(dateStr + 'T00:00:00');
    if (isNaN(date)) return dateStr;
    
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Formata mês de referência
 */
function formatMonth(dateStr) {
    if (!dateStr) return '-';
    
    const [year, month] = dateStr.split('-');
    const monthNames = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    
    const monthIndex = parseInt(month, 10) - 1;
    return `${monthNames[monthIndex]} ${year}`;
}

/**
 * Mostra mensagem de erro
 */
function showError(loadingId, message) {
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) {
        loadingEl.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;
    }
}

// =========================== INITIALIZATION ===========================

/**
 * Inicialização quando DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎪 Inicializando Carrossel de Destaques...');
    
    // Inicializa carrossel
    initCarousel();
    
    // Carrega dados
    loadAllData();
});

// =========================== EXPORT ===========================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initCarousel,
        loadAllData,
        navigateSlide,
        goToSlide
    };
}
