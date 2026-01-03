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
        'monalytics.netlify.app',
        'projeto-monalytics.netlify.app',
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
    GITHUB_RAW: 'https://raw.githubusercontent.com/asiqueira013/Projeto_Monalytics',
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
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            },
            // Modo de segurança
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
