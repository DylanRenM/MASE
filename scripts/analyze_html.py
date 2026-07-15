"""
Analyze HTML structure of the first few slides to understand layout.
"""
from lxml import etree

html_path = '/Users/dylanren/Documents/trae_projects/merge-books/.frontend-slides/unified-dev-framework-training.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

parser = etree.HTMLParser()
tree = etree.fromstring(content, parser)

slides = tree.xpath('//div[@class="deck-stage"]/section')

for i, slide in enumerate(slides[:2]):
    print(f"\n{'='*80}")
    print(f"Slide {i+1}")
    print(f"{'='*80}")
    
    def print_elem(elem, depth=0):
        tag = elem.tag
        classes = elem.get('class', '')
        style = elem.get('style', '')
        text = ''.join(elem.itertext()).strip()[:80]
        indent = '  ' * depth
        
        attrs = []
        if classes:
            attrs.append(f'class="{classes}"')
        if style:
            attrs.append(f'style="{style[:60]}..."')
        
        print(f"{indent}<{tag} {' '.join(attrs)}>")
        if text:
            print(f"{indent}  TEXT: {text}")
        
        for child in elem:
            print_elem(child, depth + 1)
    
    print_elem(slide)
