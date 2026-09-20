#%%
%reset -f
import numpy as np
#import MDAnalysis
#from MDAnalysis.analysis import helix_analysis as hel
import matplotlib.pyplot as plt
import dnaMD
import fileinput as fi
from pylab import *

def rm_neun(vari):
    indizes = np.array([])
    for x in range(len(vari)):
        nmmr = np.where(vari[x] == 99.99)
        indizes = np.append(indizes,nmmr)

    indexes = np.sort(indizes)
    indexes = np.flip(indexes)
    indexes = indexes.astype(int)
    indexes = list(dict.fromkeys(indexes))
       
    for d in range(len(vari)):
        for y in range(len(indexes)):
            #print(indexes[y])
            vari[d] = np.delete(vari[d],indexes[y])
            
    return vari

def rm_neun_axis(vari,steprangen):
    indizes = np.array([])
    #for x in range(len(vari["bps"]["1"]["helical x-axis"])):
    #for x in range(1,19):
    for x in range(steprangen[0],steprangen[1]):
        nmmr = np.where(vari.data["bps"][str(x)]["helical x-axis"] == 99.99)
        #nmmr = np.where(vari["bps"][str(x)]["helical y-axis"] == 99.99)
        indizes = np.append(indizes,nmmr)

    
    #indizes = np.append(indizes,2001)
    indexes = np.sort(indizes)
    indexes = np.flip(indexes)
    indexes = indexes.astype(int)
    indexes = list(dict.fromkeys(indexes))
       
    #for d in range(1,19):
    for d in range(steprangen[0],steprangen[1]):
        for y in range(len(indexes)):
            #print(indexes[y])
            vari.data["bps"][str(d)]["helical x-axis"] = np.delete(vari.data["bps"][str(d)]["helical x-axis"],indexes[y])
            vari.data["bps"][str(d)]["helical y-axis"] = np.delete(vari.data["bps"][str(d)]["helical y-axis"],indexes[y])
            vari.data["bps"][str(d)]["helical z-axis"] = np.delete(vari.data["bps"][str(d)]["helical z-axis"],indexes[y])

    for y in range(len(indexes)):
        vari.time = np.delete(vari.time, indexes[y])
            
    return vari#, indexes

def rm_neun_axis_new(risevari,bendvari):
    indizes = np.array([])
    for x in range(len(risevari)):
        nmmr = np.where(risevari[x] == 99.99)
        indizes = np.append(indizes,nmmr)

    indexes = np.sort(indizes)
    indexes = np.flip(indexes)
    indexes = indexes.astype(int)
    indexes = list(dict.fromkeys(indexes))
       
    for y in range(len(indexes)):
        bendvari = np.delete(bendvari,indexes[y])
        #print(indexes[y])
            
    return bendvari

#%%
#folder = "/Users/max/Library/CloudStorage/OneDrive-Persönlich/dsRNA_Cspin/MD_SIM_me"
folder = "C:/Users/maxim/OneDrive/dsRNA_Cspin/MD_SIM_me"
Desodd = dnaMD.DNA(20) 
bscdna = dnaMD.DNA(20) 
steprangen = [1,19]
#steprangen = [7,10]

#Desodd.set_helical_axis(folder+'/OL3_odd_MHrun/HelAxis_oddMH.dat')
Desodd.set_helical_axis(folder+'/OL3_even_MHrun/HelAxis_evenMH.dat',step_range=True,step=steprangen)
Desodd = rm_neun_axis(Desodd,steprangen)
Desodd.generate_smooth_axis(smooth=500, spline=3, fill_point=6, cut_off_angle=180,step_range=True,step=steprangen);
#Desodd.write_haxis_pdb(filename='desresodd/axisDeodd.pdb',step_range=True,step = AngRangen, write_smooth_axis=True)

#bscdna.set_helical_axis(folder+'/PCA/DNA/HelAxis_dna_w.dat')
bscdna.set_helical_axis(folder+'/OL3_odd_MHrun/HelAxis_oddMH.dat',step_range=True,step=steprangen)
#bscdna.set_helical_axis(folder+'/OL3_wCm_1_12_tip3p/HelAxis_Cm12tip3p.dat',step_range=True,step=steprangen)
bscdna = rm_neun_axis(bscdna,steprangen)
bscdna.generate_smooth_axis(smooth=500, spline=3, fill_point=6, cut_off_angle=180,step_range=True,step=steprangen);

Desodd.calculate_curvature_tangent(store_tangent=True,step_range=True,step=steprangen)
bscdna.calculate_curvature_tangent(store_tangent=True,step_range=True,step=steprangen)


"""
Deodd=dnaMD.DNA(20)
#Deodd.set_base_step_parameters(folder+'/DESRESodd/L-BPH_tst.dat',parameters='all',bp_step=[1, 19],step_range=True,helical=True) 
#Deodd.set_base_step_parameters(folder+'/OL3_odd_MHrun/L-BPH_oddMH.dat',parameters='all',bp_step=[1, 19],step_range=True,helical=True) 
Deodd.set_base_step_parameters(folder+'/OL3_even_MHrun/L-BPH_oddMH.dat',parameters='all',bp_step=[1, 19],step_range=True,helical=True) 
rangen = [5,16]
Deoddrise, bp_idx = Deodd.get_parameters('h-rise',rangen,bp_range=True)

Desodd.calculate_curvature_tangent(store_tangent=True)
bscdna.calculate_curvature_tangent(store_tangent=True)

Deoddangle = Desodd.calculate_angle_bw_tangents([3,17])
#Deoddangle = Desodd.calculate_angle_bw_tangents([10,11])
Deoddangle = np.degrees(Deoddangle)

bscdnaangle = bscdna.calculate_angle_bw_tangents([3,17])
#bscdnaangle = bscdna.calculate_angle_bw_tangents([10,11])
bscdnaangle = np.degrees(bscdnaangle)
Deoddangle = rm_neun_axis_new(Deoddrise,Deoddangle)"""

#%%
AngRangen = [3,17]
#AngRangen = [4,16]
#AngRangen = [5,15]
#AngRangen = [6,14]
#AngRangen = [12,15]
#AngRangen = [7,10]


Deoddangle = Desodd.calculate_angle_bw_tangents(AngRangen)
Deoddangle = np.degrees(Deoddangle)

bscdnaangle = bscdna.calculate_angle_bw_tangents(AngRangen)
bscdnaangle = np.degrees(bscdnaangle)

bns = np.linspace(0,180,91)

relevantD = np.where(np.logical_not(np.isnan(bscdnaangle)) == True)[0]
print('DNA: ' + str(round(np.mean(bscdnaangle[relevantD]),0)) + u" \u00B1 " + str(round(np.std(bscdnaangle[relevantD]),0)))

relevantA = np.where(np.logical_not(np.isnan(Deoddangle)) == True)[0]
print('RNA: ' + str(round(np.mean(Deoddangle[relevantA]),0)) + u" \u00B1 " + str(round(np.std(Deoddangle[relevantA]),0)))


plt.figure(figsize=(8,8))
h = plt.hist(bscdnaangle,bins=bns,density= True)
plt.xlabel('Angle ($^o$)')
plt.plot([np.mean(bscdnaangle[relevantD]), np.mean(bscdnaangle[relevantD])], [0,440], "--");

h2=plt.hist(Deoddangle,bins=bns,density=True,alpha=0.5)
plt.xlabel('Angle ($^o$)')
plt.axis([-2,100,0,0.15])
#plt.xlim([-5, 205])
plt.plot([np.mean(Deoddangle[relevantA]), np.mean(Deoddangle[relevantA])], [0,440], "--");

#%%
#AngRangen = [3,17]
#AngRangen = [4,16]
#AngRangen = [5,15]
#AngRangen = [6,14]
#AngRangen = [12,15]
AngRangen = [7,10]


Deoddangle = Desodd.calculate_angle_bw_tangents(AngRangen)
Deoddangle = np.degrees(Deoddangle)

bscdnaangle = bscdna.calculate_angle_bw_tangents(AngRangen)
bscdnaangle = np.degrees(bscdnaangle)

bns = np.linspace(0,180,91)

relevantD = np.where(np.logical_not(np.isnan(bscdnaangle)) == True)[0]
print('DNA: ' + str(round(np.mean(bscdnaangle[relevantD]),0)) + u" \u00B1 " + str(round(np.std(bscdnaangle[relevantD]),0)))

relevantA = np.where(np.logical_not(np.isnan(Deoddangle)) == True)[0]
print('RNA: ' + str(round(np.mean(Deoddangle[relevantA]),0)) + u" \u00B1 " + str(round(np.std(Deoddangle[relevantA]),0)))


plt.figure(figsize=(12,8))
subplot(2,2,1)
#plt.title('Bending Angle DNA')
plt.plot(bscdna.time/1000, bscdnaangle)
plt.xlabel('Time (ns)');plt.ylabel('Angle ( $^o$)')
plt.axis([-5, 1000,0,80])

subplot(2,2,3)
h = plt.hist(bscdnaangle,bins=bns,density= True)
plt.xlabel('Angle ( $^o$)')
#plt.axis([-5,90,0,h[0].max()+0.1*h[0].max()])
plt.axis([-2,100,0,0.15])
#plt.xlim([-5, 205])

plt.plot([np.mean(bscdnaangle[relevantD]), np.mean(bscdnaangle[relevantD])], [0,440], "--");

subplot(2,2,2)
#plt.title('Bending Angle RNA')
plt.plot(Desodd.time[0:len(Deoddangle)]/1000, Deoddangle)
plt.xlabel('Time (ns)')
plt.axis([-5, 1000,0,80])

subplot(2,2,4)
h2=plt.hist(Deoddangle,bins=bns,density=True)
plt.xlabel('Angle ( $^o$)')
plt.axis([-2,100,0,0.15])
#plt.xlim([-5, 205])
plt.plot([np.mean(Deoddangle[relevantA]), np.mean(Deoddangle[relevantA])], [0,440], "--");
#plt.show()

#plt.savefig('bending_DNA_RNA.png',dpi=1200)
#plt.savefig('bending_cutoff.png',dpi=1200)

