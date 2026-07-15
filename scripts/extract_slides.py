#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取HTML幻灯片中的文本内容"""

from html.parser import HTMLParser
import re

class SlideExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slides = []
        self.current_slide = None
        self.in_slide = False
        self.current_text = []
        self.current_tag = None
        self.current_class = None
        self.skip_base64 = 0
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_attr = attrs_dict.get('class', '')
        
        if tag == 'section' and 'slide' in class_attr:
            self.in_slide = True
            self.current_slide = {
                'class': class_attr,
                'style': attrs_dict.get('style', ''),
                'elements': []
            }
            self.current_text = []
            return
        
        if self.in_slide:
            if tag == 'img':
                self.skip_base64 += 1
                return
            
            self.current_tag = tag
            self.current_class = class_attr
            self.current_text = []
    
    def handle_endtag(self, tag):
        if self.skip_base64 > 0 and tag == 'img':
            self.skip_base64 -= 1
            return
        
        if self.skip_base64 > 0:
            return
        
        if tag == 'section' and self.in_slide and self.current_slide:
            self.slides.append(self.current_slide)
            self.in_slide = False
            self.current_slide = None
            return
        
        if self.in_slide and self.current_slide is not None:
            text = ''.join(self.current_text).strip()
            if text:
                self.current_slide['elements'].append({
                    'tag': self.current_tag,
                    'class': self.current_class,
                    'text': text
                })
            self.current_text = []
    
    def handle_data(self, data):
        if self.skip_base64 > 0:
            return
        if self.in_slide:
            self.current_text.append(data)


def extract_slides(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = SlideExtractor()
    parser.feed(content)
    
    return parser.slides


if __name__ == '__main__':
    html_path = '/Users/dylanren/Documents/trae_projects/merge-books/.frontend-slides/unified-dev-framework-training.html'
    slides = extract_slides(html_path)
    
    print(f"共找到 {len(slides)} 张幻灯片\n")
    print("=" * 80)
    
    for i, slide in enumerate(slides, 1):
        print(f"\n【第 {i} 张幻灯片】")
        print("-" * 60)
        for elem in slide['elements']:
            cls = elem['class']
            text = elem['text']
            if cls:
                print(f"  [{cls}] {text}")
            else:
                print(f"  {text}")
        print()
