class RecommendationsDisplay {
    constructor() {
        // Автоматичне визначення шляхів
        const repoName = 'pocket_trading_bot';
        const isLocal = window.location.hostname.includes('localhost') || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.protocol === 'file:';
        
        if (isLocal) {
            this.recommendationsUrl = 'data/recommendations.json';
        } else {
            this.recommendationsUrl = `/${repoName}/data/recommendations.json`;
        }
        
        this.kyivTZ = 'Europe/Kiev';
        this.language = localStorage.getItem('language') || 'uk';
        this.updateInterval = null;
        this.autoUpdateTimer = null;
        this.nextUpdateTime = null;
        
        console.log("🤖 Recommendations Display ініціалізовано");
        console.log("🌐 URL:", this.recommendationsUrl);
        console.log("🗣️ Мова:", this.language);
        
        this.translations = {
            uk: {
                title: "Курсовий радник AI",
                subtitle: "Макроекономічні рекомендації на основі аналізу новин",
                frequency: "Оновлення:",
                minConfidence: "Мін. впевненість:",
                model: "Модель:",
                newsBased: "На основі новин",
                nextUpdate: "Наступне оновлення:",
                lastUpdate: "Останнє оновлення",
                kievTime: "(Київський час)",
                recommendationsCount: "Рекомендацій",
                activeNow: "активних зараз",
                newsAnalyzed: "Новин проаналізовано",
                last24h: "за останні 24 год",
                marketSentiment: "Настрій ринку",
                calculating: "розрахунок...",
                marketOverview: "Огляд ринку",
                serverTime: "Київський час:",
                marketStatus: "Статус ринків",
                topCurrencies: "Найкращі валюти",
                keyRisks: "Ключові ризики",
                currentRecommendations: "Поточні рекомендації",
                refresh: "Оновити",
                loadingRecommendations: "Завантаження рекомендацій...",
                firstLoad: "Перше оновлення через",
                noRecommendationsNow: "Наразі немає рекомендацій",
                nextAutoUpdate: "Наступне автоматичне оновлення о",
                howItWorks: "Як працює система",
                dataSources: "Джерела даних:",
                dataSourcesDesc: "Новини з Reuters, Bloomberg, НБУ, економічні показники",
                analysisFrequency: "Частота аналізу:",
                analysisFrequencyDesc: "4 рази на день (08:00, 12:00, 16:00, 20:00)",
                aiAnalysis: "AI аналіз:",
                aiAnalysisDesc: "GPT OSS 120B аналізує новини та генерує рекомендації",
                recommendationTypes: "Типи рекомендацій:",
                recommendationTypesDesc: "Купувати / Уникати з вказівкою причин та ризиків",
                timeframe: "Часовий горизонт:",
                timeframeDesc: "Короткострокові рекомендації (1-3 дні)",
                disclaimer: "Дисклеймер",
                disclaimerText: "Цей аналіз призначений тільки для інформаційних цілей. Це не фінансова порада. Інвестування пов'язане з ризиками.",
                createdWith: "Створено з використанням",
                technologies: "Технології:",
                buy: "КУПУВАТИ",
                avoid: "УНИКАТИ",
                strongBuy: "СИЛЬНО КУПУВАТИ",
                strongAvoid: "СИЛЬНО УНИКАТИ",
                neutral: "НЕЙТРАЛЬНО",
                open: "ВІДКРИТО",
                closed: "ЗАКРИТО",
                lowRisk: "Низький ризик",
                mediumRisk: "Середній ризик",
                highRisk: "Високий ризик",
                confidence: "Впевненість:",
                timeframeLabel: "Часовий горизонт:",
                riskLevel: "Рівень ризику:",
                newsCount: "Новин проаналізовано:",
                analysisTime: "Час аналізу:",
                nextAnalysis: "Наступний аналіз:",
                loading: "Завантаження...",
                errorLoading: "Помилка завантаження",
                retry: "Спробувати ще раз"
            },
            ru: {
                title: "Валютный советник AI",
                subtitle: "Макроэкономические рекомендации на основе анализа новостей",
                frequency: "Обновление:",
                minConfidence: "Мин. уверенность:",
                model: "Модель:",
                newsBased: "На основе новостей",
                nextUpdate: "Следующее обновление:",
                lastUpdate: "Последнее обновление",
                kievTime: "(Киевское время)",
                recommendationsCount: "Рекомендаций",
                activeNow: "активных сейчас",
                newsAnalyzed: "Новостей проанализировано",
                last24h: "за последние 24 часа",
                marketSentiment: "Настроение рынка",
                calculating: "расчет...",
                marketOverview: "Обзор рынка",
                serverTime: "Киевское время:",
                marketStatus: "Статус рынков",
                topCurrencies: "Лучшие валюты",
                keyRisks: "Ключевые риски",
                currentRecommendations: "Текущие рекомендации",
                refresh: "Обновить",
                loadingRecommendations: "Загрузка рекомендаций...",
                firstLoad: "Первое обновление через",
                noRecommendationsNow: "В настоящее время нет рекомендаций",
                nextAutoUpdate: "Следующее автоматическое обновление в",
                howItWorks: "Как работает система",
                dataSources: "Источники данных:",
                dataSourcesDesc: "Новости Reuters, Bloomberg, НБУ, экономические показатели",
                analysisFrequency: "Частота анализа:",
                analysisFrequencyDesc: "4 раза в день (08:00, 12:00, 16:00, 20:00)",
                aiAnalysis: "AI анализ:",
                aiAnalysisDesc: "GPT OSS 120B анализирует новости и генерирует рекомендации",
                recommendationTypes: "Типы рекомендаций:",
                recommendationTypesDesc: "Покупать / Избегать с указанием причин и рисков",
                timeframe: "Временной горизонт:",
                timeframeDesc: "Краткосрочные рекомендации (1-3 дня)",
                disclaimer: "Дисклеймер",
                disclaimerText: "Данный анализ предназначен только для информационных целей. Это не финансовая консультация. Инвестирование связано с рисками.",
                createdWith: "Создано с использованием",
                technologies: "Технологии:",
                buy: "ПОКУПАТЬ",
                avoid: "ИЗБЕГАТЬ",
                strongBuy: "СИЛЬНО ПОКУПАТЬ",
                strongAvoid: "СИЛЬНО ИЗБЕГАТЬ",
                neutral: "НЕЙТРАЛЬНО",
                open: "ОТКРЫТО",
                closed: "ЗАКРЫТО",
                lowRisk: "Низкий риск",
                mediumRisk: "Средний риск",
                highRisk: "Высокий риск",
                confidence: "Уверенность:",
                timeframeLabel: "Временной горизонт:",
                riskLevel: "Уровень риска:",
                newsCount: "Новостей проанализировано:",
                analysisTime: "Время анализа:",
                nextAnalysis: "Следующий анализ:",
                loading: "Загрузка...",
                errorLoading: "Ошибка загрузки",
                retry: "Попробовать еще раз"
            }
        };
        
        this.init();
    }

    async init() {
        await this.setupLanguage();
        this.setupEventListeners();
        this.updateKyivTime();
        setInterval(() => this.updateKyivTime(), 1000);
        
        // Перше завантаження через 2 секунди
        setTimeout(() => {
            console.log("📥 Перше завантаження рекомендацій...");
            this.loadRecommendations();
            this.startAutoUpdate();
        }, 2000);
    }

    setupEventListeners() {
        // Перемикач мови
        document.getElementById('lang-uk')?.addEventListener('click', () => {
            this.switchLanguage('uk');
        });
        
        document.getElementById('lang-ru')?.addEventListener('click', () => {
            this.switchLanguage('ru');
        });
        
        // Кнопка оновлення
        document.getElementById('manual-refresh-btn')?.addEventListener('click', () => {
            this.loadRecommendations(true);
        });
    }

    startAutoUpdate() {
        // Автоматичне оновлення кожні 5 хвилин
        this.updateInterval = setInterval(() => {
            console.log("🔄 Автоматична перевірка оновлень...");
            this.loadRecommendations();
        }, 5 * 60 * 1000); // 5 хвилин
        
        console.log("✅ Автооновлення активоване: кожні 5 хвилин");
    }

    async loadRecommendations(force = false) {
        try {
            // Показуємо індикатор завантаження
            this.showLoadingState();
            
            const timestamp = force ? Date.now() : new Date().setMinutes(0, 0, 0);
            const url = `${this.recommendationsUrl}?t=${timestamp}`;
            
            console.log("📥 Запит до:", url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            console.log("✅ Дані завантажені успішно!");
            console.log("📊 Статистика:", {
                recommendations: data.recommendations?.length || 0,
                lastUpdate: data.last_update,
                marketSentiment: data.market_overview?.overall_sentiment
            });
            
            this.processData(data);
            
            // Оновлюємо час наступного оновлення
            this.updateNextUpdateTimer(data.next_analysis);
            
        } catch (error) {
            console.error('❌ Помилка завантаження даних:', error);
            this.showErrorState(error);
            
            // Спробуємо альтернативний шлях
            this.tryAlternativePaths();
        }
    }

    tryAlternativePaths() {
        const alternativePaths = [
            'data/recommendations.json',
            '/data/recommendations.json',
            './data/recommendations.json',
            'https://raw.githubusercontent.com/Danik25326/pocket_trading_bot/main/data/recommendations.json'
        ];
        
        let currentIndex = 0;
        
        const tryNextPath = () => {
            if (currentIndex >= alternativePaths.length) return;
            
            const testPath = alternativePaths[currentIndex];
            console.log(`🔄 Тестую шлях: ${testPath}`);
            
            fetch(`${testPath}?t=${Date.now()}`)
                .then(response => {
                    if (response.ok) {
                        return response.json().then(data => {
                            console.log(`✅ Знайдено працюючий шлях: ${testPath}`);
                            this.processData(data);
                            this.showMessage('success', 'Підключення відновлено!');
                        });
                    } else {
                        currentIndex++;
                        setTimeout(tryNextPath, 500);
                    }
                })
                .catch(() => {
                    currentIndex++;
                    setTimeout(tryNextPath, 500);
                });
        };
        
        tryNextPath();
    }

    processData(data) {
        // Оновлення часу останнього оновлення
        const lastUpdate = document.getElementById('last-update');
        if (lastUpdate && data.last_update_display) {
            lastUpdate.textContent = data.last_update_display;
        } else if (lastUpdate && data.last_update) {
            lastUpdate.textContent = this.formatDate(new Date(data.last_update));
        }
        
        // Кількість рекомендацій
        const recCount = document.getElementById('recommendations-count');
        if (recCount) {
            recCount.textContent = data.total_recommendations || data.recommendations?.length || 0;
        }
        
        // Кількість новин
        const newsCount = document.getElementById('news-analyzed');
        if (newsCount) {
            newsCount.textContent = data.news_count || 0;
        }
        
        // Настрій ринку
        const marketSentiment = document.getElementById('market-sentiment');
        const sentimentDesc = document.getElementById('sentiment-desc');
        if (marketSentiment && data.market_overview?.overall_sentiment) {
            const sentiment = data.market_overview.overall_sentiment;
            marketSentiment.textContent = this.getSentimentEmoji(sentiment);
            
            if (sentimentDesc) {
                sentimentDesc.textContent = sentiment;
            }
        }
        
        // Оновлення огляду ринку
        this.updateMarketOverview(data.market_overview);
        
        // Оновлення рекомендацій
        this.updateRecommendations(data.recommendations || []);
        
        // Оновлення ризиків
        this.updateRisks(data.market_overview);
        
        // Приховуємо стан завантаження
        this.hideLoadingState();
    }

    updateMarketOverview(overview) {
        if (!overview) return;
        
        // Статус ринків
        const marketStatusList = document.getElementById('market-status-list');
        if (marketStatusList && overview.market_status) {
            let html = '';
            const statuses = overview.market_status;
            
            for (const [market, status] of Object.entries(statuses)) {
                if (market === 'overall') continue;
                
                const isOpen = status.status === 'OPEN';
                html += `
                    <div class="market-status ${isOpen ? 'status-open' : 'status-closed'}">
                        <i class="fas fa-${isOpen ? 'check-circle' : 'times-circle'}"></i>
                        <span>${this.translateMarketName(market)}: ${this.translate(isOpen ? 'open' : 'closed')}</span>
                    </div>
                `;
            }
            
            marketStatusList.innerHTML = html || '<div class="no-data">Немає даних</div>';
        }
        
        // Топ валюти
        const topCurrenciesList = document.getElementById('top-currencies-list');
        if (topCurrenciesList) {
            const topCurrency = overview.top_currency;
            const worstCurrency = overview.worst_currency;
            
            let html = '';
            if (topCurrency && topCurrency !== 'N/A') {
                html += `
                    <div class="currency-item positive">
                        <i class="fas fa-crown"></i>
                        <strong>${topCurrency}</strong> - найкраща валюта
                    </div>
                `;
            }
            
            if (worstCurrency && worstCurrency !== 'N/A') {
                html += `
                    <div class="currency-item negative">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>${worstCurrency}</strong> - найгірша валюта
                    </div>
                `;
            }
            
            if (overview.positive_news_count !== undefined && overview.negative_news_count !== undefined) {
                html += `
                    <div class="currency-item info">
                        <i class="fas fa-newspaper"></i>
                        Позитивних новин: <strong>${overview.positive_news_count}</strong><br>
                        Негативних новин: <strong>${overview.negative_news_count}</strong>
                    </div>
                `;
            }
            
            topCurrenciesList.innerHTML = html || '<div class="no-data">Немає даних</div>';
        }
    }

    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-container');
        const noRecElement = document.getElementById('no-recommendations');
        
        if (!container) return;
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = this.getNoRecommendationsHTML();
            if (noRecElement) {
                noRecElement.style.display = 'block';
            }
            return;
        }
        
        if (noRecElement) {
            noRecElement.style.display = 'none';
        }
        
        // Групуємо рекомендації за типом
        const buyRecommendations = recommendations.filter(r => r.action.includes('BUY'));
        const avoidRecommendations = recommendations.filter(r => r.action.includes('AVOID'));
        const neutralRecommendations = recommendations.filter(r => r.action === 'NEUTRAL');
        
        let html = '';
        
        // Рекомендації "КУПУВАТИ"
        if (buyRecommendations.length > 0) {
            html += `<div class="recommendation-group buy-group">`;
            html += `<h3><i class="fas fa-arrow-up"></i> ${this.translate('buy')} (${buyRecommendations.length})</h3>`;
            html += `<div class="group-content">`;
            
            buyRecommendations.forEach(rec => {
                html += this.createRecommendationHTML(rec, 'buy');
            });
            
            html += `</div></div>`;
        }
        
        // Рекомендації "УНИКАТИ"
        if (avoidRecommendations.length > 0) {
            html += `<div class="recommendation-group avoid-group">`;
            html += `<h3><i class="fas fa-arrow-down"></i> ${this.translate('avoid')} (${avoidRecommendations.length})</h3>`;
            html += `<div class="group-content">`;
            
            avoidRecommendations.forEach(rec => {
                html += this.createRecommendationHTML(rec, 'avoid');
            });
            
            html += `</div></div>`;
        }
        
        // Нейтральні рекомендації
        if (neutralRecommendations.length > 0) {
            html += `<div class="recommendation-group neutral-group">`;
            html += `<h3><i class="fas fa-minus"></i> ${this.translate('neutral')} (${neutralRecommendations.length})</h3>`;
            html += `<div class="group-content">`;
            
            neutralRecommendations.forEach(rec => {
                html += this.createRecommendationHTML(rec, 'neutral');
            });
            
            html += `</div></div>`;
        }
        
        container.innerHTML = html;
    }

    createRecommendationHTML(recommendation, type) {
        const confidencePercent = Math.round(recommendation.confidence * 100);
        const assetClass = this.getAssetClass(recommendation.asset);
        const icon = this.getAssetIcon(recommendation.asset);
        
        let actionText = '';
        let actionClass = '';
        
        switch(recommendation.action) {
            case 'STRONG_BUY':
                actionText = this.translate('strongBuy');
                actionClass = 'strong-buy';
                break;
            case 'BUY':
                actionText = this.translate('buy');
                actionClass = 'buy';
                break;
            case 'STRONG_AVOID':
                actionText = this.translate('strongAvoid');
                actionClass = 'strong-avoid';
                break;
            case 'AVOID':
                actionText = this.translate('avoid');
                actionClass = 'avoid';
                break;
            default:
                actionText = this.translate('neutral');
                actionClass = 'neutral';
        }
        
        return `
            <div class="recommendation-card ${actionClass}">
                <div class="recommendation-header">
                    <div class="asset-info">
                        <div class="asset-icon ${assetClass}">
                            ${icon}
                        </div>
                        <div>
                            <div class="asset-name">${recommendation.asset}</div>
                            <div class="action-badge ${actionClass}">${actionText}</div>
                        </div>
                    </div>
                    <div class="confidence-badge">
                        ${confidencePercent}%
                    </div>
                </div>
                
                <div class="recommendation-details">
                    <div class="detail-item">
                        <div class="label">
                            <i class="fas fa-info-circle"></i> ${this.translate('confidence')}
                        </div>
                        <div class="value">
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidencePercent}%"></div>
                            </div>
                            <span class="confidence-text">${confidencePercent}%</span>
                        </div>
                    </div>
                    
                    <div class="detail-item">
                        <div class="label">
                            <i class="fas fa-clock"></i> ${this.translate('timeframeLabel')}
                        </div>
                        <div class="value">${recommendation.timeframe || '1-3 дні'}</div>
                    </div>
                    
                    <div class="detail-item">
                        <div class="label">
                            <i class="fas fa-exclamation-triangle"></i> ${this.translate('riskLevel')}
                        </div>
                        <div class="value">
                            <span class="risk-badge risk-${recommendation.risk_level || 'medium'}">
                                ${this.translate(recommendation.risk_level || 'mediumRisk')}
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="recommendation-reason">
                    <div class="reason-header">
                        <i class="fas fa-lightbulb"></i> Причина рекомендації
                    </div>
                    <div class="reason-text">${recommendation.reason || 'Аналіз на основі останніх новин та економічних показників'}</div>
                </div>
                
                ${recommendation.generated_at ? `
                <div class="recommendation-footer">
                    <small>
                        <i class="fas fa-calendar"></i> 
                        ${this.translate('analysisTime')} ${this.formatDate(new Date(recommendation.generated_at))}
                    </small>
                </div>
                ` : ''}
            </div>
        `;
    }

    updateRisks(overview) {
        const risksList = document.getElementById('key-risks-list');
        if (!risksList || !overview) return;
        
        let html = '';
        
        // Додаємо загальні ризики на основі огляду
        if (overview.negative_news_count > overview.positive_news_count * 1.5) {
            html += `<div class="risk-item"><i class="fas fa-exclamation-circle"></i> Переважають негативні новини</div>`;
        }
        
        if (overview.worst_currency && overview.worst_currency !== 'N/A') {
            html += `<div class="risk-item"><i class="fas fa-chart-line"></i> Ризики для ${overview.worst_currency}</div>`;
        }
        
        if (overview.market_status?.overall === 'INACTIVE') {
            html += `<div class="risk-item"><i class="fas fa-exchange-alt"></i> Обмежена активність ринків</div>`;
        }
        
        // Загальні ризики
        html += `<div class="risk-item"><i class="fas fa-globe"></i> Геополітична невизначеність</div>`;
        html += `<div class="risk-item"><i class="fas fa-chart-bar"></i> Волатильність на ринках</div>`;
        
        risksList.innerHTML = html || '<div class="no-data">Немає інформації про ризики</div>';
    }

    updateNextUpdateTimer(nextAnalysisTime) {
        if (!nextAnalysisTime) return;
        
        const updateTimer = () => {
            const now = new Date();
            const nextTime = new Date(nextAnalysisTime);
            const timeLeft = nextTime - now;
            
            if (timeLeft <= 0) {
                // Якщо час минув, оновлюємо дані
                this.loadRecommendations();
                return;
            }
            
            const hours = Math.floor(timeLeft / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
            
            const timerElement = document.getElementById('next-update-timer');
            const autoTimeElement = document.getElementById('next-auto-time');
            
            if (timerElement) {
                timerElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
            
            if (autoTimeElement) {
                autoTimeElement.textContent = nextTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
        };
        
        // Оновлюємо таймер кожну секунду
        updateTimer();
        if (this.autoUpdateTimer) {
            clearInterval(this.autoUpdateTimer);
        }
        this.autoUpdateTimer = setInterval(updateTimer, 1000);
    }

    updateKyivTime() {
        const now = new Date();
        const timeElement = document.getElementById('server-time');
        
        if (timeElement) {
            try {
                timeElement.textContent = now.toLocaleTimeString('uk-UA', {
                    timeZone: this.kyivTZ,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            } catch (e) {
                timeElement.textContent = now.toLocaleTimeString();
            }
        }
    }

    // Допоміжні методи
    showLoadingState() {
        const container = document.getElementById('recommendations-container');
        if (container) {
            container.innerHTML = `
                <div class="loading-state">
                    <div class="spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <p>${this.translate('loadingRecommendations')}</p>
                </div>
            `;
        }
    }

    hideLoadingState() {
        // Приховуємо спінер, якщо він є
    }

    showErrorState(error) {
        const container = document.getElementById('recommendations-container');
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>${this.translate('errorLoading')}</h3>
                    <p>${error.message || 'Невідома помилка'}</p>
                    <button class="retry-btn" onclick="recommendationsDisplay.loadRecommendations(true)">
                        <i class="fas fa-redo"></i> ${this.translate('retry')}
                    </button>
                </div>
            `;
        }
    }

    getNoRecommendationsHTML() {
        return `
            <div class="empty-state">
                <i class="fas fa-chart-line"></i>
                <h3>${this.translate('noRecommendationsNow')}</h3>
                <p>${this.translate('nextAutoUpdate')} <span id="next-auto-time">--:--</span></p>
            </div>
        `;
    }

    formatDate(date) {
        if (!date) return '--:--:--';
        try {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch (e) {
            return date.toString();
        }
    }

    getSentimentEmoji(sentiment) {
        const emojis = {
            'ПОЗИТИВНИЙ': '📈',
            'POSITIVE': '📈',
            'НЕГАТИВНИЙ': '📉',
            'NEGATIVE': '📉',
            'НЕЙТРАЛЬНИЙ': '➡️',
            'NEUTRAL': '➡️'
        };
        return emojis[sentiment?.toUpperCase()] || '➡️';
    }

    getAssetClass(asset) {
        if (['BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'ADA', 'DOT', 'DOGE'].includes(asset)) {
            return 'crypto-icon';
        } else if (['GOLD', 'SILVER', 'OIL'].includes(asset)) {
            return 'commodity-icon';
        } else {
            return 'currency-icon';
        }
    }

    getAssetIcon(asset) {
        // Повертаємо перші 3 символи назви активу
        return asset.substring(0, 3);
    }

    translateMarketName(market) {
        const translations = {
            'forex': 'Форекс',
            'crypto': 'Криптовалюти',
            'european_stocks': 'Європейські акції',
            'us_stocks': 'Американські акції',
            'ukrainian_stocks': 'Українські акції'
        };
        return translations[market] || market;
    }

    translate(key) {
        return this.translations[this.language][key] || key;
    }

    async setupLanguage() {
        this.applyLanguage(this.language);
        
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === this.language);
        });
    }

    switchLanguage(lang) {
        this.language = lang;
        localStorage.setItem('language', lang);
        this.applyLanguage(lang);
        
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
        
        console.log("🌐 Змінено мову на:", lang);
        this.loadRecommendations();
    }

    applyLanguage(lang) {
        const translations = this.translations[lang];
        if (!translations) return;
        
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (translations[key]) {
                element.textContent = translations[key];
            }
        });
    }

    showMessage(type, text) {
        let messageContainer = document.getElementById('message-container');
        if (!messageContainer) {
            messageContainer = document.createElement('div');
            messageContainer.id = 'message-container';
            document.body.appendChild(messageContainer);
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 
                               type === 'error' ? 'exclamation-circle' : 
                               'info-circle'}"></i>
            <span>${text}</span>
        `;
        
        messageContainer.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        }, 5000);
    }
}

// Ініціалізація
let recommendationsDisplay;

document.addEventListener('DOMContentLoaded', () => {
    recommendationsDisplay = new RecommendationsDisplay();
    window.recommendationsDisplay = recommendationsDisplay;
});
