#!/usr/bin/env python3
"""SimRobotics CRM v2.1 - Excel-Integrated Military CRM"""
import os, sys, psycopg2, math
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('CRM_SECRET', 'simrobotics-crm-2026')

DB_CONFIG = {
    'host': 'localhost', 'port': 5432,
    'database': 'simrobotics_crm', 'user': 'sim_admin',
    'password': 'SimData_Vector_2026!', 'connect_timeout': 5
}

PAGE_SIZE = 25
ALLOWED_SORT_COLS = {
    'companies': ['name', 'sector', 'region', 'business_type', 'source_file'],
    'contacts': ['first_name', 'last_name', 'role', 'email', 'phone', 'source_file'],
    'military_bases': ['base_name', 'branch', 'state', 'city', 'command_name', 'contact_count', 'status', 'priority'],
    'military_contacts': ['contact_name', 'title', 'contact_role', 'email', 'phone'],
    'military_outreach': ['outreach_date', 'subject', 'status', 'channel'],
}

def get_db():
    return psycopg2.connect(**DB_CONFIG)

def query(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    try:
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        else:
            rows = []
    except:
        rows = []
    conn.commit()
    conn.close()
    return rows

def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None

def query_val(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    val = cur.fetchone()
    conn.close()
    return val[0] if val else 0

def paginate(table, base_sql, count_sql, params, page, sort, order):
    page = max(1, page)
    if sort not in ALLOWED_SORT_COLS.get(table, []) or order not in ('asc', 'desc'):
        sort = 'id'
        order = 'asc'
    total = query_val(count_sql, params)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    sql = base_sql + f" ORDER BY {sort} {order} LIMIT {PAGE_SIZE} OFFSET {offset}"
    rows = query(sql, params)
    return rows, total, page, total_pages, sort, order

# ── Commercial ──────────────────────────────────────────────────

@app.route('/')
def index():
    stats = {
        'companies': query_val("SELECT count(*) FROM companies"),
        'contacts': query_val("SELECT count(*) FROM contacts"),
        'interactions': query_val("SELECT count(*) FROM interactions"),
        'research': query_val("SELECT count(*) FROM contacts WHERE needs_research = true"),
    }
    return render_template('index.html', stats=stats, section='commercial', active_page='index')

@app.route('/companies')
def companies_list():
    q = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    if q:
        base_sql = "SELECT c.*, (SELECT count(*) FROM contacts WHERE company_id=c.id) as contact_count FROM companies c WHERE c.name ILIKE %s OR c.sector ILIKE %s OR c.region ILIKE %s OR c.business_type ILIKE %s"
        count_sql = "SELECT count(*) FROM companies c WHERE c.name ILIKE %s OR c.sector ILIKE %s OR c.region ILIKE %s OR c.business_type ILIKE %s"
        params = (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')
    else:
        base_sql = "SELECT c.*, (SELECT count(*) FROM contacts WHERE company_id=c.id) as contact_count FROM companies c"
        count_sql = "SELECT count(*) FROM companies"
        params = ()
    rows, total, page, total_pages, sort, order = paginate('companies', base_sql, count_sql, params, page, sort, order)
    return render_template('companies.html', companies=rows, query=q, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='commercial', active_page='companies')

@app.route('/companies/add', methods=['GET', 'POST'])
@app.route('/companies/<int:id>/edit', methods=['GET', 'POST'])
def company_form(id=None):
    company = query_one("SELECT * FROM companies WHERE id=%s", (id,)) if id else None
    if id and not company: flash('Company not found', 'error'); return redirect('/companies')
    if request.method == 'POST':
        name = request.form['name']; sector = request.form.get('sector','') or None
        region = request.form.get('region','') or None; website = request.form.get('website','') or None
        source_file = request.form.get('source_file','') or None
        business_type = request.form.get('business_type','') or None
        if id: query("UPDATE companies SET name=%s, sector=%s, region=%s, website=%s, source_file=%s, business_type=%s WHERE id=%s", (name,sector,region,website,source_file,business_type,id))
        else: query("INSERT INTO companies (name, sector, region, website, source_file, business_type) VALUES (%s,%s,%s,%s,%s,%s)", (name,sector,region,website,source_file,business_type))
        flash('Company saved!', 'success'); return redirect('/companies')
    return render_template('company_form.html', company=company, section='commercial', active_page='companies')

@app.route('/companies/<int:id>/delete', methods=['POST'])
def company_delete(id): query("DELETE FROM companies WHERE id=%s", (id,)); flash('Company deleted.', 'success'); return redirect('/companies')

@app.route('/contacts')
def contacts_list():
    q = request.args.get('q', ''); company_id = request.args.get('company_id', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'last_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(co.first_name ILIKE %s OR co.last_name ILIKE %s OR co.email ILIKE %s OR co.role ILIKE %s)"); params.extend([f'%{q}%']*4)
    if company_id: where_parts.append("co.company_id = %s"); params.append(int(company_id))
    where_clause = " AND ".join(where_parts)
    base_sql = f"SELECT co.*, c.name as company_name FROM contacts co LEFT JOIN companies c ON co.company_id=c.id WHERE {where_clause}"
    count_sql = f"SELECT count(*) FROM contacts co WHERE {where_clause}"
    rows, total, page, total_pages, sort, order = paginate('contacts', base_sql, count_sql, tuple(params), page, sort, order)
    return render_template('contacts.html', contacts=rows, query=q, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='commercial', active_page='contacts')

@app.route('/contacts/add', methods=['GET', 'POST'])
@app.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
def contact_form(id=None):
    contact = query_one("SELECT * FROM contacts WHERE id=%s", (id,)) if id else None
    if id and not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    if request.method == 'POST':
        data = [request.form['first_name'], request.form['last_name'], request.form.get('company_id') or None, request.form.get('role','') or None, request.form.get('email','') or None, request.form.get('phone','') or None, request.form.get('linkedin_url','') or None, request.form.get('needs_research', '1') == '1', request.form.get('source_file','') or None]
        if id: data.append(id); query("UPDATE contacts SET first_name=%s,last_name=%s,company_id=%s,role=%s,email=%s,phone=%s,linkedin_url=%s,needs_research=%s,source_file=%s WHERE id=%s", data)
        else: query("INSERT INTO contacts (first_name,last_name,company_id,role,email,phone,linkedin_url,needs_research,source_file) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
        flash('Contact saved!', 'success'); return redirect('/contacts')
    companies = query("SELECT id, name FROM companies ORDER BY name")
    return render_template('contact_form.html', contact=contact, all_companies=companies, section='commercial', active_page='contacts')

@app.route('/contacts/<int:id>')
def contact_view(id):
    contact = query_one("SELECT co.*, c.name as company_name FROM contacts co LEFT JOIN companies c ON co.company_id=c.id WHERE co.id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    interactions = query("SELECT * FROM interactions WHERE contact_id=%s ORDER BY interaction_date DESC", (id,))
    return render_template('contact_view.html', contact=contact, interactions=interactions, section='commercial', active_page='contacts')

@app.route('/contacts/<int:id>/delete', methods=['POST'])
def contact_delete(id): query("DELETE FROM contacts WHERE id=%s", (id,)); flash('Contact deleted.', 'success'); return redirect('/contacts')

@app.route('/contacts/<int:id>/interactions/add', methods=['GET', 'POST'])
def interaction_add(id):
    contact = query_one("SELECT * FROM contacts WHERE id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/contacts')
    if request.method == 'POST': query("INSERT INTO interactions (contact_id, interaction_date, channel, notes, next_action) VALUES (%s,%s,%s,%s,%s)", (id, request.form.get('interaction_date') or None, request.form.get('channel','') or None, request.form.get('notes','') or None, request.form.get('next_action','') or None)); flash('Interaction logged!', 'success'); return redirect(f'/contacts/{id}')
    return render_template('interaction_form.html', contact=contact, section='commercial', active_page='contacts')

# ── Military ────────────────────────────────────────────────────

@app.route('/military')
def military_dashboard():
    stats = {
        'bases': query_val("SELECT count(*) FROM military_bases"),
        'contacts': query_val("SELECT count(*) FROM military_contacts"),
        'outreach': query_val("SELECT count(*) FROM military_outreach WHERE status NOT IN ('Not Contacted','Archived','Plan Phase')"),
        'priority': query_val("SELECT count(*) FROM military_bases WHERE priority = true"),
    }
    branch_stats = query("SELECT branch, count(*) as cnt FROM military_bases GROUP BY branch ORDER BY cnt DESC")
    recent = query("""
        SELECT mo.*, mb.base_name, mc.contact_name
        FROM military_outreach mo
        LEFT JOIN military_bases mb ON mo.base_id = mb.id
        LEFT JOIN military_contacts mc ON mo.contact_id = mc.id
        WHERE mo.status != 'Plan Phase'
        ORDER BY mo.created_at DESC LIMIT 15
    """)
    return render_template('military_dashboard.html', stats=stats, branch_stats=branch_stats, recent_outreach=recent, section='military', active_page='military_dashboard')

@app.route('/military/bases')
def military_bases_list():
    q = request.args.get('q', ''); branch = request.args.get('branch', ''); state = request.args.get('state', ''); priority = request.args.get('priority', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'base_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mb.base_name ILIKE %s OR mb.city ILIKE %s OR mb.command_name ILIKE %s)"); params.extend([f'%{q}%']*3)
    if branch: where_parts.append("mb.branch = %s"); params.append(branch)
    if state: where_parts.append("mb.state = %s"); params.append(state)
    if priority: where_parts.append("mb.priority = true")
    w = " AND ".join(where_parts)
    rows, total, page, total_pages, sort, order = paginate('military_bases', f"SELECT mb.*, (SELECT count(*) FROM military_contacts WHERE base_id=mb.id) as contact_count FROM military_bases mb WHERE {w}", f"SELECT count(*) FROM military_bases mb WHERE {w}", tuple(params), page, sort, order)
    branches = query("SELECT DISTINCT branch FROM military_bases WHERE branch IS NOT NULL ORDER BY branch")
    states = query("SELECT DISTINCT state FROM military_bases WHERE state IS NOT NULL ORDER BY state")
    return render_template('military_bases.html', bases=rows, query=q, branch=branch, state=state, priority=priority, branches=branches, states=states, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_bases')

@app.route('/military/bases/add', methods=['GET', 'POST'])
@app.route('/military/bases/<int:id>/edit', methods=['GET', 'POST'])
def military_base_form(id=None):
    base = query_one("SELECT * FROM military_bases WHERE id=%s", (id,)) if id else None
    if id and not base: flash('Base not found', 'error'); return redirect('/military/bases')
    if request.method == 'POST':
        f = [
            request.form['base_name'], request.form.get('branch','') or None, request.form.get('state','') or None,
            request.form.get('country','USA'), request.form.get('city','') or None, request.form.get('command_name','') or None,
            request.form.get('small_business_office','') or None, request.form.get('contracting_office','') or None,
            request.form.get('sb_office_email','') or None, request.form.get('sb_office_phone','') or None,
            request.form.get('website','') or None, request.form.get('date_verified') or None,
            request.form.get('status','Active'), request.form.get('opportunity_notes','') or None,
            request.form.get('next_action','') or None, request.form.get('notes','') or None,
            request.form.get('priority') == '1'
        ]
        cols = "base_name,branch,state,country,city,command_name,small_business_office,contracting_office,sb_office_email,sb_office_phone,website,date_verified,status,opportunity_notes,next_action,notes,priority"
        if id:
            f.append(id)
            query(f"UPDATE military_bases SET {','.join(c.split(',')[i]+'=%s' for i,c in enumerate(cols.split(',')))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_bases ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Base saved!', 'success'); return redirect('/military/bases')
    return render_template('military_base_form.html', base=base, section='military', active_page='military_bases')

@app.route('/military/bases/<int:id>')
def military_base_view(id):
    base = query_one("SELECT * FROM military_bases WHERE id=%s", (id,))
    if not base: flash('Base not found', 'error'); return redirect('/military/bases')
    contacts = query("SELECT * FROM military_contacts WHERE base_id=%s ORDER BY contact_name", (id,))
    outreach = query("SELECT mo.*, mc.contact_name FROM military_outreach mo LEFT JOIN military_contacts mc ON mo.contact_id=mc.id WHERE mo.base_id=%s ORDER BY mo.outreach_date DESC NULLS LAST", (id,))
    opps = query("SELECT * FROM military_opportunities WHERE base_id=%s ORDER BY created_at DESC", (id,))
    return render_template('military_base_view.html', base=base, contacts=contacts, outreach=outreach, opportunities=opps, section='military', active_page='military_bases')

@app.route('/military/bases/<int:id>/delete', methods=['POST'])
def military_base_delete(id): query("DELETE FROM military_bases WHERE id=%s", (id,)); flash('Base deleted.', 'success'); return redirect('/military/bases')

@app.route('/military/contacts')
def military_contacts_list():
    q = request.args.get('q', ''); base_id = request.args.get('base_id', '')
    page = int(request.args.get('page', 1)); sort = request.args.get('sort', 'contact_name'); order = request.args.get('order', 'asc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mc.contact_name ILIKE %s OR mc.title ILIKE %s OR mc.email ILIKE %s OR mc.notes ILIKE %s)"); params.extend([f'%{q}%']*4)
    if base_id: where_parts.append("mc.base_id = %s"); params.append(int(base_id))
    w = " AND ".join(where_parts)
    rows, total, page, total_pages, sort, order = paginate('military_contacts', f"SELECT mc.*, mb.base_name FROM military_contacts mc LEFT JOIN military_bases mb ON mc.base_id=mb.id WHERE {w}", f"SELECT count(*) FROM military_contacts mc WHERE {w}", tuple(params), page, sort, order)
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('military_contacts.html', contacts=rows, query=q, base_id=base_id, all_bases=bases, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_contacts')

@app.route('/military/contacts/add', methods=['GET', 'POST'])
@app.route('/military/contacts/<int:id>/edit', methods=['GET', 'POST'])
def military_contact_form(id=None):
    contact = query_one("SELECT * FROM military_contacts WHERE id=%s", (id,)) if id else None
    if id and not contact: flash('Contact not found', 'error'); return redirect('/military/contacts')
    if request.method == 'POST':
        f = [request.form.get('base_id') or None, request.form['contact_name'], request.form.get('title','') or None, request.form.get('email','') or None, request.form.get('phone','') or None, request.form.get('contact_role','Small Business POC'), request.form.get('decision_maker') == '1', request.form.get('notes','') or None, request.form.get('needs_followup') == '1']
        cols = "base_id,contact_name,title,email,phone,contact_role,decision_maker,notes,needs_followup"
        if id:
            f.append(id)
            query(f"UPDATE military_contacts SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_contacts ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Contact saved!', 'success'); return redirect('/military/contacts')
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    return render_template('military_contact_form.html', contact=contact, all_bases=bases, section='military', active_page='military_contacts')

@app.route('/military/contacts/<int:id>')
def military_contact_view(id):
    contact = query_one("SELECT mc.*, mb.base_name FROM military_contacts mc LEFT JOIN military_bases mb ON mc.base_id=mb.id WHERE mc.id=%s", (id,))
    if not contact: flash('Contact not found', 'error'); return redirect('/military/contacts')
    outreach = query("SELECT * FROM military_outreach WHERE contact_id=%s ORDER BY outreach_date DESC NULLS LAST", (id,))
    return render_template('military_contact_view.html', contact=contact, outreach=outreach, section='military', active_page='military_contacts')

@app.route('/military/contacts/<int:id>/delete', methods=['POST'])
def military_contact_delete(id): query("DELETE FROM military_contacts WHERE id=%s", (id,)); flash('Contact deleted.', 'success'); return redirect('/military/contacts')

@app.route('/military/outreach')
def military_outreach_list():
    q = request.args.get('q', ''); status = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'outreach_date'); order = request.args.get('order', 'desc')
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.subject ILIKE %s OR mo.notes ILIKE %s)"); params.extend([f'%{q}%']*2)
    if status: where_parts.append("mo.status = %s"); params.append(status)
    w = " AND ".join(where_parts)
    if sort not in ALLOWED_SORT_COLS.get('military_outreach', []) or order not in ('asc', 'desc'):
        sort = 'outreach_date'; order = 'desc'
    base_sql = f"SELECT mo.*, mb.base_name, mc.contact_name FROM military_outreach mo LEFT JOIN military_bases mb ON mo.base_id = mb.id LEFT JOIN military_contacts mc ON mo.contact_id = mc.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM military_outreach mo WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY {sort} {order} NULLS LAST LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    statuses = query("SELECT DISTINCT status FROM military_outreach ORDER BY status")
    return render_template('military_outreach.html', outreach_records=rows, query=q, status=status, statuses=statuses, page=page, total_pages=total_pages, total=total, sort=sort, order=order, section='military', active_page='military_outreach')

@app.route('/military/outreach/add', methods=['GET', 'POST'])
@app.route('/military/outreach/<int:id>/edit', methods=['GET', 'POST'])
def military_outreach_form(id=None):
    record = query_one("SELECT * FROM military_outreach WHERE id=%s", (id,)) if id else None
    if id and not record: flash('Outreach record not found', 'error'); return redirect('/military/outreach')
    if request.method == 'POST':
        f = [request.form.get('contact_id') or None, request.form.get('base_id') or None, request.form.get('capability_briefing_requested') == '1', request.form.get('outreach_date') or None, request.form.get('channel','') or None, request.form.get('subject','') or None, request.form.get('response','') or None, request.form.get('briefing_scheduled') or None, request.form.get('follow_up_date') or None, request.form.get('status','Not Contacted'), request.form.get('notes','') or None, request.form.get('next_action','') or None]
        cols = "contact_id,base_id,capability_briefing_requested,outreach_date,channel,subject,response,briefing_scheduled,follow_up_date,status,notes,next_action"
        if id:
            f.append(id)
            query(f"UPDATE military_outreach SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_outreach ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Outreach record saved!', 'success'); return redirect('/military/outreach')
    contacts = query("SELECT id, contact_name, title FROM military_contacts ORDER BY contact_name")
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    sl = ['Not Contacted','Contacted','Response Received','Briefing Scheduled','Briefing Completed','Won','Lost','Archived','Plan Phase']
    channels = ['Email','Phone','In-Person','Video Conference','Conference','Site Visit','Capabilities Briefing','LinkedIn','SAM.gov']
    return render_template('military_outreach_form.html', record=record, all_contacts=contacts, all_bases=bases, statuses=sl, channels=channels, section='military', active_page='military_outreach')

@app.route('/military/outreach/<int:id>/delete', methods=['POST'])
def military_outreach_delete(id): query("DELETE FROM military_outreach WHERE id=%s", (id,)); flash('Outreach record deleted.', 'success'); return redirect('/military/outreach')

@app.route('/military/opportunities')
def military_opportunities_list():
    q = request.args.get('q', ''); phase = request.args.get('phase', '')
    page = int(request.args.get('page', 1))
    where_parts = ["1=1"]; params = []
    if q: where_parts.append("(mo.opportunity_name ILIKE %s OR mo.solicitation_number ILIKE %s)"); params.extend([f'%{q}%']*2)
    if phase: where_parts.append("mo.phase = %s"); params.append(phase)
    w = " AND ".join(where_parts)
    base_sql = f"SELECT mo.*, mb.base_name FROM military_opportunities mo LEFT JOIN military_bases mb ON mo.base_id = mb.id WHERE {w}"
    count_sql = f"SELECT count(*) FROM military_opportunities mo WHERE {w}"
    total = query_val(count_sql, tuple(params)); total_pages = max(1, math.ceil(total / PAGE_SIZE)); page = min(page, total_pages)
    offset = (page - 1) * PAGE_SIZE
    rows = query(base_sql + f" ORDER BY mo.created_at DESC LIMIT {PAGE_SIZE} OFFSET {offset}", tuple(params))
    phases = query("SELECT DISTINCT phase FROM military_opportunities WHERE phase IS NOT NULL ORDER BY phase")
    return render_template('military_opportunities.html', opportunities=rows, query=q, phase=phase, phases=phases, page=page, total_pages=total_pages, total=total, section='military', active_page='military_outreach')

@app.route('/military/opportunities/add', methods=['GET', 'POST'])
@app.route('/military/opportunities/<int:id>/edit', methods=['GET', 'POST'])
def military_opportunity_form(id=None):
    opp = query_one("SELECT * FROM military_opportunities WHERE id=%s", (id,)) if id else None
    if id and not opp: flash('Opportunity not found', 'error'); return redirect('/military/opportunities')
    if request.method == 'POST':
        f = [request.form.get('base_id') or None, request.form['opportunity_name'], request.form.get('solicitation_number','') or None, request.form.get('contract_value') or None, request.form.get('phase','') or None, request.form.get('estimated_award') or None, int(request.form.get('probability', 0)), request.form.get('service_type','') or None, request.form.get('notes','') or None]
        cols = "base_id,opportunity_name,solicitation_number,contract_value,phase,estimated_award,probability,service_type,notes"
        if id:
            f.append(id)
            query(f"UPDATE military_opportunities SET {','.join(c+'=%s' for c in cols.split(','))} WHERE id=%s", f)
        else:
            query(f"INSERT INTO military_opportunities ({cols}) VALUES ({','.join('%s' for _ in f)})", f)
        flash('Opportunity saved!', 'success'); return redirect('/military/opportunities')
    bases = query("SELECT id, base_name FROM military_bases ORDER BY base_name")
    pl = ['Identification','Qualification','Capture','Proposal','Submitted','Awarded','Lost','Closed']
    return render_template('military_opportunity_form.html', opp=opp, all_bases=bases, phases=pl, section='military', active_page='military_outreach')

@app.route('/military/opportunities/<int:id>/delete', methods=['POST'])
def military_opportunity_delete(id): query("DELETE FROM military_opportunities WHERE id=%s", (id,)); flash('Opportunity deleted.', 'success'); return redirect('/military/opportunities')

# ── Placeholders ────────────────────────────────────────────────

def placeholder(title, section_name, page_name):
    return render_template('placeholder.html', title=title, section=section_name, active_page=page_name)

@app.route('/sales/pipeline')
def sales_pipeline(): return placeholder('Sales Pipeline', 'sales', 'sales_pipeline')
@app.route('/sales/deals')
def sales_deals(): return placeholder('Deals', 'sales', 'sales_deals')
@app.route('/sales/quotes')
def sales_quotes(): return placeholder('Quotes', 'sales', 'sales_quotes')
@app.route('/marketing/campaigns')
def marketing_campaigns(): return placeholder('Campaigns', 'marketing', 'marketing_campaigns')
@app.route('/marketing/leads')
def marketing_leads(): return placeholder('Leads', 'marketing', 'marketing_leads')
@app.route('/support/tickets')
def support_tickets(): return placeholder('Support Tickets', 'support', 'support_tickets')
@app.route('/support/kb')
def support_kb(): return placeholder('Knowledge Base', 'support', 'support_kb')
@app.route('/reports/analytics')
def reports_analytics(): return placeholder('Analytics', 'reports', 'reports_analytics')
@app.route('/reports/dashboards')
def reports_dashboards(): return placeholder('Custom Dashboards', 'reports', 'reports_dashboards')
@app.route('/admin/settings')
def admin_settings(): return placeholder('Settings', 'admin', 'admin_settings')
@app.route('/admin/users')
def admin_users(): return placeholder('User Management', 'admin', 'admin_users')
@app.route('/admin/audit')
def admin_audit(): return placeholder('Audit Log', 'admin', 'admin_audit')

# ── Main ────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('CRM_PORT', 80))
    print(f'\n🚀 SimRobotics CRM running on http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
