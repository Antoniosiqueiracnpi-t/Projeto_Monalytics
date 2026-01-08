// Carrega notícias da empresa
async function carregarNoticiasEmpresa(ticker) {
    try {
        console.log('🔍 Buscando noticiário empresarial de', ticker, '...');
        
        // CORREÇÃO: Remove o último dígito do ticker (PETR4 -> PETR)
        const tickerPasta = obterTickerPasta(ticker);
        
        const response = await fetch(`balancos/${tickerPasta}/noticiario.json`);
        
        if (!response.ok) {
            exibirEstadoVazioNoticias('Notícias não disponíveis para esta empresa');
            return;
        }
        
        const data = await response.json();
        newsData = data.noticias.slice(0, 5); // Pega as 5 mais recentes
        
        if (newsData.length === 0) {
            exibirEstadoVazioNoticias('Nenhuma notícia disponível');
            return;
        }
        
        renderizarNoticias();
        atualizarInfoUltimaAtualizacao(data.ultima_atualizacao);
        iniciarAutoSlide();
        
    } catch (error) {
        console.error('Erro ao carregar notícias:', error);
        exibirEstadoVazioNoticias('Erro ao carregar notícias');
    }
}
