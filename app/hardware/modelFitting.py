# import numpy as np
# import pandas as pd 
# import pickle5 as pickle
# import matplotlib.pyplot as plt
# from sklearn.model_selection import train_test_split
# from loess.loess_2d import loess_2d
# from sklearn.metrics import explained_variance_score
# import os,re,ast

# class ModelFitting():
#     def __init__(self,dataset=None,fitMethod=None,step=50,degree=2,frac=0.2,filename=None,workDir=os.getcwd(),socketInstance=None):
#         self.dataset=dataset 
#         self.fitMethod=fitMethod 
#         self.workDir=workDir 
#         self.filename=filename
#         self.step=step
#         self.degree=degree
#         self.frac=frac
#         self.socketInstance=socketInstance
#         pass

#     def threeSigmod(self,value):
#       avg = np.mean(value) 
#       std = np.std(value) 
#       threshold_up = avg + 3*std 
#       threshold_down = avg -3*std 
#       return [float(threshold_down),float(threshold_up)] 

#     def spliteData(self,filename):
#       data = pd.read_csv(filename)
#       freSet=list(set(data['Frequencies']))
#       X=[]
#       Y=[]
#       U=[]
#       V=[]
#       F=[]
#       for j in range(len(freSet)):
#         data1=data[data['Frequencies']==freSet[j]]
#         position=np.array([[0,0]])
#         displacement=np.array([[0,0]])
#         for index, row in data1.iterrows():
#           a=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Positions'])
#           position=np.vstack((position,np.array(ast.literal_eval(a))))
#           b=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Displacements'])
#           displacement=np.vstack((displacement, np.array(ast.literal_eval(b))))

#         x, y = position.T
#         u,v=displacement.T
#         f= np.full(len(x), freSet[j])
#         X=np.append(X,x)
#         Y=np.append(Y,y)
#         U=np.append(U,u)
#         V=np.append(V,v)
#         F=np.append(F,f)
#       expsData = {'frequency':F,'x': X, 'y': Y, 'u': U, 'v': V}
      
#       return pd.DataFrame({'frequency':F,'x': X, 'y': Y, 'u': U, 'v': V})

#     def preProcess(self,expsData):
#       data=expsData
#       frequencyList=list(set(data['frequency']))
#       x_min=min(data['x'])
#       x_max=max(data['x'])
#       y_min=min(data['y'])
#       y_max=max(data['y'])
#       data['x']=(data['x'].values-x_min)/(x_max-x_min)
#       data['y']=(data['y'].values-y_min)/(y_max-y_min)
#       threshold_v = self.threeSigmod(data['v'])
#       threshold_u = self.threeSigmod(data['u'])
#       data1=data.loc[(data['v']<=threshold_v[1]) &(data['v']>=threshold_v[0]) &(data['u']<=threshold_u[1]) &(data['u']>=threshold_u[0])]
#       return  frequencyList,data1

#     def dataFit(self,data,frequencyList,step,degree,frac):
#       U=[]
#       V=[]
#       Uscore=[]
#       Vscore=[]
#       x_ = np.linspace(0., 1., step)
#       y_ = np.linspace(0., 1., step)
#       _x, _y=np.meshgrid(x_, y_,indexing='ij')
#       for i in range(len(frequencyList)):
#         data1=data[data['frequency']==frequencyList[i]]
#         X=np.array([data1['x'],data1['y']]).T
#         Y=np.array([data1['u'],data1['v']]).T

#         XVars_train, XVars_test, Xresults_train, Xresults_test = train_test_split(X, Y, test_size=0.2, random_state=27)
#         u,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,0],xnew=_x.flatten(), ynew=_y.flatten(),degree=degree, frac=frac)
#         v,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,1],xnew=_x.flatten(), ynew=_y.flatten(),degree=degree, frac=frac)
#         pridectu,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,0],xnew=XVars_test[:,0], ynew=XVars_test[:,1],degree=degree, frac=frac)
#         pridectv,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,1],xnew=XVars_test[:,0], ynew=XVars_test[:,1],degree=degree, frac=frac)
#         su=explained_variance_score(Xresults_test[:,0], pridectu, multioutput = 'uniform_average')
#         sv=explained_variance_score(Xresults_test[:,1], pridectv, multioutput = 'uniform_average')
#         U.append(u)
#         V.append(u)
#         Uscore.append(su)
#         Vscore.append(sv)
#         self.socketInstance.emit('info','{:d} / {:d} ({:.0f}% done) \n".format(i+1, N, (i+1)*100/N)',namespace='/ModelFitting')
      
#       fittedModel={'frequency':frequencyList,'x':_x.flatten(),'y':_y.flatten(),'u':U,'v':V,'Uscore':Uscore,'Vscore':Vscore,}

#       return fittedModel


#     def plot(self,frequencyList,fittedModel):
      
#       for i in range(len(frequencyList)):
#         j=fittedModel['frequency'].index(frequencyList[i])
#         plt.figure(figsize=(20,20)) 
#         plt.title(frequencyList[i])
#         plt.quiver(fittedModel['x'],fittedModel['y'],fittedModel['u'][j],fittedModel['u'][j])
#         plt.show()

    
#     def fitmain(self):
#       spliteData=self.spliteData(self.filename)
#       frequencyList,data=self.preProcess(spliteData)
#       fittedModel= self.dataFit(data,frequencyList,self.step,self.degree,self.frac)
#       print(fittedModel['Vscore'])
#       print(fittedModel['Uscore'])
#       with open('./ModelFitting/trainedModel.pkl', 'wb') as f:
        # pickle.dump(fittedModel, f)
      

import numpy as np
import pandas as pd 
import pickle5 as pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from loess.loess_2d import loess_2d
from sklearn.metrics import explained_variance_score
import os,re,ast,traceback
class ModelFitting():
    def __init__(self,step=50,degree=2,frac=0.2,filename=None,workDir=os.getcwd(),socketInstance=None):
        self.workDir=workDir 
        self.filename=filename
        self.step=step
        self.degree=degree
        self.frac=frac
        self.socketInstance=socketInstance
        pass

    def threeSigmod(self,value):
      avg = np.mean(value) 
      std = np.std(value) 
      threshold_up = avg + 3*std 
      threshold_down = avg -3*std 
      return [float(threshold_down),float(threshold_up)] 

    def spliteData(self,filename):
      data = pd.read_csv(filename)
      freSet=list(set(data['Frequencies']))
      X=[]
      Y=[]
      U=[]
      V=[]
      F=[]
      for j in range(len(freSet)):
        data1=data[data['Frequencies']==freSet[j]]
        # print(data1['Positions'])
        position=np.array([[0,0]])
        displacement=np.array([[0,0]])
        for index, row in data1.iterrows():
          # print(index)
          a=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Positions'])
          position=np.vstack((position,np.array(ast.literal_eval(a))))
          b=re.sub(r"([^[\s])\s+([^]])", r"\1, \2", row['Displacements'])
          displacement=np.vstack((displacement, np.array(ast.literal_eval(b))))

        x, y = position.T
        u,v=displacement.T
        f= np.full(len(x), freSet[j])
        X=np.append(X,x)
        Y=np.append(Y,y)
        U=np.append(U,u)
        V=np.append(V,v)
        F=np.append(F,f)
      expsData = {'frequency':F,'x': X, 'y': Y, 'u': U, 'v': V}
      # expsData = pd.DataFrame(expsData)
      # expsData.to_csv('../DataCollecting/modelData.csv')
      return pd.DataFrame({'frequency':F,'x': X, 'y': Y, 'u': U, 'v': V})

    def preProcess(self,expsData):
      data=expsData
      frequencyList=list(set(data['frequency']))
      x_min=min(data['x'])
      x_max=max(data['x'])
      y_min=min(data['y'])
      y_max=max(data['y'])
      data['x']=(data['x'].values-x_min)/(x_max-x_min)
      data['y']=(data['y'].values-y_min)/(y_max-y_min)
      threshold_v = self.threeSigmod(data['v'])
      threshold_u = self.threeSigmod(data['u'])
      data1=data.loc[(data['v']<=threshold_v[1]) &(data['v']>=threshold_v[0]) &(data['u']<=threshold_u[1]) &(data['u']>=threshold_u[0])]
      return  frequencyList,data1

    def dataFit(self,data,frequencyList,step,degree,frac):
      U=[]
      V=[]
      Uscore=[]
      Vscore=[]
      x_ = np.linspace(0., 1., step)
      y_ = np.linspace(0., 1., step)
      _x, _y=np.meshgrid(x_, y_,indexing='ij')
      N=len(frequencyList)
      for i in range(N):
        data1=data[data['frequency']==frequencyList[i]]
        X=np.array([data1['x'],data1['y']]).T
        Y=np.array([data1['u'],data1['v']]).T
        try:
          XVars_train, XVars_test, Xresults_train, Xresults_test = train_test_split(X, Y, test_size=0.2, random_state=27)
          u,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,0],xnew=_x.flatten(), ynew=_y.flatten(),degree=degree, frac=frac)
          v,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,1],xnew=_x.flatten(), ynew=_y.flatten(),degree=degree, frac=frac)
          pridectu,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,0],xnew=XVars_test[:,0], ynew=XVars_test[:,1],degree=degree, frac=frac)
          pridectv,_ = loess_2d(XVars_train[:,0],XVars_train[:,1], Xresults_train[:,1],xnew=XVars_test[:,0], ynew=XVars_test[:,1],degree=degree, frac=frac)
          su=explained_variance_score(Xresults_test[:,0], pridectu, multioutput = 'uniform_average')
          sv=explained_variance_score(Xresults_test[:,1], pridectv, multioutput = 'uniform_average')
        except:
          raise Exception('error on loess')
        U.append(u)
        V.append(v)
        Uscore.append(su)
        Vscore.append(sv)
        print("{:d} / {:d} ({:.0f}% done) \n".format(i+1, N, (i+1)*100/N))
        self.socketInstance.sleep(0.1)
        self.socketInstance.emit('info','{:d} / {:d} ({:.0f}% done) \n'.format(i+1, N, (i+1)*100/N),namespace='/model')
      
      fittedModel={'frequency':frequencyList,'x':_x.flatten(),'y':_y.flatten(),'u':U,'v':V,'Uscore':Uscore,'Vscore':Vscore,}

      return fittedModel


    def plot(self,frequencyList,fittedModel):
      prefiximg = self.workDir + '\\' +'ModelFitting'+'\\'+' plots' + '\\'+ self.filename.replace('.csv','')+ '\\'
      ##check if the folder is already exsite
      os.makedirs(prefiximg)
      for i in range(len(frequencyList)):
        j=fittedModel['frequency'].index(frequencyList[i])
        plt.figure(figsize=(20,20),frameon=False) 
        plt.axis('off')
        plt.title(frequencyList[i])
        plt.xlim([0,1])
        plt.ylim([0,1])
        plt.quiver(fittedModel['x'],fittedModel['y'],fittedModel['u'][j],fittedModel['v'][j])
        plt.savefig('ModelFitting/plots/{}/quiverplot_{}.'.format(self.filename.replace('.csv',''),frequencyList[i]),bbox_inches='tight',transparent=True, pad_inches=0)
      

    
    def fitmain(self):
      self.socketInstance.emit('info','start fitting',namespace='/model')
      spliteData=self.spliteData(self.filename)
      frequencyList,data=self.preProcess(spliteData)
      try:
        fittedModel= self.dataFit(data,frequencyList,self.step,self.degree,self.frac)
      except BaseException:
        self.socketInstance.emit('error',traceback.format_exc(),namespace='/model')
        raise Exception(traceback.format_exc())
      
      # self.plot(frequencyList,fittedModel)
      with open('./ModelFitting/trainedModel_{}.pkl'.format(self.filename.replace('.csv','')), 'wb') as f:
        pickle.dump(fittedModel, f)
      self.socketInstance.emit('info','finish fitting',namespace='/model')