// Netflix-Style AI News Aggregator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive features
    initNavbar();
    initNavMenu();
    initHorizontalScrolling();
    initCardInteractions();
    initModal();
    initAudioPlayer();
    initStatsButton();
});

// Navbar scroll effect
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

// Horizontal scrolling functionality
function initHorizontalScrolling() {
    const contentRows = document.querySelectorAll('.content-row');
    
    contentRows.forEach(row => {
        const container = row.querySelector('.cards-container');
        const leftBtn = row.querySelector('.scroll-left');
        const rightBtn = row.querySelector('.scroll-right');
        
        if (!container || !leftBtn || !rightBtn) return;
        
        const cardWidth = 300 + 16; // card width + gap
        const scrollAmount = cardWidth * 3; // scroll 3 cards at a time
        
        // Update button states
        function updateScrollButtons() {
            const isAtStart = container.scrollLeft <= 0;
            const isAtEnd = container.scrollLeft >= container.scrollWidth - container.clientWidth - 1;
            
            leftBtn.style.opacity = isAtStart ? '0.5' : '0.7';
            rightBtn.style.opacity = isAtEnd ? '0.5' : '0.7';
            leftBtn.style.pointerEvents = isAtStart ? 'none' : 'all';
            rightBtn.style.pointerEvents = isAtEnd ? 'none' : 'all';
        }
        
        // Scroll left
        leftBtn.addEventListener('click', function() {
            container.scrollBy({
                left: -scrollAmount,
                behavior: 'smooth'
            });
        });
        
        // Scroll right
        rightBtn.addEventListener('click', function() {
            container.scrollBy({
                left: scrollAmount,
                behavior: 'smooth'
            });
        });
        
        // Update buttons on scroll
        container.addEventListener('scroll', updateScrollButtons);
        
        // Initial button state
        updateScrollButtons();
        
        // Touch/mouse drag scrolling
        let isDown = false;
        let startX;
        let scrollLeft;
        
        container.addEventListener('mousedown', function(e) {
            isDown = true;
            container.style.cursor = 'grabbing';
            startX = e.pageX - container.offsetLeft;
            scrollLeft = container.scrollLeft;
        });
        
        container.addEventListener('mouseleave', function() {
            isDown = false;
            container.style.cursor = 'grab';
        });
        
        container.addEventListener('mouseup', function() {
            isDown = false;
            container.style.cursor = 'grab';
        });
        
        container.addEventListener('mousemove', function(e) {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const walk = (x - startX) * 2;
            container.scrollLeft = scrollLeft - walk;
        });
    });
}

// Card interaction effects
function initCardInteractions() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        // Get the preview button if it exists
        const previewBtn = card.querySelector('.preview-btn');
        const hoverPreview = card.querySelector('.card-hover-preview');
        
        // Handle preview button click
        if (previewBtn) {
            previewBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                
                const title = card.querySelector('h3').textContent;
                const fullSummary = hoverPreview.querySelector('.preview-text').textContent;
                const categories = Array.from(card.querySelectorAll('.category-tag')).map(tag => tag.textContent);
                const keyPoints = Array.from(card.querySelectorAll('.key-point')).map(point => point.textContent);
                const meta = card.querySelector('.card-meta').textContent;
                
                // Determine source from meta
                let source = 'Unknown';
                let sourceUrl = '#';
                if (meta.includes('ArXiv')) {
                    source = 'ArXiv';
                    sourceUrl = 'https://arxiv.org/abs/2401.00000'; // Mock URL
                } else if (meta.includes('Hacker News')) {
                    source = 'Hacker News';
                    sourceUrl = 'https://news.ycombinator.com/item?id=12345'; // Mock URL
                } else if (meta.includes('RSS')) {
                    source = 'RSS Feed';
                    sourceUrl = 'https://example.com/article'; // Mock URL
                }
                
                openModal(title, fullSummary, categories, keyPoints, source, sourceUrl);
            });
        }
        
        // Prevent card content from triggering on hover preview click
        card.addEventListener('click', function(e) {
            if (e.target.closest('.card-hover-preview')) {
                e.stopPropagation();
                return;
            }
        });
    });
    
    // Handle digest cards
    const digestCards = document.querySelectorAll('.digest-card');
    digestCards.forEach(card => {
        card.addEventListener('click', function() {
            const title = card.querySelector('h3').textContent;
            const date = card.querySelector('.digest-date').textContent;
            const summary = card.querySelector('.digest-summary').textContent;
            const themes = Array.from(card.querySelectorAll('.theme-tag')).map(tag => tag.textContent);
            
            openDigestModal(title, date, summary, themes);
        });
        
        // Handle play button
        const playBtn = card.querySelector('.play-btn-mini');
        if (playBtn) {
            playBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                handleDigestAudioPlay(card);
            });
        }
    });
}

// Modal functionality
function initModal() {
    const modal = document.getElementById('articleModal');
    const closeBtn = modal.querySelector('.modal-close');
    
    // Close modal when clicking close button
    closeBtn.addEventListener('click', closeModal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });
}

function openModal(title, content, categories = [], keyPoints = [], source = '', sourceUrl = '#') {
    const modal = document.getElementById('articleModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const viewSourceBtn = document.getElementById('viewSourceBtn');
    
    modalTitle.textContent = title;
    
    // Build modal content with categories and key points
    let contentHTML = `<div class="modal-article-content">`;
    
    // Add source info
    if (source) {
        contentHTML += `<div class="modal-source">Source: ${source}</div>`;
    }
    
    if (categories.length > 0) {
        contentHTML += `<div class="modal-categories">`;
        categories.forEach(cat => {
            contentHTML += `<span class="category-tag">${cat}</span>`;
        });
        contentHTML += `</div>`;
    }
    
    contentHTML += `<h4>AI-Generated Summary</h4>`;
    contentHTML += `<p class="modal-summary">${content}</p>`;
    
    if (keyPoints.length > 0) {
        contentHTML += `<div class="modal-key-points"><h4>Key Technical Points:</h4>`;
        keyPoints.forEach(point => {
            contentHTML += `<p class="key-point">${point}</p>`;
        });
        contentHTML += `</div>`;
    }
    
    contentHTML += `<div class="modal-ai-analysis">`;
    contentHTML += `<h4>AI Analysis Details</h4>`;
    contentHTML += `<p>This article has been analyzed by our AI system and assigned a relevance score based on its content's relationship to AI/ML topics. The summary and key points above were automatically extracted to highlight the most important technical insights.</p>`;
    contentHTML += `</div>`;
    
    modalContent.innerHTML = contentHTML;
    
    // Set up source button
    viewSourceBtn.onclick = function() {
        window.open(sourceUrl, '_blank');
        showNotification(`Opening ${source}...`);
    };
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
    
    // Add animation
    const modalContent_div = modal.querySelector('.modal-content');
    modalContent_div.style.transform = 'scale(0.7)';
    modalContent_div.style.opacity = '0';
    
    setTimeout(() => {
        modalContent_div.style.transform = 'scale(1)';
        modalContent_div.style.opacity = '1';
        modalContent_div.style.transition = 'all 0.3s ease';
    }, 10);
}

function closeModal() {
    const modal = document.getElementById('articleModal');
    const modalContent_div = modal.querySelector('.modal-content');
    const viewSourceBtn = document.getElementById('viewSourceBtn');
    
    modalContent_div.style.transform = 'scale(0.7)';
    modalContent_div.style.opacity = '0';
    
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
        viewSourceBtn.style.display = 'inline-block'; // Show source button again
    }, 300);
}

// Audio player functionality
function initAudioPlayer() {
    const playBtn = document.querySelector('.play-btn');
    const progressFill = document.querySelector('.progress-fill');
    const timeDisplay = document.querySelector('.time');
    
    let isPlaying = false;
    let currentTime = 4.5 * 60; // 4:32 in seconds
    const totalTime = 15 * 60; // 15:00 in seconds
    let playInterval;
    
    playBtn.addEventListener('click', function() {
        if (isPlaying) {
            pauseAudio();
        } else {
            playAudio();
        }
    });
    
    function playAudio() {
        isPlaying = true;
        playBtn.textContent = '⏸️';
        
        playInterval = setInterval(() => {
            currentTime += 1;
            if (currentTime >= totalTime) {
                currentTime = totalTime;
                pauseAudio();
            }
            updateProgress();
        }, 1000);
    }
    
    function pauseAudio() {
        isPlaying = false;
        playBtn.textContent = '▶️';
        clearInterval(playInterval);
    }
    
    function updateProgress() {
        const progress = (currentTime / totalTime) * 100;
        progressFill.style.width = progress + '%';
        
        const currentMinutes = Math.floor(currentTime / 60);
        const currentSeconds = Math.floor(currentTime % 60);
        const totalMinutes = Math.floor(totalTime / 60);
        const totalSeconds = Math.floor(totalTime % 60);
        
        timeDisplay.textContent = `${currentMinutes}:${currentSeconds.toString().padStart(2, '0')} / ${totalMinutes}:${totalSeconds.toString().padStart(2, '0')}`;
    }
    
    // Make progress bar clickable
    const progressBar = document.querySelector('.progress-bar');
    progressBar.addEventListener('click', function(e) {
        const rect = progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        currentTime = percentage * totalTime;
        updateProgress();
    });
    
    // Initialize display
    updateProgress();
}

// Stats button functionality
function initStatsButton() {
    const statsBtn = document.querySelector('.stats-btn');
    
    statsBtn.addEventListener('click', function() {
        // Show stats modal
        showStatsModal();
    });
}

function showStatsModal() {
    const modal = document.getElementById('articleModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    
    modalTitle.textContent = 'AI News Aggregator Statistics';
    
    // Mock stats data
    const statsHTML = `
        <div class="stats-container">
            <h3>System Overview</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value">34</span>
                    <span class="stat-label">Total Articles</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">34</span>
                    <span class="stat-label">ArXiv Papers</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">0</span>
                    <span class="stat-label">HackerNews</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">0</span>
                    <span class="stat-label">RSS Articles</span>
                </div>
            </div>
            
            <h3>Analysis Metrics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value">87.9%</span>
                    <span class="stat-label">Avg Relevance Score</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">0</span>
                    <span class="stat-label">Duplicates Detected</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">12 min</span>
                    <span class="stat-label">Avg Fetch Time</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">24/7</span>
                    <span class="stat-label">Uptime</span>
                </div>
            </div>
            
            <h3>Top Categories</h3>
            <div class="category-stats">
                <div class="category-bar">
                    <span class="category-name">Research</span>
                    <div class="category-progress">
                        <div class="category-fill" style="width: 94%"></div>
                    </div>
                    <span class="category-count">32</span>
                </div>
                <div class="category-bar">
                    <span class="category-name">Technical Tutorial</span>
                    <div class="category-progress">
                        <div class="category-fill" style="width: 65%"></div>
                    </div>
                    <span class="category-count">22</span>
                </div>
                <div class="category-bar">
                    <span class="category-name">Industry Analysis</span>
                    <div class="category-progress">
                        <div class="category-fill" style="width: 15%"></div>
                    </div>
                    <span class="category-count">5</span>
                </div>
                <div class="category-bar">
                    <span class="category-name">Open Source</span>
                    <div class="category-progress">
                        <div class="category-fill" style="width: 15%"></div>
                    </div>
                    <span class="category-count">5</span>
                </div>
            </div>
        </div>
    `;
    
    modalContent.innerHTML = statsHTML;
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Add animation
    const modalContent_div = modal.querySelector('.modal-content');
    modalContent_div.style.transform = 'scale(0.7)';
    modalContent_div.style.opacity = '0';
    
    setTimeout(() => {
        modalContent_div.style.transform = 'scale(1)';
        modalContent_div.style.opacity = '1';
        modalContent_div.style.transition = 'all 0.3s ease';
    }, 10);
}

function filterCards(query) {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const summary = card.querySelector('.card-summary').textContent.toLowerCase();
        
        if (title.includes(query) || summary.includes(query)) {
            card.style.display = 'block';
            card.style.opacity = '1';
        } else {
            card.style.display = 'none';
            card.style.opacity = '0.3';
        }
    });
}

function showAllCards() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.display = 'block';
        card.style.opacity = '1';
    });
}

function performSearch(query) {
    console.log('Performing search for:', query);
    // In a real application, this would make an API call to search articles
    showNotification(`Searching for "${query}"...`);
}

// Handle navigation menu clicks
function initNavMenu() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
            
            const linkText = this.textContent;
            if (linkText === 'ArXiv' || linkText === 'Hacker News' || linkText === 'RSS Feeds') {
                filterBySource(linkText);
            } else {
                showAllCards();
            }
        });
    });
}

function filterBySource(source) {
    showNotification(`Filtering by ${source}...`);
    // In real app, would fetch articles from specific source
}

// Notification system
function showNotification(message) {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 2rem;
        background: var(--white);
        color: var(--primary-black);
        padding: 1rem 1.5rem;
        border-radius: 6px;
        z-index: 1001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Animate out and remove
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    // Navigate cards with arrow keys
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        const focusedCard = document.activeElement;
        if (focusedCard.classList.contains('card')) {
            e.preventDefault();
            const cards = Array.from(document.querySelectorAll('.card'));
            const currentIndex = cards.indexOf(focusedCard);
            
            let nextIndex;
            if (e.key === 'ArrowRight') {
                nextIndex = (currentIndex + 1) % cards.length;
            } else {
                nextIndex = currentIndex === 0 ? cards.length - 1 : currentIndex - 1;
            }
            
            cards[nextIndex].focus();
        }
    }
    
    // Open modal with Enter
    if (e.key === 'Enter') {
        const focusedCard = document.activeElement;
        if (focusedCard.classList.contains('card')) {
            e.preventDefault();
            focusedCard.click();
        }
    }
});

// Make cards focusable for keyboard navigation
document.querySelectorAll('.card').forEach(card => {
    card.setAttribute('tabindex', '0');
});

// Lazy loading simulation
function initLazyLoading() {
    const cards = document.querySelectorAll('.card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
}

// Initialize lazy loading
initLazyLoading();

// Performance optimization: Throttle scroll events
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

// Apply throttling to scroll events
window.addEventListener('scroll', throttle(function() {
    // Any scroll-based functionality can be added here
}, 100));

// Digest modal function
function openDigestModal(title, date, summary, themes) {
    const modal = document.getElementById('articleModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const viewSourceBtn = document.getElementById('viewSourceBtn');
    
    modalTitle.textContent = `Daily Digest: ${date}`;
    
    let contentHTML = `<div class="modal-digest-content">`;
    contentHTML += `<h3>${title}</h3>`;
    
    contentHTML += `<div class="modal-themes">`;
    themes.forEach(theme => {
        contentHTML += `<span class="theme-tag">${theme}</span>`;
    });
    contentHTML += `</div>`;
    
    contentHTML += `<div class="digest-full-summary">`;
    contentHTML += `<p>${summary}</p>`;
    contentHTML += `<p>This digest was automatically generated from the top AI/ML articles of the day, synthesizing key developments and trends across multiple sources.</p>`;
    contentHTML += `</div>`;
    
    contentHTML += `<div class="digest-articles-list">`;
    contentHTML += `<h4>Articles included in this digest:</h4>`;
    contentHTML += `<ul>`;
    contentHTML += `<li>• Attention Mechanisms in Vision Transformers (ArXiv - 95% relevance)</li>`;
    contentHTML += `<li>• Open-source LLM fine-tuning framework (HackerNews - 92% relevance)</li>`;
    contentHTML += `<li>• Google Gemini 2.0 announcement (TechCrunch - 91% relevance)</li>`;
    contentHTML += `<li>• Federated Learning privacy advances (ArXiv - 90% relevance)</li>`;
    contentHTML += `</ul>`;
    contentHTML += `</div>`;
    
    contentHTML += `</div>`;
    
    modalContent.innerHTML = contentHTML;
    
    // Hide source button for digest
    viewSourceBtn.style.display = 'none';
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Animation
    const modalContent_div = modal.querySelector('.modal-content');
    modalContent_div.style.transform = 'scale(0.7)';
    modalContent_div.style.opacity = '0';
    
    setTimeout(() => {
        modalContent_div.style.transform = 'scale(1)';
        modalContent_div.style.opacity = '1';
        modalContent_div.style.transition = 'all 0.3s ease';
    }, 10);
}

// Handle digest audio playback
function handleDigestAudioPlay(digestCard) {
    const playBtn = digestCard.querySelector('.play-btn-mini');
    const progressBar = digestCard.querySelector('.progress-bar-mini .progress-fill');
    
    if (playBtn.textContent.includes('Play')) {
        // Stop all other audio
        document.querySelectorAll('.play-btn-mini').forEach(btn => {
            btn.textContent = '▶️ Play';
        });
        
        playBtn.textContent = '⏸️ Pause';
        showNotification('Playing audio digest...');
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 2;
            if (progress >= 100) {
                clearInterval(interval);
                playBtn.textContent = '▶️ Play';
                progress = 0;
            }
            progressBar.style.width = progress + '%';
        }, 200);
        
        // Store interval for pause functionality
        digestCard.audioInterval = interval;
    } else {
        playBtn.textContent = '▶️ Play';
        if (digestCard.audioInterval) {
            clearInterval(digestCard.audioInterval);
        }
    }
}