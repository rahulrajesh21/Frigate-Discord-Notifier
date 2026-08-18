// Documentation Site Interactivity
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initCopyCodeButtons();
  initTableOfContents();
  initSearch();
  initMobileSidebar();
  initBreadcrumbs();
});

// Theme Management
function initTheme() {
  const themeToggle = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  
  setTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      setTheme(newTheme);
    });
  }
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  const icon = document.getElementById('theme-toggle-icon');
  if (icon) {
    if (theme === 'dark') {
      icon.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
    } else {
      icon.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    }
  }
}

// Copy Code Button Initialization
function initCopyCodeButtons() {
  const preBlocks = document.querySelectorAll('.doc-article pre');
  preBlocks.forEach((pre) => {
    // Check if code header already exists
    if (!pre.querySelector('.code-header')) {
      const codeEl = pre.querySelector('code');
      const langMatch = codeEl ? codeEl.className.match(/language-(\w+)/) : null;
      const lang = langMatch ? langMatch[1].toUpperCase() : 'CODE';

      const header = document.createElement('div');
      header.className = 'code-header';
      header.innerHTML = `
        <span>${lang}</span>
        <button class="copy-btn" aria-label="Copy Code">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          <span>Copy</span>
        </button>
      `;

      pre.insertBefore(header, pre.firstChild);

      const copyBtn = header.querySelector('.copy-btn');
      copyBtn.addEventListener('click', () => {
        const textToCopy = codeEl ? codeEl.innerText : pre.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
          copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg><span style="color:#22c55e">Copied!</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><span>Copy</span>`;
          }, 2000);
        });
      });
    }
  });
}

// Table of Contents & Scrollspy
function initTableOfContents() {
  const article = document.querySelector('.doc-article');
  const tocList = document.getElementById('toc-list');
  if (!article || !tocList) return;

  const headings = article.querySelectorAll('h2, h3');
  if (headings.length === 0) {
    document.querySelector('.toc-sidebar').style.display = 'none';
    return;
  }

  tocList.innerHTML = '';
  headings.forEach((heading, index) => {
    if (!heading.id) {
      heading.id = 'heading-' + index + '-' + heading.innerText.toLowerCase().replace(/[^a-z0-0]+/g, '-');
    }

    const li = document.createElement('li');
    li.className = 'toc-item';
    
    const a = document.createElement('a');
    a.href = '#' + heading.id;
    a.className = 'toc-link' + (heading.tagName === 'H3' ? ' indent' : '');
    a.innerText = heading.innerText;

    li.appendChild(a);
    tocList.appendChild(li);
  });

  // Scrollspy via IntersectionObserver
  const tocLinks = tocList.querySelectorAll('.toc-link');
  const observerOptions = {
    rootMargin: '-80px 0px -60% 0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        tocLinks.forEach((link) => {
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    });
  }, observerOptions);

  headings.forEach((heading) => observer.observe(heading));
}

// Search Modal & Index
function initSearch() {
  const searchModal = document.getElementById('search-modal-backdrop');
  const searchTriggers = document.querySelectorAll('.search-trigger');
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');

  if (!searchModal) return;

  // Real Documentation Index built from actual repository docs content
  const docsIndex = [
    {
      title: "Overview",
      url: "index.html",
      snippet: "Frigate Discord Video Receiver - A complete and local notification bridge that sends high-resolution recorded event video clips from Frigate NVR to Discord channels."
    },
    {
      title: "Installation & Setup - Prerequisites",
      url: "setup.html#prerequisites",
      snippet: "Python 3.10+, notify-discord CLI binaries for Linux x86_64, macOS Apple Silicon, macOS Intel, and Discord Webhook configuration."
    },
    {
      title: "Docker Compose Setup",
      url: "setup.html#docker-compose-recommended",
      snippet: "Deploying Frigate Discord Video Receiver using Docker Compose with external network frigate_default and DISCORD_WEBHOOK_URL environment variable."
    },
    {
      title: "Systemd Service Setup",
      url: "setup.html#systemd-service-linux",
      snippet: "Linux native systemd unit deployment instructions with Python virtual environment venv setup and auto-restart."
    },
    {
      title: "Configuration & Environment Variables",
      url: "configuration.html#environment-variables",
      snippet: "FRIGATE_URL, PORT, DISCORD_WEBHOOK_URL, MAX_RETRIES, RETRY_INTERVAL, MAX_FILE_SIZE_MB configuration reference."
    },
    {
      title: "Frigate-Notify Webhook Integration",
      url: "configuration.html#frigate-notify-webhook",
      snippet: "Add webhook provider under alerts in Frigate-Notify config.yml template payload."
    },
    {
      title: "Testing - Health Check",
      url: "testing.html#health-check",
      snippet: "Verify service health using curl http://localhost:5001/ returning HTTP 200 OK."
    },
    {
      title: "Testing - Dry-Run Webhook",
      url: "testing.html#dry-run-webhook-test",
      snippet: "Simulate test event trigger via POST request without downloading clips or uploading to Discord."
    },
    {
      title: "Logs & Monitoring",
      url: "testing.html#logs",
      snippet: "Docker container logs docker logs -f frigate-discord-video and systemd logs journalctl -u frigate-discord-video -f."
    }
  ];

  searchTriggers.forEach(btn => {
    btn.addEventListener('click', () => openSearch());
  });

  // Shortcut Cmd+K or Ctrl+K
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape') {
      closeSearch();
    }
  });

  searchModal.addEventListener('click', (e) => {
    if (e.target === searchModal) closeSearch();
  });

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (!query) {
        searchResults.innerHTML = '<div class="search-no-results">Type to search existing documentation...</div>';
        return;
      }

      const matches = docsIndex.filter(item => 
        item.title.toLowerCase().includes(query) || item.snippet.toLowerCase().includes(query)
      );

      if (matches.length === 0) {
        searchResults.innerHTML = `<div class="search-no-results">No results found for "${query}"</div>`;
      } else {
        searchResults.innerHTML = matches.map(item => `
          <a href="${item.url}" class="search-result-item">
            <div class="search-result-title">${item.title}</div>
            <div class="search-result-snippet">${item.snippet}</div>
          </a>
        `).join('');
      }
    });
  }

  function openSearch() {
    searchModal.classList.add('open');
    if (searchInput) {
      searchInput.value = '';
      searchInput.focus();
    }
    searchResults.innerHTML = '<div class="search-no-results">Type to search existing documentation...</div>';
  }

  function closeSearch() {
    searchModal.classList.remove('open');
  }
}

// Mobile Sidebar Drawer
function initMobileSidebar() {
  const toggleBtn = document.getElementById('mobile-toggle');
  const sidebar = document.getElementById('sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }
}

// Breadcrumb Auto Generator
function initBreadcrumbs() {
  const breadcrumbEl = document.getElementById('breadcrumbs');
  if (!breadcrumbEl) return;

  const path = window.location.pathname;
  let section = "Getting Started";
  let pageName = "Overview";

  if (path.includes('setup')) {
    section = "Getting Started";
    pageName = "Installation & Setup";
  } else if (path.includes('configuration')) {
    section = "Configuration";
    pageName = "Configuration";
  } else if (path.includes('testing')) {
    section = "Verification & Logs";
    pageName = "Testing & Monitoring";
  }

  breadcrumbEl.innerHTML = `
    <a href="index.html">Docs</a>
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
    <span>${section}</span>
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
    <span>${pageName}</span>
  `;
}

// Demo Modal Open / Close
function openDemoModal() {
  const modal = document.getElementById('demo-modal-backdrop');
  if (modal) modal.classList.add('open');
}

function closeDemoModal() {
  const modal = document.getElementById('demo-modal-backdrop');
  if (modal) modal.classList.remove('open');
}
