#!/usr/bin/env python3
"""Clone выбранного commit и полный логический restore курса + embedded aie."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import runpy
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

DEFAULT_REPOSITORY = 'https://github.com/VadimMukabenov/ai-engineer.git'


def clean_env() -> dict[str, str]:
    user = pwd.getpwuid(os.getuid())
    return {'HOME': user.pw_dir, 'USER': user.pw_name,
            'PATH': f'{Path.home() / ".local/bin"}:/usr/local/bin:/usr/bin:/bin',
            'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
            'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_TERMINAL_PROMPT': '0', 'UV_NO_PROGRESS': '1', 'UV_PYTHON_DOWNLOADS': 'never',
            'PYTHONDONTWRITEBYTECODE': '1'}


def command(args: list[str], cwd: Path, *, timeout: int = 180) -> str:
    result = subprocess.run(args, cwd=cwd, env=clean_env(), text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{Path(args[0]).name} завершился кодом {result.returncode}: '
                           f'{(result.stderr or result.stdout)[-5000:].strip()}')
    return result.stdout


def git(root: Path, *args: str) -> str:
    return command(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args], root)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value) -> str:
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':')).encode('utf-8'))


def inside_file(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Недопустимый относительный путь: {name}')
    path = root / relative
    # Для первой процедуры не поддерживаем symlinks/submodules: не следуем за checkout.
    if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise ValueError(f'Symlink в восстанавливаемом содержимом не поддерживается: {name}')
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Файл отсутствует или выходит за root: {name}')
    return path


def tracked_files(clone: Path) -> list[str]:
    names = git(clone, 'ls-files', '-z').split('\0')
    result = []
    for name in names:
        if not name or Path(name).parts[0] in {'.git', '.beads'}:
            continue
        inside_file(clone, name)
        result.append(name)
    return sorted(result)


def file_inventory(root: Path, names: list[str]) -> dict:
    return {name: {'sha256': sha(inside_file(root, name).read_bytes()),
                   'executable': bool(inside_file(root, name).stat().st_mode & 0o111)} for name in names}


def newest_public_snapshot(clone: Path) -> Path:
    candidates = []
    for path in sorted((clone / 'backups').rglob('manifest.json')):
        inside_file(clone, path.relative_to(clone).as_posix())
        row = json.loads(path.read_text())
        if row.get('public') is True and row.get('format') == 'beads-cli-export-jsonl':
            when = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
            if when.tzinfo is None:
                raise ValueError('Snapshot created_at должен включать timezone')
            candidates.append((when, path.relative_to(clone).as_posix(), path.parent))
    if not candidates:
        raise ValueError('В выбранном commit нет public Beads snapshot в backups/')
    return max(candidates)[2]


def learning_inventory(root: Path) -> dict:
    records: dict[str, str] = {}
    evidence: dict[str, str] = {}
    groups: dict[str, int] = {}
    for kind in ['attempts', 'assessments']:
        files = sorted((root / 'learning_records' / kind).glob('*.json'))
        groups[kind] = len(files)
        for file in files:
            name = file.relative_to(root).as_posix()
            path = inside_file(root, name)
            records[name] = sha(path.read_bytes())
            row = json.loads(path.read_text())
            if kind == 'assessments':
                for item in row['evidence']:
                    actual = sha(inside_file(root, item['path']).read_bytes())
                    if actual != item['sha256']:
                        raise ValueError(f'Несовпадение evidence hash: {item["path"]}')
                    evidence[item['path']] = actual
    return {'counts': groups, 'record_hashes': records, 'evidence_hashes': evidence}


def catalog_inventory(root: Path) -> dict:
    catalog = json.loads(inside_file(root, 'projects/learning-hub/course/catalog.json').read_text())
    plan = json.loads(inside_file(root, 'governance/plan.json').read_text())
    result = {kind: sorted(row['id'] for row in catalog[kind])
              for kind in ['skills', 'modules', 'outcomes', 'lessons']}
    result['projects'] = sorted(plan['mandatory_project_ids'])
    return result


def tracker_inventory(records: list[dict]) -> dict:
    issues = [r for r in records if r.get('_type', 'issue') == 'issue']
    return {'statuses': {r['id']: r['status'] for r in sorted(issues, key=lambda r: r['id'])},
            'dependencies': sorted((dep['issue_id'], dep['depends_on_id'], dep['type'])
                                   for r in issues for dep in r.get('dependencies', []))}


def hub(uv: str, recovery: Path, data_root: Path, action: str) -> dict:
    return json.loads(command([uv, 'run', '--project', str(recovery / 'projects/learning-hub'),
                               '--locked', 'learning-hub', '--root', str(data_root), action], recovery))


def run(repository: str, ref: str) -> dict:
    url = urlparse(repository)
    remote = url.scheme == 'https' and url.netloc == 'github.com' and url.path.removesuffix('.git') == '/VadimMukabenov/ai-engineer'
    if not remote and url.scheme != 'file':
        raise ValueError('Разрешён публичный GitHub ai-engineer или явный file:// для локальной проверки')
    if not ref or ref.startswith('-'):
        raise ValueError('Нужен явный Git ref или commit, не флаг')
    uv = shutil.which('uv')
    if not uv:
        raise ValueError('Не найден uv; системные пакеты автоматически не устанавливаются')
    with tempfile.TemporaryDirectory(prefix='aie-combined-restore-') as td:
        temp = Path(td); clone = temp / 'clone'; recovery = temp / 'recovered'
        command(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--no-checkout', '--', repository, str(clone)], temp)
        commit = git(clone, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}').strip()
        git(clone, 'checkout', '--detach', commit)
        names = tracked_files(clone)
        source_code = file_inventory(clone, names)
        expected_learning = learning_inventory(clone)
        expected_catalog = catalog_inventory(clone)
        snapshot = newest_public_snapshot(clone)
        api = runpy.run_path(str(inside_file(clone, 'scripts/beads-portable')))
        _, expected_tracker, manifest = api['read_snapshot'](snapshot)
        if manifest.get('public') is not True:
            raise ValueError('Выбранный snapshot не public')
        # restore сам создаёт НОВЫЙ путь/БД, проверяет пустоту и полный logical round-trip.
        tracker_report = api['restore'](snapshot, recovery)
        identity_before = api['context'](recovery)
        # Копируем только tracked code/content, никогда не .git/.beads источника.
        for name in names:
            source = inside_file(clone, name); target = recovery / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink() or target.is_dir():
                raise ValueError(f'Исходники столкнулись с небезопасным путём: {name}')
            # Native init создаёт корневой .gitignore. В НОВОМ recovery заменяем
            # обычные служебные файлы исходниками commit; .git/.beads исключены выше.
            shutil.copy2(source, target)
        if api['context'](recovery) != identity_before:
            raise ValueError('Копирование исходников изменило контекст восстановленного tracker')
        if file_inventory(recovery, names) != source_code:
            raise ValueError('Копия исходников не совпадает с выбранным commit')
        expected_verify = hub(uv, recovery, clone, 'verify')
        restored_verify = hub(uv, recovery, recovery, 'verify')
        if expected_verify.get('valid') is not True or restored_verify != expected_verify:
            raise ValueError('Проверка курса на clone/recovery не совпала или неуспешна')
        expected_status = hub(uv, recovery, clone, 'status')
        restored_status = hub(uv, recovery, recovery, 'status')
        expected_status.pop('checked_at', None); restored_status.pop('checked_at', None)
        if expected_status != restored_status or not restored_status['integrity']['valid']:
            raise ValueError('Прогресс/статус восстановленного курса отличается от выбранного commit')
        actual_learning = learning_inventory(recovery)
        if actual_learning != expected_learning or catalog_inventory(recovery) != expected_catalog:
            raise ValueError('Record counts, evidence hashes или IDs курса не совпадают')
        _, actual_tracker = api['export_records'](recovery)
        if tracker_inventory(expected_tracker) != tracker_inventory(actual_tracker):
            raise ValueError('ID/status/dependency tracker изменились после объединённого восстановления')
        if api['canonical'](expected_tracker) != api['canonical'](actual_tracker):
            raise ValueError('Поля tracker отличаются от snapshot после проверки курса')
        if file_inventory(clone, names) != source_code or file_inventory(recovery, names) != source_code:
            raise ValueError('Команды проверки изменили tracked code/content')
        progress_keys = ['mastered_outcomes', 'total_outcomes', 'percent', 'attempt_count',
                         'ready_projects', 'mastered_ids', 'next_lesson_id']
        return {'schema_version': 1, 'valid': True, 'repository': repository,
                'requested_ref': ref, 'actual_commit': commit, 'remote_checked': remote,
                'source_kind': 'github_https_clone' if remote else 'local_file_clone',
                'snapshot': snapshot.relative_to(clone).as_posix(),
                'snapshot_sha256': manifest['sha256'], 'public': True,
                'code_sha256': digest(source_code), 'tracked_code_files': len(names),
                'tracker': {'counts': tracker_report['counts'], **tracker_inventory(actual_tracker)},
                'course_counts': {key: len(value) for key, value in expected_catalog.items()},
                'learning_records': {'counts': actual_learning['counts'],
                                     'record_count': sum(actual_learning['counts'].values()),
                                     'records_sha256': digest(actual_learning['record_hashes']),
                                     'evidence_count': len(actual_learning['evidence_hashes']),
                                     'evidence_sha256': digest(actual_learning['evidence_hashes'])},
                'progress': {key: restored_status[key] for key in progress_keys},
                'comparisons': {'source_code_unchanged': True, 'tracker_ids_status_dependencies': True,
                                'all_exported_tracker_fields': True, 'course_ids': True,
                                'records_and_evidence_hashes': True, 'verify_and_status': True},
                'limitations': [*tracker_report['limitations'],
                                'Новая отдельная Git-история: source .git и .beads не копируются.',
                                'Проверяется сохранённый snapshot, не более позднее состояние живого tracker.',
                                'Symlinks/submodules не поддерживаются этой процедурой.',
                                'Временные clone/recovery удалены после проверки.']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', '--repo', default=DEFAULT_REPOSITORY)
    parser.add_argument('--ref', required=True, help='Явный branch/tag/commit; в отчёте фиксируется actual commit')
    args = parser.parse_args()
    try:
        result = run(args.repository, args.ref)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'schema_version': 1, 'valid': False, 'error': str(error),
                          'repository': args.repository, 'requested_ref': args.ref}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
