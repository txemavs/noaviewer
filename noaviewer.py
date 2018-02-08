#! /usr/bin/env python
# -*- coding: cp1252 -*-

import os,shutil,time,datetime,threading
import tkMessageBox,tkSimpleDialog,tkFileDialog
from Tkinter import *
from PIL import Image,ImageDraw,ImageOps,ImageTk

RAIZ = os.path.dirname(__file__)
ICON_SIZE=(120,90)
ORIENTATION={1:0,8:90,3:180,6:270}
FILETYPES=[("Fotos",".jpg .jpeg .jpe"),("Imágenes",IMG_FILTER),("Todos los archivos",".*")]
PIL_SUPPORTED=[".bmp",".dib",".dcx",".eps",".ps",".gif",".im",".jpg",".jpe",".jpeg",".pcd",".pcx",".png",".pbm",".pgm",".ppm",".psd",".tif",".tiff",".xbm",".xpm"]
IMG_FILTER=""
for ext in PIL_SUPPORTED: IMG_FILTER+=ext+" "
TXT=""

class Photo(object):
    '''One photo.'''
    exif=False
    loaded=False
    edited=False
    timestamp="00000000000000"
    __modified=False
    __icon_size=ICON_SIZE
    __icon_offset=(0,0)
    __preview_size=(0,0)
    
    def __str__(self):
        info=self.description+" "+self.name
        return info
            
    def __init__(self,filename):
        self.__text=[]
        self.filename=filename
        self.directory,name_ext=os.path.split(filename)
        self.name,self.ext=os.path.splitext(name_ext)
        stats=os.stat(filename)
        self.timestamp=datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y%m%d%H%M%S")
        self.bytes=stats.st_size
        self.original=self.__load()
        self.__get_info()
        self.__get_icon()
        self.original=None
        self.image=None
    
    def save(self,path):
        self.image.save(path+self.ext)
         
    def __load(self):
        try:
            image=Image.open(self.filename)
            self.loaded=True
        except:
            image=Image.new("RGB",self.__icon_size)
            draw = ImageDraw.Draw(image)
            draw.text((8,8), self.ext+"?", fill="red")
        
        self.mode=image.mode
        self.format=image.format
        self.width,self.height=image.size        
        return image
        
    def __load_image(self):
        if self.image is None: self.image=self.__load()

    def __get_info(self):
        error=""
        t=self.timestamp
        self.date=t[6:8]+"/"+t[4:6]+"/"+t[0:4]+" "+t[8:10]+":"+t[10:12]+":"+t[12:14]
        self.orientation=1
        self.make=""
        self.model="Image"
        if hasattr(self.original, '_getexif'):
            try:
                exifdata = self.original._getexif()
                d=exifdata[36867]
                self.date=d[8:10]+"/"+d[5:7]+"/"+d[0:4]+" "+d[11:19]
                self.timestamp=d[0:4]+d[5:7]+d[8:10]+d[11:13]+d[14:16]+d[17:19]
                
                self.orientation=exifdata[274]
                self.make=exifdata[271]
                self.model=exifdata[272]
                self.exif=True
            except:
                error= "*"
        self.__set_orientation()
        try:
            self.description=self.date+" "+self.model+" "+self.format+" "+self.__str_size()+" "+self.mode+" "+self.__str_orientation+" "+error
        except:
            self.description=self.__str_size()+""

    def __get_icon(self):
        icon=self.original
        icon.thumbnail(self.__icon_size,Image.ANTIALIAS)
        self.__icon=ImageTk.PhotoImage(icon)
        w,h=self.__icon_size
        pw,ph=icon.size
        self.__icon_offset=(int((w-pw)/2),int((h-ph)/2))

    def __str_size(self):
        return str(self.width)+"x"+str(self.height)
    
    def __set_orientation(self):
        if self.orientation==1:
            s=""
        else:
            self.original=self.original.rotate(ORIENTATION[self.orientation])
            if self.orientation==8: s="Gira derecha"    
            elif self.orientation==3: s="Boca abajo"
            elif self.orientation==6: s="Gira izquierda"
        self.__str_orientation=s
        return s

    def preview(self,w,h):
        if self.__preview_size==(w,h): pass
        else:
            if self.image is not None: self.view=self.image.copy()
            else: self.view=self.__load()
            if self.orientation !=1: self.view=self.view.rotate(ORIENTATION[self.orientation])
            self.view.thumbnail((w,h),Image.ANTIALIAS)
            self.__preview_size=(w,h)

        pw,ph=self.view.size
        ox,oy=int((w-pw)/2),int((h-ph)/2)
        return self.view,ox,oy

    def thumbnail(self):
        ox,oy=self.__icon_offset
        return self.__icon,ox,oy

    def __recalc(self):
        self.__preview_size=(0,0)
        if self.image is not None:
            self.width,self.height=self.image.size
    
    def rotate(self,degrees):
        self.__load_image()
        self.image=self.image.rotate(degrees)
        self.__recalc()

    def grayscale(self):
        self.__load_image()
        self.image=ImageOps.grayscale(self.image)
        self.__recalc()
        
    def autocontrast(self):
        self.__load_image()
        self.image=ImageOps.autocontrast(self.image)
        self.__recalc()

    def reload(self):
        self.image=None
        self.__recalc()
        
    def zoom(self,box):
        self.__load_image()
        pw,ph=self.view.size
        px,py=self.__preview_size
        ox,oy=int((px-pw)/2),int((py-ph)/2)
        tx,ty=self.width,self.height
        x1=int((box[0]-ox)*(float(tx)/pw))
        y1=int((box[1]-oy)*(float(ty)/ph))
        x2=int((box[2]-ox)*(float(tx)/pw))
        y2=int((box[3]-oy)*(float(ty)/ph))
        zoom=(x1,y1,x2,y2)
        self.image=self.image.crop(zoom)
        self.__recalc()
        
    def text(self,coords=None,text="",color="yellow"):
        self.__load_image()
        w,h=self.image.size
        if coords is None:
            coords=(w/2,h-16)
        draw = ImageDraw.Draw(self.image)
        draw.text(coords, text, fill=color)
        self.__recalc()
        




class App_Functions(object):
    bytes=0
    __last_dir="/"
    
    def copy_all(self,mode,dest,rename,pref,timestamp,dirdate,res,force,width,height):
        print "copy_all"+str((dest,rename,pref,dirdate))
        total=len(self.photos)
        n=0
        for photo in self.photos:
            n+=1
            try:
                print photo.filename
                if rename: 
                    if timestamp: filename=pref+photo.timestamp+photo.ext
                    else: filename=pref+str(n).zfill(4)+photo.ext
                else: filename=photo.name+photo.ext
                
                if dirdate:
                    d=photo.timestamp
                    destdate=os.path.join(dest,d[0:4],d[4:6])
                    if not os.path.isdir (destdate):
                        try: 
                            os.makedirs (destdate)
                        except:
                            print "Error dirdate"
                    destpath=os.path.join(destdate,filename)
                else: 
                    destpath=os.path.join(dest,filename)
                
                if mode==0:
                    shutil.copy(photo.filename,destpath)
                elif mode==1:
                    if res:
                        im=Image.open(photo.filename)
                        if force: 
                            im=im.resize((width,height),Image.ANTIALIAS)
                        else: im.thumbnail((width,height),Image.ANTIALIAS)
                        im.save(destpath)
    
                    else:
                        shutil.copy(photo.filename,destpath)
               
                self.status(str(int(n*100.0/total))+"% "+str(destpath))
                self.root.update()
            except:
                print "ERROR "+unicode(photo.filename)
                print sys.exc_info()[1]
            
    def save_all(self,win_save):
        dest=win_save.dest.get()
        pref=win_save.pref.get()
        mode=win_save.mode.get()        
        rename=win_save.rename.get()==1
        timestamp=win_save.timestamp.get()==1
        dirdate=win_save.dirdate.get()==1
        res=win_save.res.get()==1
        force=win_save.force.get()==1
        apply=win_save.apply.get()==1
        try:
            width=int(win_save.w.get())
            height=int(win_save.h.get())
        except:
            print "Resolucion!"
            width,height=0,0
            res=False
        print "SAVE ALL",str((dest,pref,mode,rename,dirdate,res,force,apply,width,height))

            
        if not os.path.isdir (dest):
             try: os.makedirs (dest)
             except:
                 tkMessageBox.showerror("Error", "No puedo crear "+dest)
                 return
 
        win_save.root.destroy()
        self.copy_all(mode,dest,rename,pref,timestamp,dirdate,res,force,width,height)
                
    def total_bytes(self):
        self.bytes=0
        for photo in self.photos:
            self.bytes+=photo.bytes

    def sort_date(self):
        p,d={},{}
        n=0
        for photo in self.photos:
            p[n]=photo
            d[n]=photo.timestamp
            n+=1

        selected=self.photos[self.n]
        self.photos=[]
        self.canvas.delete("icon")
        i=0
        for n,z in sorted(d.items(), lambda x, y: cmp(x[1], y[1])):            
            self.photos.append(p[n])
            self.icon_add(i)
            i+=1
        self.n=self.photos.index(selected)
          
    def remove_copies(self):
        a_name=""
        a_model=""
        a_timestamp="00000000000000"
        self.icon_select(0)
        for photo in self.photos:
            if photo.name==a_name and photo.model==a_model and photo.timestamp==a_timestamp:
                self.photos.remove(photo)
            a_name=photo.name
            a_model=photo.model
            a_timestamp=photo.timestamp

        self.canvas.delete("icon")
        for i in range(0,len(self.photos)): self.icon_add(i)
        self.icon_select(len(self.photos)-1)
          
    def status(self,text=None):
        if text is None: self.l_status.config(text=self.photos[self.n].filename)
        else: self.l_status.config(text=text)
        self.l_status2.config(text=str(self.bytes/1048567)+" Mb ("+str(self.n+1)+"/"+str(len(self.photos))+")")

    def load(self,filename,fast=False,exif=False,pref=""):
        self.status(pref+"Loading "+filename)
        self.root.update()
        photo=Photo(filename)
        if exif and not photo.exif: return
        #if photo is None: return
        self.photos.append(photo)
        last=len(self.photos)-1
        self.icon_add(last)
        self.n=last
        #self.photo_select(last,preview)
        #self.icon_visible(last,fast)
        self.total_bytes()
        if not fast: self.sort_date()
        self.icon_visible(self.n,fast)
        self.status("Loaded "+filename)
        
    def unload(self):
        if tkMessageBox.askyesno("Confirmar", "Desea cerrar "+self.photos[self.n].name+"?"):
            self.photos.remove(self.photos[self.n])
            self.canvas.delete("icon")
            for i in range(0,len(self.photos)):
                self.icon_add(i)
            self.sort_date()
            self.update()
            


    def save_filename(self):
        filename = tkFileDialog.asksaveasfilename(parent=self.root,initialdir=self.__last_dir,title="Salvar Imagen",filetypes=FILETYPES)
        self.photos[self.n].save(filename)

    def load_filename(self):
        files = tkFileDialog.askopenfilename(parent=self.root,initialdir=self.__last_dir,title="Abrir Imagen",multiple=True,filetypes=FILETYPES)
        if files:#len(files)>0:
            for filename in files: self.load(filename)
            self.__last_dir=os.path.dirname(filename)
        self.icon_select(self.n)
        
    def load_dir(self):
        directory = tkFileDialog.askdirectory(parent=self.root,initialdir=self.__last_dir,title="Abrir")
        if not directory: return
        self.__last_dir=directory
        for filename in os.listdir(directory):
            pri, ext=os.path.splitext(filename)
            if ext.lower() in PIL_SUPPORTED:
                self.load(os.path.join(directory,filename),True)
        self.icon_select(len(self.photos)-1)
        self.sort_date()

        
    def load_subdir(self):
        directory = tkFileDialog.askdirectory(parent=self.root,initialdir=self.__last_dir,title="Abrir")
        self.__last_dir=directory
        n=0
        total=0
        self.status("Buscando...")
        for root, dirs, files in os.walk(directory):
            total+=len(files)
            self.status(str(total)+" Archivos")
            self.root.update()
            
        for root, dirs, files in os.walk(directory):
            for filename in files:
                n+=1
                pref=str(int(n*100.0/total))+"% "
                pri, ext=os.path.splitext(filename)
                if ext.lower() in PIL_SUPPORTED:
                    try:
                        self.load(os.path.join(root,filename),True,True,pref)
                    except:
                        print "No "+filename
                        #print sys.exc_info()[1]
        self.icon_select(len(self.photos)-1)

    def about(self):
        tkMessageBox.showinfo("Acerca de..", "Organizador de fotos.\n\n2009 Txema Vicente")



class Preview(object):
    show_time=3000
    show_running=False
    
    def update(self):
        #self.icon_visible()
        self.icon_select()
        self.root.update()


    def preview(self):
        #self.root.config(cursor="wait")
        self.root.update()
        b=self.border   
        w,h=self.icon_size
        preview,ox,oy=self.photos[self.n].preview(self.vw-3*b-w,self.vh-2*b)      
        self.photo = ImageTk.PhotoImage(preview)
        self.canvas.delete("preview")
        self._p = self.canvas.create_image(w+2*b+ox,b+oy,image=self.photo, anchor=NW, tags="preview")
        #self.root.config(cursor="")
        
    def slideshow(self):
        self.show_running= not self.show_running
        if self.show_running: self.__slideshow()
        
    def __slideshow(self):
        if self.n>=len(self.photos)-1:
            self.show_running = False
            return
        if self.show_running:
            self.n_next()
            self.root.after(self.show_time,self.__slideshow)


    
class Icons_List(object):
    n=-1
    photos,_i,_t=[],[],[]
    offset=0
    footer=12
    border=7
    icon_size=ICON_SIZE

    def n_first(self): self.icon_select(0)
    def n_last(self): self.icon_select(len(self.photos)-1)
    def n_prev(self):
        if self.n>0: self.icon_select(self.n-1)        
    def n_next(self):
        if self.n<len(self.photos)-1: self.icon_select(self.n+1)



    def icon_visible(self,n=None,fast=False):
        if n is None: n=self.n
        b=self.border   
        w,h=self.icon_size
        d=h+b+self.footer
        y=((n+1)*d)
        max_y=self.vh-self.offset
        min_y=d-self.offset
        offset=0
        if y>max_y: offset=(max_y-y-b+2)
        elif y<min_y: offset=(min_y-y-2)
        if fast: self.icons_offset(offset)
        else:
            if offset>0:
                while not offset<2:
                    do=1+offset/32
                    offset-=do
                    self.icons_offset(do)
                    self.root.update()
            else:
                while not offset>-2:
                    do=-1+offset/32
                    offset-=do
                    self.icons_offset(do)
                    self.root.update()
            self.icons_offset(offset)
        self.root.update()

    def icon_select(self,n=None,preview=True):
        if n is None: n=self.n
        if n<0 or n>len(self.photos)-1: return
        self.root.title(self.photos[n])
        
        self.canvas.itemconfigure("rec_"+str(self.n),outline="black")
        self.canvas.itemconfigure("rec_"+str(n),outline="green")
        self.n=n
        self.status()
        self.icon_visible(n)
        if preview: self.preview()

    def icon_click(self,x,y):
        b=self.border   
        w,h=self.icon_size
        d=h+b+self.footer
        if x>b and x<b+w:
            y-=self.offset
            n=y/d
            self.icon_select(n)
            
    def icon_box(self,n):
        b=self.border   
        w,h=self.icon_size
        x=b
        y=b+n*(b+h+self.footer)+self.offset
        return x,y,w,h
        
    def icon_add(self,n):
        x,y,w,h=self.icon_box(n)
        thumbnail,ox,oy=self.photos[n].thumbnail()
        self.canvas.create_rectangle(x-2,y-2,x+w+1,y+h+self.footer+1,fill="white", outline="black", tags=("icon","ico_"+str(n),"rec_"+str(n)))
        self.canvas.create_image(x+ox,y+oy,image=thumbnail, anchor=NW, tags=("icon","ico_"+str(n)))
        text = self.canvas.create_text(x+w/2,y+h+self.footer-6, text=self.photos[n].name, tags=("icon","ico_"+str(n)))
        self._i.append(thumbnail)
        self._i.append(text)

    def icons_offset(self,dy):
        if self.offset+dy<0:
            self.offset+=dy
            self.canvas.move("icon",0,dy)



class Events(object):
    mouse_button_clicked={1:False,2:False,4:False}
    mouse_click=(-1,-1)
    mouse_move=None
    sel_box=(0,0,0,0)
    
    def event_info(self,event): print dir(event)


    
    def resize(self,event):
        self.vw=event.width
        self.vh=event.height
        
        self.canvas.config(width=event.width,height=event.height)
        self.m_status.config(width=event.width)
        self.update()
   

    def canvas_click_1(self,event):
        self.mouse_button_clicked[1]=True
        self.mouse_click=event.x,event.y

    def canvas_double_click_1(self,event):
        if (self.mouse_click[0]>self.border) and (self.mouse_click[0]<self.icon_size[0]+self.border):
            self.icon_click(event.x,event.y)
        else:
            self.canvas.delete("box")

    def canvas_release_1(self,event):
        self.mouse_button_clicked[1]=False
        self.mouse_move=None

        
    def canvas_move_1(self,event):
        if (self.mouse_click[0]>self.border) and (self.mouse_click[0]<self.icon_size[0]+self.border):
            if self.mouse_move is not None:
                self.icons_offset((event.y-self.mouse_move[1])*2)
            self.mouse_move=event.x,event.y
        else:
            self.canvas.delete("box")
            self.canvas.create_rectangle(self.mouse_click[0], self.mouse_click[1], event.x,event.y, tags="box",outline="red")
            self.sel_box=(self.mouse_click[0], self.mouse_click[1], event.x,event.y)
        

    def xcanvas_move_1(self,event):
        if self.mouse_move[0]>-1:
            self.icons_offset((event.y-self.mouse_move[1])*3)
        self.mouse_move=event.x,event.y




class Edit(object):

    def tra_none(self):
        self.photos[self.n].reload()
        self.icon_select(self.n)

    def tra_grayscale(self):
        self.photos[self.n].grayscale()
        self.icon_select(self.n)
    
    def tra_autocontrast(self):
        self.photos[self.n].autocontrast()
        self.icon_select(self.n)
    
    def tra_zoom(self):
        ox=-self.icon_size[0]-2*self.border
        oy=-self.border
        box=(self.sel_box[0]+ox,self.sel_box[1]+oy,self.sel_box[2]+ox,self.sel_box[3]+oy)
        self.photos[self.n].zoom(box)
        self.canvas.delete("box")
        self.icon_select(self.n)

    def tra_text(self):
        text=tkSimpleDialog.askstring("Texto", "Introduzca un texto:" ,initialvalue="")
        self.photos[self.n].text(text=text)
        self.icon_select(self.n)

    def rot_left(self):
        self.photos[self.n].rotate(90)
        self.icon_select(self.n)
    
    def rot_right(self):
        self.photos[self.n].rotate(270)
        self.icon_select(self.n)




class App(App_Functions,Events,Icons_List,Preview,Edit):
    __col_button=0

    def scroll(self,event,y,what=None): 
        if self.n==0: return
        print "CC",str(y),str(event)
        if event=="scroll":
            print str(y)
            if str(y)=="1": self.n_next()
            elif str(y)=="-1": self.n_prev()
            return
        elif event=="moveto":
            n=int(self.n*float(y))
            self.icon_select(n) 
            return
        t=((len(self.photos))*(self.icon_size[1]+self.border+self.footer))+self.border
        if t<self.vh:
            return
        u=-self.offset
        d=u+self.vh
        print str((t,u,d))
        self.scrollbar.set(float(u)/t,float(d)/t)

    def __init__(self):
        self.root = Tk()
        self.root.title("Fotos")
        self.root.geometry("800x500")
        self.__interface()
        self.__canvas()
        self.__menu()
        self.__toolbar()
        self.vw=self.canvas.cget("width")
        self.vh=self.canvas.cget("height")
        try:
            self.root.iconbitmap('nabla.ico')
        except: pass        
        self.root.mainloop()

    def __canvas(self):
        self.canvas=Canvas(self.f_canvas,bd=0, highlightthickness=0)
        self.canvas.grid(row=0,column=1,sticky=N+S+W+E)
        self.canvas.bind("<Button-1>",self.canvas_click_1)  
        self.canvas.bind("<Button-4>",self.n_prev)  
        self.canvas.bind("<Button-5>",self.n_next)
        self.canvas.bind("<MouseWheel>",self.event_info)
        

  
        self.canvas.bind("<Double-Button-1>",self.canvas_double_click_1)  
        self.canvas.bind("<ButtonRelease-1>",self.canvas_release_1)
        self.canvas.bind("<B1-Motion>",self.canvas_move_1)
        
    def __interface(self):
        self.f_toolbar = Frame(self.root,height=64,relief=GROOVE,bd=1)
        self.f_canvas = Frame(self.root)
        self.f_status = Frame(self.root)
        self.f_toolbar.grid(row=0,sticky=W+E)
        self.f_canvas.grid(row=1,sticky=N+S+W+E)
        self.f_status.grid(row=2,sticky=W+E)
        self.root.rowconfigure(1, weight=99)
        self.root.columnconfigure(0, weight=99)
        self.f_canvas.bind("<Configure>", self.resize)

        self.m_status = Frame(self.f_status,height=22,bd=1, relief=SUNKEN)
        self.m_status.grid_propagate(0)
        self.m_status.grid(sticky=E+S)

        self.l_status = Label(self.m_status,text="2009 Txema Vicente",anchor=W)
        self.l_status.grid(row=0,column=0,sticky=W)
        self.l_status2 = Label(self.m_status,text="OK",anchor=E)
        self.l_status2.grid(row=0,column=1,sticky=E)
        self.m_status.columnconfigure(1, weight=99)

        
    def _save_all(self):
        win=Win_Save_All(self)
        self.root.wait_window(win.root)
 
    def __menu(self):
        menubar = Menu(self.root)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Abrir", command=self.load_filename)
        filemenu.add_command(label="Buscar fotos", command=self.load_subdir)
        filemenu.add_command(label="Cargar carpeta", command=self.load_dir)
        filemenu.add_command(label="Guardar como...", command=self.save_filename)
        filemenu.add_command(label="Salvar todo...", command=self._save_all)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=filemenu)


        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Primera", command=self.n_first)
        viewmenu.add_command(label="Anterior", command=self.n_prev)
        viewmenu.add_command(label="Siguiente", command=self.n_next)
        viewmenu.add_command(label="Ultima", command=self.n_last)
        menubar.add_cascade(label="Ver", menu=viewmenu)

        toolmenu = Menu(menubar, tearoff=0)
        toolmenu.add_command(label="Quitar duplicadas", command=self.remove_copies)
        toolmenu.add_command(label="Añadir Texto", command=self.tra_text)
        toolmenu.add_command(label="Limitar Tamaño", command=hello,state="disabled")
        toolmenu.add_command(label="Enmarcar", command=hello,state="disabled")
        menubar.add_cascade(label="Herramientas", menu=toolmenu)

        transmenu = Menu(toolmenu, tearoff=0)
        transmenu.add_command(label="Girar Izquierda", command=self.rot_left)
        transmenu.add_command(label="Girar Derecha", command=self.rot_right)
        transmenu.add_command(label="Media Vuelta", command=hello,state="disabled")
        toolmenu.add_cascade(label="Transformar", menu=transmenu)

        filtermenu = Menu(toolmenu, tearoff=0)
        filtermenu.add_command(label="Auto Contraste", command=self.tra_autocontrast)
        filtermenu.add_command(label="Blanco y Negro", command=self.tra_grayscale)
        toolmenu.add_cascade(label="Filtros", menu=filtermenu)
        
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Acerca de...", command=self.about)
        menubar.add_cascade(label="Ayuda", menu=helpmenu)

        self.root.config(menu=menubar)


    def __add_button(self,text,command):
        b = Button(self.f_toolbar, width=11, height=3, text=text,command=command)
        b.grid(row=0,column=self.__col_button,sticky=E)
        self.__col_button+=1
        
    def __toolbar(self):
        self.__add_button("Abrir\nFoto",self.load_filename)
        self.__add_button("Quitar\nFoto",self.unload)
        self.__add_button("Buscar\nFotos",self.load_subdir)
        self.__add_button("Anterior",self.n_prev)
        self.__add_button("Siguiente",self.n_next)
        self.__add_button("Presentación",self.slideshow)        
        self.__add_button("Zoom",self.tra_zoom)
        self.__add_button("Original",self.tra_none)
        self.__add_button("Girar\nIzquierda",self.rot_left)
        self.__add_button("Girar\nDerecha",self.rot_right)
        f = Frame(self.f_toolbar)
        f.grid(row=0,column=self.__col_button,sticky=E)
        self.f_toolbar.columnconfigure(self.__col_button, weight=99)
        


class Win_Save_All(object):
    def __init__(self,parent):
        self.parent=parent
        self.root=Toplevel()
        self.root.title("Salvar")
        self.root.resizable(width=FALSE, height=FALSE)
        self.root.columnconfigure(0, weight=99)
        self.root.rowconfigure(1, weight=99)
        self.__interface()


    def __set_rename(self):        
        if self.rename.get()==1: state="normal"
        else: state="disabled"
        self.pref.config(state=state)
        self.chk_num.config(state=state)

    def __set_res(self,mode="normal"):        
        if self.res.get()==1: state="normal"
        else: state="disabled"
        if mode=="disabled": state="disabled"
        for w in self.tr+[self.w,self.h]:
            w.config(state=state)
        
    def __set_mode(self):        
        if self.mode.get()==1: state="normal"
        else: state="disabled"
        for w in [self.chk_res,self.chk_apply]:
            w.config(state=state)
        self.__set_res(state)
            
    def __sel_dest(self):                
        directory = tkFileDialog.askdirectory(parent=self.root,initialdir="/",title="Seleccionar carpeta")
        self.dest.delete(0, END)
        self.dest.insert(0, directory)
    
    def __interface(self):
        f1 = Frame(self.root,bd=8)
        f2 = Frame(self.root,bd=8)
        f3 = Frame(self.root,bd=8)
        f4 = Frame(self.root,bd=8)
        f1.grid(column=0,row=0,sticky=W+E)
        f2.grid(column=0,row=1,sticky=N+S+W+E)
        f3.grid(column=0,row=2,sticky=N+S+W+E)
        f4.grid(column=0,row=3,sticky=W+E)
        f1.columnconfigure(0, weight=99)
        f2.columnconfigure(0, weight=99)
        f3.columnconfigure(0, weight=99)
        f4.columnconfigure(0, weight=99)
        
        l = Label(f1,text="Carpeta de destino:",anchor=W)
        l.grid(row=0,column=0,sticky=W+E)
        self.dest = Entry(f1,width=40)
        self.dest.grid(row=1,column=0,sticky=W+E)
        b = Button(f1, width=10, text="Examinar...",command=self.__sel_dest)
        b.grid(row=10,column=0,sticky=E)
        
        self.rename = IntVar() 
        self.dirdate= IntVar()
        self.timestamp= IntVar()
        self.mode = IntVar()
        self.mode.set(0)
        self.res= IntVar()
        self.force= IntVar()
        self.apply= IntVar()
           
        c = Checkbutton(f2, text="Renombrar todos los archivos", variable=self.rename,command=self.__set_rename)
        c.grid(row=0,column=0,sticky=NW,columnspan=2)
        
        f = Frame(f2,bd=8)
        f.grid(row=1,column=0,sticky=W)
        self.pref = Entry(f2,width=26)
        self.pref.grid(row=1,column=1,sticky=W)
        self.chk_num = Checkbutton(f2, text="Usar fecha y hora en vez de numerar", variable=self.timestamp)
        self.chk_num.grid(row=2,column=1,sticky=NW)
        
        c = Checkbutton(f2, text="Organizar en subcarpetas por meses", variable=self.dirdate)
        c.grid(row=3,column=0,sticky=NW,columnspan=2)
        
        c = Radiobutton(f3, text="Conservar originales", variable=self.mode,value=0,command=self.__set_mode)
        c.grid(row=4,column=0,sticky=NW,columnspan=2)
        c = Radiobutton(f3, text="Transformar", variable=self.mode,value=1,command=self.__set_mode)
        c.grid(row=5,column=0,sticky=NW,columnspan=2)

        
        self.chk_res = Checkbutton(f3, text="Modificar resolucion", variable=self.res,command=self.__set_res)
        self.chk_res.grid(row=6,column=1,sticky=NW)
        
        fr = Frame(f3)
        fr.grid(row=7,column=1,sticky=W)
        
        tr0 = Label(fr,text="        ")
        tr0.grid(row=0,column=0)
        self.w = Entry(fr,width=5)
        self.w.grid(row=0,column=1,sticky=W)
        tr1 = Label(fr,text="x")
        tr1.grid(row=0,column=2)
        self.h = Entry(fr,width=5)
        self.h.grid(row=0,column=3,sticky=W)
        tr2 = Label(fr,text="pixels")
        tr2.grid(row=0,column=4)
        
        tr3 = Checkbutton(fr, text="Ajustar", variable=self.force)
        tr3.grid(row=0,column=5,sticky=NW)
        
        self.chk_apply = Checkbutton(f3, text="Aplicar cambios", variable=self.apply)
        self.chk_apply.grid(row=8,column=1,sticky=NW,columnspan=2)

        self.tr=[tr0,tr1,tr2,tr3]
        b = Button(f4, width=10, text="Aceptar",command=self.accept)
        b.grid(row=10,column=0,sticky=E)

        self.__set_rename()
        self.__set_mode()

    def accept(self):
        if self.dest.get()=="":
            tkMessageBox.showwarning("Error", "Especifique carpeta de destino")
            return 
        self.parent.save_all(self)


if __name__ == "__main__": app = App()
