clear
% ordner = 'Z:\Members\Max\hairpin_kink\coords';
ordner = 'C:\Users\Max\OneDrive\hairpin_kink\structures\coords';

A = importdata(sprintf('%s/in_align_onfouratoms_resid17_C5_C4',ordner)); C5 = A(1,1:3); C4 = A(1,4:6);
B = importdata(sprintf('%s/in_align_onfouratoms_resid17_N1_C2',ordner)); N = B(1,1:3); C2 = B(1,4:6);
C = importdata(sprintf('%s/in_align_onfouratoms_resid24_C5_C4',ordner)); C5(2,1:3) = C(1,1:3); C4(2,1:3) = C(1,4:6);
D = importdata(sprintf('%s/in_align_onfouratoms_resid24_N1_C2',ordner)); N(2,1:3) = D(1,1:3); C2(2,1:3) = D(1,4:6);

% [M_in, zaxis_in, angle_in, r_in] = koordshairpin(N,C2,C4,C5)
ALL_in = koordshairpin(N,C2,C4,C5);
% OSP_in.Conformers.Distance = ALL_in.rRu/10; OSP_in.Conformers.EulerAngles.R1=ALL_in.o1; OSP_in.Conformers.EulerAngles.R2 = ALL_in.o2;
% 
% nu =1; figure; out_in = DBVisualizer(OSP_in,nu,'normal');hold on
% 
% figure; M_in = ALL_in.M/10; plot3(M_in(1,1),M_in(1,2),M_in(1,3),'bo');hold on
% 
% % axes_in.x=-axes_in.x;axes_in.y=-axes_in.y;axes_in.z=-axes_in.z;
% % axes_in.x=flip(axes_in.x);axes_in.y=flip(axes_in.y);axes_in.z=flip(axes_in.z);
% axes_in = M_in.axes;
% quiver3(M_in(1,1),M_in(1,2),M_in(1,3),axes_in.x(1,1),axes_in.x(1,2),axes_in.x(1,3),'r');hold on
% quiver3(M_in(1,1),M_in(1,2),M_in(1,3),axes_in.y(1,1),axes_in.y(1,2),axes_in.y(1,3),'g');hold on
% quiver3(M_in(1,1),M_in(1,2),M_in(1,3),axes_in.z(1,1),axes_in.z(1,2),axes_in.z(1,3),'k');hold on
% quiver3(M_in(2,1),M_in(2,2),M_in(2,3),axes_in.x(2,1),axes_in.x(2,2),axes_in.x(2,3),'r');hold on
% quiver3(M_in(2,1),M_in(2,2),M_in(2,3),axes_in.y(2,1),axes_in.y(2,2),axes_in.y(2,3),'g');hold on
% quiver3(M_in(2,1),M_in(2,2),M_in(2,3),axes_in.z(2,1),axes_in.z(2,2),axes_in.z(2,3),'k');hold on;axis equal
% quiver3(M_in(1,1),M_in(1,2),M_in(1,3),M_in(2,1)-M_in(1,1),M_in(2,2)-M_in(1,2),M_in(2,3)-M_in(1,3),'k');
load('C:\Users\Max\OneDrive\allgemeine_matlab_scripts\ExpParX.mat')
Conformers.EulerAngles.R1 = ALL_in.o1;
Conformers.EulerAngles.R2 = ALL_in.o2;
Conformers.Distance = ALL_in.rRu/10;
% Result=MainPELDORtime(EP,Conformers,[-0.1:0.01:1.2]);
% figure; plotmitoffset(Result.Sexp,Result.time/1000,0.15,'k')
% xlabel('time / ns')
% xlim([0 0.85])
% ylim([0.3 1.8]);
rad2deg(Conformers.EulerAngles.R1)
rad2deg(Conformers.EulerAngles.R2)
[bend,Azz1,Azz2,scalar]=bendangle(Conformers.EulerAngles.R1,Conformers.EulerAngles.R2);disp(bend)


%%
clear A B C D %N C2 C4 C5
% ordner = 'Z:\Members\Max\hairpin_kink\coords';
ordner = 'C:\Users\Max\OneDrive\hairpin_kink\structures\coords';

A = importdata(sprintf('%s/out_resid17_C5_C4_n',ordner)); C5out = A(1,1:3); C4out = A(1,4:6);
B = importdata(sprintf('%s/out_resid17_N1_C2_n',ordner)); Nout = B(1,1:3); C2out = B(1,4:6);
C = importdata(sprintf('%s/out_resid24_C5_C4_n',ordner)); C5out(2,1:3) = C(1,1:3); C4out(2,1:3) = C(1,4:6);
D = importdata(sprintf('%s/out_resid24_N1_C2_n',ordner)); Nout(2,1:3) = D(1,1:3); C2out(2,1:3) = D(1,4:6);
% [M_out, zaxis_out, angle_out, r_out] = koordshairpin(Nout,C2out,C4out,C5out)
ALL_out = koordshairpin(Nout,C2out,C4out,C5out);
OSP_out.Conformers.Distance = ALL_out.rRu/10; OSP_out.Conformers.EulerAngles.R1=ALL_out.o1;OSP_out.Conformers.EulerAngles.R2 = ALL_out.o2;
% figure; out_out = DBVisualizer(OSP_out,1,'normal');hold on
clear A B C D ordner

load('C:\Users\Max\OneDrive\allgemeine_matlab_scripts\ExpParX.mat')
Conformers_out.EulerAngles.R1 = ALL_out.o1;
Conformers_out.EulerAngles.R2 = ALL_out.o2;
Conformers_out.Distance = ALL_out.rRu/10;%ALL_in.rRu/10;%
Result_out=MainPELDORtime(EP,Conformers_out,[-0.1:0.01:1.2]);
% figure; plotmitoffset(Result_out.Sexp,Result_out.time/1000,0.15,'k')
% xlabel('time / ns')
% xlim([0 0.85])
% ylim([0.3 1.8]);

rad2deg(Conformers_out.EulerAngles.R1)
rad2deg(Conformers_out.EulerAngles.R2)
[bend_out,Azz1_out,Azz2_out,scalar_out]=bendangle(Conformers_out.EulerAngles.R1,Conformers_out.EulerAngles.R2);disp(bend_out)
%%
thet = linspace(0,-62,30);%-58
ps = linspace(0,-4.5,30);%9.3#
% theta = linspace(0,-62+6*-2.1379,30+6);
% psi = linspace(0,-4.5+6*-0.1552,30+6);%
direction = N(1,:)-Nout(1,:); direction = direction/29; 
drehaxx = C5out(1,:)-Nout(1,:);
drehaxx = drehaxx/norm(drehaxx);
Naufnull = Nout(1,:)-Nout(1,:); C2aufnull = C2out(1,:)-Nout(1,:); C4aufnull = C4out(1,:)-Nout(1,:); C5aufnull = C5out(1,:)-Nout(1,:);

figure
for i=1:length(thet)
    Nturnwork(i,:)  = drehenRodrigues(Naufnull,drehaxx,thet(i));
    C2turnwork(i,:) = drehenRodrigues(C2aufnull,drehaxx,thet(i));
    C4turnwork(i,:) = drehenRodrigues(C4aufnull,drehaxx,thet(i));
    C5turnwork(i,:) = drehenRodrigues(C5aufnull,drehaxx,thet(i));
    
    C2Naxxw = C2turnwork(i,:)-Nturnwork(i,:); z=cross(drehaxx,C2Naxxw); z = z/norm(z);
    C2Naxx= cross(z,drehaxx);C2Naxx = C2Naxx/norm(C2Naxx);
    
    Nturn(i,:)  = drehenRodrigues(Nturnwork(i,:),z,ps(i))+direction*(i-1)+Nout(1,:);
    C2turn(i,:) = drehenRodrigues(C2turnwork(i,:),z,ps(i))+direction*(i-1)+Nout(1,:);
    C4turn(i,:) = drehenRodrigues(C4turnwork(i,:),z,ps(i))+direction*(i-1)+Nout(1,:);
    C5turn(i,:) = drehenRodrigues(C5turnwork(i,:),z,ps(i))+direction*(i-1)+Nout(1,:);
%     drehaxx = C5turn(i,:)-Nturn(i,:);drehaxx = drehaxx/norm(drehaxx);
   pltclr.plotdacoords(Nturn,C2turn,C4turn,C5turn,i)

end

pltclr.plotdacoordscolor(N,C2,C4,C5,1,'ko')
pltclr.plotdacoordscolor(Nout,C2out,C4out,C5out,1,'mo')

ALL17 = koordshairpin(Nturn,C2turn,C4turn,C5turn);
ALL24 = koordshairpin(Nout(2,:),C2out(2,:),C4out(2,:),C5out(2,:));
r = vecnorm((ALL17.M-repmat(ALL24.M,size(ALL17.M,1),1)),2,2);

%% distribution of thet and ps; distribution between both states
load('kinknoMg.mat'); load('kink600Mg.mat'); load('kink12mMMg.mat')
sigma =5.5; mu= 20; x = [0:1:29];
p=1/sqrt(2*pi*sigma.^2)*exp(-(x-mu).^2/(2*sigma.^2));
% p = normrnd(mu,sigma,200,1); figure;histogram(p)

figure;plot((r),p/max(p));hold on
plot(kinknoMg.Qband.distr(:,1)*10,kinknoMg.Qband.distr(:,2)/max(kinknoMg.Qband.distr(:,2)))
% plot(kink600Mg.Qband.distr(:,1)*10,kink600Mg.Qband.distr(:,2)/max(kink600Mg.Qband.distr(:,2)))
% plot(kink12mMMg.Qband.distr(:,1)*10,kink12mMMg.Qband.distr(:,2)/max(kink12mMMg.Qband.distr(:,2)))
xlim([20 30])

%% theta angle distribution
for d = 1:size(ALL17.axes.z,1)
    angle(d) = acosd(dot(ALL17.axes.z(d,:),ALL24.axes.z)/(norm(ALL17.axes.z(d,:))*norm(ALL24.axes.z)));
end
figure
plot((angle),p/max(p))

 
%% dopppel Verteilung
l=10;h=6;
theta2g = linspace(+l*2.1379,-62+h*-2.1379,30+l+h);%[-2.13793103448276]
psi2g = linspace(+l*0.1552,-4.5+h*-0.1552,30+l+h);%[-0.155172413793103]
% theta = linspace(0,-62,30);
% psi = linspace(0,-4.5,30);
direction2g = N(1,:)-Nout(1,:); direction2g = direction2g/29; 
drehaxx2g = C5out(1,:)-Nout(1,:);
drehaxx2g = drehaxx2g/norm(drehaxx2g);
Naufnull = Nout(1,:)-Nout(1,:); C2aufnull = C2out(1,:)-Nout(1,:); C4aufnull = C4out(1,:)-Nout(1,:); C5aufnull = C5out(1,:)-Nout(1,:);

% dirsteps=[6:-1:0,1:1:35];
dirsteps=[l:-1:0,1:1:29+h];
figure
for i=1:length(theta2g)
    Nturnwork2g(i,:)  = drehenRodrigues(Naufnull,drehaxx2g,theta2g(i));
    C2turnwork2g(i,:) = drehenRodrigues(C2aufnull,drehaxx2g,theta2g(i));
    C4turnwork2g(i,:) = drehenRodrigues(C4aufnull,drehaxx2g,theta2g(i));
    C5turnwork2g(i,:) = drehenRodrigues(C5aufnull,drehaxx2g,theta2g(i));
    
    C2Naxxw2g = C2turnwork2g(i,:)-Nturnwork2g(i,:); z=cross(drehaxx2g,C2Naxxw2g); z = z/norm(z);
    C2Naxx2g= cross(z,drehaxx2g);C2Naxx2g = C2Naxx2g/norm(C2Naxx2g);
    
    if theta2g(i) <= 0
        Nturn2g(i,:)  = drehenRodrigues(Nturnwork2g(i,:),z,psi2g(i))+direction2g*dirsteps(i)+Nout(1,:);
        C2turn2g(i,:) = drehenRodrigues(C2turnwork2g(i,:),z,psi2g(i))+direction2g*dirsteps(i)+Nout(1,:);
        C4turn2g(i,:) = drehenRodrigues(C4turnwork2g(i,:),z,psi2g(i))+direction2g*dirsteps(i)+Nout(1,:);
        C5turn2g(i,:) = drehenRodrigues(C5turnwork2g(i,:),z,psi2g(i))+direction2g*dirsteps(i)+Nout(1,:);
    else
        Nturn2g(i,:)  = drehenRodrigues(Nturnwork2g(i,:),z,psi2g(i))-direction2g*dirsteps(i)+Nout(1,:);
        C2turn2g(i,:) = drehenRodrigues(C2turnwork2g(i,:),z,psi2g(i))-direction2g*dirsteps(i)+Nout(1,:);
        C4turn2g(i,:) = drehenRodrigues(C4turnwork2g(i,:),z,psi2g(i))-direction2g*dirsteps(i)+Nout(1,:);
        C5turn2g(i,:) = drehenRodrigues(C5turnwork2g(i,:),z,psi2g(i))-direction2g*dirsteps(i)+Nout(1,:);
    end
    pltclr.plotdacoords(Nturn2g,C2turn2g,C4turn2g,C5turn2g,i)
end

pltclr.plotdacoordscolor(N,C2,C4,C5,1,'ko')
pltclr.plotdacoordscolor(Nout,C2out,C4out,C5out,1,'mo')

[M17_2g,zaxis17_2g] = koordshairpin(Nturn2g,C2turn2g,C4turn2g,C5turn2g);
[M24_2g,zaxis24_2g] = koordshairpin(Nout(2,:),C2out(2,:),C4out(2,:),C5out(2,:));
r_2g = vecnorm((M17_2g-repmat(M24_2g,size(M17_2g,1),1)),2,2);

load('kinknoMg.mat')
sigma1 =4.5; mu1= 31.5; 
sigma2 =6.5; mu2= 16.5; 
x_2g = [0:1:29+l+h];
p1=1/sqrt(2*pi*sigma1.^2)*exp(-(x_2g-mu1).^2/(2*sigma1.^2));
p2=1/sqrt(2*pi*sigma2.^2)*exp(-(x_2g-mu2).^2/(2*sigma2.^2));
figure;
plot(kinknoMg.Xband.distr(:,1)*10,kinknoMg.Xband.distr(:,2)/max(kinknoMg.Xband.distr(:,2)));hold on
plot((r_2g),p1/max(p1)+p2/max(p2)*0.3);hold on
xlim([18 35]);xlabel('distance / Angstrom');legend('exp. X-band', 'two gaussian model')

for d = 1:size(zaxis17_2g,1)
    angle2g(d) = acosd(dot(zaxis17_2g(d,:),zaxis24_2g)/(norm(zaxis17_2g(d,:))*norm(zaxis24_2g)));
end

scal2g= 30;
vert2g = p1/max(p1)+p2/max(p2)*0.3;
aachs2g = [min(angle2g):5:max(angle2g)]; a_2g=[];
ahaufen2g = round(interp1(angle2g,vert2g*scal2g,aachs2g),0);
for kl2g =1:length(ahaufen2g)
    ueb2g = repmat(aachs2g(1,kl2g),1,ahaufen2g(1,kl2g));
    a_2g = [a_2g ueb2g];
end
figure; histogram(a_2g,'BinWidth',5);xlabel('angle between z-axes / °')
% figure; plot(angle,p1/max(p1)+p2/max(p2)*0.3)

 
%% Use model for OriSel calculation
for dk = 1:size(ALL17.axes.x,1)
%     ALL17.r(dk)=norm(ALL17.M(dk,:)-ALL24.M);
    [ALL17.o1(dk,:),ALL17.o2(dk,:),ALL17.rRu(dk,:)] = RuCoordv1(ALL17.M(dk,:)-ALL24.M, ALL17.axes.x(dk,:), ALL17.axes.y(dk,:), ALL17.axes.z(dk,:), ...
        ALL24.axes.x(1,:),ALL24.axes.y(1,:),ALL24.axes.z(1,:));
end

ALL17.rRu = ALL17.rRu/10;
haufig = round((p/max(p)*30),0);
model.EulerAngles.R1 = [];  model.EulerAngles.R2 = [];   model.Distance = [];

for kl=1:size(ALL17.axes.x,1)
   o1_temp = repmat(ALL17.o1(kl,:),haufig(kl),1);
   o2_temp = repmat(ALL17.o2(kl,:),haufig(kl),1);
   r_temp  = repmat(ALL17.rRu(kl,:),haufig(kl),1);
   
   model.EulerAngles.R1 = [model.EulerAngles.R1; o1_temp];
   model.EulerAngles.R2 = [model.EulerAngles.R2; o2_temp];
   model.Distance = [model.Distance; r_temp];
end

load('kinknoMg.mat')
figure; plotmitoffset(kinknoMg.Xband.redo.Sexp,kinknoMg.Xband.redo.time,0.15,'k');hold on

load('Z:\Members\Max\newCspin\data\ExpParX.mat')
Result_model=MainPELDORtime(EP,model,kinknoMg.Xband.redo.time);
[devn, model_sc] = ScaleModdev('single',kinknoMg.Xband.redo.Sexp,Result_model.Sexp);

plotmitoffset(model_sc,Result_model.time/1000,0.15,'r');
% plotmitoffset(Result_model.Sexp,Result_model.time/1000,0.15,'r');hold on


%%
function outpt = koordshairpin(N,C2,C4,C5)
% [M, zaxis1, angle, r,o1,o2,rRu,axes]
NC5   = C5-N;
NC2   = C2-N;

for ra=1:size(N,1)
    xaxis1(ra,:) = NC5(ra,:)/norm(NC5(ra,:));
    NC2(ra,:) = NC2(ra,:)/norm(NC2(ra,:));
    zaxis1(ra,:) = cross(xaxis1(ra,:),NC2(ra,:));
    zaxis1(ra,:) = zaxis1(ra,:)/norm(zaxis1(ra,:));
    yaxis1(ra,:) = cross(zaxis1(ra,:),xaxis1(ra,:));
end

% M = C5 + 0.5*(C4-C5) + xaxis1.*(sqrt(7^2-0.5*vecnorm((C4-C5)')'.^2)+sqrt(8.1^2-0.5*vecnorm((C4-C5)')'.^2))/2;
M = C5 + 0.5*(C4-C5) + xaxis1*(sqrt(7^2-0.75^2)+sqrt(8.2^2-0.75^2))/2;

if size(N,1) == 2
    outpt.r = norm(M(1,:)-M(2,:));
    outpt.angle = acosd(dot(zaxis1(1,:),zaxis1(2,:)));
%     [outpt.o1,outpt.o2,outpt.rRu]=RuCoordv1(M(1,:)-M(2,:),xaxis1(1,:),yaxis1(1,:),zaxis1(1,:),xaxis1(2,:),yaxis1(2,:),zaxis1(2,:));
    [outpt.o1,outpt.o2,outpt.rRu]=RuCoordv1(M(2,:)-M(1,:),xaxis1(2,:),yaxis1(2,:),zaxis1(2,:),xaxis1(1,:),yaxis1(1,:),zaxis1(1,:));
%     [o1,o2,rRu]=RuCoordv1(zaxis1(1,:),xaxis1(1,:),yaxis1(1,:),zaxis1(1,:),xaxis1(2,:),yaxis1(2,:),zaxis1(2,:));
else
    outpt.angle = [];
    outpt.o1 = [];
    outpt.o2 = [];
    outpt.rRu = [];
    outpt.r = [];
end

axes.x = xaxis1;
axes.y = yaxis1;
axes.z = zaxis1;
outpt.axes = axes;
outpt.M = M;
outpt.zaxis1 = zaxis1;

end

