load('kinknoMg_database.mat')
load('kinknoMg.mat')

%%
figure
tE = kinknoMg.Xband.time; SE = kinknoMg.Xband.Sexp; o= 0.1;
plot(tE,SE(:,1),'k', tE,SE(:,2)+o,'k', tE,SE(:,3)+2*o,'k', tE,SE(:,4)+3*o,'k', tE,SE(:,5)+4*o,'k', tE,SE(:,6)+5*o,'k');hold on

tD = OSP.time/1000; SiD = OSP.Sexp; o= 0.1;
[devn,SD] = ScaleModdev('single',SE,SiD);
plot(tD,SD(:,1),'r', tD,SD(:,2)+o,'r', tD,SD(:,3)+2*o,'r', tD,SD(:,4)+3*o,'r', tD,SD(:,5)+4*o,'r', tD,SD(:,6)+5*o,'r')

%%
[bend,Azz1,Azz2,scalar]=bendangle(OSP.Conformers.EulerAngles.R1,OSP.Conformers.EulerAngles.R2);

for iod = 1:length(bend)
    if bend(iod,1) > 90
        bendcor(iod,1) = 180-bend(iod,1);
    else
        bendcor(iod,1) = bend(iod,1);
    end
end

figure; histogram(bendcor,'BinWidth',5)


%%
angle_in = acosd(dot(zaxis_in(1,:),zaxis_in(2,:)))
angle_out = acosd(dot(zaxis_out(1,:),zaxis_out(2,:)))

%%
figure
vectarrow([0,0,0],zaxis17(30,:))
hold on
vectarrow([0,0,0],zaxis24(1,:))
axis equal

acosd(dot(zaxis17(30,:),zaxis24(1,:)))
%%
figure
vectarrow([0,0,0],zaxis_out(1,:))
hold on
vectarrow([0,0,0],zaxis_out(2,:))
axis equal
acosd(dot(zaxis_out(2,:),zaxis_out(1,:)))

%%
% NC2out= Nout(1,:)-C2out(1,:);
% NC2turn= Nturn(30,:)-C2turn(30,:);
NC2out= C5out(1,:)-Nout(1,:);
NC2turn= C5turn(30,:)-Nturn(30,:);

acosd(dot(NC2out(1,:),NC2turn(1,:))/(norm(NC2out)*norm(NC2turn)))

% figure
% vectarrow([0 0 0], NC2out);hold on
% vectarrow([0 0 0], NC2turn)
% axis equal