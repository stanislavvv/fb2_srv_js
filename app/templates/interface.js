// begin template data
const linkTexts = {
    'start': 'HOME',
    'self': 'RELOAD',
    'up': 'UP',
    'next': 'NEXT',
    'prev': 'PREV'
};

const prefix = '{{ data["opds_prefix"] }}';
const approot = '{{ data["approot"] }}';
const genre_prfx = '{{ data["genre_prefix"] }}';
const lang_authors = '{{ data["lang_authors"] }}';
const lang_links = '{{ data["lang_links"] }}';
const lang_genres = '{{ data["lang_genres"] }}';
const lang_lang = '{{ data["lang_lang"] }}';
// end template data

function updateNavigationPath(path) {
    window.history.pushState(null, '', `#${path}`);
}

let isLoading = false;

function fetchOPDSData(url) {
    // Auto-scroll to top on navigation
    window.scrollTo(0, 0);

    let xmlHttp = new XMLHttpRequest();

    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }

    // Ensure URL starts with a slash
    url = url.replace(/^(\/*)/g, '');

    xmlHttp.open("GET", `/${url}`, true);

    xmlHttp.onload = function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        if(xmlHttp.status === 200) {
            parseAndRenderXML(xmlHttp.responseXML, url);
        } else {
            showError(`Ошибка загрузки: HTTP ${xmlHttp.status} - ${xmlHttp.statusText}`);
        }
    };

    xmlHttp.onerror = function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        showError('Ошибка сети. Проверьте подключение.');
    };

    xmlHttp.send();
}

function showError(message) {
    const contentSection = document.getElementById('content');
    if (contentSection) {
        contentSection.className = '';
        contentSection.innerHTML = `<div class="error-message">${message}</div>`;
    }
}

function navigateLink(link) {
    fetchOPDSData(link);  // Fetch new data and update history
    updateNavigationPath(link);
}


function renderSimpleList(xmlDoc) {
    // entry rendering (simple list)
    let contentSection = document.getElementById('content');
    contentSection.className = 'rowlist';
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(entry => {
        let title = entry.getElementsByTagName("title")[0].textContent;
        let linkHref = '';
        let cont = entry.getElementsByTagName("content")[0].textContent;
        Array.from(entry.getElementsByTagName("link")).forEach(link => {
            if ((link.getAttribute('type') === 'application/atom+xml;profile=opds-catalog' ||
                link.getAttribute('type').startsWith('application/atom')) &&
                link.getAttribute('rel') != 'search'
            ) {
                linkHref = link.getAttribute('href');
            }
        });
        let d = document.createElement("div");
        let a = document.createElement("a");
        d.classList.add('col1')
        a.href = '#' + linkHref;
        a.textContent = title;
        // a.onclick = function () { navigateLink(linkHref); return false; };
        a.onclick = function() { window.open('#' + linkHref, '_blank'); return false; };
        d.appendChild(a);
        contentSection.appendChild(d);
        let d2 = document.createElement("div");
        d2.classList.add('col2')
        if (title != cont) {
            d2.textContent = cont;
        }
        contentSection.appendChild(d2);
    });
}

function decodeHtml(html) {
    let txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
}

function renderBook(entry) {
    let contentSection = document.getElementById('content');

    let title = entry.getElementsByTagName("title")[0].textContent;
    let cont = entry.getElementsByTagName("content")[0].innerHTML;
    let updated = entry.getElementsByTagName("updated")[0].textContent;

    let d = document.createElement("div")
    d.classList.add("book_info")
    let h2 = document.createElement("h2");
    h2.textContent = title;
    d.appendChild(h2)

    let auths = document.createElement("p");
    auths.textContent = lang_authors;
    Array.from(entry.getElementsByTagName("author")).forEach(auth => {
        auth_name = auth.getElementsByTagName("name")[0].textContent;
        auth_uri = auth.getElementsByTagName("uri")[0].textContent;
        let a = document.createElement("a");
        a.href = '#' + auth_uri;
        a.textContent = auth_name;

        a.onclick = function () {
            // navigateLink(auth_uri); return false;
            window.open('#' + auth_uri, '_blank'); return false;
        };

        if (auths.firstChild) {
            auths.appendChild(document.createTextNode(" "));
        }
        auths.appendChild(a);
    });
    d.appendChild(auths)

    let cover_uri = document.createElement("img");
    let links = document.createElement("p");
    links.textContent = lang_links;
    Array.from(entry.getElementsByTagName("link")).forEach(link => {
        rel = link.getAttribute("rel");
        if (rel == 'related') {
            let href = link.getAttribute("href");
            let title = link.getAttribute("title");
            let a = document.createElement("a");
            a.href = '#' + href;
            a.textContent = title;
            a.onclick = function () {
                // navigateLink(href); return false;
                window.open('#' + href, '_blank'); return false;
            };
            if (links.firstChild) {
                links.appendChild(document.createTextNode(" "));
            }
            links.appendChild(a)
        } else if ( rel == 'http://opds-spec.org/acquisition/open-access' || rel == 'alternate') {
            let href = link.getAttribute("href");
            let title = link.getAttribute("title");
            let type = link.getAttribute("type");
            let a = document.createElement("a");
            a.textContent = title;
            if (type == 'application/x-fb2+xml' || type == 'text/html') {
                a.href = '#' + href;
                a.onclick = function () {
                    window.open('#' + href, '_blank'); return false;
                };
            } else {
                a.href = href;
                a.onclick = function () {
                    window.open(href, '_blank'); return false;
                };
            }
            if (links.firstChild) {
                links.appendChild(document.createTextNode(" "));
            }
            links.appendChild(a)
        } else if (rel == 'x-stanza-cover-image') {
            let href = link.getAttribute("href");
            cover_uri.alt = 'x-stanza-cover-image';
            cover_uri.src = href
        }
    });

    let categories = document.createElement("p");
    categories.textContent = lang_genres;
    Array.from(entry.getElementsByTagName("category")).forEach(categ => {
        let label = categ.getAttribute("label");
        let genreid = categ.getAttribute("term")
        let a = document.createElement("a");
        let href = `/${prefix}/${genre_prfx}/${genreid}`;
        a.href = '#' + href;
        a.textContent = label;
        a.onclick = function () {
            navigateLink(href); return false;
        };
        if (categories.firstChild) {
            categories.appendChild(document.createTextNode(" "));
        }
        categories.appendChild(a)
    });

    let descr = document.createElement("div");
    let dcont = entry.getElementsByTagName("content")[0].innerHTML;
    descr.innerHTML = decodeHtml(dcont);

    let languageElement = entry.getElementsByTagName("dc:language")[0];
    if (languageElement) {
        let lang = document.createElement("p");
        lang.textContent = `${lang_lang}: ${languageElement.textContent}`;
        descr.appendChild(lang);
    }

    let upd = document.createElement("p");
    upd.textContent = `Добавлено: ${updated}`;

    contentSection.appendChild(d);
    contentSection.appendChild(cover_uri);
    contentSection.appendChild(links);
    contentSection.appendChild(categories);
    contentSection.appendChild(descr);
    contentSection.appendChild(upd);

    hr = document.createElement("hr");
    contentSection.appendChild(hr)
}

// HTML rendering function for FB2 books (pre-rendered HTML from server)
function renderHTMLBook(htmlUrl, bookTitle) {
    let contentSection = document.getElementById('content');

    // Add book-content class for width limiting
    contentSection.classList.add('book-content');

    // Show loading
    contentSection.innerHTML = '<div class="loading-spinner" style="display: block; margin: 2em auto;"></div>';

    // Load pre-rendered HTML
    const xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", htmlUrl, true);

    xmlHttp.onload = function() {
        if (xmlHttp.status === 200) {
            // Parse HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(xmlHttp.responseText, 'text/html');

            // Extract content from the book-content div (if exists) or use full body
            let contentToInsert;
            const bookContent = doc.getElementById('book-content');
            if (bookContent) {
                contentToInsert = bookContent.innerHTML;
            } else {
                // If no specific container, clone the body content
                contentToInsert = doc.body ? doc.body.innerHTML : doc.documentElement.innerHTML;
            }

            // Clear content and append result
            contentSection.innerHTML = contentToInsert;

            // Add 'paragraph' class to all <p> elements for scroll position tracking
            const paragraphs = contentSection.querySelectorAll('p');
            paragraphs.forEach((p, index) => {
                if (!p.classList.contains('paragraph')) {
                    p.classList.add('paragraph');
                    p.dataset.paragraphIndex = index;
                }
            });

            // Set title from book
            const newTitle = doc.querySelector('title')?.textContent || bookTitle;
            document.querySelectorAll("#title").forEach(elem => {
                elem.textContent = newTitle;
            });

            // Show only HOME and RELOAD in navigation
            let navigationSection = document.getElementById('navigation-section');
            navigationSection.innerHTML = '';

            // HOME link - redirect to approot
            let homeLink = document.createElement("a");
            homeLink.href = `${approot}/`;
            homeLink.textContent = linkTexts['start'];
            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(homeLink);

            // RELOAD link
            let reloadLink = document.createElement("a");
            reloadLink.href = '#';
            reloadLink.textContent = linkTexts['self'];
            reloadLink.onclick = function() {
                renderHTMLBook(htmlUrl, bookTitle); return false;
            };
            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(reloadLink);

            // Hide search section
            document.getElementById('search-section').style.display = 'none';

            // Restore scroll position
            restoreScrollPosition(htmlUrl);

        } else {
            showError(`Ошибка загрузки HTML: HTTP ${xmlHttp.status}`);
        }
    };

    xmlHttp.onerror = function() {
        showError('Ошибка сети при загрузке HTML-файла.');
    };

    xmlHttp.send();
}

function fetchFB2Content(href, bookTitle) {
    // Convert .fb2 URL to .html URL by replacing extension
    const htmlUrl = href.replace(/\.fb2(\.zip)?$/, '.html');
    renderHTMLBook(htmlUrl, bookTitle);
}

function renderBookList(xmlDoc) {  // placeholder
    // entry rendering (books list)
    let contentSection = document.getElementById('content');
    contentSection.className = 'book';
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(renderBook);
}

function renderAuthorMain(xmlDoc, url) {
    let contentSection = document.getElementById('content');
    contentSection.className = 'author_info';
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(entry => {
        let title = entry.getElementsByTagName("title")[0].textContent;
        let tag = entry.getElementsByTagName("id")[0].textContent;
        if (tag.startsWith('tag:author:bio')) {
            let cont = entry.getElementsByTagName("content")[0].innerHTML;
            let d = document.createElement("div");
            let h2 = document.createElement("h2");
            h2.textContent = title;
            d.appendChild(h2);
            let p = document.createElement("p");
            // p.textContent = cont;
            p.innerHTML = decodeHtml(cont);
            d.appendChild(p);
            contentSection.appendChild(d);
        } else {
            let linkHref = '';
            Array.from(entry.getElementsByTagName("link")).forEach(link => {
                if ((link.getAttribute('type') === 'application/atom+xml;profile=opds-catalog' ||
                    link.getAttribute('type').startsWith('application/atom')) &&
                    link.getAttribute('rel') != 'search'
                ) {
                    linkHref = link.getAttribute('href');
                }
            });

            let d = document.createElement("div");
            let a = document.createElement("a");
            a.href = '#' + linkHref;
            a.textContent = title;
            // a.onclick = function () { navigateLink(linkHref); return false; };
            a.onclick = function() { window.open('#' + linkHref, '_blank'); return false; };
            d.appendChild(a);
            contentSection.appendChild(d);
        }
    });
}

function parseAndRenderXML(xmlDoc, path) {
    // Remove book-content class if present (for books width limit)
    const contentSection = document.getElementById('content');
    if (contentSection) {
        contentSection.classList.remove('book-content');
    }

    // title from opds
    let titleElement = xmlDoc.getElementsByTagName("title")[0];
    let titleText = titleElement.textContent;
    document.querySelectorAll("#title").forEach(elem => {
        elem.textContent = titleText;
    });

    // navigation from opds
    let navigationSection = document.getElementById('navigation-section');
    navigationSection.innerHTML = '';
    Array.from(xmlDoc.getElementsByTagName("link")).forEach(link => {
        if ((link.parentNode.tagName !== "entry") &&
            (link.getAttribute('rel') !== "search")) {
            let a = document.createElement("a");
            a.href = '#' + link.getAttribute('href');
            const relValue = link.getAttribute('rel');
            a.textContent = linkTexts[relValue] || relValue || link.getAttribute('href');

            // Navigate using the new fetchOPDSData function with the hash path
            a.onclick = function () {
                navigateLink(link.getAttribute('href')); return false;
            };

            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(a);
        }
    });

    // search if in opds
    let searchLink = Array.from(xmlDoc.getElementsByTagName("link"))
                           .find(l => l.getAttribute('rel') === 'search');
    if (searchLink) {
        document.getElementById('search-section').style.display = '';
    } else {
        document.getElementById('search-section').style.display = 'none';
    }

    subpath = path.replace(prefix, '').replace(/^(\/*)/g, '');
    pathElems = subpath.split('/')
    pathLength = pathElems.length;

    // Check if this is an HTML book file (url ends with .html)
    if (subpath.endsWith('.html')) {
        // Extract book title from OPDS entry
        let bookTitle = xmlDoc.getElementsByTagName("title")[0]?.textContent || 'Book';
        fetchFB2Content(subpath, bookTitle);
        return;
    }

    switch(pathElems[0]) {
        case 'author':
            if (pathLength === 4) {
                renderAuthorMain(xmlDoc);
            } else if (pathElems[4] === 'sequences') {
                renderSimpleList(xmlDoc);
            } else {
                renderBookList(xmlDoc);
            }
            break;
        case 'sequence':
            renderBookList(xmlDoc);
            break;
        case 'time':
            renderBookList(xmlDoc);
            break;
        case 'genre':
            renderBookList(xmlDoc);
            break;
        case 'random-books':
            renderBookList(xmlDoc);
            break;
        case 'rnd':
            switch(pathElems[1]) {
                case 'genre':
                    renderBookList(xmlDoc);
                    break;
                default:
                    renderSimpleList(xmlDoc);
                    break;
            };
            break;
        case 'search':
            if (pathElems[1].startsWith('books')) { // books or booksanno
                renderBookList(xmlDoc);
            } else {
                renderSimpleList(xmlDoc);
            };
            break;
        default:
            renderSimpleList(xmlDoc);
            break;
    }
}

// Position tracking functions for book content
function getScrollPosition() {
    return window.pageYOffset || document.documentElement.scrollTop;
}

function saveScrollPosition(htmlUrl) {
    const position = getScrollPosition();
    sessionStorage.setItem(`scrollPosition_${encodeURIComponent(htmlUrl)}`, position.toString());
}

// Scroll handler with debounce (1 second for testing)
let scrollTimeout = null;
window.addEventListener('scroll', function() {
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(function() {
        const hashPath = window.location.hash.substring(1);
        if (hashPath.endsWith('.html')) {
            const htmlUrl = hashPath.startsWith('/') ? hashPath : '/' + hashPath;
            saveScrollPosition(htmlUrl);
        }
    }, 1000);
});

function restoreScrollPosition(htmlUrl) {
    const storedPosition = sessionStorage.getItem(`scrollPosition_${encodeURIComponent(htmlUrl)}`);
    if (storedPosition !== null) {
        const position = parseInt(storedPosition, 10);
        if (!isNaN(position)) {
            window.scrollTo({ top: position, left: 0, behavior: 'auto' });
        }
    }
}

function performSearch() {
    let searchTerm = document.getElementById('search-input').value;
    if (searchTerm.trim()) {
        window.location.href = '#/' + prefix + '/search?searchTerm=' + encodeURIComponent(searchTerm);
    } else {
        showError('Введите поисковой запрос');
    }
}

window.onload = function() {
    // Check the hash in the URL and fetch data for it

    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        updateNavigationPath(hashPath);
        // If it's an HTML book file, render it directly
        if (hashPath.endsWith('.html')) {
            let htmlUrl = hashPath.startsWith('/') ? hashPath : '/' + hashPath;
            // Get title from current page or default
            let bookTitle = document.querySelector('#title')?.textContent || 'Book';
            renderHTMLBook(htmlUrl, bookTitle);
            // Restore scroll position after render (with delay for content to load)
            setTimeout(() => restoreScrollPosition(htmlUrl), 500);
        } else {
            fetchOPDSData(hashPath);
        }
    } else {
        fetchOPDSData(`/${prefix}/`);  // Default fallback if no hash is present
    }
};

window.onpopstate = function(event) {
    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        updateNavigationPath(hashPath);
        // If it's an HTML book file, render it directly
        if (hashPath.endsWith('.html')) {
            let htmlUrl = hashPath.startsWith('/') ? hashPath : '/' + hashPath;
            // Get title from current page or default
            let bookTitle = document.querySelector('#title')?.textContent || 'Book';
            renderHTMLBook(htmlUrl, bookTitle);
            // Restore scroll position after render (with delay for content to load)
            setTimeout(() => restoreScrollPosition(htmlUrl), 500);
        } else {
            fetchOPDSData(hashPath);
        }
    } else {
        fetchOPDSData(`/${prefix}/`);  // Default fallback if no hash is present
    }
};

// Save scroll position before page unload
window.addEventListener('beforeunload', function() {
    const hashPath = window.location.hash.substring(1);
    if (hashPath.endsWith('.html')) {
        const htmlUrl = hashPath.startsWith('/') ? hashPath : '/' + hashPath;
        saveScrollPosition(htmlUrl);
    }
});

// Dark mode initialization (default: light)
function initDarkMode() {
    const savedTheme = localStorage.getItem('darkMode');
    const body = document.body;
    const themeBtn = document.getElementById('theme-btn');

    // Default to light theme if no saved preference
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        if (themeBtn) themeBtn.textContent = '☀️';
    } else {
        body.classList.remove('dark-mode');
        if (themeBtn) themeBtn.textContent = '🌙';
    }
}

// Theme toggle
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.getElementById('theme-btn');

    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'light');
        if (themeBtn) themeBtn.textContent = '🌙';
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'dark');
        if (themeBtn) themeBtn.textContent = '☀️';
    }
}

// Initialize dark mode on load
initDarkMode();

// Theme button handler
const themeBtn = document.getElementById('theme-btn');
if (themeBtn) {
    themeBtn.addEventListener('click', toggleTheme);
}

// Ctrl+S to focus search input
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.focus();
    }
});

// Enter key in search input
const searchInput = document.getElementById('search-input');
if (searchInput) {
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}
