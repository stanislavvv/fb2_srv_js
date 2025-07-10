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
    // Получаем заголовок
    let titleElement = xmlDoc.getElementsByTagName("title")[0];
    const titleText = titleElement.textContent;
    document.querySelectorAll("#title").forEach(elem => {
        elem.textContent = titleText;
    });

    // Строка навигации по ссылкам вне entry
    let navigationSection = document.getElementById('navigation-section');
    navigationSection.innerHTML = '';
    Array.from(xmlDoc.getElementsByTagName("link")).forEach(link => {
        if ((link.parentNode.tagName !== "entry") && 
            (link.getAttribute('rel') !== "search")) {
            let a = document.createElement("a");
            a.href = '#';
            a.textContent = link.getAttribute('rel') || link.getAttribute('href');
            a.onclick = function() { fetchOPDSData(link.getAttribute('href')); return false; };
            // Вставляем разделитель (пробел) между ссылками, если это не первая ссылка
            if (navigationSection.firstChild) {
                navigationSection.appendChild(document.createTextNode(" "));
            }
            navigationSection.appendChild(a);        }
    });

    // Поле ввода для поиска, если есть ссылка с rel="search"
    let searchLink = Array.from(xmlDoc.getElementsByTagName("link"))
                           .find(l => l.getAttribute('rel') === 'search');
    if (searchLink) {
        document.getElementById('search-section').style.display = '';
    } else {
        document.getElementById('search-section').style.display = 'none';
    }

    // Рендерим каждую запись в формате entry
    let contentSection = document.getElementById('content');
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

        let p = document.createElement("p");
        let a = document.createElement("a");
        a.href = '#';
        a.textContent = title;
        a.onclick = function () { fetchOPDSData(linkHref); return false; };
        p.appendChild(a);
        contentSection.appendChild(p);
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