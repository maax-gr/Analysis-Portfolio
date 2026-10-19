function [vari, y] = rm_neun(vari)

[x,y] = find(vari == 99.99);
[x_neg,y_neg] = find(vari < -100);

y = [y;y_neg]; y =unique (y);
y = sort(y,'descend');
% y=flip(y);
%% y_neg=flip(y_neg);

for zl = 1:length(y)
    vari(:,y(zl)) = [];
end