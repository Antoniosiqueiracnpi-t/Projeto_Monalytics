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
/*
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
*/

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

const NOTICIAS_MERCADO_PATH = 'balancos/NOTICIAS/noticias_mercado.json';
const DIVIDENDOS_PATH = 'agenda_dividendos_acoes_investidor10.json';
const MAPEAMENTO_B3_PATH = 'mapeamento_b3_consolidado.csv';
const IBOV_PATH = 'balancos/IBOV/historico_precos_diarios.json';

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
        loadNoticiasData(),
        loadNoticiasMercado(),
        loadDividendosData(),
        loadMapeamentoB3(),
        loadIbovData()
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

// =========================== SLIDE 4: NOTÍCIAS DO MERCADO ===========================

/**
 * Carrega notícias do mercado
 */
async function loadNoticiasMercado() {
    try {
        const response = await fetch(`${DATA_CONFIG.GITHUB_RAW}/${DATA_CONFIG.BRANCH}/${NOTICIAS_MERCADO_PATH}?t=${Date.now()}`);
        
        if (!response.ok) {
            throw new Error('Erro ao carregar notícias');
        }
        
        const data = await response.json();
        renderNoticiasMercado(data);
        
    } catch (error) {
        console.error('❌ Erro ao carregar notícias:', error);
        showNewsError();
    }
}

/**
 * Renderiza notícias do mercado
 */
function renderNoticiasMercado(data) {
    // Esconde loading
    document.getElementById('newsLoading').style.display = 'none';
    
    // Mostra grid
    document.getElementById('newsGrid').style.display = 'grid';
    document.getElementById('newsTimestampSection').style.display = 'block';
    
    // Agrega todas as notícias em uma lista flat
    const todasNoticias = [];
    
    const portais = data.portais || {};
    for (const noticias of Object.values(portais)) {
        todasNoticias.push(...noticias);
    }
    
    // Ordena por horário (mais recentes primeiro)
    todasNoticias.sort((a, b) => {
        const timeA = a.horario.split(':').map(Number);
        const timeB = b.horario.split(':').map(Number);
        return (timeB[0] * 60 + timeB[1]) - (timeA[0] * 60 + timeA[1]);
    });
    
    // Renderiza grid
    renderNewsGrid(todasNoticias);
    
    // Inicializa filtros
    initNewsFilters(todasNoticias);
    
    // Timestamp
    const timestamp = new Date(data.ultima_atualizacao);
    document.getElementById('newsTimestamp').textContent = 
        `Última atualização: ${formatTimestamp(timestamp)}`;
}

/**
 * Renderiza grid de notícias
 */
function renderNewsGrid(noticias) {
    const grid = document.getElementById('newsGrid');
    if (!grid) return;
    
    grid.innerHTML = noticias.map(noticia => {
        const categoriaClass = (noticia.categoria || 'geral').toLowerCase();
        const tagsHtml = (noticia.tags || []).length > 0
            ? `<div class="news-tags">${noticia.tags.map(tag => 
                `<span class="news-tag">${tag}</span>`
              ).join('')}</div>`
            : '';
        
        return `
            <div class="news-card" data-categoria="${noticia.categoria || 'Geral'}">
                <img src="${noticia.imagem}" alt="${noticia.titulo}" class="news-card-image" 
                     onerror="this.src='https://i.ibb.co/ZpSVYcgH/Monalytics-3-D.png'">
                <div class="news-card-content">
                    <div class="news-card-header">
                        <span class="news-category-badge ${categoriaClass}">${noticia.categoria || 'Geral'}</span>
                        <span class="news-time">
                            <i class="fas fa-clock"></i> ${noticia.horario}
                        </span>
                    </div>
                    <h3 class="news-card-title">${noticia.titulo}</h3>
                    ${tagsHtml}
                    <div class="news-card-footer">
                        <span class="news-source">
                            <i class="fas fa-newspaper"></i> ${noticia.fonte}
                        </span>
                        <a href="${noticia.link}" target="_blank" class="news-read-more">
                            Ler mais <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// =========================== AGENDA DE DIVIDENDOS ===========================

let currentPeriodDays = 30;
let allDividendos = [];
let mapeamentoB3 = [];
let acaoAtualData = null;
let ibovData = null;
let acaoChart = null;
let ibovEnabled = false;
let periodoAtual = 365;

/**
 * Carrega dados de dividendos
 */
async function loadDividendosData() {
    try {
        const response = await fetch(`${DATA_CONFIG.GITHUB_RAW}/${DATA_CONFIG.BRANCH}/${DIVIDENDOS_PATH}?t=${Date.now()}`);

        if (!response.ok) {
            throw new Error('Erro ao carregar dividendos');
        }

        const data = await response.json();
        allDividendos = data;
        renderDividendos(currentPeriodDays);

    } catch (error) {
        console.error('❌ Erro ao carregar dividendos:', error);
        showDividendosError();
    }
}

/**
 * Renderiza agenda de dividendos
 */
function renderDividendos(days = 30) {
    // Esconde loading
    document.getElementById('dividendosLoading').style.display = 'none';

    // Mostra filtros e grid
    document.getElementById('dividendosTipoFilters').style.display = 'flex';
    document.getElementById('dividendosGrid').style.display = 'grid';
    document.getElementById('dividendosFooter').style.display = 'block';

    // Filtra dividendos futuros
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);

    const dataLimite = new Date(hoje);
    dataLimite.setDate(dataLimite.getDate() + days);

    const dividendosFuturos = allDividendos.filter(div => {
        const dataCom = new Date(div.data_com);
        return dataCom >= hoje && dataCom <= dataLimite;
    });

    // Ordena por data COM (mais próxima primeiro)
    dividendosFuturos.sort((a, b) => {
        return new Date(a.data_com) - new Date(b.data_com);
    });

    // Remove duplicatas por ticker + data_com (mantém apenas um registro por ação/data)
    const dividendosUnicos = [];
    const vistos = new Set();

    for (const div of dividendosFuturos) {
        const key = `${div.ticker}_${div.data_com}`;
        if (!vistos.has(key)) {
            vistos.add(key);
            dividendosUnicos.push(div);
        }
    }

    // Renderiza grid
    if (dividendosUnicos.length === 0) {
        showDividendosEmpty();
    } else {
        renderDividendosGrid(dividendosUnicos);
        initDividendosTipoFilters(dividendosUnicos);
        initPeriodFilters();
    }
}

/**
 * Renderiza grid de dividendos
 * (sem nome da empresa — apenas ticker)
 */
function renderDividendosGrid(dividendos) {
    const grid = document.getElementById('dividendosGrid');
    if (!grid) return;

    // Esconde mensagem vazia
    document.getElementById('dividendosEmpty').style.display = 'none';
    grid.style.display = 'grid';

    grid.innerHTML = dividendos.map(div => {
        const tipoClass = String(div.tipo || '').toLowerCase();
        const tipoLabel = div.tipo === 'DIVIDENDO' ? 'Dividendo' : (div.tipo === 'JSCP' ? 'JSCP' : div.tipo);

        return `
            <div class="dividendo-card" data-tipo="${div.tipo}">
                <div class="dividendo-card-header">
                    <div class="dividendo-ticker">${div.ticker}</div>
                    <span class="dividendo-tipo-badge ${tipoClass}">${tipoLabel}</span>
                </div>

                <div class="dividendo-valor-container">
                    <div class="dividendo-valor-label">Valor por ação</div>
                    <div class="dividendo-valor">R$ ${Number(div.valor || 0).toFixed(2)}</div>
                </div>

                <div class="dividendo-datas">
                    <div class="dividendo-data-item">
                        <div class="dividendo-data-label">
                            <i class="fas fa-calendar-check"></i> Data COM
                        </div>
                        <div class="dividendo-data-value">${formatDividendoDate(div.data_com)}</div>
                    </div>
                    <div class="dividendo-data-item">
                        <div class="dividendo-data-label">
                            <i class="fas fa-calendar-day"></i> Pagamento
                        </div>
                        <div class="dividendo-data-value">${formatDividendoDate(div.data_pagamento)}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Inicializa filtros de período
 */
function initPeriodFilters() {
    const periodBtns = document.querySelectorAll('.dividendos-filter-btn');

    periodBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const period = parseInt(btn.dataset.period);
            currentPeriodDays = period;

            // Atualiza botões ativos
            periodBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Re-renderiza
            renderDividendos(period);
        });
    });
}

/**
 * Inicializa filtros de tipo
 */
function initDividendosTipoFilters(dividendos) {
    const tipoBtns = document.querySelectorAll('.tipo-filter-btn');
    const cards = document.querySelectorAll('.dividendo-card');

    tipoBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tipo = btn.dataset.tipo;

            // Atualiza botões ativos
            tipoBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Filtra cards
            cards.forEach(card => {
                const cardTipo = card.dataset.tipo;

                if (tipo === 'todos' || cardTipo === tipo) {
                    card.style.display = 'block';
                    card.style.animation = 'fadeIn 0.3s ease';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

/**
 * Formata data para exibição
 */
function formatDividendoDate(dateStr) {
    if (!dateStr) return '-';

    const date = new Date(dateStr + 'T00:00:00');
    if (isNaN(date)) return dateStr;

    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

/**
 * Mostra mensagem de erro
 */
function showDividendosError() {
    const loading = document.getElementById('dividendosLoading');
    if (loading) {
        loading.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Erro ao carregar agenda de dividendos</span>
        `;
    }
}

/**
 * Mostra mensagem vazia
 */
function showDividendosEmpty() {
    document.getElementById('dividendosGrid').style.display = 'none';
    document.getElementById('dividendosEmpty').style.display = 'flex';
}


/**
 * Inicializa sistema de filtros
 */
function initNewsFilters(noticias) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const newsCards = document.querySelectorAll('.news-card');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            
            // Atualiza botões ativos
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filtra cards
            newsCards.forEach(card => {
                const categoria = card.dataset.categoria;
                
                if (filter === 'todas' || categoria === filter) {
                    card.style.display = 'flex';
                    // Animação de entrada
                    card.style.animation = 'fadeIn 0.3s ease';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
}

/**
 * Mostra erro ao carregar notícias
 */
function showNewsError() {
    const loading = document.getElementById('newsLoading');
    if (loading) {
        loading.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Erro ao carregar notícias do mercado</span>
        `;
    }
}

/**
 * Seleciona top N notícias priorizando categoria
 */
function selectTopNews(feed, limit = 5) {
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
        
        const dateCompare = b.data.localeCompare(a.data);
        if (dateCompare !== 0) return dateCompare;
        
        return b.hora.localeCompare(a.hora);
    });
    
    // Remove duplicatas por ticker
    const seen = new Set();
    const unique = sorted.filter(item => {
        if (seen.has(item.empresa.ticker)) return false;
        seen.add(item.empresa.ticker);
        return true;
    });
    
    return unique.slice(0, limit);
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
    
    // Inicializa busca e funcionalidades de ações
    initAcaoBusca();
    initPeriodoFilters();
    initToggleIbov();
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

/* ========================================
   ANÁLISE GRÁFICA DE AÇÕES
   ======================================== */

// ==================== 1. FUNÇÃO parseCSVLine (NOVA) ====================
// Adicione esta função ANTES de loadMapeamentoB3()
/**
 * Parser CSV robusto que lida com campos entre aspas
 * RFC 4180 compliant - baseado em regex pattern testado
 */
function parseCSVLine(csvText, delimiter = ';') {
    const pattern = new RegExp(
        (
            "(\\"+delimiter+"|\\r?\\n|\\r|^)" +
            "(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|((?!\")[^\\"+delimiter+"\\r\\n]*))"
        ),
        "gi"
    );
    
    const rows = [[]];
    let matches;
    
    while ((matches = pattern.exec(csvText)) !== null) {
        const matchedDelimiter = matches[1];
        let value = matches[2] !== undefined 
            ? matches[2].replace(/""/g, '"')  // Substitui "" por "
            : matches[3];                      // Campo sem aspas
        
        if (matchedDelimiter.length && matchedDelimiter !== delimiter) {
            rows.push([]);
        }
        
        rows[rows.length - 1].push(value || '');
    }
    
    return rows;
}


// ==================== 2. FUNÇÃO loadMapeamentoB3 CORRIGIDA ====================
async function loadMapeamentoB3() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/${MAPEAMENTO_B3_PATH}?t=${timestamp}`);
        const csvText = await response.text();
        
        console.log('📥 Carregando mapeamento B3...');
        
        // Parse CSV usando função robusta
        const rows = parseCSVLine(csvText);
        
        // Remove header e linhas vazias
        const rawData = rows.slice(1)
            .filter(row => row.length >= 2 && row[0] && row[1])
            .map(row => ({
                ticker: row[0] || '',
                empresa: row[1] || '',
                cnpj: row[2] || '',
                codigo_cvm: row[3] || '',
                setor: row[4] || '',
                segmento: row[5] || '',
                sede: row[6] || '',
                descricao: row[7] || ''
            }));
        
        console.log(`📊 Empresas carregadas: ${rawData.length}`);
        
        // Expande empresas com múltiplos tickers
        mapeamentoB3 = [];
        rawData.forEach(item => {
            const tickers = item.ticker.split(';').map(t => t.trim()).filter(t => t);
            const todosTickersStr = item.ticker;
            
            tickers.forEach(ticker => {
                mapeamentoB3.push({
                    ticker: ticker,
                    empresa: item.empresa,
                    cnpj: item.cnpj,
                    codigo_cvm: item.codigo_cvm,
                    setor: item.setor,
                    segmento: item.segmento,
                    sede: item.sede,
                    descricao: item.descricao,
                    todosTickersStr: todosTickersStr
                });
            });
        });
        
        console.log(`✅ Mapeamento B3 carregado: ${mapeamentoB3.length} entradas (tickers expandidos)`);
        
        // Debug: Verifica PETR3 e PETR4
        const petr3 = mapeamentoB3.find(item => item.ticker === 'PETR3');
        const petr4 = mapeamentoB3.find(item => item.ticker === 'PETR4');
        if (petr3) console.log('✅ PETR3 encontrado:', petr3.empresa);
        if (petr4) console.log('✅ PETR4 encontrado:', petr4.empresa);
        
    } catch (error) {
        console.error('❌ Erro ao carregar mapeamento B3:', error);
    }
}

// Carrega dados do Ibovespa
async function loadIbovData() {
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/${IBOV_PATH}?t=${timestamp}`);
        ibovData = await response.json();
        console.log('IBOV carregado:', ibovData.dados.length, 'registros');
    } catch (error) {
        console.error('Erro ao carregar IBOV:', error);
    }
}

// Inicializa busca de ações
function initAcaoBusca() {
    const searchInput = document.getElementById('acaoSearchInput');
    const searchBtn = document.getElementById('acaoSearchBtn');
    const suggestions = document.getElementById('searchSuggestions');
    
    // Event listeners para busca
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toUpperCase();
        
        if (query.length >= 2) {
            const matches = mapeamentoB3
                .filter(item => 
                    item.ticker.includes(query) || 
                    item.empresa.toUpperCase().includes(query)
                )
                .slice(0, 8);
            
            if (matches.length > 0) {
                renderSuggestions(matches);
            } else {
                suggestions.style.display = 'none';
            }
        } else {
            suggestions.style.display = 'none';
        }
    });
    
    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim().toUpperCase();
        if (query) {
            console.log('🔍 Buscando ticker:', query);
            
            const match = mapeamentoB3.find(item => item.ticker === query);
            
            if (match) {
                console.log('✅ Ticker encontrado:', match);
                loadAcaoData(match.ticker);
                suggestions.style.display = 'none';
            } else {
                console.log('⚠️ Ticker não encontrado no mapeamento');
                alert(`Ticker ${query} não encontrado no mapeamento B3`);
            }
        }
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.analise-grafica-header')) {
            suggestions.style.display = 'none';
        }
    });
    
    document.querySelectorAll('.ticker-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            const ticker = tag.dataset.ticker;
            searchInput.value = ticker;
            loadAcaoData(ticker);
        });
    });
}

/* ========================================
   SISTEMA DE EXPANSÃO DE BLOCOS
   ======================================== */

/**
 * Inicializa sistema de expansão para Notícias e Dividendos
 */
function initExpandSystem() {
    // Notícias
    const newsGrid = document.getElementById('newsGrid');
    const newsBtn = document.getElementById('newsExpandBtn');
    const newsText = document.getElementById('newsExpandText');
    const newsCount = document.getElementById('newsExpandCount');
    
    if (newsBtn && newsGrid) {
        newsBtn.addEventListener('click', () => {
            toggleExpand(newsGrid, newsBtn, newsText, newsCount, 'notícias');
        });
    }
    
    // Dividendos
    const divGrid = document.getElementById('dividendosGrid');
    const divBtn = document.getElementById('dividendosExpandBtn');
    const divText = document.getElementById('dividendosExpandText');
    const divCount = document.getElementById('dividendosExpandCount');
    
    if (divBtn && divGrid) {
        divBtn.addEventListener('click', () => {
            toggleExpand(divGrid, divBtn, divText, divCount, 'dividendos');
        });
    }
}

/**
 * Toggle expansão com animação suave
 */
function toggleExpand(grid, btn, textEl, countEl, type) {
    const isCollapsed = grid.classList.contains('collapsed');
    
    if (isCollapsed) {
        // Expandir
        grid.classList.remove('collapsed');
        grid.style.maxHeight = grid.scrollHeight + 'px';
        
        btn.classList.add('expanded');
        textEl.textContent = `Ver menos ${type}`;
        countEl.style.display = 'none';
        
        // Scroll suave para o botão
        setTimeout(() => {
            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 300);
        
    } else {
        // Colapsar
        grid.style.maxHeight = grid.scrollHeight + 'px';
        
        // Force reflow
        grid.offsetHeight;
        
        grid.classList.add('collapsed');
        grid.style.maxHeight = '';
        
        btn.classList.remove('expanded');
        textEl.textContent = `Ver mais ${type}`;
        countEl.style.display = 'inline-block';
        
        // Scroll para o topo da seção
        setTimeout(() => {
            grid.parentElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
}

/**
 * Atualiza contador de itens ocultos
 */
function updateExpandCounter(gridId, btnId, countId) {
    const grid = document.getElementById(gridId);
    const btn = document.getElementById(btnId);
    const countEl = document.getElementById(countId);
    
    if (!grid || !btn || !countEl) return;
    
    const cards = grid.children;
    const totalCards = cards.length;
    
    if (totalCards <= 6) {
        // Se tiver 6 ou menos cards, não precisa botão
        btn.style.display = 'none';
        grid.classList.remove('collapsed');
        return;
    }
    
    // Calcula quantos cards estão visíveis (aproximadamente 2 linhas = 6 cards em desktop)
    const visibleCards = window.innerWidth > 768 ? 6 : 4;
    const hiddenCards = totalCards - visibleCards;
    
    countEl.textContent = `+${hiddenCards}`;
    btn.style.display = 'flex';
}

// Hook nas funções de renderização existentes
const originalRenderNewsGrid = renderNewsGrid;
renderNewsGrid = function(noticias) {
    originalRenderNewsGrid(noticias);
    setTimeout(() => {
        updateExpandCounter('newsGrid', 'newsExpandBtn', 'newsExpandCount');
    }, 100);
};

const originalRenderDividendosGrid = renderDividendosGrid;
renderDividendosGrid = function(dividendos) {
    originalRenderDividendosGrid(dividendos);
    setTimeout(() => {
        updateExpandCounter('dividendosGrid', 'dividendosExpandBtn', 'dividendosExpandCount');
    }, 100);
};

// Inicializa ao carregar DOM
document.addEventListener('DOMContentLoaded', () => {
    initExpandSystem();
    
    // Recalcula ao redimensionar janela
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            updateExpandCounter('newsGrid', 'newsExpandBtn', 'newsExpandCount');
            updateExpandCounter('dividendosGrid', 'dividendosExpandBtn', 'dividendosExpandCount');
        }, 250);
    });
});

// Renderiza sugestões
function renderSuggestions(matches) {
    const suggestions = document.getElementById('searchSuggestions');
    
    // Remove duplicatas por empresa (mantém apenas primeira ocorrência)
    const uniqueMatches = [];
    const seenEmpresas = new Set();
    
    for (const item of matches) {
        if (!seenEmpresas.has(item.empresa)) {
            seenEmpresas.add(item.empresa);
            uniqueMatches.push(item);
        }
    }
    
    suggestions.innerHTML = uniqueMatches
        .map(item => `
            <div class="suggestion-item" data-ticker="${item.ticker}">
                <div>
                    <span class="suggestion-ticker">${item.ticker}</span>
                    ${item.todosTickersStr && item.todosTickersStr.includes(';') 
                        ? `<span style="color: #999; font-size: 0.85em; margin-left: 4px;">(${item.todosTickersStr})</span>` 
                        : ''}
                    <span class="suggestion-nome">${item.empresa}</span>
                </div>
            </div>
        `)
        .join('');
    
    suggestions.style.display = 'block';
    
    // Click em sugestão
    suggestions.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const ticker = item.dataset.ticker;
            document.getElementById('acaoSearchInput').value = ticker;
            loadAcaoData(ticker);
            suggestions.style.display = 'none';
        });
    });
}

// Carrega dados da ação
async function loadAcaoData(ticker) {
    const emptyState = document.getElementById('acaoEmptyState');
    const loadingState = document.getElementById('acaoLoadingState');
    const content = document.getElementById('acaoAnaliseContent');
    
    emptyState.style.display = 'none';
    content.style.display = 'none';
    loadingState.style.display = 'block';
    
    try {
        console.log(`🔍 Carregando dados de ${ticker}...`);
        
        // Busca info da empresa no mapeamento
        const empresaInfo = mapeamentoB3.find(item => item.ticker === ticker);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${ticker} não encontrado no mapeamento B3`);
        }
        
        console.log('✅ Empresa encontrada:', empresaInfo.empresa);
        
        // Usa o primeiro ticker como pasta
        const tickerPasta = empresaInfo.todosTickersStr 
            ? empresaInfo.todosTickersStr.split(';')[0].trim()
            : ticker;
        
        console.log(`📂 Usando pasta: balancos/${tickerPasta}/`);
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/historico_precos_diarios.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`Dados não encontrados para ${ticker}`);
        }
        
        acaoAtualData = await response.json();
        console.log('✅ Dados carregados:', acaoAtualData.dados.length, 'registros');
        
        // Atualiza UI com ticker solicitado
        document.getElementById('acaoTicker').textContent = ticker;
        document.getElementById('acaoNome').textContent = empresaInfo.empresa;
        
        // Carrega logo
        const logoImg = document.getElementById('acaoLogoImg');
        const logoFallback = document.getElementById('acaoLogoFallback');
        logoImg.src = `https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/logo.png?t=${timestamp}`;
        logoImg.style.display = 'block';
        logoFallback.style.display = 'none';
        logoFallback.textContent = ticker.substring(0, 4);
        
        // Atualiza informações da empresa
        updateEmpresaInfo(ticker);
        
        // Atualiza indicadores
        updateIndicadores();
        
        // Renderiza gráfico
        renderAcaoChart();
        
        // Mostra conteúdo
        loadingState.style.display = 'none';
        content.style.display = 'block';
        
        console.log('✅ Ação carregada com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao carregar ação:', error);
        loadingState.style.display = 'none';
        emptyState.style.display = 'block';
        alert(`Erro ao carregar ${ticker}:\n${error.message}`);
    }
}

/* ========================================
   SISTEMA DE MÚLTIPLOS DA EMPRESA
   ======================================== */

let multiplosData = null;
let multiplosChart = null;

/**
 * Carrega dados de múltiplos da empresa
 */
async function loadMultiplosData(ticker) {
    try {
        console.log(`📊 Carregando múltiplos de ${ticker}...`);
        
        // Busca info no mapeamento para pegar o ticker correto da pasta
        const empresaInfo = mapeamentoB3.find(item => item.ticker === ticker);
        const tickerPasta = empresaInfo && empresaInfo.todosTickersStr 
            ? empresaInfo.todosTickersStr.split(';')[0].trim()
            : ticker;
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/multiplos.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`Múltiplos não encontrados para ${ticker}`);
        }
        
        multiplosData = await response.json();
        console.log('✅ Múltiplos carregados:', Object.keys(multiplosData.ltm.multiplos).length);
        
        renderMultiplosSection();
        
    } catch (error) {
        console.error('❌ Erro ao carregar múltiplos:', error);
        document.getElementById('multiplosSection').style.display = 'none';
    }
}

/* ========================================
   COMPOSIÇÃO ACIONÁRIA
   ======================================== */

let acionistasData = null;
let acionistasChart = null;

/**
 * Carrega dados de composição acionária
 */
async function loadAcionistasData(ticker) {
    try {
        console.log(`📊 Carregando composição acionária de ${ticker}...`);
        
        // Busca info no mapeamento para pegar o ticker correto da pasta
        const empresaInfo = mapeamentoB3.find(item => item.ticker === ticker);
        const tickerPasta = empresaInfo && empresaInfo.todosTickersStr 
            ? empresaInfo.todosTickersStr.split(';')[0].trim()
            : ticker;
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/acionistas.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`Dados de acionistas não encontrados para ${ticker}`);
        }
        
        acionistasData = await response.json();
        console.log('✅ Composição acionária carregada:', acionistasData.acionistas.length, 'acionistas');
        
        renderComposicaoAcionaria();
        
    } catch (error) {
        console.error('❌ Erro ao carregar composição acionária:', error);
        document.getElementById('composicaoAcionariaCard').style.display = 'none';
    }
}

/* ========================================
   I.A ANALISA - ANÁLISE AUTOMÁTICA
   ======================================== */

let analiseBalancosData = null;

/**
 * Carrega análise de balanços da I.A
 */
async function loadAnaliseBalancos(ticker) {
    try {
        console.log(`🤖 Carregando análise I.A de ${ticker}...`);
        
        // Busca info no mapeamento para pegar o ticker correto da pasta
        const empresaInfo = mapeamentoB3.find(item => item.ticker === ticker);
        const tickerPasta = empresaInfo && empresaInfo.todosTickersStr 
            ? empresaInfo.todosTickersStr.split(';')[0].trim()
            : ticker;
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/analise_balancos.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`Análise não encontrada para ${ticker}`);
        }
        
        analiseBalancosData = await response.json();
        console.log('✅ Análise I.A carregada com sucesso');
        
        renderIAAnalisa();
        
    } catch (error) {
        console.error('❌ Erro ao carregar análise I.A:', error);
        document.getElementById('iaAnalisaSection').style.display = 'none';
    }
}

/**
 * Renderiza seção de análise da I.A
 */
function renderIAAnalisa() {
    const section = document.getElementById('iaAnalisaSection');
    if (!section || !analiseBalancosData) return;
    
    const data = analiseBalancosData;
    
    // Formata data de atualização
    const dataAtualizacao = new Date(data.ultima_atualizacao);
    const dataFormatada = dataAtualizacao.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
    
    // HTML principal
    let html = `
        <div class="ia-header">
            <div class="ia-icon">
                <i class="fas fa-brain"></i>
            </div>
            <div class="ia-title-group">
                <h3>I.A Analisa</h3>
                <p>Análise automática de balanços e demonstrativos</p>
            </div>
            <div class="ia-badge">
                <i class="fas fa-robot"></i> Powered by AI
            </div>
        </div>
        
        <div class="ia-content">
            <!-- Análise Crítica -->
            <div class="ia-analise-critica">
                <h4>
                    <i class="fas fa-lightbulb"></i>
                    Análise Crítica
                </h4>
                <p>${data.analise_critica}</p>
            </div>
            
            <!-- Grid de Pontos Fortes e Atenção -->
            <div class="ia-pontos-grid">
                <!-- Pontos Fortes -->
                <div class="ia-pontos-card fortes">
                    <div class="ia-pontos-header">
                        <div class="ia-pontos-icon">
                            <i class="fas fa-thumbs-up"></i>
                        </div>
                        <h4>Pontos Fortes</h4>
                    </div>
                    <div class="ia-pontos-list">
    `;
    
    // Renderiza pontos fortes
    if (data.pontos_fortes && data.pontos_fortes.length > 0) {
        data.pontos_fortes.forEach(ponto => {
            html += `
                <div class="ia-ponto-item">
                    <i class="fas fa-check-circle"></i>
                    <span>${ponto}</span>
                </div>
            `;
        });
    } else {
        html += `<div class="ia-pontos-empty">Nenhum ponto forte identificado</div>`;
    }
    
    html += `
                    </div>
                </div>
                
                <!-- Pontos de Atenção -->
                <div class="ia-pontos-card atencao">
                    <div class="ia-pontos-header">
                        <div class="ia-pontos-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h4>Pontos de Atenção</h4>
                    </div>
                    <div class="ia-pontos-list">
    `;
    
    // Renderiza pontos de atenção
    if (data.pontos_atencao && data.pontos_atencao.length > 0) {
        data.pontos_atencao.forEach(ponto => {
            html += `
                <div class="ia-ponto-item">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>${ponto}</span>
                </div>
            `;
        });
    } else {
        html += `<div class="ia-pontos-empty">✓ Nenhum ponto crítico identificado</div>`;
    }
    
    html += `
                    </div>
                </div>
            </div>
            
            <!-- Métricas em Destaque -->
            <div class="ia-metricas-destaque">
                <h4>
                    <i class="fas fa-chart-bar"></i>
                    Métricas em Destaque
                </h4>
                <div class="ia-metricas-grid">
                    <div class="ia-metrica-item">
                        <div class="ia-metrica-valor">${data.metricas.receita.cagr.toFixed(2)}%</div>
                        <div class="ia-metrica-label">CAGR Receita</div>
                    </div>
                    <div class="ia-metrica-item">
                        <div class="ia-metrica-valor">${data.metricas.margens.liquida.toFixed(2)}%</div>
                        <div class="ia-metrica-label">Margem Líquida</div>
                    </div>
                    <div class="ia-metrica-item">
                        <div class="ia-metrica-valor">${data.metricas.rentabilidade.roe_medio.toFixed(2)}%</div>
                        <div class="ia-metrica-label">ROE Médio</div>
                    </div>
                    <div class="ia-metrica-item">
                        <div class="ia-metrica-valor">${data.periodo_analisado.anos.toFixed(1)}</div>
                        <div class="ia-metrica-label">Anos Analisados</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="ia-footer">
            <i class="fas fa-info-circle"></i>
            Análise gerada automaticamente • Última atualização: ${dataFormatada} • Período: ${data.periodo_analisado.inicio} a ${data.periodo_analisado.fim}
        </div>
    `;
    
    section.innerHTML = html;
    section.style.display = 'block';
}

/**
 * HOOK: Adiciona carregamento de análise I.A ao carregar ação
 */
const originalLoadAcaoDataWithIA = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithIA.call(this, ticker);
    
    // Carrega análise I.A após carregar a ação
    await loadAnaliseBalancos(ticker);
};

/**
 * Renderiza card de composição acionária
 */
function renderComposicaoAcionaria() {
    const card = document.getElementById('composicaoAcionariaCard');
    if (!card || !acionistasData) return;
    
    const acionistas = acionistasData.acionistas;
    const dataRef = acionistasData.data_referencia;
    
    // Calcula "Outros" (100% - soma dos top acionistas)
    const somaTop = acionistas.reduce((sum, a) => sum + a.percentual_total, 0);
    const outros = 100 - somaTop;
    
    // HTML do card
    let html = `
        <div class="composicao-header">
            <div class="composicao-icon">
                <i class="fas fa-users"></i>
            </div>
            <div class="composicao-title-group">
                <h3>Composição Acionária</h3>
                <p>Top ${acionistas.length} principais acionistas</p>
            </div>
        </div>
        
        <div class="composicao-content">
            <div class="chart-wrapper">
                <div class="chart-container">
                    <canvas id="acionistasChart"></canvas>
                </div>
            </div>
            
            <div class="acionistas-list">
    `;
    
    // Lista de acionistas
    acionistas.forEach((acionista, index) => {
        const acoesMilhoes = (acionista.acoes_total / 1000000).toFixed(1);
        
        html += `
            <div class="acionista-item">
                <div class="acionista-header">
                    <div class="acionista-posicao">${acionista.posicao}º</div>
                    <div class="acionista-nome">${acionista.nome}</div>
                    <div class="acionista-percentual">${acionista.percentual_total.toFixed(2)}%</div>
                </div>
                <div class="acionista-detalhes">
                    <div class="acionista-nacionalidade">
                        <i class="fas fa-flag"></i>
                        ${acionista.nacionalidade}
                    </div>
                    <div class="acionista-acoes">
                        ${acoesMilhoes}M ações
                    </div>
                </div>
            </div>
        `;
    });
    
    // Adiciona "Outros" se necessário
    if (outros > 0) {
        html += `
            <div class="acionista-item">
                <div class="acionista-header">
                    <div class="acionista-posicao" style="background: #94a3b8;">•</div>
                    <div class="acionista-nome">Outros Acionistas</div>
                    <div class="acionista-percentual">${outros.toFixed(2)}%</div>
                </div>
                <div class="acionista-detalhes">
                    <div class="acionista-nacionalidade">
                        <i class="fas fa-chart-pie"></i>
                        Free Float e Minoritários
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
        
        <div class="composicao-footer">
            <i class="fas fa-calendar-alt"></i>
            Dados referentes a ${formatDataReferencia(dataRef)}
        </div>
    `;
    
    card.innerHTML = html;
    card.style.display = 'block';
    
    // Renderiza gráfico
    renderAcionistasChart(acionistas, outros);
}

/**
 * Renderiza gráfico de pizza dos acionistas
 */
function renderAcionistasChart(acionistas, outros) {
    const ctx = document.getElementById('acionistasChart');
    
    if (!ctx) return;
    
    // Destroi gráfico anterior se existir
    if (acionistasChart) {
        acionistasChart.destroy();
    }
    
    // Prepara dados
    const labels = acionistas.map(a => a.nome);
    const data = acionistas.map(a => a.percentual_total);
    
    // Adiciona "Outros" se necessário
    if (outros > 0) {
        labels.push('Outros');
        data.push(outros);
    }
    
    // Cores personalizadas (gradiente visual)
    const cores = [
        'rgba(139, 92, 246, 0.8)',  // Roxo
        'rgba(236, 72, 153, 0.8)',  // Rosa
        'rgba(245, 158, 11, 0.8)',  // Laranja
        'rgba(16, 185, 129, 0.8)',  // Verde
        'rgba(148, 163, 184, 0.6)'  // Cinza (Outros)
    ];
    
    const coresBorda = [
        'rgba(139, 92, 246, 1)',
        'rgba(236, 72, 153, 1)',
        'rgba(245, 158, 11, 1)',
        'rgba(16, 185, 129, 1)',
        'rgba(148, 163, 184, 0.8)'
    ];
    
    // Cria gráfico
    acionistasChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: cores.slice(0, data.length),
                borderColor: coresBorda.slice(0, data.length),
                borderWidth: 3,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false  // Legenda desabilitada (lista ao lado já mostra)
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            return `${label}: ${value.toFixed(2)}%`;
                        }
                    }
                }
            },
            cutout: '60%',  // Estilo doughnut (anel)
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

/**
 * Formata data de referência
 */
function formatDataReferencia(dataStr) {
    if (!dataStr) return '-';
    
    const [ano, mes, dia] = dataStr.split('-');
    const meses = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ];
    
    const mesNome = meses[parseInt(mes, 10) - 1];
    return `${dia} de ${mesNome} de ${ano}`;
}

/**
 * HOOK: Adiciona carregamento de acionistas ao carregar ação
 */
const originalLoadAcaoDataWithAcionistas = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithAcionistas.call(this, ticker);
    
    // Carrega composição acionária após carregar a ação
    await loadAcionistasData(ticker);
};

/**
 * Renderiza seção completa de múltiplos
 */
function renderMultiplosSection() {
    const section = document.getElementById('multiplosSection');
    if (!section || !multiplosData) return;
    
    const ltm = multiplosData.ltm;
    const metadata = multiplosData.metadata;
    
    // Agrupa múltiplos por categoria
    const categorias = {
        'Valuation': [],
        'Rentabilidade': [],
        'Endividamento': [],
        'Liquidez': [],
        'Eficiência': []
    };
    
    for (const [codigo, meta] of Object.entries(metadata)) {
        const valor = ltm.multiplos[codigo];
        if (valor !== undefined && valor !== null) {
            categorias[meta.categoria].push({
                codigo: codigo,
                nome: meta.nome,
                valor: valor,
                unidade: meta.unidade,
                formula: meta.formula
            });
        }
    }
    
    // Gera HTML
    let html = `
        <div class="multiplos-header">
            <div class="multiplos-header-icon">
                <i class="fas fa-chart-pie"></i>
            </div>
            <div class="multiplos-header-text">
                <h3>Múltiplos Financeiros</h3>
                <p>Análise fundamentalista baseada em ${ltm.periodo_referencia}</p>
            </div>
            <div class="multiplos-timestamp">
                <i class="fas fa-clock"></i>
                Preço: R$ ${ltm.preco_utilizado.toFixed(2)} (${ltm.periodo_preco})
            </div>
        </div>
    `;
    
    // Renderiza cada categoria
    const iconesCategoria = {
        'Valuation': 'fa-dollar-sign',
        'Rentabilidade': 'fa-chart-line',
        'Endividamento': 'fa-balance-scale',
        'Liquidez': 'fa-tint',
        'Eficiência': 'fa-cogs'
    };
    
    for (const [categoria, multiplos] of Object.entries(categorias)) {
        if (multiplos.length === 0) continue;
        
        const categoriaClass = categoria.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        
        html += `
            <div class="multiplos-categoria">
                <div class="categoria-header">
                    <div class="categoria-icon ${categoriaClass}">
                        <i class="fas ${iconesCategoria[categoria]}"></i>
                    </div>
                    <h4 class="categoria-titulo">${categoria}</h4>
                </div>
                <div class="categoria-grid">
        `;
        
        multiplos.forEach(mult => {
            const valorFormatado = formatMultiploValor(mult.valor, mult.unidade);
            
            html += `
                <div class="multiplo-card">
                    <div class="multiplo-card-header">
                        <div class="multiplo-nome">${mult.nome}</div>
                        <button class="btn-historico" onclick="openMultiploModal('${mult.codigo}')">
                            <i class="fas fa-chart-area"></i>
                            Histórico
                        </button>
                    </div>
                    <div class="multiplo-valor">${valorFormatado}</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    section.innerHTML = html;
    section.style.display = 'block';
    
    // Cria modal (se não existe)
    createMultiploModal();
}

/**
 * Formata valor do múltiplo
 */
function formatMultiploValor(valor, unidade) {
    if (valor === null || valor === undefined) return 'N/D';
    
    if (unidade === '%') {
        return valor.toFixed(2) + '%';
    } else if (unidade === 'x') {
        return valor.toFixed(2) + 'x';
    } else if (unidade === 'dias') {
        return Math.round(valor);
    }
    
    return valor.toFixed(2);
}

/**
 * Cria modal para exibir histórico
 */
function createMultiploModal() {
    // Verifica se já existe
    if (document.getElementById('multiplo-modal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'multiplo-modal';
    modal.className = 'multiplo-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h3 id="modal-titulo">Título</h3>
                    <p id="modal-subtitulo">Subtítulo</p>
                </div>
                <button class="modal-close" onclick="closeMultiploModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="modal-info">
                    <div class="info-box">
                        <div class="info-label">Valor Atual (LTM)</div>
                        <div class="info-value" id="modal-valor-atual">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Média 5 Anos</div>
                        <div class="info-value" id="modal-media-5y">-</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Variação vs Média</div>
                        <div class="info-value" id="modal-variacao">-</div>
                    </div>
                </div>
                
                <div class="modal-chart-container">
                    <canvas id="modal-chart"></canvas>
                </div>
                
                <div class="modal-table-container">
                    <table class="multiplos-table">
                        <thead>
                            <tr>
                                <th>Ano</th>
                                <th>Valor</th>
                                <th>Variação</th>
                            </tr>
                        </thead>
                        <tbody id="modal-table-body"></tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Fecha ao clicar fora
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeMultiploModal();
        }
    });
}

/**
 * Abre modal com histórico do múltiplo
 */
function openMultiploModal(codigo) {
    if (!multiplosData) return;
    
    const modal = document.getElementById('multiplo-modal');
    const metadata = multiplosData.metadata[codigo];
    const historico = multiplosData.historico_anual;
    const ltmValor = multiplosData.ltm.multiplos[codigo];
    
    // Atualiza título
    document.getElementById('modal-titulo').textContent = metadata.nome;
    document.getElementById('modal-subtitulo').textContent = metadata.formula;
    
    // Calcula estatísticas
    const anos = Object.keys(historico).sort();
    const valores = anos.map(ano => historico[ano].multiplos[codigo]);
    const ultimos5Anos = valores.slice(-5);
    const media5y = ultimos5Anos.reduce((a, b) => a + b, 0) / ultimos5Anos.length;
    const variacao = ((ltmValor - media5y) / media5y * 100);
    
    // Atualiza info boxes
    document.getElementById('modal-valor-atual').textContent = formatMultiploValor(ltmValor, metadata.unidade);
    document.getElementById('modal-media-5y').textContent = formatMultiploValor(media5y, metadata.unidade);
    
    const varEl = document.getElementById('modal-variacao');
    varEl.textContent = (variacao >= 0 ? '+' : '') + variacao.toFixed(1) + '%';
    varEl.className = 'info-value ' + (variacao >= 0 ? 'positivo' : 'negativo');
    
    // Renderiza gráfico
    renderMultiploChart(anos, valores, metadata);
    
    // Renderiza tabela
    renderMultiploTable(anos, valores, metadata);
    
    // Mostra modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Fecha modal
 */
function closeMultiploModal() {
    const modal = document.getElementById('multiplo-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Destroi gráfico
    if (multiplosChart) {
        multiplosChart.destroy();
        multiplosChart = null;
    }
}

/**
 * Renderiza gráfico do histórico
 */
function renderMultiploChart(anos, valores, metadata) {
    const ctx = document.getElementById('modal-chart');
    
    if (multiplosChart) {
        multiplosChart.destroy();
    }
    
    multiplosChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: anos,
            datasets: [{
                label: metadata.nome,
                data: valores,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#4f46e5',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = metadata.nome + ': ';
                            label += formatMultiploValor(context.parsed.y, metadata.unidade);
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: metadata.unidade !== '%',
                    ticks: {
                        callback: function(value) {
                            if (metadata.unidade === '%') {
                                return value.toFixed(1) + '%';
                            } else if (metadata.unidade === 'x') {
                                return value.toFixed(1) + 'x';
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Renderiza tabela do histórico
 */
function renderMultiploTable(anos, valores, metadata) {
    const tbody = document.getElementById('modal-table-body');
    
    let html = '';
    for (let i = anos.length - 1; i >= 0; i--) {
        const ano = anos[i];
        const valor = valores[i];
        const valorAnterior = i > 0 ? valores[i - 1] : null;
        const variacao = valorAnterior ? ((valor - valorAnterior) / valorAnterior * 100) : null;
        
        html += `
            <tr>
                <td>${ano}</td>
                <td>${formatMultiploValor(valor, metadata.unidade)}</td>
                <td style="color: ${variacao > 0 ? '#10b981' : variacao < 0 ? '#ef4444' : '#6b7280'}">
                    ${variacao !== null ? (variacao >= 0 ? '+' : '') + variacao.toFixed(1) + '%' : '-'}
                </td>
            </tr>
        `;
    }
    
    tbody.innerHTML = html;
}

/**
 * HOOK: Adiciona carregamento de múltiplos ao carregar ação
 */
const originalLoadAcaoData = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoData.call(this, ticker);
    
    // Carrega múltiplos após carregar a ação
    await loadMultiplosData(ticker);
};

// Fecha modal ao pressionar ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeMultiploModal();
    }
});

// Atualiza informações da empresa
function updateEmpresaInfo(ticker) {
    const empresaInfo = mapeamentoB3.find(item => item.ticker === ticker);
    
    if (!empresaInfo) {
        console.warn('⚠️ Empresa não encontrada para ticker:', ticker);
        document.getElementById('empresaRazaoSocial').textContent = 'Não disponível';
        document.getElementById('empresaCNPJ').textContent = 'Não disponível';
        document.getElementById('empresaSetorSegmento').textContent = 'Não disponível';
        document.getElementById('empresaTickers').textContent = ticker;
        document.getElementById('empresaSede').textContent = 'Não disponível';
        document.getElementById('empresaDescricao').textContent = 'Informações não disponíveis.';
        document.getElementById('empresasMesmoSetor').textContent = 'Não disponível';
        return;
    }
    
    console.log('📋 Atualizando informações da empresa:', empresaInfo.empresa);
    
    // Preenche os campos
    document.getElementById('empresaRazaoSocial').textContent = empresaInfo.empresa || 'Não disponível';
    document.getElementById('empresaCNPJ').textContent = empresaInfo.cnpj || 'Não disponível';
    
    const setorSegmento = `${empresaInfo.setor || 'N/D'} / ${empresaInfo.segmento || 'N/D'}`;
    document.getElementById('empresaSetorSegmento').textContent = setorSegmento;
    
    // Mostra TODOS os tickers
    const todosTickersExibicao = empresaInfo.todosTickersStr || ticker;
    document.getElementById('empresaTickers').textContent = todosTickersExibicao;
    console.log('✅ Tickers exibidos:', todosTickersExibicao);
    
    document.getElementById('empresaSede').textContent = empresaInfo.sede || 'Não disponível';
    document.getElementById('empresaDescricao').textContent = empresaInfo.descricao || 'Descrição não disponível.';
    
    // Empresas do mesmo setor (sem duplicatas)
    const empresasUnicas = new Map();
    mapeamentoB3.forEach(item => {
        if (item.setor === empresaInfo.setor && item.empresa !== empresaInfo.empresa) {
            if (!empresasUnicas.has(item.empresa)) {
                empresasUnicas.set(item.empresa, item);
            }
        }
    });
    
    const mesmoSetor = Array.from(empresasUnicas.values())
        .slice(0, 5)
        .map(item => {
            const primeiroTicker = item.todosTickersStr 
                ? item.todosTickersStr.split(';')[0].trim()
                : item.ticker;
            return `<span class="ticker-similar" onclick="loadAcaoData('${primeiroTicker}')" style="cursor: pointer; color: #4f46e5; font-weight: 600; margin-right: 10px; text-decoration: underline;">${primeiroTicker}</span>`;
        })
        .join('');
    
    document.getElementById('empresasMesmoSetor').innerHTML = mesmoSetor || 'Nenhuma empresa encontrada';
}

// Atualiza indicadores
function updateIndicadores() {
    if (!acaoAtualData || !acaoAtualData.dados.length) return;
    
    const dados = acaoAtualData.dados;
    const ultimo = dados[dados.length - 1];
    const umAnoAtras = dados.length >= 252 ? dados[dados.length - 252] : dados[0];
    const doisAnosAtras = dados.length >= 504 ? dados[dados.length - 504] : dados[0];
    
    // Cotação atual
    document.getElementById('cotacaoAtual').textContent = `R$ ${ultimo.fechamento.toFixed(2)}`;
    
    // Variação 12M (252 dias úteis)
    const variacao12m = ((ultimo.fechamento - umAnoAtras.fechamento) / umAnoAtras.fechamento * 100).toFixed(2);
    const varEl = document.getElementById('variacao12m');
    varEl.textContent = `${variacao12m >= 0 ? '+' : ''}${variacao12m}% ${variacao12m >= 0 ? '↑' : '↓'}`;
    varEl.className = 'indicador-valor ' + (variacao12m >= 0 ? 'positivo' : 'negativo');
    
    // Variação 24M (504 dias úteis)
    const variacao24m = ((ultimo.fechamento - doisAnosAtras.fechamento) / doisAnosAtras.fechamento * 100).toFixed(2);
    const var24mEl = document.getElementById('variacao24m');
    var24mEl.textContent = `${variacao24m >= 0 ? '+' : ''}${variacao24m}% ${variacao24m >= 0 ? '↑' : '↓'}`;
    var24mEl.className = 'indicador-valor ' + (variacao24m >= 0 ? 'positivo' : 'negativo');
    
    // Tendência MM20
    const tendenciaMM20El = document.getElementById('tendenciaMM20');
    if (ultimo.mm20) {
        const distMM20 = ((ultimo.fechamento - ultimo.mm20) / ultimo.mm20 * 100).toFixed(1);
        if (distMM20 > 2) {
            tendenciaMM20El.innerHTML = '<span class="tendencia-icon">📈</span><span>Alta</span>';
            tendenciaMM20El.className = 'indicador-valor positivo';
        } else if (distMM20 < -2) {
            tendenciaMM20El.innerHTML = '<span class="tendencia-icon">📉</span><span>Baixa</span>';
            tendenciaMM20El.className = 'indicador-valor negativo';
        } else {
            tendenciaMM20El.innerHTML = '<span class="tendencia-icon">➡️</span><span>Lateral</span>';
            tendenciaMM20El.className = 'indicador-valor neutro';
        }
    } else {
        tendenciaMM20El.innerHTML = '<span>N/D</span>';
        tendenciaMM20El.className = 'indicador-valor';
    }
    
    // Tendência MM200
    const tendenciaMM200El = document.getElementById('tendenciaMM200');
    if (ultimo.mm200) {
        const distMM200 = ((ultimo.fechamento - ultimo.mm200) / ultimo.mm200 * 100).toFixed(1);
        if (distMM200 > 5) {
            tendenciaMM200El.innerHTML = '<span class="tendencia-icon">📈</span><span>Alta</span>';
            tendenciaMM200El.className = 'indicador-valor positivo';
        } else if (distMM200 < -5) {
            tendenciaMM200El.innerHTML = '<span class="tendencia-icon">📉</span><span>Baixa</span>';
            tendenciaMM200El.className = 'indicador-valor negativo';
        } else {
            tendenciaMM200El.innerHTML = '<span class="tendencia-icon">➡️</span><span>Lateral</span>';
            tendenciaMM200El.className = 'indicador-valor neutro';
        }
    } else {
        tendenciaMM200El.innerHTML = '<span>N/D</span>';
        tendenciaMM200El.className = 'indicador-valor';
    }
    
    // Médias móveis atuais
    document.getElementById('mm20Atual').textContent = ultimo.mm20 ? `R$ ${ultimo.mm20.toFixed(2)}` : 'N/D';
    document.getElementById('mm50Atual').textContent = ultimo.mm50 ? `R$ ${ultimo.mm50.toFixed(2)}` : 'N/D';
    document.getElementById('mm200Atual').textContent = ultimo.mm200 ? `R$ ${ultimo.mm200.toFixed(2)}` : 'N/D';
    
    // Preenche informações da empresa
    updateEmpresaInfo(acaoAtualData.ticker);
}

// Renderiza gráfico
function renderAcaoChart() {
    if (!acaoAtualData) return;
    
    const ctx = document.getElementById('acaoChart');
    
    // Destroi gráfico anterior
    if (acaoChart) {
        acaoChart.destroy();
    }
    
    // Filtra dados por período
    const dadosFiltrados = filterDataByPeriodo(acaoAtualData.dados, periodoAtual);
    
    // Prepara datasets
    const datasets = [
        {
            label: acaoAtualData.ticker,
            data: dadosFiltrados.map(d => d.fechamento),
            borderColor: '#4f46e5',
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            tension: 0.1,
            fill: true,
            yAxisID: 'y'
        }
    ];
    
    // Adiciona médias móveis
    if (dadosFiltrados.some(d => d.mm20)) {
        datasets.push({
            label: 'MM20',
            data: dadosFiltrados.map(d => d.mm20),
            borderColor: '#10b981',
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: 'y'
        });
    }
    
    if (dadosFiltrados.some(d => d.mm50)) {
        datasets.push({
            label: 'MM50',
            data: dadosFiltrados.map(d => d.mm50),
            borderColor: '#f59e0b',
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: 'y'
        });
    }
    
    if (dadosFiltrados.some(d => d.mm200)) {
        datasets.push({
            label: 'MM200',
            data: dadosFiltrados.map(d => d.mm200),
            borderColor: '#ef4444',
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: 'y'
        });
    }
    
    // Adiciona IBOV se habilitado
    if (ibovEnabled && ibovData) {
        const ibovFiltrado = filterDataByPeriodo(ibovData.dados, periodoAtual);
        datasets.push({
            label: 'IBOVESPA',
            data: ibovFiltrado.map(d => d.fechamento),
            borderColor: '#8b5cf6',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            yAxisID: 'y1'
        });
    }
    
    // Cria gráfico
    acaoChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dadosFiltrados.map(d => d.data),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += 'R$ ' + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toFixed(2);
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: ibovEnabled,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
}

// Filtra dados por período
function filterDataByPeriodo(dados, periodo) {
    if (periodo === 'max') return dados;
    
    const diasAtras = parseInt(periodo);
    return dados.slice(-diasAtras);
}

// Inicializa filtros de período
function initPeriodoFilters() {
    document.querySelectorAll('.periodo-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active de todos
            document.querySelectorAll('.periodo-btn').forEach(b => b.classList.remove('active'));
            
            // Adiciona active no clicado
            btn.classList.add('active');
            
            // Atualiza período
            periodoAtual = btn.dataset.periodo;
            
            // Re-renderiza gráfico
            renderAcaoChart();
        });
    });
}

// Inicializa toggle IBOV
function initToggleIbov() {
    const btn = document.getElementById('toggleIbovBtn');
    
    btn.addEventListener('click', () => {
        ibovEnabled = !ibovEnabled;
        btn.classList.toggle('active');
        renderAcaoChart();
    });
}
