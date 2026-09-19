import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database import get_connection

try:
  import pandas as pd
  PANDAS_OK = True
except Exception:
  pd = None
  PANDAS_OK = False

try:
  from matplotlib.figure import Figure
  from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
  MATPLOTLIB_OK = True
except Exception:
  MATPLOTLIB_OK = False

BG = '#f4f6fa'
CARD = '#ffffff'
TEXT = '#182235'
MUTED = '#6b7280'
BLUE = '#2f6fed'
NAV = '#121b2e'

# ---------------- DATABASE HELPERS ----------------
def fetch_all(sql, params=()):
  con = get_connection()
  cur = con.cursor(dictionary=True)
  try:
    cur.execute(sql, params)
    return cur.fetchall()
  finally:
    cur.close(); con.close()

def execute(sql, params=()):
  con = get_connection(); cur = con.cursor()
  try:
    cur.execute(sql, params); con.commit()
    return cur.lastrowid, cur.rowcount
  except Exception:
    con.rollback(); raise
  finally:
    cur.close(); con.close()

def stats():
  return fetch_all("""SELECT
   (SELECT COUNT(*) FROM customers) customers,
   (SELECT COUNT(*) FROM restaurants) restaurants,
   (SELECT COUNT(*) FROM orders) orders,
   (SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status <> 'Cancelled') revenue,
   (SELECT COUNT(*) FROM deliveries) deliveries,
   (SELECT COALESCE(AVG(total_amount),0) FROM orders WHERE status <> 'Cancelled') avg_order""")[0]

def customers(q=''):
  sql = """SELECT customer_id,name,email,phone,DATE(date_joined) joined,
       CASE WHEN is_active=1 THEN 'Active' ELSE 'Inactive' END status
       FROM customers WHERE 1=1"""; p=[]
  if q:
    sql += " AND (name LIKE %s OR email LIKE %s OR phone LIKE %s)"; s=f'%{q}%'; p=[s,s,s]
  return fetch_all(sql+' ORDER BY customer_id DESC',p)

def customer(cid): return fetch_all('SELECT * FROM customers WHERE customer_id=%s',(cid,))[0]
def addresses(cid): return fetch_all('SELECT * FROM addresses WHERE customer_id=%s ORDER BY address_id',(cid,))
def restaurants(q=''):
  sql="""SELECT restaurant_id,name,phone,email,address_line,city,pincode,latitude,longitude,DATE(date_joined) joined,
       CASE WHEN is_active=1 THEN 'Active' ELSE 'Inactive' END status FROM restaurants WHERE 1=1""";p=[]
  if q:
    sql += " AND (name LIKE %s OR city LIKE %s OR phone LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY restaurant_id DESC',p)
def restaurant(rid): return fetch_all('SELECT * FROM restaurants WHERE restaurant_id=%s',(rid,))[0]
def menu(q=''):
  sql="""SELECT m.menu_item_id,m.restaurant_id,r.name restaurant,m.name item,m.description,m.category,m.price,
       CASE WHEN m.is_available=1 THEN 'Available' ELSE 'Unavailable' END status
       FROM menu_items m JOIN restaurants r ON r.restaurant_id=m.restaurant_id WHERE 1=1""";p=[]
  if q:
    sql += " AND (m.name LIKE %s OR m.category LIKE %s OR r.name LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY m.menu_item_id DESC',p)
def riders(q=''):
  sql="""SELECT rider_id,name,phone,vehicle_type,vehicle_number,DATE(date_joined) joined,
       CASE WHEN is_active=1 THEN 'Active' ELSE 'Inactive' END status FROM riders WHERE 1=1""";p=[]
  if q:
    sql += " AND (name LIKE %s OR phone LIKE %s OR vehicle_number LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY rider_id DESC',p)
def payments(q=''):
  sql="""SELECT payment_id,order_id,payment_method,amount,DATE_FORMAT(payment_time,'%Y-%m-%d %H:%i') payment_time,status,transaction_id
       FROM payments WHERE 1=1""";p=[]
  if q:
    sql += " AND (CAST(order_id AS CHAR) LIKE %s OR payment_method LIKE %s OR status LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY payment_id DESC',p)
def reviews(q=''):
  sql="""SELECT rv.review_id,rv.order_id,c.name customer,r.name restaurant,rv.rating,rv.comment,
       DATE_FORMAT(rv.review_time,'%Y-%m-%d %H:%i') review_time
       FROM reviews rv JOIN customers c ON c.customer_id=rv.customer_id JOIN restaurants r ON r.restaurant_id=rv.restaurant_id WHERE 1=1""";p=[]
  if q:
    sql += " AND (c.name LIKE %s OR r.name LIKE %s OR rv.comment LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY rv.review_id DESC',p)
def orders(q='',status='All'):
  sql="""SELECT o.order_id,c.name customer,r.name restaurant,DATE_FORMAT(o.order_time,'%Y-%m-%d %H:%i') order_time,o.status,o.total_amount
       FROM orders o JOIN customers c ON c.customer_id=o.customer_id JOIN restaurants r ON r.restaurant_id=o.restaurant_id WHERE 1=1""";p=[]
  if q:
    sql += " AND (CAST(o.order_id AS CHAR) LIKE %s OR c.name LIKE %s OR r.name LIKE %s)";s=f'%{q}%';p=[s,s,s]
  if status!='All':sql+=' AND o.status=%s';p.append(status)
  return fetch_all(sql+' ORDER BY o.order_id DESC',p)
def order_detail(oid):
  o=fetch_all("""SELECT o.*,c.name customer_name,r.name restaurant_name,a.address_line,a.city,a.pincode
         FROM orders o JOIN customers c ON c.customer_id=o.customer_id JOIN restaurants r ON r.restaurant_id=o.restaurant_id
         JOIN addresses a ON a.address_id=o.delivery_address_id WHERE o.order_id=%s""",(oid,))[0]
  o['items']=fetch_all("""SELECT oi.*,m.name item_name FROM order_items oi JOIN menu_items m ON m.menu_item_id=oi.menu_item_id WHERE oi.order_id=%s""",(oid,));return o
def deliveries(q=''):
  sql="""SELECT d.delivery_id,d.order_id,rd.name rider,d.status,d.distance_km,
       DATE_FORMAT(d.assigned_time,'%Y-%m-%d %H:%i') assigned_time,
       DATE_FORMAT(d.pickup_time,'%Y-%m-%d %H:%i') pickup_time,
       DATE_FORMAT(d.delivery_time,'%Y-%m-%d %H:%i') delivery_time
       FROM deliveries d JOIN riders rd ON rd.rider_id=d.rider_id WHERE 1=1""";p=[]
  if q:
    sql += " AND (CAST(d.delivery_id AS CHAR) LIKE %s OR CAST(d.order_id AS CHAR) LIKE %s OR rd.name LIKE %s)";s=f'%{q}%';p=[s,s,s]
  return fetch_all(sql+' ORDER BY d.delivery_id DESC',p)
def customer_choices(): return fetch_all('SELECT customer_id,name FROM customers WHERE is_active=1 ORDER BY name')
def restaurant_choices(): return fetch_all('SELECT restaurant_id,name FROM restaurants WHERE is_active=1 ORDER BY name')
def address_choices(cid): return fetch_all('SELECT address_id,label,address_line,city,pincode FROM addresses WHERE customer_id=%s',(cid,))
def menu_choices(rid): return fetch_all('SELECT menu_item_id,name,price FROM menu_items WHERE restaurant_id=%s AND is_available=1 ORDER BY name',(rid,))
def analytics(restaurant_id=None, status='All', date_from=None, date_to=None):
  conditions = []
  params = []

  if restaurant_id:
    conditions.append("o.restaurant_id = %s")
    params.append(restaurant_id)
  if status and status != 'All':
    conditions.append("o.status = %s")
    params.append(status)
  if date_from:
    conditions.append("DATE(o.order_time) >= %s")
    params.append(date_from)
  if date_to:
    conditions.append("DATE(o.order_time) <= %s")
    params.append(date_to)

  where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

  join_conditions = ["o.restaurant_id = r.restaurant_id"]
  join_params = []
  if restaurant_id:
    join_conditions.append("o.restaurant_id = %s")
    join_params.append(restaurant_id)
  if status and status != 'All':
    join_conditions.append("o.status = %s")
    join_params.append(status)
  if date_from:
    join_conditions.append("DATE(o.order_time) >= %s")
    join_params.append(date_from)
  if date_to:
    join_conditions.append("DATE(o.order_time) <= %s")
    join_params.append(date_to)
  order_join = " AND ".join(join_conditions)

  delivery_conditions = [
    "d.pickup_time IS NOT NULL",
    "d.delivery_time IS NOT NULL"
  ]
  delivery_params = []
  if restaurant_id:
    delivery_conditions.append("o.restaurant_id = %s")
    delivery_params.append(restaurant_id)
  if status and status != 'All':
    delivery_conditions.append("o.status = %s")
    delivery_params.append(status)
  if date_from:
    delivery_conditions.append("DATE(o.order_time) >= %s")
    delivery_params.append(date_from)
  if date_to:
    delivery_conditions.append("DATE(o.order_time) <= %s")
    delivery_params.append(date_to)
  delivery_where = " WHERE " + " AND ".join(delivery_conditions)

  review_conditions = []
  review_params = []
  if restaurant_id:
    review_conditions.append("rv.restaurant_id = %s")
    review_params.append(restaurant_id)
  if status and status != 'All':
    review_conditions.append("o.status = %s")
    review_params.append(status)
  if date_from:
    review_conditions.append("DATE(o.order_time) >= %s")
    review_params.append(date_from)
  if date_to:
    review_conditions.append("DATE(o.order_time) <= %s")
    review_params.append(date_to)
  review_where = (" WHERE " + " AND ".join(review_conditions)) if review_conditions else ""

  return {
    'summary': fetch_all("""
      SELECT
        COUNT(*) AS total_orders,
        COUNT(CASE WHEN o.status <> 'Cancelled' THEN o.order_id END) AS valid_orders,
        COALESCE(SUM(CASE WHEN o.status <> 'Cancelled' THEN o.total_amount ELSE 0 END), 0) AS revenue,
        COALESCE(AVG(CASE WHEN o.status <> 'Cancelled' THEN o.total_amount END), 0) AS avg_order,
        ROUND(100.0 * SUM(CASE WHEN o.status = 'Delivered' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0), 2) AS completion_rate,
        ROUND(100.0 * SUM(CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0), 2) AS cancellation_rate
      FROM orders o
    """ + where, tuple(params))[0],

    'counts': fetch_all("""
      SELECT
        (SELECT COUNT(*) FROM customers) AS customers,
        (SELECT COUNT(*) FROM restaurants) AS restaurants,
        (SELECT COUNT(*) FROM riders) AS riders,
        (SELECT COUNT(*) FROM menu_items) AS menu_items
    """)[0],

    'rating': fetch_all("""
      SELECT COALESCE(AVG(rv.rating), 0) AS avg_rating,
             COUNT(*) AS total_reviews
      FROM reviews rv
      JOIN orders o ON o.order_id = rv.order_id
    """ + review_where, tuple(review_params))[0],

    'delivery_metrics': fetch_all("""
      SELECT
        COALESCE(AVG(TIMESTAMPDIFF(MINUTE, o.order_time, d.pickup_time)), 0) AS avg_prep_time,
        COALESCE(AVG(TIMESTAMPDIFF(MINUTE, d.pickup_time, d.delivery_time)), 0) AS avg_travel_time,
        COALESCE(AVG(TIMESTAMPDIFF(MINUTE, o.order_time, d.delivery_time)), 0) AS avg_total_time,
        COALESCE(AVG(d.distance_km), 0) AS avg_distance
      FROM deliveries d
      JOIN orders o ON o.order_id = d.order_id
    """ + delivery_where, tuple(delivery_params))[0],

    'trend': fetch_all("""
      SELECT DATE(o.order_time) AS day,
             COUNT(*) AS orders,
             COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount ELSE 0 END), 0) AS revenue
      FROM orders o
    """ + where + """
      GROUP BY DATE(o.order_time)
      ORDER BY day
    """, tuple(params)),

    'revenue': fetch_all("""
      SELECT r.name AS restaurant,
             COUNT(CASE WHEN o.status <> 'Cancelled' THEN o.order_id END) AS orders,
             COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount ELSE 0 END), 0) AS revenue,
             COALESCE(AVG(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount END), 0) AS avg_order
      FROM restaurants r
      LEFT JOIN orders o ON """ + order_join + """
      GROUP BY r.restaurant_id, r.name
      ORDER BY revenue DESC
    """, tuple(join_params)),

    'restaurants': fetch_all("""
      SELECT r.name AS restaurant,
             COUNT(CASE WHEN o.status <> 'Cancelled' THEN o.order_id END) AS orders,
             COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount ELSE 0 END), 0) AS revenue,
             COALESCE(AVG(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount END), 0) AS avg_order
      FROM restaurants r
      LEFT JOIN orders o ON """ + order_join + """
      GROUP BY r.restaurant_id, r.name
      ORDER BY revenue DESC
    """, tuple(join_params)),

    'status': fetch_all("""
      SELECT o.status, COUNT(*) AS count
      FROM orders o
    """ + where + """
      GROUP BY o.status
      ORDER BY count DESC
    """, tuple(params)),

    'payments': fetch_all("""
      SELECT p.payment_method,
             COUNT(*) AS count,
             COALESCE(SUM(p.amount), 0) AS amount
      FROM payments p
      JOIN orders o ON o.order_id = p.order_id
    """ + where + """
      GROUP BY p.payment_method
      ORDER BY amount DESC
    """, tuple(params)),

    'ratings': fetch_all("""
      SELECT r.name AS restaurant,
             ROUND(AVG(rv.rating), 2) AS rating,
             COUNT(rv.review_id) AS reviews
      FROM restaurants r
      JOIN reviews rv ON rv.restaurant_id = r.restaurant_id
      JOIN orders o ON o.order_id = rv.order_id
    """ + review_where + """
      GROUP BY r.restaurant_id, r.name
      ORDER BY rating DESC
    """, tuple(review_params)),

    'delivery_scatter': fetch_all("""
      SELECT d.distance_km AS distance,
             TIMESTAMPDIFF(MINUTE, d.pickup_time, d.delivery_time) AS travel_time
      FROM deliveries d
      JOIN orders o ON o.order_id = d.order_id
    """ + delivery_where + """
      AND d.distance_km IS NOT NULL
    """, tuple(delivery_params)),

    'days': fetch_all("""
      SELECT DATE(o.order_time) AS day,
             COUNT(*) AS count,
             COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount ELSE 0 END), 0) AS revenue
      FROM orders o
    """ + where + """
      GROUP BY DATE(o.order_time)
      ORDER BY day
    """, tuple(params)),

    'monthly': fetch_all("""
      SELECT DATE_FORMAT(o.order_time, '%Y-%m') AS month,
             COUNT(*) AS orders,
             COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                               THEN o.total_amount ELSE 0 END), 0) AS revenue
      FROM orders o
    """ + where + """
      GROUP BY DATE_FORMAT(o.order_time, '%Y-%m')
      ORDER BY month
    """, tuple(params)),

    'menu_items': fetch_all("""
      SELECT m.name AS item,
             r.name AS restaurant,
             SUM(oi.quantity) AS quantity,
             COALESCE(SUM(oi.total_price), 0) AS revenue
      FROM order_items oi
      JOIN orders o ON o.order_id = oi.order_id
      JOIN menu_items m ON m.menu_item_id = oi.menu_item_id
      JOIN restaurants r ON r.restaurant_id = m.restaurant_id
    """ + where + """
      GROUP BY m.menu_item_id, m.name, r.name
      ORDER BY quantity DESC
      LIMIT 50
    """, tuple(params)),

    'customer_spending': fetch_all("""
      SELECT c.name AS customer,
             COUNT(o.order_id) AS orders,
             COALESCE(SUM(o.total_amount), 0) AS spending
      FROM customers c
      JOIN orders o ON o.customer_id = c.customer_id
    """ + (where if where else " WHERE 1=1") + """
      AND o.status <> 'Cancelled'
      GROUP BY c.customer_id, c.name
      ORDER BY spending DESC
      LIMIT 10
    """, tuple(params)),

    'rider_delivery': fetch_all("""
      SELECT rd.name AS rider,
             COUNT(d.delivery_id) AS deliveries,
             COALESCE(AVG(TIMESTAMPDIFF(MINUTE, d.pickup_time, d.delivery_time)), 0) AS avg_delivery_time,
             COALESCE(AVG(d.distance_km), 0) AS avg_distance
      FROM riders rd
      JOIN deliveries d ON d.rider_id = rd.rider_id
      JOIN orders o ON o.order_id = d.order_id
    """ + (where if where else " WHERE 1=1") + """
      AND d.pickup_time IS NOT NULL
      AND d.delivery_time IS NOT NULL
      GROUP BY rd.rider_id, rd.name
      ORDER BY deliveries DESC
    """, tuple(params))
  }



def setup_styles(root):
  root.configure(bg=BG); s=ttk.Style(root)
  try:s.theme_use('clam')
  except:pass
  s.configure('Page.TFrame',background=BG);s.configure('Card.TFrame',background=CARD)
  s.configure('Title.TLabel',background=BG,foreground=TEXT,font=('Segoe UI',23,'bold'));s.configure('Sub.TLabel',background=BG,foreground=MUTED,font=('Segoe UI',10))
  s.configure('CardTitle.TLabel',background=CARD,foreground=MUTED,font=('Segoe UI',10));s.configure('CardValue.TLabel',background=CARD,foreground=TEXT,font=('Segoe UI',19,'bold'))
  s.configure('Treeview',rowheight=34,font=('Segoe UI',10),background=CARD,fieldbackground=CARD,foreground=TEXT);s.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=8)
  s.map('Treeview',background=[('selected',BLUE)],foreground=[('selected','white')]);s.configure('TButton',padding=(11,7));s.configure('Accent.TButton',background=BLUE,foreground='white')

def page_header(p,title,sub):
  f=ttk.Frame(p,style='Page.TFrame');f.pack(fill='x',padx=30,pady=(25,16));ttk.Label(f,text=title,style='Title.TLabel').pack(anchor='w');ttk.Label(f,text=sub,style='Sub.TLabel').pack(anchor='w',pady=(3,0))
def make_tree(p,cols,heads,widths):
  f=ttk.Frame(p,style='Page.TFrame');t=ttk.Treeview(f,columns=cols,show='headings');vs=ttk.Scrollbar(f,orient='vertical',command=t.yview);hs=ttk.Scrollbar(f,orient='horizontal',command=t.xview);t.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
  for c,h,w in zip(cols,heads,widths):t.heading(c,text=h);t.column(c,width=w)
  t.grid(row=0,column=0,sticky='nsew');vs.grid(row=0,column=1,sticky='ns');hs.grid(row=1,column=0,sticky='ew');f.rowconfigure(0,weight=1);f.columnconfigure(0,weight=1);return f,t
def clear_tree(t):
  for x in t.get_children():t.delete(x)
def kpi(parent,title,value):
  f=ttk.Frame(parent,style='Card.TFrame',padding=16);ttk.Label(f,text=title,style='CardTitle.TLabel').pack(anchor='w');ttk.Label(f,text=value,style='CardValue.TLabel').pack(anchor='w',pady=(7,0));return f

def entry(parent,label,value=''):
  f=ttk.Frame(parent,style='Page.TFrame');f.pack(fill='x',padx=22,pady=6);ttk.Label(f,text=label).pack(anchor='w');e=ttk.Entry(f);e.pack(fill='x',pady=3);e.insert(0,str(value or ''));return e

def form_window(parent,title,w=520,h=500):
  x=tk.Toplevel(parent);x.title(title);x.geometry(f'{w}x{h}');x.transient(parent);x.grab_set();x.configure(bg=BG);return x

# ---------------- FORMS ----------------
def customer_form(parent,refresh,old=None):
  w=form_window(parent,'Edit Customer' if old else 'Add Customer');tk.Label(w,text='Customer Details',bg=BG,fg=TEXT,font=('Segoe UI',16,'bold')).pack(anchor='w',padx=22,pady=18)
  n=entry(w,'Name',old and old['name']);e=entry(w,'Email',old and old['email']);p=entry(w,'Phone',old and old['phone']);active=tk.BooleanVar(value=bool(old['is_active']) if old else True);ttk.Checkbutton(w,text='Active',variable=active).pack(anchor='w',padx=22)
  def save():
    try:
      if not n.get().strip():raise ValueError('Name is required.')
      if old:execute('UPDATE customers SET name=%s,email=%s,phone=%s,is_active=%s WHERE customer_id=%s',(n.get().strip(),e.get().strip() or None,p.get().strip() or None,int(active.get()),old['customer_id']))
      else:execute('INSERT INTO customers(name,email,phone,is_active) VALUES(%s,%s,%s,%s)',(n.get().strip(),e.get().strip() or None,p.get().strip() or None,int(active.get())))
      w.destroy();refresh()
    except Exception as ex:messagebox.showerror('Database / Validation',str(ex),parent=w)
  ttk.Button(w,text='Save',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=18);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=18)

def restaurant_form(parent,refresh,old=None):
  w=form_window(parent,'Edit Restaurant' if old else 'Add Restaurant',h=680);tk.Label(w,text='Restaurant Details',bg=BG,fg=TEXT,font=('Segoe UI',16,'bold')).pack(anchor='w',padx=22,pady=14)
  n=entry(w,'Name',old and old['name']);ph=entry(w,'Phone',old and old['phone']);em=entry(w,'Email',old and old['email']);ad=entry(w,'Address',old and old['address_line']);ci=entry(w,'City',old and old['city']);pi=entry(w,'Pincode',old and old['pincode']);la=entry(w,'Latitude',old and old['latitude']);lo=entry(w,'Longitude',old and old['longitude']);active=tk.BooleanVar(value=bool(old['is_active']) if old else True);ttk.Checkbutton(w,text='Active',variable=active).pack(anchor='w',padx=22)
  def save():
    try:
      if not n.get().strip() or not ad.get().strip() or not ci.get().strip():raise ValueError('Name, address and city are required.')
      v=(n.get().strip(),ph.get().strip() or None,em.get().strip() or None,ad.get().strip(),ci.get().strip(),pi.get().strip() or None,la.get().strip() or None,lo.get().strip() or None,int(active.get()))
      if old:execute('''UPDATE restaurants SET name=%s,phone=%s,email=%s,address_line=%s,city=%s,pincode=%s,latitude=%s,longitude=%s,is_active=%s WHERE restaurant_id=%s''',v+(old['restaurant_id'],))
      else:execute('''INSERT INTO restaurants(name,phone,email,address_line,city,pincode,latitude,longitude,is_active) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)''',v)
      w.destroy();refresh()
    except Exception as ex:messagebox.showerror('Database / Validation',str(ex),parent=w)
  ttk.Button(w,text='Save',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=15);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=15)

def menu_form(parent,refresh,old=None):
  w=form_window(parent,'Edit Menu Item' if old else 'Add Menu Item',h=560);tk.Label(w,text='Menu Item',bg=BG,fg=TEXT,font=('Segoe UI',16,'bold')).pack(anchor='w',padx=22,pady=14)
  rs=restaurant_choices();ttk.Label(w,text='Restaurant').pack(anchor='w',padx=22);cb=ttk.Combobox(w,values=[f"{r['restaurant_id']} — {r['name']}" for r in rs],state='readonly');cb.pack(fill='x',padx=22,pady=4)
  if old:
    for i,r in enumerate(rs):
      if r['restaurant_id']==old['restaurant_id']:cb.current(i);break
  n=entry(w,'Item Name',old and old['item']);d=entry(w,'Description',old and old['description']);c=entry(w,'Category',old and old['category']);pr=entry(w,'Price',old and old['price']);available=tk.BooleanVar(value=(not old or old['status']=='Available'));ttk.Checkbutton(w,text='Available',variable=available).pack(anchor='w',padx=22)
  def save():
    try:
      if cb.current()<0 or not n.get().strip():raise ValueError('Select restaurant and enter item name.')
      rid=rs[cb.current()]['restaurant_id'];v=(rid,n.get().strip(),d.get().strip() or None,c.get().strip() or None,float(pr.get()),int(available.get()))
      if old:execute('''UPDATE menu_items SET restaurant_id=%s,name=%s,description=%s,category=%s,price=%s,is_available=%s WHERE menu_item_id=%s''',v+(old['menu_item_id'],))
      else:execute('''INSERT INTO menu_items(restaurant_id,name,description,category,price,is_available) VALUES(%s,%s,%s,%s,%s,%s)''',v)
      w.destroy();refresh()
    except Exception as ex:messagebox.showerror('Database / Validation',str(ex),parent=w)
  ttk.Button(w,text='Save',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=16);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=16)

def order_form(parent,refresh):
  w=form_window(parent,'Create Order',620,650);tk.Label(w,text='New Order',bg=BG,fg=TEXT,font=('Segoe UI',16,'bold')).pack(anchor='w',padx=22,pady=14);cs=customer_choices();rs=restaurant_choices()
  def combo(label,values):
    ttk.Label(w,text=label).pack(anchor='w',padx=22);c=ttk.Combobox(w,values=values,state='readonly');c.pack(fill='x',padx=22,pady=4);return c
  cc=combo('Customer',[f"{x['customer_id']} — {x['name']}" for x in cs]);rc=combo('Restaurant',[f"{x['restaurant_id']} — {x['name']}" for x in rs]);ac=combo('Delivery Address',[]);mc=combo('Menu Item',[]);qty=entry(w,'Quantity','1');total=tk.StringVar(value='₹0.00');tk.Label(w,textvariable=total,bg=BG,fg=TEXT,font=('Segoe UI',14,'bold')).pack(anchor='w',padx=22,pady=8)
  def cust_changed(_=None):
    if cc.current()>=0:
      a=address_choices(cs[cc.current()]['customer_id']);ac['values']=[f"{x['address_id']} — {x['label'] or 'Address'} — {x['address_line']}, {x['city']}" for x in a];ac.current(0 if a else -1)
  def rest_changed(_=None):
    if rc.current()>=0:
      m=menu_choices(rs[rc.current()]['restaurant_id']);mc['values']=[f"{x['menu_item_id']} — {x['name']} — ₹{x['price']}" for x in m];mc.current(0 if m else -1);calc()
  def calc(_=None):
    try:
      if rc.current()>=0 and mc.current()>=0:
        m=menu_choices(rs[rc.current()]['restaurant_id']);total.set(f"₹{float(m[mc.current()]['price'])*int(qty.get()):,.2f}")
    except:pass
  cc.bind('<<ComboboxSelected>>',cust_changed);rc.bind('<<ComboboxSelected>>',rest_changed);mc.bind('<<ComboboxSelected>>',calc);qty.bind('<KeyRelease>',calc)
  def save():
    try:
      if min(cc.current(),rc.current(),ac.current(),mc.current())<0:raise ValueError('Select customer, restaurant, address and menu item.')
      q=int(qty.get());
      if q<=0:raise ValueError('Quantity must be positive.')
      cid=cs[cc.current()]['customer_id'];rid=rs[rc.current()]['restaurant_id'];a=address_choices(cid);m=menu_choices(rid);aid=a[ac.current()]['address_id'];mi=m[mc.current()]['menu_item_id'];price=float(m[mc.current()]['price']);amount=price*q
      oid,_=execute("INSERT INTO orders(customer_id,restaurant_id,delivery_address_id,status,total_amount) VALUES(%s,%s,%s,'Placed',%s)",(cid,rid,aid,amount));execute('INSERT INTO order_items(order_id,menu_item_id,quantity,unit_price,total_price) VALUES(%s,%s,%s,%s,%s)',(oid,mi,q,price,amount));w.destroy();refresh()
    except Exception as ex:messagebox.showerror('Could not create order',str(ex),parent=w)
  ttk.Button(w,text='Create Order',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=18);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=18)

# ---------------- PAGES ----------------
class TablePage(ttk.Frame):
  title='';subtitle='';cols=();heads=();widths=()
  def __init__(self,parent):
    super().__init__(parent,style='Page.TFrame');page_header(self,self.title,self.subtitle);bar=ttk.Frame(self,style='Page.TFrame');bar.pack(fill='x',padx=30,pady=(0,12));self.search=ttk.Entry(bar,width=34);self.search.pack(side='left',ipady=5);self.search.bind('<Return>',lambda e:self.load());ttk.Button(bar,text='Search',command=self.load).pack(side='left',padx=7);ttk.Button(bar,text='Refresh',command=self.load).pack(side='left');ttk.Button(bar,text='+ Add',style='Accent.TButton',command=self.add).pack(side='right');f,self.tree=make_tree(self,self.cols,self.heads,self.widths);f.pack(fill='both',expand=True,padx=30,pady=(0,10));b=ttk.Frame(self,style='Page.TFrame');b.pack(fill='x',padx=30,pady=(0,22));ttk.Button(b,text='View',command=self.view).pack(side='left');ttk.Button(b,text='Edit',command=self.edit).pack(side='left',padx=7);ttk.Button(b,text='Deactivate / Delete',command=self.delete).pack(side='left');self.load()
  def selected(self):
    s=self.tree.selection()
    if not s:messagebox.showinfo('Selection','Select a row first.');return None
    return self.tree.item(s[0],'values')
  def add(self):pass
  def edit(self):pass
  def view(self):pass
  def delete(self):pass

class CustomersPage(TablePage):
  title='Customers';subtitle='Live customer accounts and contact details';cols=('customer_id','name','email','phone','joined','status');heads=('ID','Name','Email','Phone','Joined','Status');widths=(70,190,220,130,110,100)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=tuple(r[c] for c in self.cols)) for r in customers(self.search.get().strip())]
  def add(self):customer_form(self,self.load)
  def edit(self):
    v=self.selected();
    if v:customer_form(self,self.load,customer(v[0]))
  def view(self):
    v=self.selected()
    if v:
      c=customer(v[0]);aa=addresses(v[0]);msg=f"ID: {c['customer_id']}\nName: {c['name']}\nEmail: {c['email'] or '-'}\nPhone: {c['phone'] or '-'}\nStatus: {'Active' if c['is_active'] else 'Inactive'}\n\nAddresses:"
      for a in aa:msg+=f"\n- {a['label'] or 'Address'} — {a['address_line']}, {a['city']} {a['pincode'] or ''}"
      messagebox.showinfo('Customer Details',msg)
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Deactivate','Set customer inactive?'):execute('UPDATE customers SET is_active=0 WHERE customer_id=%s',(v[0],));self.load()

class RestaurantsPage(TablePage):
  title='Restaurants';subtitle='Live restaurant partners, contacts and locations';cols=('restaurant_id','name','phone','email','city','joined','status');heads=('ID','Name','Phone','Email','City','Joined','Status');widths=(70,190,130,210,120,110,100)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=tuple(r[c] for c in self.cols)) for r in restaurants(self.search.get().strip())]
  def add(self):restaurant_form(self,self.load)
  def edit(self):
    v=self.selected();
    if v:restaurant_form(self,self.load,restaurant(v[0]))
  def view(self):
    v=self.selected()
    if v:
      r=restaurant(v[0]);items=fetch_all('SELECT COUNT(*) n FROM menu_items WHERE restaurant_id=%s',(v[0],))[0]['n'];messagebox.showinfo('Restaurant Details',f"{r['name']}\n{r['address_line']}, {r['city']} {r['pincode'] or ''}\nPhone: {r['phone'] or '-'}\nMenu items: {items}")
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Deactivate','Set restaurant inactive?'):execute('UPDATE restaurants SET is_active=0 WHERE restaurant_id=%s',(v[0],));self.load()

class MenuPage(TablePage):
  title='Menu';subtitle='Live menu items, categories, prices and availability';cols=('id','restaurant','item','category','price','status');heads=('ID','Restaurant','Item','Category','Price','Status');widths=(70,180,200,130,100,110)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=(r['menu_item_id'],r['restaurant'],r['item'],r['category'] or '-',f"₹{r['price']}",r['status'])) for r in menu(self.search.get().strip())]
  def add(self):menu_form(self,self.load)
  def edit(self):
    v=self.selected()
    if v:
      r=fetch_all("SELECT m.*,CASE WHEN is_available=1 THEN 'Available' ELSE 'Unavailable' END status FROM menu_items m WHERE menu_item_id=%s",(v[0],))[0];menu_form(self,self.load,r)
  def view(self):
    v=self.selected()
    if v:messagebox.showinfo('Menu Item',f"ID: {v[0]}\nRestaurant: {v[1]}\nItem: {v[2]}\nCategory: {v[3]}\nPrice: {v[4]}\nStatus: {v[5]}")
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Unavailable','Mark menu item unavailable?'):execute('UPDATE menu_items SET is_available=0 WHERE menu_item_id=%s',(v[0],));self.load()

class OrdersPage(ttk.Frame):
  def __init__(self,parent):
    super().__init__(parent,style='Page.TFrame');page_header(self,'Orders','Create, inspect, filter and cancel orders');bar=ttk.Frame(self,style='Page.TFrame');bar.pack(fill='x',padx=30,pady=(0,12));self.search=ttk.Entry(bar,width=32);self.search.pack(side='left',ipady=5);self.status=ttk.Combobox(bar,values=['All','Placed','Preparing','Ready','Picked Up','Delivered','Cancelled'],state='readonly',width=16);self.status.set('All');self.status.pack(side='left',padx=7);ttk.Button(bar,text='Filter',command=self.load).pack(side='left');ttk.Button(bar,text='Refresh',command=self.load).pack(side='left',padx=6);ttk.Button(bar,text='+ New Order',style='Accent.TButton',command=lambda:order_form(self,self.load)).pack(side='right');f,self.tree=make_tree(self,('id','customer','restaurant','time','status','amount'),('Order ID','Customer','Restaurant','Order Time','Status','Total'),(80,180,180,170,110,120));f.pack(fill='both',expand=True,padx=30,pady=(0,10));b=ttk.Frame(self,style='Page.TFrame');b.pack(fill='x',padx=30,pady=(0,22));ttk.Button(b,text='View Order',command=self.view).pack(side='left');ttk.Button(b,text='Cancel Order',command=self.cancel).pack(side='left',padx=7);self.load()
  def load(self):
    clear_tree(self.tree)
    for r in orders(self.search.get().strip(),self.status.get()):self.tree.insert('', 'end',values=(r['order_id'],r['customer'],r['restaurant'],r['order_time'],r['status'],f"₹{r['total_amount']:,.2f}"))
  def selected(self):
    s=self.tree.selection()
    if not s:messagebox.showinfo('Selection','Select an order first.');return None
    return self.tree.item(s[0],'values')
  def view(self):
    v=self.selected()
    if v:
      o=order_detail(v[0]);msg=f"Order #{o['order_id']}\nCustomer: {o['customer_name']}\nRestaurant: {o['restaurant_name']}\nStatus: {o['status']}\nTotal: ₹{o['total_amount']:,.2f}\nAddress: {o['address_line']}, {o['city']}\n\nItems:"
      for i in o['items']:msg+=f"\n- {i['item_name']} × {i['quantity']} = ₹{i['total_price']:,.2f}"
      messagebox.showinfo('Order Details',msg)
  def cancel(self):
    v=self.selected()
    if v and messagebox.askyesno('Cancel Order',f'Cancel order #{v[0]}?'):execute("UPDATE orders SET status='Cancelled' WHERE order_id=%s",(v[0],));self.load()

class DeliveriesPage(ttk.Frame):
  def __init__(self,parent):
    super().__init__(parent,style='Page.TFrame');page_header(self,'Deliveries','Rider assignments, distance and delivery timestamps');bar=ttk.Frame(self,style='Page.TFrame');bar.pack(fill='x',padx=30,pady=(0,12));self.search=ttk.Entry(bar,width=34);self.search.pack(side='left',ipady=5);ttk.Button(bar,text='Search',command=self.load).pack(side='left',padx=7);ttk.Button(bar,text='Refresh',command=self.load).pack(side='left');f,self.tree=make_tree(self,('id','order','rider','status','distance','assigned','pickup','delivery'),('Delivery ID','Order','Rider','Status','Distance km','Assigned','Pickup','Delivered'),(90,80,170,110,110,160,160,160));f.pack(fill='both',expand=True,padx=30,pady=(0,22));self.load()
  def load(self):
    clear_tree(self.tree)
    for r in deliveries(self.search.get().strip()):self.tree.insert('', 'end',values=(r['delivery_id'],r['order_id'],r['rider'],r['status'],r['distance_km'] or '-',r['assigned_time'] or '-',r['pickup_time'] or '-',r['delivery_time'] or '-'))

class RidersPage(TablePage):
  title='Riders';subtitle='Live rider and vehicle records';cols=('rider_id','name','phone','vehicle_type','vehicle_number','joined','status');heads=('ID','Name','Phone','Vehicle','Vehicle No.','Joined','Status');widths=(70,180,130,120,140,110,100)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=tuple(r[c] for c in self.cols)) for r in riders(self.search.get().strip())]
  def add(self):
    w=form_window(self,'Add Rider',500,400);n=entry(w,'Name');p=entry(w,'Phone');v=entry(w,'Vehicle Type');vn=entry(w,'Vehicle Number')
    def save():
      try:execute('INSERT INTO riders(name,phone,vehicle_type,vehicle_number) VALUES(%s,%s,%s,%s)',(n.get(),p.get() or None,v.get() or None,vn.get() or None));w.destroy();self.load()
      except Exception as e:messagebox.showerror('Database error',str(e),parent=w)
    ttk.Button(w,text='Save',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=18);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=18)
  def view(self):
    v=self.selected()
    if v:messagebox.showinfo('Rider','\n'.join(f'{h}: {x}' for h,x in zip(self.heads,v)))
  def edit(self):self.view()
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Deactivate','Set rider inactive?'):execute('UPDATE riders SET is_active=0 WHERE rider_id=%s',(v[0],));self.load()

class PaymentsPage(TablePage):
  title='Payments';subtitle='Payment transactions linked to orders';cols=('id','order_id','payment_method','amount','payment_time','status','transaction_id');heads=('ID','Order','Method','Amount','Time','Status','Transaction ID');widths=(70,80,130,110,160,100,200)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=(r['payment_id'],r['order_id'],r['payment_method'],f"₹{r['amount']}",r['payment_time'],r['status'],r['transaction_id'] or '-')) for r in payments(self.search.get().strip())]
  def add(self):
    w=form_window(self,'Add Payment',520,520);o=entry(w,'Order ID');m=entry(w,'Payment Method');a=entry(w,'Amount');s=entry(w,'Status','Paid');tx=entry(w,'Transaction ID')
    def save():
      try:execute('INSERT INTO payments(order_id,payment_method,amount,status,transaction_id) VALUES(%s,%s,%s,%s,%s)',(int(o.get()),m.get(),float(a.get()),s.get(),tx.get() or None));w.destroy();self.load()
      except Exception as e:messagebox.showerror('Database error',str(e),parent=w)
    ttk.Button(w,text='Save',style='Accent.TButton',command=save).pack(side='right',padx=22,pady=18);ttk.Button(w,text='Cancel',command=w.destroy).pack(side='right',pady=18)
  def view(self):
    v=self.selected()
    if v:messagebox.showinfo('Payment','\n'.join(f'{h}: {x}' for h,x in zip(self.heads,v)))
  def edit(self):self.view()
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Delete','Delete payment record?'):execute('DELETE FROM payments WHERE payment_id=%s',(v[0],));self.load()

class ReviewsPage(TablePage):
  title='Reviews';subtitle='Customer feedback and restaurant ratings';cols=('id','order_id','customer','restaurant','rating','comment','review_time');heads=('ID','Order','Customer','Restaurant','Rating','Comment','Time');widths=(60,80,160,170,80,300,150)
  def load(self):clear_tree(self.tree);[self.tree.insert('', 'end',values=(r['review_id'],r['order_id'],r['customer'],r['restaurant'],f"{r['rating']}/5",r['comment'] or '-',r['review_time'])) for r in reviews(self.search.get().strip())]
  def add(self):messagebox.showinfo('Reviews','Reviews can be created from completed orders; rating validation is 1–5.')
  def view(self):
    v=self.selected()
    if v:messagebox.showinfo('Review','\n'.join(f'{h}: {x}' for h,x in zip(self.heads,v)))
  def edit(self):self.view()
  def delete(self):
    v=self.selected()
    if v and messagebox.askyesno('Delete','Delete review?'):execute('DELETE FROM reviews WHERE review_id=%s',(v[0],));self.load()

class DashboardPage(ttk.Frame):
  def __init__(self,parent):
    super().__init__(parent,style='Page.TFrame');page_header(self,'Dashboard','Live KPIs and charts from your MySQL database');self.k=ttk.Frame(self,style='Page.TFrame');self.k.pack(fill='x',padx=30);self.body=ttk.Frame(self,style='Page.TFrame');self.body.pack(fill='both',expand=True,padx=30,pady=20);self.refresh()
  def refresh(self):
    for w in self.k.winfo_children():w.destroy()
    s=stats()
    for t,v in [('Customers',s['customers']),('Restaurants',s['restaurants']),('Orders',s['orders']),('Revenue',f"₹{s['revenue']:,.0f}"),('Deliveries',s['deliveries']),('Avg. Order',f"₹{s['avg_order']:,.0f}")]:kpi(self.k,t,v).pack(side='left',fill='x',expand=True,padx=(0,9))
    for w in self.body.winfo_children():w.destroy()
    if not MATPLOTLIB_OK:ttk.Label(self.body,text='Install matplotlib to display charts: pip install matplotlib').pack(expand=True);return
    try:
      d=analytics();fig=Figure(figsize=(11,5.5),dpi=90);a=fig.add_subplot(221);a.plot([str(x['day']) for x in d['days']],[x['count'] for x in d['days']],marker='o');a.set_title('Orders Over Time');a.tick_params(axis='x',rotation=45);a=fig.add_subplot(222);a.bar([x['status'] for x in d['status']],[x['count'] for x in d['status']]);a.set_title('Order Status');a=fig.add_subplot(223);x=d['revenue'][:8];a.barh([z['restaurant'] for z in x[::-1]],[z['revenue'] for z in x[::-1]]);a.set_title('Revenue by Restaurant');x=d['payments'];a=fig.add_subplot(224);a.pie([z['count'] for z in x],labels=[z['payment_method'] for z in x],autopct='%1.0f%%');a.set_title('Payment Methods');fig.tight_layout();c=FigureCanvasTkAgg(fig,master=self.body);c.draw();c.get_tk_widget().pack(fill='both',expand=True)
    except Exception as e:ttk.Label(self.body,text=f'Charts unavailable: {e}').pack(expand=True)

class AnalyticsPage(ttk.Frame):
  def __init__(self, parent):
    super().__init__(parent, style='Page.TFrame')
    page_header(
      self,
      'Analytics Dashboard',
      'SQL metrics, Pandas analysis and business insights from live data'
    )

    toolbar = ttk.Frame(self, style='Page.TFrame')
    toolbar.pack(fill='x', padx=30, pady=(0, 10))

    ttk.Label(toolbar, text='Restaurant').pack(side='left', padx=(5, 6))
    self.restaurant_filter = ttk.Combobox(toolbar, state='readonly', width=25)
    self.restaurant_filter.pack(side='left', padx=(0, 10))

    ttk.Label(toolbar, text='Status').pack(side='left', padx=(5, 6))
    self.status_filter = ttk.Combobox(
      toolbar,
      values=['All', 'Placed', 'Preparing', 'Ready', 'Picked Up', 'Delivered', 'Cancelled'],
      state='readonly',
      width=14
    )
    self.status_filter.set('All')
    self.status_filter.pack(side='left', padx=(0, 10))

    ttk.Label(toolbar, text='From').pack(side='left', padx=(5, 6))
    self.date_from = ttk.Entry(toolbar, width=12)
    self.date_from.pack(side='left', padx=(0, 8))

    ttk.Label(toolbar, text='To').pack(side='left', padx=(5, 6))
    self.date_to = ttk.Entry(toolbar, width=12)
    self.date_to.pack(side='left', padx=(0, 10))

    ttk.Button(
      toolbar, text='Apply Filters',
      style='Accent.TButton', command=self.refresh
    ).pack(side='left')

    ttk.Button(
      toolbar, text='Reset', command=self.reset_filters
    ).pack(side='left', padx=6)

    ttk.Button(
      toolbar, text='Export CSV', command=self.export_csv
    ).pack(side='right', padx=4)

    ttk.Button(
      toolbar, text='Export Excel', command=self.export_excel
    ).pack(side='right', padx=4)

    outer = tk.Frame(self, bg=BG)
    outer.pack(fill='both', expand=True, padx=25, pady=(0, 20))

    self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(
      outer, orient='vertical', command=self.canvas.yview
    )

    self.content = tk.Frame(self.canvas, bg=BG)
    self.window_id = self.canvas.create_window(
      (0, 0), window=self.content, anchor='nw'
    )

    self.content.bind(
      '<Configure>',
      lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    )
    self.canvas.bind(
      '<Configure>',
      lambda e: self.canvas.itemconfigure(self.window_id, width=e.width)
    )
    self.canvas.configure(yscrollcommand=scrollbar.set)

    self.canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    self.canvas.bind_all('<MouseWheel>', self._mousewheel)

    self.load_filters()
    self.refresh()

  def load_filters(self):
    self.restaurant_rows = restaurant_choices()
    values = ['All Restaurants'] + [
      f"{r['restaurant_id']} — {r['name']}" for r in self.restaurant_rows
    ]
    self.restaurant_filter['values'] = values
    self.restaurant_filter.current(0)

  def get_filters(self):
    restaurant_id = None
    index = self.restaurant_filter.current()
    if index > 0:
      restaurant_id = self.restaurant_rows[index - 1]['restaurant_id']

    status = self.status_filter.get() or 'All'
    date_from = self.date_from.get().strip() or None
    date_to = self.date_to.get().strip() or None

    for label, value in [('From date', date_from), ('To date', date_to)]:
      if value:
        try:
          datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
          raise ValueError(f'{label} must use YYYY-MM-DD format.')

    if date_from and date_to and date_from > date_to:
      raise ValueError('From date cannot be later than To date.')

    return restaurant_id, status, date_from, date_to

  def reset_filters(self):
    self.restaurant_filter.current(0)
    self.status_filter.set('All')
    self.date_from.delete(0, 'end')
    self.date_to.delete(0, 'end')
    self.refresh()

  def _mousewheel(self, event):
    try:
      self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
    except Exception:
      pass

  def refresh(self):
    for widget in self.content.winfo_children():
      widget.destroy()

    try:
      filters = self.get_filters()
      self.current_filters = filters
      data = analytics(
        restaurant_id=filters[0],
        status=filters[1],
        date_from=filters[2],
        date_to=filters[3]
      )

      self.build_kpis(data)
      self.build_trend(data)
      self.build_restaurant_performance(data)
      self.build_status_payment(data)
      self.build_delivery_section(data)
      self.build_business_insights(data)
      self.build_pandas_analysis(data)
      self.build_ratings(data)

    except Exception as e:
      messagebox.showerror(
        'Analytics Error', str(e), parent=self.winfo_toplevel()
      )

  def section_card(self, title, parent=None):
    parent = parent or self.content
    frame = tk.Frame(
      parent, bg=CARD,
      highlightbackground='#dfe4ec', highlightthickness=1
    )

    tk.Label(
      frame, text=title, bg=CARD, fg=TEXT,
      font=('Segoe UI', 13, 'bold')
    ).pack(anchor='w', padx=15, pady=(12, 5))

    body = tk.Frame(frame, bg=CARD)
    body.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    return frame, body

  def build_kpis(self, data):
    summary = data['summary']
    counts = data['counts']
    rating = data['rating']
    delivery = data['delivery_metrics']

    row1 = tk.Frame(self.content, bg=BG)
    row1.pack(fill='x', pady=(5, 7))

    cards1 = [
      ('Revenue', f"₹{float(summary['revenue'] or 0):,.0f}"),
      ('Orders', f"{int(summary['total_orders'] or 0):,}"),
      ('Avg Order', f"₹{float(summary['avg_order'] or 0):,.0f}"),
      ('Avg Rating', f"{float(rating['avg_rating'] or 0):.2f}/5"),
      ('Avg Delivery', f"{float(delivery['avg_total_time'] or 0):.1f} min"),
      ('Avg Distance', f"{float(delivery['avg_distance'] or 0):.2f} km")
    ]

    for title, value in cards1:
      kpi(row1, title, value).pack(
        side='left', fill='x', expand=True, padx=4
      )

    row2 = tk.Frame(self.content, bg=BG)
    row2.pack(fill='x', pady=(0, 12))

    cards2 = [
      ('Customers', counts['customers']),
      ('Restaurants', counts['restaurants']),
      ('Riders', counts['riders']),
      ('Menu Items', counts['menu_items']),
      ('Completion', f"{float(summary['completion_rate'] or 0):.1f}%"),
      ('Cancellation', f"{float(summary['cancellation_rate'] or 0):.1f}%")
    ]

    for title, value in cards2:
      kpi(row2, title, value).pack(
        side='left', fill='x', expand=True, padx=4
      )

  def embed_figure(self, parent, fig):
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    return canvas

  def build_trend(self, data):
    frame, body = self.section_card('Orders & Revenue Trend')
    frame.pack(fill='x', pady=7)

    if not MATPLOTLIB_OK:
      ttk.Label(body, text='Install matplotlib with: pip install matplotlib').pack(pady=30)
      return

    rows = data['trend']
    if not rows:
      tk.Label(body, text='No order data available.', bg=CARD, fg=MUTED).pack(pady=40)
      return

    dates = [str(x['day']) for x in rows]
    orders_data = [int(x['orders']) for x in rows]
    revenue_data = [float(x['revenue'] or 0) for x in rows]

    fig = Figure(figsize=(12, 4.2), dpi=90)
    ax1 = fig.add_subplot(111)
    ax1.plot(dates, orders_data, marker='o', linewidth=2, label='Orders')
    ax1.set_ylabel('Orders')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(alpha=0.2)

    ax2 = ax1.twinx()
    ax2.plot(dates, revenue_data, linestyle='--', linewidth=2, label='Revenue')
    ax2.set_ylabel('Revenue (₹)')
    ax1.set_title('Daily Orders and Revenue')
    self.embed_figure(body, fig)

  def build_restaurant_performance(self, data):
    row = tk.Frame(self.content, bg=BG)
    row.pack(fill='both', pady=7)

    left, left_body = self.section_card('Restaurant Revenue', row)
    left.pack(side='left', fill='both', expand=True, padx=(0, 5))

    right, right_body = self.section_card('Restaurant Orders', row)
    right.pack(side='right', fill='both', expand=True, padx=(5, 0))

    rows = data['restaurants'][:10]

    if not MATPLOTLIB_OK:
      ttk.Label(left_body, text='Matplotlib is required for charts.').pack(pady=30)
      ttk.Label(right_body, text='Matplotlib is required for charts.').pack(pady=30)
      return

    if not rows:
      tk.Label(left_body, text='No restaurant data.', bg=CARD, fg=MUTED).pack(pady=30)
      tk.Label(right_body, text='No restaurant data.', bg=CARD, fg=MUTED).pack(pady=30)
      return

    rows = rows[::-1]

    fig1 = Figure(figsize=(6, 4), dpi=90)
    ax1 = fig1.add_subplot(111)
    ax1.barh(
      [x['restaurant'] for x in rows],
      [float(x['revenue'] or 0) for x in rows]
    )
    ax1.set_xlabel('Revenue (₹)')
    ax1.grid(axis='x', alpha=0.2)
    self.embed_figure(left_body, fig1)

    fig2 = Figure(figsize=(6, 4), dpi=90)
    ax2 = fig2.add_subplot(111)
    ax2.barh(
      [x['restaurant'] for x in rows],
      [int(x['orders'] or 0) for x in rows]
    )
    ax2.set_xlabel('Orders')
    ax2.grid(axis='x', alpha=0.2)
    self.embed_figure(right_body, fig2)

  def build_status_payment(self, data):
    row = tk.Frame(self.content, bg=BG)
    row.pack(fill='both', pady=7)

    left, left_body = self.section_card('Order Status Distribution', row)
    left.pack(side='left', fill='both', expand=True, padx=(0, 5))

    right, right_body = self.section_card('Payment Method Analysis', row)
    right.pack(side='right', fill='both', expand=True, padx=(5, 0))

    if not MATPLOTLIB_OK:
      return

    status = data['status']
    if status:
      fig = Figure(figsize=(5.5, 4), dpi=90)
      ax = fig.add_subplot(111)
      ax.pie(
        [int(x['count']) for x in status],
        labels=[x['status'] for x in status],
        autopct='%1.0f%%',
        startangle=90
      )
      ax.set_title('Order Status Mix')
      self.embed_figure(left_body, fig)
    else:
      tk.Label(left_body, text='No order status data.', bg=CARD, fg=MUTED).pack(pady=30)

    payments = data['payments']
    if payments:
      fig = Figure(figsize=(5.5, 4), dpi=90)
      ax = fig.add_subplot(111)
      ax.bar(
        [x['payment_method'] for x in payments],
        [float(x['amount'] or 0) for x in payments]
      )
      ax.set_ylabel('Payment Value (₹)')
      ax.tick_params(axis='x', rotation=25)
      ax.grid(axis='y', alpha=0.2)
      self.embed_figure(right_body, fig)
    else:
      tk.Label(right_body, text='No payment data.', bg=CARD, fg=MUTED).pack(pady=30)

  def build_delivery_section(self, data):
    row = tk.Frame(self.content, bg=BG)
    row.pack(fill='both', pady=7)

    metrics = data['delivery_metrics']

    info, info_body = self.section_card('Delivery Performance', row)
    info.pack(side='left', fill='both', expand=True, padx=(0, 5))

    metric_rows = [
      ('Preparation Time', f"{float(metrics['avg_prep_time'] or 0):.1f} min"),
      ('Travel Time', f"{float(metrics['avg_travel_time'] or 0):.1f} min"),
      ('Total Delivery Time', f"{float(metrics['avg_total_time'] or 0):.1f} min"),
      ('Average Distance', f"{float(metrics['avg_distance'] or 0):.2f} km")
    ]

    for label, value in metric_rows:
      line = tk.Frame(info_body, bg=CARD)
      line.pack(fill='x', padx=10, pady=9)
      tk.Label(
        line, text=label, bg=CARD, fg=MUTED,
        font=('Segoe UI', 10)
      ).pack(side='left')
      tk.Label(
        line, text=value, bg=CARD, fg=TEXT,
        font=('Segoe UI', 10, 'bold')
      ).pack(side='right')

    chart, chart_body = self.section_card('Distance vs Travel Time', row)
    chart.pack(side='right', fill='both', expand=True, padx=(5, 0))

    if not MATPLOTLIB_OK:
      return

    points = data['delivery_scatter']
    if not points:
      tk.Label(chart_body, text='No delivery timestamp data.', bg=CARD, fg=MUTED).pack(pady=30)
      return

    fig = Figure(figsize=(6, 4), dpi=90)
    ax = fig.add_subplot(111)
    ax.scatter(
      [float(x['distance']) for x in points],
      [float(x['travel_time']) for x in points],
      alpha=0.65
    )
    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Travel Time (min)')
    ax.set_title('Distance vs Travel Time')
    ax.grid(alpha=0.2)
    self.embed_figure(chart_body, fig)

  def build_business_insights(self, data):
    frame, body = self.section_card('Business Insights')
    frame.pack(fill='x', pady=7)

    rows = []

    if data['restaurants']:
      r = data['restaurants'][0]
      rows.append((
        'Highest revenue restaurant',
        f"{r['restaurant']} — ₹{float(r['revenue'] or 0):,.0f}"
      ))

    if data['menu_items']:
      m = max(data['menu_items'], key=lambda x: int(x['quantity'] or 0))
      rows.append((
        'Most ordered menu item',
        f"{m['item']} — {int(m['quantity'] or 0)} units"
      ))

    if data['customer_spending']:
      c = data['customer_spending'][0]
      rows.append((
        'Highest customer spending',
        f"{c['customer']} — ₹{float(c['spending'] or 0):,.0f}"
      ))

    if data['rider_delivery']:
      rd = data['rider_delivery'][0]
      rows.append((
        'Most assigned deliveries',
        f"{rd['rider']} — {int(rd['deliveries'] or 0)} deliveries"
      ))

    summary = data['summary']
    rows.extend([
      ('Cancellation rate', f"{float(summary['cancellation_rate'] or 0):.1f}%"),
      ('Completion rate', f"{float(summary['completion_rate'] or 0):.1f}%"),
      ('Average delivery distance', f"{float(data['delivery_metrics']['avg_distance'] or 0):.2f} km")
    ])

    for label, value in rows:
      line = tk.Frame(body, bg=CARD)
      line.pack(fill='x', padx=10, pady=6)
      tk.Label(
        line, text=label, bg=CARD, fg=MUTED,
        font=('Segoe UI', 10)
      ).pack(side='left')
      tk.Label(
        line, text=value, bg=CARD, fg=TEXT,
        font=('Segoe UI', 10, 'bold')
      ).pack(side='right')

  def build_pandas_analysis(self, data):
    frame, body = self.section_card('Pandas Analysis')
    frame.pack(fill='both', pady=7)

    if not PANDAS_OK:
      tk.Label(
        body, text='Pandas is not installed. Run: pip install pandas',
        bg=CARD, fg=MUTED
      ).pack(pady=30)
      return

    df = pd.DataFrame(data['menu_items'])

    if df.empty:
      tk.Label(
        body, text='No menu-item order data for the selected filters.',
        bg=CARD, fg=MUTED
      ).pack(pady=30)
      return

    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)

    stats = pd.DataFrame({
      'Metric': [
        'Unique menu items ordered',
        'Total units sold',
        'Total item revenue',
        'Average units per item',
        'Median item revenue'
      ],
      'Value': [
        len(df),
        int(df['quantity'].sum()),
        f"₹{df['revenue'].sum():,.2f}",
        f"{df['quantity'].mean():,.2f}",
        f"₹{df['revenue'].median():,.2f}"
      ]
    })

    metric_tree = ttk.Treeview(body, columns=('metric', 'value'), show='headings', height=5)
    metric_tree.heading('metric', text='Metric')
    metric_tree.heading('value', text='Value')
    metric_tree.column('metric', width=300)
    metric_tree.column('value', width=220)
    for row in stats.itertuples(index=False):
      metric_tree.insert('', 'end', values=(row.Metric, row.Value))
    metric_tree.pack(side='left', fill='y', padx=8, pady=8)

    top = df.sort_values('revenue', ascending=False).head(10)
    top_tree = ttk.Treeview(
      body,
      columns=('item', 'restaurant', 'quantity', 'revenue'),
      show='headings',
      height=8
    )
    for col, heading, width in [
      ('item', 'Menu Item', 220),
      ('restaurant', 'Restaurant', 180),
      ('quantity', 'Units', 90),
      ('revenue', 'Revenue', 120)
    ]:
      top_tree.heading(col, text=heading)
      top_tree.column(col, width=width)
    for row in top.itertuples(index=False):
      top_tree.insert(
        '', 'end',
        values=(row.item, row.restaurant, int(row.quantity), f"₹{row.revenue:,.2f}")
      )
    top_tree.pack(side='left', fill='both', expand=True, padx=8, pady=8)

  def build_ratings(self, data):
    frame, body = self.section_card('Restaurant Ratings')
    frame.pack(fill='both', pady=7)

    columns = ('restaurant', 'rating', 'reviews')
    tree = ttk.Treeview(body, columns=columns, show='headings', height=8)

    tree.heading('restaurant', text='Restaurant')
    tree.heading('rating', text='Average Rating')
    tree.heading('reviews', text='Reviews')

    tree.column('restaurant', width=420)
    tree.column('rating', width=180, anchor='center')
    tree.column('reviews', width=150, anchor='center')

    for row in data['ratings']:
      tree.insert(
        '', 'end',
        values=(
          row['restaurant'],
          f"{float(row['rating'] or 0):.2f} / 5",
          row['reviews']
        )
      )

    tree.pack(fill='both', expand=True, padx=8, pady=8)

  def export_rows(self, data):
    return {
      'summary': [data['summary']],
      'restaurant_performance': data['restaurants'],
      'daily_trend': data['trend'],
      'monthly_trend': data['monthly'],
      'order_status': data['status'],
      'payments': data['payments'],
      'restaurant_ratings': data['ratings'],
      'menu_items': data['menu_items'],
      'top_customers': data['customer_spending'],
      'rider_delivery': data['rider_delivery']
    }

  def get_export_data(self):
    filters = self.get_filters()
    return analytics(
      restaurant_id=filters[0],
      status=filters[1],
      date_from=filters[2],
      date_to=filters[3]
    )

  def export_csv(self):
    if not PANDAS_OK:
      messagebox.showerror('Export', 'Pandas is required for CSV export.')
      return

    try:
      data = self.get_export_data()
      folder = filedialog.askdirectory(title='Choose export folder')
      if not folder:
        return

      stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
      export = self.export_rows(data)

      for name, rows in export.items():
        pd.DataFrame(rows).to_csv(
          f"{folder}/analytics_{name}_{stamp}.csv",
          index=False
        )

      messagebox.showinfo(
        'Export Complete',
        f"CSV files exported to:\n{folder}"
      )
    except Exception as e:
      messagebox.showerror('Export Error', str(e))

  def export_excel(self):
    if not PANDAS_OK:
      messagebox.showerror('Export', 'Pandas is required for Excel export.')
      return

    try:
      data = self.get_export_data()
      path = filedialog.asksaveasfilename(
        title='Save Excel report',
        defaultextension='.xlsx',
        filetypes=[('Excel workbook', '*.xlsx')]
      )
      if not path:
        return

      with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, rows in self.export_rows(data).items():
          pd.DataFrame(rows).to_excel(
            writer, sheet_name=name[:31], index=False
          )

      messagebox.showinfo(
        'Export Complete',
        f"Excel report saved to:\n{path}"
      )
    except Exception as e:
      messagebox.showerror('Export Error', str(e))


class SQLInsightsPage(ttk.Frame):
  def __init__(self, parent):
    super().__init__(parent, style='Page.TFrame')
    page_header(
      self,
      'SQL Insights',
      'Predefined analytical queries executed directly on MySQL'
    )

    bar = ttk.Frame(self, style='Page.TFrame')
    bar.pack(fill='x', padx=30, pady=(0, 10))
    ttk.Button(
      bar, text='Refresh SQL Insights',
      style='Accent.TButton', command=self.refresh
    ).pack(side='left')

    outer = tk.Frame(self, bg=BG)
    outer.pack(fill='both', expand=True, padx=25, pady=(0, 20))

    canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
    self.content = tk.Frame(canvas, bg=BG)
    window_id = canvas.create_window((0, 0), window=self.content, anchor='nw')

    self.content.bind(
      '<Configure>',
      lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
    )
    canvas.bind(
      '<Configure>',
      lambda e: canvas.itemconfigure(window_id, width=e.width)
    )
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    self.refresh()

  def card(self, title):
    frame = tk.Frame(
      self.content, bg=CARD,
      highlightbackground='#dfe4ec', highlightthickness=1
    )
    frame.pack(fill='x', pady=7)
    tk.Label(
      frame, text=title, bg=CARD, fg=TEXT,
      font=('Segoe UI', 13, 'bold')
    ).pack(anchor='w', padx=15, pady=(12, 6))
    body = tk.Frame(frame, bg=CARD)
    body.pack(fill='x', padx=10, pady=(0, 10))
    return body

  def add_table(self, parent, rows, columns, headings, widths):
    if not rows:
      tk.Label(
        parent, text='No data available.',
        bg=CARD, fg=MUTED
      ).pack(pady=15)
      return

    tree = ttk.Treeview(
      parent, columns=columns, show='headings', height=min(8, len(rows))
    )
    for col, heading, width in zip(columns, headings, widths):
      tree.heading(col, text=heading)
      tree.column(col, width=width)

    for row in rows:
      tree.insert('', 'end', values=tuple(row.get(c, '') for c in columns))

    tree.pack(fill='x', padx=5, pady=5)

  def refresh(self):
    for w in self.content.winfo_children():
      w.destroy()

    try:
      self.build_query(
        'Top Restaurants by Revenue',
        """SELECT r.name AS restaurant,
                  COUNT(o.order_id) AS orders,
                  COALESCE(SUM(CASE WHEN o.status <> 'Cancelled'
                                    THEN o.total_amount ELSE 0 END), 0) AS revenue
           FROM restaurants r
           LEFT JOIN orders o ON o.restaurant_id = r.restaurant_id
           GROUP BY r.restaurant_id, r.name
           ORDER BY revenue DESC
           LIMIT 10""",
        ('restaurant', 'orders', 'revenue'),
        ('Restaurant', 'Orders', 'Revenue'),
        (360, 110, 150),
        currency_cols={'revenue'}
      )

      self.build_query(
        'Most Ordered Menu Items',
        """SELECT m.name AS item,
                  r.name AS restaurant,
                  SUM(oi.quantity) AS units,
                  COALESCE(SUM(oi.total_price), 0) AS revenue
           FROM order_items oi
           JOIN orders o ON o.order_id = oi.order_id
           JOIN menu_items m ON m.menu_item_id = oi.menu_item_id
           JOIN restaurants r ON r.restaurant_id = m.restaurant_id
           WHERE o.status <> 'Cancelled'
           GROUP BY m.menu_item_id, m.name, r.name
           ORDER BY units DESC
           LIMIT 10""",
        ('item', 'restaurant', 'units', 'revenue'),
        ('Menu Item', 'Restaurant', 'Units', 'Revenue'),
        (260, 220, 90, 140),
        currency_cols={'revenue'}
      )

      self.build_query(
        'Customers with Highest Spending',
        """SELECT c.name AS customer,
                  COUNT(o.order_id) AS orders,
                  COALESCE(SUM(o.total_amount), 0) AS spending
           FROM customers c
           JOIN orders o ON o.customer_id = c.customer_id
           WHERE o.status <> 'Cancelled'
           GROUP BY c.customer_id, c.name
           ORDER BY spending DESC
           LIMIT 10""",
        ('customer', 'orders', 'spending'),
        ('Customer', 'Orders', 'Spending'),
        (360, 110, 160),
        currency_cols={'spending'}
      )

      self.build_query(
        'Average Delivery Time by Rider',
        """SELECT rd.name AS rider,
                  COUNT(d.delivery_id) AS deliveries,
                  ROUND(AVG(TIMESTAMPDIFF(MINUTE,
                    d.pickup_time, d.delivery_time)), 1) AS avg_minutes
           FROM riders rd
           JOIN deliveries d ON d.rider_id = rd.rider_id
           WHERE d.pickup_time IS NOT NULL
             AND d.delivery_time IS NOT NULL
           GROUP BY rd.rider_id, rd.name
           ORDER BY avg_minutes
           LIMIT 10""",
        ('rider', 'deliveries', 'avg_minutes'),
        ('Rider', 'Deliveries', 'Avg Time (min)'),
        (360, 120, 150)
      )

      self.build_query(
        'Monthly Revenue',
        """SELECT DATE_FORMAT(order_time, '%Y-%m') AS month,
                  COUNT(*) AS orders,
                  COALESCE(SUM(CASE WHEN status <> 'Cancelled'
                                    THEN total_amount ELSE 0 END), 0) AS revenue
           FROM orders
           GROUP BY DATE_FORMAT(order_time, '%Y-%m')
           ORDER BY month""",
        ('month', 'orders', 'revenue'),
        ('Month', 'Orders', 'Revenue'),
        (180, 120, 160),
        currency_cols={'revenue'}
      )

      self.build_query(
        'Cancellation Rate by Restaurant',
        """SELECT r.name AS restaurant,
                  COUNT(o.order_id) AS orders,
                  ROUND(100.0 * SUM(
                    CASE WHEN o.status = 'Cancelled' THEN 1 ELSE 0 END
                  ) / NULLIF(COUNT(o.order_id), 0), 2) AS cancellation_rate
           FROM restaurants r
           LEFT JOIN orders o ON o.restaurant_id = r.restaurant_id
           GROUP BY r.restaurant_id, r.name
           ORDER BY cancellation_rate DESC
           LIMIT 10""",
        ('restaurant', 'orders', 'cancellation_rate'),
        ('Restaurant', 'Orders', 'Cancellation %'),
        (360, 120, 160)
      )

    except Exception as e:
      messagebox.showerror(
        'SQL Insights Error', str(e), parent=self.winfo_toplevel()
      )

  def build_query(self, title, sql, columns, headings, widths, currency_cols=None):
    body = self.card(title)
    rows = fetch_all(sql)
    currency_cols = currency_cols or set()

    formatted = []
    for row in rows:
      item = dict(row)
      for col in currency_cols:
        if item.get(col) is not None:
          item[col] = f"₹{float(item[col]):,.2f}"
      formatted.append(item)

    self.add_table(body, formatted, columns, headings, widths)

class DeliveryAnalyticsApp(tk.Tk):
  def __init__(self):
    super().__init__();self.title('Delivery & Restaurant Analytics System');self.geometry('1450x850');self.minsize(1180,700);setup_styles(self);self.pages={};self.build();self.show('Dashboard')
  def build(self):
    side=tk.Frame(self,bg=NAV,width=220);side.pack(side='left',fill='y');side.pack_propagate(False);tk.Label(side,text='DELIVERY',bg=NAV,fg='white',font=('Segoe UI',15,'bold')).pack();tk.Label(side,text='ANALYTICS SYSTEM',bg=NAV,fg='#9ba8bf',font=('Segoe UI',8,'bold')).pack(pady=(0,20))
    items=[('Dashboard',DashboardPage),('Customers',CustomersPage),('Restaurants',RestaurantsPage),('Menu',MenuPage),('Orders',OrdersPage),('Deliveries',DeliveriesPage),('Riders',RidersPage),('Payments',PaymentsPage),('Reviews',ReviewsPage),('Analytics',AnalyticsPage),('SQL Insights',SQLInsightsPage)]
    self.classes=dict(items);self.nav={}
    for name,_ in items:
      b=tk.Button(side,text=name,anchor='w',padx=22,border=0,bg=NAV,fg='#d8dfed',activebackground=BLUE,activeforeground='white',font=('Segoe UI',10,'bold'),command=lambda n=name:self.show(n));b.pack(fill='x',ipady=9);self.nav[name]=b
    tk.Frame(side,bg='#2a354b',height=1).pack(fill='x',padx=22,pady=14);tk.Button(side,text='Settings',anchor='w',padx=22,border=0,bg=NAV,fg='#d8dfed',activebackground=BLUE,activeforeground='white',font=('Segoe UI',10,'bold'),command=self.settings).pack(fill='x',ipady=9)
    self.content=tk.Frame(self,bg=BG);self.content.pack(side='right',fill='both',expand=True)
  def show(self,name):
    for w in self.content.winfo_children():w.destroy()
    try:self.classes[name](self.content).pack(fill='both',expand=True)
    except Exception as e:messagebox.showerror('Database / GUI Error',str(e))
    for n,b in self.nav.items():b.configure(bg=BLUE if n==name else NAV,fg='white' if n==name else '#d8dfed')
  def settings(self):messagebox.showinfo('Settings','Uses your existing app/database.py\n\nXAMPP MySQL: localhost:3307\nDatabase: delivery_analytics\n\nNo password is stored in the GUI.')
