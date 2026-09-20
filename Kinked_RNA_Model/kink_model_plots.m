figure;plot((r)/10,p/max(p)*0.11);hold on
% plot(kinknoMg.Qband.distr(:,1),kinknoMg.Qband.distr(:,2)/max(kinknoMg.Qband.distr(:,2))*0.11);hold on

plot(kinknoMg.Xband.distr(:,1),kinknoMg.Xband.distr(:,2)/max(kinknoMg.Xband.distr(:,2))*0.11);hold on
histogram(OSP.Conformers.Distance,'BinWidth',0.05,'Normalization','probability')