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
    # JUnit may emit either <testsuite ...> or <testsuites><testsuite .../></testsuites>
    if root.tag == 'testsuite':
        testsuite_elements = [root]
    else:
        testsuite_elements = list(root.findall('.//testsuite'))

    if not testsuite_elements:
        return {
            'tests': 0,
            'errors': 0,
            'failures': 0,
            'skipped': 0,
            'time': 0.0,
        }

    aggregated = {
        'tests': 0,
        'errors': 0,
        'failures': 0,
        'skipped': 0,
        'time': 0.0,
    }

    for ts in testsuite_elements:
        aggregated['tests'] += int(ts.attrib.get('tests', '0'))
        aggregated['errors'] += int(ts.attrib.get('errors', '0'))
        aggregated['failures'] += int(ts.attrib.get('failures', '0'))
        aggregated['skipped'] += int(ts.attrib.get('skipped', '0'))
        aggregated['time'] += float(ts.attrib.get('time', '0'))

    return aggregated


def parse_coverage_xml(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {
            'line_rate': 0.0,
            'branch_rate': 0.0,
            'coverage_statements': 0,
            'coverage_missed': 0,
            'coverage_percent': 0.0,
        }
    root = ET.parse(xml_path).getroot()
    total = int(root.attrib.get('lines-valid', '0'))
    covered = int(root.attrib.get('lines-covered', '0'))
    missed = total - covered
    line_rate = float(root.attrib.get('line-rate', '0'))
    return {
        'line_rate': line_rate,  # 0..1
        'branch_rate': float(root.attrib.get('branch-rate', '0')),
        'coverage_statements': total,
        'coverage_missed': missed,
        'coverage_percent': line_rate * 100,
    }


def _prometheus_escape_label(value: str) -> str:
    return str(value).replace('\\', r'\\').replace('"', r'\"').replace('\n', r'\\n')


def get_pipeline_metadata():
    env = os.environ
    version = env.get('CI_PIPELINE_VERSION') or env.get('GITHUB_REF_NAME') or env.get('GITHUB_REF') or 'unknown'
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
        'status': env.get('CI_PIPELINE_STATUS', 'success'),
        'build_status': env.get('BUILD_STATUS', 'unknown'),
        'sca_sast_status': env.get('SCA_SAST_STATUS', 'unknown'),
        'test_status': env.get('TEST_STATUS', 'unknown'),
        'dast_status': env.get('DAST_STATUS', 'unknown'),
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

        fd.write('# HELP ci_pipeline_coverage_statements nombre total de statements analysés\n')
        fd.write('# TYPE ci_pipeline_coverage_statements gauge\n')
        fd.write(f"ci_pipeline_coverage_statements {metrics.get('coverage_statements', 0)}\n")

        fd.write('# HELP ci_pipeline_coverage_missed nombre de statements manquants\n')
        fd.write('# TYPE ci_pipeline_coverage_missed gauge\n')
        fd.write(f"ci_pipeline_coverage_missed {metrics.get('coverage_missed', 0)}\n")

        fd.write('# HELP ci_pipeline_coverage_percent pourcentage de couverture des statements (0-100)\n')
        fd.write('# TYPE ci_pipeline_coverage_percent gauge\n')
        fd.write(f"ci_pipeline_coverage_percent {metrics.get('coverage_percent', 0.0)}\n")

        fd.write('# HELP ci_pipeline_stage_status Statut des étapes principales du pipeline\n')
        fd.write('# TYPE ci_pipeline_stage_status gauge\n')
        fd.write(f"ci_pipeline_stage_status{{stage=\"build\",status=\"{_prometheus_escape_label(pipeline_meta['build_status'])}\"}} 1\n")
        fd.write(f"ci_pipeline_stage_status{{stage=\"sca_sast\",status=\"{_prometheus_escape_label(pipeline_meta['sca_sast_status'])}\"}} 1\n")
        fd.write(f"ci_pipeline_stage_status{{stage=\"test\",status=\"{_prometheus_escape_label(pipeline_meta['test_status'])}\"}} 1\n")
        fd.write(f"ci_pipeline_stage_status{{stage=\"dast\",status=\"{_prometheus_escape_label(pipeline_meta['dast_status'])}\"}} 1\n")
        fd.write(f"ci_pipeline_stage_status{{stage=\"ci\",status=\"{_prometheus_escape_label(pipeline_meta['status'])}\"}} 1\n")


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
