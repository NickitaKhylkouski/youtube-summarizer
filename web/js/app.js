class SummaryViewer {
    constructor() {
        this.summaries = [];
        this.filteredSummaries = [];
        this.currentSearch = '';
        this.currentSort = 'date-desc';
        
        this.init();
    }
    
    async init() {
        await this.loadSummaries();
        this.setupEventListeners();
        this.renderSummaries();
        this.updateResultsCount();
    }
    
    async loadSummaries() {
        try {
            const response = await fetch('data/summaries.json');
            this.summaries = await response.json();
            this.filteredSummaries = [...this.summaries];
        } catch (error) {
            console.error('Error loading summaries:', error);
            this.showError('Failed to load summaries. Please try again later.');
        }
    }
    
    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        searchInput.addEventListener('input', this.debounce(() => {
            this.handleSearch();
        }, 300));
        
        searchBtn.addEventListener('click', () => {
            this.handleSearch();
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        
        // Sort functionality
        const sortSelect = document.getElementById('sortSelect');
        sortSelect.addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.sortSummaries();
            this.renderSummaries();
        });
        
        // Clear filters
        const clearFilters = document.getElementById('clearFilters');
        clearFilters.addEventListener('click', () => {
            this.clearFilters();
        });
        
        // Modal functionality
        const modal = document.getElementById('summaryModal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.addEventListener('click', () => {
            this.closeModal();
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        this.currentSearch = searchInput.value.toLowerCase().trim();
        this.filterSummaries();
        this.renderSummaries();
        this.updateResultsCount();
    }
    
    filterSummaries() {
        if (!this.currentSearch) {
            this.filteredSummaries = [...this.summaries];
        } else {
            this.filteredSummaries = this.summaries.filter(summary => {
                return summary.title.toLowerCase().includes(this.currentSearch) ||
                       summary.overview.toLowerCase().includes(this.currentSearch) ||
                       summary.topics.toLowerCase().includes(this.currentSearch) ||
                       summary.chapters.toLowerCase().includes(this.currentSearch);
            });
        }
        this.sortSummaries();
    }
    
    sortSummaries() {
        this.filteredSummaries.sort((a, b) => {
            switch (this.currentSort) {
                case 'date-desc':
                    return b.sort_date.localeCompare(a.sort_date);
                case 'date-asc':
                    return a.sort_date.localeCompare(b.sort_date);
                case 'title-asc':
                    return a.title.localeCompare(b.title);
                case 'title-desc':
                    return b.title.localeCompare(a.title);
                default:
                    return 0;
            }
        });
    }
    
    renderSummaries() {
        const container = document.getElementById('summariesContainer');
        
        if (this.filteredSummaries.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <h3>No summaries found</h3>
                    <p>Try adjusting your search terms or clear the filters.</p>
                </div>
            `;
            return;
        }
        
        const summariesHTML = this.filteredSummaries.map(summary => {
            return this.createSummaryCard(summary);
        }).join('');
        
        container.innerHTML = summariesHTML;
        
        // Add click listeners to cards
        container.querySelectorAll('.summary-card').forEach((card, index) => {
            card.addEventListener('click', () => {
                this.openModal(this.filteredSummaries[index]);
            });
        });
    }
    
    createSummaryCard(summary) {
        const truncatedOverview = this.truncateText(summary.overview, 200);
        const tags = this.extractTags(summary.topics);
        
        return `
            <div class="summary-card" data-filename="${summary.filename}">
                <h3>${this.escapeHtml(summary.title)}</h3>
                <span class="summary-date">${this.formatDate(summary.date)}</span>
                <div class="summary-overview">
                    ${this.escapeHtml(truncatedOverview)}
                </div>
                <div class="summary-tags">
                    ${tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    extractTags(topicsText) {
        // Extract bullet points as tags
        const matches = topicsText.match(/- \*\*([^:]+):/g);
        if (matches) {
            return matches.slice(0, 3).map(match => 
                match.replace(/- \*\*/, '').replace(/:/, '').trim()
            );
        }
        return [];
    }
    
    openModal(summary) {
        const modal = document.getElementById('summaryModal');
        const modalBody = document.getElementById('modalBody');
        
        // Convert markdown-like content to HTML
        const htmlContent = this.convertToHtml(summary.content);
        modalBody.innerHTML = htmlContent;
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        const modal = document.getElementById('summaryModal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
    
    convertToHtml(content) {
        return content
            // Headers
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            // Bold text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            // Italic text
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // Bullet points
            .replace(/^- (.+)$/gm, '<li>$1</li>')
            // Wrap lists
            .replace(/(<li>.*<\/li>\s*)+/gs, '<ul>$&</ul>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            // Wrap in paragraphs
            .replace(/^(?!<[hul])/gm, '<p>')
            .replace(/$/gm, '</p>')
            // Clean up extra paragraphs
            .replace(/<p><\/p>/g, '')
            .replace(/<p>(<[hul])/g, '$1')
            .replace(/(<\/[hul]>)<\/p>/g, '$1');
    }
    
    clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('sortSelect').value = 'date-desc';
        this.currentSearch = '';
        this.currentSort = 'date-desc';
        this.filteredSummaries = [...this.summaries];
        this.sortSummaries();
        this.renderSummaries();
        this.updateResultsCount();
    }
    
    updateResultsCount() {
        const resultsCount = document.getElementById('resultsCount');
        const total = this.summaries.length;
        const filtered = this.filteredSummaries.length;
        
        if (this.currentSearch) {
            resultsCount.textContent = `Showing ${filtered} of ${total} summaries`;
        } else {
            resultsCount.textContent = `Showing all ${total} summaries`;
        }
    }
    
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            return dateString;
        }
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength).trim() + '...';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    showError(message) {
        const container = document.getElementById('summariesContainer');
        container.innerHTML = `
            <div class="no-results">
                <h3>Error</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SummaryViewer();
});