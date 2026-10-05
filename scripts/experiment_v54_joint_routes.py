"""Joint endpoint phase factors, small geometry, official-score training loss."""
import argparse
import json
import math
import time
import numpy as np
import torch
from torch import nn
from architecture import ROOT
from architecture_benchmark_data import load
from experiment_v50_fast_topology import features, lower
from experiment_v7_teacher import score


class JointRoutes(nn.Module):
    def __init__(self, n, hidden, routes):
        super().__init__()
        self.routes = routes
        self.s, self.t = nn.Embedding(496, routes), nn.Embedding(496, routes)
        self.ps, self.pt = nn.Embedding(496, 8), nn.Embedding(496, 8)
        self.sj = nn.Parameter(torch.randn(120, 8, routes)*.02)
        self.tj = nn.Parameter(torch.randn(120, 8, routes)*.02)
        self.geo = nn.Sequential(nn.Linear(n, hidden), nn.ReLU(), nn.Linear(hidden, hidden),
                                 nn.ReLU(), nn.Linear(hidden, routes))
        nn.init.normal_(self.s.weight, std=.03)
        nn.init.normal_(self.t.weight, std=.03)
        nn.init.zeros_(self.geo[-1].weight)
        nn.init.constant_(self.geo[-1].bias, .5)

    def forward(self, x, p, tau=0):
        phase = p[:, 2]*12+p[:, 3]
        a = (self.ps(p[:, 0])[:, :, None]*self.sj[phase]).sum(1)
        b = (self.pt(p[:, 1])[:, :, None]*self.tj[phase]).sum(1)
        costs = self.geo(x)+self.s(p[:, 0])+self.t(p[:, 1])+a+b
        return -tau*torch.logsumexp(-costs/tau, 1)+tau*math.log(self.routes) if tau else costs.amin(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=128)
    args = parser.parse_args()
    torch.set_num_threads(1)
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    folder = ROOT/'out/v54'
    folder.mkdir(exist_ok=True)
    x, y, _, _ = load('development')
    xv, yv, _, _ = load('validation')
    lo, lv = lower('development'), lower('validation')
    a, av = features(x, lo), features(xv, lv)
    mean, std = a.mean(0), np.maximum(a.std(0), 1)
    a, av = np.clip((a-mean)/std, -10, 10), np.clip((av-mean)/std, -10, 10)
    m = y > 0
    def phase(z):
        return torch.tensor(np.column_stack((z[:, 10:12], z[:, 35] % 10, z[:, 36] % 12)),
                            dtype=torch.long, device=device)
    xx, vx = torch.tensor(a[m], device=device), torch.tensor(av, device=device)
    pp, vp = phase(x[m]), phase(xv)
    yy = torch.tensor((y[m]-lo[m])/100, dtype=torch.float32, device=device)
    weights = torch.tensor(400/y[m], dtype=torch.float32, device=device)
    baseline = np.load(ROOT/'out/v50/validation-10-256.npy')
    far = xv[:, 6]+xv[:, 7] >= 150
    report = {'fit_split': 'development', 'selection_split': 'validation', 'holdout_used': False,
              'device': str(device), 'architecture': 'Joint 120-phase rank8 endpoint factors; hard-min route experts',
              'loss': 'mean(tanh(4*abs(pred-golden)/golden)), continuous prediction, development only',
              'scope': 'Learned gap, no path witness or per-query error certificate', 'candidates': []}
    begin = time.monotonic()
    for hidden, routes in ((32, 128), (32, 256), (64, 256)):
        torch.manual_seed(20261008+hidden+routes)
        model = JointRoutes(71, hidden, routes).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=.002, weight_decay=1e-5)
        for epoch in range(1, args.epochs+1):
            tau = .2*(1+math.cos(math.pi*min(epoch, args.epochs*.75)/(args.epochs*.75)))/2
            model.train()
            for idx in torch.randperm(len(xx), device=device).split(4096):
                opt.zero_grad(set_to_none=True)
                gap = model(xx[idx], pp[idx], tau)
                # Forward clipping matches inference; straight-through gradient avoids dead negative gaps.
                clipped = gap+(torch.clamp(gap, min=0)-gap).detach()
                loss = torch.tanh(torch.abs(clipped-yy[idx])*weights[idx]).mean()
                loss.backward()
                opt.step()
            for group in opt.param_groups:
                group['lr'] = .0001+.0019*(1+math.cos(math.pi*epoch/args.epochs))/2
            if epoch == 1 or epoch % 8 == 0:
                model.eval()
                with torch.no_grad():
                    gap = torch.cat([model(vx[i:i+4096], vp[i:i+4096], 0).cpu()
                                     for i in range(0, len(vx), 4096)]).numpy()
                pred = np.rint(lv+np.maximum(0, 100*gap))
                name = f'h{hidden}-r{routes}-e{epoch}'
                path = folder/f'{name}.pt'
                torch.save({'state': {k: v.detach().cpu() for k, v in model.state_dict().items()},
                            'numeric': 71, 'hidden': hidden, 'routes': routes,
                            'mean': mean, 'std': std, 'epoch': epoch, 'joint_phase': True}, path)
                np.save(folder/f'{name}.npy', pred)
                item = {'hidden': hidden, 'routes': routes, 'epoch': epoch,
                        'validation_score': score(yv, pred),
                        'distance150_mixed_score': score(yv, np.where(far, pred, baseline)),
                        'weights': str(path.relative_to(ROOT)), 'weights_bytes': path.stat().st_size,
                        'elapsed_seconds': time.monotonic()-begin}
                report['candidates'].append(item)
                report['best'] = max(report['candidates'], key=lambda r: r['distance150_mixed_score'])
                (ROOT/'reports/V54-joint-routes.json').write_text(json.dumps(report, indent=2)+'\n')
                print(json.dumps(item), flush=True)
    report['state'] = 'complete'
    (ROOT/'reports/V54-joint-routes.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
