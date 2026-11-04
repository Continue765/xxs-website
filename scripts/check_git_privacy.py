"""Check staged/tracked paths, including files added with git add -f."""
from pathlib import Path, PurePosixPath
import argparse
import subprocess


def check(repo: Path) -> None:
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=repo, check=True, capture_output=True)
    blocked = []
    private_dirs = {'local', 'private', 'output', 'backups', 'data', '.venv', '__pycache__'}
    private_suffixes = {'.xlsx', '.xls', '.csv', '.tsv', '.eml', '.pem', '.key', '.db', '.log', '.pyc'}
    for raw in result.stdout.split(b'\0'):
        if not raw:
            continue
        name = raw.decode('utf-8')
        path = PurePosixPath(name)
        filename = path.name.lower()
        if (private_dirs.intersection(path.parts) or path.suffix.lower() in private_suffixes
                or (filename.startswith('.env') and filename != '.env.example')
                or filename.startswith(('credentials', 'accounts', 'participants', 'secrets'))
                or '.local.' in filename or filename == 'workflow.json'):
            blocked.append(name)
    if blocked:
        raise ValueError('Git 索引包含私有资料路径，请先 git restore --staged：\n' + '\n'.join(blocked))
    print('Git 已跟踪路径检查通过（仍需人工审阅文本、图片与 diff）。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-hook', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.install_hook:
        hook = repo / '.git/hooks/pre-commit'
        body = '#!/bin/sh\npython3 scripts/check_git_privacy.py || exit 1\n'
        if (repo / 'scripts/check_site.py').exists():
            body += 'python3 scripts/check_site.py site || exit 1\n'
        if hook.exists() and hook.read_text() != body:
            raise SystemExit('已有 pre-commit hook，未覆盖；请人工合并检查命令。')
        hook.write_text(body, encoding='utf-8')
        hook.chmod(0o755)
        print('已安装本地 pre-commit hook。')
    check(repo)
