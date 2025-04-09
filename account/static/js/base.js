class ThemeSwitcher {
    constructor() {
        this.toggleBtn = document.getElementById('themeToggle');
        this.html = document.documentElement;
        
        this.init();
    }
    
    init() {
        this.toggleBtn?.addEventListener('click', () => this.toggleTheme());
        
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
    
    toggleTheme() {
        const newTheme = this.html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    setTheme(theme) {
        this.html.setAttribute('data-theme', theme);
        
        localStorage.setItem('theme', theme);
        
        fetch(THEME_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ theme: theme })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error('Failed to save theme preference');
            }
        });
        
        if (this.toggleBtn) {
            this.toggleBtn.textContent = theme === 'dark' ? '🌙' : '☀️';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ThemeSwitcher();
    
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
});