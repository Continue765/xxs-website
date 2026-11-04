from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

PUBLIC_FILES = {'index.html', 'manual.html', 'results.html', '.nojekyll', 'CNAME',
                'build-meta.json', 'public-manifest.json', 'assets/site.css', 'assets/site.js',
                'assets/registration.png'}
PUBLIC_FILES |= {f'assets/{kind}{ext}' for kind in ('logo', 'poster') for ext in ('.png', '.jpg', '.jpeg', '.webp')}
PRIVATE_MARKERS = ('account_password', 'account_username', 'student_id', 'XXS_SMTP_PASSWORD',
                   '联系方式:邮箱', '联系方式:电话号码', 'BEGIN PRIVATE KEY')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.images = [], set(), []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        for attr in ('href', 'src'):
            if values.get(attr):
                self.refs.append(values[attr])
        if tag == 'img':
            self.images.append(values)


def check_site(site: Path, release: bool = False) -> None:
    site = site.resolve()
    if not site.is_dir():
        raise ValueError(f'网站目录不存在：{site}')
    files, documents = {}, {}
    for file in site.rglob('*'):
        if file.is_symlink():
            raise ValueError(f'公开目录含符号链接：{file}')
        if not file.is_file():
            continue
        name = file.relative_to(site).as_posix()
        if name not in PUBLIC_FILES:
            raise ValueError(f'未允许公开的文件：{name}')
        files[name] = file
        if file.suffix in {'.html', '.css', '.js', '.json'}:
            text = file.read_text(encoding='utf-8')
            if '{{' in text or '{%' in text:
                raise ValueError(f'未替换的模板变量：{name}')
            if any(marker in text for marker in PRIVATE_MARKERS):
                raise ValueError(f'疑似私有资料进入公开文件：{name}')
            # Manifest values are SHA-256 hashes; digit runs inside them are not contacts.
            if name != 'public-manifest.json' and (re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', text)
                    or re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)', text)):
                raise ValueError(f'疑似邮箱或手机号进入公开文件：{name}')
        if file.suffix == '.html':
            document = Links(); document.feed(file.read_text(encoding='utf-8'))
            documents[name] = document
            if any('alt' not in image for image in document.images):
                raise ValueError(f'图片缺少 alt：{name}')
    required = {'index.html', 'manual.html', 'results.html', '.nojekyll', 'assets/site.css',
                'assets/site.js', 'build-meta.json', 'public-manifest.json'}
    if required - files.keys():
        raise ValueError(f'站点缺少文件：{sorted(required - files.keys())}')
    manifest = json.loads(files['public-manifest.json'].read_text(encoding='utf-8'))
    if set(manifest) != files.keys() - {'public-manifest.json'}:
        raise ValueError('文件列表与公开清单不一致，请重新 build')
    for name, digest in manifest.items():
        if hashlib.sha256(files[name].read_bytes()).hexdigest() != digest:
            raise ValueError(f'公开文件哈希不匹配：{name}')
    for name, document in documents.items():
        for ref in document.refs:
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
                    raise ValueError(f'不允许的外部链接：{name} {ref}')
                continue
            if parsed.path.startswith('/'):
                raise ValueError(f'请使用相对路径：{name} {ref}')
            target = (files[name].parent / unquote(parsed.path)).resolve() if parsed.path else files[name]
            if target.is_dir():
                target /= 'index.html'
            if not target.is_relative_to(site) or not target.is_file():
                raise ValueError(f'本地链接/资源不存在：{name} {ref}')
            if parsed.fragment and target.suffix == '.html':
                other = documents.get(target.relative_to(site).as_posix())
                if other and unquote(parsed.fragment) not in other.ids:
                    raise ValueError(f'锚点不存在：{name} {ref}')
    metadata = json.loads(files['build-meta.json'].read_text(encoding='utf-8'))
    if metadata['status'] not in {'upcoming', 'open', 'closed', 'finished'}:
        raise ValueError('站点状态无效')
    if release and metadata.get('release') is not True:
        raise ValueError('这是草稿站点；请先在工作流仓库执行 build --release 并重新同步')
    if 'CNAME' in files:
        domain = files['CNAME'].read_text(encoding='ascii').strip()
        if metadata['site_url'] != f'https://{domain}':
            raise ValueError('CNAME 与 site.url 不匹配')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='检查静态站点清单、链接及常见隐私字段')
    parser.add_argument('site', type=Path)
    parser.add_argument('--release', action='store_true', help='拒绝部署草稿')
    args = parser.parse_args()
    check_site(args.site, release=args.release)
    print('公开文件清单、资源和隐私标记检查通过。')
