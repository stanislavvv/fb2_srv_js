// navigation links text
const linkTexts = {
    'start': 'HOME',
    'self': 'RELOAD',
    'up': 'UP',
    'next': 'NEXT',
    'prev': 'PREV'
};

function fetchOPDSData(url) {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", url, true);
    xmlHttp.onload = function() {
        if(xmlHttp.status === 200) {
            parseAndRenderXML(xmlHttp.responseXML);
        } else {
            alert('Failed to fetch OPDS data');
        }
    };
    xmlHttp.send();
}

function parseAndRenderXML(xmlDoc) {
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
            a.href = '#';
            const relValue = link.getAttribute('rel');
            a.textContent = linkTexts[relValue] || relValue || link.getAttribute('href');
            a.onclick = function() { fetchOPDSData(link.getAttribute('href')); return false; };
            // Вставляем разделитель (пробел) между ссылками, если это не первая ссылка
            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(a);        }
    });

    // search if in opds
    let searchLink = Array.from(xmlDoc.getElementsByTagName("link"))
                           .find(l => l.getAttribute('rel') === 'search');
    if (searchLink) {
        document.getElementById('search-section').style.display = '';
    } else {
        document.getElementById('search-section').style.display = 'none';
    }

    // entry rendering (simple list)
    let contentSection = document.getElementById('content');
    contentSection.classList.add('rowlist_single');
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
        a.href = '#';
        a.textContent = title;
        a.onclick = function () { fetchOPDSData(linkHref); return false; };
        d.appendChild(a);
        contentSection.appendChild(d);
    });
}

function performSearch() {
    let searchTerm = document.getElementById('search-input').value;
    if (searchTerm.trim()) {
        window.location.href = '/opds/search?searchTerm=' + encodeURIComponent(searchTerm);
    } else {
        alert("Введите поисковой запрос");
    }
}