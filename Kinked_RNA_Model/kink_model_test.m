figure;pltclr.plotdacoordscolor(N-N,C2-N,C4-N,C5-N,1,'ko')
pltclr.plotdacoordscolor(Nout-Nout,C2out-Nout,C4out-Nout,C5out-Nout,1,'mo')

%%
% theta = [0:2:58];
% theta = [0:-2:-56];
theta = linspace(0,-62,30);
% drehaxx = C5(1,:)-N(1,:);
drehaxx = C5out(1,:)-Nout(1,:);
drehaxx = drehaxx/norm(drehaxx);

psi = linspace(0,-4.5,30);
%psi = linspace(0,-9.3,30);
% psi = zeros(30,1);% 

% Naufnull = N(1,:)-N(1,:); C2aufnull = C2(1,:)-N(1,:); C4aufnull = C4(1,:)-N(1,:); C5aufnull = C5(1,:)-N(1,:);
Naufnull = Nout(1,:)-Nout(1,:); C2aufnull = C2out(1,:)-Nout(1,:); C4aufnull = C4out(1,:)-Nout(1,:); C5aufnull = C5out(1,:)-Nout(1,:);
% figure
for i=1:length(theta)
    Nturnwork(i,:)  = drehenRodrigues(Naufnull,drehaxx,theta(i));
    C2turnwork(i,:) = drehenRodrigues(C2aufnull,drehaxx,theta(i));
    C4turnwork(i,:) = drehenRodrigues(C4aufnull,drehaxx,theta(i));
    C5turnwork(i,:) = drehenRodrigues(C5aufnull,drehaxx,theta(i));
    
    C2Naxxw = C2turnwork(i,:)-Nturnwork(i,:); z=cross(drehaxx,C2Naxxw); z = z/norm(z);
    C2Naxx= cross(z,drehaxx);C2Naxx = C2Naxx/norm(C2Naxx);
    
%     Nturn(i,:)  = drehenRodrigues(Nturnwork(i,:),C2Naxx,psi(i));%+direction*(i-1)+N(1,:);
%     C2turn(i,:) = drehenRodrigues(C2turnwork(i,:),C2Naxx,psi(i));%+direction*(i-1)+N(1,:);
%     C4turn(i,:) = drehenRodrigues(C4turnwork(i,:),C2Naxx,psi(i));%+direction*(i-1)+N(1,:);
%     C5turn(i,:) = drehenRodrigues(C5turnwork(i,:),C2Naxx,psi(i));%+direction*(i-1)+N(1,:);
    
    Nturn(i,:)  = drehenRodrigues(Nturnwork(i,:),z,psi(i));
    C2turn(i,:) = drehenRodrigues(C2turnwork(i,:),z,psi(i));
    C4turn(i,:) = drehenRodrigues(C4turnwork(i,:),z,psi(i));
    C5turn(i,:) = drehenRodrigues(C5turnwork(i,:),z,psi(i));
%     drehaxx = C5turn(i,:)-Nturn(i,:);drehaxx = drehaxx/norm(drehaxx);

%    pltclr.plotdacoords(Nturn,C2turn,C4turn,C5turn,i)

end

pltclr.plotdacoordscolor(Nturn,C2turn,C4turn,C5turn,30,'bo')

%%
% eins = C5turn(30,:)-Nturn(30,:); zwei = C5(1,:)-N(1,:);
% eins = C4turn(30,:)-C2turn(30,:); zwei = C4(1,:)-C2(1,:);
eins = zaxis17(30,:) ;zwei = zaxis24;
% eins = zaxis_out(1,:) ;zwei = zaxis_out(2,:);
% eins = zaxis_in(1,:) ;zwei = zaxis_in(2,:);
acosd(dot(eins,zwei/(norm(eins)*norm(zwei))))

%%
figure;pltclr.plotdacoordscolor(N-N,C2-N,C4-N,C5-N,2,'ko')
pltclr.plotdacoordscolor(Nout-Nout,C2out-Nout,C4out-Nout,C5out-Nout,2,'mo')


