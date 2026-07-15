"""
Get accurate element positions - only top-level text elements.
"""
from playwright.sync_api import sync_playwright
import json

html_path = '/Users/dylanren/Documents/trae_projects/merge-books/.frontend-slides/unified-dev-framework-training.html'
output_json = '/Users/dylanren/Documents/trae_projects/日常办公/projects/slide_layouts.json'

def get_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        page.goto(f'file://{html_path}')
        page.wait_for_timeout(3000)
        
        slides = []
        slide_elements = page.query_selector_all('section.slide')
        
        for i, slide_el in enumerate(slide_elements):
            page.evaluate("""
                document.querySelectorAll('section.slide').forEach(el => {
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                });
            """)
            
            slide_el.evaluate('el => { el.style.visibility = "visible"; el.style.opacity = "1"; }')
            page.wait_for_timeout(500)
            
            elements = []
            
            result = slide_el.evaluate("""el => {
                const elements = [];
                const textSelectors = ['h1', 'h2', 'h3', 'h4', 'p', '.kicker', '.lead', '.body', '.caption', '.label', '.panel-title', '.panel-body', '.process-item', '.agenda-item', '.stat-value', '.stat-label', '.step-name', '.step-desc', '.ag-name', '.ag-kind', '.pin-line'];
                
                textSelectors.forEach(selector => {
                    el.querySelectorAll(selector).forEach(item => {
                        const rect = item.getBoundingClientRect();
                        if (!rect || rect.width < 10 || rect.height < 10) return;
                        
                        const text = item.textContent.trim();
                        if (!text) return;
                        
                        const style = window.getComputedStyle(item);
                        
                        elements.push({
                            tag: item.tagName.toLowerCase(),
                            classes: item.className,
                            text: text,
                            x: rect.left,
                            y: rect.top,
                            width: rect.width,
                            height: rect.height,
                            computed: {
                                fontFamily: style.fontFamily,
                                fontSize: style.fontSize,
                                fontWeight: style.fontWeight,
                                fontStyle: style.fontStyle,
                                color: style.color,
                                textAlign: style.textAlign,
                                backgroundColor: style.backgroundColor
                            }
                        });
                    });
                });
                
                el.querySelectorAll('.inverse-panel, .compare-panel, .highlight-panel, .light-panel').forEach(panel => {
                    const rect = panel.getBoundingClientRect();
                    if (!rect || rect.width < 50 || rect.height < 30) return;
                    
                    const style = window.getComputedStyle(panel);
                    elements.push({
                        tag: 'div',
                        classes: panel.className,
                        text: '',
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: rect.height,
                        computed: {
                            backgroundColor: style.backgroundColor
                        }
                    });
                });
                
                return elements;
            }""")
            
            elements = result
            slides.append(elements)
            print(f'Slide {i+1}: Found {len(elements)} elements')
        
        browser.close()
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(slides, f, ensure_ascii=False, indent=2)
        
        print(f'Saved {len(slides)} slides to {output_json}')

if __name__ == '__main__':
    get_layout()
