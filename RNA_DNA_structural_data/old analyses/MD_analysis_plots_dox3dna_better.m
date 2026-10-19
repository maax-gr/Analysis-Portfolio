%%
clear;clc
load('MD_analysis_parameters_dox3dna.mat')
% range = 5:16; proplrange = 1:20;
% range = 4:16; proplrange = 1:20;
% range = 4:16; proplrange = 4:16;

% range  = 1:19; proplrange = 1:20;
% range = 1:4; proplrange = 1:5; %around SL 1
% range = 2:4; proplrange = 2:5; %around SL 1
% range  = 8:11;proplrange =8:12; %around SL 8
% range  = 5:7;proplrange =5:7; %between SL1 and SL8
range  = 12:15; proplrange = 12:16; %around SL 12
% range = 16;proplrange = 16;
% range  = 12:13; proplrange = 12:14; 
%range  = 6:9; proplrange = 6:10; %between SL1 and SL12
how = "histo";
% how = "correlation";
% how = "binned";
% how = "SLangle";

% nam1 = "evenMH"; nam2 = "evenLS"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('b');
% nam1 = "oddMH"; nam2 = "oddLS"; clr.(nam1) = getColors('y'); clr.(nam2) = getColors('b');
% nam1 = "evenMH"; nam2 = "oddMH"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('y');
% nam1 = "evenMH"; nam2 = "Cm_8"; clr.(nam1) = getColors('b'); clr.(nam2) = getColors('o'); 
nam1 = "evenMH"; nam2 = "Cm_12"; clr.(nam1) = getColors('b'); clr.(nam2) = getColors('r'); 
% nam1 = "Cm_12"; nam2 = "evenMH"; clr.(nam1) = getColors('o'); clr.(nam2) = getColors('m'); 
% nam2 = "evenMH"; nam1 = "Cm_12"; clr.(nam2) = getColors('m'); clr.(nam1) = getColors('o'); 
% nam1 = "evenMH"; nam2 = "Cm_14"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('g');
% nam1 = "evenMH"; nam2 = "Cm_15"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('r');
% nam1 = "oddMH"; nam2 = "Cm_15"; clr.(nam1) = getColors('y'); clr.(nam2) = getColors('r');
% nam1 = "Cm_12"; nam2 = "Cm_14"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('o'); num(1,1) = 12; num(1,2) = 14; whichSL = 2;
% nam1 = "Cm_8"; nam2 = "Cm_12"; clr.(nam1) = getColors('m'); clr.(nam2) = getColors('o'); num(1,1) = 8; num(1,2) = 12; whichSL = 2;

% nam1 = "Cm_12"; nam2 = "Cm_12"; clr.(nam1) = getColors('r'); clr.(nam2) = getColors('r'); num =12;whichSL = 2;

alph = 1;
figure
fig1=gcf;%figure(1);
fig1.Renderer='Painters';
for name = [nam1, nam2]
% for name = [nam1]
%     [rise.OL3.(name).rm_neun, yr] =        rm_neun(rise.OL3.(name).raw(range,:));        rise.OL3.(name).avg =        mean(rise.OL3.(name).rm_neun);
%     [twist.OL3.(name).rm_neun, yt] =       rm_neun(twist.OL3.(name).raw(range,:));       twist.OL3.(name).avg =       mean(twist.OL3.(name).rm_neun);
%     [inclination.OL3.(name).rm_neun, yi] = rm_neun(inclination.OL3.(name).raw(range,:)); inclination.OL3.(name).avg = mean(inclination.OL3.(name).rm_neun);
%     [radius.OL3.(name).rm_neun, yra] =     rm_neun(radius.OL3.(name).raw(range,:));      radius.OL3.(name).avg =      mean(radius.OL3.(name).rm_neun);
%     [propeller.OL3.(name).rm_neun, yp] =   rm_neun(propeller.OL3.(name).raw(proplrange,:));   propeller.OL3.(name).avg =   mean(propeller.OL3.(name).rm_neun);
    [rise.OL3.(name).rm_neun,twist.OL3.(name).rm_neun,inclination.OL3.(name).rm_neun,radius.OL3.(name).rm_neun, propeller.OL3.(name).rm_neun, yges.(name)] = rm_neun_multiple(rise.OL3.(name).raw(range,:),twist.OL3.(name).raw(range,:),inclination.OL3.(name).raw(range,:),radius.OL3.(name).raw(range,:),propeller.OL3.(name).raw(proplrange,:));
    rise.OL3.(name).avg = mean(rise.OL3.(name).rm_neun,1);  twist.OL3.(name).avg = mean(twist.OL3.(name).rm_neun,1);  inclination.OL3.(name).avg = mean(inclination.OL3.(name).rm_neun,1); radius.OL3.(name).avg = mean(radius.OL3.(name).rm_neun,1); propeller.OL3.(name).avg = mean(propeller.OL3.(name).rm_neun,1);  
end
dd = 1;

A.twist   = 32.7; A.rise   = 2.81; A.rad   = 8.31; A.prop   = -2.; A.inc   = 15.5;
Apr.twist = 30.0; Apr.rise = 3.00; Apr.rad = 8.86; Apr.prop = 2.3; Apr.inc = 10.55;

% Apr.twist = 30;
% Apr.rise  = 3;
% Apr.rad   = 8.86;
% Apr.prop  = 2.3;
% Apr.inc   = 10.55;

for name = [nam1, nam2]
% for name = [nam1]
    timeskip = 1; start = 1; 
%     cudof = 1896; 
    cudof = min([length(rise.OL3.(nam1).avg),length(twist.OL3.(nam1).avg),length(inclination.OL3.(nam1).avg),length(propeller.OL3.(nam1).avg),...
        length(rise.OL3.(nam2).avg),length(twist.OL3.(nam2).avg),length(inclination.OL3.(nam2).avg),length(propeller.OL3.(nam2).avg)]);
    cudofradius = length(radius.OL3.(name).avg);
%     cudof = 4000; 
% break
    
    if how=="histo"
        subplot(5,1,1)
        histogram(twist.OL3.(name).avg(1,start:timeskip:cudof),'Normalization','probability','BinWidth',0.25,'FaceColor',clr.(name),'EdgeAlpha',0.3);hold on; xlabel('twist / °'); 
        % plot([A.twist,A.twist],[0 0.3],'-','Color',getColors('y'),'LineWidth',5)
        % plot([Apr.twist,Apr.twist],[0 0.3],'-','Color',getColors('g'),'LineWidth',5)
        xlabel('helical twist / °')
        % xlim([27 36]); 
        xlim([24 37]);         %ylim([0 0.08])
        ylim([0 0.11])
        
        subplot(5,1,2)
        histogram(rise.OL3.(name).avg(1,start:timeskip:cudof),'Normalization','probability','BinWidth',0.05,'FaceColor',clr.(name),'EdgeAlpha',0.3);hold on; xlabel(sprintf('helical rise / %s',char(197))); 
        % plot([A.rise,A.rise],[0 0.3],'-','Color',getColors('y'),'LineWidth',5)
        % plot([Apr.rise,Apr.rise],[0 0.3],'-','Color',getColors('g'),'LineWidth',5)
        % xlim([2.15 3.65])
        xlim([2.15 3.85]);      %  ylim([0 0.09])
        ylim([0 0.14])
        
        subplot(5,1,3)
        histogram(inclination.OL3.(name).avg(1,start:timeskip:cudof),'Normalization','probability','BinWidth',1,'FaceColor',clr.(name),'EdgeAlpha',0.3);hold on; xlabel('inclination / °'); 
%         plot([A.inc,A.inc],[0 0.1],'-','Color',getColors('y'),'LineWidth',5)
%         plot([Apr.inc,Apr.inc],[0 0.1],'-','Color',getColors('g'),'LineWidth',5)
        % xlim([-2 22])
        xlim([-10 27]);        ylim([0 0.14])
        
        subplot(5,1,4)
        histogram(propeller.OL3.(name).avg(1,start:timeskip:cudof),'Normalization','probability','BinWidth',1,'FaceColor',clr.(name),'EdgeAlpha',0.3);hold on; xlabel('propeller / °'); 
        % plot([A.prop,A.prop],[0 0.3],'-','Color',getColors('y'),'LineWidth',5)
        % plot([Apr.prop,Apr.prop],[0 0.3],'-','Color',getColors('g'),'LineWidth',5)
        % xlim([-20, 0])
        xlim([-25, 12]);  %      ylim([0 0.1])
        ylim([0 0.17])
        
        subplot(5,1,5)
        histogram(radius.OL3.(name).avg(1,start:timeskip:cudofradius),'Normalization','probability','BinWidth',0.1,'FaceColor',clr.(name),'EdgeAlpha',0.3);hold on;xlabel(sprintf('radius / %s',char(197))); 
        % plot([A.rad,A.rad],[0 0.3],'-','Color',getColors('y'),'LineWidth',5)
        % plot([Apr.rad,Apr.rad],[0 0.3],'-','Color',getColors('g'),'LineWidth',5)
        % xlim([7.5,10.7])
        xlim([7,11.7]);        ylim([0 0.075])
        ylim([0 0.12])
    elseif how=="correlation"
        
        subplot(4,1,1)
        % plot(twist.OL3.(name).avg(1,start:timeskip:cudof),rise.OL3.(name).avg(1,start:timeskip:cudof),'x','Color',clr.(name));hold on
        scatter(twist.OL3.(name).avg(1,start:timeskip:cudof),rise.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        xlim([24 37]); ylim([2.15 3.85]); ylabel(sprintf('helical rise / %s',char(197))); xlabel('twist / °')
        % scatter(radius.OL3.(name).avg(1,start:timeskip:cudof),rise.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on

        subplot(4,1,2)
%         plot(twist.OL3.(name).avg(1,start:timeskip:cudof),propeller.OL3.(name).avg(1,start:timeskip:cudof),'x','Color',clr.(name));hold on
        scatter(twist.OL3.(name).avg(1,start:timeskip:cudof),inclination.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        xlim([24 37]);ylim([-10 27]); ylabel('inclination / °');  xlabel('twist / °')
        
%         subplot(4,1,2)
% %         plot(twist.OL3.(name).avg(1,start:timeskip:cudof),propeller.OL3.(name).avg(1,start:timeskip:cudof),'x','Color',clr.(name));hold on
%         scatter(rise.OL3.(name).avg(1,start:timeskip:cudof),inclination.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
%         xlim([2.15 3.85]);ylim([-10 27]); ylabel('inclination / °');  xlabel('rise')
  
% 
        subplot(4,1,3)
%         plot(twist.OL3.(name).avg(1,start:timeskip:cudof),propeller.OL3.(name).avg(1,start:timeskip:cudof),'x','Color',clr.(name));hold on
        scatter(twist.OL3.(name).avg(1,start:timeskip:cudof),propeller.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        xlim([24 37]);ylim([-25, 12]); ylabel('propeller / °');  xlabel('twist / °')
        
        subplot(4,1,4)
%         plot(twist.OL3.(name).avg(start:timeskip:cudof),radius.OL3.(name).avg(start:timeskip:cudof),'x','Color',clr.(name));hold on
        scatter(twist.OL3.(name).avg(start:timeskip:cudofradius),radius.OL3.(name).avg(start:timeskip:cudofradius),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        xlim([24 37]); ylim([7,11.7]); ylabel(sprintf('radius / %s',char(197))); xlabel('twist / °')
        alph = 0.8;

    elseif how=="binned"
%         timeskip = 1; start = 1; cudof = 4000; 
        twistbinned = [22:0.25:38];
        twist.OL3.(name).rounded = round(twist.OL3.(name).avg(1,start:timeskip:cudof)*4,0)/4;


        for dj = 1:length(twistbinned)
            Indi = find(twist.OL3.(name).rounded == twistbinned(dj));
            rise.OL3.(name).rounded_avg(dj) = mean(rise.OL3.(name).avg(Indi));
            propeller.OL3.(name).rounded_avg(dj) = mean(propeller.OL3.(name).avg(Indi));
            radius.OL3.(name).rounded_avg(dj) = mean(radius.OL3.(name).avg(Indi));
        end
    
%     Ypsigmarna.append(np.std(avg_Deoddrise[Indi])/2) #Ypsigma ist sigma/2
%     haufig.append(np.size(Indi))
        subplot(3,1,1)
        plot(twistbinned,rise.OL3.(name).rounded_avg,'o');hold on
        xlim([24 37]); ylim([2.15 3.85]); ylabel(sprintf('helical rise / %s',char(197))); title('MD w/o Cm')

        subplot(3,1,2)
        plot(twistbinned,propeller.OL3.(name).rounded_avg,'o');hold on
        xlim([24 37]);ylim([-25, 12]); ylabel('propeller / °');

        subplot(3,1,3)
        plot(twistbinned,radius.OL3.(name).rounded_avg,'o');hold on
        xlim([24 37]); ylim([7,11.7]); ylabel(sprintf('radius / %s',char(197))); xlabel('twist / °')

    elseif how=="SLangle"
        load(sprintf('SLangle_RNA1_%d.mat',num(1,dd)));dd = dd+1;
%         SLangle = SLangle(1:10000,:);
        for zl = 1:length(yges.(name))
            SLangle(yges.(name)(zl),:) = [];
%             SLangle(yges.(name)(zl),) = [];
        end
        
        twistfit = fitlm(SLangle(start:timeskip:cudof,whichSL), twist.OL3.(name).avg(1,start:timeskip:cudof),'linear');
        risefit = fitlm(SLangle(start:timeskip:cudof,whichSL), rise.OL3.(name).avg(1,start:timeskip:cudof),'linear');
        propfit = fitlm(SLangle(start:timeskip:cudof,whichSL), propeller.OL3.(name).avg(1,start:timeskip:cudof),'linear');
        radfit = fitlm(SLangle(start:timeskip:cudofradius,whichSL), radius.OL3.(name).avg(start:timeskip:cudofradius),'linear');

        subplot(4,1,1)
        scatter(SLangle(start:timeskip:cudof,whichSL), twist.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        plot([-50:0.1:50],twistfit.Coefficients.Estimate(1)+twistfit.Coefficients.Estimate(2)*[-50:0.1:50],'Color',clr.(name))
        text(-45,40-2*dd,sprintf('%.2f E-4',round(twistfit.Coefficients.Estimate(2),6)*10^4))
        xlim([-48 48]); ylim([24 37]); ylabel(sprintf('helical rise / %s',char(197))); title('MD w/o Cm')
        
              
        subplot(4,1,2)
        scatter(SLangle(start:timeskip:cudof,whichSL),rise.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        plot([-50:0.1:50],risefit.Coefficients.Estimate(1)+risefit.Coefficients.Estimate(2)*[-50:0.1:50],'Color',clr.(name))
        text(-45,4-0.2*dd,sprintf('%.2f E-4',round(risefit.Coefficients.Estimate(2),6)*10^4))
        xlim([-48 48]); ylim([2.15 3.85]); ylabel(sprintf('helical rise / %s',char(197))); title('MD w/o Cm')
         
        subplot(4,1,3)
        scatter(SLangle(start:timeskip:cudof,whichSL),propeller.OL3.(name).avg(1,start:timeskip:cudof),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        plot([-50:0.1:50],propfit.Coefficients.Estimate(1)+propfit.Coefficients.Estimate(2)*[-50:0.1:50],'Color',clr.(name))
        text(-45,16-4*dd,sprintf('%.2f E-4',round(propfit.Coefficients.Estimate(2),6)*10^4))
        xlim([-48 48]);ylim([-25, 12]); ylabel('propeller / °'); 
         
        subplot(4,1,4)
        scatter(SLangle(start:timeskip:cudofradius,whichSL),radius.OL3.(name).avg(start:timeskip:cudofradius),'MarkerFaceColor',clr.(name),'MarkerEdgeColor',clr.(name),'MarkerFaceAlpha',alph,'MarkerEdgeAlpha',alph,'Marker','x');hold on
        plot([-50:0.1:50],radfit.Coefficients.Estimate(1)+radfit.Coefficients.Estimate(2)*[-50:0.1:50],'Color',clr.(name))
        text(-45,12-0.5*dd,sprintf('%.2f E-4',round(radfit.Coefficients.Estimate(2),6)*10^4))
        xlim([-48 48]); ylim([7,11.7]); ylabel(sprintf('radius / %s',char(197))); xlabel('SLangle / °')
        alph = 0.8;

    end
end
% text(11,0.065,nam1)
% text(11,0.045,nam2)
% [nam1;nam2])
% saveas(gcf,sprintf('MD_vgl_%s_%s_range_%d_to_%d.png',nam1,nam2,range(1),range(end)))
% subplot(5,1,1);legend('OL3','OL3+Cm')


%% import and save
clear
load('MD_analysis_parameters_dox3dna.mat')
current = pwd; if current(10:14)=="maxim";    computer = "maxim"; else; computer = "Max";end
num = 13; ordner = sprintf("C:\\Users\\%s\\OneDrive\\dsRNA_Cspin\\MD_SIM_me\\OL3_wCm_1_%d_tip3p\\RNA%d_Cm",computer,num,num); name= sprintf('Cm_%d',num);
% ordner = sprintf("C:\\Users\\%s\\OneDrive\\dsRNA_Cspin\\MD_SIM_me\\moreStructures\\Ahel_realA\\Ahel_realA",computer); name= 'real_A';
% ordner = sprintf("C:\\Users\\%s\\OneDrive\\dsRNA_Cspin\\MD_SIM_me\\moreStructures\\Aprime\\Aprime",computer); name= 'Aprime';
% ordner = "C:\Users\Max\OneDrive\dsRNA_Cspin\MD_SIM_me\ol3_even_new\RNA_OL3"; name = "evenLS";
% ordner = "C:\Users\Max\OneDrive\dsRNA_Cspin\MD_SIM_me\ol3-odd-v2\RNA_OL3odd_LSrun"; name = "oddLS";
% ordner = "C:\Users\Max\OneDrive\dsRNA_Cspin\MD_SIM_me\OL3_odd_MHrun\RNA_oddMh"; name = "oddMH";
ordner = "C:\Users\Max\OneDrive\dsRNA_Cspin\MD_SIM_me\OL3_even_MHrun\RNA_evenMh"; name = "evenMH";
rise.OL3.(name).raw =        importdata(sprintf('%s_rise.txt',ordner));
twist.OL3.(name).raw =       importdata(sprintf('%s_twist.txt',ordner));
inclination.OL3.(name).raw = importdata(sprintf('%s_inclination.txt',ordner));
radius.OL3.(name).raw =      importdata(sprintf('%s_radius.txt',ordner));
propeller.OL3.(name).raw =   importdata(sprintf('%s_propeller.txt',ordner));

% save('MD_analysis_parameters_dox3dna.mat','rise','twist','inclination','radius',"propeller")

