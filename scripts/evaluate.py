"""Official positive-delay score; zero denominators are explicitly separated."""
import argparse
import csv
import json
import math


def metrics(expected, actual):
    if len(expected) != len(actual):
        raise ValueError('Different row counts')
    scores, relative_errors = [], []
    exact, zeros, zero_exact = 0, 0, 0
    for e, a in zip(expected, actual):
        if (e['From'].strip(), e['To'].strip()) != (a['From'].strip(), a['To'].strip()):
            raise ValueError('Request order or endpoints differ')
        golden, prediction = int(e.get('delay', e.get('Min Delay'))), int(a['delay'])
        if prediction < 0 or golden < 0:
            raise ValueError('Negative delays are not supported')
        exact += golden == prediction
        if golden == 0:
            zeros += 1
            zero_exact += prediction == 0
            continue
        error = abs(prediction-golden)/golden
        relative_errors.append(error)
        scores.append(100*(1-math.tanh(4*error)))
    errors = sorted(relative_errors)
    def quantile(p):
        return errors[min(len(errors)-1, math.ceil(p*len(errors))-1)] if errors else None
    return {'rows': len(expected), 'exact_matches': exact, 'positive_delay_score': sum(scores)/len(scores) if scores else None,
            'zero_golden_rows': zeros, 'zero_exact_matches': zero_exact,
            'relative_error_p50': quantile(.50), 'relative_error_p95': quantile(.95), 'relative_error_p99': quantile(.99),
            'max_relative_error': max(errors) if errors else None,
            'zero_policy': 'Excluded from official-formula score because V0.3 does not define division by zero; correctness reported separately.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--golden', required=True)
    parser.add_argument('--result', required=True)
    args = parser.parse_args()
    with open(args.golden, newline='') as f, open(args.result, newline='') as g:
        result = metrics(list(csv.DictReader(f)), list(csv.DictReader(g)))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
