// begin template data
const linkTexts = {
    'start': 'HOME',
    'self': 'RELOAD',
    'up': 'UP',
    'next': 'NEXT',
    'prev': 'PREV'
};

const prefix = 'opds';
const genre_prfx = 'genre';
// end template data

function updateNavigationPath(path) {
    window.history.pushState(null, '', `#${path}`);
}

function fetchOPDSData(url) {
    let xmlHttp = new XMLHttpRequest();

    // Ensure URL starts with a slash
    url = url.replace(/^(\/*)/g, '');

    xmlHttp.open("GET", `/${url}`, true);

    xmlHttp.onload = function() {
        if(xmlHttp.status === 200) {
            parseAndRenderXML(xmlHttp.responseXML, url);
        } else {
            alert('Failed to fetch OPDS data');
        }
    };
    xmlHttp.send();
}

function navigateLink(link) {
    fetchOPDSData(link);  // Fetch new data and update history
    updateNavigationPath(link);
}


function renderSimpleList(xmlDoc) {
    // entry rendering (simple list)
    let contentSection = document.getElementById('content');
    contentSection.className = 'rowlist_single';
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(entry => {
        let title = entry.getElementsByTagName("title")[0].textContent;
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
        d.classList.add('col1')
        a.href = '#' + linkHref;
        a.textContent = title;
        a.onclick = function () { navigateLink(linkHref); return false; };
        d.appendChild(a);
        contentSection.appendChild(d);
    });
}

function render2elemList(xmlDoc) {
    // entry rendering (simple list)
    let contentSection = document.getElementById('content');
    contentSection.className = 'rowlist';
    contentSection.innerHTML = '';

    Array.from(xmlDoc.getElementsByTagName("entry")).forEach(entry => {
        let title = entry.getElementsByTagName("title")[0].textContent;
        let cont = entry.getElementsByTagName("content")[0].textContent;
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
        d.classList.add('col1')
        a.href = '#' + linkHref;
        a.textContent = title;
        a.onclick = function () { navigateLink(linkHref); return false; };
        d.appendChild(a);
        contentSection.appendChild(d);

        let d2 = document.createElement("div");
        d2.classList.add('col2')
        d2.textContent = cont;
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
    auths.textContent = "Авторы:";
    Array.from(entry.getElementsByTagName("author")).forEach(auth => {
        auth_name = auth.getElementsByTagName("name")[0].textContent;
        auth_uri = auth.getElementsByTagName("uri")[0].textContent;
        let a = document.createElement("a");
        a.href = '#' + auth_uri;
        a.textContent = auth_name;

        a.onclick = function () {
            navigateLink(auth_uri); return false;
        };

        if (auths.firstChild) {
            auths.appendChild(document.createTextNode(" "));
        }
        auths.appendChild(a);
    });
    d.appendChild(auths)

    let cover_uri = document.createElement("img");
    let links = document.createElement("p");
    links.textContent = "Ссылки:";
    Array.from(entry.getElementsByTagName("link")).forEach(link => {
        rel = link.getAttribute("rel");
        href = link.getAttribute("href");
        if (rel == 'related') {
            title = link.getAttribute("title");
            let a = document.createElement("a");
            a.href = '#' + href;
            a.textContent = title;
            a.onclick = function () {
                navigateLink(auth_uri); return false;
            };
            if (links.firstChild) {
                links.appendChild(document.createTextNode(" "));
            }
            links.appendChild(a)
        } else if ( rel == 'http://opds-spec.org/acquisition/open-access' || rel == 'alternate') {
            title = link.getAttribute("title");
            let a = document.createElement("a");
            a.href = href;
            a.textContent = title;
            if (links.firstChild) {
                links.appendChild(document.createTextNode(" "));
            }
            links.appendChild(a)
        } else if (rel == 'x-stanza-cover-image') {
            cover_uri.alt = 'x-stanza-cover-image';
            cover_uri.src = href
        }
    });

    let categories = document.createElement("p");
    categories.textContent = "Жанры:"
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
            a.onclick = function () { navigateLink(linkHref); return false; };
            d.appendChild(a);
            contentSection.appendChild(d);
        }
    });
}

function parseAndRenderXML(xmlDoc, path) {
    // title from opds
    let titleElement = xmlDoc.getElementsByTagName("title")[0];
    const titleText = titleElement.textContent;
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
    switch(pathElems[0]) {
        case 'author':
            if (pathLength === 4) {
                renderAuthorMain(xmlDoc);
            } else if (pathElems[4] === 'sequences') {
                render2elemList(xmlDoc);
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

function performSearch() {
    let searchTerm = document.getElementById('search-input').value;
    if (searchTerm.trim()) {
        window.location.href = '#/opds/search?searchTerm=' + encodeURIComponent(searchTerm);
    } else {
        alert("Введите поисковой запрос");
    }
}

window.onload = function() {
    // Check the hash in the URL and fetch data for it

    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        fetchOPDSData(hashPath);
        updateNavigationPath(hashPath);
    } else {
        fetchOPDSData(`/${prefix}/`);  // Default fallback if no hash is present
    }
};

window.onpopstate = function(event) {
    let hashPath = window.location.hash.substring(1);  // Remove the leading '#'
    if (hashPath) {
        fetchOPDSData(hashPath);
    } else {
        fetchOPDSData(`/${prefix}/`);  // Default fallback if no hash is present
    }
};
