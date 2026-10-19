function [vari1,vari2,vari3,vari4,vari5, yges] = rm_neun_multiple(vari1,vari2,vari3,vari4,vari5)

[~,y1] = find(vari1 == 99.99);
[~,y2] = find(vari2 == 99.99);
[~,y3] = find(vari3 == 99.99);
[~,y4] = find(vari4 == 99.99);
[~,y5] = find(vari5 == 99.99);
[~,y_neg1] = find(vari1 < -100);
[~,y_neg2] = find(vari2 < -100);
[~,y_neg3] = find(vari3 < -100);
[~,y_neg4] = find(vari4 < -100);
[~,y_neg5] = find(vari5 < -100);

yges = [y1;y_neg1;y2;y_neg2;y3;y_neg3;y4;y_neg4;y5;y_neg5]; yges =unique (yges);
yges = sort(yges,'descend');


for zl = 1:length(yges)
    vari1(:,yges(zl)) = [];
    vari2(:,yges(zl)) = [];
    vari3(:,yges(zl)) = [];
    vari4(:,yges(zl)) = [];
    vari5(:,yges(zl)) = [];
end