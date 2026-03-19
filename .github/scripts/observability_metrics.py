#!/usr/bin/env python3
"""Extraire des métriques à partir des fichiers de rapports de tests GitHub Actions"""

from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import os


def parse_pytest_junit(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {
            'tests': 0,
            'errors': 0,
            'failures': 0,
            'skipped': 0,
            'time': 0.0,
        }
    root = ET.parse(xml_path).getroot()
    return {
        'tests': int(root.attrib.get('tests', '0')),
        'errors': int(root.attrib.get('errors', '0')),
        'failures': int(root.attrib.get('failures', '0')),
        'skipped': int(root.attrib.get('skipped', '0')),
        'time': float(root.attrib.get('time', '0')),  # secondes
    }


def parse_coverage_xml(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {'line_rate': 0.0, 'branch_rate': 0.0}
    root = ET.parse(xml_path).getroot()
    return {
        'line_rate': float(root.attrib.get('line-rate', '0')),  # 0..1
        'branch_rate': float(root.attrib.get('branch-rate', '0')),
    }


def _prometheus_escape_label(value: str) -> str:
    return str(value).replace('\\', r'\\').replace('"', r'\"').replace('\n', r'\\n')


def get_pipeline_metadata():
    env = os.environ
    version = env.get('CI_PIPELINE_VERSION') or env.get('GITHUB_REF_NAME') or env.get('GITHUB_REF') or 'unknown'
    status = env.get('CI_PIPELINE_STATUS', 'success')
    return {
        'run_id': env.get('GITHUB_RUN_ID', 'unknown'),
        'run_number': env.get('GITHUB_RUN_NUMBER', 'unknown'),
        'run_attempt': env.get('GITHUB_RUN_ATTEMPT', 'unknown'),
        'workflow': env.get('GITHUB_WORKFLOW', 'unknown'),
        'job': env.get('GITHUB_JOB', 'unknown'),
        'repository': env.get('GITHUB_REPOSITORY', 'unknown'),
        'ref': env.get('GITHUB_REF', 'unknown'),
        'ref_name': env.get('GITHUB_REF_NAME', 'unknown'),
        'sha': env.get('GITHUB_SHA', 'unknown'),
        'actor': env.get('GITHUB_ACTOR', 'unknown'),
        'event_name': env.get('GITHUB_EVENT_NAME', 'unknown'),
        'version': version,
        'status': status,
    }


def record_prometheus_metrics(metrics: dict, out_path: Path, pipeline_meta: dict):
    with out_path.open('w', encoding='utf-8') as fd:
        labels = ','.join(
            f'{k}="{_prometheus_escape_label(v)}"' for k, v in pipeline_meta.items()
        )
        fd.write('# HELP ci_pipeline_info Informations d\u00e9finissant le pipeline GH Actions\n')
        fd.write('# TYPE ci_pipeline_info gauge\n')
        fd.write(f'ci_pipeline_info{{{labels}}} 1\n')
        fd.write('# HELP ci_pipeline_status Statut d\u00e9taill\u00e9 du pipeline\n')
        fd.write('# TYPE ci_pipeline_status gauge\n')
        fd.write(f"ci_pipeline_status{{status=\"{_prometheus_escape_label(pipeline_meta['status'])}\"}} 1\n")

        fd.write('# HELP ci_pipeline_test_total nombre total de tests exécutés\n')
        fd.write('# TYPE ci_pipeline_test_total gauge\n')
        fd.write(f"ci_pipeline_test_total {metrics['tests']}\n")

        fd.write('# HELP ci_pipeline_test_failures nombre de tests échoués\n')
        fd.write('# TYPE ci_pipeline_test_failures gauge\n')
        fd.write(f"ci_pipeline_test_failures {metrics['failures']}\n")

        fd.write('# HELP ci_pipeline_test_errors nombre de tests en erreur\n')
        fd.write('# TYPE ci_pipeline_test_errors gauge\n')
        fd.write(f"ci_pipeline_test_errors {metrics['errors']}\n")

        fd.write('# HELP ci_pipeline_test_skipped nombre de tests sautés\n')
        fd.write('# TYPE ci_pipeline_test_skipped gauge\n')
        fd.write(f"ci_pipeline_test_skipped {metrics['skipped']}\n")

        fd.write('# HELP ci_pipeline_test_duration_seconds durée totale des tests en secondes\n')
        fd.write('# TYPE ci_pipeline_test_duration_seconds gauge\n')
        fd.write(f"ci_pipeline_test_duration_seconds {metrics['time']}\n")

        fd.write('# HELP ci_pipeline_coverage_line_rate taux de couverture des lignes (0..1)\n')
        fd.write('# TYPE ci_pipeline_coverage_line_rate gauge\n')
        fd.write(f"ci_pipeline_coverage_line_rate {metrics['line_rate']}\n")

        fd.write('# HELP ci_pipeline_coverage_branch_rate taux de couverture des branches (0..1)\n')
        fd.write('# TYPE ci_pipeline_coverage_branch_rate gauge\n')
        fd.write(f"ci_pipeline_coverage_branch_rate {metrics['branch_rate']}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description='Génère des métriques Prometheus à partir des artefacts pytest/coverage')
    parser.add_argument('--junit', default='pytest-results.xml', help='Chemin vers le fichier JUnit XML pytest')
    parser.add_argument('--coverage', default='coverage.xml', help='Chemin vers le fichier Coverage XML')
    parser.add_argument('--out', default='observability.prom', help='Chemin du fichier métriques Prometheus')
    args = parser.parse_args()

    tests = parse_pytest_junit(Path(args.junit))
    cov = parse_coverage_xml(Path(args.coverage))

    merged = {
        **tests,
        **cov,
    }

    pipeline_meta = get_pipeline_metadata()
    record_prometheus_metrics(merged, Path(args.out), pipeline_meta)
    print(f'Métriques écrites dans {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
