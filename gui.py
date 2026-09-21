from pathlib import Path
import os, tkinter as tk
from tkinter import filedialog, messagebox
from module_manager import APP_DIR, ModuleManager

BG="#030914"; SIDE="#061321"; PANEL="#081b2d"; CARD="#0b2237"; CARD_H="#0e2b45"
LINE="#123d5e"; BLUE="#00aaff"; CYAN="#59d7ff"; TEXT="#f5f9fc"; MUTED="#88a6bc"
GOOD="#54dda5"; WARN="#ffc857"; BAD="#ff6b78"
RISK={"safe":("Bezpieczne",GOOD),"changes_system":("Zmienia system",WARN),
      "advanced":("Zaawansowane",WARN),"external_service":("Usługa zewnętrzna",CYAN)}
ICONS={"Komputer i Windows":"▣","Sieć i Internet":"⌁","Android i ADB":"▱",
       "Bezpieczeństwo":"◇","Pliki i dane":"▤","Kopie zapasowe":"◫",
       "Diagnostyka":"◎","Narzędzia zaawansowane":"⌘"}

class Scroll(tk.Frame):
    def __init__(self,p):
        super().__init__(p,bg=BG)
        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        self.body=tk.Frame(self.canvas,bg=BG)
        self.win=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        sb=tk.Scrollbar(self,command=self.canvas.yview)
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(self.win,width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self.canvas.bind_all("<MouseWheel>",lambda e:self.canvas.yview_scroll(int(-e.delta/120),"units"))

class Dashboard:
    def __init__(self,root):
        self.root=root; self.mm=ModuleManager()
        self.q=tk.StringVar(); self.cat=tk.StringVar(value="Wszystkie"); self.status=tk.StringVar(value="System gotowy")
        root.title("PRESTIGE TECH | Dashboard 1.1")
        root.geometry("1500x920"); root.minsize(1120,720); root.configure(bg=BG)
        self.make_sidebar()
        self.page=Scroll(root); self.page.pack(side="left",fill="both",expand=True)
        self.home()

    def make_sidebar(self):
        s=self.sidebar=tk.Frame(self.root,bg=SIDE,width=238)
        s.pack(side="left",fill="y"); s.pack_propagate(False)
        brand=tk.Frame(s,bg=SIDE); brand.pack(fill="x",padx=22,pady=(26,28))
        badge=tk.Frame(brand,bg="#08253b",highlightbackground=BLUE,highlightthickness=1,width=58,height=58)
        badge.pack(anchor="w"); badge.pack_propagate(False)
        tk.Label(badge,text="PT",bg="#08253b",fg=BLUE,font=("Segoe UI",22,"bold")).pack(expand=True)
        tk.Label(brand,text="PRESTIGE TECH",bg=SIDE,fg=TEXT,font=("Segoe UI",13,"bold")).pack(anchor="w",pady=(11,0))
        tk.Label(brand,text="WIĘCEJ NIŻ TECHNOLOGIA",bg=SIDE,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w")
        self.nav={}
        items=[("⌂","Strona główna"),("◈","Moduły"),("✓","Zainstalowane"),("↻","Aktualizacje"),
               ("⚙","Narzędzia systemowe"),("▤","Raporty"),("⚙","Ustawienia"),("?","Poradnik"),("i","O programie")]
        for icon,name in items:
            f=tk.Frame(s,bg=SIDE); f.pack(fill="x",padx=10,pady=1)
            b=tk.Button(f,text=f"{icon}   {name}",anchor="w",relief="flat",bd=0,bg=SIDE,fg=MUTED,
                        activebackground=PANEL,activeforeground=TEXT,padx=13,pady=10,font=("Segoe UI",10),
                        command=(lambda n=name:self.navigate(n)))
            b.pack(fill="x"); self.nav[name]=b
        bottom=tk.Frame(s,bg="#071a2a",padx=15,pady=12); bottom.pack(side="bottom",fill="x",padx=12,pady=14)
        tk.Label(bottom,text="●  Dashboard online",bg="#071a2a",fg=GOOD,font=("Segoe UI",9,"bold")).pack(anchor="w")
        tk.Label(bottom,text="Prestige Tech Dashboard 1.1",bg="#071a2a",fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(3,0))

    def navigate(self,name):
        for n,b in self.nav.items(): b.configure(bg=SIDE,fg=MUTED)
        self.nav[name].configure(bg=PANEL,fg=TEXT)
        if name=="Strona główna": self.home()
        elif name=="Moduły": self.modules_page()
        elif name=="Zainstalowane": self.modules_page(installed_only=True,title="Zainstalowane")
        else: self.placeholder(name)

    def clear(self):
        for x in self.page.body.winfo_children(): x.destroy()

    def button(self,p,text,cmd,primary=False):
        return tk.Button(p,text=text,command=cmd,relief="flat",bd=0,
                         bg=BLUE if primary else "#10314d",fg="#001522" if primary else TEXT,
                         activebackground=CYAN,activeforeground="#001522",padx=14,pady=8,font=("Segoe UI",9,"bold"),
                         cursor="hand2")

    def home(self):
        self.clear()
        for n,b in self.nav.items(): b.configure(bg=SIDE,fg=MUTED)
        self.nav["Strona główna"].configure(bg=PANEL,fg=TEXT)
        b=self.page.body

        hero=tk.Frame(b,bg=PANEL,highlightbackground=LINE,highlightthickness=1)
        hero.pack(fill="x",padx=28,pady=(28,16))
        left=tk.Frame(hero,bg=PANEL,padx=30,pady=26); left.pack(side="left",fill="both",expand=True)
        tk.Label(left,text="PRESTIGE TECH",bg=PANEL,fg=BLUE,font=("Segoe UI",30,"bold")).pack(anchor="w")
        tk.Label(left,text="WIĘCEJ NIŻ TECHNOLOGIA",bg=PANEL,fg=TEXT,font=("Segoe UI",16,"bold")).pack(anchor="w")
        tk.Label(left,text="TECH SOLUTIONS  •  PEOPLE IMPACT",bg=PANEL,fg=CYAN,font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(4,14))
        tk.Label(left,text="Twoje centrum diagnostyki i narzędzi serwisowych.\nInstaluj tylko to, czego potrzebujesz.",
                 bg=PANEL,fg=MUTED,justify="left",font=("Segoe UI",11)).pack(anchor="w")
        actions=tk.Frame(left,bg=PANEL); actions.pack(anchor="w",pady=(18,0))
        self.button(actions,"Przeglądaj moduły",self.modules_page,True).pack(side="left")
        self.button(actions,"Otwórz folder aplikacji",lambda:self.open(APP_DIR)).pack(side="left",padx=8)

        right=tk.Frame(hero,bg="#061625",width=300); right.pack(side="right",fill="y",padx=(0,1),pady=1); right.pack_propagate(False)
        tk.Label(right,text="STATUS SYSTEMU",bg="#061625",fg=MUTED,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=22,pady=(22,12))
        installed=sum(self.mm.is_installed(m) for m in self.mm.modules)
        for label,value,color in [("Dashboard","Gotowy",GOOD),("Moduły",f"{installed} / {len(self.mm.modules)}",BLUE),
                                  ("Kanał","Stable",CYAN),("Katalog","LocalAppData",MUTED)]:
            row=tk.Frame(right,bg="#061625"); row.pack(fill="x",padx=22,pady=5)
            tk.Label(row,text=label,bg="#061625",fg=MUTED,font=("Segoe UI",9)).pack(side="left")
            tk.Label(row,text=value,bg="#061625",fg=color,font=("Segoe UI",9,"bold")).pack(side="right")

        stats=tk.Frame(b,bg=BG); stats.pack(fill="x",padx=28,pady=(0,16))
        vals=[("24","MODUŁY","Wszystkie narzędzia"),(str(installed),"ZAINSTALOWANE","Gotowe do uruchomienia"),
              (str(len(self.mm.modules)-installed),"DOSTĘPNE","Możliwe do instalacji"),("SHA-256","WERYFIKACJA","Integralność modułów")]
        for i,(num,title,sub) in enumerate(vals):
            stats.columnconfigure(i,weight=1)
            c=tk.Frame(stats,bg=CARD,highlightbackground=LINE,highlightthickness=1,padx=18,pady=14)
            c.grid(row=0,column=i,sticky="nsew",padx=(0 if i==0 else 5,0))
            tk.Label(c,text=num,bg=CARD,fg=BLUE,font=("Segoe UI",18,"bold")).pack(anchor="w")
            tk.Label(c,text=title,bg=CARD,fg=TEXT,font=("Segoe UI",8,"bold")).pack(anchor="w")
            tk.Label(c,text=sub,bg=CARD,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(3,0))

        sec=tk.Frame(b,bg=BG); sec.pack(fill="x",padx=28,pady=(4,8))
        tk.Label(sec,text="Szybki start",bg=BG,fg=TEXT,font=("Segoe UI",18,"bold")).pack(side="left")
        tk.Label(sec,text="Najczęściej używane narzędzia",bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(side="left",padx=14,pady=(7,0))
        quick=tk.Frame(b,bg=BG); quick.pack(fill="x",padx=28)
        picks=["prestige-internet-diagnostic","prestige-system-snapshot","prestige-security-check"]
        for i,mid in enumerate(picks):
            m=next(x for x in self.mm.modules if x.id==mid); quick.columnconfigure(i,weight=1)
            self.card(quick,m,0,i,compact=True)

        tk.Label(b,text="Wszystkie kategorie",bg=BG,fg=TEXT,font=("Segoe UI",18,"bold")).pack(anchor="w",padx=28,pady=(24,10))
        cats=tk.Frame(b,bg=BG); cats.pack(fill="x",padx=28,pady=(0,28))
        categories=self.mm.categories()
        for i,cat in enumerate(categories):
            cats.columnconfigure(i%4,weight=1,uniform="cat")
            f=tk.Frame(cats,bg=CARD,highlightbackground=LINE,highlightthickness=1,padx=16,pady=13,cursor="hand2")
            f.grid(row=i//4,column=i%4,sticky="nsew",padx=4,pady=4)
            count=sum(1 for m in self.mm.modules if m.category==cat)
            tk.Label(f,text=ICONS.get(cat,"◈"),bg=CARD,fg=BLUE,font=("Segoe UI Symbol",20,"bold")).pack(anchor="w")
            tk.Label(f,text=cat,bg=CARD,fg=TEXT,font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(5,1))
            tk.Label(f,text=f"{count} modułów",bg=CARD,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w")
            for w in (f,*f.winfo_children()):
                w.bind("<Button-1>",lambda e,c=cat:self.modules_page(category=c))

    def modules_page(self,installed_only=False,title="Moduły",category=None):
        self.clear()
        for n,b in self.nav.items(): b.configure(bg=SIDE,fg=MUTED)
        active="Zainstalowane" if installed_only else "Moduły"; self.nav[active].configure(bg=PANEL,fg=TEXT)
        b=self.page.body
        head=tk.Frame(b,bg=BG); head.pack(fill="x",padx=28,pady=(28,14))
        tk.Label(head,text=title,bg=BG,fg=TEXT,font=("Segoe UI",24,"bold")).pack(anchor="w")
        tk.Label(head,text="Wybierz narzędzie. Dashboard instaluje moduły osobno, więc aplikacja pozostaje lekka.",
                 bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=(4,0))
        tools=tk.Frame(b,bg=BG); tools.pack(fill="x",padx=28,pady=(4,14))
        search=tk.Frame(tools,bg=CARD,highlightbackground=LINE,highlightthickness=1)
        search.pack(side="left",fill="x",expand=True)
        tk.Label(search,text="⌕",bg=CARD,fg=BLUE,font=("Segoe UI Symbol",16)).pack(side="left",padx=(12,6))
        e=tk.Entry(search,textvariable=self.q,bg=CARD,fg=TEXT,insertbackground=TEXT,relief="flat",bd=0,font=("Segoe UI",11))
        e.pack(side="left",fill="x",expand=True,ipady=10); e.bind("<KeyRelease>",lambda e:self.render_modules(installed_only))
        cats=["Wszystkie"]+self.mm.categories()
        if category: self.cat.set(category)
        om=tk.OptionMenu(tools,self.cat,*cats,command=lambda x:self.render_modules(installed_only))
        om.configure(bg=CARD,fg=TEXT,activebackground=CARD_H,activeforeground=TEXT,relief="flat",highlightthickness=0,padx=10)
        om["menu"].configure(bg=CARD,fg=TEXT); om.pack(side="left",padx=(10,0),ipady=4)
        row=tk.Frame(b,bg=BG); row.pack(fill="x",padx=28)
        self.module_count=tk.Label(row,bg=BG,fg=MUTED,font=("Segoe UI",9)); self.module_count.pack(side="right")
        self.cards=tk.Frame(b,bg=BG); self.cards.pack(fill="both",expand=True,padx=24,pady=(5,28))
        self.render_modules(installed_only)

    def render_modules(self,installed_only=False):
        for x in self.cards.winfo_children(): x.destroy()
        q=self.q.get().lower().strip(); cat=self.cat.get()
        items=[m for m in self.mm.modules if (cat=="Wszystkie" or m.category==cat) and
               (not q or q in (m.name+" "+m.description+" "+m.category).lower()) and
               (not installed_only or self.mm.is_installed(m))]
        self.module_count.config(text=f"{len(items)} modułów")
        for c in range(3): self.cards.columnconfigure(c,weight=1,uniform="c")
        for i,m in enumerate(items): self.card(self.cards,m,i//3,i%3)

    def card(self,parent,m,r,c,compact=False):
        f=tk.Frame(parent,bg=CARD,highlightbackground=LINE,highlightthickness=1,padx=18,pady=16)
        f.grid(row=r,column=c,sticky="nsew",padx=5,pady=5)
        top=tk.Frame(f,bg=CARD); top.pack(fill="x")
        tk.Label(top,text=ICONS.get(m.category,"◈"),bg=CARD,fg=BLUE,font=("Segoe UI Symbol",22,"bold")).pack(side="left")
        label,color=RISK.get(m.risk,("Informacja",MUTED))
        tk.Label(top,text="● "+label,bg=CARD,fg=color,font=("Segoe UI",8,"bold")).pack(side="right")
        tk.Label(f,text=m.name,bg=CARD,fg=TEXT,font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(10,2))
        tk.Label(f,text=m.category.upper(),bg=CARD,fg=CYAN,font=("Segoe UI",8,"bold")).pack(anchor="w")
        tk.Label(f,text=m.description,bg=CARD,fg=MUTED,justify="left",wraplength=320,font=("Segoe UI",9)).pack(anchor="w",pady=(9,10))
        installed=self.mm.is_installed(m)
        tk.Label(f,text=("● Zainstalowano" if installed else "○ Dostępny do instalacji")+f"   v{m.version}",
                 bg=CARD,fg=GOOD if installed else MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=(0,10))
        a=tk.Frame(f,bg=CARD); a.pack(fill="x")
        if installed:
            self.button(a,"Uruchom",lambda:self.run(m),True).pack(side="left")
            if not compact:self.button(a,"Usuń",lambda:self.uninstall(m)).pack(side="left",padx=6)
        else:self.button(a,"Zainstaluj",lambda:self.install(m),True).pack(side="left")
        self.button(a,"Jak użyć?",lambda:self.help(m)).pack(side="right")

    def install(self,m):
        roots=[Path.cwd(),Path.cwd().parent]
        p=self.mm.find_local(m,roots)
        if p and messagebox.askyesno("Znaleziono moduł",f"Znaleziono lokalny moduł:\n\n{p}\n\nZainstalować go w Prestige Tech?"):
            try:self.mm.install_file(m,p); self.status.set("Zainstalowano: "+m.name); self.modules_page()
            except Exception as e:messagebox.showerror("Błąd instalacji",str(e))
            return
        p=filedialog.askopenfilename(title="Wskaż "+m.executable,filetypes=[("Program Windows","*.exe")])
        if p:
            try:self.mm.install_file(m,p); self.modules_page()
            except Exception as e:messagebox.showerror("Błąd instalacji",str(e))

    def run(self,m):
        if m.risk=="changes_system" and not messagebox.askyesno("Potwierdzenie",m.name+" może zmieniać ustawienia systemu.\n\nUruchomić moduł?"):return
        try:self.mm.launch(m)
        except Exception as e:messagebox.showerror("Nie można uruchomić",str(e))

    def uninstall(self,m):
        if messagebox.askyesno("Odinstalowanie","Usunąć moduł "+m.name+" z Dashboardu?"):
            try:self.mm.uninstall(m); self.modules_page()
            except Exception as e:messagebox.showerror("Błąd",str(e))

    def help(self,m):
        req="\n".join("• "+x for x in m.requirements) or "• Brak dodatkowych wymagań"
        messagebox.showinfo("Jak użyć? | "+m.name,
            f"{m.name}\n\n{m.description}\n\nWymagania:\n{req}\n\n"
            "Krok po kroku:\n1. Kliknij Zainstaluj.\n2. Dashboard znajdzie lokalny moduł lub poprosi o wskazanie EXE.\n"
            "3. Po instalacji kliknij Uruchom.\n4. Przeczytaj komunikaty modułu przed zatwierdzeniem zmian.\n\n"
            "Jeśli coś nie działa, sprawdź wymagania powyżej.")

    def placeholder(self,name):
        self.clear(); b=self.page.body
        tk.Label(b,text=name,bg=BG,fg=TEXT,font=("Segoe UI",25,"bold")).pack(anchor="w",padx=30,pady=(35,8))
        tk.Label(b,text="Ta sekcja zostanie podłączona w następnym etapie Dashboardu 1.x.",
                 bg=BG,fg=MUTED,font=("Segoe UI",11)).pack(anchor="w",padx=30)

    @staticmethod
    def open(p):
        Path(p).mkdir(parents=True,exist_ok=True)
        if os.name=="nt":os.startfile(p)

def main():
    root=tk.Tk(); Dashboard(root); root.mainloop()
if __name__=="__main__":main()

