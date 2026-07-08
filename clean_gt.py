import os, re

static_dir = 'c:/Users/Admin/Desktop/legal/static'
div_pattern = re.compile(r'<li>\s*<div id="google_translate_element"[^>]*></div>\s*</li>', re.IGNORECASE)
div_pattern2 = re.compile(r'<div id="google_translate_element"[^>]*></div>', re.IGNORECASE)
script_pattern = re.compile(r'<!-- Google Translate Widget -->\s*<script type="text/javascript">\s*function googleTranslateElementInit\(\).*?</script>\s*<script type="text/javascript" src="//translate.google.com/translate_a/element.js\?cb=googleTranslateElementInit"></script>', re.DOTALL)
script_pattern2 = re.compile(r'<script type="text/javascript">\s*function googleTranslateElementInit\(\).*?</script>\s*<script type="text/javascript" src="//translate.google.com/translate_a/element.js\?cb=googleTranslateElementInit"></script>', re.DOTALL)

for file in os.listdir(static_dir):
    if file.endswith('.html'):
        path = os.path.join(static_dir, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = div_pattern.sub('', content)
        new_content = div_pattern2.sub('', new_content)
        new_content = script_pattern.sub('', new_content)
        new_content = script_pattern2.sub('', new_content)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Cleaned {file}')
