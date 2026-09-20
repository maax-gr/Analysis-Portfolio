%reset -f
import numpy as np
import fileinput as fi

#%% DNA File Zeiten umschreiben
#folder = "/Users/max/Library/CloudStorage/OneDrive-Persönlich/dsRNA_Cspin/MD_SIM_me"
folder = "C:/Users/maxim/OneDrive/dsRNA_Cspin/MD_SIM_me"

#dateenamee = folder+"/OL3_odd_MHrun/HelAxis_oddMH.dat"
dateenamee = folder+"/OL3_wCm_1_12_tip3p/HelAxis_Cm12tip3p.dat"
numb = "# Time ="#'99.99'
liste = np.array([])

with open(dateenamee) as myFile:
    for num, line in enumerate(myFile, 1):
        if numb in line:
            liste = np.append(liste,num)


with open(dateenamee, 'r') as file:
    data = file.readlines()

liste = liste.astype(int)
for x in liste:
    d = int(np.where(liste == x)[0])
    if d==0:
        data[x-1] = '# Time =         0.00000\n'
    elif d>0 and d<10:
        data[x-1] = '# Time =       '+str(d)+'00.00000\n'
        
    elif d>9 and d<100:
        data[x-1] = '# Time =      '+str(d)+'00.00000\n'
        
    elif d>99 and d<1000:
        data[x-1] = '# Time =     '+str(d)+'00.00000\n'
        
    elif d>999 and d<10000:
        data[x-1] = '# Time =    '+str(d)+'00.00000\n'
        
with open(dateenamee, 'w') as file:
    file.writelines( data )
    
#%%
# Careful! only use once to add a line of 99.99 to timesteps where a basepair is missing

#wat = "odd"
#ordner = "_marcel_sim/OL3_"+wat+"_MHrun/"
#dateenamee = ordner+"L-BP_"+wat+"MH.dat";what="BP"
#dateenamee = ordner+"L-BPH_"+wat+"MH.dat";what="BPstep"
#dateenamee = ordner+"HelixRad_"+wat+"MH.dat";what="BPstep"
#dateenamee = ordner+"MGroove_"+wat+"MH.dat"; what = "BPstep"

#folder = "/Users/max/Library/CloudStorage/OneDrive-Persönlich/dsRNA_Cspin/MD_SIM_me"
folder = "C:/Users/maxim/OneDrive/dsRNA_Cspin/MD_SIM_me"

dateenamee = folder+"/OL3_odd_MHrun/HelAxis_oddMH Kopie 2.dat"; what = "BPstep"

#dateenamee = folder+"/OL3_wCm_1_12_tip3p/HelAxis_Cm12tip3p.dat"; what = "BPstep"


if what =="BP":
    linesep = 21
elif what =="BPstep":
    linesep = 20  

numb = "# Time ="#'99.99'
liste = np.array([])

with open(dateenamee) as myFile:
    for num, line in enumerate(myFile, 1):
        if numb in line:
            liste = np.append(liste,num)

diffe = np.diff(liste)
#result = np.where(diffe == 20) #for base pair steps
result = np.where(diffe == linesep) #for base pairs
#result = np.where(diffe == 36)
result = result[0]

for x in result:
    if x==0:
        srch = '# Time =         0.00000'
        rplc = '# Time =         0.00000\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif x>0 and x<10:
        srch = '# Time =       '+str(x)+'00.00000'
        rplc = '# Time =       '+str(x)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif x>9 and x<100:
        srch = '# Time =      '+str(x)+'00.00000'
        rplc = '# Time =      '+str(x)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif x>99 and x<1000:
        srch = '# Time =     '+str(x)+'00.00000'
        rplc = '# Time =     '+str(x)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif x>999 and x<10000:
        srch = '# Time =    '+str(x)+'00.00000'
        rplc = '# Time =    '+str(x)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99'
    #print(x)
    with fi.FileInput(dateenamee, inplace=True) as File:
        for line in File:
            print(line.replace(srch, rplc),end='')
            
#result19 = np.where(diffe == 19) #for base pair steps
result19 = np.where(diffe == linesep-1) #for base pairs
#result19 = np.where(diffe == 35)
result19 = result19[0]
print('result done')

for y in result19:
    if y==0:
        srch = '# Time =         0.00000'
        rplc = '# Time =         0.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>0 and y<10:
        srch = '# Time =       '+str(y)+'00.00000'
        rplc = '# Time =       '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>9 and y<100:
        srch = '# Time =      '+str(y)+'00.00000'
        rplc = '# Time =      '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>99 and y<1000:
        srch = '# Time =     '+str(y)+'00.00000'
        rplc = '# Time =     '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>999 and y<10000:
        srch = '# Time =    '+str(y)+'00.00000'
        rplc = '# Time =    '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
        
    with fi.FileInput(dateenamee, inplace=True) as File:
        for line in File:
            print(line.replace(srch, rplc),end='')
            
#result18 = np.where(diffe == 18) #for base pair steps
result18 = np.where(diffe == linesep-2) #for base pairs
#result18 = np.where(diffe == 34)
result18 = result18[0]
print('result 19 done')

for y in result18:
    if y==0:
        srch = '# Time =         0.00000'
        rplc = '# Time =         0.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>0 and y<10:
        srch = '# Time =       '+str(y)+'00.00000'
        rplc = '# Time =       '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>9 and y<100:
        srch = '# Time =      '+str(y)+'00.00000'
        rplc = '# Time =      '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>99 and y<1000:
        srch = '# Time =     '+str(y)+'00.00000'
        rplc = '# Time =     '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>999 and y<10000:
        srch = '# Time =    '+str(y)+'00.00000'
        rplc = '# Time =    '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
        
    with fi.FileInput(dateenamee, inplace=True) as File:
        for line in File:
            print(line.replace(srch, rplc),end='')
            
result17 = np.where(diffe == linesep-3) #for base pairs
result17 = result17[0]
print('result 18 done')

for y in result17:
    if y==0:
        srch = '# Time =         0.00000'
        rplc = '# Time =         0.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>0 and y<10:
        srch = '# Time =       '+str(y)+'00.00000'
        rplc = '# Time =       '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>9 and y<100:
        srch = '# Time =      '+str(y)+'00.00000'
        rplc = '# Time =      '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>99 and y<1000:
        srch = '# Time =     '+str(y)+'00.00000'
        rplc = '# Time =     '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
    elif y>999 and y<10000:
        srch = '# Time =    '+str(y)+'00.00000'
        rplc = '# Time =    '+str(y)+'00.00000\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99\n99.99   99.99   99.99   99.99   99.99   99.99'
        
    with fi.FileInput(dateenamee, inplace=True) as File:
        for line in File:
            print(line.replace(srch, rplc),end='')
            
    print('result 17 done')