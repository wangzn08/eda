#pragma once
#include "routing_search.hpp"
#ifdef BUDGET_PORT_METADATA_HEADER
#include BUDGET_PORT_METADATA_HEADER
#endif
// Compute only fields visited by the compiled tiny tree. No route search,
// phi reads, or per-request hash cache is involved in the correction.
struct BudgetResidualFeatures {
 int b,sx,sy,tx,ty,sp,tp,dx,dy,ax,ay;
 BudgetResidualFeatures(Node from,Node to,int base):b(base){auto a=archdata::SITES[from/496],z=archdata::SITES[to/496];sx=a.x;sy=a.y;tx=z.x;ty=z.y;sp=from%496;tp=to%496;dx=tx-sx;dy=ty-sy;ax=std::abs(dx);ay=std::abs(dy);}
 template<unsigned I>int integer()const{
  if constexpr(I==0)return b;
  else if constexpr(I==1)return sx;else if constexpr(I==2)return sy;
  else if constexpr(I==3)return tx;else if constexpr(I==4)return ty;
  else if constexpr(I==5)return sp;else if constexpr(I==6)return tp;
  else if constexpr(I==7)return dx;else if constexpr(I==8)return dy;
  else if constexpr(I==9)return ax;else if constexpr(I==10)return ay;
  else if constexpr(I==11)return ax/10;else if constexpr(I==12)return ay/12;
  else if constexpr(I==13)return ax%10;else if constexpr(I==14)return ay%12;
  else if constexpr(I==15)return sx%10;else if constexpr(I==16)return sy%12;
  else if constexpr(I==17)return tx%10;else if constexpr(I==18)return ty%12;
  else if constexpr(I==19)return sy%100;else if constexpr(I==20)return ty%100;
  else if constexpr(I==21)return sy/100;else if constexpr(I==22)return ty/100;
  else if constexpr(I==23)return std::min(sx,119-sx);else if constexpr(I==24)return std::min(tx,119-tx);
  else if constexpr(I==25)return std::min(sy,549-sy);else if constexpr(I==26)return std::min(ty,549-ty);
  else if constexpr(I==27)return std::min(sx,tx)<76&&std::max(sx,tx)>89;
  else if constexpr(I==28)return sy/100==ty/100;
  else if constexpr(I==29)return std::min(std::abs(sx-75),std::abs(sx-90));
  else if constexpr(I==30)return std::min(std::abs(tx-75),std::abs(tx-90));
  else if constexpr(I==31)return 12*b-150*ax-125*ay;
  else if constexpr(I==32)return (dx%10+10)%10;else if constexpr(I==33)return (dy%12+12)%12;
  else if constexpr(I>=34&&I<50){
#ifdef BUDGET_PORT_METADATA_HEADER
   return budget_port_metadata[I<42?sp:tp][I<42?I-34:I-42];
#else
   static_assert(I<34,"Port metadata was not supplied");return 0;
#endif
  }
  else if constexpr(I==50)return dx-integer<38>()-integer<48>();
  else if constexpr(I==51)return dy-integer<39>()-integer<49>();
  else if constexpr(I==52)return std::abs(integer<50>());
  else if constexpr(I==53)return std::abs(integer<51>());
  else if constexpr(I==54)return (integer<50>()%10+10)%10;
  else if constexpr(I==55)return (integer<51>()%12+12)%12;
  else {static_assert(I<56,"Unknown budget residual feature");return 0;}
 }
};
