// Package util provides XSLT transformation utilities.
package util

import (
	"bytes"
	"fmt"
	"log"
	"os"

	"github.com/wamuir/go-xslt"
)

// XSLTTransform holds a compiled XSLT stylesheet for FB2->HTML transformation.
type XSLTTransform struct {
	stylesheet *xslt.Stylesheet
}

// NewXSLTTransform compiles an XSLT file and returns a reusable transform object.
func NewXSLTTransform(xsltFile string) (*XSLTTransform, error) {
	data, err := os.ReadFile(xsltFile)
	if err != nil {
		return nil, fmt.Errorf("read xslt file %s: %w", xsltFile, err)
	}

	stylesheet, err := xslt.NewStylesheet(data)
	if err != nil {
		return nil, fmt.Errorf("compile xslt %s: %w", xsltFile, err)
	}

	log.Printf("XSLT stylesheet loaded from %s", xsltFile)
	return &XSLTTransform{stylesheet: stylesheet}, nil
}

// Close releases the XSLT stylesheet resources.
func (t *XSLTTransform) Close() {
	if t != nil && t.stylesheet != nil {
		t.stylesheet.Close()
	}
}

// Transform performs XSLT transformation on FB2 XML data, returning HTML.
func (t *XSLTTransform) Transform(fb2Data []byte) ([]byte, error) {
	if t == nil || t.stylesheet == nil {
		return nil, fmt.Errorf("XSLT transform not initialized")
	}

	result, err := t.stylesheet.Transform(fb2Data)
	if err != nil {
		return nil, fmt.Errorf("xslt transform: %w", err)
	}

	return result, nil
}

// AddXSLLine adds an <?xml-stylesheet ... ?> processing instruction after the XML declaration.
func AddXSLLine(fb2Data []byte, xslHref string) []byte {
	xslLine := fmt.Sprintf(`<?xml-stylesheet type="text/xsl" href="%s"?>`, xslHref)

	// Find XML declaration end
	xmlDeclEnd := 0
	if len(fb2Data) >= 5 && bytes.HasPrefix(fb2Data, []byte("<?xml")) {
		idx := bytes.IndexByte(fb2Data, '>')
		if idx > 0 {
			xmlDeclEnd = idx + 1
		}
	}

	if xmlDeclEnd == 0 {
		// No XML declaration found, prepend
		result := []byte(xslLine + "\n")
		result = append(result, fb2Data...)
		return result
	}

	// Insert after XML declaration
	result := make([]byte, 0, len(fb2Data)+len(xslLine)+2)
	result = append(result, fb2Data[:xmlDeclEnd]...)
	result = append(result, '\n')
	result = append(result, xslLine...)
	result = append(result, fb2Data[xmlDeclEnd:]...)
	return result
}