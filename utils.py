import numpy as np
import matplotlib.pyplot as plt
import csv

pixel_size_=5
repeat_=50*50
flag_value_=500
N_pix = 45
hole_size = 3 #必ず奇数

ticks=range(0,1100,100)
labels=[]
for i in range(-10,12,2):
    labels.append(i/10)

def Ps():
    return pixel_size_

def Repeat():
    return repeat_

def Fv():
    return flag_value_

def Image(pic,name):
    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.set(xlabel='X position', xticks=ticks, xticklabels=labels)
    ax1.set(ylabel='Y position', yticks=ticks, yticklabels=labels)
    ax1.imshow(pic.T, cmap='jet')
    fig.savefig(name+'.png')
    plt.close()
    return 0


def Visualize(input_name, posi_list, output_name, val):
    pic=np.load(input_name)
    for posi in posi_list:
        n=posi[2:]
        if(n[0]!=0 and n[1]!=0):
            pic[n[0]-pixel_size_:n[0]+pixel_size_,n[1]-pixel_size_:n[1]+pixel_size_]=np.ones([pixel_size_*2,pixel_size_*2])*val
    Image(pic,output_name)
    np.save(output_name,pic)
    return 0

def Nearest(ID, posi, rem,num):
    near=[]
    for i in range(num):
        dif=10000
        for IDxy in ID:
            idx=abs(IDxy[0]-posi[0])
            idy=abs(IDxy[1]-posi[1])
            dist=idx**2+idy**2
            if(dist<dif and IDxy not in rem and IDxy not in near):
                dif=dist
                near_id=IDxy
        near.append(near_id)
    return near

def Down(ID, pic, posi):
    pic_ext=pic[posi[0]-pixel_size_:posi[0]+pixel_size_,:]
    count=0
    for i in range(posi[1]-pixel_size_-1,0,-1):
        nn=[-1,-1]
        count+=1
        a=pic_ext[:,i]
        if(flag_value_ in a):
            nn=[posi[0],i-4]
            break
    if(nn==[-1,-1]):
        return nn, count
    return Nearest(ID, nn, [], 1)[0], count

def Up(ID, pic, posi):
    pic_ext=pic[posi[0]-pixel_size_:posi[0]+pixel_size_,:]
    count=0
    for i in range(posi[1]+pixel_size_,1000):
        nn=[-1,-1]
        count+=1
        a=pic_ext[:,i]
        if(flag_value_ in a):
            nn=[posi[0],i+5]
            break
    if(nn==[-1,-1]):
        return nn, count
    return Nearest(ID, nn, [], 1)[0], count

def Left(ID, pic, posi):
    pic_ext=pic[:,posi[1]-pixel_size_:posi[1]+pixel_size_]
    count=0
    for i in range(posi[0]-pixel_size_-1,0,-1):
        nn=[-1,-1]
        count+=1
        a=pic_ext[i,:]
        if(flag_value_ in a):
            nn=[i-4,posi[1]]
            break
    if(nn==[-1,-1]):
        return nn, count
    return Nearest(ID, nn, [], 1)[0], count

def Right(ID, pic, posi):
    pic_ext=pic[:,posi[1]-pixel_size_:posi[1]+pixel_size_]
    count=0
    for i in range(posi[0]+pixel_size_,1000):
        nn=[-1,-1]
        count+=1
        a=pic_ext[i,:]
        if(flag_value_ in a):
            nn=[i+5,posi[1]]
            break
    if(nn==[-1,-1]):
        return nn, count
    return Nearest(ID, nn, [], 1)[0], count

def Move(ID, pic, ml, l):
    X,Y,Xp,Yp=l
    if(ml=='r'):
        flag, count = Right(ID, pic, [Xp,Yp])
        X+=1
    elif(ml=='d'):
        flag, count = Down(ID, pic, [Xp,Yp])
        count = count/2.5
        Y-=1
    elif(ml=='u'):
        flag, count = Up(ID, pic, [Xp,Yp])
        count = count/2.5
        Y+=1
    elif(ml=='l'):
        flag, count = Left(ID, pic, [Xp,Yp])
        X-=1
        
    if(flag==[-1,-1]):
        #print('FLAG : ',[X,Y,Xp,Yp])
        return [X,Y,Xp,Yp,count]
    else:
        Xp,Yp = flag
    return [X,Y,Xp,Yp,count]

def Search(ID,direct):
    if(direct=='rc'):
        nn=Nearest(ID, [539,500], [], 1)[0]
        CUid=[(N_pix-1)/2 + (hole_size+1)/2,(N_pix-1)/2,nn[0],nn[1],0]
    elif(direct=='dc'):
        nn=Nearest(ID, [497,548], [], 1)[0]
        CUid=[(N_pix-1)/2,(N_pix-1)/2 + (hole_size+1)/2,nn[0],nn[1],0]
    elif(direct=='uc'):
        nn=Nearest(ID, [497,452], [], 1)[0]
        CUid=[(N_pix-1)/2,(N_pix-1)/2 - (hole_size+1)/2,nn[0],nn[1],0]
    elif(direct=='lc'):
        nn=Nearest(ID, [459,498], [], 1)[0]
        CUid=[(N_pix-1)/2 - (hole_size+1)/2,(N_pix-1)/2,nn[0],nn[1],0]
    return CUid

def Miss(posimap):
    posimap_miss=[]
    for i in posimap:
        for j in posimap:
            if((i[:4]!=j[:4] and i[:2]==j[:2]) or (i[:4]!=j[:4] and i[2:4]==j[2:4])):
                posimap_miss.append(i)

    for i in posimap:
        if((i[2]<200 or  800<i[2] or i[3]<100 or 900<i[3]) and (i[4]>10) and (i not in posimap_miss)):
            posimap_miss.append(i)
    return posimap_miss

def List_out(output):
    l_out=[]
    for i in range(len(output)):
        l_out.append(output[i][:2])
    for i in range(int((N_pix-1)/2 - (hole_size-1)/2),int((N_pix-1)/2 + (hole_size+1)/2)):
        for j in range(int((N_pix-1)/2 - (hole_size-1)/2),int((N_pix-1)/2 + (hole_size+1)/2)):
            l_out.append([i,j])
    return l_out

def Output(output, file_name):
    l_out=List_out(output)
    with open(file_name, 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(['IDx','IDy','Posix','Posiy','accuracy'])
        for i in range(int((N_pix-1)/2 - (hole_size-1)/2),int((N_pix-1)/2 + (hole_size+1)/2)):
            for j in range(int((N_pix-1)/2 - (hole_size-1)/2),int((N_pix-1)/2 + (hole_size+1)/2)):
                writer.writerow([i,j,0,0,'hole'])
        for xy in output:
            #writer.writerow(xy)
            writer.writerow([xy[0],xy[1],-1+xy[2]*2/1000,-1+xy[3]*2/1000])
        for i in range(45):
            for j in range(45):
                if([i,j] not in l_out):
                    writer.writerow([i,j,0,0,'miss'])
                #else:
                #    writer.writerow([i,j,-1+float(output[0][2])*2/1000,-1+float(output[0][3])*2/1000])
    f.close()
    return 0
