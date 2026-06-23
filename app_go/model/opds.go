// Package model provides OPDS XML structures.
package model

// OPDSFeed is the root XML element for an OPDS catalog.
type OPDSFeed struct {
	XMLName      string         `xml:"feed"`
	XMLNS        string         `xml:"xmlns,attr"`
	XMLNSdc      string         `xml:"xmlns:dc,attr"`
	XMLNSos      string         `xml:"xmlns:os,attr"`
	XMLNSopds    string         `xml:"xmlns:opds,attr"`
	ID           string         `xml:"id"`
	Title        string         `xml:"title"`
	Updated      string         `xml:"updated"`
	Icon         string         `xml:"icon"`
	Links        []OPDSLink     `xml:"link"`
	Entries      []OPDSEntry    `xml:"entry"`
}

// OPDSEntry is a single entry (book or navigation) in an OPDS feed.
type OPDSEntry struct {
	Updated      string           `xml:"updated"`
	ID           string           `xml:"id"`
	Title        string           `xml:"title"`
	Authors      []OPDSAuthor     `xml:"author,omitempty"`
	Links        []OPDSLink       `xml:"link"`
	Categories   []OPDSCategory   `xml:"category,omitempty"`
	DCLanguage   string           `xml:"dc:language,omitempty"`
	DCFormat     string           `xml:"dc:format,omitempty"`
	Content      *OPDSContent     `xml:"content,omitempty"`
}

// OPDSContent holds the HTML or plain-text content of an entry.
type OPDSContent struct {
	Type  string `xml:"type,attr"`
	Value string `xml:",chardata"`
}

// OPDSLink is a hyperlink inside the feed or entry.
type OPDSLink struct {
	HRef string `xml:"href,attr"`
	Rel  string `xml:"rel,attr,omitempty"`
	Type string `xml:"type,attr,omitempty"`
	Title string `xml:"title,attr,omitempty"`
}

// OPDSAuthor is the author element inside an entry.
type OPDSAuthor struct {
	URI  string `xml:"uri,attr,omitempty"`
	Name string `xml:",chardata"`
}

// OPDSCategory is a category (genre) element inside an entry.
type OPDSCategory struct {
	Term  string `xml:"term,attr"`
	Label string `xml:"label,attr"`
}