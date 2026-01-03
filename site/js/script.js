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
const GITHUB_BASE_URL = 'https://raw.githubusercontent.com/asiqueira013/Projeto_Monalytics/main/balancos';

const DATA_URLS = {
    bolsa: `${GITHUB_BASE_URL}/IBOV/monitor_diario.json`,
    indicadores: `${GITHUB_BASE_URL}/INDICADORES/indicadores_economicos.json`,
    noticias: `${GITHUB_BASE_URL}/feed_noticias.json`
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

/**
 * Faz requisição HTTP e retorna JSON
 */
async function fetchJSON(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Erro ao carregar ${url}:`, error);
        return null;
    }
}

// =========================== SLIDE 1: DESTAQUES DA BOLSA ===========================

/**
 * Carrega e renderiza dados da bolsa
 */
async function loadBolsaData() {
    const data = await fetchJSON(DATA_URLS.bolsa);
    
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
    const data = await fetchJSON(DATA_URLS.indicadores);
    
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
    const data = await fetchJSON(DATA_URLS.noticias);
    
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
