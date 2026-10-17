"""Features derived from current chosen ideal route, not an older predictor."""
import re,struct
from pathlib import Path
import numpy as np
from architecture import Architecture,ROOT
from boundary_potential_features import node_potentials

DTYPE=np.dtype([(k,'<u2') for k in ('sx','sy','tx','ty','core','end','target','kind')]+[(k,'<i4') for k in ('entry','nominal','terminal')])
assert DTYPE.itemsize==28
arch=Architecture();incoming=np.array([[n['delta x'],n['delta y'],n.get('delay',0)] for n in arch.nets],np.float32)
category={};port_type=[];port_lane=[]
for p in arch.ports:
    m=re.fullmatch(r'(.*)\[(\d+)\]',p['Name']);prefix=m[1] if m else p['Name']
    port_type.append(category.setdefault(prefix,len(category)));port_lane.append(int(m[2]) if m else -1)
port_type=np.array(port_type,np.int32);port_lane=np.array(port_lane,np.int32)
xgap=np.zeros(120,np.int32);ygap=np.zeros(550,np.int32)
for l in arch.lines:
    a=xgap if l['direction']=='vertical' else ygap;a[l['site']+1:]+=l['delay']

def read_selection(prefix):
    path=Path(str(prefix)+'.selected')
    with path.open('rb') as f:h=f.read(80)
    assert h[:8]==b'FULSEL01';n,stride=struct.unpack('<2I',h[72:80]);assert stride==28
    records=np.memmap(path,dtype=DTYPE,mode='r',offset=80,shape=(n,))
    with Path(str(prefix)+'.response').open('rb') as f:h=f.read(80)
    nr,response_stride=struct.unpack('<2I',h[72:80]);assert h[:8]==b'FULRES01' and nr==n and response_stride in (32,36)
    responses=np.memmap(str(prefix)+'.response',dtype='<i4',mode='r',offset=80,shape=(n,response_stride//4))
    return records,responses

def selected_features(a,records,response,base):
    valid=records['core']<160
    sx=np.where(valid,records['sx'],a[:,0]).astype(np.int32);sy=np.where(valid,records['sy'],a[:,1]).astype(np.int32)
    tx,ty=a[:,2].astype(np.int32),a[:,3].astype(np.int32)
    core=np.where(valid,records['core'].astype(np.int32),-1);end=np.where(valid,records['end'].astype(np.int32),-1)
    sp,tp=a[:,80].astype(np.int32),a[:,94].astype(np.int32);assert np.array_equal(records['target'][valid],tp[valid])
    dx,dy=tx-sx,ty-sy;ax,ay=np.abs(dx),np.abs(dy)
    qx=np.where(ax>29,(ax-20)//10,0);qy=ay//12
    rx=np.sign(dx)*(ax-qx*10);ry=np.sign(dy)*(ay%12)
    entry=np.where(valid,records['entry'],0);nominal=np.where(valid,records['nominal'],base);arc=np.where(valid,records['terminal'],0);kind=np.where(valid,records['kind'].astype(np.int32),-1)
    gx=xgap[tx]-xgap[sx];gy=ygap[ty]-ygap[sy]
    cross=(np.minimum(sx,tx)<76)&(np.maximum(sx,tx)>89)
    inside_s=(sx>=76)&(sx<=89);inside_t=(tx>=76)&(tx<=89)
    bands=np.zeros(len(a),np.float32)
    for y in range(0,450,100):bands+=((np.minimum(sy,ty)<y+49)&(np.maximum(sy,ty)>y)).astype(np.float32)
    features={
        'base':base,'sx':sx,'sy':sy,'tx':tx,'ty':ty,'original_sx':a[:,0],'original_sy':a[:,1],
        'source_port':sp,'target_port':tp,'source_category':port_type[sp],'target_category':port_type[tp],
        'source_lane':port_lane[sp],'target_lane':port_lane[tp],'source_core':core,'end_core':end,
        'core_type':np.where(valid,core%20,-1),'end_type':np.where(valid,end%20,-1),
        'core_lane':np.where(valid,core//20,-1),'end_lane':np.where(valid,end//20,-1),
        'dx':dx,'dy':dy,'abs_dx':ax,'abs_dy':ay,'qx':qx,'qy':qy,'rx':rx,'ry':ry,
        'source_x_mod10':sx%10,'source_y_mod12':sy%12,'target_x_mod10':tx%10,'target_y_mod12':ty%12,
        'source_y_mod100':sy%100,'target_y_mod100':ty%100,'source_y_band':sy//100,'target_y_band':ty//100,
        'source_edge_x':np.minimum(sx,119-sx),'target_edge_x':np.minimum(tx,119-tx),
        'source_edge_y':np.minimum(sy,549-sy),'target_edge_y':np.minimum(ty,549-ty),
        'source_band_edge':np.minimum(sy%100,99-sy%100),'target_band_edge':np.minimum(ty%100,99-ty%100),
        'source_initial_jump_x':sx-a[:,0],'source_initial_jump_y':sy-a[:,1],
        'entry':entry,'nominal':nominal,'arc':arc,'kind':kind,'valid':valid,
        'nominal_residual':nominal-125*qx-np.where(dy>0,127,125)*qy,
        'geometry_cost':base-entry-nominal,'x_line_difference':gx,'y_line_difference':gy,
        'abs_x_line_difference':abs(gx),'abs_y_line_difference':abs(gy),'cross':cross,
        'inside_source_wall':inside_s,'inside_target_wall':inside_t,'crossed_wall_bands':bands,
        'source_wall_edge':np.minimum(sx-75,90-sx),'target_wall_edge':np.minimum(tx-75,90-tx),
        'left_void_x':np.maximum(0,16-np.minimum(sx,tx)),'left_void_y':np.maximum(0,100-np.minimum(sy,ty)),
        'same_wall_band':cross&(sy//100==ty//100)&(sy%100<=49)&(ty%100<=49),
    }
    for name,p in [('core',core),('end',end)]:
        v=np.zeros((len(a),3),np.float32);v[valid]=incoming[p[valid]]
        for j in range(3):features[f'{name}_incoming_{j}']=v[:,j]
    for j in range(response.shape[1]):features[f'response_{j}']=response[:,j]
    for name,x,y,p in [('source',sx,sy,core),('target',tx,ty,end)]:
        phi=node_potentials(x,y,p)
        for j in range(24):features[f'{name}_phi_{j}']=phi[:,j]
    direction=(dx<0)*2+(dy<0);backward=(dx>=0)*2+(dy>=0)
    for name,x,y,p,d in [('source',sx,sy,core,direction),('target',tx,ty,end,backward)]:
        phi=node_potentials(x,y,p)
        for mode in range(2):
            for depth in range(3):features[f'{name}_direction_phi_{mode}_{depth}']=phi[np.arange(len(a)),mode*12+depth*4+d]
    return np.column_stack(list(features.values())).astype(np.float32),list(features)
