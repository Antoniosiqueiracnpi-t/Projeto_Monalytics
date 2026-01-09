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
  if (!header) return;
  if (window.scrollY > 50) header.classList.add('scrolled');
  else header.classList.remove('scrolled');
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
            // const headerHeight = header.offsetHeight;
            const headerHeight = header ? header.offsetHeight : 0;
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

// =========================== MAPEAMENTO B3 → CARD DA EMPRESA ===========================

// Caminho já definido no topo:
// const MAPEAMENTO_B3_PATH = 'mapeamento_b3_consolidado.csv';

let MAPA_EMPRESAS_B3 = null;

/**
 * Parser CSV para mapeamento B3
 * ESTRUTURA: ticker;empresa;cnpj;setor;segmento;sede;descricao (7 COLUNAS)
 */
function parseMapeamentoB3(csvText) {
    const linhas = csvText.split(/\r?\n/).filter(l => l.trim() !== '');
    
    if (linhas.length === 0) {
        console.error('❌ CSV vazio!');
        return {};
    }
    
    // Remove BOM UTF-8 se existir
    linhas[0] = linhas[0].replace(/^\uFEFF/, '');
    
    /**
     * Parser de linha CSV que respeita aspas duplas
     */
    function parseCSVLine(linha) {
        const campos = [];
        let campoAtual = '';
        let dentroDeAspas = false;
        
        for (let i = 0; i < linha.length; i++) {
            const char = linha[i];
            const proximoChar = linha[i + 1];
            
            if (char === '"') {
                if (dentroDeAspas && proximoChar === '"') {
                    // Aspas duplas escapadas ("") → uma aspa literal
                    campoAtual += '"';
                    i++; // Pula a segunda aspa
                } else {
                    // Alterna estado de aspas
                    dentroDeAspas = !dentroDeAspas;
                }
            } else if (char === ';' && !dentroDeAspas) {
                // Fim do campo
                campos.push(campoAtual.trim());
                campoAtual = '';
            } else {
                campoAtual += char;
            }
        }
        
        // Adiciona último campo
        campos.push(campoAtual.trim());
        return campos;
    }
    
    // Processa header
    const headerLinha = linhas.shift();
    const header = parseCSVLine(headerLinha).map(s => s.toLowerCase().trim());
    
    console.log('📋 Header CSV:', header);
    
    // VALIDAÇÃO: Estrutura exata
    const estruturaEsperada = ['ticker', 'empresa', 'cnpj', 'setor', 'segmento', 'sede', 'descricao'];
    
    if (header.length !== 7) {
        console.error('❌ CSV deve ter 7 colunas! Recebido:', header.length);
        console.error('Header:', header);
        return {};
    }
    
    const estruturaValida = estruturaEsperada.every((col, idx) => header[idx] === col);
    
    if (!estruturaValida) {
        console.error('❌ Estrutura incorreta!');
        console.error('Esperado:', estruturaEsperada);
        console.error('Recebido:', header);
        return {};
    }
    
    // Índices FIXOS (não usar indexOf!)
    const IDX_TICKER = 0;
    const IDX_EMPRESA = 1;
    const IDX_CNPJ = 2;
    const IDX_SETOR = 3;
    const IDX_SEGMENTO = 4;
    const IDX_SEDE = 5;
    const IDX_DESCRICAO = 6;
    
    const mapa = {};
    let linhasProcessadas = 0;
    
    for (const linha of linhas) {
        if (!linha.trim()) continue;
        
        const cols = parseCSVLine(linha);
        
        // Valida número de campos
        if (cols.length !== 7) {
            console.warn(`⚠️ Linha com ${cols.length} campos (esperado 7) - ignorada`);
            continue;
        }
        
        const tickerRaw = cols[IDX_TICKER];
        if (!tickerRaw) continue;
        
        // Múltiplos tickers separados por ; ou ,
        const tickers = tickerRaw
            .split(/[;,]/)
            .map(t => t.trim().toUpperCase())
            .filter(t => t.length > 0);
        
        // CORREÇÃO: Armazena TODOS os tickers formatados para exibição
        const tickersNegociacao = tickers.join(', ');
        
        const dadosEmpresa = {
            ticker: tickers[0],                    // Ticker principal (para compatibilidade)
            tickersNegociacao: tickersNegociacao,  // NOVO: Todos os tickers da empresa
            empresa: cols[IDX_EMPRESA].trim(),
            cnpj: cols[IDX_CNPJ].trim(),
            setor: cols[IDX_SETOR].trim(),
            segmento: cols[IDX_SEGMENTO].trim(),
            sede: cols[IDX_SEDE].trim(),
            descricao: cols[IDX_DESCRICAO].trim()
        };
        
        // Mapeia todos os tickers para os mesmos dados da empresa
        tickers.forEach(ticker => {
            mapa[ticker] = { ...dadosEmpresa, ticker };
        });
        
        linhasProcessadas++;
    }
    
    console.log(`✅ Parsing completo:`);
    console.log(`   Empresas: ${linhasProcessadas}`);
    console.log(`   Tickers: ${Object.keys(mapa).length}`);
    
    return mapa;
}




/**
 * Valida dados carregados
 */
function validarMapeamentoB3(mapa) {
    if (!mapa || Object.keys(mapa).length === 0) {
        console.error('❌ Mapa vazio!');
        return false;
    }
    
    // Testa PETR4
    const petr4 = mapa['PETR4'];
    if (!petr4) {
        console.error('❌ PETR4 não encontrado!');
        return false;
    }
    
    console.log('🧪 VALIDAÇÃO PETR4:');
    console.log('   Empresa:', petr4.empresa);
    console.log('   CNPJ:', petr4.cnpj);
    console.log('   Setor:', petr4.setor);
    console.log('   Segmento:', petr4.segmento);
    console.log('   Sede:', petr4.sede.substring(0, 50) + '...');
    
    // Validações
    const camposObrigatorios = ['ticker', 'empresa', 'cnpj', 'setor', 'segmento', 'sede', 'descricao'];
    const camposFaltando = camposObrigatorios.filter(campo => !(campo in petr4));
    
    if (camposFaltando.length > 0) {
        console.error('❌ Campos faltando:', camposFaltando);
        return false;
    }
    
    // NÃO deve ter codigo_cvm
    if ('codigo_cvm' in petr4) {
        console.error('❌ Campo "codigo_cvm" não deveria existir!');
        return false;
    }
    
    // Setor/Segmento podem variar conforme seu CSV (não travar por valor fixo)
    if (!petr4.setor || !petr4.segmento) {
        console.error('❌ PETR4 sem setor/segmento:', petr4.setor, petr4.segmento);
        return false;
    }

    
    console.log('✅ Validação PETR4 OK!');
    return true;
}




/**
 * Carrega CSV do mapeamento B3 direto do GitHub RAW
 * VERSÃO CORRIGIDA - Sem dependência de fetchFromGitHub
 */
async function carregarMapeamentoB3() {
    try {
        console.log('📡 Carregando mapeamento B3...');
        
        // URL direta do CSV no GitHub
        const csvUrl = `https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/${MAPEAMENTO_B3_PATH}?t=${Date.now()}`;
        
        console.log('URL:', csvUrl);
        
        // Fetch direto (CSV não usa MonalyticsSecure porque é texto, não JSON)
        const response = await fetch(csvUrl, {
            cache: 'no-store',
            mode: 'cors'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const csvText = await response.text();
        console.log('CSV baixado:', csvText.substring(0, 200) + '...');
        
        // Parse do CSV
        MAPA_EMPRESAS_B3 = parseMapeamentoB3(csvText);
        
        // Validação
        if (!validarMapeamentoB3(MAPA_EMPRESAS_B3)) {
            throw new Error('Validação dos dados falhou!');
        }
        
        console.log('✅ Mapeamento B3 carregado e validado!');
        
    } catch (err) {
        console.error('❌ Erro fatal ao carregar mapeamento:', err);
        alert('⚠️ Erro ao carregar dados das empresas. Recarregue a página.');
    }
}




/**
 * Atualiza o card de informações da empresa a partir do ticker selecionado.
 * tickerSelecionado: string, ex: "BEEF3"
 */
function atualizarCardEmpresa(tickerSelecionado) {
    if (!MAPA_EMPRESAS_B3 || !tickerSelecionado) return;
    
    const ticker = tickerSelecionado.toUpperCase();
    const info = MAPA_EMPRESAS_B3[ticker];
    
    if (!info) {
        console.warn(`⚠️ Ticker ${ticker} não encontrado no mapeamento`);
        return;
    }
    
    // 1. Razão social
    const razaoEl = document.getElementById('empresaRazaoSocial');
    if (razaoEl) razaoEl.textContent = info.empresa || '-';
    
    // 2. CNPJ
    const cnpjEl = document.getElementById('empresaCNPJ');
    if (cnpjEl) cnpjEl.textContent = info.cnpj || '-';
    
    // 3. Setor / Segmento
    const setorSegEl = document.getElementById('empresaSetorSegmento');
    if (setorSegEl) {
        const setor = info.setor || '';
        const segmento = info.segmento || '';
        setorSegEl.textContent = (setor && segmento) 
            ? `${setor} / ${segmento}` 
            : (setor || segmento || '-');
    }
    
    // 4. Tickers de negociação - CORREÇÃO: Usa tickersNegociacao com todos os tickers
    const tickersEl = document.getElementById('empresaTickers');
    if (tickersEl) {
        tickersEl.textContent = info.tickersNegociacao || info.ticker || ticker;
    }
    
    // 5. Endereço da sede
    const sedeEl = document.getElementById('empresaSede');
    if (sedeEl) {
        sedeEl.textContent = info.sede || '-';
    }
    
    // 6. Descrição
    const descEl = document.getElementById('empresaDescricao');
    if (descEl) descEl.textContent = info.descricao || '-';
    
    // 7. Empresas do mesmo setor - CORREÇÃO: Filtra por CNPJ para evitar duplicatas
    const mesmoSetorEl = document.getElementById('empresasMesmoSetor');
    if (mesmoSetorEl) {
        mesmoSetorEl.innerHTML = '';
        const setorRef = info.setor;
        const cnpjAtual = info.cnpj;
        
        if (setorRef) {
            // Usar Set para garantir CNPJs únicos e evitar empresas duplicadas
            const cnpjsExibidos = new Set();
            
            Object.values(MAPA_EMPRESAS_B3)
                .filter(e => {
                    // Mesmo setor, CNPJ diferente, e CNPJ ainda não exibido
                    if (e.setor !== setorRef) return false;
                    if (e.cnpj === cnpjAtual) return false;
                    if (cnpjsExibidos.has(e.cnpj)) return false;
                    
                    cnpjsExibidos.add(e.cnpj);
                    return true;
                })
                .slice(0, 12)
                .forEach(e => {
                    const a = document.createElement('a');
                    a.href = '#analise-acoes';
                    a.className = 'ticker-similar';
                    a.textContent = e.ticker;
                    a.addEventListener('click', evt => {
                        evt.preventDefault();
                        if (typeof selecionarTicker === 'function') {
                            selecionarTicker(e.ticker);
                        }
                    });
                    mesmoSetorEl.appendChild(a);
                });
        }
    }
    
    console.log(`✅ Card atualizado para ${ticker}:`, info);
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


// =========================== UTIL: TICKER NORMALIZAÇÃO & PASTA ===========================
/**
 * Normaliza ticker (trim + UPPER).
 */
function normalizarTicker(t) {
    return String(t || '').trim().toUpperCase();
}

/**
 * Retorna o ticker da PASTA (balancos/<TICKER_PASTA>/) para um ticker selecionado.
 * - Para empresas com múltiplas classes (3/4/11 etc), usamos o primeiro ticker da linha do CSV (ticker_pasta).
 * - Mantém compatibilidade com a base antiga usando todosTickersStr quando ticker_pasta não existir.
 */
function obterTickerPasta(ticker) {
    const t = normalizarTicker(ticker);
    if (!Array.isArray(mapeamentoB3) || !mapeamentoB3.length) return t;

    const info = mapeamentoB3.find(item => normalizarTicker(item && item.ticker) === t);
    if (!info) return t;

    const fallback = info.todosTickersStr ? String(info.todosTickersStr).split(/[;\/ ,]+/)[0] : '';
    const pasta = normalizarTicker(info.ticker_pasta || fallback || t);
    return pasta || t;
}


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
    const sorted = [...(feed || [])].sort((a, b) => {
        const prioA = priorities?.[a?.noticia?.categoria] ?? 99;
        const prioB = priorities?.[b?.noticia?.categoria] ?? 99;

        if (prioA !== prioB) return prioA - prioB;

        const dateA = a?.data || '';
        const dateB = b?.data || '';
        const dateCompare = dateB.localeCompare(dateA);
        if (dateCompare !== 0) return dateCompare;

        const horaA = a?.hora || '';
        const horaB = b?.hora || '';
        return horaB.localeCompare(horaA);
    });

    // Remove duplicatas por ticker
    const seen = new Set();
    const unique = sorted.filter(item => {
        const t = item?.empresa?.ticker;
        if (!t) return false;
        if (seen.has(t)) return false;
        seen.add(t);
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
    
    //carregarMapeamentoB3();
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
        
        // Detecta header para suportar 7 ou 8 colunas
        const header = (rows[0] || []).map(h => String(h).toLowerCase().trim());
        const hasCodigoCvm = header.includes('codigo_cvm') || header.includes('código_cvm');
        
        // Remove header e linhas vazias
        // CSV (7 colunas): ticker;empresa;cnpj;setor;segmento;sede;descricao
        const rawData = rows.slice(1)
            .filter(row => row.length >= 2 && row[0] && row[1])
            .map(row => ({
                ticker: row[0] || '',
                empresa: row[1] || '',
                cnpj: row[2] || '',
                codigo_cvm: '', // mantido por compatibilidade (CSV atual não possui essa coluna)
                setor: row[3] || '',
                segmento: row[4] || '',
                sede: row[5] || '',
                descricao: row[6] || ''
            }));

        
        console.log(`📊 Empresas carregadas: ${rawData.length}`);

        // Expande empresas com múltiplos tickers
        mapeamentoB3 = [];
        rawData.forEach(item => {
            const tickers = String(item.ticker || '')
                .split(/[;\/ ,]+/) // aceita ; , / e espaços como separador
                .map(t => t.trim().toUpperCase())
                .filter(Boolean);
        
            if (!tickers.length) return;
        
            // String padrão para exibição/lookup (sempre com ';')
            const todosTickersStr = tickers.join(';');
            // Pasta principal: 1º ticker da linha do CSV
            const ticker_pasta = tickers[0];
        
            tickers.forEach(ticker => {
                mapeamentoB3.push({
                    ticker: ticker,
                    ticker_pasta: ticker_pasta,
                    empresa: item.empresa,
                    cnpj: item.cnpj,
                    codigo_cvm: item.codigo_cvm || '',
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
        
        // Normaliza ticker recebido
        const t = String(ticker || '').trim().toUpperCase();
        
        // Busca info da empresa no mapeamento (comparação normalizada)
        const empresaInfo = mapeamentoB3.find(item => String(item.ticker || '').trim().toUpperCase() === t);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${t} não encontrado no mapeamento B3`);
        }
        
        console.log('✅ Empresa encontrada:', empresaInfo.empresa);
        
        // Usa SEMPRE a pasta principal calculada no mapeamento
        const tickerPasta = (empresaInfo.ticker_pasta && empresaInfo.ticker_pasta.trim())
            ? empresaInfo.ticker_pasta.trim().toUpperCase()
            : t;
        
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


// ============================================================================
// HOOKS DE CARREGAMENTO SEQUENCIAL - ORDEM CRÍTICA!
// ============================================================================

// HOOK 1: Acionistas
const originalLoadAcaoDataWithAcionistas = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithAcionistas.call(this, ticker);
    
    // Carrega composição acionária
    await loadAcionistasData(ticker);
};

// HOOK 2: Múltiplos (DEVE VIR ANTES DO COMPARADOR!)
const originalLoadAcaoDataWithMultiplos = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithMultiplos.call(this, ticker);
    
    // Carrega múltiplos financeiros
    await loadMultiplosData(ticker);
};

// HOOK 3: Dividendos
const originalLoadAcaoDataWithDividendos = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithDividendos.call(this, ticker);
    
    // Carrega histórico de dividendos
    await loadDividendosHistorico(ticker);
};

// HOOK 4: Análise I.A
const originalLoadAcaoDataWithIA = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithIA.call(this, ticker);
    
    // Carrega análise automática
    await loadAnaliseBalancos(ticker);
};

// HOOK 5: Comparador (POR ÚLTIMO!)
const originalLoadAcaoDataWithComparador = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataWithComparador.call(this, ticker);
    
    // Aguarda 500ms para garantir que multiplosData foi processada
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Carrega comparador de ações
    await carregarComparador(ticker);
};

console.log('✅ Hooks de carregamento inicializados na ordem correta');






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
        
        const tickerNorm = normalizarTicker(ticker);
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }
        
        const tickerPasta = obterTickerPasta(ticker);
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/multiplos.json?t=${timestamp}`);
        
        if (!response.ok) {
            // ✅ NOVO: Se não encontrar multiplos.json, avisa mas não quebra
            console.warn(`⚠️ Múltiplos não encontrados para ${ticker} (HTTP ${response.status})`);
            document.getElementById('multiplosSection').style.display = 'none';
            return;  // ✅ Retorna sem quebrar o fluxo
        }
        
        multiplosData = await response.json();
        console.log(`✅ Múltiplos carregados: ${Object.keys(multiplosData.ltm.multiplos).length}`);
        renderMultiplosSection();
        
    } catch (error) {
        console.error('Erro ao carregar múltiplos:', error);
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
        
        const tickerNorm = normalizarTicker(ticker);
        
        // Busca info da empresa no mapeamento (comparação normalizada)
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item && item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }
        const tickerPasta = obterTickerPasta(ticker);
        
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
        
        const tickerNorm = normalizarTicker(ticker);
        
        // Busca info da empresa no mapeamento (comparação normalizada)
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item && item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }
        const tickerPasta = obterTickerPasta(ticker);
        
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
                <p>Principais acionistas</p>
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
    
    // ✅ CORREÇÃO: Lista apenas os TOP 5 maiores acionistas
    const top5Acionistas = acionistas.slice(0, 5);
    
    top5Acionistas.forEach((acionista, index) => {
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

// ================================================================
// DETECTOR DE SETOR FINANCEIRO
// Verifica se empresa é intermediário financeiro para ajustar múltiplos
// ================================================================
/**
 * Verifica se empresa é intermediário financeiro para ajustar múltiplos
 */
function isIntermediarioFinanceiro(ticker) {
    if (!Array.isArray(mapeamentoB3) || mapeamentoB3.length === 0 || !ticker) {
        return false;
    }
    
    const tickerNorm = normalizarTicker(ticker);
    
    // Busca empresa no array mapeamentoB3
    const empresaInfo = mapeamentoB3.find(e => normalizarTicker(e.ticker) === tickerNorm);
    
    if (!empresaInfo) {
        console.warn(`⚠️ Ticker ${tickerNorm} não encontrado no mapeamento para detecção de setor`);
        return false;
    }
    
    // Lista de setores considerados intermediários financeiros
    const setoresFinanceiros = [
        'INTERMEDIÁRIOS FINANCEIROS',
        'INTERMEDIARIOS FINANCEIROS',
        'BANCOS',
        'SERVIÇOS FINANCEIROS',
        'SERVICOS FINANCEIROS',
        'SEGURADORAS',
        'PREVIDÊNCIA',
        'PREVIDENCIA'
    ];
    
    const setorNormalizado = empresaInfo.setor.toUpperCase().trim();
    const ehFinanceira = setoresFinanceiros.some(sf => setorNormalizado.includes(sf));
    
    console.log(`🏦 ${ticker} → Setor: "${empresaInfo.setor}" → Financeira: ${ehFinanceira}`);
    
    return ehFinanceira;
}





/**
 * Renderiza seção completa de múltiplos
 */
function renderMultiplosSection() {
    const section = document.getElementById('multiplosSection');
    if (!section || !multiplosData) return;
    
    const ltm = multiplosData.ltm;
    const metadata = multiplosData.metadata;
    
    // ✅ CORREÇÃO: Usa acaoAtualData.ticker que é o ticker atual carregado
    const ehFinanceira = isIntermediarioFinanceiro(acaoAtualData.ticker);
    console.log(`🏦 Empresa ${acaoAtualData.ticker} é financeira? ${ehFinanceira}`);
    
    // Agrupa múltiplos por categoria
    const categorias = {
        'Valuation': [],
        'Rentabilidade': [],
        'Endividamento': [],
        'Liquidez': [],
        'Eficiência': [],
        'Estrutura': []
    };
    
    for (const [codigo, meta] of Object.entries(metadata)) {
        const valor = ltm.multiplos[codigo];
        
        if (valor !== undefined && valor !== null) {
            // ✅ FILTRO ESPECÍFICO PARA INTERMEDIÁRIOS FINANCEIROS
            if (ehFinanceira) {
                // REMOVE Margem Líquida para financeiras
                if (codigo === 'MARGEM_LIQUIDA') {
                    console.log(`⚠️ Ignorando ${codigo} - não aplicável para financeiras`);
                    continue; // Pula este múltiplo
                }
                // ADICIONA PL_Ativos para financeiras
                if (codigo === 'PL_ATIVOS') {
                    console.log(`✅ Incluindo ${codigo} - específico para financeiras`);
                }
            } else {
                // REMOVE PL_Ativos para NÃO-financeiras
                if (codigo === 'PL_ATIVOS') {
                    console.log(`⚠️ Ignorando ${codigo} - apenas para financeiras`);
                    continue; // Pula este múltiplo
                }
            }
            
            // Adiciona múltiplo à categoria correspondente
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
        'Eficiência': 'fa-cogs',
        'Estrutura': 'fa-building' // ✅ NOVO: Ícone para PL/Ativos
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

/* ========================================
   HISTÓRICO DE DIVIDENDOS
   ======================================== */

let dividendosHistoricoData = null;
let dividendosChart = null;
let currentDividendosView = 'dy'; // 'dy' ou 'pagos'
let currentDividendosPeriod = 5; // 5 ou 10 anos

/**
 * Carrega DY atual do arquivo multiplos.json
 */
async function carregarDYAtual(ticker) {
    try {
        const tickerNorm = normalizarTicker(ticker);
        
        // Busca info da empresa no mapeamento (comparação normalizada)
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item && item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }
        const tickerPasta = obterTickerPasta(ticker);
        
        console.log(`🔍 Buscando DY em multiplos.json (ticker: ${tickerPasta})...`);
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/multiplos.json?t=${timestamp}`);
        
        if (response.ok) {
            const multiplosData = await response.json();
            
            // ✅ ACESSO CORRETO: multiplosData.ltm.multiplos.DY
            if (multiplosData?.ltm?.multiplos?.DY) {
                const dyAtual = multiplosData.ltm.multiplos.DY;
                
                // ✅ Atribuição robusta
                if (dividendosHistoricoData) {
                    dividendosHistoricoData.dy_atual = dyAtual;
                }
                
                console.log(`✅ DY atual carregado: ${dyAtual.toFixed(2)}%`);
                return dyAtual;
            } else {
                console.log('⚠️ DY não encontrado em multiplos.ltm.multiplos.DY, usando 0');
                if (dividendosHistoricoData) {
                    dividendosHistoricoData.dy_atual = 0;
                }
                return 0;
            }
        } else {
            console.log(`⚠️ Arquivo multiplos.json não encontrado (${response.status})`);
            if (dividendosHistoricoData) {
                dividendosHistoricoData.dy_atual = 0;
            }
            return 0;
        }
        
    } catch (error) {
        console.log('⚠️ Erro ao buscar DY atual:', error.message);
        if (dividendosHistoricoData) {
            dividendosHistoricoData.dy_atual = 0;
        }
        return 0;
    }
}

/**
 * Carrega DY histórico do arquivo multiplos.json
 */
async function carregarDYHistorico(ticker) {
    try {
        const tickerNorm = normalizarTicker(ticker);
        
        // Busca info da empresa no mapeamento (comparação normalizada)
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item && item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }
        const tickerPasta = obterTickerPasta(ticker);
        
        console.log(`📈 Buscando DY histórico em multiplos.json (ticker: ${tickerPasta})...`);
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/multiplos.json?t=${timestamp}`);
        
        if (response.ok) {
            const multiplosData = await response.json();
            
            // ✅ Extrai DY de cada ano do histórico
            const historicoAnual = multiplosData.historico_anual || {};
            
            for (const ano in historicoAnual) {
                const dyAno = historicoAnual[ano].multiplos?.DY;
                
                if (dyAno !== undefined && dyAno !== null) {
                    // Atualiza dy_percent no historico_anos correspondente
                    const anoObj = dividendosHistoricoData.historico_anos.find(
                        a => a.ano === parseInt(ano)
                    );
                    
                    if (anoObj) {
                        anoObj.dy_percent = dyAno;
                        console.log(`   ✅ ${ano}: ${dyAno.toFixed(2)}%`);
                    }
                }
            }
            
            console.log('✅ DY histórico atualizado de multiplos.json');
        }
        
    } catch (error) {
        console.warn('⚠️ Erro ao carregar DY histórico:', error);
    }
}


/**
 * Carrega e processa histórico de dividendos
 */
async function loadDividendosHistorico(ticker) {
    try {
        console.log(`💰 Carregando histórico de dividendos de ${ticker}...`);
        
        const timestamp = new Date().getTime();
        const response = await fetch(`https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/agenda_dividendos_acoes_investidor10.json?t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Arquivo de dividendos não encontrado`);
        }
        
        const allData = await response.json();
        console.log('📦 Arquivo carregado:', allData.length, 'registros');
        
        // Filtra dividendos do ticker específico
        const dividendosDoTicker = allData.filter(d => d.ticker === ticker);
        
        if (dividendosDoTicker.length === 0) {
            console.warn(`⚠️ Nenhum dividendo encontrado para ${ticker}`);
            document.getElementById('dividendosHistoricoSection').style.display = 'none';
            return;
        }
        
        console.log(`✅ Encontrados ${dividendosDoTicker.length} dividendos de ${ticker}`);
        
        // Agrupa por ano e processa
        dividendosHistoricoData = processarDividendosPorAno(dividendosDoTicker, ticker);
        
        // Busca DY atual de multiplos.json
        await carregarDYAtual(ticker);
        await carregarDYHistorico(ticker);        
        renderDividendosHistorico();
        
    } catch (error) {
        console.error('❌ Erro ao carregar dividendos:', error);
        document.getElementById('dividendosHistoricoSection').style.display = 'none';
    }
}

/**
 * Processa array de dividendos e agrupa por ano
 */
function processarDividendosPorAno(dividendos, ticker) {
    // Agrupa por ano
    const dividendosPorAno = {};
    
    dividendos.forEach(div => {
        const ano = div.ano_ref || new Date(div.data_com).getFullYear();
        
        if (!dividendosPorAno[ano]) {
            dividendosPorAno[ano] = [];
        }
        
        dividendosPorAno[ano].push({
            tipo: div.tipo || div.tipo_raw || 'Dividendos',
            valor: div.valor,
            data_com: formatarData(div.data_com_raw || div.data_com),
            data_pagamento: formatarData(div.data_pagamento_raw || div.data_pagamento)
        });
    });
    
    // Converte para array de anos com totais
    const historico_anos = Object.keys(dividendosPorAno)
        .sort((a, b) => a - b)
        .map(ano => {
            const divsAno = dividendosPorAno[ano];
            const valor_total = divsAno.reduce((sum, d) => sum + d.valor, 0);
            
            return {
                ano: parseInt(ano),
                valor_total: valor_total,
                dy_percent: 0, // Será calculado depois se tivermos o preço
                dividendos: divsAno
            };
        });
    
    return {
        ticker: ticker,
        dy_atual: 0, // Será sobrescrito por multiplos.json
        historico_anos: historico_anos
    };
}

/**
 * Formata data para padrão brasileiro
 */
function formatarData(data) {
    if (!data) return '';
    
    // Se já está no formato DD/MM/YYYY
    if (data.includes('/')) {
        const partes = data.split('/');
        if (partes[2].length === 2) {
            // Converte YY para YYYY
            partes[2] = '20' + partes[2];
        }
        return partes.join('/');
    }
    
    // Se está no formato YYYY-MM-DD
    if (data.includes('-')) {
        const partes = data.split('-');
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    
    return data;
}

/**
 * Renderiza seção de histórico de dividendos
 */
function renderDividendosHistorico() {
    const section = document.getElementById('dividendosHistoricoSection');
    if (!section || !dividendosHistoricoData) return;
    
    const data = dividendosHistoricoData;
    
    // HTML principal
    let html = `
        <div class="dividendos-hist-header">
            <div class="dividendos-hist-title-group">
                <div class="dividendos-hist-icon">
                    <i class="fas fa-hand-holding-usd"></i>
                </div>
                <div>
                    <h3>Histórico de Dividendos - ${data.ticker}</h3>
                    <p>Acompanhamento de proventos e dividend yield</p>
                </div>
            </div>
            
            <div class="dividendos-hist-controls">
                <div class="dividendos-view-switch">
                    <button class="view-switch-btn ${currentDividendosView === 'dy' ? 'active' : ''}" 
                            onclick="toggleDividendosView('dy')">
                        DIVIDEND YIELD
                    </button>
                    <button class="view-switch-btn ${currentDividendosView === 'pagos' ? 'active' : ''}" 
                            onclick="toggleDividendosView('pagos')">
                        DIVIDENDOS PAGOS
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="dividendos-stats">
            <div class="dividendos-stat-card">
                <div class="stat-label">DY Atual</div>
                <div class="stat-value">${data.dy_atual ? data.dy_atual.toFixed(2) + '%' : 'N/D'}</div>
            </div>
            <div class="dividendos-stat-card">
                <div class="stat-label">DY Médio (2020-2025)</div>
                <div class="stat-value">${calcularDYMedio().toFixed(2)}%</div>
            </div>
        </div>
        
        <!-- Gráfico -->
        <div class="dividendos-chart-wrapper">
            <div class="dividendos-chart-container">
                <canvas id="dividendosHistoricoChart"></canvas>
            </div>
        </div>
        
        <!-- Tabela -->
        <div class="dividendos-table-container" id="dividendosTableContainer">
            <!-- Será preenchida pela função renderDividendosTable -->
        </div>
    `;
    
    section.innerHTML = html;
    section.style.display = 'block';
    
    // Renderiza gráfico
    renderDividendosChart();
    
    // Renderiza tabela
    renderDividendosTable();
}

/**
 * Calcula DY médio do período selecionado
 */
function calcularDYMedio() {
    if (!dividendosHistoricoData) return 0;
    
    const anos = dividendosHistoricoData.historico_anos.filter(a => a.dy_percent > 0);
    
    if (anos.length === 0) return 0;
    
    const soma = anos.reduce((sum, a) => sum + a.dy_percent, 0);
    return soma / anos.length;
}

/**
 * Renderiza gráfico de dividendos
 */
function renderDividendosChart() {
    const ctx = document.getElementById('dividendosHistoricoChart');
    if (!ctx || !dividendosHistoricoData) return;
    
    // Destroi gráfico anterior
    if (dividendosChart) {
        dividendosChart.destroy();
    }
    
    // Filtra dados do período
    const dadosPeriodo = dividendosHistoricoData.historico_anos.slice(-currentDividendosPeriod);
    
    const labels = dadosPeriodo.map(d => d.ano.toString());
    let datasets = [];
    
    if (currentDividendosView === 'dy') {
        // Gráfico de Dividend Yield
        datasets = [{
            label: 'Dividend Yield (%)',
            data: dadosPeriodo.map(d => d.dy_percent),
            backgroundColor: 'rgba(16, 185, 129, 0.8)',
            borderColor: 'rgba(16, 185, 129, 1)',
            borderWidth: 2,
            borderRadius: 8,
            hoverBackgroundColor: 'rgba(16, 185, 129, 0.95)'
        }];
    } else {
        // Gráfico de Dividendos Pagos
        datasets = [{
            label: 'Dividendos Pagos (R$)',
            data: dadosPeriodo.map(d => d.valor_total),
            backgroundColor: 'rgba(139, 92, 246, 0.8)',
            borderColor: 'rgba(139, 92, 246, 1)',
            borderWidth: 2,
            borderRadius: 8,
            hoverBackgroundColor: 'rgba(139, 92, 246, 0.95)'
        }];
    }
    
    dividendosChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
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
                            const value = context.parsed.y;
                            if (currentDividendosView === 'dy') {
                                return `DY: ${value.toFixed(2)}%`;
                            } else {
                                return `Dividendos: R$ ${value.toFixed(2)}`;
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            if (currentDividendosView === 'dy') {
                                return value.toFixed(1) + '%';
                            } else {
                                return 'R$ ' + value.toFixed(2);
                            }
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Renderiza tabela de dividendos
 */
function renderDividendosTable() {
    const container = document.getElementById('dividendosTableContainer');
    if (!container || !dividendosHistoricoData) return;
    
    // Coleta todos os dividendos
    const todosDividendos = [];
    dividendosHistoricoData.historico_anos.forEach(ano => {
        ano.dividendos.forEach(div => {
            todosDividendos.push({
                ...div,
                ano: ano.ano
            });
        });
    });
    
    // Ordena por data_com (mais recente primeiro)
    todosDividendos.sort((a, b) => {
        const dateA = parseDataBR(a.data_com);
        const dateB = parseDataBR(b.data_com);
        return dateB - dateA;
    });
    
    if (todosDividendos.length === 0) {
        container.innerHTML = `
            <div class="dividendos-empty">
                <i class="fas fa-inbox"></i>
                <h4>Nenhum dividendo encontrado</h4>
                <p>Não há registros de dividendos disponíveis</p>
            </div>
        `;
        return;
    }
    
    // Limite inicial: 5 linhas
    const LIMITE_INICIAL = 5;
    const totalDividendos = todosDividendos.length;
    const temMais = totalDividendos > LIMITE_INICIAL;
    
    let html = `
        <div class="dividendos-table-header">
            <h4>Detalhamento de Proventos</h4>
            <div class="dividendos-table-info">
                <span id="dividendosCount">${temMais ? LIMITE_INICIAL : totalDividendos}</span> de ${totalDividendos} provento(s)
            </div>
        </div>
        
        <div class="dividendos-table-wrapper ${temMais ? 'collapsed' : ''}" id="dividendosTableWrapper">
            <table class="dividendos-table">
                <thead>
                    <tr>
                        <th>TIPO</th>
                        <th>DATA COM</th>
                        <th>PAGAMENTO</th>
                        <th style="text-align: right;">VALOR</th>
                    </tr>
                </thead>
                <tbody id="dividendosTableBody">
    `;
    
    // Renderiza dividendos (inicialmente 5)
    const dividendosExibir = temMais ? todosDividendos.slice(0, LIMITE_INICIAL) : todosDividendos;
    
    dividendosExibir.forEach(div => {
        html += renderDividendoRow(div);
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    // Botão de expansão (se necessário)
    if (temMais) {
        html += `
            <button class="dividendos-expand-btn" onclick="toggleDividendosExpand()">
                <span id="dividendosExpandText">Ver mais ${totalDividendos - LIMITE_INICIAL} dividendos</span>
                <i class="fas fa-chevron-down"></i>
            </button>
        `;
    }
    
    container.innerHTML = html;
    
    // Guarda todos os dividendos globalmente para expansão
    window.todosDividendosData = todosDividendos;
}

/**
 * Renderiza uma linha de dividendo
 */
function renderDividendoRow(div) {
    const tipoClass = div.tipo.toLowerCase().replace(/\s+/g, '-');
    
    return `
        <tr>
            <td>
                <span class="dividendos-tipo-badge ${tipoClass}">${div.tipo}</span>
            </td>
            <td>${div.data_com}</td>
            <td>${div.data_pagamento}</td>
            <td style="text-align: right;">
                <span class="dividendos-valor-destaque">R$ ${div.valor.toFixed(8)}</span>
            </td>
        </tr>
    `;
}

/**
 * Parse de data brasileira para comparação
 */
function parseDataBR(dataStr) {
    if (!dataStr) return new Date(0);
    
    const partes = dataStr.split('/');
    if (partes.length === 3) {
        return new Date(partes[2], partes[1] - 1, partes[0]);
    }
    
    return new Date(dataStr);
}


/**
 * Toggle expansão da tabela de dividendos
 */
function toggleDividendosExpand() {
    const wrapper = document.getElementById('dividendosTableWrapper');
    const tbody = document.getElementById('dividendosTableBody');
    const btn = document.querySelector('.dividendos-expand-btn');
    const countSpan = document.getElementById('dividendosCount');
    const textSpan = document.getElementById('dividendosExpandText');
    
    if (!wrapper || !todosDividendosData) return;
    
    const isCollapsed = wrapper.classList.contains('collapsed');
    const LIMITE_INICIAL = 5;
    const total = todosDividendosData.length;
    
    if (isCollapsed) {
        // Expandir - mostra todos
        let html = '';
        todosDividendosData.forEach(div => {
            html += renderDividendoRow(div);
        });
        tbody.innerHTML = html;
        
        wrapper.classList.remove('collapsed');
        btn.classList.add('expanded');
        countSpan.textContent = total;
        textSpan.textContent = 'Ver menos';
        
        // Scroll suave até o botão
        setTimeout(() => {
            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
        
    } else {
        // Colapsar - mostra apenas 5
        let html = '';
        todosDividendosData.slice(0, LIMITE_INICIAL).forEach(div => {
            html += renderDividendoRow(div);
        });
        tbody.innerHTML = html;
        
        wrapper.classList.add('collapsed');
        btn.classList.remove('expanded');
        countSpan.textContent = LIMITE_INICIAL;
        textSpan.textContent = `Ver mais ${total - LIMITE_INICIAL} dividendos`;
        
        // Scroll até o início da tabela
        document.getElementById('dividendosTableContainer').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

/**
 * Toggle entre views (DY / Pagos)
 */
function toggleDividendosView(view) {
    currentDividendosView = view;
    renderDividendosHistorico();
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

// ========================================
// CARD DE INFORMAÇÕES DA EMPRESA (MAPEAMENTO B3)
// ========================================

// mapeamentoB3 já é carregado antes (array com objetos do CSV):
// cada item: { ticker, todosTickersStr, empresa, cnpj, setor, segmento, sede, descricao, ... }

function updateEmpresaInfo(ticker) {
    if (!mapeamentoB3 || !Array.isArray(mapeamentoB3)) return;

    const tickerUpper = ticker.toUpperCase();

    // 1) Encontra linha da empresa no mapeamento (ticker principal ou entre todosTickersStr)
    const empresaInfo = mapeamentoB3.find(item => {
        if (!item) return false;

        const tBase = (item.ticker || '').toUpperCase();

        if (tBase === tickerUpper) return true;

        if (item.todosTickersStr) {
            return item.todosTickersStr
                .split(';')
                .map(t => t.trim().toUpperCase())
                .includes(tickerUpper);
        }

        return false;
    });

    if (!empresaInfo) {
        console.warn(`Ticker ${ticker} não encontrado no mapeamento B3 para o card de empresa.`);
        return;
    }

    // 2) Campos básicos
    const razaoSocialEl      = document.getElementById('empresaRazaoSocial');
    const cnpjEl             = document.getElementById('empresaCNPJ');
    const setorSegmentoEl    = document.getElementById('empresaSetorSegmento');
    const tickersEl          = document.getElementById('empresaTickers');
    const sedeEl             = document.getElementById('empresaSede');
    const descricaoEl        = document.getElementById('empresaDescricao');
    const mesmoSetorContainer = document.getElementById('empresasMesmoSetor');

    // 3) Preenche razão social
    if (razaoSocialEl) {
        razaoSocialEl.textContent = (empresaInfo.empresa || '').trim() || '-';
    }

    // 4) Preenche CNPJ
    if (cnpjEl) {
        cnpjEl.textContent = (empresaInfo.cnpj || '').trim() || '-';
        // Garante padrão visual (evita letter-spacing / fonte diferente apenas no CNPJ)
        cnpjEl.style.fontFamily = 'inherit';
        cnpjEl.style.letterSpacing = 'normal';
        cnpjEl.style.wordSpacing = 'normal';
        cnpjEl.style.fontVariantNumeric = 'normal';
    }

    // 5) Preenche setor / segmento
    if (setorSegmentoEl) {
        const setor    = (empresaInfo.setor || '').trim();
        const segmento = (empresaInfo.segmento || '').trim();

        if (setor && segmento) {
            setorSegmentoEl.textContent = `${setor} / ${segmento}`;
        } else if (setor || segmento) {
            setorSegmentoEl.textContent = setor || segmento;
        } else {
            setorSegmentoEl.textContent = '-';
        }
    }

    // 6) Preenche todos os tickers de negociação da linha
    if (tickersEl) {
        let todosTickers = [];

        if (empresaInfo.todosTickersStr) {
            todosTickers = empresaInfo.todosTickersStr
                .split(';')
                .map(t => t.trim())
                .filter(Boolean);
        }

        if (!todosTickers.length && empresaInfo.ticker) {
            todosTickers = [empresaInfo.ticker];
        }

        tickersEl.textContent = todosTickers.join(' / ') || tickerUpper;
    }

    // 7) Endereço da sede (normaliza espaços para ajudar a quebra no CSS)
    if (sedeEl) {
        const enderecoBruto = (empresaInfo.sede || '').trim();
        const endereco = enderecoBruto.replace(/\s{2,}/g, ' ');
        sedeEl.textContent = endereco || '-';
    }

    // 8) Descrição
    if (descricaoEl) {
        const desc = (empresaInfo.descricao || '').trim();
        descricaoEl.textContent = desc || '-';
    }

    // 9) Empresas do mesmo setor (lista de tickers)
    if (mesmoSetorContainer) {
        mesmoSetorContainer.innerHTML = '';

        const setorRef = (empresaInfo.setor || '').trim();
        if (setorRef) {
            const similares = mapeamentoB3
                .filter(item =>
                    item &&
                    (item.setor || '').trim() === setorRef &&
                    (item.ticker || '').toUpperCase() !== tickerUpper
                )
                .slice(0, 12); // limita quantidade para não estourar o layout

            similares.forEach(item => {
                const a = document.createElement('a');
                a.href = '#analise-acoes';
                a.className = 'ticker-similar';
                a.textContent = (item.ticker || '').toUpperCase();
                a.addEventListener('click', evt => {
                    evt.preventDefault();
                    loadAcaoData(item.ticker);
                });
                mesmoSetorContainer.appendChild(a);
            });
        }
    }
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



/* ========================================================================== */
/* COMPARADOR DE AÇÕES POR SETOR - VERSÃO CORRIGIDA
/* ========================================================================== */

// Configuração de indicadores
const INDICADORES_CONFIG = {
    // Empresas Não-Financeiras
    'NAO_FINANCEIRAS': {
        main: [
            { code: 'P_L', label: 'P/L', type: 'menor_melhor', format: 'x', allowNegative: false },
            { code: 'P_VPA', label: 'P/VPA', type: 'menor_melhor', format: 'x', allowNegative: false },
            { code: 'ROE', label: 'ROE', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'DY', label: 'DY', type: 'maior_melhor', format: '%', allowNegative: true }
        ],
        extra: [
            { code: 'MARGEM_LIQUIDA', label: 'MARGEM LÍQUIDA', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'ROA', label: 'ROA', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'DIVIDA_LIQUIDA_PL', label: 'DÍV. LÍQ./PL', type: 'menor_melhor', format: 'x', allowNegative: true },
            { code: 'PAYOUT', label: 'PAYOUT', type: 'equilibrio', format: '%', allowNegative: true }
        ]
    },
    // Bancos e Instituições Financeiras
    'FINANCEIRAS': {
        main: [
            { code: 'P_L', label: 'P/L', type: 'menor_melhor', format: 'x', allowNegative: false },
            { code: 'P_VPA', label: 'P/VPA', type: 'menor_melhor', format: 'x', allowNegative: false },
            { code: 'ROE', label: 'ROE', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'DY', label: 'DY', type: 'maior_melhor', format: '%', allowNegative: true }
        ],
        extra: [
            { code: 'MARGEM_LIQUIDA', label: 'MARGEM LÍQUIDA', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'ROA', label: 'ROA', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'INDICE_BASILEIA', label: 'BASILEIA', type: 'maior_melhor', format: '%', allowNegative: true },
            { code: 'INDICE_COBERTURA', label: 'COBERTURA', type: 'maior_melhor', format: '%', allowNegative: true }
        ]
    }
};

// Setores Financeiros
const SETORES_FINANCEIROS = [
    'Intermediários Financeiros',
    'Bancos',
    'Seguradoras',
    'Exploração de Imóveis',
    'Previdência e Seguros'
];

// Estado do comparador
let comparadorState = {
    empresasSetor: [],
    indicadorAtivo: 'main',
    tickerAtual: null,
    setorAtual: null,
    tipoSetor: 'NAO_FINANCEIRAS'
};

// Base RAW do repositório (usado no Comparador)
const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main';


/**
 * Identifica se o setor é financeiro
 */
function isSetorFinanceiro(setor) {
    return SETORES_FINANCEIROS.some(sf => setor.includes(sf));
}

/**
 * Busca empresas do mesmo setor usando mapeamento global
 */
function buscarEmpresasDoSetor(ticker) {
    console.log('🔍 Buscando empresas do setor para:', ticker);
    console.log('📊 Mapeamento B3 disponível:', mapeamentoB3?.length || 0, 'empresas');
    
    // Valida se mapeamento está carregado
    if (!Array.isArray(mapeamentoB3) || mapeamentoB3.length === 0) {
        console.error('❌ Mapeamento B3 não está carregado');
        return { empresaAtual: null, empresasSetor: [], tipoSetor: 'NAO_FINANCEIRAS' };
    }
    
    const tickerNorm = normalizarTicker(ticker);
    console.log('🎯 Ticker normalizado:', tickerNorm);
    
    // Busca empresa atual
    const empresaAtual = mapeamentoB3.find(e => normalizarTicker(e.ticker) === tickerNorm);
    
    if (!empresaAtual) {
        console.error('❌ Ticker não encontrado no mapeamento:', tickerNorm);
        console.log('📝 Primeiros 5 tickers do mapeamento:', 
            mapeamentoB3.slice(0, 5).map(e => e.ticker).join(', ')
        );
        return { empresaAtual: null, empresasSetor: [], tipoSetor: 'NAO_FINANCEIRAS' };
    }
    
    console.log('✅ Empresa encontrada:', empresaAtual.empresa);
    console.log('🏢 Setor:', empresaAtual.setor);
    
    // Filtra empresas do mesmo setor (exclui a empresa atual)
    const empresasSetor = mapeamentoB3.filter(e => 
        e.setor === empresaAtual.setor && 
        normalizarTicker(e.ticker) !== tickerNorm
    );
    
    console.log('🎯 Empresas do mesmo setor encontradas:', empresasSetor.length);
    
    // Remove duplicatas por empresa (mantém apenas primeiro ticker)
    const empresasUnicas = [];
    const empresasVistas = new Set();
    
    for (const emp of empresasSetor) {
        if (!empresasVistas.has(emp.empresa)) {
            empresasVistas.add(emp.empresa);
            empresasUnicas.push(emp);
        }
    }
    
    console.log('📊 Empresas únicas (sem duplicatas):', empresasUnicas.length);
    
    // Determina tipo de setor
    const tipoSetor = isSetorFinanceiro(empresaAtual.setor) ? 'FINANCEIRAS' : 'NAO_FINANCEIRAS';
    console.log('💼 Tipo de setor:', tipoSetor);
    
    return {
        empresaAtual,
        empresasSetor: empresasUnicas,
        tipoSetor
    };
}

/**
 * Busca múltiplos de uma empresa via arquivo multiplos.json - VERSÃO OTIMIZADA
 */
async function buscarMultiplosEmpresa(ticker) {
    try {
        const tickerNorm = normalizarTicker(ticker);
        const tickerPasta = obterTickerPasta(tickerNorm);
        
        console.log(`📈 Buscando múltiplos de ${tickerNorm} (pasta: ${tickerPasta})`);
        
        const timestamp = new Date().getTime();
        const url = `${GITHUB_RAW_BASE}/balancos/${tickerPasta}/multiplos.json?t=${timestamp}`;
        
        // ✅ Timeout de 3 segundos
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            console.warn(`⚠️ Múltiplos não encontrados para ${tickerNorm} (HTTP ${response.status})`);
            return null;  // ✅ Retorna null em vez de quebrar
        }
        
        const data = await response.json();
        
        // Busca info da empresa no mapeamento
        const empresaInfo = mapeamentoB3?.find(e => normalizarTicker(e.ticker) === tickerNorm);
        
        // Extrai múltiplos do LTM
        const multiplos = data?.ltm?.multiplos;
        
        console.log(`✅ Múltiplos carregados para ${tickerNorm}`);
        
        return {
            ticker: tickerNorm,
            empresa: empresaInfo?.empresa || tickerNorm,
            logo: `${GITHUB_RAW_BASE}/balancos/${tickerPasta}/logo.png`,
            multiplos: multiplos || {}
        };
        
    } catch (error) {
        // Se foi timeout ou erro de rede, não loga como erro
        if (error.name === 'AbortError') {
            console.warn(`⏱️ Timeout ao buscar ${ticker}`);
        } else {
            console.warn(`⚠️ Erro ao buscar múltiplos de ${ticker}:`, error.message);
        }
        return null;
    }
}



/**
 * Formata valor do indicador
 */
function formatarValorComparador(valor, formato) {
    if (valor === null || valor === undefined || isNaN(valor)) return '-';
    
    const num = parseFloat(valor);
    
    if (formato === '%') {
        return `${num.toFixed(2)}%`;
    } else if (formato === 'x') {
        return `${num.toFixed(2)}x`;
    } else if (formato === 'R$') {
        return `R$ ${num.toFixed(2)} B`;
    }
    
    return num.toFixed(2);
}

/**
 * Identifica o melhor valor para cada indicador
 */
function identificarMelhores(empresasComDados, indicadores) {
    const melhores = {};
    
    indicadores.forEach(ind => {
        const valores = empresasComDados
            .map(e => ({
                ticker: e.ticker,
                valor: e.multiplos[ind.code]
            }))
            .filter(v => v.valor !== null && !isNaN(v.valor));
        
        if (valores.length === 0) return;
        
        // Filtra valores negativos para indicadores que não permitem
        const valoresValidos = ind.allowNegative 
            ? valores 
            : valores.filter(v => v.valor >= 0);
        
        if (valoresValidos.length === 0) return;
        
        let melhorTicker;
        
        if (ind.type === 'maior_melhor') {
            // Maior valor é melhor (ROE, DY, etc)
            const max = Math.max(...valoresValidos.map(v => v.valor));
            melhorTicker = valoresValidos.find(v => v.valor === max)?.ticker;
        } else if (ind.type === 'menor_melhor') {
            // Menor valor é melhor (P/L, P/VPA, etc)
            const min = Math.min(...valoresValidos.map(v => v.valor));
            melhorTicker = valoresValidos.find(v => v.valor === min)?.ticker;
        }
        
        if (melhorTicker) {
            melhores[ind.code] = melhorTicker;
        }
    });
    
    return melhores;
}

/**
 * Renderiza tabela do comparador
 */
function renderizarComparador(empresasComDados, indicadores, melhores) {
    const tableHead = document.getElementById('comparadorTableHead');
    const tableBody = document.getElementById('comparadorTableBody');
    
    if (!tableHead || !tableBody) {
        console.error('❌ Elementos da tabela não encontrados');
        return;
    }
    
    // Limpa tabela
    tableHead.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Monta cabeçalho
    const headerRow = document.createElement('tr');
    
    // Coluna empresa
    const thEmpresa = document.createElement('th');
    thEmpresa.textContent = 'EMPRESA';
    headerRow.appendChild(thEmpresa);
    
    // Colunas de indicadores
    indicadores.forEach(ind => {
        const th = document.createElement('th');
        th.textContent = ind.label;
        th.title = ind.type === 'maior_melhor' ? 'Quanto maior, melhor' : 'Quanto menor, melhor';
        headerRow.appendChild(th);
    });
    
    tableHead.appendChild(headerRow);
    
    // Monta corpo
    empresasComDados.forEach(empresa => {
        const row = document.createElement('tr');
        
        // Coluna empresa (logo + ticker)
        const tdEmpresa = document.createElement('td');
        tdEmpresa.innerHTML = `
            <div class="empresa-cell">
                <img 
                    src="${empresa.logo}" 
                    alt="${empresa.ticker}" 
                    class="empresa-logo"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                />
                <div class="empresa-logo-fallback" style="display: none;">
                    ${empresa.ticker.substring(0, 2)}
                </div>
                <div class="empresa-info">
                    <span class="empresa-ticker">${empresa.ticker}</span>
                    <span class="empresa-nome">${empresa.empresa}</span>
                </div>
            </div>
        `;
        row.appendChild(tdEmpresa);
        
        // Colunas de indicadores
        indicadores.forEach(ind => {
            const td = document.createElement('td');
            const valor = empresa.multiplos[ind.code];
            const valorFormatado = formatarValorComparador(valor, ind.format);
            
            td.className = 'valor-cell';
            
            // Aplica classe de cor
            if (valor !== null && !isNaN(valor)) {
                if (valor > 0) td.classList.add('positive');
                else if (valor < 0) td.classList.add('negative');
            }
            
            // Adiciona estrela se for o melhor
            if (melhores[ind.code] === empresa.ticker) {
                td.classList.add('destaque');
                td.innerHTML = `
                    ${valorFormatado}
                    <i class="fas fa-star star-indicator"></i>
                `;
            } else {
                td.textContent = valorFormatado;
            }
            
            row.appendChild(td);
        });
        
        tableBody.appendChild(row);
    });
    
    console.log('✅ Tabela renderizada com', empresasComDados.length, 'empresas');
}

/**
 * Carrega e exibe comparador - VERSÃO INDEPENDENTE
 */
async function carregarComparador(ticker) {
    console.log('🚀 Iniciando carregamento do comparador para:', ticker);
    
    const section = document.getElementById('comparadorAcoesSection');
    const loading = document.getElementById('comparadorLoading');
    const empty = document.getElementById('comparadorEmpty');
    const tabs = document.getElementById('comparadorTabs');
    const tableWrapper = document.getElementById('comparadorTableWrapper');
    const footer = document.getElementById('comparadorFooter');
    const subtitle = document.getElementById('comparadorSubtitle');
    
    if (!section) {
        console.error('❌ Seção do comparador não encontrada no HTML');
        return;
    }
    
    // Mostra loading
    section.style.display = 'block';
    loading.style.display = 'flex';
    empty.style.display = 'none';
    tabs.style.display = 'none';
    tableWrapper.style.display = 'none';
    footer.style.display = 'none';
    
    try {
        // Aguarda mapeamento estar carregado (máximo 5 segundos)
        let tentativas = 0;
        while ((!mapeamentoB3 || mapeamentoB3.length === 0) && tentativas < 50) {
            console.log('⏳ Aguardando mapeamento B3... tentativa', tentativas + 1);
            await new Promise(resolve => setTimeout(resolve, 100));
            tentativas++;
        }
        
        if (!mapeamentoB3 || mapeamentoB3.length === 0) {
            throw new Error('Mapeamento B3 não carregado após timeout');
        }
        
        // Busca empresas do setor
        const { empresaAtual, empresasSetor, tipoSetor } = buscarEmpresasDoSetor(ticker);
        
        if (!empresaAtual) {
            console.warn('⚠️ Empresa atual não encontrada');
            loading.style.display = 'none';
            empty.style.display = 'flex';
            return;
        }
        
        if (empresasSetor.length === 0) {
            console.warn('⚠️ Nenhuma empresa do mesmo setor encontrada');
            loading.style.display = 'none';
            empty.style.display = 'flex';
            return;
        }
        
        // Atualiza estado
        comparadorState.tickerAtual = ticker;
        comparadorState.setorAtual = empresaAtual.setor;
        comparadorState.tipoSetor = tipoSetor;
        subtitle.textContent = `Empresas do setor: ${empresaAtual.setor}`;
        
        console.log(`📊 Buscando múltiplos de todas as empresas (incluindo ${ticker})...`);
        
        // ===== BUSCA MÚLTIPLOS DE TODAS AS EMPRESAS (incluindo a atual) =====
        const tickersParaComparar = [ticker, ...empresasSetor.map(e => e.ticker)];
        console.log(`🔍 Total de empresas para comparar: ${tickersParaComparar.length}`);
        
        const promessas = tickersParaComparar.map(t => buscarMultiplosEmpresa(t));
        const resultados = await Promise.all(promessas);

        // Monta lista final (inclui placeholders para empresas sem multiplos.json)
        const resultadosMap = new Map(
            resultados
                .filter(r => r !== null)
                .map(r => [normalizarTicker(r.ticker), r])
        );

        const empresasFinal = tickersParaComparar.map(t => {
            const tn = normalizarTicker(t);
            const r = resultadosMap.get(tn);
            if (r) return r;

            const pasta = obterTickerPasta(tn);
            const info = mapeamentoB3?.find(e => normalizarTicker(e.ticker) === tn);

            return {
                ticker: tn,
                empresa: info?.empresa || tn,
                logo: `${GITHUB_RAW_BASE}/balancos/${pasta}/logo.png`,
                multiplos: {}
            };
        });

        // Empresas com pelo menos algum múltiplo válido (para decidir se exibimos a tabela)
        const empresasComDados = empresasFinal.filter(e => e.multiplos && Object.keys(e.multiplos).length > 0);

        console.log(`✅ Total de empresas com dados: ${empresasComDados.length} (de ${empresasFinal.length})`);

        // Precisa de pelo menos 1 empresa com dados para exibir
        if (empresasComDados.length < 1) {
            console.warn('⚠️ Nenhum dado disponível');
            loading.style.display = 'none';
            empty.style.display = 'flex';
            return;
        }

        // Se tem apenas 1 empresa com dados, avisa (mas ainda mostra tabela)
        if (empresasComDados.length === 1) {
            console.warn('⚠️ Mostrando apenas empresa atual (sem comparação completa)');
            subtitle.textContent = `${empresaAtual.setor} (dados limitados)`;
        }

        // Atualiza estado (mantém todas as empresas do setor, inclusive placeholders)
        comparadorState.empresasSetor = empresasFinal;
        comparadorState.indicadorAtivo = 'main';
        comparadorState.indicadoresExtrasSelecionados = [];
        comparadorState.indicadoresExtrasDisponiveis = montarListaIndicadoresExtrasDisponiveis(tipoSetor, empresasFinal);
        atualizarBotaoAdicionarIndicadores();

        // Renderiza indicadores principais
        const indicadores = INDICADORES_CONFIG[tipoSetor].main;
        const melhores = identificarMelhores(empresasComDados, indicadores);
        renderizarComparador(empresasComDados, indicadores, melhores);
        
        // Mostra interface
        loading.style.display = 'none';
        tabs.style.display = 'flex';
        tableWrapper.style.display = 'block';
        footer.style.display = 'block';
        
        console.log('🎉 Comparador carregado com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao carregar comparador:', error);
        loading.style.display = 'none';
        empty.style.display = 'flex';
    }
}


/**
 * Alterna entre indicadores principais e extras
 */
function alternarIndicadores(grupo) {
    const { empresasSetor, tipoSetor } = comparadorState;
    if (!empresasSetor || empresasSetor.length === 0) return;

    // "Principais" = apenas indicadores principais
    if (grupo === 'main') {
        comparadorState.indicadorAtivo = 'main';
        comparadorState.indicadoresExtrasSelecionados = [];
        atualizarBotaoAdicionarIndicadores();
        marcarTabAtiva('main');

        const indicadores = INDICADORES_CONFIG[tipoSetor].main;
        const melhores = identificarMelhores(empresasSetor, indicadores);
        renderizarComparador(empresasSetor, indicadores, melhores);
        return;
    }

    // "Adicionar +4" = abre modal (usuário escolhe os indicadores)
    abrirModalIndicadoresComparador();
}

/**
 * Definições dos indicadores (labels/formatação) para o Comparador
 * Obs.: os códigos precisam bater com os códigos do JSON (ex.: P_L, P_VPA, DIV_LIQ_PL, etc)
 */
function obterDefIndicador(code) {
    const defs = {
        // Principais (comuns)
        P_L: { code: 'P_L', label: 'P/L', type: 'menor_melhor', format: 'x', allowNegative: false },
        P_VPA: { code: 'P_VPA', label: 'P/VPA', type: 'menor_melhor', format: 'x', allowNegative: false },
        ROE: { code: 'ROE', label: 'ROE', type: 'maior_melhor', format: '%', allowNegative: true },
        DY: { code: 'DY', label: 'DY', type: 'maior_melhor', format: '%', allowNegative: true },

        // Não-financeiras
        EV_EBITDA: { code: 'EV_EBITDA', label: 'EV/EBITDA', type: 'menor_melhor', format: 'x', allowNegative: false },
        EV_EBIT: { code: 'EV_EBIT', label: 'EV/EBIT', type: 'menor_melhor', format: 'x', allowNegative: false },
        EV_RECEITA: { code: 'EV_RECEITA', label: 'EV/RECEITA', type: 'menor_melhor', format: 'x', allowNegative: false },
        ROA: { code: 'ROA', label: 'ROA', type: 'maior_melhor', format: '%', allowNegative: true },
        ROIC: { code: 'ROIC', label: 'ROIC', type: 'maior_melhor', format: '%', allowNegative: true },
        MARGEM_EBITDA: { code: 'MARGEM_EBITDA', label: 'MARGEM EBITDA', type: 'maior_melhor', format: '%', allowNegative: true },
        MARGEM_LIQUIDA: { code: 'MARGEM_LIQUIDA', label: 'MARGEM LÍQUIDA', type: 'maior_melhor', format: '%', allowNegative: true },
        DIV_LIQ_EBITDA: { code: 'DIV_LIQ_EBITDA', label: 'DÍV. LÍQ./EBITDA', type: 'menor_melhor', format: 'x', allowNegative: true },
        DIV_LIQ_PL: { code: 'DIV_LIQ_PL', label: 'DÍV. LÍQ./PL', type: 'menor_melhor', format: 'x', allowNegative: true },
        ICJ: { code: 'ICJ', label: 'ICJ', type: 'maior_melhor', format: 'x', allowNegative: true },
        COMPOSICAO_DIVIDA: { code: 'COMPOSICAO_DIVIDA', label: 'COMPOSIÇÃO DÍVIDA', type: 'menor_melhor', format: '%', allowNegative: false },
        LIQ_CORRENTE: { code: 'LIQ_CORRENTE', label: 'LIQ. CORRENTE', type: 'maior_melhor', format: 'x', allowNegative: false },
        LIQ_SECA: { code: 'LIQ_SECA', label: 'LIQ. SECA', type: 'maior_melhor', format: 'x', allowNegative: false },
        LIQ_GERAL: { code: 'LIQ_GERAL', label: 'LIQ. GERAL', type: 'maior_melhor', format: 'x', allowNegative: false },
        GIRO_ATIVO: { code: 'GIRO_ATIVO', label: 'GIRO ATIVO', type: 'maior_melhor', format: 'x', allowNegative: false },
        PME: { code: 'PME', label: 'PME', type: 'menor_melhor', format: '', allowNegative: false },
        CICLO_CAIXA: { code: 'CICLO_CAIXA', label: 'CICLO CAIXA', type: 'menor_melhor', format: '', allowNegative: false },
        NCG_RECEITA: { code: 'NCG_RECEITA', label: 'NCG/RECEITA', type: 'menor_melhor', format: '%', allowNegative: true },

        // Financeiras
        PAYOUT: { code: 'PAYOUT', label: 'PAYOUT', type: 'maior_melhor', format: '%', allowNegative: true },
        PL_ATIVOS: { code: 'PL_ATIVOS', label: 'PL/ATIVOS', type: 'maior_melhor', format: '%', allowNegative: true }
    };

    if (defs[code]) return defs[code];

    // Fallback (não quebra o comparador se surgir um novo indicador no JSON)
    return {
        code,
        label: String(code || '').replace(/_/g, ' '),
        type: 'maior_melhor',
        format: 'x',
        allowNegative: true
    };
}

/**
 * Monta a lista de indicadores extras disponíveis (com base nos códigos realmente presentes no JSON do setor)
 */
function montarListaIndicadoresExtrasDisponiveis(tipoSetor, empresas) {
    const mainCodes = new Set((INDICADORES_CONFIG[tipoSetor]?.main || []).map(i => i.code));
    const codes = new Set();

    (empresas || []).forEach(emp => {
        const m = emp?.multiplos || {};
        Object.keys(m).forEach(k => {
            if (!mainCodes.has(k)) codes.add(k);
        });
    });

    const defs = Array.from(codes).map(obterDefIndicador);
    defs.sort((a, b) => (a.label || '').localeCompare((b.label || ''), 'pt-BR'));
    return defs;
}

/**
 * Atualiza o texto do botão "Adicionar +4"
 */
function atualizarBotaoAdicionarIndicadores() {
    const label = document.getElementById('comparadorAddIndicatorsLabel');
    if (!label) return;

    const qtd = (comparadorState.indicadoresExtrasSelecionados || []).length;
    label.textContent = qtd > 0 ? `Indicadores +${qtd}` : 'Adicionar +4';
}

/**
 * Marca tab ativa (somente visual)
 */
function marcarTabAtiva(grupo) {
    document.querySelectorAll('.indicator-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.group === grupo);
    });
}

/**
 * Modal: abre/fecha + renderiza lista
 */
function abrirModalIndicadoresComparador() {
    const modal = document.getElementById('comparadorIndicadoresModal');
    if (!modal) return;

    montarListaIndicadoresModal();
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');
}

function fecharModalIndicadoresComparador() {
    const modal = document.getElementById('comparadorIndicadoresModal');
    if (!modal) return;
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
}

/**
 * Renderiza checklist do modal e controla limite de 4
 */
function montarListaIndicadoresModal() {
    const list = document.getElementById('comparadorIndicadoresList');
    const counter = document.getElementById('comparadorIndicadoresCounter');
    if (!list || !counter) return;

    const disponiveis = comparadorState.indicadoresExtrasDisponiveis || [];
    const selecionados = new Set((comparadorState.indicadoresExtrasSelecionados || []).map(i => i.code));

    list.innerHTML = '';

    disponiveis.forEach(def => {
        const item = document.createElement('label');
        item.className = 'comparador-indicadores-item';

        item.innerHTML = `
            <input type="checkbox" value="${def.code}" ${selecionados.has(def.code) ? 'checked' : ''} />
            <div>
                <div class="title">${def.label}</div>
                <div class="meta">${def.code}</div>
            </div>
        `;

        list.appendChild(item);
    });

    const atualizarLimite = () => {
        const checks = Array.from(list.querySelectorAll('input[type="checkbox"]'));
        const marcados = checks.filter(c => c.checked).length;

        counter.textContent = `${marcados}/4 selecionados`;

        checks.forEach(c => {
            const parent = c.closest('.comparador-indicadores-item');
            const deveDesabilitar = !c.checked && marcados >= 4;
            c.disabled = deveDesabilitar;
            if (parent) parent.classList.toggle('disabled', deveDesabilitar);
        });
    };

    list.addEventListener('change', atualizarLimite, { once: true });
    // re-anexa em tempo real
    list.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.addEventListener('change', atualizarLimite));

    atualizarLimite();
}

/**
 * Aplica seleção do modal: renderiza Principais + até 4 extras
 */
function aplicarIndicadoresSelecionadosComparador() {
    const list = document.getElementById('comparadorIndicadoresList');
    if (!list) return;

    const checks = Array.from(list.querySelectorAll('input[type="checkbox"]')).filter(c => c.checked);
    const codes = checks.map(c => c.value).slice(0, 4);
    const extras = codes.map(obterDefIndicador);

    comparadorState.indicadoresExtrasSelecionados = extras;
    comparadorState.indicadorAtivo = 'custom';

    atualizarBotaoAdicionarIndicadores();
    marcarTabAtiva('extra');
    fecharModalIndicadoresComparador();

    const { empresasSetor } = comparadorState;
    const principais = INDICADORES_CONFIG[comparadorState.tipoSetor].main;
    const indicadores = [...principais, ...extras];
    const melhores = identificarMelhores(empresasSetor, indicadores);
    renderizarComparador(empresasSetor, indicadores, melhores);
}

/**
 * Limpa seleção do modal (volta a Principais)
 */
function limparIndicadoresSelecionadosComparador() {
    comparadorState.indicadoresExtrasSelecionados = [];
    comparadorState.indicadorAtivo = 'main';
    atualizarBotaoAdicionarIndicadores();
    marcarTabAtiva('main');
    fecharModalIndicadoresComparador();

    const { empresasSetor, tipoSetor } = comparadorState;
    const indicadores = INDICADORES_CONFIG[tipoSetor].main;
    const melhores = identificarMelhores(empresasSetor, indicadores);
    renderizarComparador(empresasSetor, indicadores, melhores);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Tabs de indicadores
    document.querySelectorAll('.indicator-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            alternarIndicadores(btn.dataset.group);
        });
    });

    // Modal (+4)
    const modal = document.getElementById('comparadorIndicadoresModal');
    const btnClose = document.getElementById('comparadorIndicadoresClose');
    const btnCancel = document.getElementById('comparadorIndicadoresCancel');
    const btnApply = document.getElementById('comparadorIndicadoresApply');
    const btnClear = document.getElementById('comparadorIndicadoresClear');

    if (btnClose) btnClose.addEventListener('click', fecharModalIndicadoresComparador);
    if (btnCancel) btnCancel.addEventListener('click', fecharModalIndicadoresComparador);
    if (btnApply) btnApply.addEventListener('click', aplicarIndicadoresSelecionadosComparador);
    if (btnClear) btnClear.addEventListener('click', limparIndicadoresSelecionadosComparador);

    // Fecha ao clicar fora do conteúdo
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) fecharModalIndicadoresComparador();
        });
    }
});




/* ========================================
   ANÁLISE DOS BALANÇOS - DEMONSTRAÇÕES FINANCEIRAS
   ======================================== */

let demonstracoesFinanceirasData = null;
let demonstracoesFinanceirasChart = null;
let demonstracoesViewType = 'anual'; // 'anual' ou 'trimestral'
let demonstracoesDisplayMode = 'tabela'; // 'tabela' ou 'grafico'
let demonstracaoTipoAtivo = 'DRE'; // 'DRE', 'BPA', 'BPP', 'DFC'

// Configuração de contas por tipo de empresa com NOMES ABREVIADOS
const CONTAS_BALANCOS = {
    NAOFINANCEIRAS: {
        DRE: [
            { codigo: '3.01', nome: 'Receita', nomeCompleto: 'Receita de Venda de Bens e/ou Serviços' },
            { codigo: '3.05', nome: 'EBIT', nomeCompleto: 'EBIT (Resultado Antes do Resultado Financeiro e dos Tributos)' },
            { codigo: '3.07', nome: 'Resultado antes do Lucro', nomeCompleto: 'Resultado Antes dos Tributos sobre o Lucro' },
            { codigo: '3.11', nome: 'Lucro/Prejuízo', nomeCompleto: 'Lucro/Prejuízo Consolidado do Período' }
        ],
        BPA: [
            { codigo: '1.01', nome: 'Ativo Circulante', nomeCompleto: 'Ativo Circulante' },
            { codigo: '1.01.01', nome: 'Caixa e Equivalentes', nomeCompleto: 'Caixa e Equivalentes de Caixa' },
            { codigo: '1.01.03', nome: 'Contas a Receber', nomeCompleto: 'Contas a Receber' },
            { codigo: '1.01.04', nome: 'Estoques', nomeCompleto: 'Estoques' },
            { codigo: '1.02', nome: 'Ativo Não Circulante', nomeCompleto: 'Ativo Não Circulante' }
        ],
        BPP: [
            { codigo: '2.01', nome: 'Passivo Circulante', nomeCompleto: 'Passivo Circulante' },
            { codigo: '2.02', nome: 'Passivo Não Circulante', nomeCompleto: 'Passivo Não Circulante' },
            { codigo: '2.03', nome: 'Patrimônio Líquido', nomeCompleto: 'Patrimônio Líquido Consolidado' }
        ],
        DFC: [
            { codigo: '6.01', nome: 'Caixa Operacional', nomeCompleto: 'Caixa Líquido das Atividades Operacionais' },
            { codigo: '6.02', nome: 'Caixa Investimento', nomeCompleto: 'Caixa Líquido Atividades de Investimento' },
            { codigo: '6.03', nome: 'Caixa Financiamento', nomeCompleto: 'Caixa Líquido Atividades de Financiamento' }
        ]
    },
    FINANCEIRAS: {
        DRE: [
            { codigo: '3.01', nome: 'Receitas Intermediação', nomeCompleto: 'Receitas de Intermediação Financeira' },
            { codigo: '3.03', nome: 'Resultado Bruto', nomeCompleto: 'Resultado Bruto de Intermediação Financeira' },
            { codigo: '3.11', nome: 'Lucro/Prejuízo', nomeCompleto: 'Lucro ou Prejuízo Líquido Consolidado do Período' }
        ],
        BPA: [
            { codigo: '1.02', nome: 'Ativos Financeiros', nomeCompleto: 'Ativos Financeiros' },
            { codigo: '1.05', nome: 'Investimentos', nomeCompleto: 'Investimentos' },
            { codigo: '1.06', nome: 'Imobilizado', nomeCompleto: 'Imobilizado' },
            { codigo: '1.07', nome: 'Intangível', nomeCompleto: 'Intangível' }
        ],
        BPP: [
            { codigo: '2.01', nome: 'Passivos Valor Justo', nomeCompleto: 'Passivos Financeiros ao Valor Justo através do Resultado' },
            { codigo: '2.02', nome: 'Passivos Custo Amortizado', nomeCompleto: 'Passivos Financeiros ao Custo Amortizado' },
            { codigo: '2.08', nome: 'Patrimônio Líquido', nomeCompleto: 'Patrimônio Líquido Consolidado' }
        ],
        DFC: []
    }
};

// Hook de carregamento no loadAcaoData
const originalLoadAcaoDataDemonstra = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataDemonstra.call(this, ticker);
    await loadDemonstracoesFinanceirasData(ticker);
};

// Carrega dados dos balanços
async function loadDemonstracoesFinanceirasData(ticker) {
    try {
        console.log('Carregando demonstrações financeiras de', ticker, '...');

        const tickerNorm = normalizarTicker(ticker);
        const empresaInfo = mapeamentoB3.find(item => normalizarTicker(item.ticker) === tickerNorm);
        
        if (!empresaInfo) {
            throw new Error(`Ticker ${tickerNorm} não encontrado no mapeamento B3`);
        }

        const tickerPasta = obterTickerPasta(ticker);
        const ehFinanceira = isSetorFinanceiro(empresaInfo.setor);
        const timestamp = new Date().getTime();

        const arquivos = ehFinanceira 
            ? ['bpa_padronizado', 'bpp_padronizado', 'dre_padronizado']
            : ['bpa_padronizado', 'bpp_padronizado', 'dre_padronizado', 'dfc_padronizado'];

        const promessas = arquivos.map(async arquivo => {
            const url = `https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/${arquivo}.csv?t=${timestamp}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Arquivo ${arquivo} não encontrado`);
            const text = await response.text();
            return { tipo: arquivo.split('_')[0].toUpperCase(), dados: parseDemonstracoesCSV(text) };
        });

        const resultados = await Promise.all(promessas);

        demonstracoesFinanceirasData = {
            ticker: ticker,
            empresa: empresaInfo.empresa,
            ehFinanceira: ehFinanceira,
            balancos: {}
        };

        resultados.forEach(resultado => {
            demonstracoesFinanceirasData.balancos[resultado.tipo] = resultado.dados;
        });

        console.log('Demonstrações carregadas:', Object.keys(demonstracoesFinanceirasData.balancos));

        renderDemonstracoesFinanceirasSection();

    } catch (error) {
        console.error('Erro ao carregar demonstrações:', error);
        document.getElementById('analiseBalancosSection').style.display = 'none';
    }
}

// Parser CSV simples
function parseDemonstracoesCSV(csvText) {
    const linhas = csvText.split('\n').filter(l => l.trim());
    const header = linhas[0].split(',').map(h => h.trim());
    
    const dados = {};
    for (let i = 1; i < linhas.length; i++) {
        const valores = linhas[i].split(',');
        const cdConta = valores[0]?.trim();
        const conta = valores[1]?.trim();
        
        if (!cdConta) continue;
        
        dados[cdConta] = {
            conta: conta,
            valores: {}
        };

        for (let j = 2; j < valores.length; j++) {
            const periodo = header[j];
            const valor = parseFloat(valores[j]);
            dados[cdConta].valores[periodo] = isNaN(valor) ? null : valor;
        }
    }

    return dados;
}

// Renderiza seção principal
function renderDemonstracoesFinanceirasSection() {
    const section = document.getElementById('analiseBalancosSection');
    if (!section || !demonstracoesFinanceirasData) return;

    const loading = document.getElementById('analiseBalancosLoading');
    const controls = document.getElementById('analiseBalancosControls');
    const subtitle = document.getElementById('analiseBalancosSubtitle');

    loading.style.display = 'none';
    controls.style.display = 'flex';
    section.style.display = 'block';

    subtitle.textContent = `${demonstracoesFinanceirasData.empresa} - ${demonstracoesFinanceirasData.ehFinanceira ? 'Instituição Financeira' : 'Empresa Não Financeira'}`;

    initDemonstracoesFinanceirasControls();
    renderDemonstracoesFinanceirasTabela();
}

// Inicializa controles de visualização
function initDemonstracoesFinanceirasControls() {
    document.getElementById('viewAnualBtn').addEventListener('click', () => alternarDemonstracoesViewType('anual'));
    document.getElementById('viewTrimestralBtn').addEventListener('click', () => alternarDemonstracoesViewType('trimestral'));
    document.getElementById('displayTabelaBtn').addEventListener('click', () => alternarDemonstracoesDisplayMode('tabela'));
    document.getElementById('displayGraficoBtn').addEventListener('click', () => alternarDemonstracoesDisplayMode('grafico'));
    document.getElementById('tipoDREBtn')?.addEventListener('click', () => alternarDemonstracaoTipo('DRE'));
    document.getElementById('tipoBPABtn')?.addEventListener('click', () => alternarDemonstracaoTipo('BPA'));
    document.getElementById('tipoBPPBtn')?.addEventListener('click', () => alternarDemonstracaoTipo('BPP'));
    document.getElementById('tipoDFCBtn')?.addEventListener('click', () => alternarDemonstracaoTipo('DFC'));
}

// Alterna entre anual e trimestral
function alternarDemonstracoesViewType(tipo) {
    demonstracoesViewType = tipo;
    document.querySelectorAll('.view-type-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-view="${tipo}"]`).classList.add('active');

    if (demonstracoesDisplayMode === 'tabela') {
        renderDemonstracoesFinanceirasTabela();
    } else {
        renderDemonstracoesFinanceirasGrafico();
    }
}

// Alterna entre tabela e gráfico
function alternarDemonstracoesDisplayMode(modo) {
    demonstracoesDisplayMode = modo;
    
    document.querySelectorAll('.chart-table-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-display="${modo}"]`).classList.add('active');

    const tableWrapper = document.getElementById('analiseBalancosTableWrapper');
    const chartWrapper = document.getElementById('analiseBalancosChartWrapper');
    const tipoControls = document.getElementById('demonstracaoTipoControls');
    const footer = document.getElementById('analiseBalancosFooter');

    if (modo === 'tabela') {
        tableWrapper.style.display = 'block';
        chartWrapper.style.display = 'none';
        tipoControls.style.display = 'none';
        renderDemonstracoesFinanceirasTabela();
    } else {
        tableWrapper.style.display = 'none';
        chartWrapper.style.display = 'block';
        tipoControls.style.display = 'flex';
        
        const dfcBtn = document.getElementById('tipoDFCBtn');
        if (dfcBtn) {
            dfcBtn.style.display = demonstracoesFinanceirasData.ehFinanceira ? 'none' : 'flex';
        }
        
        renderDemonstracoesFinanceirasGrafico();
    }

    footer.style.display = 'block';
}

// Alterna tipo de demonstração (DRE, BPA, BPP, DFC)
function alternarDemonstracaoTipo(tipo) {
    demonstracaoTipoAtivo = tipo;
    document.querySelectorAll('.demonstracao-tipo-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tipo="${tipo}"]`)?.classList.add('active');
    renderDemonstracoesFinanceirasGrafico();
}

// Formata período para exibição (remove T4/T3 quando anual)
function formatarPeriodoExibicao(periodo, viewType) {
    if (viewType === 'anual') {
        return periodo.replace(/T\d/, '');
    }
    return periodo;
}

// Renderiza tabela de balanços
function renderDemonstracoesFinanceirasTabela() {
    const thead = document.getElementById('analiseBalancosTableHead');
    const tbody = document.getElementById('analiseBalancosTableBody');
    const footer = document.getElementById('analiseBalancosDataSource');

    if (!demonstracoesFinanceirasData) return;

    const config = demonstracoesFinanceirasData.ehFinanceira ? CONTAS_BALANCOS.FINANCEIRAS : CONTAS_BALANCOS.NAOFINANCEIRAS;
    const primeiroArquivo = Object.values(demonstracoesFinanceirasData.balancos)[0];
    const primeiroItem = Object.values(primeiroArquivo)[0];
    const todosPeriodos = Object.keys(primeiroItem.valores).sort();

    let periodosExibir;
    if (demonstracoesViewType === 'anual') {
        const anos = {};
        todosPeriodos.forEach(p => {
            const match = p.match(/(\d{4})T(\d)/);
            if (match) {
                const ano = match[1];
                const trim = parseInt(match[2]);
                if (!anos[ano] || trim > parseInt(anos[ano].match(/T(\d)/)[1])) {
                    anos[ano] = p;
                }
            }
        });
        periodosExibir = Object.values(anos).sort().slice(-8);
    } else {
        periodosExibir = todosPeriodos;
    }

    // Cabeçalho
    let headerHTML = '<tr><th>Conta</th>';
    periodosExibir.forEach(periodo => {
        const periodoFormatado = formatarPeriodoExibicao(periodo, demonstracoesViewType);
        headerHTML += `<th>${periodoFormatado}</th>`;
    });
    headerHTML += '</tr>';
    thead.innerHTML = headerHTML;

    // Corpo - NOVA ESTRUTURA SEM COLSPAN
    let bodyHTML = '';
    
    for (const [grupoNome, contas] of Object.entries(config)) {
        if (contas.length === 0) continue;

        // Linha de cabeçalho do grupo - SEM COLSPAN, com células vazias
        bodyHTML += `<tr class="grupo-row">`;
        bodyHTML += `<td class="grupo-header">${grupoNome}</td>`;
        
        // Adiciona células vazias para cada período (mantém estrutura da tabela)
        periodosExibir.forEach(() => {
            bodyHTML += `<td class="grupo-header-empty"></td>`;
        });
        bodyHTML += `</tr>`;

        // Contas do grupo
        contas.forEach(contaConfig => {
            const dadosConta = demonstracoesFinanceirasData.balancos[grupoNome]?.[contaConfig.codigo];
            
            if (!dadosConta) return;

            bodyHTML += `<tr><td title="${contaConfig.nomeCompleto}">${contaConfig.nome}</td>`;

            periodosExibir.forEach(periodo => {
                let valor = dadosConta.valores[periodo];

                if (demonstracoesViewType === 'anual' && (grupoNome === 'DRE' || grupoNome === 'DFC')) {
                    const ano = periodo.match(/(\d{4})/)[1];
                    const trimestre = parseInt(periodo.match(/T(\d)/)[1]);
                    
                    valor = 0;
                    for (let t = 1; t <= trimestre; t++) {
                        const p = `${ano}T${t}`;
                        const v = dadosConta.valores[p];
                        if (v !== null && v !== undefined) {
                            valor += v;
                        }
                    }
                }

                const valorFormatado = formatarValorDemonstracoes(valor);
                bodyHTML += `<td>${valorFormatado}</td>`;
            });

            bodyHTML += '</tr>';
        });
    }

    tbody.innerHTML = bodyHTML;

    const primeiroFormatado = formatarPeriodoExibicao(periodosExibir[0], demonstracoesViewType);
    const ultimoFormatado = formatarPeriodoExibicao(periodosExibir[periodosExibir.length - 1], demonstracoesViewType);
    footer.textContent = `Dados referentes ao período ${primeiroFormatado} a ${ultimoFormatado}`;
    document.getElementById('analiseBalancosFooter').style.display = 'block';
    document.getElementById('analiseBalancosTableWrapper').style.display = 'block';
}



// Renderiza gráfico de balanços
function renderDemonstracoesFinanceirasGrafico() {
    const ctx = document.getElementById('analiseBalancosChart');
    if (!ctx || !demonstracoesFinanceirasData) return;

    if (demonstracoesFinanceirasChart) {
        demonstracoesFinanceirasChart.destroy();
    }

    const config = demonstracoesFinanceirasData.ehFinanceira ? CONTAS_BALANCOS.FINANCEIRAS : CONTAS_BALANCOS.NAOFINANCEIRAS;
    const primeiroArquivo = Object.values(demonstracoesFinanceirasData.balancos)[0];
    const primeiroItem = Object.values(primeiroArquivo)[0];
    const todosPeriodos = Object.keys(primeiroItem.valores).sort();

    let periodosExibir;
    if (demonstracoesViewType === 'anual') {
        // Anual: último trimestre de cada ano
        const anos = {};
        todosPeriodos.forEach(p => {
            const match = p.match(/(\d{4})T(\d)/);
            if (match) {
                const ano = match[1];
                const trim = parseInt(match[2]);
                if (!anos[ano] || trim > parseInt(anos[ano].match(/T(\d)/)[1])) {
                    anos[ano] = p;
                }
            }
        });
        periodosExibir = Object.values(anos).sort().slice(-12); // Últimos 12 anos
    } else {
        // Trimestral: TODO O HISTÓRICO (não limita)
        periodosExibir = todosPeriodos;
    }

    const labels = periodosExibir.map(p => formatarPeriodoExibicao(p, demonstracoesViewType));

    const contasSelecionadas = config[demonstracaoTipoAtivo];
    
    if (!contasSelecionadas || contasSelecionadas.length === 0) {
        console.warn(`Tipo ${demonstracaoTipoAtivo} não possui contas configuradas`);
        return;
    }

    // Datasets
    const datasets = [];
    const coresLinha = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    const coresBarra = ['#6366f1', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#f472b6'];
    const coresUsar = demonstracaoTipoAtivo === 'DFC' ? coresBarra : coresLinha;
    
    let corIndex = 0;

    contasSelecionadas.forEach(contaConfig => {
        const dadosConta = demonstracoesFinanceirasData.balancos[demonstracaoTipoAtivo]?.[contaConfig.codigo];
        if (!dadosConta) return;

        const dados = periodosExibir.map(periodo => {
            let valor = dadosConta.valores[periodo];

            if (demonstracoesViewType === 'anual' && (demonstracaoTipoAtivo === 'DRE' || demonstracaoTipoAtivo === 'DFC')) {
                const ano = periodo.match(/(\d{4})/)[1];
                const trimestre = parseInt(periodo.match(/T(\d)/)[1]);
                
                valor = 0;
                for (let t = 1; t <= trimestre; t++) {
                    const p = `${ano}T${t}`;
                    const v = dadosConta.valores[p];
                    if (v !== null && v !== undefined) {
                        valor += v;
                    }
                }
            }

            return valor ? valor / 1000000 : null;
        });

        datasets.push({
            label: contaConfig.nome,
            data: dados,
            borderColor: coresUsar[corIndex % coresUsar.length],
            backgroundColor: demonstracaoTipoAtivo === 'DFC' 
                ? coresUsar[corIndex % coresUsar.length] 
                : coresUsar[corIndex % coresUsar.length] + '20',
            borderWidth: demonstracaoTipoAtivo === 'DFC' ? 0 : 3,
            tension: 0.4,
            fill: demonstracaoTipoAtivo !== 'DFC'
        });

        corIndex++;
    });

    const tipoGrafico = demonstracaoTipoAtivo === 'DFC' ? 'bar' : 'line';

    demonstracoesFinanceirasChart = new Chart(ctx, {
        type: tipoGrafico,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 20, // Espaço extra no topo para a legenda
                    bottom: 10
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'start',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 12, // Aumentado de 10 para 12
                        font: {
                            size: 11,
                            family: "'Inter', sans-serif"
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 13,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            return `${label}: R$ ${value.toFixed(2)}mi`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: demonstracaoTipoAtivo === 'DFC',
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toFixed(0) + 'mi';
                        },
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 10
                        },
                        maxRotation: 45, // Rotação para acomodar mais períodos
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });

    document.getElementById('analiseBalancosChartWrapper').style.display = 'block';
}


// Formata valores em milhares (0.000mi)
function formatarValorDemonstracoes(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) {
        return '-';
    }

    const milhoes = valor / 1000000;
    
    if (Math.abs(milhoes) >= 1000) {
        return (milhoes / 1000).toFixed(3).replace('.', ',') + 'bi';
    }
    
    return milhoes.toFixed(3).replace('.', ',') + 'mi';
}

console.log('✅ Análise dos Balanços (Demonstrações Financeiras) inicializada');



/* ========================================
   COMUNICADOS DA EMPRESA
   ======================================== */

let comunicadosEmpresaData = null;

// Hook de carregamento no loadAcaoData
const originalLoadAcaoDataComunicados = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataComunicados.call(this, ticker);
    await loadComunicadosEmpresa(ticker);
};



// Carrega comunicados da empresa
async function loadComunicadosEmpresa(ticker) {
    try {
        console.log('Carregando comunicados da empresa de', ticker, '...');

        const tickerPasta = obterTickerPasta(ticker);
        const timestamp = new Date().getTime();
        const url = `https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/noticias.json?t=${timestamp}`;

        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Arquivo de comunicados não encontrado');
        }

        const data = await response.json();
        
        // Extrai array de notícias
        let comunicados = [];
        
        if (data.noticias && Array.isArray(data.noticias)) {
            comunicados = data.noticias;
        } else {
            throw new Error('Estrutura de dados inválida');
        }
        
        if (comunicados.length === 0) {
            throw new Error('Nenhum comunicado disponível');
        }
        
        // Ordena por data (mais recente primeiro)
        comunicados.sort((a, b) => {
            const dataA = new Date(a.data);
            const dataB = new Date(b.data);
            return dataB - dataA;
        });

        comunicadosEmpresaData = {
            ticker: ticker,
            empresa: data.empresa || {},
            total: data.total_noticias || comunicados.length,
            ultima_atualizacao: data.ultima_atualizacao,
            comunicados: comunicados
        };

        console.log(`${comunicados.length} comunicado(s) carregado(s)`);

        renderComunicadosEmpresa();

    } catch (error) {
        console.error('Erro ao carregar comunicados:', error);
        document.getElementById('comunicadosEmpresaSection').style.display = 'none';
    }
}

// Formata data ISO para exibição (2026-01-05 -> 05 jan. 2026)
function formatarDataComunicado(dataISO) {
    const data = new Date(dataISO + 'T00:00:00');
    const opcoes = { day: '2-digit', month: 'short', year: 'numeric' };
    return data.toLocaleDateString('pt-BR', opcoes);
}

// Verifica se comunicado é novo (últimos 7 dias)
function comunicadoEhNovo(dataISO) {
    const data = new Date(dataISO + 'T00:00:00');
    const hoje = new Date();
    const diasDiferenca = (hoje - data) / (1000 * 60 * 60 * 24);
    return diasDiferenca <= 7;
}

// Agrupa comunicados por mês/ano
function agruparComunicadosPorMes(comunicados) {
    const grupos = {};
    
    comunicados.forEach(com => {
        const data = new Date(com.data + 'T00:00:00');
        const mesAno = `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, '0')}`;
        
        if (!grupos[mesAno]) {
            grupos[mesAno] = {
                titulo: data.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }),
                comunicados: []
            };
        }
        
        grupos[mesAno].comunicados.push(com);
    });
    
    return grupos;
}

// Extrai ID do comunicado da URL
function extrairIdComunicado(url) {
    const match = url.match(/idNoticia=(\d+)/);
    return match ? match[1] : 'N/A';
}

// Define cor da badge por categoria
function getCorCategoria(categoria) {
    const cores = {
        'Governança': { bg: '#dbeafe', text: '#1e40af' },
        'Aviso': { bg: '#fef3c7', text: '#92400e' },
        'Outros': { bg: '#e5e7eb', text: '#374151' },
        'Resultados': { bg: '#d1fae5', text: '#065f46' },
        'Dividendos': { bg: '#fce7f3', text: '#9f1239' }
    };
    
    return cores[categoria] || cores['Outros'];
}

// Renderiza card de comunicado
function renderComunicadoCard(comunicado) {
    const ehNovo = comunicadoEhNovo(comunicado.data);
    const dataFormatada = formatarDataComunicado(comunicado.data);
    const idComunicado = extrairIdComunicado(comunicado.url);
    const corCategoria = getCorCategoria(comunicado.categoria);
    
    // Limpa o título removendo espaços extras
    const tituloLimpo = comunicado.titulo.trim();
    const headlineLimpo = comunicado.headline.trim();
    
    return `
        <div class="comunicado-card">
            <div class="comunicado-card-header">
                <div class="comunicado-data">
                    <i class="far fa-calendar"></i>
                    <span>${dataFormatada}</span>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    ${ehNovo ? `
                        <div class="comunicado-badge novo">
                            <i class="fas fa-star"></i>
                            <span>Novo</span>
                        </div>
                    ` : ''}
                    <div class="comunicado-badge" style="background: ${corCategoria.bg}; color: ${corCategoria.text};">
                        <span>${comunicado.categoria}</span>
                    </div>
                </div>
            </div>
            
            <h3 class="comunicado-titulo">${tituloLimpo}</h3>
            <p class="comunicado-assunto">${headlineLimpo}</p>
            
            <div class="comunicado-footer">
                <div class="comunicado-protocolo">
                    <i class="fas fa-file-alt"></i>
                    <span>ID: ${idComunicado}</span>
                </div>
                <a href="${comunicado.url}" target="_blank" rel="noopener noreferrer" class="comunicado-link">
                    <i class="fas fa-external-link-alt"></i>
                    <span>Ver Detalhes</span>
                </a>
            </div>
        </div>
    `;
}

// Renderiza seção de comunicados
function renderComunicadosEmpresa() {
    const section = document.getElementById('comunicadosEmpresaSection');
    const loading = document.getElementById('comunicadosEmpresaLoading');
    const content = document.getElementById('comunicadosEmpresaContent');
    const empty = document.getElementById('comunicadosEmpresaEmpty');
    const subtitle = document.getElementById('comunicadosEmpresaSubtitle');
    const recentes = document.getElementById('comunicadosRecentes');
    const verMaisContainer = document.getElementById('comunicadosVerMaisContainer');
    const antigos = document.getElementById('comunicadosAntigos');

    if (!comunicadosEmpresaData || comunicadosEmpresaData.comunicados.length === 0) {
        loading.style.display = 'none';
        empty.style.display = 'flex';
        section.style.display = 'block';
        return;
    }

    const totalComunicados = comunicadosEmpresaData.comunicados.length;
    const nomeEmpresa = comunicadosEmpresaData.empresa.nome || comunicadosEmpresaData.ticker;
    
    loading.style.display = 'none';
    content.style.display = 'block';
    section.style.display = 'block';
    
    subtitle.textContent = `${nomeEmpresa} - ${totalComunicados} comunicado${totalComunicados !== 1 ? 's' : ''} disponível${totalComunicados !== 1 ? 'is' : ''}`;

    // Renderiza 3 comunicados mais recentes
    const comunicadosRecentes = comunicadosEmpresaData.comunicados.slice(0, 3);
    recentes.innerHTML = comunicadosRecentes.map(com => renderComunicadoCard(com)).join('');

    // Se houver mais de 3, mostra botão "Ver Mais"
    if (totalComunicados > 3) {
        verMaisContainer.style.display = 'block';
        
        // Agrupa comunicados antigos por mês
        const comunicadosAntigos = comunicadosEmpresaData.comunicados.slice(3);
        const gruposPorMes = agruparComunicadosPorMes(comunicadosAntigos);
        
        let antigosHTML = '';
        
        Object.keys(gruposPorMes).sort().reverse().forEach(mesAno => {
            const grupo = gruposPorMes[mesAno];
            const grupoId = `mes-${mesAno}`;
            
            antigosHTML += `
                <div class="comunicados-mes-grupo">
                    <div class="comunicados-mes-header" onclick="toggleMesComunicados('${grupoId}')">
                        <i class="far fa-calendar-alt"></i>
                        <h3 class="comunicados-mes-titulo">${grupo.titulo}</h3>
                        <span class="comunicados-mes-count">${grupo.comunicados.length}</span>
                        <i class="fas fa-chevron-down comunicados-mes-toggle"></i>
                    </div>
                    <div class="comunicados-mes-conteudo" id="${grupoId}">
                        ${grupo.comunicados.map(com => renderComunicadoCard(com)).join('')}
                    </div>
                </div>
            `;
        });
        
        antigos.innerHTML = antigosHTML;
    } else {
        verMaisContainer.style.display = 'none';
    }

    // Inicializa botão Ver Mais
    initComunicadosVerMais();
}

// Inicializa botão Ver Mais
function initComunicadosVerMais() {
    const btn = document.getElementById('comunicadosVerMaisBtn');
    const antigos = document.getElementById('comunicadosAntigos');
    
    if (!btn) return;
    
    // Remove event listeners anteriores
    const novoBotao = btn.cloneNode(true);
    btn.parentNode.replaceChild(novoBotao, btn);
    
    novoBotao.addEventListener('click', () => {
        const isExpanded = antigos.style.display === 'block';
        
        if (isExpanded) {
            antigos.style.display = 'none';
            novoBotao.classList.remove('expanded');
            novoBotao.querySelector('span').textContent = 'Ver comunicados anteriores';
        } else {
            antigos.style.display = 'block';
            novoBotao.classList.add('expanded');
            novoBotao.querySelector('span').textContent = 'Ocultar comunicados anteriores';
            
            // Scroll suave até os comunicados antigos
            setTimeout(() => {
                antigos.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        }
    });
}

// Toggle expansão de mês
function toggleMesComunicados(grupoId) {
    const header = event.currentTarget;
    const conteudo = document.getElementById(grupoId);
    
    if (conteudo.classList.contains('expanded')) {
        conteudo.classList.remove('expanded');
        header.classList.remove('expanded');
    } else {
        conteudo.classList.add('expanded');
        header.classList.add('expanded');
    }
}

console.log('✅ Comunicados da Empresa inicializado');


// ============================================
// NOTICIÁRIO EMPRESARIAL
// ============================================

let currentNewsIndex = 0;
let newsData = [];
let autoSlideInterval = null;

// Hook de carregamento
const originalLoadAcaoDataNoticias = loadAcaoData;
loadAcaoData = async function(ticker) {
    await originalLoadAcaoDataNoticias.call(this, ticker);
    await carregarNoticiasEmpresa(ticker);
};


// Carrega notícias da empresa
async function carregarNoticiasEmpresa(ticker) {
    try {
        console.log('🔍 Buscando noticiário empresarial de', ticker, '...');
        
        // Normaliza o ticker e obtém a pasta correta
        const tickerNorm = normalizarTicker(ticker);
        const tickerPasta = obterTickerPasta(tickerNorm);
        
        console.log(`📁 Ticker normalizado: ${tickerNorm} | Pasta: ${tickerPasta}`);
        
        // ✅ SOLUÇÃO 1: Cache busting com timestamp
        const timestamp = new Date().getTime();
        const url = `https://raw.githubusercontent.com/Antoniosiqueiracnpi-t/Projeto_Monalytics/main/balancos/${tickerPasta}/noticiario.json?t=${timestamp}`;
        
        console.log(`🌐 URL: ${url}`);
        
        // ✅ SOLUÇÃO 2: Configuração otimizada do fetch
        const response = await fetch(url, {
            method: 'GET',
            cache: 'no-store',
            redirect: 'follow'
        });
        
        if (!response.ok) {
            console.warn(`❌ HTTP ${response.status}: ${response.statusText}`);
            exibirEstadoVazioNoticias(`Notícias não disponíveis para ${ticker}`);
            return;
        }
        
        // ✅ SOLUÇÃO 3: Sempre usar .text() primeiro (ignora Content-Type)
        const rawText = await response.text();
        
        // ✅ SOLUÇÃO 4: Validação de HTML 404
        if (rawText.trim().startsWith('<!DOCTYPE') || rawText.trim().startsWith('<html')) {
            console.warn(`❌ Arquivo não encontrado (retornou HTML)`);
            exibirEstadoVazioNoticias(`Notícias não disponíveis para ${ticker}`);
            return;
        }
        
        // ✅ SOLUÇÃO 5: Parse manual com try-catch
        let data;
        try {
            data = JSON.parse(rawText);
            console.log('✅ JSON parseado com sucesso!');
        } catch (parseError) {
            console.error('❌ Erro ao parsear JSON:', parseError.message);
            console.log('📄 Primeiros 200 caracteres:', rawText.substring(0, 200));
            exibirEstadoVazioNoticias('Formato de notícias inválido');
            return;
        }
        
        // ✅ SOLUÇÃO 6: Validação de estrutura
        if (!data || !data.noticias || !Array.isArray(data.noticias)) {
            console.warn('⚠️ Estrutura JSON inválida');
            console.log('Estrutura recebida:', Object.keys(data || {}));
            exibirEstadoVazioNoticias('Formato de notícias inválido');
            return;
        }
        
        // ✅ SOLUÇÃO 7: Filtrar notícias válidas
        const noticiasValidas = data.noticias.filter(n => 
            n && n.titulo && n.descricao && n.url
        );
        
        if (noticiasValidas.length === 0) {
            console.log('ℹ️ Nenhuma notícia válida encontrada');
            exibirEstadoVazioNoticias('Nenhuma notícia disponível');
            return;
        }
        
        // Pega as 5 mais recentes
        newsData = noticiasValidas.slice(0, 5);
        
        console.log(`✅ ${newsData.length} notícias carregadas com sucesso!`);
        console.table(newsData.map(n => ({
            data: n.data,
            titulo: n.titulo.substring(0, 50) + '...'
        })));
        
        // Renderiza
        renderizarNoticias();
        atualizarInfoUltimaAtualizacao(data.ultima_atualizacao);
        iniciarAutoSlide();
        
    } catch (error) {
        console.error('❌ Erro fatal ao carregar notícias:', error);
        console.error('Stack trace:', error.stack);
        exibirEstadoVazioNoticias('Erro ao carregar notícias');
    }
}




// Renderiza as notícias no carrossel
function renderizarNoticias() {
    const carousel = document.getElementById('newsCarousel');
    const dotsContainer = document.getElementById('newsCarouselDots');
    
    if (!carousel || !dotsContainer) return;
    
    // Limpa conteúdo anterior
    carousel.innerHTML = '';
    dotsContainer.innerHTML = '';
    
    // Cria os itens de notícia
    newsData.forEach((noticia, index) => {
        const newsItem = criarItemNoticia(noticia, index);
        carousel.appendChild(newsItem);
        
        // Cria dot de navegação
        const dot = document.createElement('div');
        dot.className = `noticiario-dot ${index === 0 ? 'active' : ''}`;
        dot.onclick = () => irParaNoticia(index);
        dotsContainer.appendChild(dot);
    });
    
    // Configura navegação
    configurarNavegacaoNoticias();
}

// Cria um item de notícia
function criarItemNoticia(noticia, index) {
    const item = document.createElement('div');
    item.className = `noticiario-item ${index === 0 ? 'active' : ''}`;
    
    const data = formatarDataNoticia(noticia.data_hora || noticia.data);
    const fonte = noticia.fonte || 'Google News';
    const tipo = formatarTipoNoticia(noticia.tipo);
    
    item.innerHTML = `
        <div class="noticiario-item-header">
            <div class="noticiario-item-date">
                <i class="fas fa-calendar-alt"></i>
                <span>${data}</span>
            </div>
            <div class="noticiario-item-source">
                <i class="fas fa-globe"></i>
                <span>${fonte}</span>
            </div>
        </div>
        <h3 class="noticiario-item-title">${noticia.titulo}</h3>
        <p class="noticiario-item-description">${noticia.descricao}</p>
        <div class="noticiario-item-footer">
            <div class="noticiario-item-type">
                <i class="fas fa-tag"></i>
                <span>${tipo}</span>
            </div>
            <a href="${noticia.url}" target="_blank" rel="noopener noreferrer" class="noticiario-read-more-btn">
                Ler notícia completa
                <i class="fas fa-arrow-right"></i>
            </a>
        </div>
    `;
    
    return item;
}

// Formata a data da notícia
function formatarDataNoticia(dataHora) {
    try {
        const data = new Date(dataHora);
        const hoje = new Date();
        const diferenca = Math.floor((hoje - data) / (1000 * 60 * 60 * 24));
        
        if (diferenca === 0) return 'Hoje';
        if (diferenca === 1) return 'Ontem';
        if (diferenca < 7) return `Há ${diferenca} dias`;
        if (diferenca < 30) return `Há ${Math.floor(diferenca / 7)} semanas`;
        if (diferenca < 365) return `Há ${Math.floor(diferenca / 30)} meses`;
        
        return data.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    } catch (error) {
        return 'Data indisponível';
    }
}

// Formata o tipo de notícia
function formatarTipoNoticia(tipo) {
    const tipos = {
        'noticia_mercado': 'Notícia de Mercado',
        'comunicado': 'Comunicado',
        'resultado': 'Resultado Financeiro',
        'dividendos': 'Dividendos',
        'default': 'Notícia'
    };
    
    return tipos[tipo] || tipos.default;
}

// Atualiza informação de última atualização
function atualizarInfoUltimaAtualizacao(ultimaAtualizacao) {
    const infoElement = document.getElementById('newsUpdateInfo');
    if (!infoElement) return;
    
    try {
        const data = new Date(ultimaAtualizacao);
        const dataFormatada = data.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        infoElement.innerHTML = `
            <i class="fas fa-sync-alt"></i>
            <span>Última atualização: ${dataFormatada}</span>
        `;
    } catch (error) {
        infoElement.innerHTML = `
            <i class="fas fa-sync-alt"></i>
            <span>Notícias atualizadas</span>
        `;
    }
}

// Exibe estado vazio
function exibirEstadoVazioNoticias(mensagem) {
    const carousel = document.getElementById('newsCarousel');
    const dotsContainer = document.getElementById('newsCarouselDots');
    
    if (!carousel) return;
    
    carousel.innerHTML = `
        <div class="news-empty-state">
            <div class="news-empty-icon">
                <i class="fas fa-newspaper"></i>
            </div>
            <div class="news-empty-text">${mensagem}</div>
        </div>
    `;
    
    if (dotsContainer) {
        dotsContainer.innerHTML = '';
    }
    
    // Desabilita botões de navegação
    const prevBtn = document.getElementById('newsPrev');
    const nextBtn = document.getElementById('newsNext');
    if (prevBtn) prevBtn.disabled = true;
    if (nextBtn) nextBtn.disabled = true;
}

// Configura navegação
function configurarNavegacaoNoticias() {
    const prevBtn = document.getElementById('newsPrev');
    const nextBtn = document.getElementById('newsNext');
    
    if (prevBtn) {
        prevBtn.onclick = () => navegarNoticias('prev');
        prevBtn.disabled = currentNewsIndex === 0;
    }
    
    if (nextBtn) {
        nextBtn.onclick = () => navegarNoticias('next');
        nextBtn.disabled = currentNewsIndex === newsData.length - 1;
    }
}

// Navega entre notícias
function navegarNoticias(direcao) {
    pausarAutoSlide();
    
    if (direcao === 'next' && currentNewsIndex < newsData.length - 1) {
        currentNewsIndex++;
    } else if (direcao === 'prev' && currentNewsIndex > 0) {
        currentNewsIndex--;
    }
    
    atualizarNoticiaAtiva();
    iniciarAutoSlide();
}

// Vai para notícia específica
function irParaNoticia(index) {
    pausarAutoSlide();
    currentNewsIndex = index;
    atualizarNoticiaAtiva();
    iniciarAutoSlide();
}

// Atualiza notícia ativa
function atualizarNoticiaAtiva() {
    // Atualiza itens de notícia
    const newsItems = document.querySelectorAll('.noticiario-item');
    newsItems.forEach((item, index) => {
        item.classList.toggle('active', index === currentNewsIndex);
    });
    
    // Atualiza dots
    const dots = document.querySelectorAll('.noticiario-dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentNewsIndex);
    });
    
    // Atualiza botões
    const prevBtn = document.getElementById('newsPrev');
    const nextBtn = document.getElementById('newsNext');
    if (prevBtn) prevBtn.disabled = (currentNewsIndex === 0);
    if (nextBtn) nextBtn.disabled = (currentNewsIndex === newsData.length - 1);
}

// Inicia auto-slide
function iniciarAutoSlide() {
    pausarAutoSlide();
    
    autoSlideInterval = setInterval(() => {
        if (currentNewsIndex < newsData.length - 1) {
            currentNewsIndex++;
        } else {
            currentNewsIndex = 0;
        }
        atualizarNoticiaAtiva();
    }, 8000); // Troca a cada 8 segundos
}

// Pausa auto-slide
function pausarAutoSlide() {
    if (autoSlideInterval) {
        clearInterval(autoSlideInterval);
        autoSlideInterval = null;
    }
}

// Pausa auto-slide quando o usuário interage
document.addEventListener('DOMContentLoaded', () => {
    const newsCard = document.querySelector('.news-card');
    if (newsCard) {
        newsCard.addEventListener('mouseenter', pausarAutoSlide);
        newsCard.addEventListener('mouseleave', iniciarAutoSlide);
    }
});
