"""Try higher-order coarse-region residuals after the 795-entry spatial model."""
import json
import time

from architecture import ROOT
from experiment_spatial_residual import evaluate, fit, load


def main():
    started=time.monotonic()
    development=load('development','spatial')
    validation=load('validation','spatial')
    designs=[('x_pair_source_y',),('x_pair_target_y',),
             ('y_pair_source_x',),('y_pair_target_x',),
             ('x_pair_source_y','x_pair_target_y'),
             ('x_pair_source_y','y_pair_source_x')]
    results=[]
    for families in designs:
        tables=fit(development,families,100)
        results.append({'features':families,'entries':[len(t) for t in tables],
                        'metrics':evaluate(validation,families,tables)})
    report={'baseline':evaluate(validation,(),()),'candidates':results,
            'elapsed_seconds':time.monotonic()-started,'holdout_used':False}
    (ROOT/'reports/P4-spatial-interactions.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
