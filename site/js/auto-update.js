/**
 * Sistema de Auto-Atualização Monalytics
 * Verifica periodicamente se há novos dados disponíveis
 * e recarrega automaticamente sem necessidade de F5
 */

class MonalyticsAutoUpdater {
  constructor(config = {}) {
    this.config = {
      checkInterval: config.checkInterval || 5, // minutos
      timestampUrl: config.timestampUrl || '/data/ultima_atualizacao.json',
      showNotifications: config.showNotifications !== false,
      debug: config.debug || false
    };
    
    this.lastKnownTimestamp = 0;
    this.isFirstCheck = true;
    this.checkTimer = null;
    
    this.init();
  }

  log(message, ...args) {
    if (this.config.debug) {
      console.log(`[AutoUpdater] ${message}`, ...args);
    }
  }

  async init() {
    this.log('Iniciando auto-updater...');
    
    // Carregar timestamp inicial
    await this.checkForUpdates();
    this.isFirstCheck = false;
    
    // Iniciar verificação periódica
    this.startPeriodicCheck();
    
    // Adicionar estilos CSS
    this.injectStyles();
    
    this.log(`✅ Configurado para verificar a cada ${this.config.checkInterval} minutos`);
  }

  startPeriodicCheck() {
    const intervalMs = this.config.checkInterval * 60 * 1000;
    
    this.checkTimer = setInterval(() => {
      this.checkForUpdates();
    }, intervalMs);
  }

  async checkForUpdates() {
    try {
      // Adicionar timestamp na URL para evitar cache
      const url = `${this.config.timestampUrl}?t=${Date.now()}`;
      
      const response = await fetch(url, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const serverTimestamp = data.timestamp;
      
      this.log('Timestamp servidor:', serverTimestamp);
      this.log('Timestamp local:', this.lastKnownTimestamp);
      
      // Se é a primeira verificação, apenas salvar o timestamp
      if (this.isFirstCheck) {
        this.lastKnownTimestamp = serverTimestamp;
        this.log('Timestamp inicial registrado');
        return;
      }
      
      // Verificar se há atualizações
      if (serverTimestamp > this.lastKnownTimestamp) {
        this.log('🔄 Novos dados detectados!');
        this.lastKnownTimestamp = serverTimestamp;
        await this.handleUpdate(data);
      } else {
        this.log('✅ Nenhuma atualização disponível');
      }
      
    } catch (error) {
      console.error('[AutoUpdater] Erro ao verificar atualizações:', error);
    }
  }

  async handleUpdate(updateInfo) {
    this.log('Processando atualização...', updateInfo);
    
    // Recarregar dados do dashboard
    await this.reloadDashboardData();
    
    // Mostrar notificação
    if (this.config.showNotifications) {
      this.showNotification(
        'Dados Atualizados!',
        `Última atualização: ${updateInfo.hora || updateInfo.data}`
      );
    }
    
    // Disparar evento customizado para outros scripts
    window.dispatchEvent(new CustomEvent('monalytics:dataUpdated', {
      detail: updateInfo
    }));
  }

  async reloadDashboardData() {
    this.log('Recarregando dados do dashboard...');
    
    try {
      // Se existir função global de reload
      if (typeof window.loadDashboardData === 'function') {
        await window.loadDashboardData();
        this.log('✅ Dashboard recarregado via loadDashboardData()');
        return;
      }
      
      // Se existir função de carregamento de dados
      if (typeof window.carregarDados === 'function') {
        await window.carregarDados();
        this.log('✅ Dashboard recarregado via carregarDados()');
        return;
      }
      
      // Fallback: recarregar página inteira (suave)
      this.log('⚠️ Nenhuma função de reload encontrada, recarregando página...');
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      
    } catch (error) {
      console.error('[AutoUpdater] Erro ao recarregar dados:', error);
    }
  }

  showNotification(title, message) {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = 'monalytics-notification';
    notification.innerHTML = `
      <div class="notification-icon">🔄</div>
      <div class="notification-content">
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
      </div>
      <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  injectStyles() {
    const styles = `
      .monalytics-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 999999;
        min-width: 300px;
        max-width: 400px;
        display: flex;
        align-items: center;
        gap: 12px;
        opacity: 0;
        transform: translateX(400px);
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
      }
      
      .monalytics-notification.show {
        opacity: 1;
        transform: translateX(0);
      }
      
      .monalytics-notification .notification-icon {
        font-size: 24px;
        flex-shrink: 0;
        animation: rotate 1s ease-in-out;
      }
      
      @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      .monalytics-notification .notification-content {
        flex: 1;
      }
      
      .monalytics-notification .notification-title {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 4px;
      }
      
      .monalytics-notification .notification-message {
        font-size: 12px;
        opacity: 0.9;
      }
      
      .monalytics-notification .notification-close {
        background: transparent;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        opacity: 0.7;
        transition: opacity 0.2s;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .monalytics-notification .notification-close:hover {
        opacity: 1;
      }
      
      /* Responsivo */
      @media (max-width: 768px) {
        .monalytics-notification {
          top: 10px;
          right: 10px;
          left: 10px;
          min-width: auto;
          max-width: none;
        }
      }
    `;
    
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
  }

  // Método para parar o auto-updater
  stop() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
      this.log('Auto-updater parado');
    }
  }

  // Método para reiniciar o auto-updater
  restart() {
    this.stop();
    this.startPeriodicCheck();
    this.log('Auto-updater reiniciado');
  }

  // Método para forçar verificação manual
  forceCheck() {
    this.log('Verificação manual forçada');
    this.checkForUpdates();
  }
}

// Inicializar automaticamente quando DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAutoUpdater);
} else {
  initAutoUpdater();
}

function initAutoUpdater() {
  // Configuração personalizada (pode ser alterada)
  window.monalyticsUpdater = new MonalyticsAutoUpdater({
    checkInterval: 5,        // Verificar a cada 5 minutos
    showNotifications: true, // Mostrar notificações
    debug: false            // Ativar logs de debug (true para desenvolvimento)
  });
  
  console.log('✅ Monalytics Auto-Updater ativado');
  console.log('💡 Use window.monalyticsUpdater.forceCheck() para verificar manualmente');
}

// Expor globalmente para debug
window.MonalyticsAutoUpdater = MonalyticsAutoUpdater;
